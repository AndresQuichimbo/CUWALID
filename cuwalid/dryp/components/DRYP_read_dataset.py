import warnings
warnings.filterwarnings('ignore', message="overflow encountered in reduce")
warnings.filterwarnings('ignore', message="invalid value encountered in subtract")
#  slope = (y_hi - y_lo) / (x_hi - x_lo)[:, None]
warnings.filterwarnings('ignore', message="invalid value encountered in add")
#  y_new = slope*(x_new - x_lo)[:, None] + y_lo

import os
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray  # activate the rio accessor
from netCDF4 import Dataset, num2date, date2num
from datetime import datetime, timedelta
from cuwalid.dryp.components.DRYP_projection import reproject_dataset

#@profile
class read_temporal_dataset():
	"""Read all input dataset

	Parameters
	----------
	file_type:	0 for csv and 1 for netCDF
	
	Returns
	-------
	dataset:
	
	"""
	def __init__(self, filename, file_type, dt, end_date, ini_date):#, str_dt):
		""" Setting variables and time steps for reading inputs
		
		Parameters
		-----------
		filename: 	file name of dataset
		file_type:	file format 0 for csv files and 1 to netCDF fiels
		end_date:	end date of simulation
		ini_date:	initial date
		dt:			model time step)
		
		Returns
		-------
		
		"""
		
		freq_dt=str(int(dt))+'min'
		
		if os.path.exists(filename):
		
			if file_type == 1: 
				# Read netCDF fiels
				data_set = Dataset(filename, 'r')
				
				# slicing, aggregation, and interpolation.
				
				# Change number to datetime
				time_aux = num2date(data_set['time'][:-1],
								units=data_set['time'].units,
								calendar=data_set['time'].calendar)
				
				self.data_set = data_set
				
				# change time nstimedate to datetime
				time = []
				for iidate in time_aux:
					if not iidate == None:
						time.append(datetime(
							iidate.year,
							iidate.month,
							iidate.day,
							iidate.hour,
							iidate.minute)
							)
					else:
						time.append(None)
				time = np.array(time)
			
			else:
				
				# Read time series of precipitation	csv
				data_set = pd.read_csv(filename)
				
				# change to txt to datetime
				data_set["Date"] = pd.to_datetime(data_set['Date'], format = '%d/%m/%Y %H:%M')
				
				# Find id of the precipitation array for the the simulation period 
				idate_aux = np.where((data_set["Date"] <= end_date)
									& (data_set["Date"] >= ini_date))[0]
				
				self.data_set = data_set.iloc[idate_aux]
				
				if dt > 60:
					# aggregate data to the model time step
					self.data_set.index = pd.DatetimeIndex(self.data_set['Date'])
					
					self.data_set = (self.data_set.resample(freq_dt).sum()).reset_index()
				
				if not idate_aux.size:
					print(filename)
					raise Exception("Dataset do not match the simulation period")
		else:
			
			self.data_set = None
			print(filename, 'Flux data not provided')
				
		# find precipitation and PET for an specific time step
	def get_dataset_one_step(self, t, env_state, file_type, field):#, filename):
		"""
		Call this to execute a step in the model.

		Parameters
		-----------
		t: 			time step index
		env_state:	grid
		file_type:	file format 0 for csv files and 1 to netCDF fiels
		field:		variable name
		
		Returns
		-------
		dataset_at_t:	list of values
		
		"""		
		dataset_at_t = np.zeros(env_state.grid_size)
		
		if not np.isnan(self.time[t]):
			
			if file_type == 1:
				dataset_at_t = (self.data_set.variables[field][self.time[t]][:]).flatten()
			
			else: # Uniform precipitation over the whole catchement
				# add interpo;ation here for future versions**
				dataset_at_t = np.ones(env_state.grid_size)*self.data_set[field][self.time[t]]
		
		return dataset_at_t
		
	def get_point_dataset_one_step(self, t):
		"""
		Call this to read forcing data at time step t

		Parameters
		----------
		t: 			time step index
		env_state:	grid

		Returns
		-------
		dataset_at_t:	list of values
		
		"""
		head = list(self.data_set)
		
		head.remove('Date')
		#print(type(head), t)
		dataset_at_t = np.array(self.data_set[head].iloc[t])
	
		return dataset_at_t

class read_dataset_interp(object):
	"""Read netcdf files as input datasets
	
	"""
	#@profile
	def __init__(self, dt, dt_ds, ini_date, end_date, file_format,
		reproject, interpolate, grid_length, lat, lon, proj=None,
		projm=None):
		"""set model grid time series and model files

		Parameters
		----------
		dt:			model time step
		dt_ds:		data set frequency
		ini_date:	datetime- inital date for the simulation
		end_date:	datetime- final date for the simulation
		file_format:integer- 1: read multiple files
		reproject:	integer- 1: activate reprojection
		interpolate: integer- 1: activate interpolation
		grid_length: size of the grid
		proyection:	define the pojection of the dataset (optional)

		Returns
		--------
		
		"""
				
		# Define the time step for temporal aggregation
		self.freq_dt=str(int(dt))+'min'
		
		# Define dataset x and y intervals for spatial interpolation
		#self.lon = env_state.lon
		#self.lat = env_state.lat
		
		# Check if the simulation period is rigth
		
		if ini_date >= end_date:
			raise Exception("End of the simulation period should be later than initial date")
		
		
		self.date_sim_dt = pd.date_range(ini_date, end_date,
			#periods = t_end*inputfile.dt_hourly*inputfile.dt_sub_hourly,
			freq = str(int(dt))+'min')
		self.date_sim_dt = self.date_sim_dt[:-1]
		
		# Save number of time steps
		# self.t_end = t_end
		self.read_before = 1
		self.fill_value = 1
		self.file_format = file_format
		self.reproject_ds = reproject
		self.interpolate_ds = interpolate
		self.read_before_ds = 1
		self.grid_length = grid_length
		
		# rainfall component time step
		self.dt = dt
		self.dt_ds = dt_ds
		self.ini_date = ini_date
		self.end_date = end_date
		
		# check if temporal interpolation is required
		if dt_ds != self.dt:
			self.nsteps_day_ds = int(1440/dt)
		else:
			self.nsteps_day_ds = int(1440/dt_ds)
		
		if self.dt_ds < 60:
			self.nsteps_hour_ds = int(1)
		else:
			self.nsteps_hour_ds = int(self.dt_ds/60)
		
		self.j_step = 0
				
		self.lat = lat
		self.lon = lon

		if proj is None:
			self.proj = "EPSG:4326"
		else:
			self.proj = proj
		if projm is None:
			self.projm = "EPSG:4326"
		else:
			self.projm = projm

	#@profile
	def get_one_step_dataset(self, j_step, fname_ds, field):
		"""
		Call this to execute a step in the model.

		Parameters
		----------
			j_step:		Counter for time
			fname_ds:	filename dataset

		Returns
		-------
			data:	precipitation for the actual time step
					
		"""
		
		# find the date of the simulation time period at time step j_step 
		idate_ds = self.date_sim_dt[j_step]# - timedelta(hours=(self.nsteps_pre-1))
		
		if self.file_format > 0:
		
			# create zero array for precipitation
			#data = np.zeros(env_state.grid_size)
			#if (self.read_before_ds == 1):# or (self.file_format == 2):
			##if self.file_format == 1:
			#	# find the location of the date in the dataset
			#	# lacation depending on the hour
			#	hour_ds = int(int(idate_ds.strftime('%H'))/self.nsteps_hour_ds)
			#	
			#	# location depending on the day, for multi-netcdf format or first read 
			#	j_step = int(int(idate_ds.strftime('%j'))-1)*self.nsteps_day_ds + hour_ds
			#	#print(idate_ds, j_step)
			
			#if (self.read_before_ds == 0) and (self.file_format == 2):
			# make zero at the beggining of each year
			#if (self.read_before_ds == 0) and (self.file_format == 2):
			
			# find the location of the date in the dataset
			# lacation depending on the hour
			# numbers of hours of the day depending on the time step
			hour_ds = int(int(idate_ds.strftime('%H'))/self.nsteps_hour_ds)
				
			# location depending on the day, for multi-netcdf format or first read 
			# number of hours for the model from the beggining of the year
			aux_time_j = int(int(idate_ds.strftime('%j'))-1)*self.nsteps_day_ds + hour_ds
			
			# add line to change to montly files
			# needs to find 
			year = idate_ds.year
			month = idate_ds.month
			#day = idate_ds.day
			#hour = idate_ds.hour

			if (self.read_before_ds == 1):
				self.step_0 = 0
			
			if (self.file_format == 3):# and (self.read_before_ds == 0):
				# find the location of the day at the beggining og the month
				date_ini = datetime(year, month, 1, 0, 0, 0)
				id_ini_month = int(int(date_ini.strftime('%j'))-1)*self.nsteps_day_ds
				# find the location of the
				j_step = aux_time_j - id_ini_month
				#print(idate_ds, date_ini, id_ini_month)
			else:
				id_ini_month = 0
						
			if (self.read_before_ds == 1):			
				j_step = aux_time_j - id_ini_month
				self.j_step = int(j_step)
			
			# modified to read giraf, MONTHLY -----------------------
			if (self.read_before_ds == 0) and (self.file_format == 3):
				if j_step == 0:
					self.read_before_ds = 1
				
			#---------------------------------------------------------
			if (self.read_before_ds == 0) and (self.file_format == 2):
				if aux_time_j == 0:
					self.j_step = 0
						
				j_step = self.j_step

			# THIS IS A PARTIAL SOLUTION, SO IT WILL BE MODIFIED LATER
			# this will allow the model to read datasets fstarting from any time step
			if (self.read_before_ds == 1) and (self.file_format == 1):
				self.step_0 = aux_time_j + 0
			
			if (self.read_before_ds == 0) and (self.file_format == 1):
				j_step = self.j_step
			
			#print(idate_ds, aux_time_j, j_step, self.j_step, self.file_format, id_ini_month)
			#if field == 'pet':
			#	keys = ['longitude', 'latitude']
			#else:
			keys = ['lon', 'lat']
			
			# Read data at the begining of the simulation or if a new dataset starts
			if (self.read_before_ds == 1) or (j_step == 0):
				
				# Filename of the current year
				if self.file_format == 2:
					# read yearly files files
					#fname_ds = fname_ds + '_' + str(idate_ds.year) + '.nc'
					fname_ds = fname_ds.replace("YYYY", str(idate_ds.year))
				elif self.file_format == 3:
					# read monthly files
					#fname_ds = fname_ds + '_' + str(idate_ds.year) + '*'
					# customize it for ghiraf
					if month < 10:
						str_month = '0'+str(month)
					else:
						str_month = str(month)

					fname_ds = fname_ds.replace("YYYY", str(idate_ds.year))
					fname_ds = fname_ds.replace("MM", str_month)
					#fname_ds = fname_ds + '/' + str(idate_ds.year) + '/chaf-v00_' + str(idate_ds.year) + '-' + str_month+'*'
					#fname_ds = fname_ds + '/' + str(idate_ds.year) + '/IMERG_' + str(idate_ds.year) + '-' + str_month+'*'
				
				#print(fname_ds)
				# read dataset
				self.ds = xr.open_dataset(fname_ds)
				# check if dimension names are compatible with DRYP names
				if 'latitude' in list(self.ds.coords):
					self.ds = self.ds.rename({'longitude':'lon', 'latitude':'lat'})

				if field == 'pet':					
					# THIS IS ONLY FOR HPET DATA AT HOURLY TIME STEPS
					self.ds = xr.where(self.ds < 0.0, 0.0, self.ds)
					self.ds = xr.where(self.ds > 10.0, 0.2, self.ds)
					#self.ds = self.ds.ffill('lon')
					#self.ds = self.ds.bfill('lat')
					#self.ds = self.ds.ffill('lon')
					#self.ds = self.ds.bfill('lat')
				
				if field == 'pre':
					if 'rain' in list(self.ds.variables):
						self.ds = self.ds.rename({'rain':'pre'})
					if 'precipitation' in list(self.ds.variables):
						self.ds = self.ds.rename({'precipitation':'pre'})
					
					self.ds = xr.where(self.ds < 0.0, 0.0, self.ds)
					self.ds = xr.where(self.ds > 200.0, 200.0, self.ds)
				#print(self.ds)#, self.ds['time'], self.ini_date, self.end_date)
				# slice data for the simulation period
				# Do not apply for multi-data files
				#if self.file_format == 1:
				#	self.ds = self.ds.sel(time=slice(self.ini_date, self.end_date))
				#print(self.ds, self.ds['time'], self.ini_date, self.end_date)
				# reproject dataset
				if self.reproject_ds == 1:
					self.ds = reproject_dataset(self.ds, self.proj, self.projm)#, keys)
					
				if self.dt_ds != self.dt:
					# temporal resampling
					self.ds = self.ds.resample(time=self.freq_dt).sum()
					#print(self.ds)		
				# flag to no read every time the whole dataset
				self.read_before_ds = 0
			
			#print(self.ds, self.dt_ds, self.dt)		
			if self.interpolate_ds == 1:
				# Spatial interpolation
				ds = self.ds.isel(time=[j_step-self.step_0]).interp(
					lat=self.lat, lon=self.lon,
					method="linear")
			else:
				ds = self.ds.isel(time=[j_step-self.step_0])
				
			data = np.array(ds.variables[field][0][:]).flatten()
			#print(ds)			
			self.j_step += 1
			
		else:
			
			# Read time series of precipitation	csv
			if (self.read_before_ds == 1) or (j_step == 0):
				self.ds = pd.read_csv(fname_ds)
				#print(self.ds)
				# change to txt to datetime
				self.ds["Date"] = pd.to_datetime(self.ds['Date'])#, format='%d/%m/%Y %H:%M')
				
				# slice data set, select only the simulation period
				idate = np.where((self.ds["Date"] < self.end_date)
								& (self.ds["Date"] >= self.ini_date))[0]
				
				if not idate.size:
					#print(fname_ds)
					raise Exception("Dataset do not match the simulation period")
					
				self.ds = self.ds.iloc[idate]
				
				if self.dt != self.dt_ds:
					# aggregate data to the model time step
					self.ds.index = pd.DatetimeIndex(self.ds['Date'])
					self.ds = (self.ds[[field]].resample(self.freq_dt).sum())#.reset_index()
					
				#time_pre = fpre["Date"]
				self.read_before_ds = 0
				
			data = np.full(self.grid_length, self.ds[field].iloc[j_step])
		
		return data
		
# new read data for savi
class read_dataset(object):
	"""Read input datasets from different sequential files
	Parameters
	Returns
	
	"""
	def __init__(self, dt, dt_ds, ini_date, end_date, file_format,
		reproject, interpolate, grid_length):
		"""set model grid time series and model files

		Parameters
		----------
		dt:			model time step
		dt_ds:		data set frequency
		ini_date:	datetime- inital date for the simulation
		end_date:	datetime- final date for the simulation
		file_format:integer- 1: read multiple files
		reproject:	integer- 1: activate reprojection
		interpolate: integer- 1: activate interpolation
		grid_length: size of the grid

		Returns
		-------
		
		"""
				
		# Define the time step for temporal aggregation
		self.freq_dt=str(int(dt))+'min'
		
		# Define dataset x and y intervals for spatial interpolation
		#self.lon = env_state.lon
		#self.lat = env_state.lat
		
		# Check if the simulation period is rigth
		
		if ini_date >= end_date:
			raise Exception("End of the simulation period should be later than initial date")
		
		
		self.date_sim_dt = pd.date_range(ini_date, end_date,
			#periods = t_end*inputfile.dt_hourly*inputfile.dt_sub_hourly,
			freq = str(int(dt))+'min')
		self.date_sim_dt = self.date_sim_dt[:-1]
		
		
		#self.t_end = t_end
		self.read_before_pre = 1
		self.year_pre = int(ini_date.year)
		self.dt = dt
		self.nsteps_pre = int(dt/dt_ds)
		self.nsteps_day_pre = int(1440/dt_ds)
		self.nsteps_hour_pre = int(dt_ds/60)
		self.ini_date = ini_date
		self.end_date = end_date
				
		self.grid_length = grid_length
		self.file_format = file_format
		self.read_before_ds = 1
	
	# find precipitation and PET for an specific time step
	def get_one_step_dataset(self, j_step, fname_ds, field):
		"""
		Call this to execute one step in the model.

		Parameters
		----------
			j:	Counter for time
		
		Returns
		-------
			rain:	precipitation for the actual time step
			pet:	potential evapotranspiration for current timestep
		"""
		#date = self.date_sim_dt[j]
		# Precipitation
		idate_pre = self.date_sim_dt[j_step] - timedelta(hours=(self.nsteps_pre-1))
		#print(type(idate_pre), idate_pre)
		data = np.zeros(self.grid_length)
		
		if self.file_format == 1:
		
			if self.read_before_pre == 1:
				self.i_tstep = j_step
				hour_pre = int(int(idate_pre.strftime('%H'))/self.nsteps_hour_pre)
				j_tp = (int(idate_pre.strftime('%j'))-1)*self.nsteps_day_pre + hour_pre
				self.fpre = Dataset(fname_ds, 'r')
				
				self.i_tstep = j_step + j_tp
				data_ti = (self.fpre.variables[field][self.i_tstep][:]).flatten()
				self.read_before_pre = 0
			
			else:
				data_ti = (self.fpre.variables[field][self.i_tstep][:]).flatten()
				self.read_before_pre = 0
				
			self.i_tstep += 1
			data += data_ti
	
		elif self.file_format == 2:
		
			for i in range(self.nsteps_pre):			
				if self.year_pre == idate_pre.year:
					hour_pre = int(int(idate_pre.strftime('%H'))/self.nsteps_hour_pre)
					j_tp = (int(idate_pre.strftime('%j'))-1)*self.nsteps_day_pre + hour_pre
					
					if self.read_before_pre == 1:
						fname_pre = fname_ds + '_' + str(idate_pre.year) + '.nc'
						self.fpre = Dataset(fname_pre, 'r')
						data_ti = (self.fpre.variables[field][j_tp][:]).flatten()
						self.read_before_pre = 0
					else:
						data_ti = (self.fpre.variables[field][j_tp][:]).flatten()
						self.read_before_pre = 0
				else:
					hour_pre = int(int(idate_pre.strftime('%H'))/self.nsteps_hour_pre) 
					j_tp = (int(idate_pre.strftime('%j'))-1)*self.nsteps_day_pre + hour_pre
					
					fname_pre = fname_ds + '_' + str(idate_pre.year) + '.nc'
					self.fpre = Dataset(fname_pre, 'r')
					data_ti = (self.fpre.variables[field][j_tp][:]).flatten()
					self.read_before_pre = 0
				data += data_ti
				self.year_pre = int(idate_pre.year)
				idate_pre += timedelta(hours=1)
		
		else:
			
			# Read time series of precipitation	csv
			if (self.read_before_ds == 1) or (j_step == 0):
				self.ds = pd.read_csv(fname_ds)
				#print(self.ds)
				# change to txt to datetime
				self.ds["Date"] = pd.to_datetime(self.ds['Date'])#, format='%d/%m/%Y %H:%M')
				
				# slice data set, select only the simulation period
				idate = np.where((self.ds["Date"] < self.end_date)
								& (self.ds["Date"] >= self.ini_date))[0]
				
				if not idate.size:
					print(fname_ds)
					raise Exception("Dataset do not match the simulation period")
					
				self.ds = self.ds.iloc[idate]
				
				if self.dt > 60:
					# aggregate data to the model time step
					self.ds.index = pd.DatetimeIndex(self.ds['Date'])
					self.ds = (self.ds.resample(self.freq_dt).sum())#.reset_index()
					
				#time_pre = fpre["Date"]
				self.read_before_ds = 0
				
			data = np.full(self.grid_length, self.ds[field].iloc[j_step])
		
		
		return data
