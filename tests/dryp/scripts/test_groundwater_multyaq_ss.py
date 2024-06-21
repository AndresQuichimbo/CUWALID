# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 11:14:04 2023
Funtion to test steady-state conditions for the groundwater component
@author: Edisson Quichimbo
"""
from tests.dryp.scripts.context import dryp
import numpy as np
from DRYPv2.dryp.components.DRYP_io import (grid_environment)
from DRYPv2.dryp.components.DRYP_groundwater_EFD_SS import (gwflow_EFD)

run_fortran = False
#run_fortran = True
if run_fortran is True:
	import DRYPv2.dryp.components.gaussf90 as gauss
else:
	from DRYPv2.dryp.components.DRYP_solvers import gauss_seidel_iteration

#@profile
def run_DRYP_SS():
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
	grid = grid_env.create_grid(
		grid_ncols,
		grid_nrows,
		grid_xllcorner,
		grid_yllcorner,
		grid_cellsize,
		domain)
	
	# create arrays and model variables
	# surface
	#surface = np.arange(grid_size)*0.001 + 200.0
	surface = np.full(grid_size, 200.0)
	Droot = np.full(grid_size, 1.0)
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
	bottom = np.full(grid_size, 0.0)
	#thickness = surface - bottom
	thickness = np.full(grid_size, 20.0)
	Ksat = np.full(grid_size, 10.00)
	conductivity = riv_width*riv_length*Ksat
	
	# create a grid of aquifer type
	aqtype = np.ones(grid_size)
	aqtype[18:] = 3
	#print(aqtype)
	
	#bathymetry = np.full(grid_size, 200)
	head = np.full(grid_size, 100.0)
	#Sy = np.full(grid_size, 0.05)
	Ksat_aq = np.full(grid_size, 1.00)
	CHB = np.full(grid_size, -9999)
	CHB[grid_ncols] = 100.0
	
	# get rainfall
	rain = np.full(grid_size, 0.001)
	
	# aquifer type activated
	gwmethod = 3
	faq_factor = False
	# create groundwater component
	gw = gwflow_EFD(grid,
		 	None,
			Ksat_aq,
			area_river,
			CHB,
			gwmethod,
			faq_factor)
	
	head = head[:]
	
	stage = np.zeros_like(head)
	#error tolerance
	error_tol = False
	
	#error = np.zeros(len(env_state.SZgrid.node_y))
	max_iter = 10000
	iter = 0
	
	# nodes to perform calculation
	act_nodes = grid.core_nodes[:]
	riv_nodes = np.zeros(grid_size)
	riv_nodes[act_nodes] = 1
	river_cells = riv_nodes*river_cells		
	riv_nodes = np.array(np.where(river_cells > 0)[0], dtype=int)
	
	# nodes to transfer information from river grid
	# to core nodes grid (active nodes)
	if riv_nodes.size > 0:
		act_riv_nodes = np.where(river_cells[act_nodes] > 0)[0]
	
	# flip order of node calcualtion to improve convergence
	#flip_order = True
	flip_order = False#True
	
	# relaxation factor w
	# w > 0 is over relaxation, w < 1 under relaxation
	w = 1.5
	#print(rain)
	head0 = head[:]
	
	while error_tol == False:				
		# GROUNDWATER --------------------------------------------------
		# calculate transmissibity
		head_ini = head0[act_nodes]

		# calculate transmissivity
		gw.run_one_step_gw_SS(grid,
				surface,
				bottom,
				thickness,
				Droot,
				riv_elevation,
				riv_nodes,
				conductivity,
				aqtype,
				head0,
				rain*0.001, #[mm/dt]recharge,
				stage,
				1,
				)
								
		# flip nodes to improve convergence
		if flip_order is True:
			nodes = np.flip(nodes)
		
		# call gauss seidel iterator for solving groundwater flow
		#RUN FORTRAN
		if run_fortran is True:
			head = np.array(head0, np.float32)
			gauss.solver.gauss_seidel_iteration(
				head,
				np.array(surface,np.float32),
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
				surface,
				head0,
				gw.T,
				gw.fluxes,
				act_nodes, #nodes
				grid.links_at_node,
				grid.node_at_link_head,
				grid.node_at_link_tail,
				w)
		
		# updated water table for evaluation
		head_updated = head[act_nodes]
		
		# evaluate errors
		error_tol = np.allclose(head_ini, head_updated,
			rtol=1e-05, atol=1e-015, equal_nan=True
			)
		
		# update water table
		head0 = head[:]
		
		# calculate iteration
		iter += 1
		if iter >= max_iter:
			error_tol = True
	
	#print(iter)
	#print(head[act_nodes])

	print('SS Multi-aquifer:Test runs successfully')
	
	
if __name__ == '__main__':
	run_DRYP_SS()