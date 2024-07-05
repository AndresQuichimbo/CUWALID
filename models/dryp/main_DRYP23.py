# -*- coding: utf-8 -*-
"""
DRYP: Dryland WAter Partitioning Model
"""
import numpy as np
#import pandas as pd
from models.dryp.components.DRYP_io_files import get_model_settings
from models.dryp.components.DRYP_io import (
	grid_environment,
	surface_parameters,
	model_environment_status,
	soil_parameters,
	groundwater_parameters,
	interception_parameters,
	set_initial_conditions,
	extract_id_from_coords)
from models.dryp.components.DRYP_infiltration import infiltration
from models.dryp.components.DRYP_interception import interception
from models.dryp.components.DRYP_read_dataset import (
	read_temporal_dataset, read_dataset, read_dataset_interp)
from models.dryp.components.DRYP_soil_layer import swbm
from models.dryp.components.DRYP_ABM_connector import ABMconnector
#from components.DRYP_routing import runoff_routing
#from components.DRYP_flow_accum import runoff_routing
from models.dryp.components.DRYP_flow_accumf90 import runoff_routing
from models.dryp.components.DRYP_groundwater_EFD import (
	gwflow_EFD,	storage_uz_sz,
	recharge_routing)
from models.dryp.components.DRYP_store_functions import (
	GlobalGridVar,
	save_map_to_rastergrid)


# Structure and model components ---------------------------------------
# data_in:	Input variables 
# env_state:Model state and fluxes
# rf:		Precipitation
# cnp:		canopy interception
# abc:		Anthropic boundary conditions
# inf:		Infiltration 
# swbm:		Soil water balance
# ro:		Routing - Flow accumulator
# gw:		Groundwater flow

#@profile
def run_DRYP(filename_input):
	
	# read model paramters and model setting file
	data_in = get_model_settings(filename_input)
	
	# read topography and channel characteristics
	topo = surface_parameters(data_in.fname_surface)

	# read soil paramters
	soil = soil_parameters(topo.grid_size, data_in.fname_soil)

	# read soil paramters
	rsoil = soil_parameters(topo.grid_size, data_in.fname_riparian)

	# read aquifer parameters
	aquifer = groundwater_parameters(topo.grid_size,
				data_in.fname_aquifer)
	
	# read interception paramters
	vegetation = interception_parameters(topo.grid_size,
				data_in.fname_interception_hillslope)

	# setting location and model results
	#env_state.set_output_dir(data_in)
	#env_state.points_output(data_in)
	
	# Read precipitation
	PRE = read_dataset_interp(data_in.dt, data_in.dt_pre,
		data_in.ini_date, data_in.end_date,
		data_in.netcf_pre,
		data_in.reproject_pre,
		data_in.interpolate_pre,
		topo.grid_size,
		topo.lat,
		topo.lon,
		proj=data_in.proj_data,
		projm=data_in.proj_model,
		)
	
	# Read reference potential evpotranpiration
	ET0 = read_dataset_interp(data_in.dt, data_in.dt_ETo,
		data_in.ini_date, data_in.end_date,
		data_in.netcf_ETo,
		data_in.reproject_ETo,
		data_in.interpolate_ETo,
		topo.grid_size,
		topo.lat,
		topo.lon,
		proj=data_in.proj_data,
		projm=data_in.proj_model,
		)
	
	# Read SAVI
	SAVI = read_dataset(data_in.dt, data_in.dt_savi,
		data_in.ini_date, data_in.end_date,
		data_in.netcf_savi,
		data_in.reproject_savi,
		data_in.interpolate_savi,
		topo.grid_size)
		
	# Read SAVI minimum value
	SAVImin = read_dataset(data_in.dt, data_in.dt_savi_min,
		data_in.ini_date, data_in.end_date,
		data_in.netcf_savi_min,
		data_in.reproject_savi_min,
		data_in.interpolate_savi_min,
		topo.grid_size)
	
	# Read SAVI maximum value
	SAVImax = read_dataset(data_in.dt, data_in.dt_savi_max,
		data_in.ini_date, data_in.end_date,
		data_in.netcf_savi_max,
		data_in.reproject_savi_max,
		data_in.interpolate_savi_max,
		topo.grid_size)
	
	
	# read overland flow boundary condition
	dataFlux = read_temporal_dataset(
			data_in.fname_surface.fname_TSOF,
			data_in.netcf_Flux,
			data_in.dt,
			data_in.end_date,
			data_in.ini_date,
			)

	# add variable saturated component
	Qusz = recharge_routing(topo.grid_size)

	# create a raster grid environment, landlab grid
	grid = grid_environment().create_grid(
		topo.grid_ncols,
		topo.grid_nrows,
		topo.grid_xllcorner,
		topo.grid_yllcorner,
		topo.grid_cellsize,
		topo.mask
		)
	
	# setting model fluxes and state variables
	#env_state = model_environment_status(data_in)

	abc = ABMconnector()
	inf = infiltration(data_in.inf_method)
	cnp = interception()
	
	swb = swbm(data_in.dt)
	swb_rip = swbm(data_in.dt)
	ro = runoff_routing(grid,
		 	topo.grid_size,
			topo.surface, 
			topo.FlowDir,
			topo.Ksat,
			topo.decay,
			topo.riv_width,
			topo.riv_length)

	gw = gwflow_EFD(grid,
			aquifer.Ksat,
			topo.area_river,
			aquifer.CHB,
			data_in.gw_func)
	
	
	# read location of point boundary conditions
	#if dataFlux.data_set is not None:
	#	if data_in.netcf_ABC == 0:
	#		idFluxOF = extract_id_from_coords(
	#			env_state.grid,
	#			data_in.filename_OF_points
	#			)
	#	
	#	elif data_in.netcf_ABC == 2:
	#		idFluxOF = extract_id_from_raster(
	#			env_state.grid,
	#			data_in.filename_OF_points
	#			)
	
	t = 0	
	t_eto = 0	
	t_pre = 0
	t_savi = 0
	t_kc = 0
	t_abs = 0
	
	gws_mb = []
	
	etg_agg = np.zeros(topo.grid_size)
	rch_agg = np.zeros(topo.grid_size)
	dt_GW = int(data_in.dt)
	
	# nodes to perform calculation
	act_nodes = grid.core_nodes[:]
	riv_nodes = np.zeros(topo.grid_size)
	riv_nodes[act_nodes] = 1
	topo.river_cells = riv_nodes*topo.river_cells
		
	riv_nodes = np.array(np.where(topo.river_cells > 0)[0], dtype=int)
	# nodes to transfer information from river grid
	# to core nodes grid (active nodes)
	if riv_nodes.size > 0:
		act_riv_nodes = np.where(topo.river_cells[act_nodes] > 0)[0]
	
	# find location of lakes
	id_lakes = topo.surface[act_nodes] - topo.bathymetry[act_nodes]
	id_lakes = np.where(id_lakes > 0)[0]

	# INITIAL CONDITIONS =========
	# surface water
	ro.Q_ini = topo.Qo[:]

	# set initial conditions for soil and groundwater
	head = aquifer.head[:]
	theta = soil.theta[:]
	river_sat_deficit = np.zeros(topo.grid_size)
	
	save_rz_var = False
	if riv_nodes.size > 0:
		save_rz_var = True
		rtheta = soil.theta[riv_nodes]
		
	# update initial conditions
	head[act_nodes], Duz0, z_extintion, river_sat_deficit[act_nodes], Ft0, SORP0, t_0, dry_day = (
		set_initial_conditions(
				topo.grid_size, soil.Droot[act_nodes],
				head[act_nodes],
				topo.surface[act_nodes], 
			    topo.bathymetry[act_nodes],
				vegetation.extintion_depth[act_nodes],
				topo.grid_cellsize,
				data_in.run_GW)
		)
	
	
	#if riv_nodes.size > 0:
	#	river_sat_deficit = river_sat_deficit[act_riv_nodes]

	runoff = np.zeros(topo.grid_size)
	recharge = np.zeros(topo.grid_size)
	baseflow = np.zeros(topo.grid_size)
	AOF_threshold = np.ones(topo.grid_size)

	# Output variables and location
	idOF, idOF_act = extract_id_from_coords(grid, data_in.fname_DISpoints)	# Discharge points
	idUZ, idUZ_act = extract_id_from_coords(grid, data_in.fname_SMDpoints)	# Soil moisture points
	idGW, idGW_act = extract_id_from_coords(grid, data_in.fname_GWpoints)
	
	# initialize array to store model results
	point_var = GlobalGridVar(data_in.ini_date,
			   data_in.dt_results, data_in.save_results)
	grid_var = GlobalGridVar(data_in.ini_date,
			   data_in.dt_results, data_in.save_netcdf)
	total_var = GlobalGridVar(data_in.ini_date,
			   data_in.dt_results, data_in.save_results)
	
	# grid and average results at riparian area
	if riv_nodes.size > 0:
		grid_rpvar = GlobalGridVar(data_in.ini_date,
			   data_in.dt_results, data_in.save_netcdf)
		total_rpvar = GlobalGridVar(data_in.ini_date,
			   data_in.dt_results, data_in.save_results)

	while t < data_in.ndays:
	
		for UZ_ti in range(data_in.dt_hourly):
			
			for dt_pre_sub in range(data_in.dt_sub_hourly):
				
				# get rainfall
				rain = PRE.get_one_step_dataset(t_pre, data_in.fname_TSPre, 'pre')
				#rain[rain>300] = 300.
				
				# get potential evapotranspiration
				PET = ET0.get_one_step_dataset(t_eto, data_in.fname_TSMeteo, 'pet')
				#PET[PET>1] = 1.0
				
				# not in used, NOT DELETE
				# estimate abstractions
				AOF, AUZ, ASZ = abc.run_ABM_one_step(
					rain, Duz0, theta,
					soil.theta_fc,
					soil.theta_wp,
					head,
					)				
				
				# check if interception is activated
				if vegetation.av is None:
					SAVIdt = None
					SAVIdt_min = None
					SAVIdt_max = None
				else:
					SAVIdt = SAVI.get_one_step_dataset(t_savi, data_in.fname_savi, 'savi')
					SAVIdt_min = SAVImin.get_one_step_dataset(t_savi, data_in.fname_savi_min, 'savi')
					SAVIdt_max = SAVImax.get_one_step_dataset(t_savi, data_in.fname_savi_max, 'savi')
				
				# calculate AV
				if vegetation.av is not None:
					av = (SAVIdt - SAVIdt_min)/(SAVIdt_max - SAVIdt_min)
				else:
					av = None
				
				# add interception component - UZ zone
				Pth, Eca, PETh, LAI, Kc, Sc0_cn = cnp.run_interception_one_step(
						rain[act_nodes], PET[act_nodes], vegetation.av,
						SAVIdt, SAVIdt_max, SAVIdt_min,
						None,
						vegetation.lai_a,
						vegetation.lai_b,
						vegetation.fcw_cn,
						vegetation.Sc0_cn)
				
				# Estimate Kc for the riparian area
				Pthr, Ecar, PETr, LAIr, Kcr, Sc0_cnrp = cnp.run_interception_one_step(
						rain, PET, vegetation.av,
						SAVIdt, SAVIdt_max, SAVIdt_min,
						None,
						vegetation.lai_a,
						vegetation.lai_b,
						vegetation.fcw_cn,
						vegetation.Sc0_cnrp)
						
				##### NOT IN USE, NOT DELETE
				##### estimate precipitation over the soil
				##### it combines the interception from the hillslopes
				##### and the riparian zone
				####Pth = (Pth*(1-topo.rip_to_cell_area_factor)
				####	+ Pthr*(topo.rip_to_cell_area_factor))
							
				#### NOT IN USE, NOT DELETE												
				#### add irrigation as rain, still under development
				####Pth = Pth[:] + abc.auz[:]
				
				# INFILTRATION: estimate infiltration --------------------
				#inf.run_infiltration_one_step(Pth, env_state, data_in)
				INF, EXS, Ft0, SORP0, t_0, dry_day = inf.run_infiltration_one_step(
						soil.Ksat[act_nodes],
						soil.theta_sat[act_nodes],
						soil.PSI[act_nodes],
						soil.Droot[act_nodes],
						theta[act_nodes],
						rain[act_nodes],
						Ft0, SORP0, t_0, dry_day,
						)
				
				# subsurface storage [mm]
				#if data_in.run_GW > 0:
				tws = storage_uz_sz(
						topo.surface[act_nodes],
						topo.bathymetry[act_nodes],
						aquifer.bottom[act_nodes],
						soil.Droot[act_nodes]*0.001,
						soil.theta_sat[act_nodes],
						aquifer.Sy[act_nodes],
						head[act_nodes],
						theta[act_nodes]
						)
					
				# ratio of Etp
				ratio_etp = head[act_nodes] - z_extintion
				ratio_etp[ratio_etp < 0] = 0
				ratio_etp[vegetation.extintion_depth[act_nodes] > 0] = (
						ratio_etp[vegetation.extintion_depth[act_nodes] > 0]
						/(vegetation.extintion_depth[act_nodes])[
						vegetation.extintion_depth[act_nodes] > 0]
						)
				
				# calculate ratio of potential evapotranspiration from
				# groundwater
				ratio_etp[ratio_etp > 1] = 1
				
				# potention evapotranspiration ONLY over model domain
				if Kc is not None:
					PETh = Kc[act_nodes]*PETh#[act_nodes]
				# potential evapotranspiration for saturated zone
				PETsz = PETh*ratio_etp
				# potential evapotranspiration for unsaturated zone
				PETuz = PETh - PETsz
				
				# SOIL WATER BALANCE: Mestimate soil water balance-------
				# Units for fluxes are in mm, units of soil moisture [--]
				AET, PCR, theta[act_nodes], ROF= swb.run_swbm_one_step(
						INF,
						PETuz,
						np.ones_like(act_nodes),#Kc[act_nodes],
						soil.Ksat[act_nodes],
						soil.theta_sat[act_nodes],
						soil.theta_fc[act_nodes],
						soil.theta_wp[act_nodes],
						soil.c_SOIL[act_nodes],
						Duz0,
						theta[act_nodes]
						)
				
				# if rivers available, run the water balance in the riparaian
				# zone, otherwise skip code
				if riv_nodes.size > 0:
					# RIPARIAN WATER BALANCE -------------------------------------
					# calculate riparial pet
					rpet_dt = PETuz[act_riv_nodes] - AET[act_riv_nodes]					
					rsmd = soil.theta_fc[riv_nodes] - rtheta
					rsmd[rsmd < 0] = 0

					# estimate available storage at riparian zone
					# change gw discharge from m to mm per unit rip. area
					rsmd, qriv, inf_rip_dt = swb_rip.water_deficit(
						baseflow[riv_nodes]*1000.0*topo.cell_to_rip_area_factor[riv_nodes],
						rpet_dt, rsmd)
					
					river_sat_deficit[riv_nodes] += (rsmd*topo.area_bank_cells[riv_nodes])
					
					# update groundwater discharge at river cells
					baseflow[riv_nodes] = (qriv*
			    			topo.rip_to_cell_area_factor[riv_nodes]*0.001)
								
				# update infiltration excess to considers lakes
				# precipitation over lakes is directly added to the total storage
				# as recharge
				# find lakes
				#id_lakes = bathymetry 
				# add excess to recharge
				aux_rch = np.zeros_like(EXS[:])
				if id_lakes.size > 0:
					aux_rch[id_lakes] = EXS[id_lakes]
					# update infiltration excess
					EXS[id_lakes] = 0
				
				# Update infiltration excess
				#exs_dt = EXS+ROF#[env_state.act_nodes]
								
				# Add runoff from all sources
				runoff[act_nodes] = EXS + ROF + baseflow[act_nodes]
				
				# add data abstractions/sink/source points
				# select row from dataframe and add to the excess component
				#if dataFlux.data_set is not None:					
				#	runoff[idFluxOF] += dataFlux.get_point_dataset_one_step(t_abs)
				
				# RUNOFF: estimate runoff---------------------------------------
				# all units of length must be changed to m
				ro.run_runoff_one_step(
						runoff*0.001,
						AOF, AOF_threshold,
						topo.conductivity,
						topo.decay,
						topo.river_cells,
						topo.area_cells,
						topo.area_river,
						river_sat_deficit,
						None)
				
				if riv_nodes.size > 0:
					# change transmission losses rate to riparian area
					# change units from m to mm per unit rip. area
					tls_aux = ro.trans_losses[riv_nodes]*topo.volume_to_depth_factor_rip[riv_nodes]

					# estimate inputs to riparian unsaturated zone [mm]
					riv_infiltration = tls_aux + inf_rip_dt

					# estimate riparian water balance,
					# use Ksas of the channel in [mm/dt]
					rAET, rPCR, rtheta, rROF = swb_rip.run_swbm_one_step(
							riv_infiltration,#[riv_nodes],
							rpet_dt,
							np.ones_like(riv_nodes),#Kc[act_nodes],
							rsoil.Ksat[riv_nodes],
							rsoil.theta_sat[riv_nodes],
							rsoil.theta_fc[riv_nodes],
							rsoil.theta_wp[riv_nodes],
							rsoil.c_SOIL[riv_nodes],
							rsoil.Droot[riv_nodes],
							rtheta
							)
					
					# update focused recharge
					rPCR += rROF

					# transfer fluxes from riparian zone to model cells
					# lenght units are keept in mm
					rAET *= topo.rip_to_cell_area_factor[riv_nodes]
					rPCR *= topo.rip_to_cell_area_factor[riv_nodes]

					# update total recharge, umits [mm/dt]
					recharge[riv_nodes] += rPCR
				
				# correct hill slop fluxes to grid cells
				#swb.pcl_dt *= env_state.hill_factor
				#swb.aet_dt *= env_state.hill_factor
				
				# estimate total groundwater recharge, units in [mm/dt]
				recharge[act_nodes] += PCR + aux_rch# - abc.asz# [mm/dt]
				
				#### apply dumping to groundwater recharge
				###rech = Qusz.run_recharge_routing(soil, rech, Dusz)
				
				# temporal aggregation of fluxes for groundwater
				# this will allow to run the groundwater component
				# at different time steps
				etg_agg[act_nodes] += PETsz[:] # [mm/h]
				rch_agg += recharge[:] # [mm/dt]
				
				# save total catchment fluxes for water balance
				# Save soil interception variables
				#if env_state.av is not None:
				#	eca_mb.append(np.mean(Eca[env_state.act_nodes]))
				#	lai_mb.append(np.mean(LAI[env_state.act_nodes]))
				#	kc_mb.append(np.mean(Kc[env_state.act_nodes]))
				#	
				#	kcrip_mb.append(np.mean(Kcr[env_state.act_nodes]))
				#	ecar_mb.append(np.mean(Ecar[env_state.act_nodes]))
				#else:
				#	eca_mb.append(0)
				#	lai_mb.append(0)
				#	kc_mb.append(0)
				#	kcrip_mb.append(0)
												
				# GROUNDWATER --------------------------------------------------
				# activate groundwater component (gw)
				if data_in.run_GW > 0:
					if dt_GW == data_in.dtSZ:
						# estimate and change recharge units
						# from mm/h --> m/h
						
						# run groundwater component
						#if data_in.run_GW > 1:
							# under development
							#gw.run_one_step_gw_2Layer(env_state, data_in.dtSZ/60,
							#	swb.tht_dt,	env_state.Droot*0.001)
						#else:
						head, baseflow = gw.run_one_step_gw(grid,
								topo.surface,
								aquifer.bottom,
								aquifer.thickness,
								topo.bathymetry,
								topo.riv_elevation,
								riv_nodes,
								aquifer.Sy,
								soil.Droot*0.001,
								topo.conductivity,
								aquifer.gwtype,
								soil.theta_sat,
								soil.theta_fc,
								theta,
								head,
								(rch_agg - etg_agg)*0.001, #[mm/dt]recharge,
								ro.stage,
								data_in.dtSZ/60
								)
							#gw.run_one_step_gw(env_state.grid, data_in.dtSZ/60,
							#	swb.tht_dt,	env_state.Droot*0.001)
						
						# empty array
						rch_agg = np.zeros(topo.grid_size)
						etg_agg = np.zeros(topo.grid_size)
						dt_GW = 0
					
					# time accumulator for gw	
					dt_GW += int(data_in.dt)
				
				# update soil moisture
				if data_in.run_GW > 0:

					Duz0, theta[act_nodes] = swb.run_soil_aquifer_one_step(
						topo.surface[act_nodes],
						head[act_nodes],#aquifer.head[act_nodes],
						soil.Droot[act_nodes],
						soil.theta_fc[act_nodes],
						soil.theta_wp[act_nodes],
						Duz0, theta[act_nodes]
						)
				
				# estimate groundwater storage change for delta t
				twsc = np.zeros_like(rain)
				twsc[act_nodes] = storage_uz_sz(
						topo.surface[act_nodes],
						topo.bathymetry[act_nodes],
				    	aquifer.bottom[act_nodes],
						soil.Droot[act_nodes]*0.001,
						soil.theta_sat[act_nodes],
						aquifer.Sy[act_nodes],
						head[act_nodes],
						theta[act_nodes]) - tws
							
				# get all state and flux variables to grid storage
				grid_var.store_variables(PRE.date_sim_dt, t_pre,
			      	[rain[act_nodes], PET[act_nodes], ro.discharge[act_nodes],
					AET, INF, runoff[act_nodes], theta[act_nodes],
	   				recharge[act_nodes], PETsz, head[act_nodes],
					baseflow[act_nodes], twsc[act_nodes],
					])
				
				# get all fluxes and states at sampling points
				point_var.store_variables(PRE.date_sim_dt, t_pre,
			      	[AET[idOF_act], INF[idOF_act],
			  		ro.discharge[idOF], theta[idUZ], recharge[idGW], head[idGW],
					baseflow[idGW]])
				#print([np.mean(rain[act_nodes])], [np.mean(PET[act_nodes])],
	   			#	[np.mean(ro.discharge[act_nodes])],
	   			#	[np.mean(AET)], [np.mean(INF)], [np.mean(runoff[act_nodes])],
				#	[np.mean(recharge[act_nodes])],[np.mean(theta[act_nodes])])
				# get mean total values for each flux and state
				total_var.store_variables(PRE.date_sim_dt, t_pre,
			      	[[np.mean(rain[act_nodes])], [np.mean(PET[act_nodes])],
	   				[np.mean(ro.discharge[act_nodes])],
	   				[np.mean(AET)], [np.mean(INF)],
					[np.mean(theta[act_nodes])], [np.mean(recharge[act_nodes])],
					[np.mean(PETsz)], [np.mean(head[act_nodes])],
					[np.mean(baseflow[act_nodes])], [np.mean(twsc[act_nodes])],
					[gw.flux_at_CHB], [np.mean(ro.trans_losses[act_nodes])]])
				
				# get mean total values for each flux and state of the riparian zone
				if riv_nodes.size > 0:
					total_rpvar.store_variables(PRE.date_sim_dt, t_pre,
			    	  	[[np.mean(rAET)], [np.mean(rPCR)],
	    				[np.mean(ro.trans_losses[riv_nodes])],
						[np.mean(rtheta)]]
						)
					
					grid_rpvar.store_variables(PRE.date_sim_dt, t_pre,
			      		[rAET, rPCR, ro.trans_losses[riv_nodes], rtheta])
								
				# reinitiate recharge variable
				recharge[act_nodes] = 0.0
				
				# update time steps indices
				t_pre += 1
				t_savi += 1
				t_kc += 1
				t_abs +=1
				
			t_eto += 1		
		t += 1
	
	# name of variables to store as grid
	var_name = ['pre', 'pet', 'dis', 'aet', 'inf', 'run', 'tht',
	    'rch', 'egw', 'wte', 'gdh', 'twsc']
					
	# save grided model result datasets 
	grid_var.save_netCDF_var(data_in.fnameTS_grid+'.nc',
			   topo.lat, topo.lon, act_nodes, var_name
			   )
	
	# save average values
	var_name = ['pre', 'pet', 'dis', 'aet', 'inf', 'tht',
	    'rch', 'egw', 'wte', 'gdh', 'twsc', 'chb', 'tls']
	length_var = np.ones(len(var_name), dtype=int)
	total_var.save_csv_var(data_in.fnameTS_avg, var_name,
			length_var, multi_files=False)

	# name of variables to store
	var_name = ['aet', 'inf', 'dis', 'tht', 'rch', 'wte', 'gdh']
	
	# save point variables
	length_var = [len(idOF_act), len(idOF_act), len(idOF),
	   			len(idUZ), len(idGW), len(idGW), len(idGW)]
	
	point_var.save_csv_var(data_in.fnameTS_point, var_name, length_var)

	# save average riparian zone variables in a csv file
	if riv_nodes.size > 0:
		var_name = ['aet', 'fch', 'tls', 'tht']
		
		# save grided model result datasets 
		grid_var.save_netCDF_var(data_in.fnameTS_grid+'rp.nc',
			   topo.lat, topo.lon, riv_nodes, var_name
			   )
		
		#save average values in csv
		length_var = np.ones(len(var_name), dtype=int)
		total_rpvar.save_csv_var(data_in.fnameTS_RZ_avg, var_name,
			length_var, multi_files=False)
	
	# Save water table for initial conditions
	save_map_to_rastergrid(grid, head,
			data_in.fnameTS_avg + '_wte_ini.asc')
	
	# Save soil moisture for initial conditions
	save_map_to_rastergrid(grid, theta,
			data_in.fnameTS_avg + '_tht_ini.asc')
	
	# save channel flow initial conditions
	save_map_to_rastergrid(grid, ro.Q_ini,
			data_in.fnameTS_avg + '_Q_ini.asc')
	
	if riv_nodes.size > 0:
		# Save riparian soil moisture for initial conditions
		theta[riv_nodes] = rtheta
		save_map_to_rastergrid(grid, theta,
				data_in.fnameTS_avg + '_tht_rp_ini.asc')
	
if __name__ == '__main__':
	run_DRYP()