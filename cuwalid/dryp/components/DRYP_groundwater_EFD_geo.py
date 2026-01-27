# -*- coding: utf-8 -*-
import numpy as np
import cuwalid.dryp.components.lakesf90 as lakes
from cuwalid.dryp.components.DRYP_io import _compute_inactive_links

REG_FACTOR = 0.001  # Regularization factor for confined aquifers
COURANT_2D = 0.50 # Courant Number 2D flow

# --- 1. GROUNDWATER FLOW SOLVER CLASS ---
class gwflow_EFD(object):
	"""Module for solving 2D Unsteady Dupuit-Forchheimer Equation in Polar Coordinates
	using a highly efficient Vectorized Explicit Finite Difference Method (FDM).
	"""

	def __init__(self, grid, Ksat, area_river, bc, method=0):
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

		self.method = method

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
		
		# set up boundary conditions
		self.id_CHB = None
		if bc is not None:
			self.id_CHB = np.where(bc != -9999)[0]
			if self.id_CHB.size > 0:
				self.bc = bc[self.id_CHB]
			else:
				self.id_CHB = None

		# get active nodes array
		# create provisional domain for active nodes
		inodetype = np.zeros(grid['N_cells'])
		inodetype[grid['core_nodes']] = 1  # mark active nodes
		if self.id_CHB is not None:
			inodetype[self.id_CHB] = 2  # mark constant head boundary nodes
		
		self.act_nodes = inodetype

		# get inactive links from grid object
		inactive_links, _ = _compute_inactive_links(grid, inodetype)
		
		# Pre-calculated static conductance array (length = N_connections)
		self.C_static = _precalculate_static_conductance(grid, Ksat)

		# update pre-calculated inactive links in grid
		self.C_static[inactive_links] = 0.0
	
		# calculate cell area
		A = grid['Areas']	
			
		# calcualte river factor to reduce number of calculations
		kriv = np.ones_like(area_river)
		kriv[area_river > 0] = 1/area_river[area_river > 0]
		self.kriv = kriv

		# calcualte aquifer-river factor to reduce calculations
		self.kaq = 1/A

		pass

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
		# get number of cells
		N_cells = grid['N_cells']

		# Array lookups for connections
		I = grid['I']
		J = grid['J']

		# create dynamic surface elevation to handle lakes
		surface_i = surface.copy()

		# number of active nodes
		act_nodes = np.where(self.act_nodes > 0)[0]

		# initialize discharge
		discharge = np.zeros_like(surface, dtype=float)
		
		# initialize seepage
		dqs = np.zeros_like(surface, dtype=float)
		
		# initialize water storage change
		water_storage_change = np.zeros_like(thickness, dtype=float)
		
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

		# flux at constant head boundary
		self.flux_at_CHB = 0.0

		# Apply initial fixed boundary conditions (if provided)
		if self.bc is not None:
			head[self.id_CHB] = self.bc
			# Ensure that BC nodes are not updated by the flux calculation
			Sy_for_update = Sy.copy()
			Sy_for_update[self.id_CHB] = np.inf # Effectively sets update term to zero
		else:
			Sy_for_update = Sy
	
		## Calculate the per-cell update factor (dt / (Sy * Area))
		#Update_Factor = dt / (Sy_for_update * grid['Areas'])
	
		# calculate maximum allowable time step based on Courant condition
		dts = get_maximim_time_step(self.Ksat[act_nodes], Sy[act_nodes],
							  thickness[act_nodes], grid['Dx_cell'][act_nodes])

		# Calculate minimal time step		
		dtp = np.nanmin([dt, dts])		
		dtsp = dtp

		# inner iteration counter
		inner_iter = 0

		while dtp <= dt:
			# adjusting heads at the bottom of the model domain
			# WARNING! this could lead to increases in mass balance errors
			head = np.minimum(surface, head)
			
			# calculate aquifer saturated thickness at nodes
			# for models with exponential function assign effective depth
			# skip this for first iiteration
			if inner_iter > 0:
				thickness_sat[act_nodes] = update_saturated_thickness(head,
											bottom, surface, thickness,
											inodetype, method=self.method
											)

				if self.id_CHB is not None:
				#self.ch_boundaries = bc[self.id_CHB]
					head[self.id_CHB] = self.bc[self.id_CHB]

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
			if ids_lks is not None:
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
			Net_Flux = -Net_Flux/grid['Areas'] + recharge/dt

			# add river component
			if len(riv_nodes) > 0:
				# Calculate channel cell conductivity
				hriv = np.minimum(head[riv_nodes],
					riv_elevation[riv_nodes]+stage[riv_nodes])

				# Calculate head difference between aquifer and river stage
				head_diff = head[riv_nodes] - hriv
				head_diff[head_diff < 0] = 0
							
				# Calculate river cell flux [m3 h-1]
				qs_riv = np.zeros_like(riv_nodes, dtype=float)
				qs_riv = (conductivity[riv_nodes]*head_diff)
				#print(len(riv_nodes), 'qs_riv', len(qs_riv))
				# add river out/inflow to the mass balance [depth/time]
				# change river flow units m3 -> m
				#print('Net_Flux before riv', Net_Flux, len(Net_Flux))
				#print('riv_nodes', riv_nodes, len(riv_nodes))
				Net_Flux[riv_nodes] += -self.kaq[riv_nodes]*qs_riv

			
			# 3. REGULARIZATION APPROACH **************************
			# calculate regularization for aquifer cells
			# check if lakes are active
			if ids_lks is not None:
				surface_i[ids_lks] = z_lks

			# calculate regularization for aquifer cells
			dqs[act_nodes] = regularization_T(surface_i[act_nodes], head[act_nodes],
				thickness[act_nodes], Net_Flux[act_nodes], REG_FACTOR)
		
			# 4. handle lakes at lake nodes
			if ids_lks is not None:
				# create a mask of wet cell lakes
				wet_msk_lks = np.where(head[ids_lks] >= bathymetry[ids_lks], 1, 0)
				# Calculate anomaly in water table depth at lake nodes
				dh_lks = head[ids_lks] - z_lks
				# Mask out dry cell lakes (dry cells become zero)
				dh_lks = dh_lks*wet_msk_lks
				# redistribute the water table depth anomaly to the links at lake nodes
				# calculate the sum of water table depth anomaly at lake nodes
				sum_dh_lks = np.add.reduceat(dh_lks, np.append([0], np.cumsum(sizes_lks)[:-1]))
				# count the number of wet cells in each lake
				sum_wet_lks = np.add.reduceat(wet_msk_lks, np.append([0], np.cumsum(sizes_lks)[:-1]))
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
			aux_head = np.array(head[act_nodes], np.float32)
			lakes.uz_sz_interaction.update_soil(
				np.array(surface[act_nodes], np.float32),# surface elev
				np.array(bathymetry[act_nodes], np.float32),# bottom elev. upper layer
				np.array(bathymetry[act_nodes]-Droot[act_nodes], np.float32), # bottom elev. lower layer
				np.ones(len(act_nodes), np.float32),# specifiy yield upper layer (always 1 for lakes)
				np.zeros(len(act_nodes), np.float32), # field capacity (always zero for lakes)
				np.zeros(len(act_nodes), np.float32),# water content (alwas zero for lakes)
				np.array(theta_sat[act_nodes], np.float32),#tht_sat
				np.array(theta_fc[act_nodes], np.float32),#tht_fc
				np.array(theta_dt[act_nodes], np.float32),#tht_dt
				np.array(water_storage_change[act_nodes], np.float32),#dS
				np.array(Sy_for_update[act_nodes], np.float32),#Sy
				aux_head
				)

            # asign updated values of aquifer heads to the groundwater object
			head[act_nodes] = aux_head

			# accumulate discharge
			if len(riv_nodes) > 0:
				discharge[riv_nodes] += qs_riv*self.kaq[riv_nodes]*dtsp

			discharge[act_nodes] += dqs[act_nodes]*dtsp

			# Apply boundary condition reset (fixed head nodes must not change)
			if self.bc is not None:
				head[self.id_CHB] = self.bc
	
			# Physical constraint: Head cannot be negative
			head = np.maximum(head, 0.0)

			# adjusting head at the surface of the model domain
			# WARNING! this could lead to increases in mass balance errors
			head = np.minimum(surface, head)

			# calculate new time step based on Courant condition
			dtsp = get_maximim_time_step(self.Ksat[act_nodes], Sy[act_nodes],
				thickness_sat[act_nodes], grid['Dx_cell'][act_nodes])
			
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
		self.flux_at_CHB = self.flux_at_CHB/len(act_nodes)
		# check calculate water balance of the groundwater component
		#print(np.mean(recharge[act_nodes]), np.mean(discharge[act_nodes]),
		#		np.mean(total_storage_change), self.flux_at_CHB)
		try:
			MB = (np.mean(recharge[act_nodes]) - np.mean(discharge[act_nodes])
				 - np.mean(total_storage_change) - self.flux_at_CHB)
			#print(MB)
			assert np.allclose(MB, 0.0, rtol=1e-05, atol=1e-04)
		except:
			raise Exception(MB,'Groundwater Water balance Error: '
		   		'Please check units and non-data values')

		return head, discharge
	
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
