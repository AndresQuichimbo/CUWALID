
import os
import numpy as np
from landlab.grid.mappers import (
        map_link_head_node_to_link,
        map_link_tail_node_to_link,
		)

#import time
#Global variables
REG_FACTOR = 0.001 # Regularisation factor
COURANT_2D = 0.250 # Courant Number 2D flow
COURANT_1D = 0.50 # Courant number 1D flow
STR_RIVER = 0.00001 # Riverbed storage factor
# provisional
a_faq = 150
b_faq = 131
# ratio between vertical and horizontal Ksat
fkxy = 0.1
lakes_is_active = 0
class gwflow_EFD(object):
		
	def __init__(self, grid, surface, Ksat, area_river,
	      bc, method, fparameter=False):
		"""Initialize groundwater component

		Parameters
		----------
		grid:		landlab grid
		Ksat:		saturated hydraulic conductivity
		area_river:	area of river at river cells
		bc:			boundary conditions
		
		Returns
		------
		water table depth
		groundwater discharge
		flux boundary
		
		"""
		#grid_size = grid.shape[0]*grid.shape[1]
		
		# make boundaries close
		grid.status_at_node[grid.status_at_node == 1] = grid.BC_NODE_IS_CLOSED
		# Initialize the gw component
		if 'aux_grid' not in grid.at_node:
			grid.add_zeros('node', 'aux_grid', dtype=float)
		
		if bc is not None:
			self.id_CHB = np.where(bc != -9999)[0]
			if self.id_CHB.size > 0:
				#gw.at_node['water_table__elevation'][id_CHB] = gw.at_node['SZ_CHB'][id_CHB]
				grid.status_at_node[self.id_CHB] = grid.BC_NODE_IS_FIXED_VALUE
				self.ch_boundaries = bc[self.id_CHB]
			else:
				self.id_CHB = None
		else:
			self.id_CHB = None
		# create discharge array
		#self.discharge = np.zeros(grid_size)
		#print(grid)
		# calculate transmissivity at links
		# create link arrays for hydraulic conductivity
		grid.at_node['aux_grid'][:] = Ksat
		Ksath = map_link_tail_node_to_link(grid, 'aux_grid')
		Ksatt = map_link_head_node_to_link(grid, 'aux_grid')
		Ksatm = 0.5*(Ksath + Ksatt)
		self.Ksat = np.zeros(len(grid.length_of_link))
		self.Ksat[grid.active_links] = (Ksath[grid.active_links]*Ksatt[grid.active_links]
				/Ksatm[grid.active_links])
		#print(fparameter)
		# transmissivity factor
		self.fdhdl = None
		if fparameter is True:
			# if transmissivity factor is active calutate f
			if surface is not None:
				# if surface provided, calculate f
				grid.at_node['aux_grid'][:] = surface
				fdhdl = grid.calc_grad_at_link(grid.at_node['aux_grid'])
				fdhdl = np.abs(fdhdl)
				# specified the maximum surface variation to limit flow
				slope_factor = 200/grid.dx
				self.fdhdl = np.ones_like(fdhdl)
				self.fdhdl[fdhdl > slope_factor] = 0.0
				#self.fdhdl = fdhdl[:]
				#print(self.fdhdl[grid.active_links])
			
		
		self.method = method
		# calculate cell area
		self.A = np.power(grid.dx, 2)	
			
		# calcualte river factor to reduce number of calculations
		kriv = np.ones_like(area_river)
		kriv[area_river > 0] = 1/area_river[area_river > 0]
		self.kriv = kriv
			
		# calcualte aquifer-river factor to reduce calculations
		self.kaq = 1/self.A
	
		self.lakes_is_active = 0
		
		
	# run model under steady state
	def run_one_step_gw_SS(self, grid, surface, bottom, thickness,
		     Droot, riv_elevation, riv_nodes, conductivity, inodetype,
			 head, recharge, stage, dt):
		"""Function to update water table depending on the
		unsaturated zone.
		
		Parameters
		-----------
		Droot:		Rooting depth [mm]
		tht_dt:		Water content at time t [-]
		Duz:		Unsaturated zone depth [m]
		surface:	Topograhic elevation [m]
		head:		water table [m]
		theta_sat:	Saturated water content [-]
		theta_fv:	Field capacity [-]
		Sy:			Specific yield [-]
		dq:			water storage anomaly [m]
		thickness:	effective aquifer depth [m]
		SS_loss:	transmission losses [m3 h-1]
		
		Returns
		------
		Groundwater storage variation [m]
		water table elevation [m]
		groundwater discharge [m]
		"""
		# Calculate time step ---------------------------------------------------
		#print('===============================================================')
		# select active link of model domain
		act_links = grid.active_links[:]
		act_nodes = np.array(grid.core_nodes, dtype=int)
		
		# initialize arrays
		#water_storage_change[:] = 0.0
		discharge = np.zeros_like(surface)
		dqs = np.zeros_like(surface)
		#thickness_sat = np.zeros_like(thickness, dtype=float)
		
		fluxes = np.zeros_like(thickness)
		
		#thickness_sat[act_nodes] = thickness[act_nodes]
		thickness_sat = np.array(thickness, dtype=float)
		if self.method == 1:
			thickness_sat[act_nodes] = head[act_nodes] - bottom[act_nodes]
		elif self.method == 2:
			thickness_sat[act_nodes] = exponential(thickness[act_nodes],
						surface[act_nodes]-Droot[act_nodes],
						head[act_nodes])
		elif self.method == 3:
			# update thikness for aquifers with linear transmissinity
			idnodes = np.where(inodetype == 3)[0]
			#print(idnodes)
			thickness_sat[idnodes] = head[idnodes] - bottom[idnodes]
			# updates thickness of aquiferes with exponential transmissivity
			idnodes = np.where(inodetype == 1)[0]
			thickness_sat[idnodes] = exponential(thickness[idnodes],
								surface[idnodes]-Droot[idnodes],
								head[idnodes])
			#print(thickness_sat_aux)
		#print(thickness[act_nodes])
		#self.flux_out = 0.0		
		#stage = env_state.grid.at_node['Q_ini'] * self.kriv	*0.0
		#print(len(riv_nodes))
		if len(riv_nodes) > 0:
			#print(head)
			aux_riv = np.ones_like(riv_nodes)
			aux_riv[stage[riv_nodes] > 0] = 0.0
			head = np.minimum(surface, head)
			#print(head)
		# adjusting head at the surface of the model domain
		# WARNING! this could lead to increases in mass balance errors
		#if env_state.func == 2:
		#	env_state.SZgrid.at_node['water_table__elevation'][:] = np.maximum(
		#		env_state.SZgrid.at_node['water_table__elevation'],
		#		env_state.SZgrid.at_node['BOT']
		#		)
		
		# Make river water table always below or equal surface elevation
		#self.hriv = np.minimum(self.hriv,
		#	riv_elevation
		#	)
		#print(164,head)
		if self.id_CHB is not None:
			head[self.id_CHB] = self.ch_boundaries
		#print(167,head)
		# calculate aquifer saturated thickness at nodes
		# for models with exponential function assign effective depth
		# skip this for first iiteration
		
		# check that that saturated thickness is not negative
		#(thickness_sat[act_nodes])[thickness_sat[act_nodes] < 0] = 0
		thickness_sat[thickness_sat < 0] = 0
		#print(thickness_sat)
		
		# map mean values of thickness at node to links
		grid.at_node['aux_grid'][:] = thickness_sat[:]
		thickness_link = map_link_head_node_to_link(grid, 'aux_grid')
		aux_t = map_link_tail_node_to_link(grid, 'aux_grid')
		thickness_link = 0.5*(aux_t+thickness_link)
		T = np.zeros_like(self.Ksat)
		
		# calculate transmissivity            
		if self.fdhdl is None:
			T[act_links] = self.Ksat[act_links]*thickness_link[act_links]
		else:
			T[act_links] = (self.Ksat[act_links]
		   					*thickness_link[act_links]
							*self.fdhdl[act_links])
		
		#print(head)	
		# Calculate the hydraulic gradients
		grid.at_node['aux_grid'][:] = head[:]#np.array(head[:])
		#print(grid.at_node)
		dhdl = grid.calc_grad_at_link(grid.at_node['aux_grid'])
		#print(dhdl)
		# Calculate flux per unit length at each face
		qs = np.zeros_like(self.Ksat)
		qs[act_links] = -T[act_links]*dhdl[act_links]
		
		# calculate total flux at constant head boundary condition cells
		# units are m per time step
		#if self.act_fix_link == 1:
		#	self.flux_out += (np.sum(qs[self.fixed_links])
		#					/grid.dx)*dtsp
		#print(200,head)	
		# Add flux at boundary conditions
		#dfhbc = env_state.SZgrid.at_node['SZ_FHB']
		#print(len(act_node))
		# save flux boundary condition as average for the whole basin domain
		# units are in m per time step
		#self.flux_out += np.mean(dfhbc[act_node])*dtsp
		#print(self.flux_out)
		# Calculate flux gradient
		dqsdxy = (-grid.calc_flux_div_at_node(qs)#- dfhbc 
				+ recharge/dt)
		#print(type(riv_nodes))
		#print(head)
		# if river cells available, caluculate the flux accorss the channel
		if len(riv_nodes) > 0:
			# Calculate channel cell conductivity
			hriv = np.minimum(head[riv_nodes],
				riv_elevation[riv_nodes]+stage[riv_nodes])
				
			Tch = np.zeros_like(riv_nodes)
			#Tch = (conductivity[riv_nodes]*exponential(
			#	STR_RIVER,	riv_elevation[riv_nodes],
			#	hriv[riv_nodes]))
			head_diff = head[riv_nodes] - hriv
			
			head_diff[head_diff < 0] = 0
			#stage_aux = stage[riv_nodes]
			#stage_aux[diff_stage < 0.0] = 0.0
						
			# Calculate river cell flux [m3 h-1]
			qs_riv = np.zeros_like(riv_nodes)
			qs_riv = (conductivity[riv_nodes]*
				head_diff)#*self.C_factor)
				#(diff_stage-stage_aux)*self.C_factor)
			
			#qs_riv[qs_riv < 0.0] = qs_riv[qs_riv < 0.0]*aux_riv[qs_riv < 0.0]
			
			# Regularization approach for river cells
			#dqs_riv = np.zeros_like(riv_nodes)
			#dqs_riv = regularization_T(riv_elevation, self.hriv,
			#	self.f[riv_nodes], -qs_riv, REG_FACTOR
			#	)
			
			# add river out/inflow to the mass balance
			# change river flow units m3 -> m
			#dqsdxy[riv_nodes] += -self.kaq*dqs_riv
			dqsdxy[riv_nodes] += -self.kaq*qs_riv
		
		# Regularization approach for aquifer cells
		# calculate aquifer thickness
		
		#if env_state.func == 1 or  env_state.func == 2:
		dqs[act_nodes] = regularization_T(surface[act_nodes], head[act_nodes],
			thickness[act_nodes], dqsdxy[act_nodes], REG_FACTOR)
		
		if len(riv_nodes) > 0:
			fluxes[riv_nodes] += -self.kaq*qs_riv

		# Calculate storage change			
		fluxes[act_nodes] = -dqs[act_nodes] + recharge[act_nodes]
		
		# update transmissivity
		self.T = T

		# calculate fluxes
		self.fluxes = fluxes*self.A
		
		# adjusting head at the surface of the model domain
		# WARNING! this could lead to increases in mass balance errors
		#grid.at_node['water_table__elevation'][:] = np.minimum(
		#head = np.minimum(surface, head)

		#print(head)#self.head = hea

 
def regularization(zm, hm, bm, dq, r):
	"""regularization function for unconfined

	Parameters
	----------
	zm : float numpy array
		surface elevation
	hm : float numpy array
		hydraulic head
	bm : float numpy array
		bottom elevation aquifer
	dq : float numpy array
		flux per unit area
	r :	float numpy array
		regularization factor

	Returns
	-------
	float
		regularization factor
	"""
	aux = (hm-bm)/(zm-bm)
	aux = np.where((aux-1) > 0, 1, aux)
	return np.exp((aux-1)/r)*dq*np.where(dq > 0, 1, 0)


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
	return np.exp((aux-1)/r)*dq*np.where(dq > 0,1,0)
	
def exponential_T(Ksat, f, z, h):
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
	float numpy array
		transmissivity
	"""
	
	return Ksat*f*np.exp(-np.maximum(z-h, 0)/f)

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
	#print(f*np.exp(-np.maximum(z-h, 0)/f))
	return f*np.exp(-np.maximum(z-h, 0)/f)
