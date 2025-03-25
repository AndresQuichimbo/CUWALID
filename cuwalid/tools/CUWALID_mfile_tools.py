import datetime
import os
import numpy as np
import pandas as pd
import xarray as xr
import rasterio
import matplotlib.pyplot as plt
import rioxarray
from itertools import compress
import operator
import calendar
import cuwalid.tools.DRYP_pptools as pptools

def read_dataset(fname, var_name='tht'):
	# Open the first netCDF file
	# output dataset
	data = xr.open_dataset(fname)
	#print(data)
	data = data[var_name]
	return data
	
def resample_dataset(data, mean=True, delt='Y', extremes=False):
	# calculate climatological mean
	# output an array
	if extremes is False:
		if mean is True:
			data = data.resample(time=delt).mean()
		else:
			data = data.resample(time=delt).sum()
	else:
		if extremes == "min":
			data = data.resample(time=delt).min()
		elif extremes == "max":
			data = data.resample(time=delt).max()
		else:
			print("extremes must be False, max, or min")
	return data

def season_name_to_number(season):
	"""
    Converts a string representing a season to a list of numbers indicating corresponding months.

    Parameters
    ----------
    season : str or list or int
        The season represented by three capital letters (e.g., "OND") or a list of month numbers.

    Returns
    -------
    list
        A list of integers representing the months for the given season. If the input is already 
        a list of months, it is returned as is. If the input is not recognized, it returns 
        the input wrapped in a list.

    Notes
    -----
    Supported season codes:
    - "MAM" : March, April, May [3, 4, 5]
    - "OND" : October, November, December [10, 11, 12]
    - "JJS" : June, July, August [6, 7, 8]
    - "JF"  : January, February [1, 2]
    - "JJSA": June, July, August, September [6, 7, 8, 9]

    If the input is not a string or a list, the function wraps the input in a list.

    Examples
    --------
    >>> season_name_to_number("MAM")
    [3, 4, 5]

    >>> season_name_to_number([1, 2, 3])
    [1, 2, 3]

    >>> season_name_to_number(2)
    [2]
    """

	if isinstance(season, str):
		if season == "MAM":
			season = [3,4,5]
		elif season == "OND":
			season = [10,11,12]
		elif season == "JJS":
			season = [6,7,8]
		elif season == "JF":
			season = [1,2]
		elif season == "JJSA":
			season = [6,7,8,9]
		return season
	else:
		if isinstance(season, list):
			return season
		else:
			return [season]

def get_dates_season(season, year):
	imonths = season_name_to_number(season)
	last_day = calendar.monthrange(year, imonths[-1])[1]
	start_date = str(year) + " " + str(imonths[0]) + " " + str(1)
	end_date = str(year) + " " + str(imonths[-1]) + " " + str(last_day)
	return start_date, end_date

def date_to_day_of_year(date_str):
    # Convert the date string into a datetime object
    date = datetime.datetime.strptime(date_str, "%Y %m %d")
    # Return the day of the year (1 for Jan 1, 365 for Dec 31 in non-leap years)
    return date.timetuple().tm_yday

def concatenate_netCDF(fname_list, var, agg="M", dim='time', season=None):
	""" Get a xarray from a list of netcdf files
	
	Parameters
	----------
	fnames : list of paths
		list of file names of netcdf file
	var : str
		variable name
	agg : str
		temporal resampling (default monthly)
	season : str
		name of the season, e.g MAM
	
	Returns
	-------
	dataconcatenat : xarray
		xarray with all values 
	"""
	
	concat_first_read = True
	for ifname in fname_list:
		
		# read dataset
		mean = False
		if (var == 'tht') or (var == 'wte'):
			mean = True
		
		# check if is the riparian area
		if (var == 'fch') or (var == 'tls'):# or (var == 'flood'):
			ifname = ifname.split('.')[0]+'rp.nc'
		if (var == 'flood'):
			ifname = ifname.split('.')[0]+'max.nc'
		
		# read dataset
		if (var == 'flood'):
			data = read_dataset(ifname, var_name="dis")
		else:
			data = read_dataset(ifname, var_name=var)
		
		# select season
		if season is not None:
			data = get_season_dataset(data, season)
		# sclice dataset
		#data = slice_dataset_time(data)
		
		# resample dataset
		data = resample_dataset(data, mean=mean, delt=agg)
		
		# accummulate dataset, just in case of TWSA
		#if var == 'twsc':
		#	data = data.cumsum(dim=dim)
		
		# concatenate all datasets
		if concat_first_read is True:
			dataconcatenat = data.copy()
			concat_first_read = False
		else:
			dataconcatenat = xr.concat([dataconcatenat, data], dim=dim)
	
	return dataconcatenat

def get_season_dataset(data, season):
	# get seasson
	return data.where(data.time.dt.month.isin(season_name_to_number(season)))

def create_binary_dataarray(dataset):
	"""Create a binary dataset by changing positive values
	to 1 and negative values to 0
	
	Parameters
	----------
	dataset : dataarray
	
	Returns:
	dataset : dataarray
		binary dataset
	"""
	dataset = dataset.where(dataset >= 0, 0)
	dataset = dataset.where(dataset == 0, 1)
	return dataset
	
def get_tercile_probabilities(dataset, thresholds, dim="time"):
	"""Get tercile probabilities from an ensamble dataarray
	this function count the number of values above/within/below
	the thresholds and return the probabilities.
	WARNING: threshold values need to be of lengh 2 
	
	Parameters
	----------
	dataset : dataarray
		ensamble of values to evaluate
	thresholds : numpy array
		threshold balues to bin dataset, it must have a same
		grid size of the dataset
	dim: str
		axis at which it will be evalueated (default time)
		
	Returns
	-------
	terciles: dataarray
		tercile dataset, binned dataset
	"""
	# get lenght of ensamble
	nsim = len(dataset)
	
	# terciles below normal values
	BN = create_binary_dataarray(
			thresholds[0] - dataset
			)
	
	# tercile between normal values
	NN = (create_binary_dataarray(
			thresholds[1] - dataset)*
		create_binary_dataarray(
			dataset - thresholds[0])
			)
	#print(NN)
	
	# tercile above normal values
	AN = create_binary_dataarray(
			dataset - thresholds[1]
			)
	
	# Define the dimensions and coordinates
	dims = AN.sum(dim=dim).dims
	coords = AN.sum(dim=dim).coords	
	
	# Step 3: Create the xarray dataset
	terciles = xr.Dataset({
		'AN': (dims, AN.sum(dim=dim).values),
		'NN': (dims, NN.sum(dim=dim).values),
		'BN': (dims, BN.sum(dim=dim).values),
		},
		coords=coords
		)
	
	return terciles*1/nsim

def get_percentile_probabilities(dataset, thresholds, dim="time"):
	"""Get tercile probabilities from an ensamble dataarray
	this function count the number of values above/within/below
	the thresholds and return the probabilities.
	WARNING: threshold values need to be of lengh 2 
	
	Parameters
	----------
	dataset : dataarray
		ensamble of values to evaluate
	thresholds : numpy array
		threshold balues to bin dataset, it must have a same
		grid size of the dataset
	dim: str
		axis at which it will be evalueated (default time)
		
	Returns
	-------
	terciles: dataarray
		tercile dataset, binned dataset
	"""
	# get lenght of ensamble
	nsim = len(dataset)
	
	# terciles below normal values
	BN = create_binary_dataarray(
			thresholds[0] - dataset
			)
		
	# tercile above normal values
	AN = create_binary_dataarray(
			dataset - thresholds[0]
			)
	
	# Define the dimensions and coordinates
	dims = AN.sum(dim=dim).dims
	coords = AN.sum(dim=dim).coords	
	
	# Step 3: Create the xarray dataset
	percentiles = xr.Dataset({
		'AN': (dims, AN.sum(dim=dim).values),
		#'BN': (dims, nsim - BN.sum(dim=dim).values),
		'BN': (dims, BN.sum(dim=dim).values),
		},
		coords=coords
		)
	
	return percentiles*1/nsim

def get_tercile_probabilities_from_netcdf(path_data, path_threshold, var="dis",
			season=None, extremes=False, idtercile=[0, 2]):
	"""This function read a netcdf file of historical values and calculates
	the probabilities from historical simulations, it selects the seasons if
	season is not False, and also select the maximum or minimum values
	if extremes is activated

	Parameters
	----------
	
	path_data : str
		path of the histrical values
	path_threshold: str
		path of thresholds/terciles
	var : str
		variable selected from the netcdf file to process
	season : str or None
		select only the months that are specified on season (e.g. OND)
	extremes : str or None
		if selected, min or max values will be extracted before tercile apply
	idterciles : list
		id of the lower and upper tercile, respectively
	Returns:
	--------
	tercile : Dataarray
		dataset of tercile probabilities
	"""
	# read dataset (choose year and variable)
	ds = read_dataset(path_data, var_name=var)
	
	# aggregate data to yearly values, if season is provided, select season first
	if season is not None:
		ds = resample_dataset(
				get_season_dataset(ds, season),
				extremes=extremes,
				)
	else:
		ds = resample_dataset(ds, extremes=extremes)
		
	# read tercile thresholds for the selected variable and year
	ds_thrshold = read_dataset(path_threshold, var_name=var).values
	threshold = [ds_thrshold[idtercile[0]], ds_thrshold[idtercile[1]]]
	
	# calculate probability forecast
	tercile = get_tercile_probabilities(ds, threshold, dim="time")
	return tercile

def get_tercile_probabilities_from_ensamble_netcdf(path_data, path_threshold, var="dis",
			season=None, axis="sim", idtercile=[0, 2]):
	"""This function read a netcdf file of ensambles and calculate the probabilities
	of 
	"""
	# read dataset (choose year and variable)
	ds = read_dataset(path_data, var_name=var)
		
	# read tercile thresholds for the selected variable and year
	ds_thrshold = read_dataset(path_threshold, var_name=var).values
	threshold = [ds_thrshold[idtercile[0]], ds_thrshold[idtercile[1]]]
	
	# calculate probability forecast
	tercile = get_tercile_probabilities(ds, threshold, dim=axis)
	return tercile

def get_percentiles_probabilities_from_netcdf(path_data, path_threshold, var="dis", season=None):
	# read dataset (choose year and variable)
	ds = read_dataset(path_data, var_name=var)
	
	# aggregate data to yearly values, if season is provided, select season first
	if season is not None:
		ds = resample_dataset(
				get_season_dataset(ds, season),
				)
	else:
		ds = resample_dataset(ds)
		
	# read tercile thresholds for the selected variable and year
	ds_thrshold = read_dataset(path_threshold, var_name=var).values
	threshold = [ds_thrshold[1]]
	
	# calculate probability forecast
	percentile = get_percentile_probabilities(ds, threshold, dim="time")
	
	return percentile
	
def reproject_dataset(data, oldPP, newPP):
	"""Transform projection system
	oldPP and newPP have to be defined first
	
	Parameters
	----------
	Data:	Dataset
	
	Returns
	-------
	Data:	Dataset
	"""
	# check if projection is in ERSG format
	if len(newPP) > 11:
		newPP = rasterio.crs.CRS.from_string(newPP)
	
	# reprojec dataset
	data = data.rename({'lon': 'x', 'lat': 'y'})  # new method
	data = data.rio.write_crs(oldPP) # write crs
	data = data.rio.reproject(newPP) # reproject the file
	data = data.rename({'x': 'lon', 'y': 'lat'})  # new method
	
	return data

def clip_dataset_by_region(ds, region):
	# Clip the data model
	ds_clipped = ds.rio.clip(region.geometry.values, region.crs)
	return ds_clipped

def extract_mdataset(fname_list, region, clip_region=False,
	dataPP=None, maskPP=None, bands=["pre", "aet", "pet", "rch"],
	fname_out=None, save=False):
	"""This function clip netcdf files by region, projection should
	match WGS84, otherwise it will raise an error.
	
	Parameters
	----------
	netcdf_path : str
		list of paths
	region : geodataframe
		name of variable to process
	region_clip: bool
		make values outside the region NaN, default true

	Returns
	-------
	dataset : xarray dataset
		concatenated datasets

	"""
	first_read = True
	for ifname in fname_list:
		# Check if input file exist
		if os.path.exists(ifname):
			# read dataset and calculate the correlation
			pptools.extract_dataset(ifname, region, clip_region=clip_region,
				dataPP=dataPP, maskPP=maskPP,
				bands=bands, save=save,
				fname_out=fname_out
				)


def extract_dataset(netcdf_path, region, clip_region=True,
	dataPP=None, maskPP=None, bands=["AN", "NN", "BN"]):
	"""This function clip netcdf files by region, projection should
	match WGS84, otherwise it will raise an error.
	
	Parameters
	----------
	netcdf_path : str
		list of paths
	region : geodataframe
		name of variable to process
	region_clip: bool
		make values outside the region NaN, default true

	Returns
	-------
	dataset : xarray dataset
		concatenated datasets

	"""
	# =========================================================
	# DO NOT CHANGE FROM THIS LINE
	# =========================================================
	# SPECIFY projection
	# define new projection (output) #!with.PYPROJ.library
	newPP, oldPP = maskPP, dataPP
	if dataPP is None:
		oldPP = rasterio.crs.CRS.from_string(
		"+proj=laea +lat_0=5 +lon_0=20 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
		)
	if maskPP is None:
		# define current projection (input)
		newPP = 'EPSG:4326'
		
	# get bounding boxfrom shapefile
	bbox = region.total_bounds
	
	# create new dataset by extracting the specified area/extend
	first_read = True
	for ivar in bands:
		# Open dataset of model outputs
		data = read_dataset(netcdf_path, var_name=ivar)
		
		# reproject estimated probabilistic forecasting
		data = reproject_dataset(data, oldPP, newPP)
		
		# clip area
		if clip_region is True:
			region_ds = clip_dataset_by_region(data, region)
		else:
			region_ds = data.sel(
				lat=slice(bbox[3], bbox[1]),
				lon=slice(bbox[0], bbox[2])
				)
		
		if first_read is True:
			dataset = region_ds.copy()
			first_read = False
		else:
			dataset = xr.merge([dataset, region_ds])
	
	return dataset
	
def get_ensamble_from_netcdf_list(fname_list, var_name, mean=True,
								delta=None, season=None,
								fname_output=None):
	"""This function read a list of netcdf paths and return a dataset
	or netCDF file containing all concatenated netCDFs
	
	Parameters
	----------
	fname_list : list
		list of paths
	var_name : str
		name of variable to process
	mean : bool
	
	delta : str
		time step for aggregation, default None
	fname_output : str
		file path of output file, default is None so no file is stored
	
	Returns
	-------
	dataset : xarray dataset
		concatenated datasets
	
	"""

	first_read = True
	for ifname in fname_list:
		# Check if input file exist
		if os.path.exists(ifname):
			# read dataset and calculate the correlation
			idata = read_dataset(ifname, var_name=var_name)
			#idata = slice_dataset_time(idata)
			
			# if seasonal average, select months
			if season is not None:
				idata = idata.where(idata.time.dt.month.isin(
						season_name_to_number(season))
						)
			
			if delta is not None:
				# calculate annual average to reduce the use of memory
				idata = resample_dataset(idata, mean=mean, delt=delta)
			
			if mean is True:
				idata = idata.mean(dim='time')
			else:
				idata = idata.sum(dim='time')
	
		else:
			idata = idata*np.nan
		
		if first_read is True:
			dataset = idata.copy()
			first_read = False
		else:
			dataset = xr.concat([dataset, idata], 'sim')

	# save dataset or return dataset
	if fname_output is not None:
		save_xarray_dataset_as_netcdf(fname_output, dataset, [var_name])
		return None
	else:
		return dataset

def get_postprocessed_hydro_variables_mfiles(fname, field=["wrsi", "aet"]):#, "tht"]):
	"""Function for post processing hydrological variables such as WRSI"""
	for ifield in field:
		
		for ifname in fname:
			# test if file exist
			if os.path.exists(ifname):
				if ifield == "wrsi":
					# Calculate WRSI 
					data = read_dataset(ifname, "aet")/read_dataset(ifname, "pet")
					data = data.rename("wrsi")
				elif ifield == "aet":
					# Calculate total evaporation
					data = read_dataset(ifname, "aet") + read_dataset(ifname, "egw")
					data = data.rename("aet")
				#elif ifield == "tht":
				#	data = pptools.calculate_saturation_from_netCDF()

				# Define the path for the yearly NetCDF file
				fname_output = ifname.split('.')[0]+'_'+ifield+'.nc'

				# Group by year and create a new dataset for each year

				# loop over years
				data.to_netcdf(fname_output)
			else:
				print(ifname+" File does not found, skip this file from the analysis")

def get_postprocessed_storage_mfiles(fname_list,path_surface, path_Droot, path_theta_sat, path_Sy,
								  path_bathymetry=None, path_bottom=None,
								  start_time=None, end_time=None, fname_out=None,
								  anomalies=True):
	"""Get storage from a list of modet simulation files,
	only valid for yearly netcdf files.
	When seasonal average is set, the calucation will aggregate annually
	before the average is calculated.
	When accumulation is active, the temporal aggregation is done at the
	end othe concatenation.
	
	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	path_surface :	str
		file name of raster surface
	path_surface :	str
		file name of raster surface
	path_bathymetry :	str
		file name of raster surface
	path_bottom :	str
		file name of raster surface
	path_Droot :	str
		file name of raster surface
	path_theta_sat :	str
		file name of raster surface
	path_Sy :	str
		file name of raster surface
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".
	
	Returns
	-------
	data : xarray dataset
		containing all calculated values
	"""
	for ifname in fname_list:
		# test if file exist
		if os.path.exists(ifname):
			pptools.calculate_storage_from_files(ifname, path_surface,
								path_Droot, path_theta_sat, path_Sy,
								path_bathymetry=path_bathymetry, path_bottom=path_bottom,
								start_time=None, end_time=None, fname_out=None,
								anomalies=anomalies)
		else:
			print(ifname+" File does not found, skip this file from the analysis")

def get_postprocessed_saturation_mfiles(fname_list, path_theta_sat, path_theta_wp,
								  path_bathymetry=None, path_bottom=None,
								  start_time=None, end_time=None, fname_out=None,
								  anomalies=True):
	"""Get saturation from a list of modet simulation files,
	
	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	path_theta_sat :	str
		file name of raster water content as saturation
	path_theta_wp :	str
		file name of raster water content at wilting point
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".
	
	Returns
	-------
	data : xarray dataset
		containing all calculated values
	"""
	for ifname in fname_list:
		# test if file exist
		if os.path.exists(ifname):
			pptools.calculate_saturation_from_netCDF(ifname, path_theta_wp,
									path_theta_sat, fname_out=None,
									var_name="tht")
		else:
			print(ifname+" File does not found, skip this file from the analysis")

def save_xarray_dataset_as_netcdf(fname, data, var_name):
	# data has to be in the same dimentions
	# Create a xarray DataArray
	#ds = xr.DataArray(data, coords={"time": time}, dims=["time", "lon"])

	# Set the compression format
	encoding = {}
	for ivar in var_name:
		encoding.update({ivar: {'zlib': True, 'complevel': 9}})

	# Save the dataset to a netcdf file
	data.to_netcdf(fname, encoding=encoding)
	
	#return
def slice_dataset_time(dataset, start_time="2000-01-01", end_time="2023-01-01"):
	# Slice the dataset between two dates
	dataset = dataset.sel(time=slice(start_time, end_time))
	return dataset

def merge_xarray_dataset(dataset1, dataset2):
	return xr.merge([dataset1, dataset2])
	

def get_average_from_list(fname_list, var="pre", mean=True, season=None,
				accum=False, delta=None):
	"""Get average values from a list of modet simulation files,
	only valid for yearly netcdf files.
	When seasonal average is set, the calucation will aggregate annually
	before the average is calculated.
	When accumulation is active, the temporal aggregation is done at the
	end othe concatenation.
	
	Parameters
	----------
	fname_list :	list
		list of file name of the netcdf (from model outputs)
	field :	str
		variable name
	mean : bool
		time interval for temporal aggregation.
	season : str
		list of months to ger average, default None
	accum : bool
		True accumulate values, False is default
	delta : str
		Time step for temporal aggregation, default None
	
	Returns
	-------
	data : xarray dataset
		containing all calculated values
	"""
	# loop over all continues simulation files
	concat_first_read = True
	for ifname in fname_list:
		#print(ifname, var)
		# read datasets
		data = read_dataset(ifname, var_name=var)
		#print(data)
		# if seasonal average, select months
		if season is not None:
			data = data.where(data.time.dt.month.isin(
				season_name_to_number(season)))
			# calculate annual average to reduce the use of memory
			data = resample_dataset(data, mean=mean, delt='Y')
			
		else:
			# if aggregation is provided, reduce the size of array
			# by aggregating to the annual rates
			#if delta is not None:
				# aggregate only when accumulation is not active
			if accum is False:
				data = resample_dataset(data, mean=mean, delt="Y")
			
		if concat_first_read is True:
			dataconcatenat = data.copy()
			concat_first_read = False
		else:
			dataconcatenat = xr.concat([dataconcatenat, data], dim="time")
	
	# accummulate dataset, just in case of TWSA
	if season is None:
		if accum is True:
			dataconcatenat = dataconcatenat.cumsum(dim='time')
			# aggregate dataset when accumulation is calculated
			if delta is not None:
				dataconcatenat = resample_dataset(dataconcatenat, mean=mean, delt=delta)
		
		
	# get mean values
	data = dataconcatenat.mean('time')
		
	return data

def get_average_all_variables_from_list(fname, field, season):
	"""Create a netCDF file containing mean values from all processed
	and output variables
	
	Parameters:
	-----------
	fname: path (str)
		file path of model outputs
	field: list (str)
		list of variables to process
	season: list (str)
		list of season to process

	Returns:
	--------
	xarray: dataset
		dataset containing mean values
	"""

	# loop over all specified variables
	first_read = True
	
	for ifield in field:
		
		fname_list = fname.copy()
		# check if is the riparian area
		if (ifield == 'fch') or (ifield == 'tls') or (ifield == 'ssz'):
			fname_list = [
				ifname.split('.')[0]+'rp.nc' for ifname in fname_list
				]
		
		# NOT activated when calculating the average, activate it when
		# using anomalies
		if (ifield == "twsc") or (ifield == "wrsi"):
			fname_list = [
				ifname.split('.')[0]+'_'+ifield+'.nc' for ifname in fname
				]
		
		if ifield == "flood":
			fname_list = [
				ifname.split('.')[0]+'max.nc' for ifname in fname_list
				]
		

		# read dataset
		mean = False
		if (ifield == 'tht') or (ifield == 'wte'):
			mean = True
		
		accum = False
		if ifield == 'twsc':
			accum = True
		
		delta = None
		if ifield == 'twsc':
			accum = "Y"
			
		# loop over all continues simulation files
		if ifield == "flood":
			data = get_average_from_list(fname_list, var="dis", mean=mean,
					season=season, accum=accum, delta=delta)
			data = data.rename('flood')
			#data = data.rename({'dis':'flood'})
		else:
			data = get_average_from_list(fname_list, var=ifield, mean=mean,
					season=season, accum=accum, delta=delta)
		
		# concatenate all datasets into one netcdf file
		if first_read == True:
			dataset = data.copy()
			first_read = False
		else:
			dataset = xr.merge([dataset, data])
	
	return dataset
	
	
def drop_false_keys(store_keys):
	"""Function to select variables that have false values in

	Parameters
	----------
	keys:	dict
		list of keys available at the dictionary
	store_keys:	dictionary with boolean values to store variables

	Returns
	-------
	drop_keys:	list of variables to drop from dict
	"""
	var_value = map(operator.truth, list(store_keys.values()))
	drop_keys = list(compress(list(store_keys.keys()), var_value))

	return drop_keys
	
def update_TWSA(data_current, data_previous):
	"""This fuction updates the TWSA using a TWSA file
	from the previous period. DRYP outputs TWSC, thus
	in order to preprocess TWSC into TWSA, values of
	TWSC need to be accumulated over time.
	When values are updated, TWSC is fo the current
	file is accumulated and then the last step of the
	previous simulution is added.
	
	Parameters
	----------
	data_current : dataarray
	data_previous : dataarray
	
	Returns
	-------
	
	
	"""
	data_current = data_current.cumsum(dim='time')
	
	data_current = data_current + data_previous.values[-1]
	
	return data_current

