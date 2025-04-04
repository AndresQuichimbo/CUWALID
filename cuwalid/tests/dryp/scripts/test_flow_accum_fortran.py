# -*- coding: utf-8 -*-
""" test flow accumulation algorithm python and fortran
Created on Mon Feb 13 11:14:04 2023
@author: Edisson Quichimbo
"""
import numpy as np
from landlab import RasterModelGrid
#from components.DRYP_flow_accum import runoff_routing
from cuwalid.dryp.components.DRYP_flow_accumf90 import runoff_routing

def test_runoff():
	# create a raster grid landlab object
	ncol = 12
	nrow = 3
	grid_cellsize = 1000.0
	grid = RasterModelGrid((nrow, ncol), grid_cellsize)
	grid_size = grid.shape[0]*grid.shape[1]
	
	surface = grid.node_x*0.01 + 100.0
	#riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	river_cells = np.zeros(grid_size)
	river_cells[ncol+1] = 1
	area_river = np.full(grid_size, 10000.0)
	#rip_to_cell_area_factor = np.full(grid_size, 1000./np.power(grid_cellsize,2))
	flowDir = None
	decay = np.full(grid_size, 3600.0*0.5/grid_cellsize)
	#area_bank_cells = 1000*110.0
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
			area_cells,
			area_river,
			river_sat_deficit,
			None)
	
	out = [ro.discharge[ncol+1], ro.trans_losses[ncol+1]]
	answer = [(ncol-2.0)*np.power(grid_cellsize, 2), 839701.111778]
	assert np.allclose(out, answer)

	print('Flow routing: Test completed successfully')
	
if __name__ == '__main__':
	test_runoff()