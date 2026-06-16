# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 11:14:04 2023

@author: Edisson
"""
import numpy as np
from landlab import RasterModelGrid
from cuwalid.dryp.components.DRYP_groundwater_EFD import gwflow_EFD

# analytical solution
def constant_transmissivity(x, R=0.00001, L=11000, T=1000, hbc=100):
    h = hbc + (R/(2*T))*(L**2 - x**2)
    return h

def test_groundwater():
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
	#thickness = surface - bottom
	thickness = np.full(grid_size, 100.0)
	bathymetry = np.full(grid_size, 200.0)
	head = np.full(grid_size, 100.0)
	Sy = np.full(grid_size, 0.01)	
	Ksat_aq = np.full(grid_size, 10.0)
	CHB = np.full(grid_size, -9999)
	CHB[ncol*2-1] = 100.0

	# soi components
	Ksat = np.full(grid_size, 10.00)
	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)	
	Droot = np.full(grid_size, 1.0)

	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)

	# aquifer type
	aqtype = np.zeros(grid_size)

	# recharge	
	recharge = np.full(grid_size, 0.00001)	
	
	act_nodes = grid.core_nodes[:]
	
	riv_nodes = []
	
	# time step
	dt = 1.0
	method = 0
	
	# from analitical solution
	#answer = [103.29709717, 107.56528382, 111.22180669, 114.32537025, 116.92001661,
	#		119.0390284, 120.70745745, 121.94379969, 122.76111063, 123.16773231]
	
	# from analitical solution
	x = np.linspace(1000, 10000, 10)
	answer = constant_transmissivity(x)
	
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
	
	assert np.allclose(out, answer, atol=7.5e-2)
	# tolerance use for numerical errors is assumed to be 7.5 cm

	print('Groundwater: Test completed successfully')

def test_groundwater_implicit():
	"""Implicit groundwater solver should match the confined benchmark.

	This uses a larger model time step than the explicit solver test and
	checks that the steady-state profile stays within the same tolerance.
	"""
	ncol = 12
	nrow = 3
	grid = RasterModelGrid((nrow, ncol), 1000.0)
	grid_size = grid.shape[0]*grid.shape[1]

	surface = np.full(grid_size, 200.0)
	riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)

	bottom = np.full(grid_size, 0.0)
	thickness = np.full(grid_size, 100.0)
	bathymetry = np.full(grid_size, 200.0)
	head = np.full(grid_size, 100.0)
	Sy = np.full(grid_size, 0.01)
	Ksat_aq = np.full(grid_size, 10.0)
	CHB = np.full(grid_size, -9999)
	CHB[ncol*2-1] = 100.0

	Ksat = np.full(grid_size, 10.0)
	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)
	Droot = np.full(grid_size, 1.0)

	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)
	aqtype = np.zeros(grid_size)
	recharge = np.full(grid_size, 0.00001)
	act_nodes = grid.core_nodes[:]
	riv_nodes = []

	x = np.linspace(1000, 10000, 10)
	answer = constant_transmissivity(x)

	gw = gwflow_EFD(
		grid, Ksat_aq, area_river, CHB, 0,
		solver='implicit', implicit_max_iter=6,
		implicit_tolerance=1.0e-8
	)

	for i in range(1000):
		head, baseflow = gw.run_one_step_gw(
			grid,
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
			recharge,
			stage,
			50.0
		)

	out = head[act_nodes]
	assert np.allclose(out, answer, atol=7.5e-2)
	
if __name__ == '__main__':
	test_groundwater()