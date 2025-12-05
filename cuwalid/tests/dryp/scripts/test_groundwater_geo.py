# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 11:14:04 2023
Test fuction of the groundwater component
@author: Edisson Quichimbo
"""
import numpy as np
#from landlab import RasterModelGrid
from cuwalid.dryp.components.DRYP_io import create_grid_from_extent
from cuwalid.dryp.components.DRYP_groundwater_EFD_geo import gwflow_EFD

# analytical solution
def constant_transmissivity(x, R=0.00001, L=11000, T=1000, hbc=100):
    h = hbc + (R/(2*T))*(L**2 - x**2)
    return h

def test_groundwater_constant_transmissivity():
	"""Groundwater aquifer test function.
	It solves the groundwater flow equation for a confined aquifer with
	constant transmissivity.
	The analytical solution is compared with the numerical solution.
	x direction: left boundary head = 100 m
	L = 11000 m
	recharge: R = 0.00001 m/d
	Ksat: K = 10 m/d
	Thickness: b = 100 m
	Transmissivity T = Kb = 1000 m2/d
	h(L) = 100 m
	Q(0) = 0 m3/d
	Analytical solution:
	h(x) = 100 + (R/(2T))*(L^2 - x^2/2)

	Expected outcome:
	The numerical solution should be close to the analytical solution:
	error < 7.5e-2 m

	"""
	# create a raster grid dryp object
	ncol = 12 # x direction
	nrow = 3 # y direction
	grid = create_grid_from_extent(ncol, nrow, 0, 0, 1000.0, projected=True)
	grid_size = ncol*nrow
		
	surface = np.full(grid_size, 200.0)
	riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	riv_nodes = np.zeros(grid_size)
	
	# aquifer properties
	bottom = np.full(grid_size, 0.0)
	#thickness = surface - bottom
	thickness = np.full(grid_size, 100.0)
	bathymetry = np.full(grid_size, 200.0)
	head = np.full(grid_size, 100.0)
	Sy = np.full(grid_size, 0.01)	
	Ksat_aq = np.full(grid_size, 10.0)
	CHB = np.full(grid_size, -9999)
	CHB[ncol*2-1] = 100.0

	# soil properties
	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)
	Ksat = np.full(grid_size, 10.00)
	Droot = np.full(grid_size, 1.0)

	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)
	
	# aquifer type
	aqtype = np.zeros(grid_size)
	
	# recharge
	recharge = np.full(grid_size, 0.00001)

	
	act_nodes = grid['core_nodes'][:]

	riv_nodes = []
	
	# time step
	dt = 1.0
	method = 0
	
	# from analitical solution
	x = np.linspace(1000, 10000, 10)
	answer = constant_transmissivity(x)

	# run groundwater model
	gw = gwflow_EFD(grid, Ksat_aq, area_river, CHB, method)
	
	for i in range(5000):
		
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
	
	#print(i, head.reshape(nrow, ncol))
	out = head[act_nodes]
	#print('Output:', out)
	#print('Answer:', answer)
	#print('Error:', out-answer)
	
	assert np.allclose(out, answer, atol=7.5e-2)
	# tolerance use for numerical errors is assumed to be 7.5 cm

	print('Groundwater constant transmissivity: Test completed successfully')
	
if __name__ == '__main__':
	test_groundwater_constant_transmissivity()