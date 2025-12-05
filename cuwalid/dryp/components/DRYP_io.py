import os
#import time
#import datetime
import numpy as np
import pandas as pd
from landlab import RasterModelGrid
#from landlab.io import read_esri_ascii, write_esri_ascii
#from datetime import datetime
#from netCDF4 import Dataset, num2date, date2num
#from landlab.components import FlowDirectorSteepest, FlowAccumulator
import rasterio
from scipy.ndimage import label

# Global parameters
ABC_RIVER = 0.2 # River abstraction parameter

class grid_environment(object):
	"""grid elements and state variables required for running the model"""
	def __init__(self, inputfile):
		"""this function create a grid landlab object, this function can be
		used directly from landlab rastergrid function
		"""
		if inputfile.fname_DEM != None and os.path.exists(inputfile.fname_DEM):
			with rasterio.open(inputfile.fname_DEM) as src:
				##self.crs = src.crs      # coordinate reference system
				##self.transform = src.transform  # affine transform (georeferencing info)
				#self.bounds = src.bounds  # (left, bottom, right, top)
				#self.res = src.res        # (x resolution, y resolution)
				#self.dtype = src.dtypes[0]  # data type of first band
				#self.nodata = src.nodata    # NoData value
				#self.driver = src.driver    # file format (e.g. GTiff)
			
				self.grid_ncols = src.width
				self.grid_nrows = src.height
				self.grid_xllcorner = src.bounds[1]
				self.grid_yllcorner = src.bounds[0]
				self.grid_cellsize = src.transform[0]

		else:
			raise Exception("A digital elevation model map must be supplied")
		
		# define grid size for model arrays
		self.grid_size = self.grid_ncols*self.grid_nrows

	def create_grid(self, domain):
		"""This function create a lanadlab grid object

		Parameters
		----------
		domain:	numpy array
			array defining the model domain, core nodes >0, inactive nodes <=0
	
		Returns
		-------
		grid:	landlab grid

		"""
		grid = create_landlab_grid(
			self.grid_ncols,
			self.grid_nrows,
			self.grid_xllcorner,
			self.grid_yllcorner,
			self.grid_cellsize,
			domain=domain)
		return grid
	
	def create_projected_grid(self, domain, projected=False):
		"""This function create a projected grid (approximate Cartesian grid)
		using WGS84 approximation where the cell size is provided in degrees.
		
		Parameters
		----------
		None

		Returns
		-------
		dict
			A dictionary with:
			- 'lon' : 2D array of longitudes (degrees)
			- 'lat' : 2D array of latitudes (degrees)
			- 'x'   : 2D array of x coordinates (m, east)
			- 'y'   : 2D array of y coordinates (m, north)
			- 'mean_lat' : mean latitude used in the approximation
		"""
		grid = create_grid_from_extent(
			self.grid_ncols,
			self.grid_nrows,
			self.grid_yllcorner,
			self.grid_xllcorner,
			self.grid_cellsize,
			domain=domain,
			projected=projected)
		
		return grid
	
	def compute_inactive_links(self, grid, domain):
		"""Compute inactive links for the rectangular grid.

		Rules:
		- A link is active only if both its end nodes are active.
		- If a link connects an active node with an inactive node, the link is inactive.

		Parameters
		----------
		grid : dict
			Grid dictionary returned by _generate_rectangular_grid_data (must contain 'I' and 'J' arrays).
		domain : array_like
			1D flattened domain array where active nodes have values > 0.
		Returns
		-------
		inactive_links : numpy.ndarray
			1D array of link indices that are inactive.
		active_link_mask : numpy.ndarray
			boolean array (same length as grid['I']) True where link is active.
		"""
		inactive_links, active_links = _compute_inactive_links(grid, domain)

		grid['inactive_links'] = inactive_links
		grid['active_link_mask'] = active_links

		return grid

def create_grid_from_extent(ncols, nrows, lon_min, lat_min, cellsize, domain=None, projected=False):
	"""
	Create a projected grid (approximate Cartesian grid) using WGS84
	approximation where the cell size is provided in degrees.
	Parameters
	----------
	ncols : int
	    Number of grid columns (width).
	nrows : int
	    Number of grid rows (height).
	lon_min : float
	    Longitude of the lower-left corner (degrees).
	lat_min : float
	    Latitude of the lower-left corner (degrees).
	cellsize_deg : float
	    Grid cell size (degrees).
	Returns
	-------
	dict
	    A dictionary with:
	    - 'lon' : 2D array of longitudes (degrees)
	    - 'lat' : 2D array of latitudes (degrees)
	    - 'x'   : 2D array of x coordinates (m, east)
	    - 'y'   : 2D array of y coordinates (m, north)
	    - 'mean_lat' : mean latitude used in the approximation
	"""
	# Generate 1D coordinate arrays (cell centers)
	lon = np.linspace(lon_min + cellsize / 2,
	                  lon_min + (ncols - 0.5) * cellsize,
	                  ncols)
	lat = np.linspace(lat_min + cellsize / 2,
	                  lat_min + (nrows - 0.5) * cellsize,
	                  nrows)
	
	# 2D meshgrid of geographic coordinates
	lon2d, lat2d = np.meshgrid(lon, lat)

	if not projected:
		# Compute mean latitude for conversion approximation
		mean_lat = np.mean(lat)
		mean_lat_rad = np.deg2rad(mean_lat)
		# Conversion factors (WGS84) from degrees to meters

		# meters_per_deg_lat = meters_dy
		meters_dy = 111132.92 - 559.82 * np.cos(2 * mean_lat_rad) + 1.175 * np.cos(4 * mean_lat_rad)
		# meters_per_deg_lon = meters_dx
		meters_dx = 111412.84 * np.cos(mean_lat_rad) - 93.5 * np.cos(3 * mean_lat_rad)
		
		# Compute Cartesian coordinates (relative to lower-left corner)
		x = (lon2d - lon_min) * meters_dx
		y = (lat2d - lat_min) * meters_dy
		#x = (lon - lon_min) * meters_per_deg_lon
		#y = (lat - lat_min) * meters_per_deg_lat
	else:
		# For projected grid, assume cellsize is already in meters

		meters_dx, meters_dy = np.meshgrid(np.full(len(lon), cellsize, dtype=float),
									 np.full(len(lat), cellsize, dtype=float))	
		# Compute Cartesian coordinates (relative to lower-left corner)
		x = lon#2d# - lon_min) * meters_dx
		y = lat#2d# - lat_min) * meters_dy

	# Create grid dictionary
	grid = _generate_rectangular_grid_data(ncols, nrows, meters_dx.flatten(), meters_dy.flatten())

	# Add coordinate arrays
	grid['x'] = x
	grid['y'] = y

	if domain is None:
		# create core nodes array
		domain = center_ones(nrows, ncols).flatten()

	grid['core_nodes'] = np.where(domain > 0)[0]

	return grid

def center_ones(nrows: int, ncols: int):
    """
    Return a 2D NumPy array with zeros on the border and ones in the interior.
    Border thickness = 1. If nrows<=2 or ncols<=2 returns all zeros.

    Args:
        nrows (int): number of rows
        ncols (int): number of columns

    Returns:
        numpy.ndarray: array shape (nrows, ncols)

	Example:
		>>> center_ones(5, 6)
		array([[0, 0, 0, 0, 0, 0],
			   [0, 1, 1, 1, 1, 0],
			   [0, 1, 1, 1, 1, 0],
			   [0, 1, 1, 1, 1, 0],
			   [0, 0, 0, 0, 0, 0]])
		
    """

    if nrows <= 2 or ncols <= 2:
        return np.zeros((nrows, ncols), dtype=int)

    a = np.zeros((nrows, ncols), dtype=int)
    a[1:-1, 1:-1] = 1
    return a

def _generate_rectangular_grid_data(N_x, N_y, Dx_cell, Dy_cell):
	"""
	Generates the geometric and hydraulic data for a regular 
	2D rectangular mesh with NON-UNIFORM cell sizes.
	
	Returns: A dictionary containing all necessary grid arrays.
	"""
	# Total number of cells
	N_cells = N_x * N_y    
	# A. Cell Properties
	Cell_Areas = Dx_cell * Dy_cell # Area of each cell (Ai)
	
	# B. Connectivity (I, J arrays for vectorization)
	I_list = [] # current node index
	J_list = [] # neighbor node index
	L_ij_list = [] # face length between cells i and j
	Delta_L_ij_list = [] # distance between centroids of cells i and j
	d_i_list = [] # distance from centroid of cell i to face ij
	d_j_list = [] # distance from centroid of cell j to face ij

	# Helper function to get 1D index from 2D coordinates
	def to_1d(i, j):
		return j * N_x + i

	# Loop through all internal cells to define connections
	for j in range(N_y):
		for i in range(N_x):
			idx = to_1d(i, j)
			
			# --- East/West Connections (Flow in x-direction) ---
			if i < N_x - 1: # East neighbor exists
				neighbor_idx = to_1d(i + 1, j)
				
				# Host/Neighbor cell dimensions
				dx_i = Dx_cell[idx]
				dx_j = Dx_cell[neighbor_idx]
				
				# Face length (L_ij) is based on the shared (vertical) dimension (Dy)
				face_len_y = (Dy_cell[idx] + Dy_cell[neighbor_idx]) / 2.0
				
				# Connection 1: I -> J
				I_list.append(idx)
				J_list.append(neighbor_idx)
				L_ij_list.append(face_len_y)                    # Face length (L_ij)
				Delta_L_ij_list.append(dx_i / 2.0 + dx_j / 2.0) # Centroid distance (Delta_L_ij)
				d_i_list.append(dx_i / 2.0)                     # Host centroid to face (d_i)
				d_j_list.append(dx_j / 2.0)                     # Neighbor centroid to face (d_j)
				
				# Connection 2: J -> I
				I_list.append(neighbor_idx)
				J_list.append(idx)
				L_ij_list.append(face_len_y)
				Delta_L_ij_list.append(dx_i / 2.0 + dx_j / 2.0)
				d_i_list.append(dx_j / 2.0) # d_i (J) is now dx_j/2
				d_j_list.append(dx_i / 2.0) # d_j (I) is now dx_i/2

			# --- North/South Connections (Flow in y-direction) ---
			if j < N_y - 1: # North neighbor exists
				neighbor_idx = to_1d(i, j + 1)
				
				# Host/Neighbor cell dimensions
				dy_i = Dy_cell[idx]
				dy_j = Dy_cell[neighbor_idx]
				
				# Face length (L_ij) is based on the shared (horizontal) dimension (Dx)
				face_len_x = (Dx_cell[idx] + Dx_cell[neighbor_idx]) / 2.0
				
				# Connection 1: I -> J
				I_list.append(idx)
				J_list.append(neighbor_idx)
				L_ij_list.append(face_len_x)                    # Face length (L_ij)
				Delta_L_ij_list.append(dy_i / 2.0 + dy_j / 2.0) # Centroid distance (Delta_L_ij)
				d_i_list.append(dy_i / 2.0)                     # Host centroid to face (d_i)
				d_j_list.append(dy_j / 2.0)                     # Neighbor centroid to face (d_j)

				# Connection 2: J -> I
				I_list.append(neighbor_idx)
				J_list.append(idx)
				L_ij_list.append(face_len_x)
				Delta_L_ij_list.append(dy_i / 2.0 + dy_j / 2.0)
				d_i_list.append(dy_j / 2.0) # d_i (J) is now dy_j/2
				d_j_list.append(dy_i / 2.0) # d_j (I) is now dy_i/2

	#N_connections = len(I_list)
	#print(f"Total connections established: {N_connections}")
	
	return {
		'N_cells': N_cells,
		'N_x': N_x,
		'N_y': N_y,
		'Areas': Cell_Areas,
		'Dx_cell': Dx_cell, # Store for visualization/debug
		'Dy_cell': Dy_cell, # Store for visualization/debug
		'I': np.array(I_list),           # Host cell indices (i)
		'J': np.array(J_list),           # Neighbor cell indices (j)
		'L_ij': np.array(L_ij_list),	# Face lengths between cells
		'Delta_L_ij': np.array(Delta_L_ij_list), # Distances between centroids
		'd_i': np.array(d_i_list), # Distance from centroid of cell i to face ij
		'd_j': np.array(d_j_list), # Distance from centroid of cell j to face ij
	}

def _compute_inactive_links(grid, domain):
    """
    Compute inactive links for the rectangular grid.

    Rules:
    - A link is active only if both its end nodes are active.
    - If a link connects an active node with an inactive node, the link is inactive.

    Parameters
    ----------
    grid : dict
        Grid dictionary returned by _generate_rectangular_grid_data (must contain 'I' and 'J' arrays).
    domain : array_like
        1D flattened domain array where active nodes have values > 0.

    Returns
    -------
    inactive_links : numpy.ndarray
        1D array of link indices that are inactive.
    active_link_mask : numpy.ndarray
        boolean array (same length as grid['I']) True where link is active.
    """

    if 'I' not in grid or 'J' not in grid:
        raise ValueError("grid must contain 'I' and 'J' arrays of link connectivity")

    I = np.asarray(grid['I'], dtype=int)
    J = np.asarray(grid['J'], dtype=int)
    domain = np.asarray(domain)

    # active node mask: True for active nodes
    active_node = domain > 0

    # link is active only if both end nodes are active
    active_link_mask = np.logical_and(active_node[I], active_node[J])

    # inactive link indices
    inactive_links = np.where(~active_link_mask)[0]

    return inactive_links, active_link_mask

def create_landlab_grid(ncol, nrow, xllcorner, yllcorner, cellsize, domain=None):
	"""this function create a grid landlab object, this function can be
	used directly from landlab rastergrid function
	
	Parameters
	----------
	ncol:		number of column of the grid, grid width (integer)
	nrow:		number of column of the grid, grid width (integer)
	xllcorner:	lower left x coordinate
	yllcorner:	lower left x coordinate
	cellsize:	grid spacing, size of the model cells
	
	Returns
	-------
	grid:	landlab grid
	"""
	grid = RasterModelGrid((nrow, ncol), xy_spacing=cellsize,
		xy_of_lower_left=(yllcorner, xllcorner), xy_of_reference=(0.0, 0.0),
		#xy_axis_name=('x', 'y'),
		#xy_axis_units='-',
		#bc=None
		)
	
	if domain is not None:
		idomain = np.where(domain > 0)[0]
		grid.status_at_node[idomain] = grid.BC_NODE_IS_CORE
		idomain = np.where(domain <= 0)[0]
		grid.status_at_node[idomain] = grid.BC_NODE_IS_CLOSED
	
	return grid

class index_handler(object):
	def __init__(self):
		pass
	
	def get_core_nodes(self, grid):
		"""This function return the core nodes of the grid
		Parameters
		----------
		grid:	landlab grid object

		Returns
		-------
		core_nodes:	numpy array
			array of core nodes ids
		"""
		core_nodes = grid.core_nodes
		return core_nodes
	
def get_index_from_coord_file(grid, filename):
	""" This function reads data points to report model results
	Values at each point will be extracted for all components depending
	on the specified points:
	OF:	surfave component
	UZ:	soil and riparian component
	GW: saturated component
	Parameters
	-----
	grid:	landlab grid object
	inputfile:	python obkject containing a list of points
	Returns
	------
	list of nodes where values will be extracted
	"""				
	# Reading output points
	xpoint, ypoint = read_point_coordinates(filename)
	idpoint, idypoint_active = extract_idnode_from_coords(grid,
		xpoint, ypoint)
	
	return idpoint, idypoint_active


class surface_parameters(object):
	"""Setting model input varables and environmental states
	"""
	def __init__(self, inputfile):
		"""Create variables to store model states and input data sets.
		Read all input datasst and variables for all components
		"""
		# build the data classes
		# ================ Reading surface water model inputs ==============
		
		#print('******************* Reading Input Files ********************')
		#print(inputfile.fname_DEM)
		# Reading digital elevation model
		if inputfile.fname_DEM != None and os.path.exists(inputfile.fname_DEM):
			domain = rasterio.open(inputfile.fname_DEM)
			#print(domain.transform[0])
			self.grid_ncols = domain.width
			self.grid_nrows = domain.height
			self.grid_xllcorner = domain.bounds[1]
			self.grid_yllcorner = domain.bounds[0]
			self.grid_cellsize = domain.transform[0]

			self.surface = np.array(
				np.flip(rasterio.open(inputfile.fname_DEM).read(1), 0).flatten(),
				dtype=float)
			
		else:
			raise Exception("A digital elevation model map must be supplied")
		
		#print(self.surface)
		# define grid size for model arrays
		grid_size = len(self.surface)

		# Reading river banks
		if inputfile.fname_ripwidth != None and os.path.exists(inputfile.fname_ripwidth):
			self.river_banks= np.flip(rasterio.open(inputfile.fname_ripwidth).read(1), 0).flatten()
		else:
			self.river_banks = np.full(grid_size, 100.0, dtype=float)
		
		self.river_banks[self.river_banks > grid_size] = grid_size
		#self.river_banks = 50.0 # metres
		#if self.river_banks > self.grid_cellsize:
		#	self.river_banks = domain.transform[0]


		# Catchment area: raster file of ceros and ones: ones represent the main cathment
		# The area can be the model domain or any area inside the model domain
		if inputfile.fname_Mask == None or not os.path.exists(inputfile.fname_Mask):
			mask = np.flip(rasterio.open(inputfile.fname_DEM).read(1), 0)#.flatten()
			# make domain edges not active
			mask[0,0:self.grid_ncols-1] = -9999
			mask[self.grid_nrows-1,0:self.grid_ncols] = -9999
			mask[0:self.grid_nrows-1,0] = -9999
			mask[0:self.grid_nrows-1,self.grid_ncols-1] = -9999
			self.mask = mask.astype(int).flatten()
			
			print('Basin boundary...................not provided')
		else:
			self.mask = np.flip(rasterio.open(inputfile.fname_Mask).read(1), 0).astype(int).flatten()
		#print(self.mask)
		# define model domain for calculation
		self.mask[self.mask > 0] = 1
		self.mask[self.mask < 0] = 0
		#print(self.mask)
		# Reading the raster file of river network
		if inputfile.fname_River != None and os.path.exists(inputfile.fname_River):     
			self.riv_length= np.flip(rasterio.open(inputfile.fname_River).read(1), 0).flatten()
		else:
			self.riv_length = np.full(grid_size, self.grid_cellsize, dtype=float)#
			print('River network....................not provided')
			print('All cells are considered rivers with length of grid size')
		
		self.river_cells = np.zeros(grid_size, int)
		self.river_cells[self.riv_length > 0] = 1
		self.river_cells[self.mask <= 0] = 0
		
		# Reading the raster file of river width		
		if inputfile.fname_RiverWidth == None or not os.path.exists(inputfile.fname_RiverWidth):
			self.riv_width = np.full(grid_size, 10.0, dtype=float)
			print('River width......................not provided. Global default applied of W = 10 m')
		else:
			self.riv_width = np.flip(rasterio.open(inputfile.fname_RiverWidth).read(1), 0).flatten()
			
		# Reading the raster file of river elevation		
		if inputfile.fname_RiverElev == None or not os.path.exists(inputfile.fname_RiverElev):
			self.riv_elevation = self.surface[:]
			print('River bottom......................not provided')
			print('River bottom elevation: surface elevation')
		else:
			self.riv_elevation = np.flip(rasterio.open(inputfile.fname_RiverElev).read(1), 0).flatten()
			
		# Reading a raster file of flow direction in LandLab format (receiving node ID)
		if inputfile.fname_FlowDir != None and os.path.exists(inputfile.fname_FlowDir):
			self.FlowDir = np.flip(rasterio.open(inputfile.fname_FlowDir).read(1), 0).flatten()
		else:
			self.FlowDir = None
			print('Flow direction...................not provided')
			#self.act_update_flow_director = True

		# LAKES COMPONENT ========================================================================
		# read maximum surface water elevation of lakes
		if inputfile.fname_bathymetry != None and os.path.exists(inputfile.fname_bathymetry):
			z_lakes = np.flip(rasterio.open(inputfile.fname_bathymetry).read(1), 0).flatten()
			z_lakes[z_lakes<0] = 0
			self.bathymetry = self.surface - z_lakes
		else:
			print('Lake bathymetry..................not provided. Global default z')
			self.bathymetry = self.surface[:]
		#print(self.bathymetry, self.surface)
		#print(v)
		# CHANNEL ===============================================================================
		# Channel hydraulic parameters
		# Assuming a flow velocity of 1 m/s => 3600 m/h
		if inputfile.fname_kTchannel == None or not os.path.exists(inputfile.fname_kTchannel):			
			self.decay = np.full(grid_size, inputfile.kTch/self.grid_cellsize, dtype=float)
			print('Channel decay parameter..........not provided')
			print('Assumed value equivalent to a velocity of 1m/s')
		else:		
			self.decay = np.flip(rasterio.open(inputfile.fname_kTchannel).read(1), 0).flatten()
			self.decay = self.decay*inputfile.kTch
		#self.decay = (inputfile.kT_units*3600.0*inputfile.kTch/self.grid_cellsize)
		#river_banks = 30.0 # It is hard coded for now and will be pass as a raster grid
		#print(inputfile.kTch)
		# Read saturated hydraulic conductivity channel
		if inputfile.fname_Ksat == None or not os.path.exists(inputfile.fname_Ksat):			
			#self.Ksat = np.flip(rasterio.open(inputfile.fname_ksat).read(1), 0).flatten()
			self.Ksat = np.ones(grid_size, dtype=float)
			print('Channel Ksat.....................not provided')
			print('Assumed equal to soil Ksat')
		else:		
			self.Ksat = np.flip(rasterio.open(inputfile.fname_Ksat).read(1), 0).flatten()
			
		# Changing channel Ksat_ch units from mm/h to m/dt -> m/h
		self.Ksat = self.Ksat*0.001*inputfile.kKch*self.mask
		
		# Calculating streambed conductivity [m3/h]
		self.conductivity = self.Ksat*self.riv_width*self.riv_length*self.mask
		#self.SS_loss = self.Ksat * self.riv_length * self.riv_width
			 
		# calculating cells area [m2]
		self.area_cells = np.power(self.grid_cellsize, 2)#*self.area_catch_factor
		
		#self.area_cells_hills = rg.dx*rg.dy*rg.at_node['cth_area_k']
		
		area_bank_cells = self.river_cells*self.riv_length*self.river_banks#(
			#self.riv_width+2*self.river_banks
			#)
		
		self.area_bank_cells = np.where(area_bank_cells > self.area_cells,
				  self.area_cells, area_bank_cells)

		# read initial conditions of channel flow: in m3/h
		if inputfile.fname_Qo == None or not os.path.exists(inputfile.fname_Qo):			
			self.Qo = np.zeros(grid_size, dtype=float)
			print('Initial channel storage..........not provided, assumed 0.0 m3')
			#print('Assumed value equivalent to a velocity of 1m/s')
		else:		
			self.Qo = np.flip(rasterio.open(inputfile.fname_Qo).read(1), 0).flatten()
			
		#self.area_catch_factor = (rg.at_node['cth_area_k']
		#	/ np.sum(rg.at_node['cth_area_k'][self.basin_nodes]))
		
		#self.area_river_factor = np.zeros_like(grid_size)
		#self.area_river_factor[self.river_ids_nodes] = (1 / np.sum(
		#	self.area_catch_factor[self.basin_nodes]))
		#self.area_cth = 1/np.sum(self.area_cath_factor[self.basin_nodes])
		# Calculate area of river banks, riparian zone
		#if self.grid_cellsize > inputfile.river_banks:		
		#	# if river banks are smaller than grid size
		#	self.area_cells_banks[self.riv_nodes] = (riv_length[self.riv_nodes]
		#		* (riv_width[self.riv_nodes]+2*inputfile.river_banks))
				
		#	self.area_cells_banks = np.where(self.area_cells_banks > np.power(rg.dx, 2),
		#			np.power(rg.dx, 2), self.area_cells_banks)
			
		#else:
			# if river banks are bigger than grid size
			# the riparian area is equal to the grid size
		#	self.area_cells_banks[self.riv_nodes] = (np.power(rg.dx,2)
		#			    *self.area_catch_factor[self.riv_nodes])
		
		# inactive cells, cells outside the catchment
		#self.mask_grid = np.ones(len(aux_mask), dtype=int) - aux_mask
		
		# riparian area factor [-]: area_rip/area_cell
		# to pass from rip_cell to model_cell
		self.rip_to_cell_area_factor = self.area_bank_cells/self.area_cells
		self.cell_to_rip_area_factor = np.zeros_like(self.rip_to_cell_area_factor, dtype=float)
		self.cell_to_rip_area_factor[self.area_bank_cells > 0] = (
			self.area_cells/
			self.area_bank_cells[self.area_bank_cells > 0])
		
		# hillslope area cell factor [-]
		#self.hill_factor = aux_mask*self.area_cells_hills/self.area_cells
		
		# proportion of riparian area in each cell [-]
		# to pass from [m3] -> [mm]
		self.volume_to_depth_factor_rip = np.zeros(grid_size, dtype=float)
		self.volume_to_depth_factor_rip[self.area_bank_cells > 0] = (
			1000./self.area_bank_cells[self.area_bank_cells > 0])
		self.grid_size = grid_size
		
		self.area_river = self.river_cells*self.riv_length*self.riv_width

		# this axis have to be flipped to match landlab grid
		lat_end = self.grid_xllcorner + self.grid_cellsize*self.grid_nrows
		self.lat = np.arange(self.grid_xllcorner, lat_end, self.grid_cellsize)[:self.grid_nrows]
		lon_end = self.grid_yllcorner + self.grid_cellsize*self.grid_ncols
		self.lon = np.arange(self.grid_yllcorner, lon_end, self.grid_cellsize)[:self.grid_ncols]
		#print(self.surface)
		#print(v)
		pass
	# Find coordinates of points in model components
#	def points_output(self, inputfile):
#		""" This function reads data points to report model results
#		Values at each point will be extracted for all components depending
#		on the specified points:
#		OF:	surfave component
#		UZ:	soil and riparian component
#		GW: saturated component
#		Parameters
#		-----
#		inputfile:	python obkject containing a list of points
#
#		Returns
#		------
#		list of nodes where values will be extracted
#		"""				
#		# Reading output points
#		gaugeid = get_index_from_coord_file(self.grid,
#			inputfile)
#		
#		return gaugeid


def set_initial_conditions(grid_size, Droot, head, surface, 
		    bathymetry, extintion_depth, cell_size, gw_activated):
	"""This function check for initial condition
	
	Parameters
	----------
	theta:	initial soil moisture at unsaturated zone [-]
	rtheta:	inital soil moisturea at riparian zone [-]
	Droot:	rooting depth [mm]
	head:	water table elevation [m]
	surface:	sorface elevation [m]
	extintion_depth: depth at which plants cannot take water [m]
	
	Returns
	-------
	head :	numpy array
		initail water table [m]
	theta :	numpy array
		initial soil moisture at unsaturated zone [-]
	rtheta : numpy array
		inital soil moisturea at riparian zone [-]
	Duz : numpy array
		variable unsaturated thickness [mm]
	z_extintion : numpy array
		elevation of plan extintion depth [m]
	river_sat_deficit : numpy array
		maximum volume of water allowed in in the riparian zone
		and below the riparian zone (m3)
	"""
	if gw_activated > 0:
		# Calculating intial groundwater river deficit
		river_sat_deficit = (surface - head)*np.power(cell_size, 2)
		
		# setting initial conditions for soil depth (units: mm)
		Duz = (bathymetry - head)*1000
		Duz[Duz < 0] = 0
		Duz = np.where(Duz > Droot,
				Droot, Duz)
		
	else:
	#	print("Groundwater component not used")
		# set water table below the soil depth [m]
		head = bathymetry - Droot*0.001
		
		# setting unsaturated zone depth equal to rooting depth [mm]
		Duz = Droot[:]
		
		# adding the saturated deficit [m3]
		# setting a high saturated deficit to allow free drainage
		river_sat_deficit = np.full(len(Droot), 1000*np.power(cell_size, 2), dtype=float)
		
	# calculate the extintion elevation
	z_extintion = bathymetry - extintion_depth

	Ft0 = None
	SORP0 = None
	t_0 = None
	dry_day = None
	
	return head, Duz, z_extintion, river_sat_deficit, Ft0, SORP0, t_0, dry_day

class soil_parameters(object):
	"""Setting model input varables and environmental states
	"""
	def __init__(self, grid_size, inputfile):
		"""Read soil layer parameters
		Parameters
		------
		grid_size:	size of the model domain
		inputfile:	list of file manes for soil parameters
		
		Returns
		-------
		"""
		#print("Reading soil parameter for soil layer")	
		
		# Reading Soil saturated hydraulic conductivity
		if inputfile.fname_Ksat == None or not os.path.exists(inputfile.fname_Ksat):
			self.Ksat = np.ones(grid_size, dtype=float)
			print('Hydraulic conductivity...........not provided. Global default applied of 1.0 mm/h')
		else:
			self.Ksat = np.flip(rasterio.open(inputfile.fname_Ksat).read(1), 0).flatten()
					
		# Change units and applying scale factor kKs
		#self.Ksat = (self.Ksat*inputfile.kKsat)
		#self.Ksat = (self.Ksat*inputfile.unit_sim_k*inputfile.kKsat)
				
		# Reading residual water content
		#if inputfile.fname_theta_r == None or not os.path.exists(inputfile.fname_theta_r):
		#	self.theta_res = np.zeros(grid_size)
		#	self.theta_res[:] += 0.025
		#	print('Residual moisture content..... not provided as raster. Global default applied of 0.025')
		#else:
		#	self.theta_res = np.flip(rasterio.open(inputfile.fname_theta_r).read(1), 0).flatten()
			
		# Reading Wilting point field
		if inputfile.fname_theta_wp == None or not os.path.exists(inputfile.fname_theta_wp):
			self.theta_wp = np.full(grid_size, 0.05, dtype=float)
			print('Wilting point....................not provided. Global default applied of 0.05')
		else:
			self.theta_wp = np.flip(rasterio.open(inputfile.fname_theta_wp).read(1), 0).flatten()
				
		# Read Saturated water content (porosity)
		if inputfile.fname_n == None or not os.path.exists(inputfile.fname_n):
			self.theta_sat = np.full(grid_size, 0.40, dtype=float)
			print('Porosity.........................not provided. Global default applied of 0.4')
		else:
			self.theta_sat = np.flip(rasterio.open(inputfile.fname_n).read(1), 0).flatten()
			
		# Reading available water content: raster file		
		if inputfile.fname_theta_AWC == None or not os.path.exists(inputfile.fname_theta_AWC):
			theta_AWC = np.full(grid_size, 0.10, dtype=float)
			print('Available Water Content..........not provided. Global default applied of 0.10')
		else:
			theta_AWC = np.flip(rasterio.open(inputfile.fname_theta_AWC).read(1), 0).flatten()

		self.theta_fc = theta_AWC + self.theta_wp

		# Exponent for soil moisture - matrix potential relation
		# Rawls (1982), and Clapp and Hornberger (1978)
		if inputfile.fname_b_SOIL == None or not os.path.exists(inputfile.fname_b_SOIL):
			self.lambdas = np.full(grid_size, 10.05, dtype=float)
			print('Soil particle distribution par...not provided. Global default applied of 10.5')
		else:
			self.lambdas = np.flip(rasterio.open(inputfile.fname_b_SOIL).read(1), 0).flatten()
			
		# air-entry/saturated capillary potential, [mm]
		if inputfile.fname_PSI == None or not os.path.exists(inputfile.fname_PSI):
			psi_a = np.full(grid_size, 153.0)
			print('Suction head.....................not provided. Global default applied of 153 mm')
		else:
			psi_a = np.flip(rasterio.open(inputfile.fname_PSI).read(1), 0).flatten()
			
		# Sorptivity for the Campbell model
		self.PSI = psi_a*(self.lambdas*2+2.5)/(self.lambdas+2.5)
		
		# Exponent c for Rawls (1982), and Clapp and Hornberger (1978)
		# c_SOIL = np.array(self.lambdas)*2+2.5
		# Campbell (1974)
		self.c_SOIL = 2.0/np.array(self.lambdas) + 3.0
		
		# Reading soil depth map: raster file [mm]
		if inputfile.fname_SoilDepth == None or not os.path.exists(inputfile.fname_SoilDepth):
			self.Droot = np.full(grid_size, 1000.0, dtype=float)
			#self.depth_uz *= 1000.0	# default value 1000 mm
			print('Rooting depth....................not provided. Global default applied of 1000mm')
		else:
			self.Droot = np.flip(rasterio.open(inputfile.fname_SoilDepth).read(1), 0).flatten()
			self.Droot = np.array(self.Droot, dtype=float)
		# Applying scale factor kDroot
		#self.Droot *= inputfile.kDroot
		#self.Droot = np.array(self.depth_uz)

		# Reading initial available water content: raster file		
		if inputfile.fname_theta == None or not os.path.exists(inputfile.fname_theta):
			self.theta = self.theta_wp+0.01*theta_AWC
			print('Initial water content............not provided, dry condition assumed (wiltinf point)')
		else:
			self.theta = np.flip(rasterio.open(inputfile.fname_theta).read(1), 0).flatten()

		# store factors in the object
		self.kKsat_soil = inputfile.kKsat
		self.kDroot = inputfile.kDroot

		#self.theta_fc = theta_AWC + self.theta_wp
	
	def apply_factor_ksat(self, kKsat_soil=None):
		"""Apply scale factor to soil saturated hydraulic conductivity
		Parameters
		----------
		kKsat_soil:	scale factor for soil saturated hydraulic conductivity

		Returns
		-------
		"""
		if kKsat_soil is not None:
			kKsat_soil[kKsat_soil == 1.0] = self.kKsat_soil
			self.Ksat = self.Ksat * kKsat_soil
		else:
			self.Ksat = self.Ksat*self.kKsat_soil

	def apply_factor_Droot(self, kDroot=None):
		"""Apply scale factor to soil rooting depth
		Parameters
		----------
		kDroot:	scale factor for soil rooting depth

		Returns
		-------
		"""
		if kDroot is not None:
			self.Droot = self.Droot * kDroot
		else:
			self.Droot = self.Droot * self.kDroot

	

	def print_soil_parameters(self):
		print('Soil saturated hydraulic conductivity [mm/h]:')
		print(self.Ksat)
		print('Soil wilting point [-]:')
		print(self.theta_wp)
		print('Soil field capacity [-]:')
		print(self.theta_fc)
		print('Soil porosity [-]:')
		print(self.theta_sat)
		print('Soil particle distribution parameter [-]:')
		print(self.lambdas)
		print('Soil suction head [mm]:')
		print(self.PSI)
		print('Soil exponent c [-]:')
		print(self.c_SOIL)
		print('Soil rooting depth [mm]:')
		print(self.Droot)
		print('Initial soil moisture [-]:')
		print(self.theta)

class groundwater_parameters(object):
	"""This function reads all aquifer paramters required to run the saturated component
	"""
	def __init__(self, grid_size, inputfile):
		"""Read aquifer parameters
		
		Parameters
		----------
		grid_size :	int
			size of the model domain
		inputfile :	object
			list of file manes for aquifer parameters
		
		Returns
		-------
		"""
		#print("Reading aquifer parameters")
		#print("Running Groundwater component")

		# read aquifer type
		# 1: exponential model
		# 2: constant model
		# 3: linear model
		if inputfile.fname_aquifertype != None and os.path.exists(inputfile.fname_aquifertype):
			self.gwtype = np.flip(rasterio.open(inputfile.fname_aquifertype).read(1), 0).flatten()
		else:
			print('Transmissivity model type .......not provided')
			self.gwtype = np.full(grid_size, 3, dtype=int)

		# Reading specific yield
		if inputfile.fname_SZ_Sy == None or not os.path.exists(inputfile.fname_SZ_Sy):				
			self.Sy = np.full(grid_size, 0.01, dtype=float)
			print('Specific yield...................not provided. Global default applied of 0.01')
		else:
			self.Sy = np.flip(rasterio.open(inputfile.fname_SZ_Sy).read(1), 0).flatten()
		
		# Applying scale factor kSy
		self.Sy = self.Sy*inputfile.kSy
		
		# Aquifer bottom
		if inputfile.fname_SZ_bot == None or not os.path.exists(inputfile.fname_SZ_bot): 
			self.bottom = np.zeros(grid_size, dtype=float)
			print('Aquifer bottom elevation.........not provided. Global default applied of 0.0 m')
		else:
			self.bottom = np.flip(rasterio.open(inputfile.fname_SZ_bot).read(1), 0).flatten()
			
		# Aquifer Saturated hydraulic conductivity
		if inputfile.fname_SZ_Ksat == None or not os.path.exists(inputfile.fname_SZ_Ksat):
			self.Ksat = np.ones(grid_size, dtype=float)
			print('Aquifer Ksat.....................not provided. Global default applied of 1.0 m/h')
		else:
			self.Ksat = np.flip(rasterio.open(inputfile.fname_SZ_Ksat).read(1), 0).flatten()
			
		# Applying scale factor kKsat_gw
		self.Ksat *= inputfile.kKsat
		#self.Ksat *= inputfile.kKsat_gw*inputfile.unit_sim_k
		#gw.at_node['Hydraulic_Conductivity'] *= inputfile.kKsat_gw*inputfile.unit_sim_k
		#print(gw.at_node['Hydraulic_Conductivity'])				
		# Check if flux boundary is provided m/h
		if inputfile.fname_FHB == None or not os.path.exists(inputfile.fname_FHB):
			self.FHB = np.zeros(grid_size, dtype=float)
			print('Flux boundary conditions. .......not provided')
		else:
			self.FHB = np.flip(rasterio.open(inputfile.fname_FHB).read(1), 0).flatten()
			#SZ_CHBa = read_esri_ascii(inputfile.fname_FHB,
			#	name='SZ_FHB', grid=gw)[1]
			#gw.at_node['SZ_FHB'][gw.at_node['SZ_FHB'] == -9999] = 0				
			#gw.at_node['SZ_FHB'][:] = gw.at_node['SZ_FHB'][:]*2/(np.power(rg.dx, 2))
		#gw.at_node['SZ_FHB'][gw.status_at_node[gw.status_at_node == gw.BC_NODE_IS_CLOSED]] = 0
		#gw.at_node['SZ_FHB'][:] = gw.at_node['SZ_FHB']*inputfile.kFlux
		
		# Check if constant head boundary is provided
		if inputfile.fname_CHB == None or not os.path.exists(inputfile.fname_CHB):
			self.CHB = None			
			print('Constant head boundary conditions not provided')
		else:
			self.CHB = np.flip(rasterio.open(inputfile.fname_CHB).read(1), 0).flatten()
			#read_esri_ascii(inputfile.fname_CHB,
			#	name='SZ_CHB', grid=gw)[1]
			#id_CHB = np.where(gw.at_node['SZ_CHB'] != -9999)[0]
			#gw.at_node['water_table__elevation'][id_CHB] = gw.at_node['SZ_CHB'][id_CHB]
			#gw.status_at_node[id_CHB] = gw.BC_NODE_IS_FIXED_VALUE

		
		# Read parameters for calulating  effective thickness
		# a: numerator, and b: denominator
		# Read aquifer thickness or paramter a for calculating effective thickness
		if inputfile.fname_thickness == None or not os.path.exists(inputfile.fname_thickness):
			self.thickness = np.full(grid_size, 50.0, dtype=float)
			#gw.at_node['SZ_a_aq'][:] = 50.0
			print('Aquifer effective depth..........not provided, aassumed value of 50m')
		else:
			self.thickness = np.flip(rasterio.open(inputfile.fname_thickness).read(1), 0).flatten()
			#SZ_CHBa = read_esri_ascii(inputfile.fname_a_aq,
			#	name='SZ_a_aq', grid=gw)[1]
		

		#gw.at_node['SZ_a_aq'][:] += np.array(rg.at_node['Soil_depth']*0.001)
		
		# Read aquifer parameter b for calculating effective thickness
		#if inputfile.fname_b_aq == None or not os.path.exists(inputfile.fname_b_aq):
		#	gw.add_zeros('node', 'SZ_b_aq', dtype=float)
		#	print('Not available b parameter aquifer, b=0')
		#else:
		#	SZ_CHBa = read_esri_ascii(inputfile.fname_b_aq,
		#		name='SZ_b_aq', grid=gw)[1]
					
		# Initial water table depth
		#print("reading initial water table elevation...")
		if inputfile.fname_GWini == None or not os.path.exists(inputfile.fname_GWini):
			self.head = np.flip(rasterio.open(inputfile.fname_DEM).read(1), 0).flatten()
			#h = gw.add_zeros('node', 'water_table__elevation', dtype=float)
			#gw.at_node['water_table__elevation'] = z - rg.at_node['Soil_depth']*0.001
			print('Initial water table elevation... not provided assumed equal to surface')
			#print('Initial water table elevation assumed equal to root depth elevation')
		else:
			self.head = np.flip(rasterio.open(inputfile.fname_GWini).read(1), 0).flatten()
			#h = read_esri_ascii(inputfile.fname_GWini,
			#	name='water_table__elevation', grid=gw)[1]

class interception_parameters(object):
	"""This function reads all aquifer paramters required to run the saturated component
	"""
	def __init__(self, grid_size, inputfile):
		"""Read soil layer parameters

		Attributes
		----------
		extintion_depth : numpy array
			depth at which plants can no longer take water [m]
		tap_depth : numpy array
			depth at which plants starts to strees, water taken from the saturated
			zone is limited [mm]

		
		Parameters
		----------
		grid_size:	int
			size of the model domain
		inputfile:	object
			list of file manes for soil parameters
		
		Returns
		-------
		"""
		# INTERCEPTION COMPONENT ==================================================
		#if 
		#if inputfile.fname_savi != None and os.path.exist(inputfile.fname_savi):
		#	self.av = rasterio.open(fname_in).read(1)
		#else:
		#	print('Fraction of vegetation cover..not provided as raster. Global default 1')
		#	self.av = 1.0
		
		#if inputfile.fname_kc != None and os.path.exist(inputfile.fname_kc):
		#	self.av = rasterio.open(fname_in).read(1)
		#else:
		#	print('Fraction of vegetation cover..not provided as raster. Global default 1')
		#	self.av = 1.0

		# read crop vegetation factor: default 1

		if inputfile.fname_av is not None and os.path.exists(inputfile.fname_av):
			self.av = np.flip(rasterio.open(inputfile.fname_av).read(1), 0).flatten()
			self.av[self.av < 0] = 0.0
		else:
			print('Fraction of vegetation cover.....not provided. Global default 1')
			self.av = None
		# read Coeficient of exponential function: default 0
		if inputfile.fname_laia is not None and os.path.exists(inputfile.fname_laia):
			self.lai_a = np.flip(rasterio.open(inputfile.fname_laia).read(1), 0).flatten()
		else:
			print('Vegetation exponential coef......not provided. Global default 1')
			self.lai_a = 0

		# read Power value for exponential function: default 0
		if inputfile.fname_laib is not None and os.path.exists(inputfile.fname_laib):
			self.lai_b = np.flip(rasterio.open(inputfile.fname_laib).read(1), 0).flatten()
		else:
			print('Vegetation exponential coef......not provided. Global default 1')
			self.lai_b = 0

		# read Min Soil-Adjusted Vegetation Index: default 0
		if inputfile.fname_savi_min is not None and os.path.exists(inputfile.fname_savi_min):
			self.savi_min = np.flip(rasterio.open(inputfile.fname_savi_min).read(1), 0).flatten()
		else:
			print('Fraction of vegetation cover.....not provided. Global default 1')
			self.savi_min = 0

		# Max Soil-Adjusted Vegetation Index: defgault 1
		if inputfile.fname_savi_max is not None and os.path.exists(inputfile.fname_savi_max):
			self.savi_max = np.flip(rasterio.open(inputfile.fname_savi_max).read(1), 0).flatten()
		else:
			print('Fraction of vegetation cover.....not provided. Global default 1')
			self.savi_max = 1.0
		
		#------Modification for Dyna-Veg---------------------------------------------------
		# bioma-dependent coefficient
		if inputfile.fname_fcw_canopy is not None and os.path.exists(inputfile.fname_fcw_canopy):
			self.fcw_cn = np.flip(rasterio.open(inputfile.fname_fcw_canopy).read(1), 0).flatten()
		else:
			print('Biome-dependent coefficient......not provided. Global 1 [-]')
			self.fcw_cn = np.ones(grid_size, dtype=float)
		
		# inital water content of the canopy storage
		if inputfile.fname_Sc0_canopy is not None and os.path.exists(inputfile.fname_Sc0_canopy):
			self.Sc0_cn = np.flip(rasterio.open(inputfile.fname_Sc0_canopy).read(1), 0).flatten()
		else:
			print('Initial canopy storage...........not provided. Global 0 [-]')
			self.Sc0_cn = np.zeros(grid_size, dtype=float)
		
		# inital water content of the canopy storage, riparian zone
		if inputfile.fname_Sc0_canopy is not None and os.path.exists(inputfile.fname_Sc0_canopy):
			self.Sc0_cnrp = np.flip(rasterio.open(inputfile.fname_Sc0_canopy).read(1), 0).flatten()
		else:
			print('Initial riparian canopy storage, not provided. Global 0 [-]')
			self.Sc0_cnrp = np.zeros(grid_size, dtype=float)
		
		# Tap water threshold for evaporation uptake
		# tap needs to be equal or higher than the soil depth [mm]
		if inputfile.fname_tap_depth is not None and os.path.exists(inputfile.fname_tap_depth):
			self.tap_depth = np.flip(rasterio.open(inputfile.fname_tap_depth).read(1), 0).flatten()
		else:
			print('Tap water level..................not provided. Global 0 [mm]')
			self.tap_depth = np.zeros(grid_size, dtype=float)
		
		# read soil depth, it is the same as the hillslope soil
		if inputfile.fname_SoilDepth is not None and os.path.exists(inputfile.fname_SoilDepth):
			Droot = np.flip(rasterio.open(inputfile.fname_SoilDepth).read(1), 0).flatten()
		else:
			Droot = np.full(grid_size, 1000.0, dtype=float)

		Droot = Droot*inputfile.kDroot
		
		# Final plant water uptake threshold for evaporation uptake [mm]
		if inputfile.fname_extintion_depth is not None and os.path.exists(inputfile.fname_extintion_depth):
			self.extintion_depth = np.flip(rasterio.open(inputfile.fname_extintion_depth).read(1), 0).flatten()
		else:
			print('Extinction depth.................not provided. Default is rooting depth [mm]')
			#final_depth = np.flip(rasterio.open(inputfile.fname_SoilDepth).read(1), 0).flatten()
			#self.extintion_depth = final_depth[:]
			self.extintion_depth = Droot[:]
		
		
		# change units: mm -> m
		self.extintion_depth = -(self.tap_depth - self.extintion_depth)*0.001
		
		self.extintion_depth[self.extintion_depth <= 0] = Droot[self.extintion_depth <= 0]*0.001

		pass

	def apply_factor_tap(self, kTap):
		"""Apply scale factor to tap depth
		Parameters
		----------
		kTap:	scale factor for tap depth

		Returns
		-------
		"""
		self.tap_depth = self.tap_depth * kTap

class water_body_parameters(object):
	"""This function reads all aquifer paramters required to run the saturated component
	"""
	def __init__(self, grid_size, inputfile, id_nodes=None):
		"""Read aquifer parameters
		
		Parameters
		----------
		grid_size :	int
			size of the model domain
		inputfile :	object
			list of file manes for aquifer parameters
		
		Returns
		-------
		"""
		# ----------------------------------------------------------------------------------
		# ponds
		# ----------------------------------------------------------------------------------
		self.pnds_Amax = None
		self.pnds_hmax = None
		self.pnds_Vo = None

		if inputfile.fname_pnd_Amax != None and os.path.exists(inputfile.fname_pnd_hmax):
			self.pnds_Amax = np.flip(rasterio.open(inputfile.fname_pnd_Amax).read(1), 0).flatten()
			
			if inputfile.fname_pnd_hmax is not None and os.path.exists(inputfile.fname_pnd_hmax):
				self.pnds_hmax = np.flip(rasterio.open(inputfile.fname_pnd_hmax).read(1), 0).flatten()
			else:
				print('Water body max. depth............not provided. Global value 1 [m]')
				self.pnds_hmax = np.ones(grid_size, dtype=float)

			if inputfile.fname_pnd_Vo != None and os.path.exists(inputfile.fname_pnd_Vo):
				self.pnds_Vo = np.flip(rasterio.open(inputfile.fname_pnd_Vo).read(1), 0).flatten()
			else:
				print('Initial water body volume........not provided. Global value 0 [m3]')
				self.pnds_Vo = np.zeros(grid_size, dtype=float)

			# add function to reduce the size of arrays
			if id_nodes is None:
				id_nodes = np.where(self.pnds_Amax > 0)[0]
				if len(id_nodes) > 0:
					self.pnds_Amax = self.pnds_Amax[id_nodes]
					self.pnds_hmax = self.pnds_hmax[id_nodes]
					self.pnds_Vo = self.pnds_Vo[id_nodes]
				else:
					id_nodes = None
					self.pnds_Amax = None
					self.pnds_hmax = None
					self.pnds_Vo = None

		else:
			print('Ponds are not active')

		self.id_nodes = id_nodes

		## read water bodies ids and postptocess all required variables
		#if inputfile.fname_lks_name != None and os.path.exists(inputfile.fname_lks_name):
		#	# read lake names
		#	name_lks = np.flip(rasterio.open(inputfile.fname_lks_name).read(1), 0).flatten()
		#else:
		#	print('Lake names.......................................... not provided')
		#	name_lks = None

		# ----------------------------------------------------------------------------------
		# deep lakes
		# ----------------------------------------------------------------------------------
		self.ids_lks = None
		self.size_lks = None
		self.ids_max_depth_lks = None

		# read water bodies ids and postptocess all required variables
		if inputfile.fname_bathymetry != None and os.path.exists(inputfile.fname_bathymetry):
			#print('Processing lakes parameters')
			# STEP 1: Read and identify lake
			# read lake names, preserve the order, do not flatten
			depth_lks = np.flip(rasterio.open(inputfile.fname_bathymetry).read(1), 0)#.flatten()

			# get lakes parameters
			_, ids_lks, size_lks, ids_max_depth_lks, _ = get_water_body_parameters(depth_lks)
			# transfer variables to the class
			#self.name_lks = name_lks
			self.ids_lks = ids_lks
			self.size_lks = size_lks
			self.ids_max_depth_lks = ids_max_depth_lks
			#print('Lakes parameters are active')
			#print('Lakes ids', self.ids_lks)
			#print('Lakes size', self.size_lks)
			#print('Lakes max depth ids', self.ids_max_depth_lks)

		else:
			print('Deep lakes are not active')
			#print('Initial water body volume........not provided. Global value 0 [m3]')

		# ----------------------------------------------------------------------------------
		# shallow lakes
		# ----------------------------------------------------------------------------------
		# read water bodies ids and postptocess all required variables
		self.ids_slks = None
		self.name_slks = None
		self.depth_slks = None
		self.area_slks = None

		# read water bodies ids and postptocess all required variables
		if inputfile.fname_slks_depth != None and os.path.exists(inputfile.fname_slks_depth):

			if inputfile.fname_slks_area != None and os.path.exists(inputfile.fname_slks_area):
				area_slks = np.flip(rasterio.open(inputfile.fname_slks_area).read(1), 0).flatten()
				self.area_slks = area_slks[self.ids_slks]
			else:
				print('Shallow lake area................not provided. Global value 0 [m2]')
				pass
				#self.area_slks = np.ones(len(self.ids_slks), dtype=float)


			#print('Processing lakes parameters')
			# STEP 1: Read and identify lake
			# read lake names, preserve the order, do not flatten
			depth_slks = np.flip(rasterio.open(inputfile.fname_slks_depth).read(1), 0)#.flatten()

			# get lakes parameters
			name_slks, ids_slks, depth_slks = get_water_body_parameters(depth_slks)

			# transfer variables to the class
			self.ids_slks = ids_slks
			self.name_slks = name_slks
			self.depth_slks = depth_slks

		else:
			print('Shallow lakes are not active')
			#print('Initial water body volume........not provided. Global value 0 [m3]')

class zone_parameters(object):
	"""reading zone/mask parameters for calibration or modeling outputs
	"""
	def __init__(self, path_mask):
		"""Read soil layer parameters
		
		Parameters
		----------
		path_mask:	string
					path to the raster file with zones/mask for calibration
					
		"""		
		# Reading Soil saturated hydraulic conductivity
		if path_mask == None or not os.path.exists(path_mask):
			self.zone_mask = None
			print('Submask/zones....................not provided')
		else:
			self.zone_mask = np.flip(rasterio.open(path_mask).read(1), 0).astype(int).flatten()

	def get_scale_factor_zones(self, factor):
		"""get scale factor for all zones
		Parameters
		------
		factor:	numpy array
			scale factor for each zone, it should be the same size as the number of zones
		
		Returns
		-------
		parameter:	numpy array
			calibrated model parameter
		"""
		# initial parameter
		parameter = np.ones_like(self.zone_mask, dtype=float)
		if self.zone_mask is not None:
			num_zones = int(self.zone_mask.max())
			for izone in range(1, num_zones + 1):
				id_zone = np.where(self.zone_mask == izone)[0]
				parameter[id_zone] = parameter[id_zone]*factor[izone - 1]
			return parameter
		else:
			return None
	
	def extract_zone_info(self, core_nodes=None):
		"""get zone info such as indices and size. If core nodes are provided,
		only core nodes are considered for getting zone info

		Parameters
		----------
		core_nodes:	numpy array
			array with the core nodes ids

		Returns
		-------
		ids_zones:	list
			list of numpy arrays with the ids of each zone
		size_zones:	list
			list with the size of each zone
		"""
		if self.zone_mask is None:
			return None, None
		if core_nodes is not None:
			# Make all other (non-core) nodes equal to 0
			all_indices = np.arange(self.zone_mask.size)
			non_core = np.setdiff1d(all_indices, core_nodes)
			self.zone_mask[non_core] = 0
		
		# get ids and size of zones
		ids_zone, size_zone = get_zone_indices_and_sizes(self.zone_mask)
		return ids_zone, size_zone
	
	def get_zone_info_from_core_nodes(self, core_nodes):
		"""get zone info from core nodes
		Parameters
		----------
		core_nodes:	numpy array
			array with the core nodes ids
		
		Returns
		-------
		ids_zones:	list
			list of numpy arrays with the ids of each zone
		size_zones:	list
			list with the size of each zone
		"""
		if self.zone_mask is None:
			return None, None

		if core_nodes is not None:
			# Make all other (non-core) nodes equal to 0
			all_indices = np.arange(self.zone_mask.size)
			non_core = np.setdiff1d(all_indices, core_nodes)
			self.zone_mask[non_core] = 0

		# get mask for core nodes
		mask_core = self.zone_mask[core_nodes]

		# get ids and size of zones
		ids_zone, size_zone = get_zone_indices_and_sizes(mask_core)

		return ids_zone, size_zone

def get_water_body_parameters(depth, area=None):
    """This function calculates all water body parameters required to run
    the water body component
    
    Parameters
    ----------
    depth :	numpy array
        bathymetry of the water body [m]
    area :	numpy array
        surface area of the water body [m2]
    
    Returns
    -------
    tuple of lists/arrays
        name_lks : array
            labels of lake cells (for returned ids)
        ids_lks : list
            flat indices of all lake cells (flattened, grouped by lake label)
        size_lks : list
            number of cells in each lake
        ids_max_depth_lks : list
            flat indices of the cell with maximum depth in each lake
        depths : array
            depth values corresponding to ids_lks
    """
    # mask lakes from depth
    name_lks = (depth > 0).astype(int)

    # label lakes (connected components)
    labeled, num_features = label(name_lks)

    # build groups of flat indices per labeled lake (1..num_features)
    flat = labeled.flatten()
    ids_group_by_label = []
    for lab in range(1, num_features + 1):
        ids = list(np.where(flat == lab)[0])
        ids_group_by_label.append(ids)

    # flatten groups to single list of ids (grouped by label)
    ids_lks = [idx for grp in ids_group_by_label for idx in grp]

    # sizes per lake
    size_lks = [len(grp) for grp in ids_group_by_label]

    # find index of maximum depth within each group (global flat index)
    depth_flat = depth.flatten()
    ids_max_depth_lks = []
    for grp in ids_group_by_label:
        if len(grp) == 0:
            continue
        grp_depths = depth_flat[grp]
        imax = int(np.argmax(grp_depths))
        ids_max_depth_lks.append(grp[imax])

    # reduce name array to only the returned ids (labels for those ids)
    name_lks_out = flat[ids_lks]

    # reduce depth array to those ids
    depths_out = depth_flat[ids_lks]

    return name_lks_out, ids_lks, size_lks, ids_max_depth_lks, depths_out


def get_water_body_parametersold(depth, area=None):
	"""This function calculates all water body parameters required to run the water body component
	Parameters
	----------
	depth :	numpy array
		bathymetry of the water body [m]
	area :	numpy array
		surface area of the water body [m2]
	
	Returns
	-------
	tuple of three lists
		ids_lks : list
			flat indices of all lake cells
		size_lks : list
			number of cells in each lake
		ids_max_depth_lks : list
			flat indices of the cell with maximum depth in each lake
	"""
	# mask lakes from depth
	name_lks = depth > 0
	name_lks = name_lks.astype(int)

	# label lakes
	name_lks, num_features = label(name_lks)

	# get lakes parameters
	ids_lks, size_lks = get_zone_indices_and_sizes(name_lks)

	# flatten the name array to match the grid
	name_lks = name_lks.flatten()
#	#print('name_lks', name_lks.shape, 'num_features', num_features)
#	# POST-PROCESSING LAKES VARIABLES		
#	# Step 2: For each label, collect flat indices (len=number of lakes)
#	ids_group_by_label = []
#	for label_num in range(1, num_features + 1):
#		flat_indices = list(np.where(name_lks == label_num)[0])
#		ids_group_by_label.append(flat_indices)
#
#	# Step 3: Get length of each lake (number of cells)
#	size_lks = list(map(len, ids_group_by_label))
#
#	# Step 4: Get index of all lakes
#	ids_lks = list(np.where(name_lks > 0)[0])

	# Step 5: Get index of the maximum depth for each lake
	ids_max_depth_lks = numpy_argmin_reduceat(-depth.flatten()[ids_lks],
							np.append([0], np.cumsum(size_lks)[:-1])
							)
	# map the indices to the original ids_lks
	ids_max_depth_lks = [ids_lks[i] for i in ids_max_depth_lks]

	# reduce size of lakes names array
	name_lks = name_lks[ids_lks]

	# reduce depth array
	depth = depth.flatten()[ids_lks]
	 	
	return name_lks, ids_lks, size_lks, ids_max_depth_lks, depth

def get_zone_indices_and_sizes(mask):
	"""This function get ids and length zones from a mask
	Parameters
	----------
	mask :	numpy array
		bathymetry of the water body [m]
	
	Returns
	-------
	tuple of three lists
		ids_lks : list
			flat indices of all lake cells
		size_lks : list
			number of cells in each lake
		ids_max_depth_lks : list
			flat indices of the cell with maximum depth in each lake
	"""
	# get masks
	name_zones = mask.astype(int)

	# flatten the name array to match the grid
	name_zones = name_zones.flatten()

	# number of features
	num_features = name_zones.max()

	# Step 2: For each label, collect flat indices (len=number of lakes)
	ids_group_by_label = []
	for label_num in range(1, num_features + 1):
		flat_indices = list(np.where(name_zones == label_num)[0])
		ids_group_by_label.append(flat_indices)

	# Step 3: Get length of each lake (number of cells)
	size_zones = list(map(len, ids_group_by_label))

	# Step 4: Get index of all lakes
	ids_zones = list(np.where(name_zones > 0)[0])
	 	
	return ids_zones, size_zones

def read_point_coordinates(filename, xlabel="East", ylabel="North"):
    """
    Read x and y coordinates from a CSV file efficiently.

    Parameters
    ----------
    filename : str
        Path to the CSV file with coordinates.
    xlabel : str, optional
        Name of the column containing x coordinates. Default is "East".
    ylabel : str, optional
        Name of the column containing y coordinates. Default is "North".

    Returns
    -------
    tuple of np.ndarray
        xpoint : np.ndarray
            Array of x coordinates.
        ypoint : np.ndarray
            Array of y coordinates.
    """
    if not filename or not os.path.exists(filename):
        raise FileNotFoundError(f"File does not exist: {filename}")

    # Read only required columns directly as float NumPy arrays
    datapoints = pd.read_csv(filename, usecols=[xlabel, ylabel])

    xpoint = datapoints[xlabel].to_numpy(dtype=float)
    ypoint = datapoints[ylabel].to_numpy(dtype=float)

    return xpoint, ypoint

def extract_idnode_from_coords(grid, xpoint, ypoint):
	""" extract nodes from coordinates
	this component uses the landlab funtion "find_nearest_node
	Parameters
	----------
	grid:		landlabgrid
	xpoint:		numpy array with x coordinates
	ypoint:		numpy array with y coordinates

	Returns
	-------
	tuple of numby array with id nodes in the nodes array and
	idpoint:		nodes in the grid
	idpoint_active:	index of ipoint in the active node list
	"""
#	try:
#		assert len(xpoint) > 0
#	except:
#		raise Exception('Sample points must be inside the model domain'
#		   		'Please check the file of sample points')

	idpoint = []
	idpoint_active = []
	for ixpoint, iypoint in zip(xpoint, ypoint):
		# find the nearest point in the grid
		point = grid.find_nearest_node(
			[ixpoint, iypoint])
		if grid.status_at_node[point] == 0:
			# store id only if it is an active node
			idpoint.append(point)
			# find the index ot the point in the active nodes
			# array and store in a list of id active nodes
			point_active = np.where(grid.core_nodes == point)[0]
			idpoint_active.append(point_active[0])

	idpoint = np.array(idpoint, dtype=int)
	idpoint_active =  np.array(idpoint_active, dtype=int)

	try:
		assert len(xpoint) > 0
	except:
		raise Exception('Sample points must be inside the model domain'
		   		'Please check the file of sample points')

	return idpoint, idpoint_active
	
def extract_id_from_raster(grid, filename):
	""" extract nodes from raster file

	Parameters
	----------
	grid: 		landlabgrid
	filename:	filename raster
	
	Returns
	-------
	numby array with id nodes
	"""
	if filename != None and os.path.exists(filename):
		location_map = rasterio.open(filename.fname_laibrip).read(1).flatten()
	else:
		print(filename)
		raise Exception("File do not exis")
	
	id_location = np.where(location_map > 0)[0]
	
	aux = [id_location, location_map[id_location]]
	
	#sort data
	aux_sort = aux.sort(axis=0)
	
	return id_location[0]

def create_coordinate_array(xllcorner, yllcorner, grid_nrows, grid_ncols, cellsize):
	"""This function create two arrays representing:
	the x-axis (lon: longitud) and y-axis (lat: latitude)
	WARNING: this axis have to be flipped to match landlab grid, so be carful when
	using in other components

	Parameters
	----------
	xllcorner:	lower left x-coordinate (float)
	yllcorner:	lower left y-coordinate (float)
	grid_nrows:	number of rows of the model domain (int)
	grid_ncols:	number of columns of the model domain (int)
	cellsize:	model grid size (float)
	
	Returns
	-------
	tuple: lon, lat:	numpy arrays
	"""
	lat_end = xllcorner + cellsize*grid_nrows
	lat = np.arange(xllcorner, lat_end, cellsize)
	lon_end = yllcorner + cellsize*grid_ncols
	lon = np.arange(yllcorner, lon_end, cellsize)
	return lon, lat

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

# Getting the min Index 
def numpy_argmax_reduceat(a, index):
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

def read_parameter_set_file(filename):
	"""This function reads a parameter set file for model calibration
	Parameters
	----------
	filename :	str
		path to the parameter set file
	
	Returns
	-------
	param_set :	numpy array
		array with the parameter set values
	"""
	# check if file exists
	param_set = None
	if filename != None and os.path.exists(filename):
		param_set = np.loadtxt(filename, delimiter=',')
	return param_set
		