"""DRYP raster pre-processing tools"""
import os
import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window
from rasterio.mask import mask
from rasterio.crs import CRS
from rasterio.transform import Affine
from shapely.geometry import box
import geopandas as gpd
from rasterio.features import geometry_mask
from landlab import RasterModelGrid
from landlab.components import FlowDirectorD8
from landlab.core.utils import as_id_array
from scipy.ndimage import label

def create_raster_soil_parameters(fname_porosity, fname_psi, fname_lambda):
	"""Calculate soil water content at field capacity and available water content
	
	Parameters:
	-----------
	fname_porosity : str
		raster file name of porosity
	fname_psi : str
		raster filename of air entry pressure
	fname_lambda : str
		raster file name of soil particle distribution

	Returns:
	--------
	None
		None, but creates three raster files with the following names:

	Examples:
	--------
	>>> fname_porosity = "porosity.asc"
	>>> fname_psi = "psi.asc"
	>>> fname_lambda = "lambda.asc"
	>>> create_raster_soil_parameters(fname_porosity, fname_psi, fname_lambda)
	>>> # This will create three raster files: "field_capacity.asc", "wilting_point.asc", and "available_water_content.asc"
	>>> # with the calculated soil water content values.
	>>> # The function does not return any values, but it saves the results as raster files.
	
	"""
	# read raster files
	porosity = open_raster(fname_porosity)[0]
	psi = open_raster(fname_psi)[0]
	lambdas, profile, transform = open_raster(fname_lambda)
	
	# calculate soil water content
	field_capacity, wilting_point, available_water_content =calculate_soil_paramters(
		porosity, psi, lambdas, psi_fc=336.506, psi_wp=15295.743)

	# create files names
	fname_fc = ""
	fname_wp = ""
	fname_awc = ""

	# save soil properties as raster files
	save_raster(fname_fc, field_capacity, profile, transform)
	save_raster(fname_wp, wilting_point, profile, transform)
	save_raster(fname_awc, available_water_content, profile, transform)

def create_raster_flowdirection_dryp(fname, fname_out=None, translate=True, format_data="D8"):
	"""Create raster DRYP flow direction from a DEM or file from a raster D8 flow direction map.
	if a flow direction is provided, the function will translate it to landlab format, if not,
	the function will calculate the flow direction from the DEM and save it as raster file.
	
	Parameters:
	-----------
	fname : str
		filename path of the flow direction map, the raster
		file has to be in D8 direction format
	translate : bool
		True if the flow direction map is in D8 format, False if it is in Landlab format
	fname_out : str
		filename of the output file
		The output raster file will be created with the specified name.
		The output raster file will contain the flow direction values.
		Make sure to provide the correct file path and name for the output raster file.
		Example: "path/to/output_raster.tif"
		Note: The output raster file will be created in the same format as the input raster file.
	format_data : str
		format of the data, D8 or D* format
		- D8: D8 format (default)
		- LDD: LDD format
		- GRASS: GRASS format
		- AGNPS: AGNPS format
		- i-digit: i-digit format

	Returns:
	--------
	None
		None, but creates a raster file with the specified name.
		The raster file will contain the flow direction values in Landlab format.
		Note: The function does not return any values, but it saves the
		raster file with the specified name.

	Example:
	--------
	>>> fname = "flow_direction.asc"
	>>> fname_out = "flow_direction_landlab.asc"
	>>> create_raster_flowdirection_dryp(fname, fname_out, translate=True)
	>>> # This will create a raster file named "flow_direction_landlab.asc"
	>>> # with the flow direction values in Landlab format.
	>>> # The function does not return any values, but it saves the raster file.
	
	"""
	# read raster dataset
	flowdird8, profile, transform = open_raster(fname) 
	
	if translate is True:
		# calculate flow direction
		flowdir = transform_flowdirection_d8_to_landlab_array(
			flowdird8, format_data=format_data)

		# Update profile to use int32 for output data type
		# (cell indices can range from 0 to millions, not 0-255 as in uint8 input)
		profile = profile.copy()
		profile['dtype'] = 'int32'
	else:
		# get array shape
		shape = np.shape(flowdird8)
		# create grid
		domain = rasterio.open(fname)
		# create a raster grid environment, landlab grid
		grid = RasterModelGrid(
				(domain.height, domain.width),
				xy_spacing=domain.transform[0],
				xy_of_lower_left=(domain.bounds[0], domain.bounds[1]),
				xy_of_reference=(0.0, 0.0),
				)
		
		grid.add_field("aux_grid",
			  np.array(np.flip(flowdird8, 0), dtype=float),#.flatten(),
			  at="node")
		
		# calculate flow rirection
		fd = FlowDirectorD8(grid, 'aux_grid')
		fd.run_one_step()
	
		# 2. Creates drainage networks, flowpaths and id arrays
		# a value of 1 must be added to change from python to forttran
		flowdir = as_id_array(grid["node"]["flow__receiver_node"])
		
		# reshape array to save as raster
		flowdir = flowdir.reshape(shape)
		
		# flip raster in order to make aggree with landlab
		flowdir = np.flip(flowdir, 0)
	
	if fname_out is not None:
		save_raster(fname_out, flowdir, profile, transform)
	else:
		return flowdir, profile, transform

def create_raster_river_network(fname, threshold, fname_out=None,
								cell_area=False, fill_value=None):
	"""Create a raster file from a raster D8 flow direction map. The
	river network will be created from a flow accumulation map and a 
	threshold specified for the minimm number of cells or minimum area.
	
	Parameters:
	-----------
	fname : str
		filename path of the flow accumulation map, this file raster
		file can be created by get_watershed_area() funtion
	threshold : float
		number of cells otr area (if cell_area is False)
	fname_out : str
		filename of the output file
	cell_area : Bool
		False when area is provided, True when number of cell is
		provided
	fill_value : float
		river lenght [meters]

	Returns:
	--------
	None
		None, but creates a raster file with the specified name.
		The raster file will contain the river network values in Landlab format.
		Note: The function does not return any values, but it saves the
		raster file with the specified name.
	
	Example:
	--------

	>>> fname = "flow_accumulation.asc"
	>>> threshold = 1000	# number of cells or area in square meters
	>>> fname_out = "river_network.asc"
	>>> create_raster_river_network(fname, threshold, fname_out, cell_area=False, fill_value=None)
	>>> # This will create a raster file named "river_network.asc"
	>>> # with the river network values in Landlab format.
	>>> # The function does not return any values, but it saves the raster file.
	
	"""
	# read raster dataset
	raster, profile, transform = open_raster(fname) 
	
	# get raster properties
	attributes = rasterio.open(fname)
	area_cell = np.power(attributes.transform[0], 2)

	# check if area or number of cells is provided
	if cell_area is False:
		threshold = threshold*area_cell

	# assign values
	value = 1
	if fill_value is not None:
		value = fill_value

	# select river cells
	raster[raster < threshold] = -9999
	raster[raster >= threshold] = value
	
	# save soil properties as raster files
	if fname_out is not None:
		save_raster(fname_out, raster, profile, transform)
	else:
		return raster, profile, transform

def create_raster_bc_at_point(fname_wte, fname_bc_head,
										fname_out=None):
	"""Create a raster file from values at specified locations
	of a raster file. Only values at selcted locations are kept in
	the raster, the remained values are assined -9999
	(non data values in DRYP).
	
	Parameters:
	-----------
	fname_wte : str
		file path of the raster file
		The raster file should be in a format supported by rasterio (e.g., GeoTIFF).
		The raster file should contain the values that you want to extract at the specified locations.
		For example, if you have a raster file representing water table elevation, provide the path to that file.
		Make sure to provide the correct file path to the raster file.
		Example: "path/to/raster_file.tif"
	fname_bc_head : str
		file path of the point list
		coordinates of the points to be extracted from the raster
		are specified in the file. The file must contain two columns:
		'East' and 'North', which represent the coordinates of the points.
		These coordinates should be in the same coordinate system as the raster file.
		For example, if the raster file is in UTM coordinates, the coordinates in the file should also be in UTM.
		Make sure to provide the correct file path to the point list.
		Example: "path/to/point_list.csv"
	fname_out : str
		file path of the output raster file
		The output raster file will be created with the specified name.
		The output raster file will contain the values at the specified locations.
		Make sure to provide the correct file path and name for the output raster file.
		Example: "path/to/output_raster.tif"
		Note: The output raster file will be created in the same format as the input raster file.

	Returns:
	--------
	None
		None, but creates a raster file with the specified name.
		The raster file will contain the values at the specified locations.
		Note: The function does not return any values, but it saves the
		raster file with the specified name.
	
	Example:
	--------
	>>> fname_wte = "water_table_elevation.asc"
	>>> fname_bc_head = "boundary_conditions.csv"
	>>> fname_out = "boundary_conditions_raster.asc"
	>>> create_raster_bc_at_point(fname_wte, fname_bc_head, fname_out)
	>>> # This will create a raster file named "boundary_conditions_raster.asc"
	>>> # with the values at the specified locations.
	>>> # The function does not return any values, but it saves the raster file.

	"""
	# read list of xy coordinates as dataframe
	coordinates = pd.read_csv(fname_bc_head)

	# create a list of tuples
	coordinates = list(zip(coordinates['East'], coordinates['North']))

	# read raster dataset
	dataset = rasterio.open(fname_wte)

	# get list of indices
	indices = find_indices(dataset, coordinates)
	
	# get raster properties
	raster, profile, transform = open_raster(fname_wte)

	# create a copy of raster file
	head = raster.copy()

	# make non data all values
	raster[:] = -9999

	# get head values
	for index in indices:
		row, column = index
		raster[row, column] = head[row, column]
	if fname_out is not None:
	# save soil properties as raster files
		save_raster(fname_out, raster, profile, transform)
	else:
		return raster, profile, transform
	
def create_raster_from_shapefile(fname_shp, fname_raster, fname_out=None):
	"""This function takes a shapefile (\*.shp) and a raster file
	to create a new raster containing the shapefile geometry
	as mask
	
	Parameters:
	-----------
	fname_shp : str
		file path of shapefile
	fname_raster : str
		file path of raster file

	Returns:
	--------
	None
		None, but creates a raster file with the specified name.
		The raster file will contain the shapefile geometry as a mask.
		Note: The function does not return any values, but it saves the
		raster file with the specified name.

	Example
	-------

	>>> shapefile_path = 'test.shp'
	>>> fname_raster = "test.asc"
	>>> fname_out = "mask.asc"
	>>> create_raster_from_shapefile(shapefile_path, fname_raster, fname_out)
	>>> # This will create a raster file named "mask.asc"
	>>> # with the shapefile geometry as a mask.
	>>> # The function does not return any values, but it saves the raster file.


	"""
	# Load the shapefile as a GeoDataFrame
	gdf = gpd.read_file(fname_shp)

	# Define the raster dimensions and extent
	data, profile, transform = open_raster(fname_raster)
	grid_ncols, grid_nrows, grid_cellsize = get_raster_properties(fname_raster)

	# Create a mask for the shapefile using the raster dimensions and extent
	array = geometry_mask(gdf.geometry,
		transform=transform,
		out_shape=(grid_nrows, grid_ncols),
		invert=True)
	
	# Create a new raster with the same dimensions and extent of the input
	if fname_out is not None:
		save_raster(fname_out, array, profile, transform)
	else:
		return array, profile, transform

def create_raster_landlab_idnodes(fname, fname_out=None):
	"""Create a raster file of landlab idnodes
	
	Parameters
	----------
	fname : str
		path of raster file
		
	Returns:
	--------
	None
		None, but creates a raster file with the specified name.
		The raster file will contain the idnodes values in Landlab format.
		Note: The function does not return any values, but it saves the
		raster file with the specified name.

	Example:
	--------

	>>> fname = "raster.asc"
	>>> fname_out = "idnodes.asc"
	>>> create_raster_landlab_idnodes(fname, fname_out)
	>>> # This will create a raster file named "idnodes.asc"
	>>> # with the idnodes values in Landlab format.
	>>> # The function does not return any values, but it saves the raster file.
			
	"""
	# get raster properties
	raster, profile, transform = open_raster(fname)

	# get array shape
	shape = np.shape(raster)

	# flatten array
	raster = raster.reshape(-1)

	# create id grid
	idnodes = np.arange(len(raster), dtype=int).reshape(shape)
	idnodes = np.flip(idnodes, 0)
	
	if fname_out is not None:
		# save soil properties as raster files
		save_raster(fname_out, idnodes, profile, transform)
	else:
		return idnodes, profile, transform

def create_raster_landlab_idcorenodes(fname, fname_out=None):
	"""Create a raster file of landlab idnodes
	
	Parameters
	----------
	fname : str
		path of mask raster file
		
	Returns
	-------
	file
		idnodes raster file with name fname_out
	"""
	# get raster properties
	raster, profile, transform = open_raster(fname)

	# get array shape
	shape = np.shape(raster)

	# flip raster
	raster = np.flip(raster, 0)

	# flatten array
	raster = raster.reshape(-1)

	# get location of id nodes
	core_nodes = np.where(raster > 0)[0]
	idnodes = np.full(len(raster), -9999)
	
	# create id grid
	idnodes[core_nodes] = np.arange(len(core_nodes), dtype=int)
	idnodes = idnodes.reshape(shape)
	idnodes = np.flip(idnodes, 0)
	
	# save soil properties as raster files
	if fname_out is not None:
		save_raster(fname_out, idnodes, profile, transform)
	else:
		return idnodes, profile, transform

def open_raster(fname):
	"""read raster file
	Parameters
	----------
	fname : str
		file name of the raster
	
	Returns
	-------
	data : numpy array
		raster values
	profile : object
		raster properties
	transform : object
		transformation parameters to pass to other functions
	
	"""
	with rasterio.open(fname) as src:
		# Read the input raster data
		data = src.read(1)
		# Get the metadata of the input raster
		profile = src.profile
		# Get the affine transformation
		transform = src.transform
	return data, profile, transform

def save_raster(fname, data, profile, transform):
	"""This function saves a raster file with the specified name.
	
	Parameters:
	-----------
	fname : str
		file name of the raster
		The raster file will be created with the specified name.
		The raster file will contain the data and properties specified in the profile.
		Make sure to provide the correct file path and name for the raster file.
		Example: "path/to/raster_file.tif"
		Note: The raster file will be created in the same format as the input raster file.
	
	data : numpy array
		raster values
		The data array contains the raster values that you want to save.
		The data array should be a 2D numpy array representing the raster data.
		The data array should have the same dimensions as the raster file.
		For example, if you have a 100x100 raster, the data array should be of shape (100, 100).
		Make sure to provide the correct data array for the raster file.
		Example: np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
		Note: The data array should be in the same format as the input raster file.
		For example, if the input raster file is in GeoTIFF format, the data array should be in GeoTIFF format.
		Make sure to provide the correct data array for the raster file.
		
	profile : object
		raster properties
		The profile object contains the metadata and properties of the raster file.
		It should be obtained from the input raster file using rasterio.
		The profile object should include information such as data type, dimensions, and coordinate reference system.


	transform : object
		transformation parameters
		The transform object contains the affine transformation parameters for the raster file.
		It should be obtained from the input raster file using rasterio.
		The transform object should include information such as pixel size and origin coordinates.


	Returns:
	--------
	None
		None, but creates a raster file with the specified name.
		The raster file will contain the data and properties specified in the profile.
		Note: The function does not return any values, but it saves the raster file with the specified name.

	Example:
	--------

	>>> fname = "output_raster.asc"
	>>> data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> profile = {}
	>>> transform = Affine(1, 0, 0, 0, -1, 0)
	>>> save_raster(fname, data, profile, transform)
	>>> # This will create a raster file named "output_raster.asc"
	>>> # with the specified data and properties.
	>>> # The function does not return any values, but it saves the raster file.


	"""
	# Update the profile with the new data type and dimensions
	os.remove(fname) if os.path.exists(fname) else None
	with rasterio.open(fname, 'w', **profile) as dst:
		# Write the modified raster data
		# ensure that data has the same format type
		dst.write(np.array(data, dtype=profile['dtype']), 1)
		# Set the affine transformation
		dst.transform = transform

def read_raster(fname, flatten=True):
	"""This function reads a raster file and returns the data as a
	numpy array.
	"""
	data = np.flip(rasterio.open(fname).read(1), 0)
	if flatten:
		data = data.flatten()
	return data

def get_raster_properties(fname):
	"""This function gets the properties of a raster file.

	
	Parameters:
	-----------
	fname : str
		file name of the raster
		The raster file should be in a format supported by rasterio (e.g., GeoTIFF).
		The raster file should contain the data that you want to extract properties from.
		For example, if you have a raster file representing elevation, provide the path to that file.
		Make sure to provide the correct file path to the raster file.
		Example: "path/to/raster_file.tif"
	
	Returns:
	--------
	grid_ncols : int
		number of columns in the raster file
		The number of columns in the raster file.
		This value represents the number of pixels along the x-axis of the raster.
		Example: 100 (for a raster with 100 columns)
		grid_nrows : int
		number of rows in the raster file
		The number of rows in the raster file.
		This value represents the number of pixels along the y-axis of the raster.
		Example: 100 (for a raster with 100 rows)
		grid_cellsize : float
		cell size of the raster file
		The cell size of the raster file.
		This value represents the size of each pixel in the raster.
		Example: 30.0 (for a raster with a cell size of 30 meters)
		Note: The cell size is the same for both x and y axes in a square raster.
		Make sure to provide the correct cell size for the raster file.
	
	"""
	domain = rasterio.open(fname)
	grid_ncols = domain.width
	grid_nrows = domain.height
	#grid_xllcorner = domain.bounds[1]
	#grid_yllcorner = domain.bounds[0]
	grid_cellsize = domain.transform[0]
	return grid_ncols, grid_nrows, grid_cellsize

def getFeatures(gdf):
	"""Function to parse features from GeoDataFrame
	in such a manner that rasterio wants them
	https://automating-gis-processes.github.io/CSC18/lessons/L6/clipping-raster.html
	"""
	# Next we need to get the coordinates of the geometry
	# in such a format that rasterio wants them. This can
	# be conducted easily with following function
	import json
	return [json.loads(gdf.to_json())['features'][0]['geometry']]

def check_raster_alignaments(fname_base, fname):
	"""This function check if a rasters dataset has the same
	number of cells and grid size
	
	Parameters
	----------
	fname_base : str
		file name of the reference raster
	fname : str
		file name of the raster to check
	
	Returns
	-------
	bool
		True if raster has similar size
		False if raster does not match the original size
	"""
	# get shape of raster daataset
	shape_base = get_raster_properties(fname_base)

	# get shape of raster to check
	shape_raster = get_raster_properties(fname)

	# compare shape of raster datasets
	if (shape_raster[1] == shape_base[1]) and (shape_raster[0] == shape_base[0]):
		return True
	else:
		return print("Reference:", shape_base, "Dataset:", shape_raster, fname)

def clip_raster_by_mask_old(fname, fname_mask, fname_output):
	"""This function clip a raster file by using a mask raster file. All raster
	files must have the same size, otherwise and error will raise.
	The output file will be 

	Parameters:
	-----------    
	fname : str
		raster file name
	fname_mask : str
		file name for the clipped raster dataset
	fname_out : str
		file name for the clipped raster dataset

	Returns:
	--------
	file
		clipped raster file
	
	Examples:
	--------

	>>> fname = "raster.asc"
	>>> fname_mask = "mask.asc"
	>>> fname_output = "clipped_raster.asc"
	>>> clip_raster_by_mask(fname, fname_mask, fname_output)
	>>> # This will create a raster file named "clipped_raster.asc"
	>>> # with the clipped raster values.
	
	"""

	# open raster
	data, profile, transform = open_raster(fname_mask)

	# find bounds
	min_row, max_row, min_col, max_col = find_region_bounds(data)


    # --- pixel size from affine transform ---
	pixel_width = transform.a
	pixel_height = -transform.e  # usually negative, so take abs

    # --- convert indices to coordinates ---
    # top-left corner (min_col, min_row)
	xmin, ymax = rasterio.transform.xy(transform, min_row, min_col, offset="ul")

    # bottom-right corner (+1 to move outside the last pixel)
	xmax, ymin = rasterio.transform.xy(transform, max_row + 1, max_col + 1, offset="ul")

    # --- create extent tuple [xmin, ymin, xmax, ymax] ---
	extent = (xmin, ymin, xmax, ymax)
	
	# create and save clipped raster
	clip_raster_by_extent(fname, fname_output, extent)


def clip_raster_by_extent_old(fname, fname_output, extent):
	"""Function to clip raster files by extent.
	
	Parameters:
	-----------    
	fname : str
		raster file name
	fname_out : str
		file name for the clipped raster dataset
	extent : list of floats
		list of boundaries to clip, [xmin, ymin, xmax, ymax]
	
	Returns:
	--------
	None
		None, but creates a raster file with the specified name.
		The raster file will contain the clipped raster values.
		Note: The function does not return any values, but it saves the
		raster file with the specified name.

	Example:
	--------
	>>> fname = "raster.asc"
	>>> fname_output = "clipped_raster.asc"
	>>> extent = [xmin, ymin, xmax, ymax]
	>>> clip_raster_by_extent(fname, fname_output, extent)
	>>> # This will create a raster file named "clipped_raster.asc"
	>>> # with the clipped raster values.
	>>> # The function does not return any values, but it saves the raster file.
	
	"""
	# Open the raster file
	src = rasterio.open(fname)
	
	# Define the clipping extent using a polygon or bounding box
	# Option 1: Polygon geometry
	#polygon = gpd.read_file('path/to/your/polygon/shapefile.shp')
	#clipping_geometry = polygon.geometry.values[0]
	
	# Option 2: Bounding box coordinates (left, bottom, right, top)
	# clipping_extent = (xmin, ymin, xmax, ymax)
	# create polygon object
	shapes = box(extent[0], extent[1], extent[2], extent[3])
	
	# Insert the bbox into a GeoDataFrame
	df = gpd.GeoDataFrame({"id":1,"geometry":[shapes]})
	
	# Get the geometry coordinates by using the function.
	coords = getFeatures(df)
	
	# Perform the clipping
	clipped, out_transform = mask(src, shapes=coords, crop=True)
	
	# Get the metadata of the clipped raster
	out_meta = src.meta.copy()
	out_meta.update({
		#"driver": "GTiff",
		"height": clipped.shape[1],
		"width": clipped.shape[2],
		"transform": out_transform
	})

	# Save the clipped raster to a new file
	with rasterio.open(fname_output, "w", **out_meta) as dest:
		dest.write(clipped)

def find_region_bounds(array, add_empty_frame=True):
    """
    Finds slicing indices for the extent of a region (>0) in a 2D array.
    
    Returns:
    --------
    tuple: (min_row, max_row, min_col, max_col) as exclusive slicing indices.
           Returns None if no valid region (>0) is found.
    """
    nonzero_indices = np.nonzero(array > 0)
    
    # Check if any elements are greater than zero
    if len(nonzero_indices[0]) == 0:
        return None

    # Base minimum and maximum indices (inclusive)
    min_row = int(np.min(nonzero_indices[0]))
    max_row = int(np.max(nonzero_indices[0]))
    min_col = int(np.min(nonzero_indices[1]))
    max_col = int(np.max(nonzero_indices[1]))

    if add_empty_frame:
        # Pad bounds by 1 while keeping them safely within array dimensions
        min_row = max(min_row - 1, 0)
        min_col = max(min_col - 1, 0)
        
        # Convert maximum inclusive index to exclusive slicing index 
        # (+1 for exclusive slice, +1 for padding)
        max_row_slice = min(max_row + 2, array.shape[0])
        max_col_slice = min(max_col + 2, array.shape[1])
    else:
        # Standard exclusive slicing conversion (+1)
        max_row_slice = max_row + 1
        max_col_slice = max_col + 1

    return min_row, max_row_slice, min_col, max_col_slice


def clip_raster_by_mask(fname, fname_mask, fname_output):
    """
    Clips a raster file using a mask raster file. 
    The mask must align spatially with the target raster coordinate system.

    Parameters:
    -----------    
    fname : str
        Input raster file path to be clipped.
    fname_mask : str
        Mask raster file path used to determine the clip extent.
    fname_output : str
        Output file path for the clipped raster dataset.
    """
    # Open mask raster to extract spatial region
    with rasterio.open(fname_mask) as mask_src:
        mask_data = mask_src.read(1)  # Read band 1
        transform = mask_src.transform

        # Find pixel bounds
        bounds = find_region_bounds(mask_data)
        if bounds is None:
            raise ValueError(f"No valid mask region (>0) found in {fname_mask}.")
            
        min_row, max_row, min_col, max_col = bounds

        # Convert exclusive pixel indices directly to geospatial coordinates.
        # Uses standard 'ul' (upper-left corner) placement.
        xmin, ymax = rasterio.transform.xy(transform, min_row, min_col, offset="ul")
        xmax, ymin = rasterio.transform.xy(transform, max_row, max_col, offset="ul")

    # Create extent tuple [xmin, ymin, xmax, ymax]
    extent = (xmin, ymin, xmax, ymax)
    
    # Crop and save the source raster
    clip_raster_by_extent(fname, fname_output, extent)


def clip_raster_by_extent(fname, fname_output, extent):
    """
    Clips a raster using pure Rasterio windows without geometry masks.
    
    Parameters:
    -----------    
    fname : str
        Path to the input raster file.
    fname_output : str
        Path to save the clipped raster dataset.
    extent : list or tuple of floats
        Boundaries to clip, structured as [xmin, ymin, xmax, ymax].
    """
    xmin, ymin, xmax, ymax = extent
    
    with rasterio.open(fname) as src:
        # Calculate pixel windows directly from the spatial coordinates
        window = from_bounds(xmin, ymin, xmax, ymax, transform=src.transform)
        
        # Force round the window lengths to integer values to prevent sub-pixel distortions
        window = Window(
            col_off=int(round(window.col_off)),
            row_off=int(round(window.row_off)),
            width=int(round(window.width)),
            height=int(round(window.height))
        )
        
        # Read only the target subset data from disk
        clipped = src.read(window=window)
        out_transform = src.window_transform(window)
        
        # Update metadata for dimensions and transform offset
        out_meta = src.meta.copy()
        out_meta.update({
            "height": window.height,
            "width": window.width,
            "transform": out_transform
        })
        
        # Write the clean data segment to disk
        with rasterio.open(fname_output, "w", **out_meta) as dest:
            dest.write(clipped)


def get_transform_parameters(fname):
	"""This function read a raster file and extract the transformation
	parameters. This paramters allows to get the coordinates
	(lat/y, lon/x) from indices of a numpy array
	
	Parameters
	----------
	fname : str
		raster file name

	Returns
	-------
	crs : object
		coordinates reference system
	transform : 2D numpy array
		transformation matrix
	
	
	"""
	with rasterio.open(fname) as dataset:
		# Read the metadata
		crs = dataset.crs
		transform = dataset.transform

	crs = CRS.from_dict(crs)
	transform = Affine.from_gdal(*transform)
	
	return crs, transform

def get_lat_lon_coordinates(transform, col, row, center=True):
	"""This function gets latitude/North and longitud/East
	from set of python array index.
	
	Parameters
	----------
	transform : object
		object containing raster properties
	col : int
		column index
	row : int
		row index
	center : bool, optional
		If True, return the coordinates of the center of the pixel.
		If False, return the coordinates of the upper-left corner of the pixel.
		Default is True.
	
	Returns
	-------
	lat, lon : float
		coordinates x an y of the array indices col and row

	Examples
	--------
	>>> from DRYP_rrtools import get_lat_lon_coordinates
	>>> from DRYP_rrtools import get_transform_parameters

	>>> fname = "raster.asc"
	>>> crs, transform = get_transform_parameters(fname)
	>>> col, row = 20, 30
	>>> lat, lon = get_lat_lon_coordinates(transform, col, row)

	"""
	if center:
		lon, lat = transform*(col + 0.5, row + 0.5)
	else:
		lon, lat = transform*(col, row)

	return lon, lat


def clapp_horner_retention_curve(ipsi, porosity, psi, lambdas):
	"""Function to estimate water content at specied matric
	potentialClap and Horn water retention curve
	
	Parameters
	----------
	ipsi : float or numpy array
		matrix potential
	porosity : numpy array of floats
		water content at saturated conditions
	psi : numpy array of float
		soil ari entry pressure
	lambdas : numpy array of floats
		soil particle distribution
	
	Returns
	-------
	theta : numpy array of floats
		water content at the 
	"""
	
	return porosity*np.power(np.abs(ipsi)/np.abs(psi), -lambdas)

def calculate_soil_paramters(porosity, psi, lambdas, psi_fc=336.506, psi_wp=15295.743):
	"""This function calculate the water content at
	field capacity and the total availble water of the soli
	from Clapp and Horner
	
	Parameters
	----------
	porosity : float or numpy array
		porosity [-]
	psi : float or numpy array
		air entry pressure [cm]
	lambdas : float or numpy array
		soil particle distribution paramters
	phi_fc : float or numpy array
		suction head at field capacity [cm]
		default, phi_fc = 336.506 #cm => 33kPa
	phi_wp : float or numpy array
		suction head at wilting point [cm],
		default, phi_wp = 15295.743 # cm => 1500kPa

	Returns
	-------
	field_capacity : float or numpy array
		water content at field capacity [-]
	wilting_point : float or numpy array
		Water content at wilting point [-]
	available_water_content : float or numpy array
		availble water content,  storage capacity [-]
	"""

	# calculate water content at field capacity
	field_capacity = clapp_horner_retention_curve(psi_fc, porosity, psi, lambdas)

	# calculate water content at wilting point
	wilting_point = clapp_horner_retention_curve(psi_wp, porosity, psi, lambdas)
	
	# calculate availble water content
	available_water_content = field_capacity - wilting_point

	return field_capacity, wilting_point, available_water_content

def calculate_channel_width_from_discharge(discharge):
	"""This function estimates channel velocity from flow rate
	using the
	
	Parameters
	----------
	discharge : numpy array of floats
		discharge in m3 s-1
	
	Returns
	-------
	width : numpy array of floats
		channel width 
	"""
	# calculate channel depth [m] ====================
	depth = 0.349*np.power(discharge, 0.341)
	# calculate channel width [m]
	width_bf = 2.71*np.power(discharge, 0.557)
	return width_bf - 2.2*depth
		
	
def calculate_channel_velocity(discharge, width, slope=0.01, roughness=0.026):
	"""Calculate channel valocity

	Parameters
	----------
	discharge : numpy array of floats
		discharge in m3 s-1
	width : numpy array or float
		channel width in meters
		
	Returns
	-------
	numpy array
		channel streamflow velocity in m3 s-1
	"""
	# calculate channel depth [m] ====================
	depth = 0.349*np.power(discharge, 0.341)
	# calculate hydraulic radious
	HR = depth*(2.0*depth + width)/(width + 2.0*depth*np.sqrt(5.0))
	# calculate channel velocity (m/s)
	return roughness*np.power(HR, 2.0/3.0)*np.power(slope, 0.5)
	
def calculate_channel_residence_time(velocity, river_length):
	"""Calculate decay parameter from streamflow velocity and river length
	
	Parameters
	----------
	velocity : numpy array of floats
		river flow velocity in m3 s-1
	river_length : numpy array of floats
		river length in meters
		
	Returns
	-------
	decay : numpy array floats
		channel decay/residence time parameter
	"""
	# calculate river decay parameters: units 1/s
	return velocity/river_length

def transform_flowdirection_d8_to_landlab_array(flowdir, format_data="D8"):
	"""Function to get flow direction in landlab format from a D8
	direction map.

	GRASS pcraster format:
		135  90  45
		180   0 360
		225 270 315

	AGNPS pcraster format: Agricultural Non-Point Source Pollution Model
		8 1 2
		7 0 3
		6 5 4

	LDD pcraster format
		7 8 9
		4 0 6
		1 2 3

	D8 direction format
		32 64 128
		16 0  1
		8  4  2
	
	i-digit format 2 -> 8
		4 3 2
		5 0 1
		6 7 8

	Landlab grid
		6 7 8
		3 4 5
		0 1 2

	Parameters:
	-----------
	flowdir : numpy array of int
		flow direction map in D8 format
	format_data : str
		format of the data, D8 or D* format
		- D8: D8 format (default)
		- LDD: LDD format
		- GRASS: GRASS format
		- AGNPS: AGNPS format
		- i-digit: i-digit format

	Returns:
	--------
	drinodes: numpy array of ints
		flow direction map in landlab format

	Examples:
	--------
	>>> from DRYP_rrtools import get_landlab_flowdirection_from_d8_format
	>>> D8_direction = [		
			[4, 8, 8],
			[4, 3, 8],
			[0, 16, 16],
			]

	>>> landlab_direction = get_landlab_flowdirection_from_d8_format(D8_direction)
	>>> landlab_direction = [
				[3, 3, 4],
				[0, 0, 1],
				[0, 0, 1],
				]
	"""
	# get array shape
	shape = np.shape(flowdir)

	# ensure that flowdir is a numpy array
	flowdir = np.array(flowdir, dtype=int)

	# flip raster in order to make aggree with landlab
	flowdir = np.flip(flowdir, 0)

	# flatten array
	fdg = flowdir.reshape(-1)
	
	# create array of nodes
	dirnodes=np.arange(len(fdg), dtype=int)

	# create landlab idnodes
	ids=np.arange(len(fdg), dtype=int)
	
	# find the number of columns
	ncols=shape[1]
	
	# create an array of D* direction codes
	if format_data == "D8":
		dir_code=[1, 128, 64, 32, 16, 8, 4, 2]
	elif format_data == "LDD":
		dir_code=[6, 9, 8, 7, 4, 1, 1, 3]
	elif format_data == "GRASS":
		dir_code=[360, 45, 90, 135, 180, 225, 270, 315]
	elif format_data == "AGNPS":
		dir_code=[3, 2, 1, 8, 7, 6, 5, 4]
	else:
		dir_code=np.arange(1,9)
	
	# create list of idnodes for each D8 code
	loc=[1, ncols+1, ncols, ncols-1, -1, -ncols-1, -ncols, -ncols+1]
	print(f"Transforming flow direction from ",format_data, " format to DRYP landlab format")
	
	# replace D8 codes with landlab codes
	for idir_code, iloc in zip(dir_code, loc):
		dirnodes[np.where(fdg==idir_code)]=ids[np.where(fdg==idir_code)]+iloc
		
	# correction of the flow direction due to index outside the grid
	# make nodes at edges sink points
	
	# create id grid
	nodes = np.arange(len(fdg), dtype=int).reshape(shape)
	
	idnodes = nodes[0,:] # at the top
	dirnodes[idnodes] = idnodes 
	idnodes = nodes[:,0] # at the left
	dirnodes[idnodes] = idnodes
	idnodes = nodes[:,-1] # at the right
	dirnodes[idnodes] = idnodes
	idnodes = nodes[-1,:] # at the bottom
	dirnodes[idnodes] = idnodes
	
	return np.flip(dirnodes.reshape(shape), 0)

def find_indices(raster, coordinates, get_values=False):
	"""Finds the indices of the points in the raster given the coordinates.

	Parameters
	----------
	dataset: rasterio dataset object
		Dataset object.
	coordinates: list
		A list of tuples containing the (x, y) coordinates of the points.
	Returns
	-------
	  A list of tuples containing the (row, column) indices of the points.
	  If get_values is True, also returns a list of values at the given coordinates.
	"""
	import numpy as np
	xs = [c[0] for c in coordinates]
	ys = [c[1] for c in coordinates]
	# vectorised transform: compute all row/col indices in one call
	rows, cols = rasterio.transform.rowcol(raster.transform, xs, ys)
	rows = np.asarray(rows, dtype=int)
	cols = np.asarray(cols, dtype=int)
	indices = list(zip(rows.tolist(), cols.tolist()))
	if get_values:
		band = raster.read(1)  # read once
		values = band[rows, cols].tolist()
		return indices, values
	return indices

def create_raster_lake_label_from_bathymetry(path_bathymetry, path_lake_labels=None):
	"""Get or create a raster file with lake labels from a bathymetry, this function
	detects all lakes in the raster and assign a unique label to each lake.

	Parameters
	----------
	path_bathymetry : str
		file path of the bathymetry raster file
	path_lake_labels : str, optional
		file path of the output lake labels raster file
		The default is None, if None the function will return the lake labels
		and other lake properties as numpy arrays.
		The output raster file will be created in the same format as the input raster file.
		Example: "path/to/lake_labels.tif"
	Returns
	-------
	name_lks : numpy array
		array with lake labels
	num_features : int
		number of lakes detected
	ids_lks : list of int
		list of indices of all lake cells
	size_lks : list of int
		list of number of cells in each lake
	ids_max_depth_lks : list of int
		list of indices of the maximum depth cell in each lake
		These values represent the properties of the lakes detected in the bathymetry raster.
		The values are returned as numpy arrays and lists.
		Note: The function will return these values only if path_lake_labels is None.
		Make sure to provide the correct file path for the bathymetry raster file.
		Example: "path/to/bathymetry.tif"
		Make sure to provide the correct file path for the output lake labels raster file if needed.
		Example: "path/to/lake_labels.tif"
		Note: The function does not return any values if path_lake_labels is provided,
		but it saves the lake labels raster file and a csv file with lake properties.
	Examples
	--------
	>>> path_bathymetry = "bathymetry.tif"
	>>> path_lake_labels = "lake_labels.tif"
	>>> create_raster_lake_label_from_bathymetry(path_bathymetry, path_lake_labels)
	>>> # This will create a raster file named "lake_labels.tif"
	>>> # with the lake labels and a csv file with lake properties.
	>>> # The function does not return any values, but it saves the raster file and csv file.
	>>> # If path_lake_labels is None, the function will return the lake labels and other lake properties as numpy arrays.
	>>> path_bathymetry = "bathymetry.tif"
	>>> name_lks, num_features, ids_lks, size_lks, ids_max_depth_lks = create_raster_lake_label_from_bathymetry(path_bathymetry)
	>>> # This will return the lake labels and other lake properties as numpy arrays.
	
	
	"""

	if os.path.exists(path_bathymetry):
		# STEP 1: Read and identify lake
		# read lake names, preserve the order, do not flatten
		depth_lks = np.flip(rasterio.open(path_bathymetry).read(1), 0)#.flatten()

		# mask lakes from depth
		name_lks = depth_lks > 0
		name_lks = name_lks.astype(int)

		# label lakes
		name_lks, num_features = label(name_lks)
	
		# flatten the name array to match the grid
		name_lks_flat = name_lks.flatten()

		# POST-PROCESSING LAKES VARIABLES		
		# Step 2: For each label, collect flat indices (len=number of lakes)
		ids_group_by_label = []
		for label_num in range(1, num_features + 1):
			flat_indices = list(np.where(name_lks_flat == label_num)[0])
			ids_group_by_label.append(flat_indices)
		
		# Step 3: Get length of each lake (number of cells)
		size_lks = list(map(len, ids_group_by_label))
		
		# Step 4: Get index of all lakes
		ids_lks = list(np.where(name_lks_flat > 0)[0])
		
		# Step 5: Get index of the maximum depth for each lake
		ids_max_depth_lks = numpy_argmin_reduceat(-depth_lks.flatten()[ids_lks],
								np.append([0], np.cumsum(size_lks)[:-1])
								)
		# map the indices to the original ids_lks
		ids_max_depth_lks = [ids_lks[i] for i in ids_max_depth_lks]

		# transfer variables to the class
		if path_lake_labels is not None:
			# save lake labels as raster file
			# get raster properties
			_, profile, transform = open_raster(path_bathymetry)
			profile.update(dtype=rasterio.int32)
			save_raster(path_lake_labels, name_lks, profile, transform)
			print('Lake labels rater file saved as:', path_lake_labels)

			
			df = pd.DataFrame({
				'lake_id': np.arange(1, num_features + 1),
				'num_cells': size_lks,
				'id_max_depth': ids_max_depth_lks,
				})

			# save list of lakes and max depth as csv file
			path_lake_labels_csv = path_lake_labels.split('.')[0]+'_list.csv'
			if os.path.exists(path_lake_labels_csv):
				os.remove(path_lake_labels_csv)
			
			df.to_csv(path_lake_labels_csv, index=False)
			print('Lake properties saved as:', path_lake_labels_csv)


		else:
			return name_lks, num_features, ids_lks, size_lks, ids_max_depth_lks
		
def create_raster_flat_area_from_bathymetry(path_bathymetry, path_surface,
											path_flat_area=None, save_file=False):
	"""Flatten lakes areas of a the surface raster file. Lakes are detected from 
	bathymetry raster file. The output raster file will be created in the same format
	as the input raster file.
	Parameters
	----------
	path_bathymetry : str
		file path of the bathymetry raster file
	path_surface : str
		file path of the surface raster file
	path_flat_area : str, optional
		file path of the output flat area raster file
		The default is None, if None the function will return the flat area
		and other lake properties as numpy arrays.
		The output raster file will be created in the same format as the input raster file.
		Example: "path/to/flat_area.tif"
	save_file : bool, optional
		If True, the function will save the flat area raster file.
		The default is False.
	Returns
	-------

	"""

	name_lks, num_features, _, size_lks, ids_max_depth_lks = create_raster_lake_label_from_bathymetry(
		path_bathymetry, path_lake_labels=None)
	
	if save_file and path_flat_area is None:
		# get raster properties
		_, profile, transform = open_raster(path_bathymetry)

# Getting the min Index 
def numpy_argmin_reduceat(a, index):
	"""Get the index of the minimum value in each group of a 1D array.
	Parameters
	----------
	a : numpy array
		1D array of values.
	index : numpy array
		1D array of number of elements that define the groups.
	Returns
	-------
	min_idx : numpy array
		1D array of indices of the minimum value in each group.
	"""
	# Ensure the input is a numpy array
	n = a.max() + 1  # limit-offset
	# Create an array to hold the group indices
	id_arr = np.zeros(a.size, dtype=int)
	# Assign group indices based on the input index array
	id_arr[index] = 1
	# Cumulative sum to create unique group identifiers
	shift = n*id_arr.cumsum()
	# Shift the original array by the group indices
	sortidx = (a+shift).argsort()
	grp_shifted_argmin = index
	idx =sortidx[grp_shifted_argmin] - index
	min_idx = idx + index
	return min_idx