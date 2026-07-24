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
import time

# global variables
SY = 0.01
KSAT = 10.0
RECHARGE = 0.00001

# analytical solution
def constant_transmissivity(x, R=RECHARGE, L=11000, T=KSAT*100, hbc=100):
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
	h(x) = 100 + (R/(2*T))*(L**2 - x**2)

	Expected outcome:
	The numerical solution should be close to the analytical solution:
	error < 7.5e-2 m

	"""
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
	thickness = np.full(grid_size, 100.0)
	bathymetry = np.full(grid_size, 200.0)
	head = np.full(grid_size, 100.0)
	Sy = np.full(grid_size, SY)	
	Ksat_aq = np.full(grid_size, KSAT)
	CHB = np.full(grid_size, -9999)
	CHB[ncol*2-1] = 100.0

	# soil properties
	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)
	Ksat = np.full(grid_size, KSAT)
	Droot = np.full(grid_size, 1.0)

	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)
	
	# aquifer type
	aqtype = np.zeros(grid_size)
	
	# recharge
	recharge = np.full(grid_size, RECHARGE)

	
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
	
	# run the model for 5000 time steps
	# measure the time taken to run the model
	start_time = time.time()
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
	end_time = time.time()
	print('Time taken to run the model for 5000 time steps: {:.2f} seconds'.format(end_time - start_time))
	out = head[act_nodes]
	assert np.allclose(out, answer, atol=7.5e-2)
	# tolerance use for numerical errors is assumed to be 7.5 cm

	print('Groundwater constant transmissivity: Test completed successfully')

def test_groundwater_constant_transmissivity_implicit():
	"""Implicit geo groundwater solver should match the confined benchmark."""
	ncol = 12
	nrow = 3
	grid = create_grid_from_extent(ncol, nrow, 0, 0, 1000.0, geographic=False)
	grid_size = ncol*nrow

	surface = np.full(grid_size, 200.0)
	riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)

	bottom = np.full(grid_size, 0.0)
	thickness = np.full(grid_size, 100.0)
	bathymetry = np.full(grid_size, 200.0)
	head = np.full(grid_size, 100.0)
	Sy = np.full(grid_size, SY)
	Ksat_aq = np.full(grid_size, KSAT)
	CHB = np.full(grid_size, -9999)
	CHB[ncol*2-1] = 100.0

	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)
	Ksat = np.full(grid_size, KSAT)
	Droot = np.full(grid_size, 1.0)

	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)
	aqtype = np.zeros(grid_size)
	recharge = np.full(grid_size, RECHARGE)
	act_nodes = grid['core_nodes'][:]
	riv_nodes = []

	x = np.linspace(1000, 10000, 10)
	answer = constant_transmissivity(x)

	gw = gwflow_EFD(
		grid, Ksat_aq, area_river, CHB, 0,
		solver='implicit', implicit_max_iter=6,
		implicit_tolerance=1.0e-8, linear_max_iter=200
	)
	# run the model for 5000 time steps
	# measure the time taken to run the model
	start_time = time.time()
	for i in range(100):
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
	end_time = time.time()
	print('Time taken to run the model for 100 time steps: {:.2f} seconds'.format(end_time - start_time))
	out = head[act_nodes]
	assert np.allclose(out, answer, atol=7.5e-2)


def test_groundwater_constant_transmissivity_geographic_coordinates():
	"""Geographic-grid groundwater run should stay consistent with projected-grid output."""
	ncol = 12
	nrow = 3
	grid_size = ncol*nrow

	# Build a geographic grid whose east-west cell size is close to 1000 m.
	meters_per_degree_lon_equator = 111319.34
	cellsize_deg = 1000.0 / meters_per_degree_lon_equator
	grid_geo = create_grid_from_extent(
		ncol, nrow, 36.0, -1.0, cellsize_deg, geographic=True
	)
	grid_proj = create_grid_from_extent(
		ncol, nrow, 0.0, 0.0, 1000.0, geographic=False
	)

	surface = np.full(grid_size, 200.0)
	riv_elevation = np.full(grid_size, 195.0)
	riv_width = np.full(grid_size, 10.0)
	riv_length = np.full(grid_size, 1000.0)
	bottom = np.full(grid_size, 0.0)
	thickness = np.full(grid_size, 100.0)
	bathymetry = np.full(grid_size, 200.0)
	Sy = np.full(grid_size, SY)
	Ksat_aq = np.full(grid_size, KSAT)
	CHB = np.full(grid_size, -9999)
	CHB[ncol*2-1] = 100.0

	theta_sat = np.full(grid_size, 0.6)
	theta_fc = np.full(grid_size, 0.4)
	theta = np.full(grid_size, 0.4)
	Ksat = np.full(grid_size, KSAT)
	Droot = np.full(grid_size, 1.0)
	area_river = np.full(grid_size, 10000.0)
	conductivity = riv_width*riv_length*Ksat
	stage = np.full(grid_size, 0.01)
	aqtype = np.zeros(grid_size)
	recharge = np.full(grid_size, RECHARGE)
	riv_nodes = []

	# Geographic conversion should produce valid metric cell sizes.
	assert np.all(grid_geo['Dx_cell'] > 0.0)
	assert np.all(grid_geo['Dy_cell'] > 0.0)
	assert not np.allclose(grid_geo['Dx_cell'], grid_geo['Dy_cell'])

	def _run_case(grid, n_steps=5000):
		head = np.full(grid_size, 100.0)
		gw = gwflow_EFD(grid, Ksat_aq, area_river, CHB, 0)
		for _ in range(n_steps):
			head, _ = gw.run_one_step_gw(
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
				1
			)
		return head[grid['core_nodes']]

	out_geo = _run_case(grid_geo)
	out_proj = _run_case(grid_proj)

	# The two solutions should remain close when metric spacing is similar.
	assert np.allclose(out_geo, out_proj, atol=1.0e-1)
	print('Groundwater constant transmissivity geographic coordinates: Test completed successfully')
	
if __name__ == '__main__':
	test_groundwater_constant_transmissivity()
	test_groundwater_constant_transmissivity_implicit()
	test_groundwater_constant_transmissivity_geographic_coordinates()