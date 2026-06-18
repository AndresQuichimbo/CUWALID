# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 11:14:04 2023
Test fuction of the groundwater component
@author: Edisson Quichimbo
"""
import time

import numpy as np
#from landlab import RasterModelGrid
from cuwalid.dryp.components.DRYP_io import create_grid_from_extent
from cuwalid.dryp.components.DRYP_groundwater_EFD_geo import gwflow_EFD

# global variables
SY = 0.01
KSAT = 10.0
RECHARGE = 0.00001
ANSWER = [100.09959412, 100.18914032, 100.26866913, 100.33820343, 100.39776611, 100.48051453, 100.67976379, 100.82920074, 100.92882538, 100.9786377 ]
	

def test_groundwater_multiaq():
	# create a raster grid dryp object
	ncol = 12 # x direction
	nrow = 3 # y direction
	grid = create_grid_from_extent(ncol, nrow, 0, 0, 1000.0, geographic=False)
	grid_size = ncol*nrow
		
	surface = np.full(grid_size, 200.0)
	riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	riv_nodes = np.zeros(grid_size)
	
	# aquifer properties
	bottom = np.full(grid_size, 0.0)
	#thickness = surface - bottom
	thickness = np.full(grid_size, 20.0)
	bathymetry = np.full(grid_size, 200.0)
	head = np.full(grid_size, 100.0)
	Sy = np.full(grid_size, SY)	
	Ksat_aq = np.full(grid_size, KSAT)
	CHB = np.full(grid_size, -9999)
	CHB[ncol] = 100.0


	# soil properties
	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)
	Ksat = np.full(grid_size, KSAT)
	Droot = np.full(grid_size, 1.0)

	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)
	
	aqtype = np.ones(grid_size, dtype=int)
	aqtype[18:] = 3
	
	recharge = np.full(grid_size, RECHARGE)

	act_nodes = grid['core_nodes'][:]
	#print('act_nodes', act_nodes)
	riv_nodes = []
	
	# time step
	dt = 1.0
	method = 3
	
	# from analitical solution
	#answer = [116.51869202, 124.97717285, 130.36439514, 134.1315918, 136.88113403,
	#	136.95245361, 136.98146057, 137.00320435, 137.0177002, 137.02494812]
		
	gw = gwflow_EFD(grid, Ksat_aq, area_river, CHB, method)
	#print('ksat_aq', gw.C_static)
	start_time = time.time()
	for i in range(150000):
		
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
						1
						)
	end_time = time.time()
	print('Time taken to run the model for 150000 time steps: {:.2f} seconds'.format(end_time - start_time))
	#print(i, head.reshape(nrow, ncol))
	out = head[act_nodes]
	#print('Output:', out)
	#print('Answer:', ANSWER)
	#print('Error:', out-ANSWER)
	assert np.allclose(out, ANSWER, atol=7.5e-2)

	print('Groundwater Muti-aquifer: Test completed successfully')

def test_groundwater_multiaq_implicit():
	# create a raster grid dryp object
	ncol = 12 # x direction
	nrow = 3 # y direction
	grid = create_grid_from_extent(ncol, nrow, 0, 0, 1000.0, geographic=False)
	grid_size = ncol*nrow
		
	surface = np.full(grid_size, 200.0)
	riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	riv_nodes = np.zeros(grid_size)
	
	# aquifer properties
	bottom = np.full(grid_size, 0.0)
	#thickness = surface - bottom
	thickness = np.full(grid_size, 20.0)
	bathymetry = np.full(grid_size, 200.0)
	head = np.full(grid_size, 100.0)
	Sy = np.full(grid_size, SY)	
	Ksat_aq = np.full(grid_size, KSAT)
	CHB = np.full(grid_size, -9999)
	CHB[ncol] = 100.0


	# soil properties
	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)
	Ksat = np.full(grid_size, KSAT)
	Droot = np.full(grid_size, 1.0)

	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)
	
	aqtype = np.ones(grid_size, dtype=int)
	aqtype[18:] = 3
	
	recharge = np.full(grid_size, RECHARGE)

	act_nodes = grid['core_nodes'][:]
	#print('act_nodes', act_nodes)
	riv_nodes = []
	
	# time step
	dt = 1.0
	method = 3
	
	# from analitical solution
	#answer = [116.51869202, 124.97717285, 130.36439514, 134.1315918, 136.88113403,
	#	136.95245361, 136.98146057, 137.00320435, 137.0177002, 137.02494812]
		
	gw = gwflow_EFD(grid, Ksat_aq, area_river, CHB, method,
				 solver='implicit', implicit_max_iter=6,
				 implicit_tolerance=1.0e-8, linear_max_iter=200
				 )
	
	#print('ksat_aq', gw.C_static)
	start_time = time.time()
	for i in range(1500):
		
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
						100.
						)
	end_time = time.time()
	print('Time taken to run the model for 150 time steps: {:.2f} seconds'.format(end_time - start_time))
	#print(i, head.reshape(nrow, ncol))
	out = head[act_nodes]
	#print('Output:', out)
	#print('Answer:', ANSWER)
	#print('Error:', out-ANSWER)
	assert np.allclose(out, ANSWER, atol=7.5e-2)

	print('Groundwater Muti-aquifer: Test completed successfully')

if __name__ == '__main__':
	test_groundwater_multiaq()
	test_groundwater_multiaq_implicit()