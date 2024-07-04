# -*- coding: utf-8 -*-
"""
DRYP: Calculate catchment areas at poin location
"""
import os
import sys
import numpy as np
import pandas as pd
#from landlab import RasterModelGrid
#from models.dryp.components.DRYP_io_files import get_model_settings
from models.dryp.components.DRYP_io import (
	grid_environment,
	extract_id_from_coords)
from models.dryp.components.DRYP_flow_accum import runoff_routing
from models.dryp.components.DRYP_store_functions import (
	save_map_to_rastergrid)
import rasterio
from models.dryp.components.DRYP_flow_accum import watershed

def get_watershed_area(fname_surface, fname_outlet, fname_out=None,
						fname_flowDir=None, fname_mask=None):
	"""This function read the input dataset file and
	calculate the area and indices (in landlab format). It also
	provides a map of contributing areas (flow accumulation).

	This function store all files in the same directory of the
	output files if post processing directory is not provided.
	
	Parameters
	----------
	fname_surface: str
		file name of the elevation raster map
	fname_outlet : str
		file name of the outflow raster map
	fname_floedir : str
		(optional) filename of the flow direction raster map
	fname_out : str
		(optional) filename of the output raster file

	Returns
	-------
	file
		csv file containing a list areas and node index
		asc flow accumalation map as raster file

		
	Examples
	--------

	>>> from models.dryp.components.DRYP_watershed import get_watershed_map
	>>> fname_surface = "surface.asc"
	>>> fname_flowdir = "flowdir.asc"
	>>> fname_outlet = "point.csv"

	>>> get_watershed_area(fname_surface, fname_outlet, fname_flowdir)
	"""

	# read datasets: surface, flow direction, and list of points
	surface = read_raster(fname_surface)
	
	# read flow direction
	flowDir = None
	if fname_flowDir is not None:
		flowDir = read_raster(fname_flowDir)
	
	## get raster shape and cellsize
	domain = rasterio.open(fname_surface)
	#grid_shape = (domain.height, domain.width)
	grid_size = (domain.height*domain.width)
	#grid_size = int(domain.nrows*domain.ncols)
	area_cell = np.power(domain.transform[0], 2)

	# read mask
	mask = None
	if fname_mask is not None:
		mask = read_raster(fname_mask)

	# create a raster grid environment, landlab grid
	grid = grid_environment().create_grid(
		domain.width,
		domain.height,
		domain.bounds[1],
		domain.bounds[0],
		domain.transform[0], # cell size
		mask)
	
	ro = runoff_routing(grid,
		 	grid_size,
			surface, 
			flowDir,
			np.zeros_like(surface),
			np.zeros_like(surface),
			np.zeros_like(surface),
			np.zeros_like(surface),
			)

	# get basin outlets
	# Output variables and location
	idnodes = extract_id_from_coords(grid, fname_outlet)[0]

	ro.run_runoff_one_step(
						np.ones_like(surface),# unit area
						np.zeros_like(surface),#AOF
						np.zeros_like(surface),#AOF_threshold,
						np.zeros_like(surface), #conductivity,
						np.ones_like(surface),
						np.zeros_like(surface),# no rivers
						np.full(grid_size, area_cell),
						np.zeros_like(surface),
						np.ones_like(surface)*1e5,
						None)
	
	# save files
	if fname_out is None:
		fname_out = fname_surface.split('.')[0]

	# Save contributing area as raster file
	save_map_to_rastergrid(grid, ro.discharge,
			fname_out + '_flowaccum.asc')
	
	# save list of catchement areas
	df = pd.DataFrame()
	df['IDnode'] = idnodes
	df['Area'] = ro.discharge[idnodes]
	
	fname = fname_out + '_areas.csv'
	df.to_csv(fname)

def get_watershed_mask(fname_surface, fname_outlet, fname_out=None,
					  fname_flowDir=None, fname_mask=None):
	"""Function to delineate a basin assuming an outlet
	point is provided. This function requires a flow direction map
	but if not provided the flow direction will be created
	
	Parameters
	----------
	fname_surface: str
		file name of the elevation raster map
	fname_outlet : str
		file name of the outflow raster map
	fname_floedir : str
		(optional) filename of the flow direction raster map

	fname_out : str
		(optional) filename of the output raster file

	Returns
	-------
	raster file


	Examples
	--------
	>>> from models.dryp.components.DRYP_watershed import get_watershed_map
	>>> fname_surface = "surface.asc"
	>>> fname_flowdir = "flowdir.asc"
	>>> fname_outlet = "point.csv"

	>>> get_watershed_mask(fname_surface, fname_outlet, fname_flowdir)
	
	"""

	# read datasets: surface, flow direction, and list of points
	surface = read_raster(fname_surface)
	
	# read flow direction
	flowDir = None	
	if fname_flowDir is not None:
		flowDir = read_raster(fname_flowDir)
	
	# read mask
	mask = None
	if fname_mask is not None:
		mask = read_raster(fname_mask)

	## get raster shape and cellsize
	domain = rasterio.open(fname_surface)
	grid_shape = (domain.height, domain.width)
	#grid_size = int(domain.nrows*domain.ncols)
	#area_cell = np.power(domain.transform[0], 2)

	# create a raster grid environment, landlab grid
	grid = grid_environment().create_grid(
		domain.width,
		domain.height,
		domain.bounds[1],
		domain.bounds[0],
		domain.transform[0], # cell size
		mask)
	
	# initializa watershed module
	basin = watershed(grid, surface, flowDir)

	# get basin outlets
	# Output variables and location
	idnodes = extract_id_from_coords(grid, fname_outlet)[0]

	# create array with outlets
	outlet = np.zeros_like(surface)
	outlet[idnodes] = 1

	# get watershed
	basinmask = basin.get_watersheds(outlet)

	# reshape landlab grid into a 2D numpy array
	basinmask = np.flip(basinmask.reshape(grid_shape), 0)
	
	# get raster file properties
	surface, profile, transform = open_raster(fname_surface)

	# save files
	if fname_out is None:
		fname_out = fname_surface.split('.')[0] + '_basin.asc'

	# save raster dataset
	save_raster(fname_out, basinmask, profile, transform)

def open_raster(fname):
	with rasterio.open(fname) as src:
		# Read the input raster data
		data = src.read(1)
		# Get the metadata of the input raster
		profile = src.profile
		# Get the affine transformation
		transform = src.transform
	return data, profile, transform

def get_raster_properties(fname):
	domain = rasterio.open(fname)
	grid_ncols = domain.width
	grid_nrows = domain.height
	#grid_xllcorner = domain.bounds[1]
	#grid_yllcorner = domain.bounds[0]
	grid_cellsize = domain.transform[0]
	return grid_ncols, grid_nrows, grid_cellsize

def read_raster(fname):
	return np.flip(rasterio.open(fname).read(1), 0).flatten()

def save_raster(fname, data, profile, transform):
	os.remove(fname) if os.path.exists(fname) else None
	with rasterio.open(fname, 'w', **profile) as dst:
		# Write the modified raster data
		dst.write(np.array(data, dtype=np.float32), 1)
		# Set the affine transformation
		dst.transform = transform