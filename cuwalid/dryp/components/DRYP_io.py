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
# Global parameters
ABC_RIVER = 0.2 # River abstraction parameter
		
class surface_parameters(object):
	"""Setting model input varables and environmental states
	"""
	def __init__(self, inputfile):
		"""Create variables to store model states and input data sets.
		Read all input datasst and variables for all components
		"""
		# build the data classes
		# ================ Reading surface water model inputs ==============
		
		print('******************* Reading Input Files ********************')
		
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
			self.mask = mask.flatten()
			
			print('Basin boundary................ not provided')
		else:
			self.mask = np.flip(rasterio.open(inputfile.fname_Mask).read(1), 0).flatten()
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
			print('River network................. not provided as raster')
			print('All cells are considered rivers with length of grid size')
		
		self.river_cells = np.zeros(grid_size, int)
		self.river_cells[self.riv_length > 0] = 1
		self.river_cells[self.mask <= 0] = 0
		
		# Reading the raster file of river width		
		if inputfile.fname_RiverWidth == None or not os.path.exists(inputfile.fname_RiverWidth):
			self.riv_width = np.full(grid_size, 10.0, dtype=float)
			print('River width................... not provided as raster. Global default applied of W = 10 m')
		else:
			self.riv_width = np.flip(rasterio.open(inputfile.fname_RiverWidth).read(1), 0).flatten()
			
		# Reading the raster file of river elevation		
		if inputfile.fname_RiverElev == None or not os.path.exists(inputfile.fname_RiverElev):
			self.riv_elevation = self.surface[:]
			print('River bottom.................. not provided as raster')
			print('River bottom elevation: surface elevation')
		else:
			self.riv_elevation = np.flip(rasterio.open(inputfile.fname_RiverElev).read(1), 0).flatten()
			
		# Reading a raster file of flow direction in LandLab format (receiving node ID)
		if inputfile.fname_FlowDir != None and os.path.exists(inputfile.fname_FlowDir):
			self.FlowDir = np.flip(rasterio.open(inputfile.fname_FlowDir).read(1), 0).flatten()
		else:
			self.FlowDir = None
			print('Flow direction................ not provided as raster')
			#self.act_update_flow_director = True

		# LAKES COMPONENT ========================================================================
		# read maximum surface water elevation of lakes
		if inputfile.fname_bathymetry != None and os.path.exists(inputfile.fname_bathymetry):
			z_lakes = np.flip(rasterio.open(inputfile.fname_bathymetry).read(1), 0).flatten()
			z_lakes[z_lakes<0] = 0
			self.bathymetry = self.surface - z_lakes
		else:
			print('Maximum water elevation lakes..not provided as raster. Global default z')
			self.bathymetry = self.surface[:]
	
		# CHANNEL ===============================================================================
		# Channel hydraulic parameters
		# Assuming a flow velocity of 1 m/s => 3600 m/h
		if inputfile.fname_kTchannel == None or not os.path.exists(inputfile.fname_kTchannel):			
			self.decay = np.full(grid_size, inputfile.kTch/self.grid_cellsize, dtype=float)
			print('Channel decay parameter.................. not provided')
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
			print('Channel Ksat.................. not provided')
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
		#rg.at_node['cth_area_k']
		
		#self.area_cells_hills = rg.dx*rg.dy*rg.at_node['cth_area_k']
		
		area_bank_cells = self.river_cells*self.riv_length*self.river_banks#(
			#self.riv_width+2*self.river_banks
			#)
		
		self.area_bank_cells = np.where(area_bank_cells > self.area_cells,
				  self.area_cells, area_bank_cells)

		# read initial conditions of channel flow: in m3/h
		if inputfile.fname_Qo == None or not os.path.exists(inputfile.fname_Qo):			
			self.Qo = np.zeros(grid_size, dtype=float)
			print('Initial channel storage.................. not provided, assumed 0.0 m3')
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
		
		pass
	# Find coordinates of points in model components
	def points_output(self, inputfile):
		""" This function reads data points to report model results
		Values at each point will be extracted for all components depending
		on the specified points:
		OF:	surfave component
		UZ:	soil and riparian component
		GW: saturated component
		Parameters
		-----
		inputfile:	python obkject containing a list of points

		Returns
		------
		list of nodes where values will be extracted
		"""				
		# Reading output points
		gaugeid = extract_id_from_coords(self.grid,
			inputfile)
		
		return gaugeid


class grid_environment(object):
	"""grid elements and state variables required for running the model"""
	def __init__(self,):
		"""this function create a grid landlab object, this function can be
		used directly from landlab rastergrid function
		"""
		pass

	def create_grid(self, ncol, nrow, xllcorner, yllcorner, cellsize, domain):
		"""this function create a grid landlab object, this function can be
		used directly from landlab rastergrid function
		Parameters
		------
		ncol:		number of column of the grid, grid width (integer)
		nrow:		number of column of the grid, grid width (integer)
		xllcorner:	lower left x coordinate
		yllcorner:	lower left x coordinate
		cellsize:	grid spacing, size of the model cells
		Returns
		------
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

class model_environment_status(object):
	"""grid elements and state variables required for running the model"""
	def __init__(self, grid_size):
		"""ininitalize model variables which are common for all components"""
		
		pass

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
			print('Hydraulic conductivity........ not provided as raster. Global default applied of 1.0 mm/h')
		else:
			self.Ksat = np.flip(rasterio.open(inputfile.fname_Ksat).read(1), 0).flatten()
					
		# Change units and applying scale factor kKs
		self.Ksat = (self.Ksat*inputfile.kKsat)
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
			print('Wilting point................. not provided as raster. Global default applied of 0.05')
		else:
			self.theta_wp = np.flip(rasterio.open(inputfile.fname_theta_wp).read(1), 0).flatten()
				
		# Read Saturated water content (porosity)
		if inputfile.fname_n == None or not os.path.exists(inputfile.fname_n):
			self.theta_sat = np.full(grid_size, 0.40, dtype=float)
			print('Porosity...................... not provided as raster. Global default applied of 0.4')
		else:
			self.theta_sat = np.flip(rasterio.open(inputfile.fname_n).read(1), 0).flatten()
			
		# Reading available water content: raster file		
		if inputfile.fname_theta_AWC == None or not os.path.exists(inputfile.fname_theta_AWC):
			theta_AWC = np.full(grid_size, 0.10, dtype=float)
			print('Available Water Content....... not provided as raster. Global default applied of 0.10')
		else:
			theta_AWC = np.flip(rasterio.open(inputfile.fname_theta_AWC).read(1), 0).flatten()

		self.theta_fc = theta_AWC + self.theta_wp

		# Exponent for soil moisture - matrix potential relation
		# Rawls (1982), and Clapp and Hornberger (1978)
		if inputfile.fname_b_SOIL == None or not os.path.exists(inputfile.fname_b_SOIL):
			self.lambdas = np.full(grid_size, 10.05, dtype=float)
			print('Soil particle distribution par. not provided as raster. Global default applied of 10.5')
		else:
			self.lambdas = np.flip(rasterio.open(inputfile.fname_b_SOIL).read(1), 0).flatten()
			
		# air-entry/saturated capillary potential, [mm]
		if inputfile.fname_PSI == None or not os.path.exists(inputfile.fname_PSI):
			psi_a = np.full(grid_size, 153.0)
			print('Suction head.................. not provided as raster. Global default applied of 153 mm')
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
			print('Rooting depth................. not provided as raster. Global default applied of 1000mm')
		else:
			self.Droot = np.flip(rasterio.open(inputfile.fname_SoilDepth).read(1), 0).flatten()
			self.Droot = np.array(self.Droot, dtype=float)
		# Applying scale factor kDroot
		self.Droot *= inputfile.kDroot
		#self.Droot = np.array(self.depth_uz)

		# Reading initial available water content: raster file		
		if inputfile.fname_theta == None or not os.path.exists(inputfile.fname_theta):
			self.theta = self.theta_wp+0.01*theta_AWC
			print('Not available initail water content....... dry condition assumed (wiltinf point)')
		else:
			self.theta = np.flip(rasterio.open(inputfile.fname_theta).read(1), 0).flatten()

		self.theta_fc = theta_AWC + self.theta_wp

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
		print("Reading aquifer parameters")
		#print("Running Groundwater component")

		# read aquifer type
		# 1: exponential model
		# 2: constant model
		# 3: linear model
		if inputfile.fname_aquifertype != None and os.path.exists(inputfile.fname_aquifertype):
			self.gwtype = np.flip(rasterio.open(inputfile.fname_aquifertype).read(1), 0).flatten()
		else:
			print('No transmissivity model type provided')
			self.gwtype = np.full(grid_size, 3, dtype=int)

		# Reading specific yield
		if inputfile.fname_SZ_Sy == None or not os.path.exists(inputfile.fname_SZ_Sy):				
			self.Sy = np.full(grid_size, 0.01, dtype=float)
			#gw.add_zeros('node', 'SZ_Sy', dtype=float) # Water table elevation
			#gw.at_node['SZ_Sy'] += 0.01
			print('Specific yield................ not provided as raster. Global default applied of 0.01')
		else:
			self.Sy = np.flip(rasterio.open(inputfile.fname_SZ_Sy).read(1), 0).flatten()
			#read_esri_ascii(inputfile.fname_SZ_Sy,
			#	name='SZ_Sy', grid=gw)[1]
		
		# Applying scale factor kSy
		self.Sy = self.Sy*inputfile.kSy
		
		# Aquifer bottom
		if inputfile.fname_SZ_bot == None or not os.path.exists(inputfile.fname_SZ_bot): 
			self.bottom = np.zeros(grid_size, dtype=float)
			print('Aquifer bottom elevation...... not provided as raster. Global default applied of 0.0 m')
		else:
			self.bottom = np.flip(rasterio.open(inputfile.fname_SZ_bot).read(1), 0).flatten()
			
		# Aquifer Saturated hydraulic conductivity
		if inputfile.fname_SZ_Ksat == None or not os.path.exists(inputfile.fname_SZ_Ksat):
			self.Ksat = np.ones(grid_size, dtype=float)
			print('Aquifer Ksat.................. not provided as raster. Global default applied of 1.0 m/h')
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
			print('Flux boundary conditions. not provided as raster')
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
			print('Constant head boundary conditions not provided as raster')
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
			print('Not available aquifer effective depth... assumed value of 50m')
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
		print("reading initial water table elevation...")
		if inputfile.fname_GWini == None or not os.path.exists(inputfile.fname_GWini):
			self.head = np.flip(rasterio.open(inputfile.fname_DEM).read(1), 0).flatten()
			#h = gw.add_zeros('node', 'water_table__elevation', dtype=float)
			#gw.at_node['water_table__elevation'] = z - rg.at_node['Soil_depth']*0.001
			print('Initial water table elevation not provided assumed equal to surface')
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

		if inputfile.fname_av != None and os.path.exists(inputfile.fname_av):
			self.av = np.flip(rasterio.open(inputfile.fname_av).read(1), 0).flatten()
		else:
			print('Fraction of vegetation cover..not provided as raster. Global default 1')
			self.av = None
		# read Coeficient of exponential function: default 0
		if inputfile.fname_laia != None and os.path.exists(inputfile.fname_laia):
			self.lai_a = np.flip(rasterio.open(inputfile.fname_laia).read(1), 0).flatten()
		else:
			print('Vegetation exponential coeficient..not provided as raster. Global default 1')
			self.lai_a = 0

		# read Power value for exponential function: default 0
		if inputfile.fname_laib != None and os.path.exists(inputfile.fname_laib):
			self.lai_b = np.flip(rasterio.open(inputfile.fname_laib).read(1), 0).flatten()
		else:
			print('Vegetation exponential coeficient..not provided as raster. Global default 1')
			self.lai_b = 0

		# read Min Soil-Adjusted Vegetation Index: default 0
		if inputfile.fname_savi_min != None and os.path.exists(inputfile.fname_savi_min):
			self.savi_min = np.flip(rasterio.open(inputfile.fname_savi_min).read(1), 0).flatten()
		else:
			print('Fraction of vegetation cover..not provided as raster. Global default 1')
			self.savi_min = 0

		# Max Soil-Adjusted Vegetation Index: defgault 1
		if inputfile.fname_savi_max != None and os.path.exists(inputfile.fname_savi_max):
			self.savi_max = np.flip(rasterio.open(inputfile.fname_savi_max).read(1), 0).flatten()
		else:
			print('Fraction of vegetation cover..not provided as raster. Global default 1')
			self.savi_max = 1.0
		
		#------Modification for Dyna-Veg---------------------------------------------------
		# bioma-dependent coefficient
		if inputfile.fname_fcw_canopy != None and os.path.exists(inputfile.fname_fcw_canopy):
			self.fcw_cn = np.flip(rasterio.open(inputfile.fname_fcw_canopy).read(1), 0).flatten()
		else:
			print('Biome-dependent coefficient, not provided. Global 1 []')
			self.fcw_cn = np.ones(grid_size, dtype=float)
		
		# inital water content of the canopy storage
		if inputfile.fname_Sc0_canopy != None and os.path.exists(inputfile.fname_Sc0_canopy):
			self.Sc0_cn = np.flip(rasterio.open(inputfile.fname_Sc0_canopy).read(1), 0).flatten()
		else:
			print('Initial canopy storage, not provided. Global 0 []')
			self.Sc0_cn = np.zeros(grid_size, dtype=float)
		
		# inital water content of the canopy storage, riparian zone
		if inputfile.fname_Sc0_canopy != None and os.path.exists(inputfile.fname_Sc0_canopy):
			self.Sc0_cnrp = np.flip(rasterio.open(inputfile.fname_Sc0_canopy).read(1), 0).flatten()
		else:
			print('Initial riparian canopy storage, not provided. Global 0 []')
			self.Sc0_cnrp = np.zeros(grid_size, dtype=float)
		
		# Tap water threshold for evaporation uptake
		# tap needs to be equal or higher than the soil depth [mm]
		if inputfile.fname_tap_depth != None and os.path.exists(inputfile.fname_tap_depth):
			self.tap_depth = np.flip(rasterio.open(inputfile.fname_tap_depth).read(1), 0).flatten()
		else:
			print('Tap water level, not provided. Global 0 [mm]')
			self.tap_depth = np.zeros(grid_size, dtype=float)
		
		#self.ztap = z - self.tap_depth*0.001
		
		# read soil depth, it is the same as the hillslope soil
		if inputfile.fname_SoilDepth != None and os.path.exists(inputfile.fname_SoilDepth):
			Droot = np.flip(rasterio.open(inputfile.fname_SoilDepth).read(1), 0).flatten()
		else:
			Droot = np.full(grid_size, 1000.0, dtype=float)

		Droot = Droot*inputfile.kDroot
		
		# Final plant water uptake threshold for evaporation uptake [mm]
		if inputfile.fname_extintion_depth != None and os.path.exists(inputfile.fname_extintion_depth):
			self.extintion_depth = np.flip(rasterio.open(inputfile.fname_extintion_depth).read(1), 0).flatten()
		else:
			print('Final root water uptake level, not provided. Default is rooting depth [mm]')
			#final_depth = np.flip(rasterio.open(inputfile.fname_SoilDepth).read(1), 0).flatten()
			#self.extintion_depth = final_depth[:]
			self.extintion_depth = Droot[:]
		
		
		# change units: mm -> m
		self.extintion_depth = -(self.tap_depth - self.extintion_depth)*0.001
		
		self.extintion_depth[self.extintion_depth <= 0] = Droot[self.extintion_depth <= 0]*0.001

		pass

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
		#print("Reading water body parameters")

		if inputfile.fname_pnd_Amax != None and os.path.exists(inputfile.fname_pnd_hmax):
			self.pnds_Amax = np.flip(rasterio.open(inputfile.fname_pnd_Amax).read(1), 0).flatten()
			self.pnds_hmax = np.flip(rasterio.open(inputfile.fname_pnd_hmax).read(1), 0).flatten()
			if inputfile.fname_pnd_Vo != None and os.path.exists(inputfile.fname_pnd_Vo):
				self.pnds_Vo = np.flip(rasterio.open(inputfile.fname_pnd_Vo).read(1), 0).flatten()
				
			else:
				print('initial watr body volume not provided. Global value 0 [m3]')
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
			print('Water body parameters not provided')
			self.pnds_Amax = None
			self.pnds_hmax = None
			self.pnds_Vo = None

		self.id_nodes = id_nodes

def extract_id_from_coords(grid, filename):
	""" extract nodes from a csv file
	this component uses the landlab funtion "find_nearest_node

	Parameters
	----------
	grid:		landlabgrid
	filename:	csv file with coordinates
	
	Returns
	-------
	tuple of numby array with id nodes in the nodes array and 
	in the active nodes list
	idpoint:		nodes in the grid
	idpoint_active:	index of ipoint in the active node list
	"""
	
	# check if file is available
	if filename == None or not os.path.exists(filename):
		print(filename)
		raise Exception("File do not exis")
	
	# read coordinates from csv file
	datapoints = pd.read_csv(filename)
	
	# creating variables for storing outputs
	npoints = len(datapoints['North'])
	
	idpoint = []
	idpoint_active = []
	#print(grid.shape)
	for ndis in range(npoints):
		# find the nearest point in the grid
		point = grid.find_nearest_node(
			[datapoints['East'][ndis],
			datapoints['North'][ndis]])
		if grid.status_at_node[point] == 0:
			# store id only if it is an active node
			idpoint.append(point)
			# find the index ot the point in the active nodes
			# array and store in a list of id active nodes
			point_active = np.where(grid.core_nodes == point)[0]
			idpoint_active.append(point_active[0])

	try:
		assert len(idpoint) > 0
	except:
		raise Exception('Sample points must be inside the model domain'
		   		'Please check the file of sample points')
	
	return idpoint, idpoint_active
	
def extract_id_from_raster(grid, filename):
	""" find id location of boundary conditions from raster
	this component uses the landlab funtion "find_nearest_node

	Parameters
	----------
	grid: 		landlabgrid
	filename:	filename raster
	
	Returns
	-------
	numby array with id nodes
	"""
	# read Power value for exponential function: default 0
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
		