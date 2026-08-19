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
from cuwalid.dryp.components.DRYP_io import zone_parameters
from cuwalid.dryp.components.DRYP_json_reader import get_model_settings
from cuwalid.dryp.components.DRYP_groundwater_EFD import storage_uz_sz
from cuwalid.dryp.components.assemble_model_components import (
    initialize_core_hydrology_components,
    set_flux_boundary_conditions,
    initialize_simulation_state_variables,
    initialize_output_arrays,
	setup_monitoring_nodes
	)
from cuwalid.dryp.components.read_model_parameters import read_model_parameters
from cuwalid.dryp.components.read_temporal_datasets import read_temporal_datasets
from cuwalid.dryp.components.save_model_output import save_model_outputs										
import cuwalid.dryp.components.DRYP_util as utils
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

	domain, topo, soil, rsoil, aquifer, vegetation, water_bodies, water_bodies_management = \
		read_model_parameters(data_in)
	
	# create model grid
	#grid = domain.create_grid(topo.mask)
	grid = domain.create_projected_grid(topo.mask, geographic=data_in.geographic)

	# READING FORCING DATASET -------------------------------------------
	# Read precipitation
	print("***************************** READING TEMPORAL DATASETS ****************************")

	PRE, ET0, SAVI, LAI, Kc, av, SAVImin, SAVImax, fluxOF, fluxUZ, fluxSZ, fluxWB, Qusz = \
		read_temporal_datasets(data_in, topo)

	# MODEL COMPONENTS ------------------------------------------------------
	print("*************************** ASSEMBLING MODEL COMPONENTS ****************************")

	abc, inf, cnp, swb, swb_rip, ro, gw, lks, pnds = initialize_core_hydrology_components(
		data_in, grid, topo, aquifer, water_bodies
		)

	(idFluxOF, idFluxOF_act, idFluxUZ, idFluxUZ_act,
	idFluxSZ, idFluxSZ_act, idFluxWB, idFluxWB_act,
	idFluxWBout, idFluxWBout_act) = set_flux_boundary_conditions(
		data_in, grid, fluxOF, fluxUZ, fluxSZ, fluxWB
	)

	# Initialise time step variables
	t = t_eto = t_pre = t_savi = t_kc = t_av = t_abs= 0

	(gws_mb, etg_agg, rch_agg, dt_GW, act_nodes, riv_nodes, act_riv_nodes,
	id_lakes, head, theta, river_sat_deficit, save_rz_var, rtheta,
	Duz0, z_extintion, Ft0, SORP0, t_0, dry_day,
	runoff, recharge, baseflow, AOF_threshold) = initialize_simulation_state_variables(
		data_in, topo, grid, aquifer, soil, vegetation, ro
	)
	
	# INITIALISE OUTPUT AND MONITORING --------------------------------
	#print("************************ READING SETTINGS FOR MODEL OUPUTS *************************")
	print("Setting up outputs and monitoring nodes")
	idOF, idUZ, idGW, idzone_info = setup_monitoring_nodes(grid, data_in)
	#print("Monitoring nodes OF:", idGW)
	#print("Monitoring nodes IDs:", idzone_info[2])
	(#idOF, idOF_act, idUZ, idUZ_act, idGW, idGW_act,
	point_var, grid_var, grid_rmax, grid_vmax, total_var,
	grid_rpvar, total_rpvar, grid_pndvar, total_pndvar, grid_veg,
	grid_lks, zone_var) = initialize_output_arrays(data_in)#, grid, riv_nodes, water_bodies

	# ------------------------------------------------------------------
	# ENABLE INCREMENTAL NETCDF STREAMING FOR GRIDDED OUTPUTS -----------
	# Without this, every grid_* store buffers its ENTIRE output time
	# series in memory and only writes to disk once, at the very end
	# of the run (in save_model_outputs). For a large grid run over a
	# long period that can exhaust memory. Enabling streaming here
	# makes each store flush completed periods to its netCDF file every
	# `flush_every` periods, bounding memory use regardless of run
	# length. This is fully backward compatible: the save_netCDF_var
	# call at the end of the run (in save_model_outputs) is unchanged -
	# it now just flushes whatever remains buffered and closes the
	# file. Point/zone/average CSV stores (point_var, zone_var,
	# total_var, total_rpvar, total_pndvar) are unaffected since their
	# data volume is tiny compared to full-grid output.
	#
	# Two related, independently-configurable options (both optional,
	# both set via data_in - default to the previous behaviour if not
	# provided):
	#   - data_in.nc_split_by: split gridded output into separate files
	#     per period instead of one continuous file for the whole run
	#     - e.g. 'monthly' produces one .nc file per calendar month.
	#     Useful to keep individual file sizes manageable for large
	#     domains / long runs. None (default) keeps a single file, as
	#     before.
	#   - data_in.nc_async_write: if True (default), each flush's
	#     actual disk write runs in a background thread so the
	#     simulation keeps computing the next period instead of
	#     waiting for the write to finish - the only synchronization
	#     point is that a NEW flush waits for the PREVIOUS write to
	#     finish, so at most one write is ever in flight. This adds
	#     negligible overhead as long as flush_every is large enough
	#     that computing the next batch takes longer than writing the
	#     previous one (true for any reasonable flush_every - a single
	#     netCDF write is fast relative to dozens-to-hundreds of
	#     simulation time steps). Set to False to write synchronously
	#     instead (e.g. for debugging).
	_nc_flush_every = getattr(data_in, 'nc_flush_every', 60)
	_nc_split_by = getattr(data_in, 'nc_split_by', None)
	_nc_async_write = getattr(data_in, 'nc_async_write', True)
	grid_var.enable_netcdf_streaming(
		data_in.fnameTS_grid + '.nc', topo.lat, topo.lon, act_nodes,
		projection=data_in.PROJECTION, flush_every=_nc_flush_every,
		split_by=_nc_split_by, async_write=_nc_async_write)
	grid_vmax.enable_netcdf_streaming(
		data_in.fnameTS_grid + 'vmax.nc', topo.lat, topo.lon, act_nodes,
		projection=data_in.PROJECTION, flush_every=_nc_flush_every,
		split_by=_nc_split_by, async_write=_nc_async_write)
	grid_veg.enable_netcdf_streaming(
		data_in.fnameTS_grid + 'veg.nc', topo.lat, topo.lon, act_nodes,
		projection=data_in.PROJECTION, flush_every=_nc_flush_every,
		split_by=_nc_split_by, async_write=_nc_async_write)
	grid_rmax.enable_netcdf_streaming(
		data_in.fnameTS_grid + 'rmax.nc', topo.lat, topo.lon, riv_nodes,
		projection=data_in.PROJECTION, flush_every=_nc_flush_every,
		split_by=_nc_split_by, async_write=_nc_async_write)
	grid_rpvar.enable_netcdf_streaming(
		data_in.fnameTS_grid + 'rp.nc', topo.lat, topo.lon, riv_nodes,
		projection=data_in.PROJECTION, flush_every=_nc_flush_every,
		split_by=_nc_split_by, async_write=_nc_async_write)
	if water_bodies.ids_slks is not None:
		grid_lks.enable_netcdf_streaming(
			data_in.fnameTS_grid + 'lks.nc', topo.lat, topo.lon,
			water_bodies.ids_slks, projection=data_in.PROJECTION,
			flush_every=_nc_flush_every, split_by=_nc_split_by,
			async_write=_nc_async_write)
	if water_bodies.id_nodes is not None:
		grid_pndvar.enable_netcdf_streaming(
			data_in.fnameTS_grid + 'pnd.nc', topo.lat, topo.lon,
			water_bodies.id_nodes, projection=data_in.PROJECTION,
			flush_every=_nc_flush_every, split_by=_nc_split_by,
			async_write=_nc_async_write)
	# ------------------------------------------------------------------

	# ------------------------------------------------------------------
	# PRECOMPUTE STATIC, NODE-INDEXED ARRAYS ----------------------------
	# soil/topo/aquifer/vegetation properties are static for the whole
	# run, so re-slicing them with act_nodes/riv_nodes on every single
	# sub-hourly time step (as the loop used to do) allocates a brand
	# new array copy every iteration for no reason. For large grids run
	# over many time steps this is a significant, easily avoidable cost.
	# Slice once here and reuse the cached arrays inside the time loop.
	Ksat_a = soil.Ksat[act_nodes]
	theta_sat_a = soil.theta_sat[act_nodes]
	PSI_a = soil.PSI[act_nodes]
	Droot_a = soil.Droot[act_nodes]
	Droot_a_m = Droot_a*0.001
	theta_fc_a = soil.theta_fc[act_nodes]
	theta_wp_a = soil.theta_wp[act_nodes]
	c_SOIL_a = soil.c_SOIL[act_nodes]
	Sy_a = aquifer.Sy[act_nodes]
	surface_a = topo.surface[act_nodes]
	bottom_a = aquifer.bottom[act_nodes]
	bathymetry_a = topo.bathymetry[act_nodes]
	extintion_depth_a = vegetation.extintion_depth[act_nodes]
	ones_act_nodes = np.ones_like(act_nodes)
	# full-domain (not just act_nodes) static array used by the
	# groundwater component every step
	Droot_full_m = soil.Droot*0.001

	if riv_nodes.size > 0:
		Droot_r = rsoil.Droot[riv_nodes]
		Ksat_r = rsoil.Ksat[riv_nodes]
		theta_sat_r = rsoil.theta_sat[riv_nodes]
		theta_fc_r = rsoil.theta_fc[riv_nodes]
		theta_wp_r = rsoil.theta_wp[riv_nodes]
		c_SOIL_r = rsoil.c_SOIL[riv_nodes]
		soil_theta_fc_r = soil.theta_fc[riv_nodes]
		cell_to_rip_area_factor_r = topo.cell_to_rip_area_factor[riv_nodes]
		area_bank_cells_r = topo.area_bank_cells[riv_nodes]
		rip_to_cell_area_factor_r = topo.rip_to_cell_area_factor[riv_nodes]
		volume_to_depth_factor_rip_r = topo.volume_to_depth_factor_rip[riv_nodes]
		riv_elevation_r = topo.riv_elevation[riv_nodes]
		Sy_r = aquifer.Sy[riv_nodes]
		ones_riv_nodes = np.ones_like(riv_nodes)
	# ------------------------------------------------------------------

	# Initialise the progress bar
	print("****************************** SIMULATION IN PROGRESS ******************************")
	print("Simulation period: from", data_in.ini_date, "to", data_in.end_date, "number of days:", data_in.ndays)
	progress_bar = tqdm(total=data_in.ndays, unit='days')
	while t < data_in.ndays:

		for UZ_ti in range(data_in.dt_hourly):
			
			for dt_pre_sub in range(data_in.dt_sub_hourly):

				# get rainfall
				rain = PRE.get_one_step_dataset(t_pre, data_in.fname_TSPre, 'pre')
				
				# get potential evapotranspiration
				PET = ET0.get_one_step_dataset(t_eto, data_in.fname_TSMeteo, 'pet')
				
				# ABSTRCTIONS/IRRIGATION ------------------------------
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
				# first check if ponds is active
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
				Pth, Eca, PETh, LAIdt, Kcdt, vegetation.Sc0_cn[act_nodes] = cnp.run_interception_one_step(
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
				#print("Precipitation after interception and irrigation", Pth)				
				# INFILTRATION: estimate infiltration --------------------
				#inf.run_infiltration_one_step(Pth, env_state, data_in)
				INF, EXS, Ft0, SORP0, t_0, dry_day = inf.run_infiltration_one_step(
						Ksat_a,
						theta_sat_a,
						PSI_a,
						Droot_a,
						theta[act_nodes],
						#rain[act_nodes],
						Pth,
						Ft0, SORP0, t_0, dry_day,
						)
				
				# subsurface storage [mm]
				#if data_in.run_GW > 0:
				tws = storage_uz_sz(
						surface_a,
						bathymetry_a,
						bottom_a,
						Droot_a_m,
						theta_sat_a,
						Sy_a,
						head[act_nodes],
						theta[act_nodes]
						)
				
				# GROUNDWATER ABSTRACTIONS ------------------------------
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
				extintion_mask = extintion_depth_a > 0
				ratio_etp[extintion_mask] = (
						ratio_etp[extintion_mask]
						/extintion_depth_a[extintion_mask]
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
						ones_act_nodes,#Kc[act_nodes],
						Ksat_a,
						theta_sat_a,
						theta_fc_a,
						theta_wp_a,
						c_SOIL_a,
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
					rsmd = (soil_theta_fc_r - rtheta)*Droot_r
					rsmd[rsmd < 0] = 0

					# estimate available storage at riparian zone
					# change gw discharge from m to mm per unit rip. area
					rsmd, qriv, inf_rip_dt = swb_rip.water_deficit(
						baseflow[riv_nodes]*1000.0*cell_to_rip_area_factor_r,
						rpet_dt, rsmd)
					
					# change river saturated deficit units from mm to m3
					# also update saturatin deficit with saturated zone
					river_sat_deficit[riv_nodes] += (rsmd*0.001*
									  area_bank_cells_r)
					
					# THIS VALUES IS TRANFERED TO THE CELL AREA
					# update groundwater discharge at river cells
					# change units from mm to m
					baseflow[riv_nodes] = (qriv*
							rip_to_cell_area_factor_r*0.001)
				
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
				
				# ABSTRACTIONS SURFACEWATER ------------------------------
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
					tls_aux = ro.trans_losses[riv_nodes]*volume_to_depth_factor_rip_r

					if lks is not None:
						# Move Transmission losses to reservoirs or lakes
						tls2lake = lks.compute_lakes_tributary_volume(tls_aux[water_bodies.ids_slks])

						# calculate water balance in lakes
						et_lks = lks.get_lakes_evaporation_volume(PET[water_bodies.ids_slks])

						# update lake storage
						lks.add_volume_to_lakes(et_lks.keys, tls2lake.values-et_lks.values)

					# aggregate all inputs to riparian unsaturated zone [mm]
					riv_infiltration = tls_aux + inf_rip_dt

					# estimate riparian water balance,
					# use Ksas of the channel in [mm/dt]
					rAET, rPCR, rtheta, rROF = swb_rip.run_swbm_one_step(
							riv_infiltration,#[riv_nodes],
							rpet_dt,
							ones_riv_nodes,#Kc[act_nodes],
							Ksat_r,
							theta_sat_r,
							theta_fc_r,
							theta_wp_r,
							c_SOIL_r,
							Droot_r,
							rtheta
							)

					# update focused recharge
					rPCR += rROF

					# transfer fluxes from riparian zone to model cells
					# lenght units are keept in mm
					rAET *= rip_to_cell_area_factor_r
					rPCR *= rip_to_cell_area_factor_r

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
						#print("Aquifer Start Head", head[idGW[0]])
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
								Droot_full_m,
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
						
						# calculate lakes total volume
						vtot_lks = head - topo.bathymetry
						vtot_lks[vtot_lks < 0] = 0
						#vtot_lks = vtot_lks*topo.area_cells
						vtot_lks = np.sum(vtot_lks)/grid['n_core_nodes']
						
						# empty array
						rch_agg = np.zeros(topo.grid_size)
						etg_agg = np.zeros(topo.grid_size)
						dt_GW = 0
					
					# time accumulator for gw	
					dt_GW += int(data_in.dt)
				
				else:
					vtot_lks = None

				# update soil moisture
				if data_in.run_GW > 0:

					Duz0, theta[act_nodes] = swb.run_soil_aquifer_one_step(
						surface_a,
						head[act_nodes],#aquifer.head[act_nodes],
						Droot_a,
						theta_fc_a,
						theta_wp_a,
						Duz0, theta[act_nodes]
						)
				
				# estimate groundwater storage change [mm] for delta t
				twsc = np.zeros_like(rain)
				twsc[act_nodes] = storage_uz_sz(
						surface_a,
						bathymetry_a,
						bottom_a,
						Droot_a_m,
						theta_sat_a,
						Sy_a,
						head[act_nodes],
						theta[act_nodes]) - tws

				# get all state and flux variables to grid storage
				if data_in.save_netcdf is True:
					grid_var.store_variables(PRE.date_sim_dt, t_pre,
					  	{"pre": rain[act_nodes], "pet": PET[act_nodes],
		   				"dis": ro.discharge[act_nodes],
						"aet": AET, "inf": INF, "run": runoff[act_nodes],
						"tht": theta[act_nodes],
		   				"rch": recharge[act_nodes], "egw": PETsz,
						"wte": head[act_nodes],
						"gdh": baseflow[act_nodes], "twsc": twsc[act_nodes],
						})
				
				# store vegetation variables
				if vegetation.av is not None:
					grid_veg.store_variables(PRE.date_sim_dt, t_pre,
						{'pth': Pth, 'eca': Eca, 'scz': vegetation.Sc0_cn[act_nodes],
	   					#'lai': LAIdt, 'kc': Kcdt, 'av': vegetation.av
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
				# store lake levels
				if water_bodies.ids_slks is not None:
					grid_lks.store_variables(PRE.date_sim_dt, t_pre,
				  			{"slks": lks.get_lakes_volumetric_states_list()
							}
							)
					
				# get all fluxes and states at sampling points
				point_var.store_variables(PRE.date_sim_dt, t_pre,
				  	{"aet": AET[idOF[1]], "inf": INF[idOF[1]],
			  		"dis": ro.discharge[idOF[0]], "tht": theta[idUZ[0]],
					"rch": recharge[idGW[0]], "wte": head[idGW[0]],
					"gdh": baseflow[idGW[0]], "ssz": ro.SSZ[idOF[0]],
					"twsc": twsc[idGW[0]], "tls": ro.trans_losses[idOF[0]],
					}
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
					"chb":[gw.flux_at_CHB*1000.0] if data_in.run_GW > 0 else [0],
					"tls":[np.mean(ro.trans_losses[act_nodes])],
					'eca': [np.mean(Eca)] if Eca is not None else [0],
					'scz': [np.mean(vegetation.Sc0_cn[act_nodes])] if vegetation.Sc0_cn[act_nodes] is not None else [0],
					'pth': [np.mean(Pth)] if Pth is not None else [0],
					'lai': [np.mean(LAIdt)] if LAIdt is not None else [0],
					'kc': [np.mean(Kcdt)] if Kcdt is not None else [1],
					'av': [np.mean(vegetation.av)] if vegetation.av is not None else [0],
					'lks': [vtot_lks] if vtot_lks is not None else [0],
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
				
				if idzone_info[2] is not None:
					zone_var.store_variables(PRE.date_sim_dt, t_pre,
					  	{"pre":utils.collapse_mean(rain[idzone_info[0]], idzone_info[2]),
		   				"pet":utils.collapse_mean(PET[idzone_info[0]], idzone_info[2]),
		   				"run":utils.collapse_mean(runoff[idzone_info[0]], idzone_info[2]),
		   				"aet":utils.collapse_mean(AET[idzone_info[1]], idzone_info[2]),
						"inf":utils.collapse_mean(INF[idzone_info[1]], idzone_info[2]),
						"tht":utils.collapse_mean(theta[idzone_info[0]], idzone_info[2]),
						"rch":utils.collapse_mean(recharge[idzone_info[0]], idzone_info[2]),
						"egw":utils.collapse_mean(PETsz[idzone_info[1]], idzone_info[2]),
						"wte":utils.collapse_mean(head[idzone_info[0]], idzone_info[2]),
						"gdh":utils.collapse_mean(baseflow[idzone_info[0]], idzone_info[2]),
						"twsc":utils.collapse_mean(twsc[idzone_info[0]], idzone_info[2]),
						#"chb":[gw.flux_at_CHB],
						"tls":utils.collapse_mean(ro.trans_losses[idzone_info[0]], idzone_info[2]),
						#'eca': [np.mean(Eca)] if Eca is not None else [0],
						#'scz': [np.mean(vegetation.Sc0_cn[act_nodes])] if vegetation.Sc0_cn[act_nodes] is not None else [0],
						#'pth': [np.mean(Pth)] if Pth is not None else [0],
						#'lai': [np.mean(LAIdt)] if LAIdt is not None else [0],
						#'kc': [np.mean(Kcdt)] if Kcdt is not None else [1],
						#'av': [np.mean(vegetation.av)] if vegetation.av is not None else [0],
						})

				# reinitiate recharge variable
				recharge[act_nodes] = 0.0

				# reinitiate river saturation deficit (m3)
				# activate only when groundwater is active
				if data_in.run_GW > 0:
					# apply only when river exist
					if riv_nodes.size > 0:
						river_sat_deficit[riv_nodes] = ((
							riv_elevation_r - head[riv_nodes])*
							topo.area_cells*
							Sy_r)

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
	save_model_outputs(data_in, total_var, point_var, zone_var, total_rpvar, total_pndvar,
					grid_var, grid_rmax, grid_vmax, grid_rpvar, grid_pndvar, grid_veg, grid_lks,
					grid, head, theta, ro.SSZ, rtheta, topo, water_bodies.pnds_Vo,
					act_nodes, riv_nodes, water_bodies.ids_slks, water_bodies.id_nodes,
					projection=data_in.PROJECTION)
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