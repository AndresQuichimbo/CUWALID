# -*- coding: utf-8 -*-
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import cg, spsolve
import cuwalid.dryp.components.lakesf90 as lakes
from cuwalid.dryp.components.DRYP_io import _compute_inactive_links

REG_FACTOR = 0.001  # Regularization factor for confined aquifers
COURANT_2D = 0.50 # Courant Number 2D flow

# --- 1. GROUNDWATER FLOW SOLVER CLASS ---
class gwflow_EFD(object):
	"""Module for solving 2D Unsteady Dupuit-Forchheimer Equation in Polar Coordinates
	using a highly efficient Vectorized Explicit Finite Difference Method (FDM).
	"""

	def __init__(self, grid, Ksat, area_river, bc, method=0,
			solver='explicit', implicit_max_iter=8,
			implicit_tolerance=1.0e-6, linear_max_iter=200):
		"""Initialize the groundwater flow solver.
		Args:
			grid (object): Grid object containing spatial discretization.
			Ksat (float): Hydraulic conductivity [L/T].
			area_river (float): Area of the river boundary [L^2].
			bc (dict): Boundary conditions.
			method (str): Numerical method to use ('vectorized' or 'looped').
		"""

		self.grid = grid

		self.Ksat = Ksat

		self.bc = bc
		self.bc_values = None

		self.method = method
		self.solver = solver.lower()
		if self.solver not in ('explicit', 'implicit'):
			raise ValueError("solver must be 'explicit' or 'implicit'")
		self.implicit_max_iter = max(1, int(implicit_max_iter))
		self.implicit_tolerance = float(implicit_tolerance)
		self.linear_max_iter = max(20, int(linear_max_iter))

		# create additional arrays for model component variables
		self.method = method	
		#	print('GROUND WATER MODEL SETTINGS ********************************')		
		if method == 0:
			print('Groundwater settings: Constant transmissivity function')
		elif method == 1:
			print('Groundwater settings: Linear transmissivity function')
		elif method == 2:
			print('Groundwater settings: Exponential transmissivity function')
		else:
			print('Groundwater settings: Multi-transmissivity function')
		print(f'Groundwater solver: {self.solver}')
		
		# set up boundary conditions
		self.id_CHB = None
		if bc is not None:
			self.id_CHB = np.where(bc != -9999)[0]
			if self.id_CHB.size > 0:
				self.bc_values = bc[self.id_CHB]
			else:
				self.id_CHB = None
		#print("Constant Head Boundary Nodes:", bc.reshape((grid['N_y'], grid['N_x'])))
		#print("Constant Head Boundary Nodes:", self.id_CHB)
		#print("Constant Head Boundary Values:", self.bc)
		#print("Initial Head:", c)
		# get active nodes array
		# create provisional domain for active nodes
		inodetype = np.zeros(grid['N_cells'])
		inodetype[grid['core_nodes']] = 1  # mark active nodes
		if self.id_CHB is not None:
			inodetype[self.id_CHB] = 2  # mark constant head boundary nodes
		
		self.act_nodes = inodetype
		#print(inodetype.reshape((grid['N_y'], grid['N_x'])))
		# get inactive links from grid object
		inactive_links, _ = _compute_inactive_links(grid, inodetype)
		
		# Pre-calculated static conductance array (length = N_connections)
		self.C_static = _precalculate_static_conductance(grid, Ksat)

		# update pre-calculated inactive links in grid
		self.C_static[inactive_links] = 0.0
		self._prepare_solver_layout(grid)
	
		# calculate cell area
		A = grid['Areas']	
			
		# calcualte river factor to reduce number of calculations
		kriv = np.ones_like(area_river)
		kriv[area_river > 0] = 1/area_river[area_river > 0]
		self.kriv = kriv

		# calcualte aquifer-river factor to reduce calculations
		self.kaq = 1/A

		pass

	def _prepare_solver_layout(self, grid):
		"""Precompute sparse-assembly topology for the implicit solver."""
		self.active_nodes = np.where(self.act_nodes > 0)[0]
		self.active_node_mask = self.act_nodes > 0
		self.fixed_node_mask = np.zeros(grid['N_cells'], dtype=bool)
		if self.id_CHB is not None:
			self.fixed_node_mask[self.id_CHB] = True

		self.free_nodes = self.active_nodes[~self.fixed_node_mask[self.active_nodes]]
		self.free_index = -np.ones(grid['N_cells'], dtype=int)
		self.free_index[self.free_nodes] = np.arange(len(self.free_nodes))

		edge_mask = (
			(grid['I'] < grid['J'])
			& (self.C_static > 0.0)
			& self.active_node_mask[grid['I']]
			& self.active_node_mask[grid['J']]
		)
		self.edge_indices = np.flatnonzero(edge_mask)
		self.edge_i = grid['I'][self.edge_indices]
		self.edge_j = grid['J'][self.edge_indices]
		self.edge_c_static = self.C_static[self.edge_indices]

		edge_i_fixed = self.fixed_node_mask[self.edge_i]
		edge_j_fixed = self.fixed_node_mask[self.edge_j]

		ff_mask = (~edge_i_fixed) & (~edge_j_fixed)
		if_mask = edge_i_fixed & (~edge_j_fixed)
		fi_mask = (~edge_i_fixed) & edge_j_fixed

		self.ff_edge_idx = np.flatnonzero(ff_mask)
		self.if_edge_idx = np.flatnonzero(if_mask)
		self.fi_edge_idx = np.flatnonzero(fi_mask)

		self.ff_i = self.free_index[self.edge_i[self.ff_edge_idx]]
		self.ff_j = self.free_index[self.edge_j[self.ff_edge_idx]]
		self.if_free = self.free_index[self.edge_j[self.if_edge_idx]]
		self.fi_free = self.free_index[self.edge_i[self.fi_edge_idx]]
		self.if_fixed_global = self.edge_i[self.if_edge_idx]
		self.fi_fixed_global = self.edge_j[self.fi_edge_idx]

		self.ff_rows = np.concatenate((self.ff_i, self.ff_j))
		self.ff_cols = np.concatenate((self.ff_j, self.ff_i))

	def run_one_step_gw(self, grid, surface, bottom, thickness,
			bathymetry, riv_elevation, riv_nodes, Sy, Droot,
			conductivity, inodetype, theta_sat, theta_fc, theta_dt,
			head, recharge, stage, dt,
			ids_lks=None, sizes_lks=None, ids_max_depth_lks=None
			):
		"""Solves the non-linear Dupuit-Forchheimer equation explicitly using CVFDM 
		and indexed vectorization (np.bincount).
		
		Function to update water table depending on the
		unsaturated zone.
		
		Parameters
		-----------
		grid : object grid
			landlab grid
		bottom : numpy array
			aquifer bottom elevation [m]
		Droot: numpy array
			Rooting depth [mm]
		tht_dt: numpy array
			Water content at time t [-]
		Duz: numpy array
			Unsaturated zone depth [m]
		surface:	numpy array
			Topograhic elevation [m]
		bathymetry:	numpy array
			topographic elevation including bottom lakes
		conductivity : numpy array
			hydroulic conductivity of the streambed [m3 h-1]
		head: numpy array
			water table [m]
		theta_sat: numpy array
			Saturated water content [-]
		theta_fv: numpy array
			Field capacity [-]
		Sy:	numpy array
			Specific yield [-]
		dq : numpy array
			water storage anomaly [m]
		thickness :	numpy array
			effective aquifer depth [m]
		SS_loss :	numpy array
			transmission losses [m3 h-1]
		recharge : numpy array
			groundwater recharge [m/dt]
		
		Returns
		-------
		head : numpy array
			water table head [m]
		discharge : numpy array
			groundwater discharge (baseflow) [m/dt]
		
		"""
		if self.solver == 'implicit':
			return self._run_one_step_gw_implicit(
				grid, surface, bottom, thickness, bathymetry,
				riv_elevation, riv_nodes, Sy, Droot, conductivity,
				inodetype, theta_sat, theta_fc, theta_dt, head,
				recharge, stage, dt, ids_lks=ids_lks,
				sizes_lks=sizes_lks,
				ids_max_depth_lks=ids_max_depth_lks
			)

		# get number of cells
		N_cells = grid['N_cells']
		areas = grid['Areas']
		inv_areas = 1.0/areas

		# Array lookups for connections
		I = grid['I']
		J = grid['J']

		# create dynamic surface elevation to handle lakes
		surface_i = surface.copy()

		# number of active nodes
		act_nodes = np.where(self.act_nodes > 0)[0]
		n_act_nodes = len(act_nodes)
		Ksat_act = self.Ksat[act_nodes]
		Sy_act = Sy[act_nodes]
		thickness_act = thickness[act_nodes]
		dx_act = grid['Dx_cell'][act_nodes]
		recharge_over_dt = recharge/dt

		# initialize discharge
		discharge = np.zeros_like(surface, dtype=float)
		
		# initialize seepage
		dqs = np.zeros_like(surface, dtype=float)
		
		# initialize water storage change
		water_storage_change = np.zeros_like(thickness, dtype=float)
		#print('Initial Head', len(bottom), len(surface), len(head), len(thickness))
		# initialize saturated thinckess
		thickness_sat = np.array(thickness, dtype=float)
		thickness_sat[act_nodes] = update_saturated_thickness(head[act_nodes],
									bottom[act_nodes], surface[act_nodes],
									thickness_sat[act_nodes], inodetype[act_nodes],
									method=self.method
									)
		#print('thickness', thickness_sat[act_nodes])
		# change in total storage at the end of the time step
		total_storage_change = 0.0
		#print("Constant Head Boundary Nodes:", self.id_CHB)
		# flux at constant head boundary
		self.flux_at_CHB = 0.0
		#print("Initial Head:", head[act_nodes])
		# Apply initial fixed boundary conditions (if provided)
		if self.id_CHB is not None:
			head[self.id_CHB] = self.bc_values
			# Ensure that BC nodes are not updated by the flux calculation
			Sy_for_update = Sy.copy()
			Sy_for_update[self.id_CHB] = np.inf # Effectively sets update term to zero
		else:
			Sy_for_update = Sy

		surface_act32 = np.asarray(surface[act_nodes], dtype=np.float32)
		bathymetry_act32 = np.asarray(bathymetry[act_nodes], dtype=np.float32)
		bathy_minus_droot_act32 = np.asarray(
			bathymetry[act_nodes] - Droot[act_nodes], dtype=np.float32
		)
		ones_act32 = np.ones(n_act_nodes, np.float32)
		zeros_act32 = np.zeros(n_act_nodes, np.float32)
		theta_sat_act32 = np.asarray(theta_sat[act_nodes], np.float32)
		theta_fc_act32 = np.asarray(theta_fc[act_nodes], np.float32)
		theta_dt_act32 = np.asarray(theta_dt[act_nodes], np.float32)
		Sy_for_update_act32 = np.asarray(Sy_for_update[act_nodes], np.float32)

		has_river = len(riv_nodes) > 0
		if has_river:
			riv_nodes = np.asarray(riv_nodes)
			riv_elevation_nodes = riv_elevation[riv_nodes]
			riv_area = areas[riv_nodes]
			riv_sy = Sy[riv_nodes]
			riv_storage = riv_area*riv_sy
			riv_kaq = self.kaq[riv_nodes]
			if np.ndim(conductivity) == 0:
				riv_cond = conductivity
			else:
				riv_cond = conductivity[riv_nodes]

		has_lakes = ids_lks is not None
		if has_lakes:
			lks_reduce_idx = np.append([0], np.cumsum(sizes_lks)[:-1])
		#print("Initial Head2:", head[act_nodes])#.reshape((grid['N_y'], grid['N_x'])))
		## Calculate the per-cell update factor (dt / (Sy * Area))
		#Update_Factor = dt / (Sy_for_update * grid['Areas'])
		#print("BC Head:", head[act_nodes])
		
		# calculate maximum allowable time step based on Courant condition
		dts = get_maximim_time_step(Ksat_act, Sy_act, thickness_act, dx_act)
		# Calculate minimal time step		
		dtp = np.nanmin([dt, dts])		
		dtsp = dtp
		# inner iteration counter
		inner_iter = 0

		while dtp <= dt:
			# adjusting heads at the bottom of the model domain
			# WARNING! this could lead to increases in mass balance errors
			np.minimum(surface, head, out=head)
			# calculate aquifer saturated thickness at nodes
			# for models with exponential function assign effective depth
			# skip this for first iiteration
			if inner_iter > 0:
				thickness_sat[act_nodes] = update_saturated_thickness(
					head[act_nodes],
					bottom[act_nodes],
					surface[act_nodes],
					thickness[act_nodes],
					inodetype[act_nodes],
					method=self.method
				)

				if self.id_CHB is not None:
				#self.ch_boundaries = bc[self.id_CHB]
					head[self.id_CHB] = self.bc_values
			
			# 1. Calculate Transmissivity at the Interface (T_ij^k = K_avg * h_avg)    
			# Head at interface (Arithmetic Mean): h_avg = (h_i + h_j) / 2
			h_i = head[I]
			h_j = head[J]
			thickness_sat_i = thickness_sat[I]
			thickness_sat_j = thickness_sat[J]
	
			#h_interface = 0.5 * (h_i + h_j)
			# Limit h_interface to the saturated thickness at the interface
			thickness_interface = 0.5 * (thickness_sat_i + thickness_sat_j)
			
			# Handle lakes at lake nodes			
			if has_lakes:
				z_lks = np.repeat(head[ids_max_depth_lks], sizes_lks)

				# Check if head is above the bottom elevation of the lakes
				z_lks = np.where(
					z_lks >= bathymetry[ids_lks], z_lks, bathymetry[ids_lks]
					)
	
			# T_interface^k = C_static * h_interface
			# Q_flow_i_to_j = C_static * h_interface * (h_i - h_j)
			Q_flow_i_to_j = self.C_static * thickness_interface * (h_i - h_j)

			# 2. Calculate Divergence: Sum Fluxes per Cell (Net Flux) using np.bincount    
			# Flux leaving cell I (Outflow, must be subtracted): Q_flow_i_to_j where I is the host
			Net_Flux = np.bincount(I, weights=Q_flow_i_to_j, minlength=N_cells)
	
			# Net flux into cell I = Inflow - Outflow [depth/time]
			Net_Flux = -Net_Flux*inv_areas

			if self.id_CHB is not None:
				self.flux_at_CHB = Net_Flux[self.id_CHB].sum()
			
			Net_Flux += recharge_over_dt

			#print("Head before river interaction:", head[act_nodes])
			# add river component
			if has_river:
				riv_stage = riv_elevation_nodes + stage[riv_nodes]

				# Equivalent to head - min(head, river_stage), but avoids an extra temporary array.
				head_diff = head[riv_nodes] - riv_stage
				np.maximum(head_diff, 0.0, out=head_diff)

				# New implementation of river-aquifer interaction using conductance and head difference
				# and a threshold to avoid numerical instability when conductivity is high.
				with np.errstate(divide='ignore', invalid='ignore'):
					aux = np.log(head_diff) - riv_cond*dt/riv_storage
				head_diff -= np.where(aux > 0.0, np.exp(aux), 0.0)
				qs_riv = head_diff*riv_storage
				
				# Calculate river cell flux [m3 h-1] (This section has been removed)
				#qs_riv = np.zeros_like(riv_nodes, dtype=float)
				#qs_riv = (conductivity[riv_nodes]*head_diff)
				
				# add river out/inflow to the mass balance [depth/time]
				# change river flow units m3 -> m
				#print('Net_Flux before riv', Net_Flux, len(Net_Flux))
				#print('riv_nodes', riv_nodes, len(riv_nodes))
				Net_Flux[riv_nodes] -= riv_kaq*qs_riv

			
			# 3. REGULARIZATION APPROACH **************************
			# calculate regularization for aquifer cells
			# check if lakes are active
			if has_lakes:
				surface_i[ids_lks] = z_lks

			# calculate regularization for aquifer cells
			dqs[act_nodes] = regularization_T(surface_i[act_nodes], head[act_nodes],
				thickness[act_nodes], Net_Flux[act_nodes], REG_FACTOR)
		
			# 4. handle lakes at lake nodes
			if has_lakes:
				# create a mask of wet cell lakes
				wet_msk_lks = np.where(head[ids_lks] >= bathymetry[ids_lks], 1, 0)
				# Calculate anomaly in water table depth at lake nodes
				dh_lks = head[ids_lks] - z_lks
				# Mask out dry cell lakes (dry cells become zero)
				dh_lks = dh_lks*wet_msk_lks
				# redistribute the water table depth anomaly to the links at lake nodes
				# calculate the sum of water table depth anomaly at lake nodes
				sum_dh_lks = np.add.reduceat(dh_lks, lks_reduce_idx)
				# count the number of wet cells in each lake
				sum_wet_lks = np.add.reduceat(wet_msk_lks, lks_reduce_idx)
				# calculate the average water table depth anomaly at lake nodes
				avg_dh_lks = np.divide(sum_dh_lks, sum_wet_lks,
							out=np.zeros_like(sum_dh_lks),
							where=sum_wet_lks!=0
							)
				
				# assign maximum lake depth to the head at lake nodes
				head[ids_lks] = (head[ids_lks]*(1-wet_msk_lks)+ 
					wet_msk_lks*(z_lks + #avg_dh_lks
					np.repeat(avg_dh_lks, sizes_lks))
					)
				
				# modify storage change at lake nodes [depth/time]
				# calculate the change in water storage at lake nodes
				# if storage chang eis positive, and seepage is positive, accumulate the seepage to
				# the water storage change at lake nodes
				dqs[ids_lks] = dqs[ids_lks]*(1-wet_msk_lks)# + wet_msk_lks*avg_dh_lks

			# 5. Final Explicit Update    
			# Calculate storage change			
			water_storage_change[act_nodes] = (Net_Flux[act_nodes]-dqs[act_nodes])*dtsp
			#print('water_storage_change', water_storage_change[27:36])
			
			# calculate total storage change to evaluate mass balance
			total_storage_change += np.mean(water_storage_change[act_nodes])

			# Update storage change for soil-gw interactions
			# run FORTRAN connector
			# create an auxiliary variable to interact with fortran
			aux_head = np.asarray(head[act_nodes], np.float32)
			water_storage_change_act32 = np.asarray(
				water_storage_change[act_nodes], np.float32
			)
			#print('Before update soil', aux_head)
			lakes.uz_sz_interaction.update_soil(
				surface_act32,# surface elev
				bathymetry_act32,# bottom elev. upper layer
				bathy_minus_droot_act32, # bottom elev. lower layer
				ones_act32,# specifiy yield upper layer (always 1 for lakes)
				zeros_act32, # field capacity (always zero for lakes)
				zeros_act32,# water content (alwas zero for lakes)
				theta_sat_act32,#tht_sat
				theta_fc_act32,#tht_fc
				theta_dt_act32,#tht_dt
				water_storage_change_act32,#dS
				Sy_for_update_act32,#Sy
				aux_head
				)

            # asign updated values of aquifer heads to the groundwater object
			head[act_nodes] = aux_head
			#print('Updated Head', head[act_nodes])
			# accumulate discharge
			if has_river:
				discharge[riv_nodes] += qs_riv*riv_kaq*dtsp

			discharge[act_nodes] += dqs[act_nodes]*dtsp

			# Apply boundary condition reset (fixed head nodes must not change)
			if self.id_CHB is not None:
				head[self.id_CHB] = self.bc_values
			#print("Updated Head:", head.reshape((grid['N_y'], grid['N_x'])))
			# Physical constraint: Head cannot be negative
			np.maximum(head, 0.0, out=head)
			
			# adjusting head at the surface of the model domain
			# WARNING! this could lead to increases in mass balance errors
			np.minimum(surface, head, out=head)

			# calculate new time step based on Courant condition
			dtsp = get_maximim_time_step(Ksat_act, Sy_act, thickness_sat[act_nodes], dx_act)
			
			# Update time step
			if dtsp <= 0:
				raise Exception("invalid time step", dtsp)			
			if dtp == dt:			
				dtp += dtsp			
			elif (dtp + dtsp) > dt:			
				dtsp = dt - dtp				
				dtp += dtsp				
			else:			
				dtp += dtsp

			# store history
			inner_iter += 1

		# calculate discharge at the end of the time step
		self.flux_at_CHB = self.flux_at_CHB/n_act_nodes
		# check calculate water balance of the groundwater component
		#print(np.mean(recharge[act_nodes]), np.mean(discharge[act_nodes]),
		#		np.mean(total_storage_change), self.flux_at_CHB)
		try:
			MB = (np.mean(recharge[act_nodes]) - np.mean(discharge[act_nodes])
				 - np.mean(total_storage_change) - self.flux_at_CHB)
			#print(MB)
			assert np.allclose(MB, 0.0, rtol=1e-05, atol=1e-04)
		except:
			raise Exception('Groundwater Water balance Error: ', MB,
		   		'Please check units and non-data values: ', 
				np.where(np.isnan(recharge[act_nodes]) | np.isinf(recharge[act_nodes])),
				' Check time step: dt = ', dtsp)

		return head, discharge

	def _run_one_step_gw_implicit(self, grid, surface, bottom, thickness,
			bathymetry, riv_elevation, riv_nodes, Sy, Droot,
			conductivity, inodetype, theta_sat, theta_fc, theta_dt,
			head, recharge, stage, dt,
			ids_lks=None, sizes_lks=None, ids_max_depth_lks=None):
		"""Solve groundwater flow with a Picard-linearized backward-Euler step.

		This path assembles a free-node sparse system on unique edges, so the
		linear operator remains symmetric and compact while reusing the existing
		vectorized geometry and soil-coupling code.
		"""
		act_nodes = self.active_nodes
		n_act_nodes = len(act_nodes)
		n_free_nodes = len(self.free_nodes)
		has_lakes = ids_lks is not None
		surface_i = surface.copy()
		head_initial = np.minimum(surface, np.array(head, dtype=float, copy=True))
		if self.id_CHB is not None:
			head_initial[self.id_CHB] = self.bc_values
		head_iter = head_initial.copy()

		discharge = np.zeros_like(surface, dtype=float)
		dqs = np.zeros_like(surface, dtype=float)
		water_storage_change = np.zeros_like(thickness, dtype=float)
		total_storage_change = 0.0
		self.flux_at_CHB = 0.0

		areas = grid['Areas']
		areas_act = areas[act_nodes]
		recharge_volume_free = recharge[self.free_nodes]*areas[self.free_nodes]*dt
		storage_coeff_free = Sy[self.free_nodes]*areas[self.free_nodes]#/dt

		surface_act32 = np.asarray(surface[act_nodes], dtype=np.float32)
		bathymetry_act32 = np.asarray(bathymetry[act_nodes], dtype=np.float32)
		bathy_minus_droot_act32 = np.asarray(
			bathymetry[act_nodes] - Droot[act_nodes], dtype=np.float32
		)
		ones_act32 = np.ones(n_act_nodes, np.float32)
		zeros_act32 = np.zeros(n_act_nodes, np.float32)
		theta_sat_act32 = np.asarray(theta_sat[act_nodes], np.float32)
		theta_fc_act32 = np.asarray(theta_fc[act_nodes], np.float32)
		theta_dt_act32 = np.asarray(theta_dt[act_nodes], np.float32)
		Sy_for_update = Sy[act_nodes].copy()
		if self.id_CHB is not None:
			bc_local_mask = np.isin(act_nodes, self.id_CHB)
			Sy_for_update[bc_local_mask] = np.inf
		Sy_for_update_act32 = np.asarray(Sy_for_update, np.float32)

		has_river = len(riv_nodes) > 0
		if has_river:
			riv_nodes = np.asarray(riv_nodes, dtype=int)
			riv_stage = riv_elevation[riv_nodes] + stage[riv_nodes]
			riv_area = areas[riv_nodes]
			riv_sy = Sy[riv_nodes]
			riv_storage = np.maximum(riv_area*riv_sy, np.finfo(float).eps)
			if np.ndim(conductivity) == 0:
				riv_cond = np.full(len(riv_nodes), conductivity, dtype=float)
			else:
				riv_cond = conductivity[riv_nodes]
			riv_exchange_coeff = (
				riv_storage/dt
				* (1.0 - np.exp(-riv_cond*dt/riv_storage))
			)
			riv_free_mask = self.free_index[riv_nodes] >= 0
			riv_free_nodes = riv_nodes[riv_free_mask]
			riv_free_stage = riv_stage[riv_free_mask]
			riv_free_coeff = riv_exchange_coeff[riv_free_mask]
			riv_free_index = self.free_index[riv_free_nodes]
		else:
			riv_free_nodes = np.zeros(0, dtype=int)
			riv_free_stage = np.zeros(0, dtype=float)
			riv_free_coeff = np.zeros(0, dtype=float)
			riv_free_index = np.zeros(0, dtype=int)

		if has_lakes:
			lks_reduce_idx = np.append([0], np.cumsum(sizes_lks)[:-1])

		for inner_iter in range(self.implicit_max_iter):
			thickness_sat = np.array(thickness, dtype=float)
			thickness_sat[act_nodes] = update_saturated_thickness(
				head_iter[act_nodes], bottom[act_nodes], surface[act_nodes],
				thickness_sat[act_nodes], inodetype[act_nodes], method=self.method
			)
			thickness_sat[thickness_sat < 0] = 0.0

			head_trial = head_initial.copy()
			if n_free_nodes > 0:
				head_trial[self.free_nodes] = self._solve_implicit_free_heads(
					head_initial, head_iter, thickness_sat, recharge_volume_free,
					storage_coeff_free, riv_free_nodes, riv_free_index,
					riv_free_stage, riv_free_coeff, dt
				)

			np.maximum(head_trial, 0.0, out=head_trial)
			np.minimum(surface, head_trial, out=head_trial)
			if self.id_CHB is not None:
				head_trial[self.id_CHB] = self.bc_values

			if has_lakes:
				z_lks = np.repeat(head_trial[ids_max_depth_lks], sizes_lks)
				z_lks = np.where(z_lks >= bathymetry[ids_lks], z_lks, bathymetry[ids_lks])
				surface_i[ids_lks] = z_lks

			Net_Flux, qs_riv = self._compute_flux_terms(
				grid, thickness_sat, head_trial, recharge, Sy, dt,
				riv_nodes if has_river else None,
				riv_elevation, stage, conductivity
			)

			dqs.fill(0.0)
			dqs[act_nodes] = regularization_T(
				surface_i[act_nodes], head_trial[act_nodes],
				thickness[act_nodes], Net_Flux[act_nodes], REG_FACTOR
			)

			if has_lakes:
				wet_msk_lks = np.where(head_trial[ids_lks] >= bathymetry[ids_lks], 1, 0)
				dh_lks = (head_trial[ids_lks] - z_lks)*wet_msk_lks
				sum_dh_lks = np.add.reduceat(dh_lks, lks_reduce_idx)
				sum_wet_lks = np.add.reduceat(wet_msk_lks, lks_reduce_idx)
				avg_dh_lks = np.divide(
					sum_dh_lks, sum_wet_lks,
					out=np.zeros_like(sum_dh_lks),
					where=sum_wet_lks != 0
				)
				head_trial[ids_lks] = (
					head_trial[ids_lks]*(1 - wet_msk_lks)
					+ wet_msk_lks*(z_lks + np.repeat(avg_dh_lks, sizes_lks))
				)
				dqs[ids_lks] = dqs[ids_lks]*(1 - wet_msk_lks)

			water_storage_change.fill(0.0)
			water_storage_change[act_nodes] = (
				(Net_Flux[act_nodes] - dqs[act_nodes])*dt
			)
			total_storage_change = np.mean(water_storage_change[act_nodes])

			head_next = self._apply_soil_interaction(
				act_nodes, head_initial, water_storage_change,
				surface_act32, bathymetry_act32, bathy_minus_droot_act32,
				ones_act32, zeros_act32, theta_sat_act32,
				theta_fc_act32, theta_dt_act32, Sy_for_update_act32
			)
			np.maximum(head_next, 0.0, out=head_next)
			np.minimum(surface, head_next, out=head_next)
			if self.id_CHB is not None:
				head_next[self.id_CHB] = self.bc_values

			if np.max(np.abs(head_next[act_nodes] - head_iter[act_nodes])) <= self.implicit_tolerance:
				head_iter = head_next
				break

			head_iter = head_next

		head[:] = head_iter
		if has_river and qs_riv.size > 0:
			discharge[riv_nodes] += qs_riv*self.kaq[riv_nodes]*dt
		discharge[act_nodes] += dqs[act_nodes]*dt
		self.flux_at_CHB = self.flux_at_CHB/n_act_nodes

		try:
			MB = (
				np.mean(recharge[act_nodes])*dt - np.mean(discharge[act_nodes])
				- np.mean(total_storage_change) - self.flux_at_CHB*dt
			)
			assert np.allclose(MB, 0.0, rtol=1e-05, atol=1e-04)
		except:
			raise Exception('Groundwater Water balance Error: ', MB,
		   		'Please check units and non-data values: ',
				np.where(np.isnan(recharge[act_nodes]) | np.isinf(recharge[act_nodes])))

		return head, discharge

	def _solve_implicit_free_heads(self, head_initial, head_iter, thickness_sat,
			recharge_volume_free, storage_coeff_free, riv_free_nodes,
			riv_free_index, riv_free_stage, riv_free_coeff, dt):
		"""Assemble and solve the free-node backward-Euler system."""
		if len(self.free_nodes) == 0:
			return np.zeros(0, dtype=float)

		edge_g = self.edge_c_static*dt*0.5*(thickness_sat[self.edge_i] + thickness_sat[self.edge_j])
		diag = storage_coeff_free.copy()
		rhs = storage_coeff_free*head_initial[self.free_nodes] + recharge_volume_free

		if self.ff_edge_idx.size > 0:
			g_ff = edge_g[self.ff_edge_idx]
			diag += np.bincount(self.ff_i, weights=g_ff, minlength=len(self.free_nodes))
			diag += np.bincount(self.ff_j, weights=g_ff, minlength=len(self.free_nodes))
			offdiag_data = -np.concatenate((g_ff, g_ff))
		else:
			offdiag_data = np.zeros(0, dtype=float)

		if self.if_edge_idx.size > 0:
			g_if = edge_g[self.if_edge_idx]
			diag += np.bincount(self.if_free, weights=g_if, minlength=len(self.free_nodes))
			rhs += np.bincount(
				self.if_free,
				weights=g_if*head_initial[self.if_fixed_global],
				minlength=len(self.free_nodes)
			)

		if self.fi_edge_idx.size > 0:
			g_fi = edge_g[self.fi_edge_idx]
			diag += np.bincount(self.fi_free, weights=g_fi, minlength=len(self.free_nodes))
			rhs += np.bincount(
				self.fi_free,
				weights=g_fi*head_initial[self.fi_fixed_global],
				minlength=len(self.free_nodes)
			)

		if riv_free_nodes.size > 0:
			active_river = head_iter[riv_free_nodes] > riv_free_stage
			if np.any(active_river):
				idx = riv_free_index[active_river]
				coeff = riv_free_coeff[active_river]
				stage = riv_free_stage[active_river]
				diag += np.bincount(idx, weights=coeff, minlength=len(self.free_nodes))
				rhs += np.bincount(idx, weights=coeff*stage, minlength=len(self.free_nodes))

		rows = np.concatenate((np.arange(len(self.free_nodes)), self.ff_rows))
		cols = np.concatenate((np.arange(len(self.free_nodes)), self.ff_cols))
		data = np.concatenate((diag, offdiag_data))
		matrix = csr_matrix((data, (rows, cols)), shape=(len(self.free_nodes), len(self.free_nodes)))

		x0 = head_iter[self.free_nodes]
		solution, info = cg(
			matrix, rhs, x0=x0,
			tol=self.implicit_tolerance,
			#atol=0.0,
			maxiter=self.linear_max_iter
		)
		#print('CG solver info:', info, '\nsolution:', solution, '\nx0:', x0)
		if info != 0:
			solution = spsolve(matrix, rhs)

		return solution

	def _compute_flux_terms(self, grid, thickness_sat, head, recharge, Sy, dt,
			riv_nodes, riv_elevation, stage, conductivity):
		"""Compute vectorized net fluxes and river exchange for a trial head."""
		N_cells = grid['N_cells']
		inv_areas = 1.0/grid['Areas']
		I = grid['I']
		J = grid['J']

		thickness_interface = 0.5*(thickness_sat[I] + thickness_sat[J])
		Q_flow_i_to_j = self.C_static*thickness_interface*(head[I] - head[J])
		Net_Flux = -np.bincount(I, weights=Q_flow_i_to_j, minlength=N_cells)*inv_areas

		if self.id_CHB is not None:
			self.flux_at_CHB = Net_Flux[self.id_CHB].sum()

		Net_Flux += recharge#/dt
		qs_riv = np.zeros(0, dtype=float)
		if riv_nodes is not None and len(riv_nodes) > 0:
			riv_stage = riv_elevation[riv_nodes] + stage[riv_nodes]
			#head_diff = head[riv_nodes] - riv_stage
			#np.maximum(head_diff, 0.0, out=head_diff)
			#if np.ndim(conductivity) == 0:
			#	riv_cond = np.full(len(riv_nodes), conductivity, dtype=float)
			#else:
			#	riv_cond = conductivity[riv_nodes]
			#riv_storage_exact = np.maximum(
			#	grid['Areas'][riv_nodes]*Sy[riv_nodes],
			#	np.finfo(float).eps
			#)
			#with np.errstate(divide='ignore', invalid='ignore'):
			#	aux = np.log(head_diff) - riv_cond*dt/riv_storage_exact
			#head_diff_loss = head_diff - np.where(aux > 0.0, np.exp(aux), 0.0)
			#qs_riv = head_diff_loss*riv_storage_exact
			qs_riv = conductivity[riv_nodes] * np.maximum(head[riv_nodes] - riv_stage, 0.0)
			Net_Flux[riv_nodes] -= self.kaq[riv_nodes]*qs_riv

		return Net_Flux, qs_riv

	def _apply_soil_interaction(self, act_nodes, head_initial,
			water_storage_change, surface_act32, bathymetry_act32,
			bathy_minus_droot_act32, ones_act32, zeros_act32,
			theta_sat_act32, theta_fc_act32, theta_dt_act32,
			Sy_for_update_act32):
		"""Apply the existing Fortran soil connector to updated storage."""
		head_next = np.array(head_initial, dtype=float, copy=True)
		aux_head = np.asarray(head_next[act_nodes], np.float32)
		water_storage_change_act32 = np.asarray(
			water_storage_change[act_nodes], np.float32
		)
		lakes.uz_sz_interaction.update_soil(
			surface_act32,
			bathymetry_act32,
			bathy_minus_droot_act32,
			ones_act32,
			zeros_act32,
			zeros_act32,
			theta_sat_act32,
			theta_fc_act32,
			theta_dt_act32,
			water_storage_change_act32,
			Sy_for_update_act32,
			aux_head
		)
		head_next[act_nodes] = aux_head
		return head_next
	
# --- 2. PRE-CALCULATION OF STATIC CONDUCTANCE ---
def _precalculate_static_conductance(grid, Ksat):
	"""
	Calculates the static (non-head-dependent) part of the geometric conductance 
	using the harmonic mean for K, required for a heterogeneous medium.

	Formula: C_static = L_ij / (d_i/K_i + d_j/K_j)
	This remains correct and robust even for regular grids.
	"""
	
	# Hydraulic properties lookup for host (i) and neighbor (j) cells
	K_i = Ksat[grid['I']]
	K_j = Ksat[grid['J']]
	
	# Term 1: Harmonic mean K denominator (d_i/K_i + d_j/K_j)
	harmonic_denominator = grid['d_i'] / K_i + grid['d_j'] / K_j
	
	# C_static = L_ij / harmonic_denominator
	C_static = grid['L_ij'] / harmonic_denominator
	
	return C_static

def regularization_T(zm, hm, f, dq, r):
	"""regularization function for confined aquifers

	Parameters
	----------
	zm : float numpy array
		surface elevation
	hm : float numpy array
		hydraulic head
	f : float numpy array
		e-folding depth
	dq : float numpy array
		flux per unit area
	r : float numpy array
		regularization factor
	
	Returns
	-------
	float numpy array 
		regularization
	"""
	aux = (hm-zm)/f+1
	aux = np.where(aux > 0,aux,0)
	aux = np.where(aux > 1, 1, aux)
	return np.exp((aux-1)/r)*dq*np.where(dq > 0,1,0)

def exponential(f, z, h):
	"""Calculate aquifer transmissivity following
	Fan et. al. (2013)
	
	Parameters
	-----------
	Ksat:	Saturated hydraulic conductivity aquifer
	f:		effective aquifer depth
	z:		elevation at link (node average)
	h:		water table elevation
	Returns
	-------
	transmissivity
	"""
	
	return f*np.exp(-np.maximum(z-h, 0)/f)


def update_saturated_thickness(head, bottom, surface,
            thickness, inodetype, method=0):
	"""Update aquifer saturated thickness based on the selected method.
	Parameters 
	-----------
    head : numpy array
        water table [m]
    bottom : numpy array
        aquifer bottom elevation [m]
    surface:	numpy array
        Topograhic elevation [m]
    thickness :	numpy array
        effective aquifer depth [m]
    inodetype : numpy array
        aquifer type indicator

    Returns
    -------
    thickness_sat : numpy array
        updated saturated thickness [m]
    """
	# For method==0, tha saturated thickenss is constant
	if method == 0:
		# Saturated thickness become zero when head is below bottom
		thickness_aux = head - bottom
		thickness[thickness_aux < 0] = 0.0
	
	elif method == 1:
		# Saturated thickness for unconfined conditions
		thickness = head - bottom
	elif method == 2:
		# Saturated thickness for exponential dacay function
		thickness = exponential(thickness,
					surface-thickness,
					head)
	elif method == 3:
		# saturated thickness for multiaquifer conditions
		# update thikness for aquifers with linear transmissinity
		idnodes = np.where(inodetype == 1)
		thickness[idnodes] = head[idnodes] - bottom[idnodes]
		# updates thickness of aquiferes with exponential transmissivity
		idnodes = np.where(inodetype == 2)
		thickness[idnodes] = exponential(thickness[idnodes],
					surface[idnodes]-thickness[idnodes],
					head[idnodes])
		
	# check that that saturated thickness is not negative
	thickness[thickness < 0] = 0.0 

	return thickness

def time_step_confined(D, Sy, T, dx):
	"""Maximum time step for confined aquifers
	D:	Courant number
	"""
	dt = D*Sy*np.power(dx, 2)/(T)
	
	return np.nanmin(dt[dt > 0])

def get_maximim_time_step(Ksat, Sy, thickness, delta_x):
	"""Calculate maximum allowable time step based on Courant condition
	for confined aquifers.
	Parameters
	-----------
	delta_x : numpy array
		grid size [L]
	thickness : numpy array
		effective aquifer depth [m]
	Ksat : numpy array
		hydraulic conductivity [L/T]
	Sy : numpy array
		specific yield [-]

	Returns
	-------
	dt : float
		maximum allowable time step [T]

	"""
	# calculate maximum diffusivity
	Ksat_max = np.max(Ksat)
	id_ksat_max = np.argmax(Ksat)
	Sy_min = np.min(Sy)
	id_Sy_min = np.argmin(Sy)

	Sy_min = Sy[id_ksat_max]
	D_max_ksat = Ksat_max * thickness[id_ksat_max] / Sy[id_ksat_max]
	D_max_sy = Ksat[id_Sy_min] * thickness[id_Sy_min] / Sy_min
	D_max = max(D_max_ksat, D_max_sy)
	
	dt = (COURANT_2D * (delta_x**2).min() / D_max)

	return dt
