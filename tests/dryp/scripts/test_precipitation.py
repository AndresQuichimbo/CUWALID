# -*- coding: utf-8 -*-
"""
Test precipitation component of DRYP model
Test read a unit precipitation and accumualate the precipitation
over the especified period (ndays=29 days)

This script first create a netcdf file of hourly dataset filled
with a precipitation of 1 mm per hour.

The result at the end of the simulatio should be the cummulative
value of ndays*pre*(number_of_hours_day = 24) = 696 mm

Information related to projection is arbitrary
"""
from context import dryp
import os
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta
from CUWALID.models.DRYP.dryp.components.DRYP_io import grid_environment
from CUWALID.models.DRYP.dryp.components.DRYP_read_dataset import (read_dataset_interp)
from CUWALID.models.DRYP.dryp.components.DRYP_io import create_coordinate_array

def create_test_dataset(fname):
	"""Create dataset for resting the precipitation component"""
	# Define the time range
	start_date = pd.Timestamp('2000-01-01')
	end_date = pd.Timestamp('2000-01-30')
	dates = pd.date_range(start=start_date, end=end_date, freq='H')

	# Create sample data
	lon = np.linspace(-6.0, -5.80, 10)  # Longitude values
	lat = np.linspace(-0.0, 0.10, 5)    # Latitude values
	data = np.ones((len(dates), len(lat), len(lon)), dtype=float)  # test array

	# Create xarray DataArray
	da = xr.DataArray(data,
		   coords=[dates, lat, lon],
		   dims=['time', 'lat', 'lon'],
		   name='pre')

	# Create xarray Dataset
	ds = xr.Dataset({'pre': da})

	# Add attributes
	ds.attrs['description'] = 'Test NetCDF'

	# Save the dataset to NetCDF file
	ds.to_netcdf(fname)

def test_precipitation():	
	# simulation parameters
	dt = 60 # model time step
	dt_pre = 60 # dataset time step
	ini_date = datetime(2000,1,1,0,0,0)
	end_date = datetime(2000,1,30,0,0,0)
	netcf_pre = 1 # read precipitation as netcdf
	reproject_pre = 1 # activate reprojection
	interpolate_pre = 1 # activate interpolation
	
	# specify grid parameters
	grid_ncols = 12
	grid_nrows = 3
	grid_xllcorner = 1200.0
	grid_yllcorner = 167000.0
	grid_cellsize = 1000.0
	grid_size = grid_ncols*grid_nrows
	domain = None

	# create a raster grid environment, landlab grid
	grid_env = grid_environment()
	grid =	grid_env.create_grid(
		grid_ncols,
		grid_nrows,
		grid_xllcorner,
		grid_yllcorner,
		grid_cellsize,
		domain)
	
	# get array of coordinates
	lon, lat = create_coordinate_array(
		grid_xllcorner, grid_yllcorner,
		grid_nrows, grid_ncols,
		grid_cellsize
		)
	
	# setting model components
	# Read precipitation
	PRE = read_dataset_interp(dt, dt_pre,
		ini_date, end_date,
		netcf_pre,
		reproject_pre,
		interpolate_pre,
		grid_size,
		lat,
		lon,
		proj="EPSG:4326",
		projm="EPSG:32630"
		)
	
	# create a test netcdf dataset for evaluation
	fname = "HAD_test_precipitation.nc"
	create_test_dataset(fname)

	# create a numpy array to store precipitaiton
	pre = np.zeros((grid_ncols, grid_nrows))

	t, t_pre = 0, 0
	
	while t < 29:
		for UZ_ti in range(24):
			for dt_pre_sub in range(1):
				# get rainfall				
				rain = PRE.get_one_step_dataset(t_pre, fname, 'pre')
				# accumulate values of precipitaiton
				pre += rain.reshape((grid_ncols, grid_nrows))
				
				t_pre += 1
		t += 1
	
	# calculate the exact answer
	answer = np.full((grid_ncols, grid_nrows), 24.0*29.0)
	
	# evaluate the result
	assert np.allclose(pre, answer)
	
	# remove the test dataset created
	os.remove(fname) if os.path.exists(fname) else None

	print('Precipitation: Test runs successfully')

if __name__ == '__main__':
	test_precipitation()