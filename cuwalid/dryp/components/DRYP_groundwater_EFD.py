# -*- coding: utf-8 -*-
import numpy as np
from landlab.grid.mappers import (
        map_link_head_node_to_link,
        map_link_tail_node_to_link,
		map_max_of_node_links_to_node)

#from components.DRYP_GW_SW_conector import update_soil
from cuwalid.dryp.components.DRYP_GW_SW_conector import update_soil
import cuwalid.dryp.components.lakesf90 as lakes

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
	"""Groundwater component. It uses an explicit approach to solve the
	diffuse flow equation. It assumes only one layer and in a
	Dupuit-Forchhheimer flow approach
	
	Attributes
	----------
	flux_at_CHB : numpy array
		flux at boundary condition [m/dt]
	
	"""
		
	def __init__(self, grid, Ksat, area_river, bc, method):
		"""Initialize groundwater component

		Parameters
		----------
		grid:	landlab grid
			model domain grid
		Ksat:	numpy array
			saturated hydraulic conductivity [m/h]
		area_river:	numpy array
			area of river at river cells [m2]
		bc:	numpy array
			boundary conditions 
		
		Returns
		-------
		head : numpy array
			water table head [m]
		discharge : numpy array
			groundwater discharge (baseflow) [m]
		
		"""
		# make boundaries close
		grid.status_at_node[grid.status_at_node == 1] = grid.BC_NODE_IS_CLOSED
		
		# Initialize the gw component
		if 'aux_grid' not in grid.at_node:
			grid.add_zeros('node', 'aux_grid', dtype=float)
		
		# Verify if head boundary conditions are provided
		if bc is not None:
			self.id_CHB = np.where(bc != -9999)[0]
			if self.id_CHB.size > 0:
				grid.status_at_node[self.id_CHB] = grid.BC_NODE_IS_FIXED_VALUE
				self.ch_boundaries = bc[self.id_CHB]
			else:
				self.id_CHB = None
		else:
			self.id_CHB = None
		
		# calculate transmissivity at links
		# create link arrays for hydraulic conductivity
		grid.at_node['aux_grid'][:] = Ksat
		Ksath = map_link_tail_node_to_link(grid, 'aux_grid')
		Ksatt = map_link_head_node_to_link(grid, 'aux_grid')
		Ksatm = 0.5*(Ksath + Ksatt)
		self.Ksat = np.zeros(len(grid.length_of_link))
		self.Ksat[grid.active_links] = (Ksath[grid.active_links]*Ksatt[grid.active_links]
				/Ksatm[grid.active_links])
			
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
		#print('Change approach in setting_file: line 26')
		#	print('************************************************************')
		
		# calculate cell area
		A = np.power(grid.dx, 2)	
			
		# calcualte river factor to reduce number of calculations
		kriv = np.ones_like(area_river)
		kriv[area_river > 0] = 1/area_river[area_river > 0]
		self.kriv = kriv
			
		# calcualte aquifer-river factor to reduce calculations
		self.kaq = 1/A
			
		# Add a second layer for groundwater 
		#if data_in.run_GW > 1:
		#	# Saturated thickness confined conditions
		#	env_state.SZgrid.add_zeros('node', 'Vb', dtype=float)
		#	
		#	self.Vb = (env_state.SZgrid.at_node['BOT']
		#		-env_state.SZgrid.at_node['BOTb'])
		#	
		#	# Calulate specfic storage (storativity)
		#	env_state.SZgrid.at_node['Ss_2'][:] = (env_state.SZgrid.at_node['Ss_2']
		#		* self.Vb)
		#	
		#	act_links = env_state.SZgrid.active_links		
		#	Kmax = map_max_of_link_nodes_to_link(env_state.SZgrid, 'Ksat_2')		
		#	Kmin = map_min_of_link_nodes_to_link(env_state.SZgrid, 'Ksat_2')		
		#	Ksl = map_mean_of_link_nodes_to_link(env_state.SZgrid, 'Ksat_2')
		#	
		#	self.Ksat_2 = np.zeros_like(Ksl)		
		#	self.Ksat_2[act_links] = Kmax[act_links]*Kmin[act_links]/Ksl[act_links]		
	
		#self.lakes_is_active = data_in.lakes
		self.lakes_is_active = 1
		self.flux_at_CHB = 0.0
		
	#@profile
	def run_one_step_gw(self, grid, surface, bottom, thickness,
		     bathymetry, riv_elevation, riv_nodes, Sy, Droot,
			 conductivity, inodetype, theta_sat, theta_fc, theta_dt,
			 head, recharge, stage, dt,
			 ids_lks=None, sizes_lks=None, ids_max_depth_lks=None
			 ):
		"""Function to update water table depending on the
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
		# Calculate time step ---------------------------------------------------
		#print('===============================================================')
		# create a copy of the surface elevation
		surface_i = surface.copy()
		
		# select active link of model domain
		act_links = grid.active_links[:]
		# select active nodes
		act_nodes = np.array(grid.core_nodes, dtype=int)
		# select links at constant head boundary conditions
		if self.id_CHB is not None:			
				links_at_CHB = grid.links_at_node[
					grid.open_boundary_nodes]
		
		# initialize arrays
		# initialize discharge
		discharge = np.zeros_like(surface, dtype=float)
		# initialize seepage
		dqs = np.zeros_like(surface, dtype=float)
		# initialize water storage change
		water_storage_change = np.zeros_like(thickness, dtype=float)
		# initialize saturated thinckess
		thickness_sat = np.array(thickness, dtype=float)
		
		# cange in total storage at the end of the time step
		total_storage_change = 0.0#np.zeros(len(act_nodes), dtype=float)

		# flux at constant head boundary
		self.flux_at_CHB = 0.0
		
		# calculate saturated thickness
		if self.method == 1:
			thickness_sat[act_nodes] = head[act_nodes] - bottom[act_nodes]
		elif self.method == 2:
			thickness_sat[act_nodes] = exponential(thickness[act_nodes],
						surface[act_nodes]-thickness[act_nodes],
						head[act_nodes])
		elif self.method == 3:
			# update thikness for aquifers with linear transmissinity
			idnodes = np.where(inodetype == 3)
			thickness_sat[idnodes] = head[idnodes] - bottom[idnodes]
			# updates thickness of aquiferes with exponential transmissivity
			idnodes = np.where(inodetype == 1)
			thickness_sat[idnodes] = exponential(thickness[idnodes],
								surface[idnodes]-thickness[idnodes],
								head[idnodes])
			
		# Calculate transmissivity
		# get ksat at nodes
		Ksat_node = map_max_of_node_links_to_node(grid, self.Ksat)
		# calculate transmissivity
		T_node = Ksat_node[act_nodes]*thickness_sat[act_nodes]
		
		# Calculate time step
		dts = time_step_confined(COURANT_2D, Sy[act_nodes],
			T_node, grid.dx)
					
		# Calculate minimal time step		
		dtp = np.nanmin([dt, dts])		
		dtsp = dtp
						
		#stage = env_state.grid.at_node['Q_ini'] * self.kriv	*0.0
		if len(riv_nodes) > 0:
			aux_riv = np.ones_like(riv_nodes)
			aux_riv[stage[riv_nodes] > 0] = 0.0
		
		ti = 0
		inner_iter = 0
		
		# loop until time step it reached
		while dtp <= dt:			
			#startTime = time.time()
			# adjusting heads at the bottom of the model domain
			# WARNING! this could lead to increases in mass balance errors
			head = np.minimum(surface, head)
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
			if self.id_CHB is not None:
				#self.ch_boundaries = bc[self.id_CHB]
				head[self.id_CHB] = self.ch_boundaries

			# calculate aquifer saturated thickness at nodes
			# for models with exponential function assign effective depth
			# skip this for first iiteration
			if inner_iter > 0:
				# For method==0, tha saturated thickenss is constant
				if self.method == 1:
					# Saturated thickness for unconfined conditions
					thickness_sat[act_nodes] = head[act_nodes] - bottom[act_nodes]
				elif self.method == 2:
					# Saturated thickness for exponential dacay function
					thickness_sat[act_nodes] = exponential(thickness[act_nodes],
								surface[act_nodes]-thickness[act_nodes],
								head[act_nodes])
				elif self.method == 3:
					# saturated thickness for multiaquifer conditions
					# update thikness for aquifers with linear transmissinity
					idnodes = np.where(inodetype == 1)
					thickness_sat[idnodes] = head[idnodes] - bottom[idnodes]
					# updates thickness of aquiferes with exponential transmissivity
					idnodes = np.where(inodetype == 2)
					thickness_sat[idnodes] = exponential(thickness[idnodes],
								surface[idnodes]-thickness[idnodes],
								head[idnodes])
			
			# check that that saturated thickness is not negative
			thickness_sat[thickness_sat < 0] = 0
			
			# map mean values of thickness at node to links
			grid.at_node['aux_grid'][:] = thickness_sat[:]
			thickness_link = map_link_head_node_to_link(grid, 'aux_grid')
			aux_t = map_link_tail_node_to_link(grid, 'aux_grid')
			thickness_link = 0.5*(aux_t+thickness_link)
			T = np.zeros_like(self.Ksat)
			
			# calculate transmissivity            
			T[act_links] = self.Ksat[act_links]*thickness_link[act_links]
			
			# LAKES
			###---------------------------------------------------------------
			### Additional requirements for lakes
			#print(ids_lks)# list of lake id nodes: ids_lks
			#print(sizes_lks)# list of number of cells per lake: sizes_lks 
			#print(ids_max_depth_lks)# list of lakes id maximum depths: ids_max_depth_lks

			# Check if lakes are active
			#if self.ids_lakes is not None:
			# Create an array of maximum lake depth
			if ids_lks is not None:
				z_lks = np.repeat(head[ids_max_depth_lks], sizes_lks)

				# Check if head is above the bottom elevation of the lakes
				z_lks = np.where(
					z_lks >= bathymetry[ids_lks], z_lks, bathymetry[ids_lks]
					#head[ids_lks] >= bathymetry[ids_lks], z_lks, bathymetry[ids_lks]
					)
				#print('head', head[27:36])
			#print('bathy', bathymetry[27:36])
			#print('stage',z_lks)
			# FIRST DISABLE THE FOLLOWING CODE BLOCK IF YOU ARE NOT USING LAKES
			# THERE IS NO NEED TO CHANGE THE TRANSMISIVITY AT LAKE NODES SINCE
			# LAKE STAGE VARIATION IS REDISTRIBUTED OVER THE WET LAKE CELLS
			###---------------------------------------------------------------
			### change transmisivity at lakes nodes and links
			### identify links at lake nodes that have water table depth above
			### the surface
			###aux_Tr = T.copy() # create a copy of transmissivity
			##
			##lake_nodes = head - bathymetry # find lake with water
			##
			##inner_lake_nodes = lake_nodes.reshape(
			##		grid.number_of_node_rows,
			##		grid.number_of_node_columns
			##		)
			##
			##inner_lake_nodes = np.where(
			##	shrink_region(inner_lake_nodes).reshape(-1) > 0)
			##
			###outer_lake_nodes = np.where(
			###	expand_region(inner_lake_nodes).reshape(-1) > 0)
			##
			##lake_nodes = np.where(lake_nodes > 0) # select lake nodes with water 
			###print(lake_nodes,len(lake_nodes))
			##links_at_lake = grid.links_at_node[lake_nodes] # select lake links
			##inner_links_at_lake = grid.links_at_node[inner_lake_nodes] # select lake links
			###outer_links_at_lake = grid.links_at_node[inner_lake_nodes] # select lake links
			##
			###T[outer_links_at_lake] = COURANT_2D*grid.dx*grid.dx*0.01 # reduce transmissivity
			###T[links_at_lake] = T[links_at_lake]*0.025 # reduce transmissivity
			###T[links_at_lake] = COURANT_2D*grid.dx*grid.dx*0.025 # reduce transmissivity
			##T[inner_links_at_lake] = COURANT_2D*grid.dx*grid.dx*0.05 # reduce transmissivity
			##
			###Sy_aux = Sy[act_nodes]
			##Sy_aux = Sy.copy()
			##Sy_aux[lake_nodes] = 1.0
			###Sy_aux[inner_lake_nodes] = 1.0
			###Sy_aux[outer_lake_nodes] = 1.0
			###print(Sy, Sy_aux)
			##

			# --------------------------------------------------------------
			# Calculate the hydraulic gradients
			grid.at_node['aux_grid'][:] = head[:]
			dhdl = grid.calc_grad_at_link(grid.at_node['aux_grid'])
			
			# Calculate flux per unit length at each face
			qs = np.zeros_like(self.Ksat)
			qs[act_links] = -T[act_links]*dhdl[act_links]
			
			# calculate total flux at constant head boundary condition cells
			# units are m per time step
			if self.id_CHB is not None:
				# select links at CHB nodes
				links_at_CHB = grid.links_at_node[self.id_CHB]
				# get link directions at CHB nodes
				link_dirs_at_CHB = grid.active_link_dirs_at_node[self.id_CHB]
				# get active links at CHB links
				active_links_at_CHB = links_at_CHB[link_dirs_at_CHB != 0]
				# get direction of active links
				active_link_dirs_at_CHB = link_dirs_at_CHB[link_dirs_at_CHB != 0]
				# calculate flux at CHB
				self.flux_at_CHB += (np.sum(qs[active_links_at_CHB]*
					active_link_dirs_at_CHB
					)/grid.dx)*dtsp
				
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
			#print('dqsdxy0', dqsdxy[27:36])
			#print('time step', dtsp)

			# CALCULATE FLUX AT RIVER CELLS*************************
			# check if river cells are available
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
				qs_riv = (conductivity[riv_nodes]*head_diff)
					#*self.C_factor)
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
			
			# REGULARIZATION APPROACH **************************
			# calculate regularization for aquifer cells
			# check if lakes are active
			if ids_lks is not None:
				surface_i[ids_lks] = z_lks
			# calculate regularization for aquifer cells
			dqs[act_nodes] = regularization_T(surface_i[act_nodes], head[act_nodes],
				thickness[act_nodes], dqsdxy[act_nodes], REG_FACTOR)
			#print('surface', surface_i[27:36])
			#print('dqs', dqs[27:36])
			#print('dqsdxy', dqsdxy[27:36])
			
			#print('head_no', head[27:36])
			# UPDATE HEAD AT LAKE NODES *************************
			# check if lakes are active
			# if not, skip this part
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
				#print('avg_dh_lks', avg_dh_lks)
				# assign maximum lake depth to the head at lake nodes
				#head[ids_lks] = z_lks + avg_dh_lks
				head[ids_lks] = head[ids_lks]*(1-wet_msk_lks) + wet_msk_lks*z_lks + avg_dh_lks

				# modify storage change at lake nodes
				# calculate the change in water storage at lake nodes
				# if storage chang eis positive, and seepage is positive, accumulate the seepage to
				# the water storage change at lake nodes
				dqs[ids_lks] = dqs[ids_lks]*(1-wet_msk_lks)# + wet_msk_lks*avg_dh_lks
				#print('dqs', dqs[27:36])
			#print('head_lks', head[27:36])
			
			# Calculate storage change			
			water_storage_change[act_nodes] = (dqsdxy[act_nodes]-dqs[act_nodes])*dtsp
			#print('water_storage_change', water_storage_change[27:36])
			
			# calculate total storage change to evaluate mass balance
			total_storage_change += np.mean(water_storage_change[act_nodes])
			
			
			# UPDATE HEAD AT ACTIVE NODES FOR SOIL-GW INTERACTIONS
			# enable lakes layer
			if self.lakes_is_active == 0:
				#print('No Lakes')
				# Update storage change for soil-gw interactions
				head[act_nodes] = (fun_update_UZ_SZ_depth(
					np.array(water_storage_change[act_nodes]),#dS
					np.array(head[act_nodes]),#h0
					np.array(theta_dt[act_nodes]),#tht_dt
					np.array(theta_sat[act_nodes]),#tht_sat
					np.array(theta_fc[act_nodes]),#tht_fc
					np.array(Sy[act_nodes]),#Sy
					np.array(surface[act_nodes] - Droot[act_nodes])
					))
			else:
				# Update storage change for soil-gw interactions
				run_fortran = True
				
				if run_fortran is True:
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
				else:
					#print('no fortran')
					# run python based-soil surface interaction (for testing)
					head[act_nodes] = (update_soil(
						surface[act_nodes],# surface elev
						bathymetry[act_nodes],# bottom elev. upper layer
						bathymetry[act_nodes]-Droot[act_nodes], # bottom elev. lower layer
						1,#np.ones(len(act_node), np.float32),
						0,#np.zeros(len(act_node), np.float32),
						0,#np.zeros(len(act_node), np.float32),# assuming lake conditons
						theta_sat[act_nodes], #tht_sat
						theta_fc[act_nodes], #tht_fc
						theta_dt[act_nodes], #tht_dt
						water_storage_change[act_nodes],#dS
						head[act_nodes],#h0
						Sy[act_nodes],#Sy
						))
			#print('head_uz', head[27:36])
			
			
			# accumulate discharge
			if len(riv_nodes) > 0:
				discharge[riv_nodes] += qs_riv*self.kaq*dtsp
				
			#print(type(dqs),discharge[act_nodes])
			discharge[act_nodes] += dqs[act_nodes]*dtsp
			#print('discharge',env_state.SZgrid.at_node['discharge'][219])
			# Calculate maximum time step
			dtsp = time_step_confined(COURANT_2D, Sy[act_nodes],
			#dtsp = time_step_confined(COURANT_2D, Sy_aux[act_nodes],
				map_max_of_node_links_to_node(grid, T)[act_nodes], grid.dx
				)
			
			#dtsp_riv = time_step_confined(COURANT_1D, env_state.SZgrid.at_node['SZ_Sy'],
			#			Tch/self.W, 0.02*(env_state.SZgrid.dx - self.W), env_state.riv_nodes)
			
			# adjusting head at the surface of the model domain
			# WARNING! this could lead to increases in mass balance errors
			#grid.at_node['water_table__elevation'][:] = np.minimum(
			head = np.minimum(surface, head) # time step could be very small
			#print('head_final', head[27:36])
			#print('head_final', head[ids_lks])
			#print("t", dtsp)
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
				
			inner_iter += 1
		
		# change discharge to model time step
		#env_state.SZgrid.at_node['discharge'][:] *= (1/self.dtSZ)
		
		# if water table is above the surface, make storage zero
		
		# estimate availble water storage of the aquifer
		
		# change time step of flux leaving the basin to model time step
		#if self.act_fix_link == 1:
		#	self.flux_out *= 1/self.dtSZ
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
		#print(inner_iter)
		#print(head)
		#print(v)
		return head, discharge

def transmissivity_multi_aquifer(Ksat, head, surface, thickness, aqtype, method):
	"""Calculate aquifer transmissivity
	
	Parameters
	-----------
	env_state:		environmental variables
	Ksat:			Saturated hydraulic conductivity aquifer
	act_links:		array of active links of SZ domain
	f:				effective aquifer depth
	zm:				surface elevation at link (node average)
    idlink:array of aquifer types
    method: specified if the different aquifers are located
	
	Returns
	-------
	T:				Transmissivity
	"""
	T = np.zeros_like(Ksat)
	
	# Calculate transmisivity for especific aquifer types
	if method == 1:
		# exponential transmissivity
		T = exponential(Ksat, thickness, surface, head)
	
	elif method == 2:
		# Constant transmissivity
		T = Ksat*thickness
	
	elif method == 3:
		#print(aqtype)
		# multi type aquifer
		# Type 1: exponential model
		if len(aqtype[0]) > 0:
			T[aqtype[0]] = exponential(Ksat[aqtype[0]],
						thickness[aqtype[0]], surface[aqtype[0]],
						head[aqtype[0]]
						)
		# Type 2: constant
		if len(aqtype[1]) > 0:
			T[aqtype[1]] = Ksat[aqtype[1]]*thickness
		
		# Type 3: linear relation with aquifer thickness
		if len(aqtype[2]) > 0:
			T[aqtype[2]] = Ksat[aqtype[2]]*(thickness[aqtype[2]])

		#print(T[act_links])
	else:
		# linear relation with aquifer thickness		
		T = Ksat*thickness
	#print(T[act_links])
	#print(act_links)
	
	return T

def fun_update_UZ_SZ_depth(dS, h0, tht_dt, tht_sat, tht_fc, Sy, zr):
	"""Function to update water table depending on both water content of
	the unsaturated zone.
	
	Parameters
	------
	dS:			water storage anomaly [m]
	h0:			initail water table [m]
	tht_dt:		water content at t0 [--]
	tht_sat:	water content at saturated conditions [--]
	tht_fc:		water content at field capacity [--]
	Sy:			specific yield [-]
	zr:			root zone elevation [m]
	
	Returns
	-------
	h:	updated water table
	"""	
	
	tht_dt = np.where(dS >= 0.0,
		tht_sat - tht_dt,
		tht_sat - tht_fc,
		)
	
	alpha = np.where(dS >= 0.0,
		1 - Sy/tht_dt,
		1 - tht_dt/Sy,
		)
	
	beta = np.where(dS >= 0.0,
		dS/tht_dt, dS/Sy
		)
	
	dSp = np.where(dS >= 0.0,
		(zr-h0)*Sy, tht_dt*(h0-zr)
		)
	
	dSp[dSp <= 0] = 0.0
	
	C = np.where(np.abs(dSp) < np.abs(dS), 0, 1)	
	alpha = np.where(np.abs(dSp) < np.abs(dS), alpha, 0)	
	beta = np.where(np.abs(dSp) < np.abs(dS), beta, 0)
	
	alpha = np.where(np.abs(dSp) == 0, 0, alpha)	
	beta = np.where(np.abs(dSp) == 0, 0, beta)
		
	D = np.where(h0 > zr, 0, 1)
	
	D = np.where(dS > 0, 0, D)
	
	C[np.abs(dSp) == 0] = 1.0
	
	gama = dS/tht_dt
	lambd = dS/Sy,
	
	# Update water table elevation
	h = h0 +(zr-h0)*alpha + beta + ((1-D)*gama + D*lambd)*C
	
	return h
	
def storage_uz_sz(surface, bathymetry, bottom, Droot, theta_sat,
		  Sy, head, theta, *two_layer):
	""" calculate the Total storage along the vertical
	profile of each model cell
	
	Parameters
	------
	surface:	surface elevation [m]
	bottom:		bottom elevation [m]
	bathymetry:	surface elevation of lakes [m] 
	Droot:		Rooting depth [mm]
	theta:		Water content at time t [-]
	head:		water table [m]
	theta_sat:	Saturated water content [-]
	Sy:			Specific yield [-]
	
	Returns
	-------
	total:		Volume of water stored in the saturated zone [mm]
	"""
	#print(theta)
	# water stored in lakes
	str_lakes = head - bathymetry
	str_lakes[str_lakes < 0.0] = 0.0

	# estimate saturated-unsaturated storage
	z_root = bathymetry - Droot
	str_usz = (head - str_lakes - z_root)
	str_usz[str_usz < 0] = 0.0
	
	# estimate storage water available in the unsaturated zone
	# estimate rooting depth storage
	str_uz = Droot - str_usz
	
	# estimate saturated storage
	str_sz = head - str_usz - str_lakes - bottom
		
	# total storage
	# total = storage in saturated zone
	# 		+ storage in unsaturated zone + storage in lakes
	total = (str_lakes
			+ str_uz*theta
			+ str_usz*theta_sat
			+ str_sz*Sy
			)
	
	#if two_layer[0] == 2:
	#
	#	# saturated thickness (unconfined)
	#	b = np.minimum(head_bottom, bottom)
	#		
	#	b = b - bottom_b
	#	
	#	# Storage from unconfined conditions
	#	b = b*Sy_b
	#	
	#	# Specific storage from confined conditions
	#	Ss = head_bottom - bottom
	#	
	#	Ss[Ss <= 0] = 0
	#	
	#	# Update storage in case of confined conditions
	#	b[Ss > 0] = 0
	#	
	#	# Update head for Specific storage
	#	Ss[Ss > 0] += (bottom[Ss > 0] - bottom_b[Ss > 0])
	#	
	#	# Water from confined store
	#	str_sz2l = Ss*Ss_b

	#	# storage second layer
	#	str_sz2l = b + str_sz2l
	#	total += str_sz2l
	#print(total[env_state.SZgrid.core_nodes])
	#print(np.mean(total[env_state.SZgrid.core_nodes])*1000)
	#return np.mean(total[env_state.SZgrid.core_nodes])
	return total*1000.0

def smoth_func_L1(h, hr, r, dq, *nodes):

	aux = np.power(h-hr, 3)/r	
	aux = np.where(aux > 0, aux, 0)
	aux = np.where(aux > 1, 1, aux)
	aux = np.where(dq > 0, 1, aux)
	
	if nodes:
		p = np.zeros_like(aux)
		p[nodes] = 1
		aux *= p
	
	return  aux
	
def smoth_func_L2(h, zb, D, r, *nodes):
	""" Reduce the hydraulic conductivity Ksat
	when the water table is close to the bottom of the layer
	
	Parameters
	----------
	h:	head elevation [m]
	hr:	bottom elevation [m]

	Returns
	------
	D:	distance for smoothing [m]
	r:	smoothing parameter [-]
	"""
	
	# calculate ration of smoothing
	u = (h-zb)/D
	#aux = (1-u)/r
	#
	u[u < 0] = 0
	u[u > 1] = 1
	#
	#FSy = 1 - np.exp(-aux)
	#FSs = 1 - np.exp(aux)
	#
	#FSy = np.where(u >= 1, 0, FSy)
	#FSs = np.where(u >= 1, FSs, 0)
	#	
	#if nodes:
	#	aux = np.zeros_like(aux)
	#	aux[nodes] = 1
	#	FSs *= aux
	#	FSy *= aux
	
	return  u

def river_flux(h, hriv, C, A, *nodes):
	q_riv = (h-hriv)*C/A
	if nodes:
		p = np.zeros_like(aux)
		p[nodes] = 1
		aux *= p
	return  q_riv

def smoth_func_T(h, hriv, r, f, dq, *nodes):
	SF = (h-hriv+f)/f
	SF = np.where(SF > 1, SF, 0)
	SF = np.where(SF > 0, 1 - np.exp(SF/r), 0)
	if nodes:
		p = np.zeros_like(SF)
		p[nodes] = 1
		SF *= p
	return SF

def smoth_func(h, hriv, r, dq, *nodes):
	aux = np.power(h-hriv, 3)/r	
	aux = np.where(aux > 0, aux, 0)
	aux = np.where(aux > 1, 1, aux)
	if nodes:
		p = np.zeros_like(aux)
		p[nodes] = 1
		aux *= p
	return  np.where(aux <= 0, 0, aux)
	
 
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


def time_step(D, Sy, Ksat, h, zb, dx, *nodes):
	""" Maximum time step for unconfined aquifers
	Parameters
	----------
	D:		Courant number
	Sy:		specific yield
	Ksat:	saturated hydraulic conductivity
	h:		water table elevation
	zb:		aquifer bottom elevation
	dx:		grid size
	nodes:	nodes at which the calculation will be applied
	"""
	T = (h - zb)*Ksat
	#print(T[nodes])
	dt = D*Sy*np.power(dx, 2)/(T)
	
	if nodes:		
		dt = np.nanmin((dt[nodes])[dt[nodes] > 0])
		#print('a',dt)
	else:
		dt = np.nanmin(dt[dt > 0])
	return dt

def time_step_confined(D, Sy, T, dx):
	"""Maximum time step for confined aquifers
	D:	Courant number
	"""
	dt = D*Sy*np.power(dx, 2)/(T)
	
	#dt = np.nanmin(dt[dt > 0])
	#return dt
	return np.nanmin(dt[dt > 0])

def shrink_region(array):
	"""
    Shrinks a binary region in a 2D array by removing 
    pixels around the regions.

    Parameters
	----------
    array:numpy array
		2D NumPy array of integers. 

    Returns
	-------
    	2D NumPy array with the shrunk region.

    This function first converts the input array to integers. 
    Then, it identifies and removes single-pixel protrusions 
    from the binary region represented by non-zero values 
    in the array. 
    """
	array = np.array(array, dtype=int)
	array[array < 0] = 0
	array[array > 0] = 1
	
	aux = array.copy()
	array[np.diff(aux, prepend=0, axis=1) == 1] = 0
	array[np.diff(aux, prepend=0, axis=0) == 1] = 0
	array[np.diff(aux, append=0, axis=0) == -1] = 0
	array[np.diff(aux, append=0, axis=1) == -1] = 0
	
	return array

def expand_region(array):
	"""
    Shrinks a binary region in a 2D array by removing 
    pixels around the regions.

    Parameters
	----------
    array:numpy array
		2D NumPy array of integers. 

    Returns
	-------
    	2D NumPy array with the shrunk region.

    This function first converts the input array to integers. 
    Then, it identifies and removes single-pixel protrusions 
    from the binary region represented by non-zero values 
    in the array. 
    """
	array = np.array(array, dtype=int)
	array[array < 0] = 0
	array[array > 0] = 1
	
	aux = array.copy()
	array[np.diff(aux, append=0, axis=1) == 1] = 1
	array[np.diff(aux, append=0, axis=0) == 1] = 1
	array[np.diff(aux, prepend=0, axis=0) == -1] = 1
	array[np.diff(aux, prepend=0, axis=1) == -1] = 1
	
	return array

class recharge_routing(object):
	def __init__(self, grid_size):
		"""Apply a damping effect ot the percolation
		Parameters
		------
		Returns
		-------
		"""
		self.Susz0 = np.zeros(grid_size)
		

	def run_recharge_routing(self, soil, R, Dusz):
		"""Apply a damping effect ot the percolation
		Parameters
		------
		soil:	lamda parameter
		Ksat: 	soil hydraulic conductivity
		R:		percolation 
		Dusz:	distance between the routing depth and the
				water table [m]
		Returns
		-------
		Qusz:	recharge []
		"""
		# update the storage of the unsaturated zone
		Susz = self.Susz0 + R
		
		# Maximum storage of the unsaturated zone
		Suszmax = Dusz*0.01#soil.theta_sat
		
		# flow velocity of through the unsaturated zone
		aux = np.zeros_like(Dusz)
		
		aux[Dusz > 0] = Susz[Dusz > 0]/Suszmax[Dusz > 0]
		
		v = soil.Ksat_uz*np.power(aux, soil.c_SOIL)
		
		aux = np.ones_like(Dusz)
		
		aux[Dusz > 0] = v[Dusz > 0]/Dusz[Dusz > 0]
		
		# calulate the inital flow
		Qusz0 = Susz*aux
				
		aux[Dusz <= 0] = 0
		
		# calculate the flow out of the unsaturated zone
		Qusz = Qusz0*(1-np.exp(-aux))
		
		aux = np.ones_like(Dusz)
		aux[v > 0] = Dusz[v > 0]/v[v > 0]
		Qusz = Qusz*aux
		
		# Update storage of the unsaturated zone
		self.Susz0 = Susz - Qusz
		
		self.Susz0[self.Susz0 < 0] = 0
		
		return Qusz
		
		# run steady state conditions