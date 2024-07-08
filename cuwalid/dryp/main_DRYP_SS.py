# -*- coding: utf-8 -*-
"""
DRYP: Dryland WAter Partitioning Model
"""
import os
import numpy as np
from cuwalid.dryp.components.DRYP_io_files import get_model_settings
from cuwalid.dryp.components.DRYP_io import (
	grid_environment,
	surface_parameters,
	soil_parameters,
	groundwater_parameters)
from cuwalid.dryp.components.DRYP_read_dataset import (
	read_dataset_interp)
from cuwalid.dryp.components.DRYP_groundwater_EFD_SS import (
	gwflow_EFD)
from cuwalid.dryp.components.DRYP_store_functions import (
	save_map_to_rastergrid)
#run_fortran = False
run_fortran = True
if run_fortran is True:
	import cuwalid.dryp.components.gaussf90 as gauss
else:
	from cuwalid.dryp.components.DRYP_solvers import gauss_seidel_iteration

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
def run_DRYP_SS(filename_input):
	
	# read model paramters and model setting file
	data_in = get_model_settings(filename_input)
	
	# read topography and channel characteristics
	topo = surface_parameters(data_in.fname_surface)

	# read soil paramters
	soil = soil_parameters(topo.grid_size, data_in.fname_soil)
	
	# read aquifer parameters
	aquifer = groundwater_parameters(topo.grid_size,
				data_in.fname_aquifer)
	
	# Read precipitation
	PRE = read_dataset_interp(data_in.dt, data_in.dt_pre,
		data_in.ini_date, data_in.end_date,
		data_in.netcf_pre,
		data_in.reproject_pre,
		data_in.interpolate_pre,
		topo.grid_size,
		topo.lat,
		topo.lon
		)
	

	# get rainfall
	recharge = PRE.get_one_step_dataset(0, data_in.fname_TSPre, 'rch')
	#rain[rain >	9] = 9.0
	#rain = np.full(topo.grid_size, 0.001)
	
	# create directories for outputs
	if not os.path.exists(data_in.DirOutput):
		os.mkdir(data_in.DirOutput)
		print("Directory ", data_in.DirOutput, " Created ")
	else:
		print("Directory ", data_in.DirOutput, " already exists")

	# create a raster grid environment, landlab grid
	grid = grid_environment().create_grid(
		topo.grid_ncols,
		topo.grid_nrows,
		topo.grid_xllcorner,
		topo.grid_yllcorner,
		topo.grid_cellsize,
		topo.mask
		)
	
	# transmissivity values
	# 0: constant, 1: linear, 2: exponential, 3: multi-funtions
	gwmethod = 0
	gw = gwflow_EFD(grid,
		 	topo.surface,
			aquifer.Ksat,
			topo.area_river,
			aquifer.CHB,
			#data_in.gw_func,
			gwmethod,
			fparameter=False
			)
	
	head = aquifer.head[:]
	
	stage = np.zeros_like(head)
	
	
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
	
	# flip order of node calcualtion to improve convergence
	#flip_order = True
	flip_order = False

	# relaxation factor w
	# w > 0 is over relaxation, w < 1 under relaxation
	w = 1.5
	
	#error tolerance
	error_tol = False
	
	# maximum numbner of iterations
	max_iter = 10000000
	iter = 0

	# iteration to print results
	print_out = 1000
	iprint = 0

	# initioal condition for the numerical solution		
	head0 = head[:]

	while error_tol == False:				
		# GROUNDWATER --------------------------------------------------
		# calculate transmissibity
		head_ini = head0[act_nodes]
		#print(head0)
		gw.run_one_step_gw_SS(grid,
				topo.surface,
				aquifer.bottom,
				aquifer.thickness,
				soil.Droot*0.001, # in meters
				topo.riv_elevation,
				riv_nodes,
				topo.conductivity,
				aquifer.gwtype,
				head0,
				recharge*0.001, #[mm/dt]recharge,
				stage,
				data_in.dtSZ/60,
				)
								
		
		# flip nodes to improve convergence
		if flip_order is True:
			nodes = np.flip(nodes)
			
		# call gauss seidel iterator for solving groundwater flow
		#RUN FORTRAN
		if run_fortran is True:
			head = np.array(head0,np.float32)
			gauss.solver.gauss_seidel_iteration(
				head,
				np.array(topo.surface,np.float32),
				np.array(gw.T, np.float32),#*env_state.SZgrid.dx, # conductivity
				np.array(gw.fluxes, np.float32),
				np.array(act_nodes, np.int)+1, #nodes
				np.array(grid.links_at_node, np.int)+1,
				np.array(grid.node_at_link_head, np.int)+1,
				np.array(grid.node_at_link_tail, np.int)+1,
				w,
				)
		else:
			head = gauss_seidel_iteration(
				topo.surface,
				head0,
				gw.T,
				gw.fluxes,
				act_nodes, #nodes
				grid.links_at_node,
				grid.node_at_link_head,
				grid.node_at_link_tail,
				w)
		
		
		head_updated = head[act_nodes]
		#print(head_ini)
		#print(head_updated)
		# evaluate errors
		error_tol = np.allclose(head_ini, head_updated,
			rtol=1e-05, atol=1e-015, equal_nan=True
			)
		#print(error_tol)	
		head0 = head[:]
		#print(wte_end)
		
		iter += 1
		if iter >= max_iter:
			error_tol = True

		# Save water table for initial conditions
		if print_out == iprint:
			save_map_to_rastergrid(grid,
				head,
				data_in.DirOutput+'/' + data_in.Mname + '_ss__wte_i.asc')
			
			iprint = 0
		iprint += 1

	print(iter)
	#print(wte_end)
	
	
	
	# Save water table for initial conditions
	save_map_to_rastergrid(grid,
			head,
			data_in.DirOutput+'/' + data_in.Mname + '_ss__wte.asc'
			)
	
if __name__ == '__main__':
	run_DRYP_SS()