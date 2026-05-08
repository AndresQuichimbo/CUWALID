import os
import numpy as np
import pandas as pd
from calendar import monthrange
import datetime
from datetime import timedelta
from netCDF4 import Dataset, num2date, date2num
from landlab.io import write_esri_ascii
from itertools import compress
import operator
from cuwalid.dryp.components.DRYP_global_parameters import *
import rasterio
    

# global settings
agg_balance_global = 'D'
agg_balance_local = 'D'
point_aggre = 'D'

# save varoiables
save_all = True

# print variables
print_precipitation = False
print_infiltration = False
print_excess = False
print_watertable = True
print_actualetp = True
print_chstorage = False
print_percolation = True
print_soilmoisture = True
print_translosses = True
print_discharge = True
print_cropKc = True
print_Eca = True
print_Pth = True

# print maps
print_maps_end = True
print_watertable_map = True
print_soilmoisture_map = True

# NETCDF4 model outputs
apply_scale_offset = True

class GlobalGridVar:
	"""Setting variables and arrays for saving model grid variables
	Returns
	"""
	def __init__(self, ini_date, dt, save_results=True, store_var=None, store_max=False, nstep_day=None):
		"""Create a set of 2D arrays to store spatio-temporal datasets.

		Parameters:
		----------
		ini_date: datetime object
			starting date of the simulation
		dt: string
			delta time step, e.g. 1D, 1H, 1M, 1Y
		save_results: bool
			flag to save results in a file
			True - save results in a file
			False - do not save results in a file
		store_max: bool
			flag to store maximum values over a specified period
		store_var:	dictionary
			with key containing model name variables and boolean as values


		Returns:
		-------
		None
		"""
		# set activate store
		self.save_results = save_results

		# set variables
		self.var_acummulation = None
		self.var_maximum = None
		self.cumm_variable = []

		# Calculate time delta
		self.delta = str2timedelta(ini_date, dt)
		
		# Calculate next time step			
		self.idate = addtime(ini_date, self.delta)
		self.pdate = ini_date
		self.time_grid = []
		self.nsteps_vector = []
		self.nsteps = 0
		self.dt_time = dt
		self.update_keys = True
		self.drop_var = None
		if store_var is not None:
			# select variables that are not stored
			self.drop_var = drop_false_keys(store_var)
			if len(self.drop_var) == 0:
				self.drop_var = None
		#self.store_var = None
		#self.update_keys = True
		
		# set counter for number of step for max value
		self.nsteps_max = 1

		# activate option to save maximum values over a specified period
		# this function will only be activated if data is stored in time
		# steps greater than one day

		# maximum number of time steps per day
		self.daily_steps = nstep_day
		self.store_max = store_max

		# activate store maximum value options
		if store_max is True:
			if self.delta[1] > 0:
				self.store_max = True
			if self.delta[2] > 1:
				self.store_max = True
		else:
			self.store_max = False
		
		if self.daily_steps is None:
			self.store_max = False
		elif self.daily_steps > 1:
			if self.store_max is not True:
				self.store_max = False
		else:
			self.store_max = False

		self.start_storing = False

		self.store_var_names = None
		#print(self.store_max)
		#if store_max is True:
		#	self.store_max = True
		#else:
		#	self.store_max = False
		#print(self.store_max)
		pass

	def store_variables(self, date_sim_dt, t_date, variables):
		"""	This function store variables in a 2D array, it will
		store the variables in a 2D array, if the time step is greater than
		one day, it will store the maximum values for the entire day.
		Otherwise, it will store the values for the entire day. It will
		stack variables in an 1d-array so store

		Parameters
		----------
		date_sim_dt :numpy array
			1D array of dates at results time steps
		t_date :int
			index of the date to store
		variables :	dict
			dictionary containig variables to store

		Returns
		-------
		numpy array
		"""
		if self.save_results is True:
			# remove variables that are not being stored
			if self.drop_var is not None:
				variables = remove_variables_from_dict(
					variables, self.drop_var)
			
			# get keys from dictionary, if not already stored
			if self.update_keys is True:
				self.store_var_names = list(variables.keys())
				self.store_var_length = get_list_of_length_field_dict(
					variables)
				self.update_keys = False
			
			# change dictionary to list
			variables = list(variables.values())			

			## check if the last date is read
			date = date_sim_dt[t_date]
			
			# accumulate variables/create array of variables
			variables = np.concatenate(variables)
			#print(date, self.idate, t_date)
			if date < self.idate:
				#print("Date: ", date, " - ", self.idate)
				# accumulate variables
				if self.var_acummulation is None:
					# create variables
					self.var_acummulation = np.array(variables)
				else:
					# accumulate
					self.var_acummulation += variables
				self.nsteps += 1
				#print(self.daily_steps, self.nsteps, self.nsteps_max)
				#print("Store: ", self.var_acummulation)
				# Store maximum values at daily time steps
				# accumulate values for the entire day
				if self.store_max is True:
					if self.nsteps_max >= self.daily_steps:
						# if variable storing values does not exist
						# create a new variable
						if self.var_maximum is None:
							# create variables
							self.var_maximum = np.array(variables)
							#self.var_maximum = np.array(self.var_acummulation)

						self.var_maximum = np.maximum(
								self.var_acummulation,
								self.var_maximum)
						
						self.var_acummulation = None

						self.nsteps_max = 0

					self.nsteps_max += 1
					#print("Max: ", self.nsteps_max, " - ", self.var_maximum)
				
			else:
				#self.nsteps += 1
				#print('max', self.daily_steps)
				# Store variables at the specified time step
				if (self.var_acummulation is None):
					# create variables
					self.var_acummulation = np.array(variables)
				else:
					# accumulate
					if self.start_storing is True:
						if date <= self.idate:
							self.var_acummulation += variables
					self.start_storing = True	
				#print("Store: ", self.var_acummulation)
				#print("Store: ", variables)

				# Store maximum values at daily time steps
				# accumulate values for the entire day
				if self.store_max is True:
					# if variable storing does not exist
					# create a new variable
					if self.var_maximum is None:
						# create variables
						self.var_maximum = np.array(variables)
						#self.var_maximum = np.array(self.var_acummulation)
					# get maximum value
					self.var_maximum = np.maximum(
							self.var_acummulation,
							self.var_maximum)

					# restart daily accumulation counter
					self.nsteps_max = 1
				#print(self.daily_steps, self.nsteps, self.nsteps_max)
				#print('Accum2: ', self.var_acummulation)
				# store variables
				self.nsteps_vector.append(self.nsteps)
				if self.store_max is True:
					self.cumm_variable.append(self.var_maximum)
				else:
					self.cumm_variable.append(self.var_acummulation)
				
				# reset variables
				self.time_grid.append(self.pdate)
				self.pdate = self.idate
				self.idate = addtime(self.idate, self.delta)
				self.nsteps = 1
				self.var_acummulation = None
				#print(t_date, "Date: ", date, " - ", self.idate)
				#print(self.var_maximum)
				#if (t_date < len(date_sim_dt)-1):
					#print(t_date, "Date: ", date, " - ", self.idate)
				self.var_maximum = None
			#print(len(self.cumm_variable))
			#print('Accum: ', self.var_acummulation)
			# check the if the last step has been processed
			# check if variable has been accumulated, otherwise
			# store the available dataset, skip if it has already
			# been added
			if (t_date == len(date_sim_dt)-1):
				#print("Last date: ", t_date, "Date: ", date, " - ", self.idate)
				if self.var_acummulation is not None:
					self.nsteps_vector.append(self.nsteps)
					if self.store_max is True:
						self.cumm_variable.append(self.var_maximum)
					else:
						self.cumm_variable.append(self.var_acummulation)
					self.time_grid.append(self.pdate)
		pass
	
	def save_csv_var(self, fname, multi_files=True):
		"""This function save multiple arrays in a csv file
		
		Parameters
		----------
		fname : str
			filename of csv files to store
		multi_files : bool
			flag to save variables in one file or in multiple files
			True - save in multiple files
			False - save variables in one file

		Returns
		-------
		csv files
			output files in csv format
		"""
		# check if there are variables to store otherwise exit function
		if self.store_var_names is None:
			print("No variables to store")
			return
		
		# additional variables
		# var_name:	name of the variable to store
		# length_var:	number of points to store
		
		if self.save_results is True:
			# number of variables
			nvar = len(self.store_var_names)
			# change list to numpy array
			self.cumm_variable = np.array(self.cumm_variable)
			# grid size
			if multi_files is False:
				df = pd.DataFrame()
				df['Date'] = self.time_grid[:]
			isize = 0
			for i, iname in enumerate(self.store_var_names):
				#npre = dataset.createVariable('pre', np.float32, ('time', 'lat', 'lon'), zlib=True)
				if save_all is True:
					# slice dataset to assign variable vame
					var_size = self.store_var_length[i]
					inodes = range(isize, isize+var_size)
					data = self.cumm_variable[:,inodes]
					factor = 1
					# calulate the average for especif variables
					if (iname == 'tht') or (iname == "wte") or (iname == "ssz"):
						#print(self.nsteps_vector)
						factor = np.array(self.nsteps_vector, dtype=float)
						#print("Factor: ", factor)
						factor = 1/factor
						data = data.T
						data = factor*data[np.newaxis,:]
						data = data[0]
						data = data.T
						#print("Factor: ", factor)
						
					# create list of comuns name
					columname = [self.store_var_names[i] + '_'+ str(k) for k in range(var_size)]
					
					
					if multi_files is False:
						# save variables in only one file
						for k, icolumname in enumerate(columname):
							df[icolumname] = data[:, k]
						
					else:
						# save variables in a multiple files
						# create pandas dataframe
						df = pd.DataFrame(data, columns=columname)
						df['Date'] = self.time_grid[:]

						# save to csv
						fname_csv = fname+self.store_var_names[i]+'.csv'
						df.to_csv(fname_csv, index=False)
					
				isize += var_size
			if multi_files is False:
				fname_csv = fname+'.csv'
				df.to_csv(fname_csv, index=False)
			

	def save_netCDF_var(self, fname, latitude, longitude, nodes, projection=None):
		"""This function save multiple arrays in a netcdf file
		
		Parameters
		----------
		fname : str
			filename of csv files to store
		latitude : numpy array
			x-coordinates of gridded dataset (lat-dimension)
		longitude : numpy array
			y-coordinates of gridded dataset (lon-dimension)
		multi_files : bool
			flag to save variables in one file or in multiple files
			True - save in multiple files
			False - save variables in one file

		Returns
		-------
		netcdf
			output files in netcdf format
		"""
		# check if there are variables to store otherwise exit function
		if self.store_var_names is None:
			print("No variables to store")
			return
			# additional variables
			# var_name:	name of the variable to store
			# length_var:	number of points to store
		
		if self.save_results is True:
			# number of variables
			var_size = len(nodes)
			# change list to numpy array
			self.cumm_variable = np.array(self.cumm_variable)
			# grid size
			nrow = len(latitude)
			ncol = len(longitude)

			# create a mask to save space 
			grid_size = nrow*ncol
			grid = np.full(grid_size, -9999., dtype=float)
			
			# create netcdf file
			dataset = Dataset(fname, 'w', format='NETCDF4_CLASSIC')
			dataset.createDimension('time', None)		
			dataset.createDimension('lon', ncol)		
			dataset.createDimension('lat', nrow)		
			dataset.description = self.dt_time+": Units of time depends on time step"
			dataset.source = "Variable generated using: DRYPv2.0"
			if projection is not None:
				dataset.projection = projection

			# Create coordinate variables for 4-dimensions		
			lat = dataset.createVariable('lat', np.float32, ('lat',))		
			lon = dataset.createVariable('lon', np.float32, ('lon',))		
			time = dataset.createVariable('time', np.float32, ('time',))
			time.units = 'hours since 1980-01-01 00:00:00'		
			time.calendar = 'gregorian'
			lon.units = 'meters'
			lat.units = 'meters'
			#print(self.nsteps_vector)
			# create variable
			for ivar in self.store_var_names:
				dataset.createVariable(ivar, np.float32, ('time', 'lat', 'lon'), fill_value=-9999., zlib=True)
				dataset.variables[ivar].units = UNIT_NAME_VAR[ivar]
				dataset.variables[ivar].long_name = LONG_NAME_VAR[ivar]
						
			# save variables
			for j, idate in enumerate(self.time_grid):
				time[j] = date2num(idate, units=time.units, calendar=time.calendar)
				isize = 0
				for k, iname in enumerate(self.store_var_names):
					if save_all is True:
						# precipitation
						factor = 1.0
						if (iname == 'tht') or (iname == "wte") or (iname == "ssz") or (iname == 'thtrp'):
							factor = 1.0/self.nsteps_vector[j]
							
						# selec nodes of the whole variable array 
						inodes = range(isize, isize+var_size)
						
						# save values in active grid nodes
						grid[nodes] = self.cumm_variable[j,inodes]*factor
						# convert 1D array into 2D grid array
						grid2D = grid.reshape(nrow, ncol)
						# store data in the variable name
						dataset.variables[iname][j] = grid2D[:,:]
						
					isize += var_size
			lat[:] = latitude
			lon[:] = longitude
			
			dataset.close()

def str2timedelta(date, delta):
	"""Generate an array of delta time step, indicating units
	It will assume a year time step if only one number is provided
	format Y M D H
	
	Parameters
	----------
	delta: string indicating time step units, e.g (1Y, 1M)
	
	Returns
	-------
	dt:	array of time step units.
	"""
	#print(delta)
	dt = [0, 0, 0, 0]
	if len(delta) > 1:
		dt_t = int(delta[:-1])
		dt_delta = delta[-1]
		#print(delta, type(dt_t), dt_delta)
		if dt_delta == 'H':
			dt[3] = dt_t
		elif dt_delta == 'D':
			dt[2] = dt_t
		elif dt_delta == 'M':
			dt[1] = dt_t
		else:
			dt[0] = dt_t
	else:
		if delta == 'H':
			dt[3] = 1
		elif delta == 'D':
			dt[2] = 1
		elif delta == 'M':
			dt[1] = 1
		else:
			dt[0] = 1
	return dt

def addtime(date, dt):
	"""Get a delta time step
	
	Parameters
	----------
	date:	staring date
	dt:		array of delta time, obtained with str2timedelts fuc

	Returns
	------
	data:	date added dt
	"""

	# add time step in years
	if dt[0] > 0:
		date = datetime.date(date.year+1,1,1)

	# add time steps in months
	if dt[1] > 0:
		if date.month == 12:
			#date.month = 1
			#date.year += 1
			date = datetime.datetime(date.year+1,1,1)
		else:
			#date.month += dt[1]
			date = datetime.datetime(date.year, date.month+1, 1)
	
	# add time steps in days
	if dt[2] > 0:
		#print(type(date))
		date = date + timedelta(days=dt[2])#, hours=dt[3])
	if dt[3] > 0:
		date = date + timedelta(hours=dt[3])
	#print(date)
	return date

def save_map_to_rastergrid2(grid, field, fname):
	os.remove(fname) if os.path.exists(fname) else None
	if print_maps_end is True:
		files = write_esri_ascii(fname, grid, field)

def save_map_to_rastergrid(grid, field, fname):
	os.remove(fname) if os.path.exists(fname) else None
	field[np.isnan(field)] = -9999
	grid.at_node['aux_grid'] = field[:]
	if print_maps_end is True:
		files = write_esri_ascii(fname, grid, 'aux_grid')

def save_map_to_rasterfile(grid, field, fname):
	"""Save a map to a raster file using rasterio
	Parameters
	----------
	grid:	grid properties
		grid size, profile, transform
	field:	numpy array
		field to save
	fname:	str
		filename of the raster file
	Returns
	-------
	raster file
	"""
	# check if file exists
	os.remove(fname) if os.path.exists(fname) else None

	# replace nan values by -9999
	field[np.isnan(field)] = -9999

	# rehshape field to 2D array
	nrow = grid['N_x']
	ncol = grid['N_y']
	field = np.flip(field.reshape(ncol, nrow), axis=0)

	# save raster file	
	if print_maps_end is True:
		save_raster(fname, field, grid['profile'], grid['transform'])

def remove_variables_from_dict(data, variables):
	""" remove keys of a dictionary
	
	Parameters
	----------
	data:	dictionary
	variable:	key to remove from dictionary
	
	Returns
	-------
	data:	dictionary without keys -variables

	"""
	for key in variables:
		data.pop(key, None)
	return data

def drop_false_keys(store_keys):
	"""Function to select variables that have false values in

	Parameters
	----------
	keys:	list of kyes available at the dictionary
	store_keys:	dictionary with boolean values to store variables

	Returns
	-------
	drop_keys:	list of variables to drop from dict
	"""
	var_value = map(operator.not_, list(store_keys.values()))
	drop_keys = list(compress(list(store_keys.keys()), var_value))

	return drop_keys

def get_list_of_length_field_dict(var):
	"""Get length of values of each element from a dictionary"""
	return [len(value) for key, value in var.items()]

def del_all(data, var_to_remove):
	"""Remove list of elements from mapping.
	check wich optionis faster"""
	for key in var_to_remove:
		del data[key]
	return data

def save_raster(fname, data, profile, transform):
	os.remove(fname) if os.path.exists(fname) else None
	with rasterio.open(fname, 'w', **profile) as dst:
		# Write the modified raster data
		# ensure that data has the same format type
		dst.write(np.array(data, dtype=profile['dtype']), 1)
		# Set the affine transformation
		dst.transform = transform
