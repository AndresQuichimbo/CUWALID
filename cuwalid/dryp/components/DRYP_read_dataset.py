import warnings
warnings.filterwarnings('ignore', message="overflow encountered in reduce")
warnings.filterwarnings('ignore', message="invalid value encountered in subtract")
#  slope = (y_hi - y_lo) / (x_hi - x_lo)[:, None]
warnings.filterwarnings('ignore', message="invalid value encountered in add")
#  y_new = slope*(x_new - x_lo)[:, None] + y_lo
#import matplotlib.pyplot as plt
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
		
		if filename != None and os.path.exists(filename):
		
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
			#print(filename, 'Flux data not provided')
			print('Flux dataset.....................not provided')

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
		proj_model=None, step_func=False, noskip=True):
		"""set model grid time series and model files

		Parameters
		----------
		dt:			int
			model time step
		dt_ds:		int
			data set frequency
		ini_date:	datetime
			inital date for the simulation
		end_date:	datetime
			final date for the simulation
		file_format:integer
			0 for csv files
			1 for netCDF files
			2 for YEARLY netCDF files
			3 for MONTHLY netCDF files
			4 for DAILY netCDF files
			5 for ensamble netCDF files
		reproject:	bool
			True default values
		interpolate: bool
		 	 True: activate interpolation
		grid_length: int
			size of the grid
		proyection:	obj, string
			define the pojection of the dataset (optional)
		step_func : bool
			reading option to use step function on temporal values
			default values is False, which meand step function not active
		noskip : bool
			reading option to skip reading when file is not available
			True: an error will raised if file is not available, default value
			False: a non data value will return if is not available

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
		
		if file_format > 5:
			print("Provide a valid data type to enable reading")
			print("Use: 0 for csv files")
			print("Use: 1 for netCDF files")
			print("Use: 2 for YEARLY netCDF files")
			print("Use: 3 for MONTHLY netCDF files")
			print("Use: 4 for DAILY netCDF files")
			print("Use: 5 for ensamble netCDF files")
			raise Exception("Change 'data_reading' options in settings file")
			
			
		self.reproject_ds = reproject
		self.interpolate_ds = interpolate
		self.read_before_ds = True
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
		if proj_model is None:
			self.proj_model = "EPSG:4326"
		else:
			self.proj_model = proj_model

		self.step_func = step_func

		self.noskip = noskip

	#@profile
	def get_one_step_dataset(self, j_step, fname_ds, field, time_field="time"):
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
			if fname_ds is not None:
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
				day = idate_ds.day
				#hour = idate_ds.hour

				if (self.read_before_ds is True):
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

				if (self.read_before_ds is True):			
					j_step = aux_time_j - id_ini_month
					self.j_step = int(j_step)

				# modified to read giraf, MONTHLY -----------------------
				if (self.read_before_ds is True) and (self.file_format == 3):
					if j_step == 0:
						self.read_before_ds = True

				#---------------------------------------------------------
				if (self.read_before_ds is False) and (self.file_format == 2):
					if aux_time_j == 0:
						self.j_step = 0

					j_step = self.j_step

				# THIS IS A PARTIAL SOLUTION, SO IT WILL BE MODIFIED LATER
				# this will allow the model to read datasets fstarting from any time step
				if (self.read_before_ds is True) and (self.file_format == 1):
					self.step_0 = aux_time_j + 0

				if (self.read_before_ds is False) and (self.file_format == 1):
					j_step = self.j_step

				# THIS IS A PARTIAL SOLUTION TO READ STORM, SO IT WILL BE MODIFIED LATER
				if (self.read_before_ds is True) and (self.file_format == 5):
					self.step_0 = aux_time_j + 0

				if (self.read_before_ds is False) and (self.file_format == 5):
					j_step = self.j_step


				#print(idate_ds, aux_time_j, j_step, self.j_step, self.file_format, id_ini_month)
				#if field == 'pet':
				#	keys = ['longitude', 'latitude']
				#else:
				#keys = ['lon', 'lat']

				# Read data at the begining of the simulation or if a new dataset starts
				if (self.read_before_ds is True) or (j_step == 0):

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
					elif self.file_format == 4:
						# read daily values
						if month < 10:
							str_month = '0'+str(month)
						else:
							str_month = str(month)
						if day < 10:
							str_day = '0'+str(day)
						else:
							str_day = str(day)
						# Names should include YYYY for year  MM for months, and DD for days
						# in order to read daily files
						fname_ds = fname_ds.replace("YYYY", str(idate_ds.year))
						fname_ds = fname_ds.replace("MM", str_month)
						fname_ds = fname_ds.replace("DD", str_day)

					# read dataset
					if self.file_format == 5:
						groupds = list(Dataset(fname_ds).groups.keys())[0]
						meta = xr.open_dataset(fname_ds)
						meta = meta.assign_coords({
						    'y': meta['projection_y_coordinate'].load(),
						    'x': meta['projection_x_coordinate'].load()
						    })
						#mask = meta['regions']
						#mask.plot(cmap='turbo', levels=5)

						#self.ds = xr.open_dataset(fname_ds, group=str(idate_ds.year))
						self.ds = xr.open_dataset(fname_ds, group=groupds)
						# Replace all years with 2025
						new_time = self.ds["time"].dt.strftime(str(idate_ds.year)+"-%m-%d %H:%M:%S")
						self.ds = self.ds.assign_coords(time=pd.to_datetime(new_time))
						#delta_year = int(groupds) - idate_ds.year
						#new_time = self.ds["time"] + pd.DateOffset(years=-delta_year)
						#new_time = self.ds.time + pd.Timedelta(years=delta_year)  # Shift by 5 years
						#self.ds = self.ds.sum(dim=('time'), skipna=True)
						# Assign the new time dimension to the dataset
						#self.ds['time'] = new_time
						self.ds = self.ds.assign_coords({
						    'y': meta['projection_y_coordinate'].load(),
						    'x': meta['projection_x_coordinate'].load()
						    })
						del(meta)
						#print(self.ds)

					else:
						if self.noskip is False:
							if not os.path.exists(fname_ds):
								self.ds = None
							else:
								self.ds = xr.open_dataset(fname_ds)
						else:
							self.ds = xr.open_dataset(fname_ds)

					if self.ds is not None:
						# check if dimension names are compatible with DRYP names
						if 'latitude' in list(self.ds.coords):
							self.ds = self.ds.rename({'longitude':'lon', 'latitude':'lat'})
						if 'X' in list(self.ds.coords):
							self.ds = self.ds.rename({'X':'lon', 'Y':'lat'})
						if 'x' in list(self.ds.coords):
							self.ds = self.ds.rename({'x':'lon', 'y':'lat'})
						try:
							self.ds = self.ds.rename({"Time (in Days)":"time"})
							#print(self.ds)
						except:
							a=1
							#print(self.ds)
						try:
							self.ds = self.ds.rename({"array_index":"time"})
							#print(self.ds)
						except:
							a=1
						
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

						# temporal resampling
						if self.dt_ds != self.dt:
							if self.step_func is False:
								# temporal resampling
								self.ds = self.ds.resample(time=self.freq_dt).sum()
							#print("resample", self.ds)		

						# reproject dataset
						if self.reproject_ds is True:
							self.ds = reproject_dataset(self.ds, self.proj, self.proj_model)#, keys)
							#print("repro", self.ds, self.proj, self.proj_model)
						# flag to no read every time the whole dataset
					self.read_before_ds = False

				#print(self.ds, self.dt_ds, self.dt)
				# set index
				iindex = j_step-self.step_0
				#print(iindex,j_step,self.step_0)

				if self.ds is not None:
					# select data step
					if self.step_func is False:
						ds = self.ds.isel(time=[iindex])
					else:
						if self.dt_ds > 1440:
							#print(month)
							ds = self.ds.isel(time=[month-1])
						else:
							ds = self.ds.isel(time=[day])
					#print(ds)
					if self.interpolate_ds is True:
						# Spatial interpolation
						#ds = self.ds.isel(time=[j_step-self.step_0]).interp(
						ds = ds.interp(
							lat=self.lat, lon=self.lon,
							method="linear")
						#print("interpolate", ds)
					#else:
					#	ds = self.ds.isel(time=[j_step-self.step_0])
					#print(ds)
					# get data at time step t
					#ds[field].plot(x='lon', y='lat')
					#plt.imshow(np.array(ds.variables[field][0][:]))
					#plt.savefig('precipitation'+field+str(self.j_step)+'.png')
					#plt.close()
					data = np.array(ds.variables[field][0][:]).flatten()
					#print(np.where(np.isnan(data)))
				else:
					data = None	
				self.j_step += 1
			else:
				data = None
		else:
			#print(fname_ds)
			# Read time series of precipitation	csv
			if fname_ds is not None:
				if (self.read_before_ds is True) or (j_step == 0):
					if not os.path.exists(fname_ds):
						self.ds = None
					else:
						self.ds = pd.read_csv(fname_ds)
					#print(pd.read_csv(fname_ds))
					if self.ds is not None:
						#self.ds = pd.read_csv(fname_ds)
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
						self.read_before_ds = False

				if self.ds is not None:
					data = np.full(self.grid_length, self.ds[field].iloc[j_step])
			else:
				data = None
		
		return data
		
# new read data for savi
class read_dataset(object):
	"""Read input datasets from different sequential files
	Parameters
	Returns
	
	"""
	def __init__(self, dt, dt_ds, ini_date, end_date, file_format,
		reproject, interpolate, grid_length, noskip=True):
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
		self.noskip = noskip
	
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
		if fname_ds is not None:
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
		else:
			data = None
		
		return data
