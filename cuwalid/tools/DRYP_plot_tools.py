import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import os
import xarray as xr
import geopandas as gpd

long_name = {'pre':'precipitation', 'aet':'actual evapotranspiration',
			 'pet':'potential evapotranspiration',
			 'inf':'infiltration', 'tls':'transmission losses',
			 'fch':'focused recharge',
			 'ssz':'surface storage', 'rch':'total groundwater recharge',
			'wte':'water table elevation', 'egw':'groundwater evaporation',
			'run':'runoff',
			'gdh':'groundwater discharge',
			'tht':'soil moisture', 'twsc':'water storage change',
			'dis':'discharge',
			"vpd" : "Total volume of water available - ponds",
			"epd" : "evaporation - ponds",
			"apd" :"Total abstractions - ponds",
			"chb" : "flux constant head boundary",
			}

units_var = {'pre':'mm/dt', 'aet':'mm/dt', 'pet':'mm/dt', 'inf':'mm/dt',
			'tls':'mm/dt', 'fch':'mm/dt', 'ssz':'m3/dt', 'rch':'mm/dt',
			'wte':'m', 'egw':'mm/dt', 'run':'mm/dt', 'gdh':'m3/dt',
			'tht':'m3/m3', 'twsc':'mm', 'dis':'m3/dt',
			"vpd" : "m3",
			"epd" : "m3/dt",
			"apd" :"m3/dt",
			"chb" : "m3/dt",
			"sz" : "m3",
			}

name_axis = {0:'Y', 1: "X", 'time':'Time'}

def read_json_file(json_file):
	"""Read a JSON file and return the data as a dictionary.
	Parameters:
	-----------
	json_file: str
		path to the JSON file
	Returns:
	--------
		data: dict
			data from the JSON file as a dictionary
	Example:
	>>> json_file = "path/to/json_file.json"
	>>> data = read_json_file(json_file)
	"""
	with open(json_file, 'r') as file:
		data = json.load(file)
	return data

def split_text(text, max_len=1):
	"""Split text into lines of a maximum length.
	Parameters:
	-----------
	text: str
		input text string
	max_len: int
		maximum length of each line (default is 1)
	Returns:
	--------
		text: str
			text string with lines split at maximum length
	Example:
	>>> text = "This is a long text that needs to be split into lines."
	>>> print(split_text(text, max_len=2))
	"""
	words = text.split()
	# Group words into lines (each line containing up to two words)
	lines = [" ".join(words[i:i+max_len]) for i in range(0, len(words), max_len)]
	text = "\n".join(lines)
	return text


def plot_avg_var(fname, fname_out=None, fields=None, delta_t='1D', ax=None,
				 date_start=None, date_end=None, max_subplots=None):
	"""Plot average variables from a csv file.
	
	Parameters:
	-----------
	fname: str
		file name of the csv file
	fname_out: str
		output file name for the plot (optional)
	fields: list
		list of fields to plot (optional)
		if None, all fields will be plotted
	delta_t:
		time interval for resampling (default is daily 'D')
	date_start: str
		start date in the format 'YYYY-MM-DD' (optional)
	date_end: str
		end date in the format 'YYYY-MM-DD' (optional)
	max_subplots: int
		maximum number of subplots to create (optional)
		only the first max_subplots fields will be plotted

	Returns:
	--------
		ax: axes of the plot

	Example:
	
	>>> import matplotlib.pyplot as plt
	>>> import pandas as pd
	>>> import numpy as np
	>>> import os
	>>> import xarray as xr
	>>> import geopandas as gpd
	>>> import cuwalid.tools.DRYP_plot_tools as plotcwld
	>>> plotcwld.plot_avg_var('data.csv', 'output_plot.png', delta_t='M')
	
	"""
	# read the csv file and convert the date column to datetime
	df = pd.read_csv(fname)

	if fields is None:
		fields = list(df)
		try:
			fields.remove('Date')
		except:
			print('No Date column in the file')
	
	# change time to datetime format
	df["Date"] = pd.to_datetime(df['Date'])		
	df.index = pd.DatetimeIndex(df['Date'])

	# check if the date_start and date_end are provided
	df = slice_dataframe(df, date_start, date_end)
	# resample the data to the specified time interval
	# and calculate the mean for each field
	try:
		df2 = df.resample(delta_t).mean().reset_index()		
		df = df.resample(delta_t).sum().reset_index()
	except:
		df2 = df.resample(delta_t).mean(numeric_only=True).reset_index()	
		df = df.resample(delta_t).sum(numeric_only=True).reset_index()	

	# check if the number of subplots is less than the number of fields
	if max_subplots is not None:
		if len(fields) > max_subplots:
			fields = fields[:max_subplots]
	
	# create a figure with subplots for each field
	if ax is None:	
		fig, ax = plt.subplots(len(fields), 1, sharex = True)
		fig.set_size_inches(9, len(fields)*1.25)
	
	for ilabel, iax in zip(fields, fig.axes):
		# plot the data for each field
		iilabel = ilabel.split("_")[0]
		if iilabel == 'tht':			
			iax.plot(df2['Date'], df2[ilabel])				
		else:			
			iax.plot(df['Date'], df[ilabel])
		try:
			iax.set_ylabel(split_text(long_name[iilabel] + " " +
							  "["+units_var[iilabel]+"]", 1))
		except:
			iax.set_ylabel(ilabel)
		
	plt.legend(frameon = False)		
	iax.set_xlabel('Date')
	fig.tight_layout()
	if fname_out is not None:	
		plt.savefig(fname_out,dpi = 300)
	return ax
	
def plot_point_var(fname, fields=None, fname_out=None, delta_t='D',
				   date_start=None, date_end=None, mean=True,
				   max_nfields=None, ax=None):
	"""Plot point variables from a csv file."
	Parameters:
	-----------
	fname: str
		file name of the csv file
	fname_out: str
		output file name for the plot (optional)
	fields: list
		list of fields to plot (optional)
		if None, all fields will be plotted
	delta_t: str
		time interval for resampling (default is daily 'D')
	mean: bool
		if True, plot the mean of the fields (default is True)
	max_nfields: int
		maximum number of fields to plot (optional)
	date_start: str
		start date in the format 'YYYY-MM-DD' (optional)
	date_end: str
		end date in the format 'YYYY-MM-DD' (optional)

	Returns:
	--------
		ax: axes of the plot
	Example:
	--------
	>>> import matplotlib.pyplot as plt
	>>> import pandas as pd
	>>> import numpy as np
	>>> import os
	>>> import xarray as xr
	>>> import geopandas as gpd
	>>> import cuwalid.tools.DRYP_plot_tools as plotcwld
	>>> plotcwld.plot_point_var('data.csv', 'output_plot.png', delta_t='M')
	

	"""	
	df = pd.read_csv(fname)		
	
	if fields is None:
		fields = list(df)
		try:
			fields.remove('Date')
		except:
			print('No Date column in the file')
	
	# check if the number of fields is less than the maximum number of fields
	if max_nfields is not None:
		if len(fields) > max_nfields:
			fields = fields[:max_nfields]
	
	# change time to datetime format
	df["Date"] = pd.to_datetime(df['Date'])		
	df.index = pd.DatetimeIndex(df['Date'])

	# check if the date_start and date_end are provided
	df = slice_dataframe(df, date_start, date_end)
	# resample the data to the specified time interval
	# and calculate the mean for each field
	if mean is True:
		try:
			df = df.resample(delta_t).mean().reset_index()
		except:
			df = df.resample(delta_t).mean(numeric_only=True).reset_index()
	else:
		try:
			df = df.resample(delta_t).sum().reset_index()
		except:
			df = df.resample(delta_t).sum(numeric_only=True).reset_index()
	
	# create a figure with subplots for each field
	if ax is None:
		fig, ax = plt.subplots(1, 1, sharex=True)		
		fig.set_size_inches(8, 2.5)		
	
	for ilabel in fields:
		# plot the data for each field
		try:
			ax.plot(df['Date'], df[ilabel], label=ilabel)
		except:
			pass
		
	plt.legend(frameon=False)		
	
	# add label to the y-axis
	iilabel = ilabel.split("_")[0]

	# check if the label is in the long_name dictionary
	if iilabel in long_name.keys():
		# split the label into multiple lines if it is too long
		ylabel = split_text(long_name[iilabel] + " " +
						  "["+units_var[iilabel]+"]", 1)
	#else:
		# if the label is not in the dictionary, use the label as is
		# split the label into multiple lines if it is too long
		#ylabel = split_text(ilabel, 1)
		# use the label as is
	#	ylabel = ilabel

	ax.set_ylabel(ylabel)
	ax.set_xlabel('Date')
		
	#fig.tight_layout()
	
	
	if fname_out is not None:
		plt.savefig(fname_out,dpi = 300)
	
	return ax

def plot_profile(dataset, axis=0, time=[0], n=1, dem=None, river_bottom=None,
				 bathymetry=None, title=None, fname_out=None, ax=None, plot_step=False):
	"""Plot a profile of the dataset along a specified axis (0 or 1).
	
	Parameters:
	-----------
	dataset: xarray dataset
		dataset to plot
	axis: int
		axis to plot along (0 or 1)
	time: list
		list of time steps to plot (default is [0])
	n: int
		index of the profile to plot (default is 1)
	dem: numpy array
		digital elevation model (optional)
	bathymetry: numpy array
		bathymetry data (optional)
	title: str
		title of the plot (optional)
	fname_out: str
		output file name for the plot (optional)
	ax: matplotlib axes
		axes to plot on (optional)
	
	Returns:
	--------
		ax: axes of the plot
	
	Example:
	--------
	>>> import matplotlib.pyplot as plt
	>>> import numpy as np
	>>> import os
	>>> import xarray as xr
	>>> import cuwalid.tools.DRYP_plot_tools as plotcwld
	>>> import cuwalid.tools.DRYP_pptools as pptools
	>>> import cuwalid.tools.DRYP_rrtools as rrtools
	>>> path_bathymetry = "path_bathymetry.asc"
	>>> path_dem = "path_dem.asc"
	>>> dem = rrtools.open_raster([path_dem)[0]
	>>> bathymetry = rrtools.open_raster(path_bathymetry)[0]
	>>> bathymetry[bathymetry < 0] = np.nan
	>>> fname = 'peth_model_outputs.nc'
	>>> dataset = xr.open_dataset(fname)["wte"]
	>>> plotcwld.plot_profile(dataset, axis=0, time=[0], n=1, dem=None, bathymetry=None, title=None)
	>>> plt.show()
	"""
	
	#check if the axis is valid
	nlat, nlon = dataset['lat'].shape[0], dataset['lon'].shape[0] 

	# check that nlat and nlon are the same as the dem and bathymetry
	if dem is not None:
		nlatr, nlonr = np.shape(dem)
		if nlat != nlatr or nlon != nlonr:
			raise ValueError("The shape of the dem does not match the dataset")
	
	if river_bottom is not None:
		nlatrb, nlonrb = np.shape(river_bottom)
		if nlat != nlatrb or nlon != nlonrb:
			raise ValueError("The shape of the river bottom does not match the dataset")

	if bathymetry is not None:
		nlatb, nlonb = np.shape(bathymetry)
		if nlat != nlatb or nlon != nlonb:
			raise ValueError("The shape of the bathymetry does not match the dataset")

	# check if value of n is valid
	if axis == 0:
		if n < 0 or n >= nlon:
			raise ValueError("The value of n must be between 0 and " + str(nlon-1))
	elif axis == 1:
		if n < 0 or n >= nlat:
			raise ValueError("The value of n must be between 0 and " + str(nlat-1))		

	if ax is None:
		# create a new figure and axes if ax is not provided
		fig, ax = plt.subplots()
		fig.set_size_inches(10., 7.2)
	colors = plt.rcParams['axes.prop_cycle'].by_key()['color']	
	for kk, icolor in zip(time, colors):
		try:
			datelabel = pd.to_datetime(dataset['time'][kk].item()).strftime('%Y-%m-%d')
		except:
			datelabel = str(kk)
		
		if axis == 0: # plot along latitude
			ax.plot(dataset['lat'].values, dataset.isel(time=kk, lon=[n]).values.reshape(-1),
				'.-', label=datelabel, alpha=0.7, color=icolor#label=str(kk)
				)
			if plot_step is True:
				ax.step(dataset['lat'].values, dataset.isel(time=kk, lon=[n]).values.reshape(-1),
					'o--', label=datelabel, alpha=0.4, where='mid', color=icolor#label=str(kk)
				)
		else: # plot along longitude
			ax.plot(dataset['lon'].values, dataset.isel(time=kk, lat=[n]).values.reshape(-1),
				'.-', label=datelabel, alpha=0.7, color=icolor#label=str(kk)
				)
			if plot_step is True:
				ax.step(dataset['lon'].values, dataset.isel(time=kk, lat=[n]).values.reshape(-1),
					'o--', label=datelabel, alpha=0.4, where='mid', color=icolor#label=str(kk)
					)

	if dem is not None:
		dem[dem < 0] = np.nan
	if bathymetry is not None:
		bathymetry[bathymetry < 0] = np.nan
	if river_bottom is not None:
		river_bottom[river_bottom < 0] = np.nan
	# check if the axis is 0 or 1
	# if axis is 0, plot the profile along the latitude
	if axis == 0: # plot along latitude
		if dem is not None: #acces has to be flipped
			ax.plot(dataset['lat'], dem[:, n][::-1], 'gray', ls='-', alpha=0.7)
			
		if bathymetry is not None:
			ax.plot(dataset['lat'], bathymetry[:, n][::-1], 'k', alpha=0.7)

		if river_bottom is not None:
			ax.plot(dataset['lat'], river_bottom[:, n][::-1], 'grey', alpha=0.7)
		
		ax.set_xlabel('Latitude')

	else:
		if dem is not None:
			ax.plot(dataset['lon'], dem[n], 'gray', ls='-', alpha=0.7)
		if bathymetry is not None:
			ax.plot(dataset['lon'], bathymetry[n], 'k', alpha=0.7)
		if river_bottom is not None:
			ax.plot(dataset['lon'], river_bottom[n], 'grey', alpha=0.7)
		ax.set_xlabel('Longitude')
	
	# set the title of the plot
	# check if the title is None or not
	if title is None:
		var_name = dataset.name
		try:
			ax.set_title('Profile of ' + long_name[var_name]+
						  " along axis "+name_axis[axis]+
						  " at index "+str(n))
			ax.set_ylabel(long_name[var_name]+
						  " ["+units_var[var_name]+"]")
		except:
			pass
	else:
		ax.set_ylabel(title)
		ax.set_title('Profile of ' + title)
			
	#plt.grid(True, which='both')
	plt.legend(frameon=False)

	if fname_out is not None:
		plt.savefig(fname_out,dpi = 300)

	return ax

def slice_dataframe(df, date_start, date_end):
	"""Slice a dataframe along a time axes.

	Parameters:
	-----------	
	df: pandas DataFrame
		dataframe to slice
	date_start: str
		start date in the format 'YYYY-MM-DD'
	date_end: str
		end date in the format 'YYYY-MM-DD'
	Returns:
	--------
		sliced_df: pandas DataFrame
			sliced dataframe with the specified date range
	Example:
	>>> import pandas as pd
	>>> import cuwalid.tools.DRYP_plot_tools as plotcwld
	>>> data = {'Date': ['2023-01-01', '2023-01-02', '2023-01-03'],
	...         'Value': [1, 2, 3]}
	>>> df = pd.DataFrame(data)
	>>> date_start = '2023-01-01'
	>>> date_end = '2023-01-02'
	>>> sliced_df = plotcwld.slice_dataframe(df, date_start, date_end)
	>>> print(sliced_df)
	        Date  Value
	0  2023-01-01      1
	1  2023-01-02      2
	"""
	if not isinstance(df, pd.DataFrame):
		raise ValueError("Input must be a pandas DataFrame")
	if 'Date' not in df.columns:
		raise ValueError("DataFrame must contain a 'Date' column")
	# Convert 'Date' column to datetime if it is not already
	df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
#	if not isinstance(date_start, str) or not isinstance(date_end, str):
#		raise ValueError("Start and end dates must be strings in 'YYYY-MM-DD' format")
#	else:
	if date_start is not None and date_end is not None:
		df = df[(df['Date'] >= date_start) & (df['Date'] <= date_end)]
	return df#.reset_index(drop=True)