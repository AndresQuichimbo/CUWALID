# -*- coding: utf-8 -*-
""" test basin delineation algorithm python
Created on Mon Feb 13 11:14:04 2023
@author: Edisson Quichimbo
"""
from context import dryp
import numpy as np
from landlab import RasterModelGrid
from models.DRYP.dryp.components.DRYP_flow_accum import watershed


def test_basin_delineation():
	# create a raster grid landlab object
	ncol = 6
	nrow = 5
	grid_cellsize = 1000.0
	grid = RasterModelGrid((nrow, ncol), grid_cellsize)
	
    # specified surface elevation
	surface = np.array([
		20, 30, 40, 50, 60, 70,
	   10, 20, 30, 40, 50, 60,
       0, 10, 20, 30, 40, 50,
       10, 20, 30, 40, 50, 60,
       20, 30, 40, 50, 60, 70,
       ], dtype=float)

	# specify flow direction (not available)
	flowDir = None
	
    # specifiy catchment oulet
	outlet = np.array([
		0, 0, 0, 0, 0, 0,
	   0, 0, 0, 0, 0, 0,
       0, 1, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0,
       ], dtype=int)


	# start basin delineation algorithm
	basins = watershed(grid, surface, flowDir)
    
    # Watershed delineation ------------------------------------
	out = basins.get_watersheds(outlet)
	
	answer = [
		0, 0, 0, 0, 0, 0,
	   0, 0, 1, 1, 1, 0,
       0, 1, 1, 1, 1, 0,
       0, 0, 1, 1, 1, 0,
       0, 0, 0, 0, 0, 0,
       ]

	assert np.allclose(out, answer)
	print('Basin delineation: Test runs successfully')
	
if __name__ == '__main__':
	test_basin_delineation()