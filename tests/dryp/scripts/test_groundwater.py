# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 11:14:04 2023

@author: Edisson
"""
from context import dryp
import numpy as np
from landlab import RasterModelGrid
from models.DRYP.dryp.components.DRYP_groundwater_EFD import gwflow_EFD


def test_groundwater():
	# create a raster grid landlab object
	ncol = 12
	nrow = 3
	grid = RasterModelGrid((nrow, ncol), 1000.0)
	grid_size = grid.shape[0]*grid.shape[1]

	# surface component	
	surface = np.full(grid_size, 200.0)
	riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	riv_nodes = np.zeros(grid_size)
	
	# groundwater component
	bottom = np.full(grid_size, 0.0)
	thickness = surface - bottom
	bathymetry = np.full(grid_size, 200.0)
	head = np.full(grid_size, 100.0)
	Sy = np.full(grid_size, 0.01)	
	Ksat_aq = np.full(grid_size, 20.0)
	aqtype = np.ones(grid_size)

	# soi components
	Ksat = np.full(grid_size, 10.00)
	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)	
	Droot = np.full(grid_size, 1.0)

	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)
	CHB = np.full(grid_size, -9999)
	CHB[ncol] = 100.0
	
	recharge = np.full(grid_size, 0.001)	
	
	act_nodes = grid.core_nodes[:]
	
	riv_nodes = []
	
	# time step
	dt = 1.0
	method = 1
	
	# from analitical solution
	answer = [103.29709717, 107.56528382, 111.22180669, 114.32537025, 116.92001661,
			119.0390284, 120.70745745, 121.94379969, 122.76111063, 123.16773231]

	
	gw = gwflow_EFD(grid, Ksat_aq, area_river, CHB, method)
	
	for i in range(50000):
		
		head, baseflow = gw.run_one_step_gw(grid,
						surface,
						bottom,
						thickness,
						bathymetry,
						riv_elevation,
						riv_nodes,
						Sy,
						Droot,
						conductivity,
						aqtype,
						theta_sat,
						theta_fc,
						theta,
						head,
						recharge, #[mm/dt]recharge,
						stage,
						1.0
						)
	
	#print(i, head[act_nodes])
	out = head[act_nodes]
	
	assert np.allclose(out, answer)
	print('Groundwater: Test runs successfully')
	
if __name__ == '__main__':
	test_groundwater()