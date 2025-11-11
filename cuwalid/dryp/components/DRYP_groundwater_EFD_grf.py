# -*- coding: utf-8 -*-
import numpy as np
import cuwalid.dryp.components.lakesf90 as lakes

REG_FACTOR = 0.001  # Regularization factor for confined aquifers
COURANT_2D = 0.50 # Courant Number 2D flow

# --- 1. GROUNDWATER FLOW SOLVER CLASS ---
class gwflow_solver_grs(object):
	"""Module for solving 2D Unsteady Dupuit-Forchheimer Equation in Polar Coordinates
	using a highly efficient Vectorized Explicit Finite Difference Method (FDM).
	"""

	def __init__(self, grid, Ksat, area_river, bc, method):
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
		self.area_river = area_river
		self.bc = bc
		self.method = method
		
		# Pre-calculated static conductance array (length = N_connections)
		self.C_static = _precalculate_static_conductance(grid)




		



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
		thickness_sat = np.array(thickness, dtype=float)

		N_cells = grid['N_cells']

		# Array lookups for connections
		I = grid['I']
		J = grid['J']

		# Apply initial fixed boundary conditions (if provided)
		if h_BC_mask is not None:
			h[h_BC_mask] = h_BC_value
			# Ensure that BC nodes are not updated by the flux calculation
			Sy_for_update = grid['Sy'].copy()
			Sy_for_update[h_BC_mask] = np.inf # Effectively sets update term to zero
		else:
			Sy_for_update = grid['Sy']
	
		# Calculate the per-cell update factor (dt / (Sy * Area))
		Update_Factor = dt / (Sy_for_update * grid['Areas'])
	
		# Store history every 1000 steps
		store_interval = 1000
		h_history = [h.copy()]
	
		# Stability Check Warning (Based on maximum diffusivity)
		D_max = np.max(grid['K']) * head / np.min(grid['Sy'])
	
		dt = (COURANT_2D * (grid['Dx_cell']**2).min() / D_max)

		while dtp > dt:
			h_prev = h.copy()

			# calculate aquifer saturated thickness at nodes
			# for models with exponential function assign effective depth
			# skip this for first iiteration
			
			if inner_iter > 0:
				thickness_sat[act_nodes] = update_saturated_thickness(head, bottom,
														  surface, thickness, inodetype, method=self.method)
			
			# 1. Calculate Transmissivity at the Interface (T_ij^k = K_avg * h_avg)    
			# Head at interface (Arithmetic Mean): h_avg = (h_i + h_j) / 2
			h_i = head[I]
			h_j = head[J]
			thickness_sat_i = thickness_sat[I]
			thickness_sat_j = thickness_sat[J]
	
			h_interface = 0.5 * (h_i + h_j)
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
			Total_Flux_Out = np.bincount(I, weights=Q_flow_i_to_j, minlength=N_cells)
	
			# Flux entering cell I (Inflow, must be added): Q_flow_i_to_j where J is the host
			Total_Flux_In = np.bincount(J, weights=Q_flow_i_to_j, minlength=N_cells)
	
			# Net flux into cell I = Inflow - Outflow
			Net_Flux = Total_Flux_In - Total_Flux_Out
			
			# add river component
			if riv_nodes.size > 0:
				for riv_node in riv_nodes:
					# Calculate head difference between aquifer and river stage
					head_diff = h_prev[riv_node] - riv_elevation[riv_node]
					if head_diff > 0:
						# Outflow from aquifer to river
						Q_river = conductivity[riv_node] * head_diff
						Net_Flux[riv_node] -= Q_river
						
			if ids_lks is not None:
				# create a mask of wet cell lakes
				wet_msk_lks = np.where(head[ids_lks] >= bathymetry[ids_lks], 1, 0)
				#print('wet', wet_msk_lks)
				# Calculate anomaly in water table depth at lake nodes
				dh_lks = head[ids_lks] - z_lks
				#print('dh_lks', dh_lks)
				# Mask out dry cell lakes (dry cells become zero)
				dh_lks = dh_lks*wet_msk_lks
				#print('dh_lks_masked', dh_lks)
				#print('size', ids_lks)
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
				
				# modify storage change at lake nodes
				# calculate the change in water storage at lake nodes
				# if storage chang eis positive, and seepage is positive, accumulate the seepage to
				# the water storage change at lake nodes
				Net_Flux[ids_lks] = Net_Flux[ids_lks]*(1-wet_msk_lks)# + wet_msk_lks*avg_dh_lks

			# 3. Final Explicit Update    
			# Change in head = (dt / (Sy * Area)) * [Net_Flux + Recharge]
			dh = Update_Factor * (Net_Flux + recharge * grid['Areas'])
			
			# 4. Regularization
			# calculate regularization for aquifer cells
			dhs = regularization_T(surface, h_prev,
				h_interface, dh, REG_FACTOR)
			dh = dh - dhs # total change in head after regularization (TWSA)
			
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
				np.array(Sy[act_nodes], np.float32),#Sy
				aux_head
				)
			
            # asign updated values of aquifer heads to the groundwater object
			head[act_nodes] = aux_head

			# and Apply Updates
			h = h_prev + dh

			# Apply boundary condition reset (fixed head nodes must not change)
			if h_BC_mask is not None:
				h[h_BC_mask] = h_BC_value
	
			# Physical constraint: Head cannot be negative
			h = np.maximum(h, 0.0) 
	
		return h
	
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
