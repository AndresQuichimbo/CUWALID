import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
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
			"apd" :"Total abstractions - ponds"
			}

units_var = {'pre':'mm/dt', 'aet':'mm/dt', 'pet':'mm/dt', 'inf':'mm/dt',
			'tls':'mm/dt', 'fch':'mm/dt', 'ssz':'m3/dt', 'rch':'mm/dt',
			'wte':'m', 'egw':'mm/dt', 'run':'mm/dt', 'gdh':'m3/dt',
			'tht':'m3/m3', 'twsc':'mm', 'dis':'m3/dt',
			"vpd" : "m3",
			"epd" : "m3/dt",
			"apd" :"m3/dt"
			}

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


def plot_avg_var(fname, fname_out=None, fields=None, delta_t='D', max_subplots=None):
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
	delta_t: time interval for resampling (default is daily 'D')
	
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
	>>> import cuwalid.tools.DRYP_plot_tools as plttools
	>>> plttools.plot_avg_var('data.csv', 'output_plot.png', delta_t='M')
	
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
	
def plot_point_var(fname, fields=None, fname_out=None, delta_t='D', mean=True, max_nfields=None):
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
	Returns:
	--------
		ax: axes of the plot
	Example:
	-------
	>>> import matplotlib.pyplot as plt
	>>> import pandas as pd
	>>> import numpy as np
	>>> import os
	>>> import xarray as xr
	>>> import geopandas as gpd
	>>> import cuwalid.tools.DRYP_plot_tools as plttools
	>>> plttools.plot_point_var('data.csv', 'output_plot.png', delta_t='M')
	

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
		
	fig.tight_layout()
	
	
	if fname_out is not None:
		plt.savefig(fname_out,dpi = 300)
	
	return ax

def plot_profile(dataset, axis=0, time=[0], n=1, dem=None, bathymetry=None, title=None, fname_out=None):
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
	
	Returns:
	--------
		ax: axes of the plot
	
	Example:
	-------
	>>> import matplotlib.pyplot as plt
	>>> import pandas as pd
	>>> import numpy as np
	>>> import os
	>>> import xarray as xr
	>>> import geopandas as gpd
	>>> import cuwalid.tools.DRYP_plot_tools as plttools
	>>> plttools.plot_profile(dataset, axis=0, time=[0], n=1, dem=None, bathymetry=None, title=None)

	"""
	
	fig, ax = plt.subplots()#3, 5, sharex=True, sharey=True)
	fig.set_size_inches(10., 7.2)

	for kk in time:
		if axis == 0:
			ax.plot(dataset['lat'].values, dataset.isel(time=kk, lon=[n]).values.reshape(-1),
				'.-', label=str(kk)
				)
		else:
			ax.plot(dataset['lon'].values, dataset.isel(time=kk, lat=[n]).values.reshape(-1),
				'.-', label=str(kk)
				)

	if dem is not None:
		dem[dem < 0] = np.nan
	if bathymetry is not None:
		bathymetry[bathymetry < 0] = np.nan

	if axis == 0:
		if dem is not None:
			ax.plot(dataset['lat'], dem[:, n][::-1], 'k')
			
		if bathymetry is not None:
			ax.plot(dataset['lat'], bathymetry[:, n][::-1], 'gray')
		
		ax.set_xlabel('Latitude')

	else:
		if dem is not None:
			ax.plot(dataset['lon'], dem[-n], 'k')
		if bathymetry is not None:
			ax.plot(dataset['lon'], bathymetry[-n], 'gray')
		ax.set_xlabel('Longitude')
	
	if title is None:
		var_name = dataset.name
		try:
			ax.set_title('Profile of ' + long_name[var_name])# +
			ax.set_ylabel(long_name[var_name]+
						  " ["+units_var[var_name]+"]")
		except:
			pass
	else:
		ax.set_ylabel(title)
		ax.set_title('Profile of ' + title)
			
	plt.grid(True, which='both')
	plt.legend(frameon=False)

	if fname_out is not None:
		plt.savefig(fname_out,dpi = 300)

	return ax