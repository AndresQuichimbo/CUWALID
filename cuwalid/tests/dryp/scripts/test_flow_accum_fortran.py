# -*- coding: utf-8 -*-
""" test flow accumulation algorithm python and fortran
Created on Mon Feb 13 11:14:04 2023
@author: Edisson Quichimbo
"""
import numpy as np
from cuwalid.dryp.components.DRYP_io import create_grid_from_extent
#from landlab import RasterModelGrid
#from components.DRYP_flow_accum import runoff_routing
from cuwalid.dryp.components.DRYP_flow_accumf90 import runoff_routing

# create fuction to calculate transmission losses
def transmission_losses(q, decay, riv_width, riv_length, Ksat, t):
	# make sure that all variables are in float32
	q = np.float32(q)
	decay = np.float32(decay)
	riv_width = np.float32(riv_width)
	riv_length = np.float32(riv_length)
	Ksat = np.float32(Ksat)
	t = np.float32(t)

	# Calculate parameter p4 for transmission losses estimation
	par_4 = 2.0*Ksat/(decay*riv_width)
	# Calculate parameter p3 for estimating time to get dry
	# conditions in the channel
	par_3 = Ksat*riv_width*riv_length/(riv_width-2*Ksat)
	t = -(1/decay)*np.log(par_3/(q*decay))
	if t> 1:
		t = 1
	qtl = q*decay*par_4*(1-np.exp(-decay*t))+Ksat*riv_width*riv_length*t
	return qtl

def test_runoff_no_river():
	# create a raster grid landlab object
	ncol = 12
	nrow = 3
	grid_cellsize = 1000.0
	grid = create_grid_from_extent(
		ncol,
		nrow,
		0.0,
		0.0,
		grid_cellsize,
		active_domain=None)
	
	# create arrays and model variables
	grid_size = grid['N_cells']
	
	# surface
	slope = grid['x']*0.01
	surface, _ = np.meshgrid(slope, grid['y'])
	surface = surface.flatten() + 100.0

	# river properties
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	river_cells = np.zeros(grid_size)
	
	#river_cells[ncol+1] = 1
	area_river = np.full(grid_size, 10000.0)
	
	flowDir = None
	decay = np.full(grid_size, 3600.0*0.5/grid_cellsize)
	area_cells = np.power(grid_cellsize, 2)
	
	Ksat = np.full(grid_size, 0.5)
	conductivity = riv_length*riv_width*Ksat
	
	runoff = np.full(grid_size, 1.0)
	head = np.full(grid_size, 50.0)
	AOF_threshold = np.ones(grid_size)
	AOF = np.zeros(grid_size)
	river_sat_deficit = (surface - head)*np.power(grid_cellsize, 2)

	ro = runoff_routing(grid, grid_size, surface, flowDir,
			Ksat, decay, riv_width, riv_length)

	# RUNOFF: estimate runoff---------------------------------------
	ro.run_runoff_one_step(
			runoff,
			AOF, AOF_threshold,
			conductivity,
			decay,
			river_cells,
			grid['Areas'],
			area_river,
			river_sat_deficit,
			None)
	
	out = [ro.discharge[ncol+1], 0.0]
	answer = [(ncol-2.0)*np.power(grid_cellsize, 2), 0.0]
	#print(out, answer)
	assert np.allclose(out, answer)
	print('Flow routing no river: Test completed successfully')

def test_runoff():
	# create a raster grid landlab object
	ncol = 12
	nrow = 3
	grid_cellsize = 1000.0
	grid = create_grid_from_extent(
		ncol,
		nrow,
		0.0,
		0.0,
		grid_cellsize,
		active_domain=None)
	
	# create arrays and model variables
	grid_size = grid['N_cells']
	# surface
	slope = grid['x']*0.01
	surface, _ = np.meshgrid(slope, grid['y'])
	surface = surface.flatten() + 100.0

	# river properties
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	river_cells = np.zeros(grid_size)
	
	river_cells[ncol+2] = 1
	area_river = np.full(grid_size, 10000.0)
	
	flowDir = None
	decay = np.full(grid_size, 3600.0*0.5/grid_cellsize)
	area_cells = np.power(grid_cellsize, 2)
	
	Ksat = np.full(grid_size, 0.5)
	conductivity = riv_length*riv_width*Ksat
	runoff = np.full(grid_size, 1.0)
	head = np.full(grid_size, 50.0)
	AOF_threshold = np.ones(grid_size)
	AOF = np.zeros(grid_size)
	river_sat_deficit = (surface - head)*np.power(grid_cellsize, 2)

	ro = runoff_routing(grid, grid_size, surface, flowDir,
			Ksat, decay, riv_width, riv_length)

	# RUNOFF: estimate runoff ---------------------------------------
	ro.run_runoff_one_step(
			runoff,
			AOF, AOF_threshold,
			conductivity,
			decay,
			river_cells,
			grid['Areas'],
			area_river,
			river_sat_deficit,
			None)
	#print('discharge', ro.discharge.reshape((nrow, ncol)))
	#print('trans_losses', ro.trans_losses.reshape((nrow, ncol)))
	
	# calculate expected values
	qtl = transmission_losses(
						ro.discharge[ncol+2],
						decay[ncol+2],
						riv_width[ncol+2],
						riv_length[ncol+2],
						Ksat[ncol+2],
						1
						)
	#print('transmission losses: ', qtl)
	out = [ro.discharge[ncol+2], ro.trans_losses[ncol+2]]
	answer = [(ncol-3.0)*np.power(grid_cellsize, 2), qtl]
	#print(out, answer)
	assert np.allclose(out, answer)

	print('Flow routing: Test completed successfully')
	
if __name__ == '__main__':
	test_runoff_no_river()
	test_runoff()