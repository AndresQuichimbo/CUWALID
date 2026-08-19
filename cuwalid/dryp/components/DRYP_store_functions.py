import os
import numpy as np
import pandas as pd
import datetime
from datetime import timedelta
from netCDF4 import Dataset, num2date, date2num
from landlab.io import write_esri_ascii
from itertools import compress
import operator
import concurrent.futures
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

		# --- Optional incremental / streaming netCDF output ------------
		# When enabled (see enable_netcdf_streaming), completed output
		# periods are written straight to disk once a configurable
		# number of them have accumulated, instead of being buffered in
		# memory for the entire simulation. This is opt-in and fully
		# backward compatible: if it is never enabled, save_netCDF_var
		# behaves exactly as before.
		self._nc_stream_cfg = None
		self._nc_ds_state = None
		# background writer: at most one write is ever in flight (see
		# _wait_for_pending_write) - this bounds memory (only one
		# snapshot alive at a time) and avoids any concurrent access to
		# the same netCDF file handle / reusable grid buffer.
		self._nc_write_executor = None
		self._nc_pending_future = None
		#print(self.store_max)
		#if store_max is True:
		#	self.store_max = True
		#else:
		#	self.store_max = False
		#print(self.store_max)
		pass

	def enable_netcdf_streaming(self, fname, latitude, longitude, nodes,
			projection=None, flush_every=60, split_by=None, async_write=True):
		"""Write completed output periods straight to a netCDF file on
		disk as soon as `flush_every` of them have accumulated, instead
		of buffering the entire simulation's gridded output in memory.

		Call this once, right after creating a GlobalGridVar object,
		for stores whose output is saved via save_netCDF_var (e.g.
		grid_var, grid_rmax, grid_lks, grid_vmax, grid_rpvar,
		grid_pndvar, grid_veg). It has no benefit - but also no effect
		- on stores that are only ever saved via save_csv_var.

		The existing call to save_netCDF_var(fname, latitude,
		longitude, nodes, projection=...) at the end of the run still
		needs to happen exactly as before: it will simply flush
		whatever is left buffered and close the file, rather than
		writing everything from scratch, so no other code needs to
		change.

		Parameters
		----------
		fname : str
			output netCDF filename (the same value you would
			otherwise pass to save_netCDF_var). When split_by is set,
			this is used as a template: the period is inserted before
			the extension, e.g. 'out.nc' -> 'out_2020-01.nc' for a
			monthly split.
		latitude, longitude : numpy array
			grid coordinate arrays
		nodes : numpy array
			node indices this store's variables correspond to
		projection : optional
			projection metadata to attach to the file
		flush_every : int
			number of completed output periods to buffer in memory
			before writing them to disk (default 60, e.g. roughly two
			months of daily output). Buffered periods are still split
			across separate files at a `split_by` boundary even if
			flush_every hasn't been reached yet, so output files never
			mix periods.
		split_by : str or None
			If given, start a new output file at each period boundary
			instead of writing one continuous file for the whole run -
			useful to keep individual files a manageable size for very
			large domains / long runs. One of:
			  - None (default): a single continuous file, as before.
			  - 'D' / 'day' / 'daily': one file per calendar day.
			  - 'M' / 'month' / 'monthly': one file per calendar month.
			  - 'Y' / 'year' / 'yearly': one file per calendar year.
		async_write : bool
			If True (default), the actual disk write for each flush
			runs in a background thread so the simulation can keep
			computing the next period instead of waiting for the
			write to finish. netCDF4/HDF5 writes release the GIL
			while blocked on I/O, so this genuinely overlaps with
			computation. At most one write is ever in flight (a new
			flush waits for the previous one before starting), which
			also caps memory to roughly one extra buffered batch. Set
			to False to write synchronously instead (e.g. for
			debugging, or on a filesystem/setup where background
			writes are undesirable).
		"""
		valid_split = (None, 'D', 'd', 'day', 'daily',
					   'M', 'm', 'month', 'monthly',
					   'Y', 'y', 'year', 'yearly')
		if split_by not in valid_split:
			raise ValueError(
				f"Unsupported split_by value: {split_by!r}. Use one of "
				f"{valid_split}.")
		self._nc_stream_cfg = dict(
			fname=fname, latitude=latitude, longitude=longitude,
			nodes=nodes, projection=projection,
			flush_every=max(1, int(flush_every)),
			split_by=split_by, async_write=bool(async_write),
		)

	def _nc_period_key(self, date, split_by):
		"""Group key identifying which output file `date` belongs to."""
		if split_by is None:
			return None
		if split_by in ('D', 'd', 'day', 'daily'):
			return (date.year, date.month, date.day)
		if split_by in ('M', 'm', 'month', 'monthly'):
			return (date.year, date.month)
		if split_by in ('Y', 'y', 'year', 'yearly'):
			return (date.year,)
		return None

	def _nc_period_filename(self, base_fname, period_key, split_by):
		"""Insert a period-specific suffix before the file extension."""
		if split_by is None or period_key is None:
			return base_fname
		root, ext = os.path.splitext(base_fname)
		if len(period_key) == 3:
			suffix = f"_{period_key[0]:04d}-{period_key[1]:02d}-{period_key[2]:02d}"
		elif len(period_key) == 2:
			suffix = f"_{period_key[0]:04d}-{period_key[1]:02d}"
		else:
			suffix = f"_{period_key[0]:04d}"
		return f"{root}{suffix}{ext}"

	def _nc_get_executor(self):
		if self._nc_write_executor is None:
			# a single worker keeps writes strictly serialized (safe
			# for a single netCDF file handle) while still overlapping
			# I/O with the main thread's ongoing computation
			self._nc_write_executor = concurrent.futures.ThreadPoolExecutor(
				max_workers=1)
		return self._nc_write_executor

	def _nc_wait_for_pending_write(self):
		"""Block until any in-flight background write has finished.

		Called before touching the open dataset/grid buffer again (at
		the start of the next flush, or before closing/rolling over to
		a new file) - this is what keeps the single background write
		safe without any locks: the main thread simply never touches
		shared state while a write could still be using it.
		"""
		if self._nc_pending_future is not None:
			self._nc_pending_future.result()
			self._nc_pending_future = None

	def _nc_open_file(self, fname, period_key):
		nodes = self._nc_stream_cfg['nodes']
		latitude = self._nc_stream_cfg['latitude']
		longitude = self._nc_stream_cfg['longitude']
		projection = self._nc_stream_cfg['projection']
		var_size = len(nodes)
		nrow = len(latitude)
		ncol = len(longitude)
		grid_size = nrow*ncol

		dataset = Dataset(fname, 'w', format='NETCDF4_CLASSIC')
		dataset.createDimension('time', None)
		dataset.createDimension('lon', ncol)
		dataset.createDimension('lat', nrow)
		dataset.description = self.dt_time+": Units of time depends on time step"
		dataset.source = "Variable generated using: DRYPv2.0"
		if projection is not None:
			dataset.projection = projection

		lat_var = dataset.createVariable('lat', np.float32, ('lat',))
		lon_var = dataset.createVariable('lon', np.float32, ('lon',))
		time_var = dataset.createVariable('time', np.float32, ('time',))
		time_var.units = 'hours since 1980-01-01 00:00:00'
		time_var.calendar = 'gregorian'
		lon_var.units = 'meters'
		lat_var.units = 'meters'

		for ivar in self.store_var_names:
			dataset.createVariable(
				ivar, np.float32, ('time', 'lat', 'lon'),
				fill_value=-9999., zlib=True,
				chunksizes=(1, nrow, ncol))
			dataset.variables[ivar].units = UNIT_NAME_VAR[ivar]
			dataset.variables[ivar].long_name = LONG_NAME_VAR[ivar]

		lat_var[:] = latitude
		lon_var[:] = longitude

		self._nc_ds_state = dict(
			dataset=dataset,
			grid=np.full(grid_size, -9999., dtype=np.float32),
			nrow=nrow, ncol=ncol, var_size=var_size, nodes=nodes,
			time_idx=0, period_key=period_key, fname=fname,
		)

	def _nc_close_file(self):
		# always wait for any write still targeting this file before
		# closing it - closing while a background write is in flight
		# would corrupt the file or crash.
		self._nc_wait_for_pending_write()
		if self._nc_ds_state is not None:
			self._nc_ds_state['dataset'].close()
			self._nc_ds_state = None

	def _nc_write_batch(self, state, store_var_names, cumm_variable, time_grid, nsteps_vector):
		"""Write one contiguous batch of buffered periods (all
		belonging to the same output file) to disk. Runs either
		directly on the main thread or inside the background writer
		thread - it only touches `state` (the dataset/grid for one
		already-open file) and the snapshot arrays passed in, never the
		live self.cumm_variable/self.time_grid/self.nsteps_vector, so
		it's safe to run concurrently with the simulation continuing to
		accumulate new data.
		"""
		dataset = state['dataset']
		grid = state['grid']
		var_size = state['var_size']
		nodes = state['nodes']
		nrow, ncol = state['nrow'], state['ncol']
		time_units = dataset.variables['time'].units
		time_cal = dataset.variables['time'].calendar

		for j, idate in enumerate(time_grid):
			jt = state['time_idx']
			dataset.variables['time'][jt] = date2num(
				idate, units=time_units, calendar=time_cal)
			isize = 0
			for iname in store_var_names:
				factor = 1.0
				if iname in ('tht', 'wte', 'ssz', 'thtrp'):
					factor = 1.0/nsteps_vector[j]
				inodes = range(isize, isize+var_size)
				grid[nodes] = cumm_variable[j][inodes]*factor
				grid2D = grid.reshape(nrow, ncol)
				dataset.variables[iname][jt] = grid2D[:, :]
				isize += var_size
			state['time_idx'] += 1
		# flush this batch to disk immediately so data is durable as
		# soon as the write "completes", rather than sitting in an
		# HDF5-library buffer indefinitely
		dataset.sync()

	def _flush_netcdf(self, final=False):
		"""Write any buffered output periods to the streaming netCDF
		file(s), creating/rolling over files as needed, and clear them
		from memory. If final=True, also wait for all writes to finish
		and close the currently open file.
		"""
		cfg = self._nc_stream_cfg
		if cfg is None:
			return

		if not self.save_results:
			return

		if self.store_var_names is None:
			if final:
				print("No variables to store")
			return

		# never touch the open file/grid buffer while a previous write
		# might still be using them
		self._nc_wait_for_pending_write()

		split_by = cfg['split_by']
		n = len(self.time_grid)
		start = 0
		while start < n:
			period_key = self._nc_period_key(self.time_grid[start], split_by)
			end = start
			while end < n and self._nc_period_key(self.time_grid[end], split_by) == period_key:
				end += 1
			# [start:end) is one contiguous run belonging to the same
			# output file (time_grid is chronological, so periods are
			# naturally contiguous - no need to group non-locally)

			if self._nc_ds_state is not None and self._nc_ds_state['period_key'] != period_key:
				# crossing a period boundary - finish and close the
				# previous file before starting the next one
				self._nc_close_file()

			if self._nc_ds_state is None:
				fname = self._nc_period_filename(cfg['fname'], period_key, split_by)
				self._nc_open_file(fname, period_key)

			state = self._nc_ds_state
			snapshot_cumm = self.cumm_variable[start:end]
			snapshot_time = self.time_grid[start:end]
			snapshot_nsteps = self.nsteps_vector[start:end]
			store_var_names = self.store_var_names

			is_last_run = (end == n)
			write_sync = (not cfg['async_write']) or (final and is_last_run)
			if write_sync:
				self._nc_write_batch(state, store_var_names,
									 snapshot_cumm, snapshot_time, snapshot_nsteps)
			else:
				self._nc_wait_for_pending_write()  # extra safety, see below
				self._nc_pending_future = self._nc_get_executor().submit(
					self._nc_write_batch, state, store_var_names,
					snapshot_cumm, snapshot_time, snapshot_nsteps)

			start = end

		# free the buffered periods now that they are either safely on
		# disk or handed off (with their own independent snapshot) to
		# the background writer - this is the whole point: memory use
		# stays bounded instead of growing with the simulation length
		self.cumm_variable = []
		self.time_grid = []
		self.nsteps_vector = []

		if final:
			self._nc_close_file()
			if self._nc_write_executor is not None:
				self._nc_write_executor.shutdown(wait=True)
				self._nc_write_executor = None

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
					# create variables (np.concatenate already returns a
					# fresh array, no need to copy it again)
					self.var_acummulation = variables
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
							self.var_maximum = variables

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
					# create variables (no need to copy, np.concatenate
					# already returned a fresh array)
					self.var_acummulation = variables
				else:
					# accumulate the value at the boundary itself (it
					# belongs to the period that is about to be closed).
					# NOTE: previously this addition was gated by
					# `self.start_storing`, which stayed False the first
					# time a period closed and silently dropped this
					# step's contribution from the very first output
					# period. That gate has been removed - the date
					# check below is sufficient to avoid pulling in a
					# value that belongs to the next period.
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
						self.var_maximum = variables
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

				# stream completed periods to disk if incremental
				# netCDF output has been enabled for this store,
				# keeping memory use bounded for large/long runs
				# instead of buffering the whole simulation
				if (self._nc_stream_cfg is not None and
						len(self.cumm_variable) >= self._nc_stream_cfg['flush_every']):
					self._flush_netcdf()
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
					# calculate the average for specific variables
					# NOTE: 'thtrp' added here to match the same set of
					# time-averaged variables used in save_netCDF_var -
					# previously it was summed here but averaged there,
					# giving inconsistent CSV vs netCDF outputs.
					if iname in ('tht', 'wte', 'ssz', 'thtrp'):
						#print(self.nsteps_vector)
						factor = 1.0/np.array(self.nsteps_vector, dtype=float)
						# broadcast factor (per time step) along the time
						# axis without transposing the (possibly large)
						# data array back and forth
						data = data*factor[:, np.newaxis]
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
		# if incremental streaming was enabled for this store (see
		# enable_netcdf_streaming), most of the output has already
		# been written to disk during the run - just flush whatever
		# is left buffered and close the file. The fname/latitude/
		# longitude/nodes/projection arguments are ignored in that
		# case since they were already fixed when streaming was
		# enabled (callers don't need to change anything).
		if self._nc_stream_cfg is not None:
			self._flush_netcdf(final=True)
			return

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
			# use float32 to match the netCDF variable dtype below -
			# avoids doubling memory use and an implicit cast on every
			# write
			grid_size = nrow*ncol
			grid = np.full(grid_size, -9999., dtype=np.float32)
			
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
				dataset.createVariable(
					ivar, np.float32, ('time', 'lat', 'lon'),
					fill_value=-9999., zlib=True,
					# chunk one time-slice at a time - the natural write
					# pattern here - instead of relying on netCDF4's
					# default chunk guess, which can be poor for an
					# unlimited time dimension
					chunksizes=(1, nrow, ncol))
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
