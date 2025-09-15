# -*- coding: utf-8 -*-
"""
DRYP - Dryland WAter Partitioning Model
__date__ = '20230801'
__version__ = '2.0.1'
__author__ = 'Andres Quichimbo (andresquichimbo@gmail.com)'
__library__ = 'dryp'

General command line:
	python run_drp_input.py filename_input.json
		
Parameters:
	-input_file : string
		path to input json as described in documentation which can be found at https://cuwalid.github.io/model-info/dryp-model
Version(s):
20191130 (1.0.0) --> Development of application for version 2.0.0 of Cuwalid models
"""

import argparse
import numpy as np
from tqdm import tqdm
from cuwalid.dryp.components.DRYP_json_reader import get_model_settings
from cuwalid.dryp.components.DRYP_groundwater_EFD import storage_uz_sz
from cuwalid.dryp.components.assemble_model_components import initialize_core_hydrology_components, initialize_optional_components_and_flux_ids, initialize_simulation_state_variables, setup_output_and_monitoring
from cuwalid.dryp.components.read_model_parameters import read_model_parameters_and_settings
from cuwalid.dryp.components.read_temporal_datasets import read_temporal_datasets_and_grid
from cuwalid.dryp.components.save_model_output import save_model_outputs										

# ---------------------------------------------------------------------
# Version and algorithm information
project_name = 'DRYP'
alg_version = '2.0.1'
alg_type = 'Model'
alg_name = 'RUN_DRYP'
alg_release = '2023-08-01'
# ---------------------------------------------------------------------

# Structure and model components --------------------------------------
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
	"""This function integrates all components of the model, with
	all model parameters and component settings being specified in
	the -filename_input- file.
	
	"""
	
	# read model paramters and model setting file
	data_in = get_model_settings(filename_input)

	print("***************************** READING MODEL PARAMETERS *****************************")

	data_in, topo, soil, rsoil, aquifer, vegetation, water_bodies, water_bodies_management = \
		read_model_parameters_and_settings(filename_input)
	
	# READING FORCING DATASET -------------------------------------------
	# Read precipitation
	print("***************************** READING TEMPORAL DATASETS ****************************")

	PRE, ET0, SAVI, LAI, Kc, av, SAVImin, SAVImax, fluxOF, fluxUZ, fluxSZ, fluxWB, Qusz, grid = \
		read_temporal_datasets_and_grid(data_in, topo)

	# MODEL COMPONENTS ------------------------------------------------------
	print("*************************** ASSEMBLING MODEL COMPONENTS ****************************")

	abc, inf, cnp, swb, swb_rip, ro, gw = initialize_core_hydrology_components(
		data_in, grid, topo, aquifer
	)

	(pnds, idFluxOF, idFluxOF_act, idFluxUZ, idFluxUZ_act,
	idFluxSZ, idFluxSZ_act, idFluxWB, idFluxWB_act,
	idFluxWBout, idFluxWBout_act) = initialize_optional_components_and_flux_ids(
		data_in, grid, water_bodies, fluxOF, fluxUZ, fluxSZ, fluxWB
	)

	# Initialise time step variables
	t = t_eto = t_pre = t_savi = t_kc = t_av = t_abs= 0

	(gws_mb, etg_agg, rch_agg, dt_GW, act_nodes, riv_nodes, act_riv_nodes,
	id_lakes, head, theta, river_sat_deficit, save_rz_var, rtheta,
	Duz0, z_extintion, Ft0, SORP0, t_0, dry_day,
	runoff, recharge, baseflow, AOF_threshold) = initialize_simulation_state_variables(
		data_in, topo, grid, aquifer, soil, vegetation, ro
	)

	(idOF, idOF_act, idUZ, idUZ_act, idGW, idGW_act,
	point_var, grid_var, grid_rmax, grid_vmax, total_var,
	grid_rpvar, total_rpvar, grid_pndvar, total_pndvar) = setup_output_and_monitoring(
		data_in, grid, riv_nodes, water_bodies
	)

	# Initialise the progress bar
	print("****************************** SIMULATION IN PROGRESS ******************************")
	progress_bar = tqdm(total=data_in.ndays, unit='days')
	while t < data_in.ndays:

		for UZ_ti in range(data_in.dt_hourly):
			
			for dt_pre_sub in range(data_in.dt_sub_hourly):
				#print(data_in.fname_TSPre)
				# get rainfall
				rain = PRE.get_one_step_dataset(t_pre, data_in.fname_TSPre, 'pre')
				#rain = rain*0.5 # This is specific for IMERG 30 min resolution only
				# for the forcast TRAINING.
				#rain[rain>300] = 300.
				#print("rain", np.where(np.isnan(rain[act_nodes])))
				
				# get potential evapotranspiration
				PET = ET0.get_one_step_dataset(t_eto, data_in.fname_TSMeteo, 'pet')
				#PET[PET>1] = 1.0
				
				# read flux boundary conditions for all components
				# add data abstractions/sink/source points
				# select row from dataframe and add to the excess component
				if fluxUZ.data_set is not None:					
					rain[idFluxUZ] += fluxUZ.get_point_dataset_one_step(t_abs)
				
				# not in used, NOT DELETE
				# estimate abstractions
				AOF, AUZ, ASZ = abc.run_ABM_one_step(
					rain, Duz0, theta,
					soil.theta_fc,
					soil.theta_wp,
					head,
					)				
				
				#print("pet", PET[act_nodes])
				# check if interception is activated
				#if vegetation.av is None:
				#	SAVIdt = None
				#	SAVIdt_min = None
				#	SAVIdt_max = None
				#	LAIdt = None
				#	Kcdt = None
				#else:
				SAVIdt = SAVI.get_one_step_dataset(t_savi, data_in.fname_TSsavi, 'savi')
				SAVIdt_min = SAVImin.get_one_step_dataset(t_savi, data_in.fname_savi_min, 'savi')
				SAVIdt_max = SAVImax.get_one_step_dataset(t_savi, data_in.fname_savi_max, 'savi')
				LAIdt = LAI.get_one_step_dataset(t_savi, data_in.fname_TSlai, 'LAI')
				Kcdt = Kc.get_one_step_dataset(t_savi, data_in.fname_TSkc, 'kc')
				avdt = av.get_one_step_dataset(t_av, data_in.fname_TSav, 'VegetationFraction')

				if Kcdt is not None:
					# remove the folowing line
					#Kcdt = np.flip(Kcdt.reshape((topo.grid_ncols, topo.grid_nrows)),0).flatten()
					Kcdt = Kcdt[act_nodes]
					Kcdt[Kcdt <= 0] = 1.0
				if LAIdt is not None:
					# remove the folowing line
					#LAIdt = np.flip(LAIdt.reshape((topo.grid_ncols, topo.grid_nrows)),0).flatten()
					LAIdt = LAIdt[act_nodes]
					LAIdt[LAIdt <= 0] = 0.0
				if SAVIdt is not None:
					# remove the folowing line
					#SAVIdt = np.flip(SAVIdt.reshape((topo.grid_ncols, topo.grid_nrows)),0).flatten()
					SAVIdt = SAVIdt[act_nodes]
				
				#print(vegetation.av, SAVIdt, SAVIdt_max, SAVIdt_max, LAIdt, Kcdt)
				# PONDS: Add ponds here ------------------------------------------
				# first check that ponds is active
				if water_bodies.id_nodes is not None:
					water_bodies.pnds_Vo, et_pnds, aoz_pnds, Ppnds = pnds.run_ponds_one_step(
				 							water_bodies.pnds_Vo,
											rain[water_bodies.id_nodes],
											PET[water_bodies.id_nodes], #aoz,
											topo.area_cells,
											)
					# transfer data to the entire model domain
					rain[water_bodies.id_nodes] = Ppnds
				
				## calculate AV
				#av = None
				if avdt is None:
					if vegetation.av is not None:
						#av = (SAVIdt - SAVIdt_min)/(SAVIdt_max - SAVIdt_min)
						vegetation.av = vegetation.av[act_nodes]
				else:
					vegetation.av = avdt[act_nodes]
				
				# add interception component - UZ zone
				Pth, Eca, PETh, LAIdt, Kcdt, Sc0_cn = cnp.run_interception_one_step(
						rain[act_nodes], PET[act_nodes], vegetation.av,
						SAVIdt, SAVIdt_max, SAVIdt_min,
						LAIdt,
						vegetation.lai_a,
						vegetation.lai_b,
						vegetation.fcw_cn[act_nodes],
						vegetation.Sc0_cn[act_nodes],
						Kcdt)
				
				## Estimate Kc for the riparian area
				#Pthr, Ecar, PETr, LAIr, Kcr, Sc0_cnrp = cnp.run_interception_one_step(
				#		rain, PET, vegetation.av,
				#		SAVIdt, SAVIdt_max, SAVIdt_min,
				#		None,
				#		vegetation.lai_a,
				#		vegetation.lai_b,
				#		vegetation.fcw_cn,
				#		vegetation.Sc0_cnrp,
				#		Kcdt)
						
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
						#rain[act_nodes],
						Pth,
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
				
				# calculate maximum water available to extract from water bodies
				# select row from dataframe and add to the excess component
				# units of abstractions should be given in flux/volume units (e.g. m3)
				if fluxWB.data_set is not None:
					# read datasets				
					maximum_flux_wb = np.abs(fluxWB.get_point_dataset_one_step(t_abs))
					
					# change units from m3 to m
					maximum_flux_wb = maximum_flux_wb/topo.area_cells

					# calculate storage of water bodies (meters)
					# storage can not be negative
					storage_wb = head[idFluxWB] - topo.bathymetry[idFluxWB]
					storage_wb[storage_wb < 0] = 0

					# calculate maximum abstractions
					maximum_flux_wb = water_bodies_management.get_abstractions(
						storage_wb, maximum_flux_wb)
					#print(maximum_flux_wb)
				
				# ratio of Etp, units of procesing are in meters
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
				if Kcdt is not None:
					PETh = Kcdt*PETh#[act_nodes]
					#PETh = Kcdt[act_nodes]*PETh#[act_nodes]
				# potential evapotranspiration for saturated zone
				#PETsz = PETh*ratio_etp
				# potential evapotranspiration for unsaturated zone
				#PETuz = PETh - PETsz
				PETuz = PETh.copy()# - PETsz
				#print(INF)
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
					# all values and rates are ONLY valid for the riparian area
					# calculate riparial pet
					rpet_dt = PETuz[act_riv_nodes] - AET[act_riv_nodes]					
					
					# calculate riparian water deficit [mm]
					rsmd = (soil.theta_fc[riv_nodes] - rtheta)*rsoil.Droot[riv_nodes]
					rsmd[rsmd < 0] = 0

					# estimate available storage at riparian zone
					# change gw discharge from m to mm per unit rip. area
					rsmd, qriv, inf_rip_dt = swb_rip.water_deficit(
						baseflow[riv_nodes]*1000.0*topo.cell_to_rip_area_factor[riv_nodes],
						rpet_dt, rsmd)
					
					# change river saturated deficit units from mm to m3
					# also update saturatin deficit with saturated zone
					river_sat_deficit[riv_nodes] += (rsmd*0.001*
									  topo.area_bank_cells[riv_nodes])
					
					# THIS VALUES IS TRANFERED TO THE CELL AREA
					# update groundwater discharge at river cells
					# change units from mm to m
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
								
				# Add runoff from all sources - change all units to mm 
				runoff[act_nodes] = EXS + ROF + baseflow[act_nodes]*1000.0
				
				# add data abstractions/sink/source points
				# all abstractions units should be in m3 (cubic meters)
				# positive values indicate flow in the river/pond
				# negative values indicate flow out of the river/ponds
				if fluxOF.data_set is not None:					
					# select row from dataframe and add to the excess component
					# change units of flow rate to depth (m3 to m)
					runoff[idFluxOF] += fluxOF.get_point_dataset_one_step(t_abs)*1000.00/topo.area_cells
				
				# add flux (abstractions) from water bodies to streams	
				if fluxWB.data_set is not None:					
					# select row from dataframe and add to the excess component
					# units should be in m
					runoff[idFluxWBout] += maximum_flux_wb
					#print(maximum_flux_wb)
				# RUNOFF: estimate runoff---------------------------------------
				# all variables with containing length must be changed to meters [m]
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
					# change transmission losses rate to riparian area, all units
					# must be in mm/dt
					
					# change units of volumetric rate flow to depth rate flow
					# change units from m to mm per unit rip. area
					tls_aux = ro.trans_losses[riv_nodes]*topo.volume_to_depth_factor_rip[riv_nodes]

					# aggregate all inputs to riparian unsaturated zone [mm]
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

					# update recharge with abstractions for water bodies
					# add flux (abstractions) from water bodies to streams	
					if fluxWB.data_set is not None:					
						# select row from dataframe and add to the excess component
						recharge[idFluxWB] += -maximum_flux_wb
				
				# correct hill slop fluxes to grid cells
				#swb.pcl_dt *= env_state.hill_factor
				#swb.aet_dt *= env_state.hill_factor
				
				# estimate total groundwater recharge, units in [mm/dt]
				recharge[act_nodes] += PCR + aux_rch# - abc.asz# [mm/dt]
				
				#### apply dumping to groundwater recharge
				###rech = Qusz.run_recharge_routing(soil, rech, Dusz)
				# this is an update for increasing evapranspiration in humid areas
				PETsz = (PETh - AET)# + rAET))*ratio_etp #this is to increase evapotranspiraiton rates
				
				if riv_nodes.size > 0:
					PETsz[act_riv_nodes] = (PETsz[act_riv_nodes] - rAET)# + rAET))*ratio_etp #this is to increase evapotranspiraiton rates
				
				PETsz = PETsz*ratio_etp																						  
				
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
				
				# add data abstractions/sink/source points
				# units should be in m3 (cubic meters)
				if fluxSZ.data_set is not None:					
					# select row from dataframe and add to the excess component
					# cange units from flow (m3) to depth in mm
					rch_agg[idFluxSZ] += fluxSZ.get_point_dataset_one_step(t_abs)*1000.0/topo.area_cells
				
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
								topo.surface[:],
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
								data_in.dtSZ/60,
								ids_lks=water_bodies.ids_lks,
								sizes_lks=water_bodies.size_lks,
								ids_max_depth_lks=water_bodies.ids_max_depth_lks,
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
				  	{"pre": rain[act_nodes], "pet": PET[act_nodes],
	   				"dis": ro.discharge[act_nodes],
					"aet": AET, "inf": INF, "run": runoff[act_nodes],
					"tht": theta[act_nodes],
	   				"rch": recharge[act_nodes], "egw": PETsz,
					"wte": head[act_nodes],
					"gdh": baseflow[act_nodes], "twsc": twsc[act_nodes],
					})
				
				# store maximum values
				if grid_vmax.store_max is True:
					grid_vmax.store_variables(PRE.date_sim_dt, t_pre,
				  			{"pre": rain[act_nodes], "pet": PET[act_nodes],
	   						"aet": AET, "inf": INF, "run": runoff[act_nodes],
							"rch": recharge[act_nodes], "egw": PETsz,
							"gdh": baseflow[act_nodes],
							}
							)
				# store maximum values at streams locations
				if grid_rmax.store_max is True:
					if riv_nodes.size > 0:
						grid_rmax.store_variables(PRE.date_sim_dt, t_pre,
				  			{"dis": ro.discharge[riv_nodes]}
							)

				# get all fluxes and states at sampling points
				point_var.store_variables(PRE.date_sim_dt, t_pre,
				  	{"aet": AET[idOF_act], "inf": INF[idOF_act],
			  		"dis": ro.discharge[idOF], "tht": theta[idUZ],
					"rch": recharge[idGW], "wte": head[idGW],
					"gdh": baseflow[idGW], "ssz": ro.SSZ[idOF],}
					)
				
				# get mean total values for each flux and state
				total_var.store_variables(PRE.date_sim_dt, t_pre,
				  	{"pre":[np.mean(rain[act_nodes])],
	   				"pet":[np.mean(PET[act_nodes])],
	   				"run":[np.mean(runoff[act_nodes])],
	   				"aet":[np.mean(AET)],
					"inf":[np.mean(INF)],
					"tht":[np.mean(theta[act_nodes])],
					"rch":[np.mean(recharge[act_nodes])],
					"egw":[np.mean(PETsz)],
					"wte":[np.mean(head[act_nodes])],
					"gdh":[np.mean(baseflow[act_nodes])],
					"twsc":[np.mean(twsc[act_nodes])],
					"chb":[gw.flux_at_CHB],
					"tls":[np.mean(ro.trans_losses[act_nodes])],
					})
				
				# get mean total values for each flux and state of the riparian zone
				if riv_nodes.size > 0:
					total_rpvar.store_variables(PRE.date_sim_dt, t_pre,
					  	{"etrp": [np.mean(rAET)],
						"fch": [np.mean(rPCR)],
						"tls": [np.mean(ro.trans_losses[riv_nodes])],
						"thtrp": [np.mean(rtheta)],
						"ssz": [np.mean(ro.SSZ[riv_nodes])]}
						)
					
					grid_rpvar.store_variables(PRE.date_sim_dt, t_pre,
				  		{"etrp": rAET, "fch": rPCR,
						"tls": ro.trans_losses[riv_nodes],
						"thtrp": rtheta,
						"ssz": ro.SSZ[riv_nodes]}
						)

				# get mean total values for each flux and state of water bodies
				if water_bodies.id_nodes is not None:
					total_pndvar.store_variables(PRE.date_sim_dt, t_pre,
					  	{"epd": [np.mean(et_pnds)],
						"vpd": [np.mean(water_bodies.pnds_Vo)],
						"apd": [np.mean(aoz_pnds)],
						}
						)
					
					grid_pndvar.store_variables(PRE.date_sim_dt, t_pre,
				  		{"epd": et_pnds,
						"vpd": water_bodies.pnds_Vo,
						"apd": aoz_pnds,
						}
						)

				# reinitiate recharge variable
				recharge[act_nodes] = 0.0

				# reinitiate river saturation deficit (m3)
				# activate only when groundwater is active
				if data_in.run_GW > 0:
					# apply only when river exist
					if riv_nodes.size > 0:
						river_sat_deficit[riv_nodes] = ((
							topo.riv_elevation[riv_nodes] - head[riv_nodes])*
							np.power(topo.grid_size, 2)*
							aquifer.Sy[riv_nodes])

						river_sat_deficit[river_sat_deficit < 0] = 0.0

				
				# update time steps indices
				t_pre += 1
				t_savi += 1
				t_kc += 1
				t_abs += 1
				
			t_eto += 1		
		
		# update progress bar
		progress_bar.update(1)
	
		t += 1
		
	# Close the progress bar
	progress_bar.close()
	
	print("********************************** SAVING RESULTS **********************************")
	save_model_outputs(data_in, total_var, point_var, grid_var, grid_rmax,
				   grid_vmax, grid_rpvar, total_rpvar, grid_pndvar, total_pndvar,
				   water_bodies, grid, head, theta, ro, rtheta, topo,
				   act_nodes, riv_nodes)
	print("======================= ALL PROCESSES COMPLETED SUCCESSFULLY =======================")
# ---------------------------------------------------------------------
# Call script from external library	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run DRYP with JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	run_DRYP(args.config_file)
# ---------------------------------------------------------------------