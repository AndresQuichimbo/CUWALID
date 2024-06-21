# -*- coding: utf-8 -*-
"""
DRYP: Dryland WAter Partitioning Model
"""
from context import dryp
import numpy as np
import pandas as pd
from CUWALID.models.DRYP.dryp.components.DRYP_io import (grid_environment)
from CUWALID.models.DRYP.dryp.components.DRYP_infiltration import infiltration
from CUWALID.models.DRYP.dryp.components.DRYP_interception import interception
from CUWALID.models.DRYP.dryp.components.DRYP_soil_layer import swbm
from CUWALID.models.DRYP.dryp.components.DRYP_ABM_connector import ABMconnector
#from CUWALID.models.DRYP.dryp.components.DRYP_flow_accum import runoff_routing
from CUWALID.models.DRYP.dryp.components.DRYP_flow_accumf90 import runoff_routing
from CUWALID.models.DRYP.dryp.components.DRYP_groundwater_EFD import (
	gwflow_EFD,	storage_uz_sz)
#from components.DRYP_store_functions import (
#	GlobalTimeVarPts, GlobalTimeVarAvg, GlobalGridVar,
#	save_map_to_rastergrid, check_mass_balance)


def test_dryp():
	"""test dryp model for an speciic period
	"""
	# define grid properties
	grid_ncols = 12
	grid_nrows = 3
	grid_xllcorner = 0
	grid_yllcorner = 0
	grid_cellsize = 1000.0
	grid_size = grid_ncols*grid_nrows
	domain = None
	
	# create a raster grid environment, landlab grid
	grid_env = grid_environment()
	grid =	grid_env.create_grid(
		grid_ncols,
		grid_nrows,
		grid_xllcorner,
		grid_yllcorner,
		grid_cellsize,
		domain)
	
	# create arrays and model variables
	# surface
	surface = np.arange(grid_size)*0.001 + 200.0
	#surface = np.full(grid_size, 200)
	riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	river_cells = np.zeros(grid_size)
	area_river = np.full(grid_size, 10000.0)
	rip_to_cell_area_factor = np.full(grid_size, 1000./np.power(grid_cellsize,2))
	flowDir = None
	decay = np.full(grid_size, 3600.0*0.5/grid_cellsize)
	area_bank_cells = 1000*110.0
	area_cells = np.power(grid_cellsize,2)
	
	# groundwater
	bottom = np.full(grid_size, 0)
	thickness = surface - bottom
	bathymetry = np.full(grid_size, 200)
	head = np.full(grid_size, 100)
	Sy = np.full(grid_size, 0.05)
	Ksat_aq = np.full(grid_size, 1.00)
	CHB = np.full(grid_size, -9999)
	CHB[grid_ncols] = 100.0

	# soil
	Ksat = np.full(grid_size, 0.545)
	PSI = np.full(grid_size, 11.01)
	Droot = np.full(grid_size, 1000.0)
	theta_sat = np.full(grid_size, 0.60)
	theta_fc = np.full(grid_size, 0.40)
	theta_wp = np.full(grid_size, 0.30)
	b = 10.5 # soil particle distribution parameter
	c = np.full(grid_size, 2/b + 3)
	
	extintion_depth = np.full(grid_size, 1000.0)
	z_extintion = surface - extintion_depth
	Kc = None

	conductivity = 1000.*riv_length*riv_width*Ksat
	# forcing
	ppre = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.4, 0.6, 0.6]
	ppet = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
	
	# start model components
	abc = ABMconnector()
	inf = infiltration(1)
	cnp = interception()
	
	swb = swbm(60)
	swb_rip = swbm(60)
	ro = runoff_routing(grid, grid_size, surface, flowDir,
			Ksat, decay, riv_width, riv_length)

	gw = gwflow_EFD(grid, Ksat, area_river, CHB, 1)
	
	# nodes to perform calculation
	act_nodes = grid.core_nodes[:]
	riv_nodes = np.where(river_cells > 0)[0]
	if riv_nodes.size > 0:
		act_riv_nodes = np.where(riv_nodes[act_nodes] > 0)[0]

	# find location of lakes
	id_lakes = surface[act_nodes] - bathymetry[act_nodes]
	id_lakes = np.where(id_lakes > 0)[0]

	volume_to_depth_factor_rip = np.full(grid_size, 1000./area_bank_cells)
	cell_to_rip_area_factor = np.full(grid_size, grid_cellsize/area_bank_cells)
	run_GW = 0
	dtSZ = 60
	dt_GW = 60
	dt = 60

	# initial conditions
	Duz0 = np.full(len(act_nodes), 1000.0)
	theta = np.full(grid_size, 0.212)
	if riv_nodes.size > 0:
		rtheta = np.full(len(riv_nodes), 0.212)
	baseflow = np.zeros(grid_size)
	recharge = np.zeros(grid_size)
	etg_agg = np.zeros(grid_size)
	rch_agg = np.zeros(grid_size)

	runoff = np.zeros(grid_size)
	AOF_threshold = np.ones(grid_size)
	AOF = np.zeros(grid_size)
	river_sat_deficit = (surface - head)*np.power(grid_cellsize, 2)
	Ft0 = None
	SORP0 = None
	t_0 = None
	dry_day = None

	# initialize array to store model results
	#point_var = GlobalGridVar(ini_date,
	#		   dt_results, data_in.save_results)
	#grid_var = GlobalGridVar(data_in.ini_date,
	#		   data_in.dt_results, data_in.save_results)
	#total_var = GlobalGridVar(data_in.ini_date,
	#		   data_in.dt_results, data_in.save_results)


	# run the model through time step
	for i in range(3):
		rain = np.full(grid_size, ppre[i])
		PETh = np.full(grid_size, ppet[i])
		# INFILTRATION: estimate infiltration --------------------
		#inf.run_infiltration_one_step(Pth, env_state, data_in)
		INF, EXS, Ft0, SORP0, t_0, dry_day = inf.run_infiltration_one_step(
				Ksat[act_nodes],
				theta_sat[act_nodes],
				PSI[act_nodes],
				Droot[act_nodes],
				theta[act_nodes],
				rain[act_nodes],
				Ft0, SORP0, t_0, dry_day,
				)
		
		# subsurface storage [mm]
		tws = storage_uz_sz(
				surface[act_nodes],
				bathymetry[act_nodes],
				bottom[act_nodes],
				Droot[act_nodes]*0.001,
				theta_sat[act_nodes],
				Sy[act_nodes],
				head[act_nodes],
				theta[act_nodes]
				)
		#print(171, tws)	
		# adding groundwater evapotranspiration
		# ratio of Etp
		ratio_etp = head[act_nodes] - z_extintion[act_nodes]
		ratio_etp[ratio_etp < 0] = 0
		ratio_etp[extintion_depth[act_nodes] > 0] = (
				ratio_etp[extintion_depth[act_nodes] > 0]
				/(extintion_depth[act_nodes])[
				extintion_depth[act_nodes] > 0]
				)
		
		ratio_etp[ratio_etp > 1] = 1
		
		# potention evapotranspiration ONLY over model domain
		if Kc is not None:
			PETh = Kc[act_nodes]*PETh[act_nodes]
		# potential evapotranspiration for saturated zone
		PETsz = PETh[act_nodes]*ratio_etp
		# potential evapotranspiration for unsaturated zone
		PETuz = PETh[act_nodes] - PETsz
		
		# SOIL WATER BALANCE: Mestimate soil water balance-------
		AET, PCR, theta[act_nodes], ROF= swb.run_swbm_one_step(
				INF,
				PETuz,
				np.ones_like(act_nodes),#Kc[act_nodes],
				Ksat[act_nodes],
				theta_sat[act_nodes],
				theta_fc[act_nodes],
				theta_wp[act_nodes],
				c[act_nodes],
				Duz0,
				theta[act_nodes]
				)
		if riv_nodes.size > 0:
			# RIPARIAN WATER BALANCE -------------------------------------
			# calculate riparial pet
			rpet_dt = PETuz[act_riv_nodes] - AET[act_riv_nodes]
		# estimate available storage at riparian zone
			# change gw discharge from m to mm per unit rip. area
			smd, qriv, inf_rip_dt = swb_rip.water_deficit(
				baseflow[riv_nodes]*1000*cell_to_rip_area_factor[riv_nodes],
				rpet_dt)
				
			river_sat_deficit[riv_nodes] += (smd*area_bank_cells[riv_nodes])
		
			# update groundwater discharge at river cells
			baseflow[riv_nodes] = (
				qriv[riv_nodes]*
				rip_to_cell_area_factor[riv_nodes]*0.001)
						
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
		
						
		# Add runoff from all sources (all units must change to m)
		runoff[act_nodes] = EXS + ROF + baseflow[act_nodes]
		# add data abstractions/sink/source points
		# select row from dataframe and add to the excess component
		#if dataFlux.data_set is not None:					
		#	runoff[idFluxOF] += dataFlux.get_point_dataset_one_step(t_abs)
		#print(exs_dt)			  
		
		# RUNOFF: estimate runoff---------------------------------------
		ro.run_runoff_one_step(
				runoff*0.001,
				AOF, AOF_threshold,
				conductivity,
				decay,
				river_cells,
				area_cells,
				area_river,
				river_sat_deficit,
				None)
		
		if riv_nodes.size > 0:
			# change transmission losses rate to riparian area
			# change units from m to mm per unit rip. area
			tls_aux = ro.trans_losses[riv_nodes]*volume_to_depth_factor_rip[riv_nodes]
		# estimate inputs to riparian unsaturated zone [mm]
			riv_infiltration = tls_aux + inf_rip_dt
		# estimate riparian water balance,
			# use Ksas of the channel in [mm/dt]
			rAET, rPCR, rtheta, rROF = swb_rip.run_swbm_one_step(
					riv_infiltration,#[riv_nodes],
					rpet_dt[riv_nodes],
					np.ones_like(riv_nodes),#Kc[act_nodes],
					Ksat[riv_nodes],
					theta_sat[riv_nodes],
					theta_fc[riv_nodes],
					theta_wp[riv_nodes],
					c[riv_nodes],
					Droot[riv_nodes],
					rtheta
					)
			
				# update focused recharge
			rPCR += rROF
		# transfer fluxes from riparian zone to model cells
			rAET *= rip_to_cell_area_factor[riv_nodes]
			rPCR *= rip_to_cell_area_factor[riv_nodes]
			recharge[riv_nodes] += rPCR
		
		# estimate total groundwater recharge
		recharge[act_nodes] += PCR + aux_rch #- abc.asz# [mm/dt]
		
		# temporal aggregation of fluxes for groundwater
		etg_agg[act_nodes] += PETsz[:] # [mm/h]
		rch_agg += recharge[:] # [mm/dt]
		
		
		# GROUNDWATER --------------------------------------------------
		# activate groundwater component (gw)
		if run_GW > 0:
			if dt_GW == dtSZ:
				
				head, baseflow = gw.run_one_step_gw(grid,
						surface,
						bottom,
						thickness,
						bathymetry,
						riv_elevation,
						riv_nodes,
						Sy,
						Droot*0.001,
						conductivity,
						None,
						theta_sat,
						theta_fc,
						theta,
						head,
						(rch_agg - etg_agg)*0.001, #[mm/dt]recharge,
						ro.stage,
						dtSZ/60
						)
				
				# empty array
				rch_agg = np.zeros(grid_size)
				etg_agg = np.zeros(grid_size)
				dt_GW = 0
			
			# time accumulator for gw	
			dt_GW += int(dt)
		
		# update soil moisture
		if run_GW > 0:
			Duz0, theta[act_nodes] = swb.run_soil_aquifer_one_step(
				surface[act_nodes],
				head[act_nodes],
				Droot[act_nodes],
				theta_fc[act_nodes],
				theta_wp[act_nodes],
				Duz0, theta[act_nodes]
				)
			
		# estimate groundwater storage change for delta t
		twsc = np.zeros_like(rain)
		# get the total water storage change as grid
		twsc[act_nodes] = storage_uz_sz(
				surface[act_nodes],
				bathymetry[act_nodes],
				bottom[act_nodes],
				Droot[act_nodes]*0.001,
				theta_sat[act_nodes],
				Sy[act_nodes],
				head[act_nodes], theta[act_nodes]) - tws
			
				# save the mean values		
			#gws_mb.append(np.mean(twsc[act_nodes]-twsc0))
		#print(349, twsc[act_nodes])
		recharge[act_nodes] = 0.0
	
	print('DRYP model: Test runs successfully')

if __name__ == '__main__':
	test_dryp()