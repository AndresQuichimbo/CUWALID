"""DRYP: post-processing tools."""
import os
import json
import xarray as xr
import numpy as np
import pandas as pd
import calendar
import rasterio
import cuwalid.tools.DRYP_rrtools as rrtools
#from cuwalid.dryp.components.DRYP_json_reader import get_model_settings

class grid_pptools(object):
	"""
	Function to post-processing DRYP model outputs.
	This function save proccessed variables as netCDF files. 

	Examples
	--------
	>>> import DRYP_pptools as pptools
	>>> gridpp = pptools.grid_pptools(file_model_input)
	>>> gridpp.get_mean() # save mean values
	>>> gridpp.get_wrsi() # save wsri
	>>> gridpp.get_twsa() # save total water storage anomaly

	"""
	def __init__(self, inputfile):
		"""Fuction to generate names of model results. This names are
		then passed to other functions to calculate and save  model
		results
		
		Parameters
		----------
		inputfile : str
			filename including path of the model "input_file"
		
		Returns
		-------
		object containing strings as filenames
		"""
		# Output filenames
		filename = pd.read_csv(inputfile)
		self.Mname = filename.drylandmodel[1]
		# get directories
		self.DirOutput = filename.drylandmodel[81]
		self.Dirpostpp = filename.drylandmodel[83]
		if self.Dirpostpp == "none":
			self.DirOutput = filename.drylandmodel[81]
		
		# get filenames of all outputs
		self.fname_grid = self.DirOutput+'/' + self.Mname + '_grid.nc'
		self.fname_point = self.DirOutput+'/' + self.Mname + '_p_'
		self.fname_UZ = self.DirOutput+'/' + self.Mname + '_UZ_'
		self.fname_RZ = self.DirOutput+'/' + self.Mname + '_RZ_'
		self.fname_RZ_avg  = self.DirOutput+'/' + self.Mname + '_RZ_avg'
		self.fname_avg = self.DirOutput+'/' + self.Mname + '_avg'

		# get filenames post-postproccess outputs
		self.fname_gridpp = self.Dirpostpp + '/' + self.Mname + '_grid.nc'
		# model variables list
		self.var_name = ['pre', 'pet', 'dis', 'aet', 'inf', 'run', 'tht', 
		   'rch', 'egw', 'wte', 'gdh', 'twsc']

	def get_mean(self, deltat='Y', start_time=None, end_time=None):
		"""Thids function get mean values of all variables of a netcdf file"""
		calculate_mean_from_netCDF(self.fname_grid,
			     fname_out=self.fname_gridpp, 
				 field=self.var_name,
				 deltat='Y', start_time=start_time, end_time=end_time)

	def get_wrsi(self, deltat='Y', start_time=None, end_time=None):
		"""This function gets wrsi index from model outputs"""
		calculate_WRSI_from_netCDF(self.fname_grid,
			     fname_out=self.fname_gridpp,
				 deltat='Y', start_time=start_time, end_time=end_time)

	def get_twsa(self, var_name=None, mean=True, deltat='Y',
	      start_time=None, end_time=None):
		"""Get total water storage anomaly from model outputs"""
		calculate_twsa_from_netCDF(self.fname_grid,
			     fname_out=self.fname_gridpp,
				 var_name="twsc", start_time=start_time, end_time=end_time)
		
	def get_seasonal_average(self,var_name=None):
		"""Get seasonal average values"""

	def get_anomalies(self, var_name=None):
		"""Get anomalies"""

	def get_aridity_index(self, var_name=None):
		"""Get anomalies"""
	

		
class get_output_filenames(object):
	"""Function to get all names of model outputs"""
	def __init__(self, path_input):
		"""Fuction to generate names of model results. This names are
		paths to the model outputs. The function will read the
		configuration file and generate the names of the outputs.
		path_grid : path to the model grid outputs
		path_csv : path to the model csv outputs
		path_raster : path to the model raster outputs
		
		Parameters:
		----------
		path_input : str
			filename including path of the model "input_file"
		
		Returns:
		--------
		object containing strings as filenames
				
		Example:
		--------
		>>> import DRYP_pptools as pptools
		>>> fnames = pptools.get_output_filenames(file_model_input)
		>>> fnames.path_csv
		>>> fnames.path_csv["avg"]
		>>> fnames.path_csv["point"]["pre"]
		>>> fnames.path_grid
		>>> fnames.path_grid["grid"]
		>>> fnames.path_grid["rp"]
		>>> fnames.path_raster
		>>> fnames.path_raster["wte"]
		>>> fnames.path_raster["tht"]
		>>> fnames.path_raster["Qo"]
		>>> fnames.path_raster["Vpnd"]
		>>> fnames.path_raster["thtrp"]
		"""
		# Output filenames
		with open(path_input, 'r') as f:
			dryp_config = json.load(f)

		Mname = dryp_config["model_name"]
		DirOutput = dryp_config["OUTPUT"]["path_output"]

		fnameTS_grid = os.path.join(DirOutput, Mname + '_grid')
		fnameTS_point = os.path.join(DirOutput, Mname + '_p_')
		fnameTS_UZ = os.path.join(DirOutput, Mname + '_UZ_')
		fnameTS_RZ = os.path.join(DirOutput, Mname + '_RZ_')
		fnameTS_RZ_avg = os.path.join(DirOutput, Mname + '_RZ_avg')
		fnameTS_avg = os.path.join(DirOutput, Mname + '_avg')

		labels = ['pre', 'pet', 'dis', 'aet', 'inf', 'run', 'tht', 
		   'rch', 'egw', 'wte', 'gdh', 'twsc']

		point_csv_dict = {}
		# get directories
		for key in labels:
			# name csv file names
			point_csv_dict[key] = fnameTS_point + key + '.csv'

		# get directories
		# name csv file names
		self.path_csv = {
		"avg" : fnameTS_avg+".csv",
		"point" : point_csv_dict,
		"avgrp": fnameTS_avg+'rp'+".csv",
		"avgpnd": fnameTS_avg+'pnd'+".csv",
		}

		# filename of the model grid outputs
		self.path_grid = {
		"grid" : fnameTS_grid+'.nc',
		"rp" : fnameTS_grid+'rp.nc',
		"pnd" : fnameTS_grid+'pnd.nc',
		"vmax" : fnameTS_grid+'vmax.nc',
		"rmax" : fnameTS_grid+'rmax.nc',
		}

		# name outputs for initial conditions
		self.path_raster = {
		"wte" : fnameTS_avg + '_wte_ini.asc',
		"tht" : fnameTS_avg + '_tht_ini.asc',
		"Qo" :fnameTS_avg + '_Q_ini.asc',
		"thtrp" : fnameTS_avg + '_tht_rp_ini.asc',
		"Vpnd" : fnameTS_avg + '_V_pnd_ini.asc',
		}
	pass

def calculate_storage_from_files(fname, path_surface, path_Droot, path_theta_sat, path_Sy,
								  path_bathymetry=None, path_bottom=None,
								  start_time=None, end_time=None, fname_out=None,
								  anomalies=True):
	
	"""Calculate storage for all components (surface, subsurface, groundwater)
	from model simulations
	
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

	"""


	#fsurface, fbathymetry,
	#fbottom, fDroot, ftheta_sat, fSy):
	
	#fsurface = fname_rasters[0]
	#fbathymetry = fname_rasters[1]
	##fbottom = fname_rasters[0]
	#fDroot = fname_rasters[2]
	#ftheta_sat = fname_rasters[3]
	#fSy = fname_rasters[4]
	
	head = preprocesses_netCDF(fname, "wte", mean=True, deltat='M',
			start_time=start_time, end_time=end_time
			)
	
	theta = preprocesses_netCDF(fname, "tht", mean=True, deltat='M',
			start_time=start_time, end_time=end_time
			)
		
	surface = rrtools.open_raster(path_surface)[0]
	if path_bathymetry is not None:
		bathymetry = rrtools.open_raster(path_bathymetry)[0]
	else:
		bathymetry = surface.copy()
	
	if path_bottom is not None:
		bottom = rrtools.open_raster(path_bottom)[0]
	else:
		bottom = np.zeros_like(surface)
	
	Droot = rrtools.open_raster(path_Droot)[0]
	theta_sat = rrtools.open_raster(path_theta_sat)[0]
	Sy = rrtools.open_raster(path_Sy)[0]
	
	str_sz, str_uz, str_lakes = calculate_storage(head, theta, surface,
		bathymetry, bottom, Droot*0.001, theta_sat, Sy)
	
	if anomalies is True:
		str_sz = str_sz-str_sz.mean(dim="time")
		str_uz = str_uz-str_uz.mean(dim="time")
		str_lakes = str_lakes-str_lakes.mean(dim="time")
	
	#save raster dataset as netcdf
	# save files
	if fname_out is None:
		fname_out = fname
	
	# save dataset as netcdf
	# unsaturated zone storage
	fname_out_uz = fname_out.split('.')[0]+'_str_uz.nc'
	save_xarray_dataset_as_netcdf(fname_out_uz, str_uz, ["str_uz"])

	# saturated zone storage
	fname_out_sz = fname_out.split('.')[0]+'_str_sz.nc'
	save_xarray_dataset_as_netcdf(fname_out_sz, str_sz, ["str_sz"])

	# lakes zone storage
	fname_out_pnd = fname_out.split('.')[0]+'_str_lakes.nc'
	save_xarray_dataset_as_netcdf(fname_out_pnd, str_lakes, ["str_lakes"])

	#return str_sz, str_uz, str_lakes

def calculate_storage(head, theta, surface, bathymetry, bottom, Droot, theta_sat,
		  Sy):
	"""Function to calculate storage for all components of the water balance
	calculate the Total storage along the vertical profile of each model cell
	
	Parameters
	----------
	surface:	surface elevation [m]
	bottom:		bottom elevation [m]
	bathymetry:	surface elevation of lakes [m] 
	Droot:		Rooting depth [mm]
	theta:		Water content at time t [-]
	head:		water table [m]
	theta_sat:	Saturated water content [-]
	Sy:			Specific yield [-]
	
	Returns
	-------
	total:		Volume of water stored in the saturated zone [mm]
	"""
	
	# water stored in lakes
	str_lakes = head - bathymetry
	#str_lakes[str_lakes < 0.0] = 0.0
	str_lakes = str_lakes.where(str_lakes < 0.0, 0.0)
	str_lakes = str_lakes.rename("str_lakes")

	# estimate saturated-unsaturated storage
	z_root = bathymetry - Droot
	str_usz = (head - str_lakes - z_root)
	#str_usz[str_usz < 0] = 0.0
	str_usz = str_usz.where(str_usz < 0.0, 0.0)
	
	# estimate storage water available in the unsaturated zone
	# estimate rooting depth storage
	str_uz = Droot - str_usz
	str_uz = str_uz*theta
	str_uz = str_uz.rename("str_uz")
	
	# estimate saturated storage
	str_sz = head - str_usz - str_lakes - bottom
	str_sz = str_sz*Sy + str_usz*theta_sat
	str_sz = str_sz.rename("str_sz")
	# total storage
	# total = storage in saturated zone
	# 		+ storage in unsaturated zone + storage in lakes
	#total = (str_lakes
	#		+ str_uz*theta
	#		+ str_usz*theta_sat
	#		+ str_sz*Sy
	#		)
	
	return str_sz, str_uz, str_lakes


def calculate_anomalies_from_netCDF(fname, field='pre', fname_out=None,
			       deltat='Y', start_time=None, end_time=None):
	"""Get anomalies from netcdf filed
	
	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	field :	str
		model variables to process
	deltat : str
		time interval for temporal aggregation.
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".

	Returns
	-------

	"""

	# pre process Actual evapotranspiration (AET)
	dataset = preprocesses_netCDF(fname, field,
				       mean=True, deltat=deltat,
					   start_time=start_time, end_time=end_time
					   )
	# calculate anomaly
	anomaly = calculate_anomaly(dataset, dataset_mean=None, dim="time")

	# save files
	if fname_out is None:
		fname_out = fname
		fname_out = fname.split('.')[0]+'_wrsi.nc'
	save_xarray_dataset_as_netcdf(fname_out, anomaly, [field])

	
def calculate_mean_from_netCDF(fname, field, fname_out=None,
			       deltat='Y', start_time=None, end_time=None):
	"""Get mean average values from dataset. The output filename
	 will be added "mean" at the end of the name.

	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	field :	list
		list of model variables to process
	deltat : str
		time interval for temporal aggregation.
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".

	Returns
	-------
	netCDF file containing all calculated values
	"""

	# iterate through all fields
	first_read = True
	
	for ifield in field:
		# read dataset
		mean = False
		if (ifield == 'tht') or (ifield == 'wte') or (ifield == "ssz"):
			mean = True
		
		# check if is the riparian area
		if (ifield == 'fch'):
			ifname = fname.split('.')[0]+'rp.nc'
		else:
			ifname = fname
		
		if check_if_field_available_in_netCDF(ifname, ifield) is True:
			# preporcess netcdf file
			data = preprocesses_netCDF(ifname, ifield,
					       mean=mean, deltat=deltat,
						   start_time=start_time, end_time=end_time
						   )

			# get mean average values
			data = data.mean('time')

			# save in only one file all variables
			if first_read == True:
				dataset = data.copy()
				first_read = False
			else:
				dataset = xr.merge([dataset, data])
	
	# save files
	if fname_out is None:
		fname_out = fname
		fname_out = fname_out.split('.')[0]+'_mean.nc'
	save_xarray_dataset_as_netcdf(fname_out, dataset, field)

def calculate_WRSI_from_netCDF(fname, fname_out=None, deltat='Y',
			       start_time=None, end_time=None):
	"""Get mean average values from dataset.

	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	field :	list
		list of model variables to process
	deltat : str
		time interval for temporal aggregation.
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".

	Returns
	-------
	netCDF file containing all calculated values
	"""
	# pre process Actual evapotranspiration (AET)
	dataset_aet = preprocesses_netCDF(fname, "aet",
				       mean=True, deltat=deltat,
					   start_time=start_time, end_time=end_time
					   )	
	
	# pre process Potential evapotranspiration (PET)
	dataset_pet = preprocesses_netCDF(fname, "pet",
				       mean=True, deltat=deltat,
					   start_time=start_time, end_time=end_time
					   )
	
	# save in only one file all variables
	dataset = calculate_WRSI(dataset_aet, dataset_pet)
	
	# assign variable name to the new dataset
	dataset.name = "wsri"
	
	# save files
	if fname_out is None:
		fname_out = fname
		fname_out = fname.split('.')[0]+'_wrsi.nc'
	save_xarray_dataset_as_netcdf(fname_out, dataset, ["wsri"])

def calculate_twsa_from_netCDF(fname, fname_out=None, var_name="twsc",
			       start_time=None, end_time=None):
	"""This funtion calculate the total water storage anomaly
	 from the dryp model outputs
	 
	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	var_name :	str
		model variables to process
	mean : boolean
		True calulate the mean, False acculumate over time
	deltat : str
		time interval for temporal aggregation.
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".

	Returns
	-------
	xarray :
		2D time series mean or sum of tne dataset

	 """
	data = preprocesses_netCDF(fname, var_name, mean=False, deltat='M',
			    start_time=start_time, end_time=end_time)
	data = data.cumsum(dim='time')

	# surface water needs to be added
	
	# change variable name to the new dataset
	data = data.rename("twsa")

	# save files
	if fname_out is None:
		fname_out = fname
		fname_out = fname_out.split('.')[0]+'_twsa.nc'
	save_xarray_dataset_as_netcdf(fname_out, data, ["twsa"])


def calculate_AI_from_netCDF(fname_pre, fname_pet, fname_out=None,
			     deltat='Y', start_time=None, end_time=None, average=True):
	"""Get mean average values from dataset.

	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	field :	list
		list of model variables to process
	deltat : str
		time interval for temporal aggregation.
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".
	average : bool
		if True, the long therm average is caluated otherwise it will
		return a time series dataarray

	Returns
	-------
	netCDF file containing all calculated values
	"""
	# pre process Actual evapotranspiration (AET)
	dataset_pre = preprocesses_netCDF(fname_pre, "pre",
				       mean=True, deltat=deltat,
					   start_time=start_time, end_time=end_time
					   )	
	
	# pre process Potential evapotranspiration (PET)
	dataset_pet = preprocesses_netCDF(fname_pet, "pet",
				       mean=True, deltat=deltat,
					   start_time=start_time, end_time=end_time
					   )
	
	# save in only one file all variables
	dataset = calculate_aridity_index(dataset_pre, dataset_pet)
	
	# assign variable name to the new dataset
	dataset.name = "ai"
	
	# get mean value or time series
	if average is True:
		dataset = dataset.mean(dim='time')
	
	# save files
	if fname_out is None:
		fname_out = fname_pre
		fname_out = fname_pre.split('.')[0]+'_ai.nc'
	save_xarray_dataset_as_netcdf(fname_out, dataset, ["ai"])

def calculate_saturation_from_netCDF(fname, path_wp, path_sat, fname_out=None,
									 var_name="tht",):
	"""This funtion calculate the saturation from water content from
	the dryp model outputs
	 
	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	path_wp :	str
		file name of the wilting point raster dataset
	path_sat :	str
		file name of the soil moisture at saturation as raster
	var_name :	str
		model variables to process
	deltat : str
		time interval for temporal aggregation.
	
	Returns
	-------
	xarray :
		2D time series mean or sum of tne dataset

	Example:
	--------
	>>> import sys
	>>> import os
	>>> import geopandas as gpd

	>>> import cuwalid.tools.DRYP_pptools as pptools

	>>>	path_Sy = "path_to_file"
	>>>	path_surface = "path_to_file"
	>>>	path_bathymetry = "path_to_file"
	>>>	path_theta_sat = "path_to_file"
	>>>	path_theta_wp = "path_to_file"
	>>>	path_Droot = "path_to_file"


	>>>	fname = "path_output_netcdf_file"
	>>>	shapefile_path = "path_output_netcdf_file"

	>>>	region = gpd.read_file(shapefile_path)

	>>>	pptools.extract_dataset(fname, region, clip_region=False,
	>>>		dataPP=None, maskPP=None, bands=["pre", "aet", "rch", "dis"], save=True)

	>>>	pptools.calculate_saturation_from_netCDF(fname, path_theta_wp, path_theta_sat,
	>>>			fname_out=None, var_name="tht")

	"""
	
	# change variable name to the new dataset
	dataset = read_dataset(fname, var_name=var_name)

	# read raster dataset -  wilting point
	theta_wp = rrtools.open_raster(path_wp)[0]
	theta_wp = np.array(np.flip(theta_wp, 0), dtype=float)

	# read raster dataset -  wilting point
	theta_sat = rrtools.open_raster(path_sat)[0]
	theta_sat = np.array(np.flip(theta_sat, 0), dtype=float)

	# calculate saturation
	data = calculate_saturation(dataset, theta_wp, theta_sat)
	# save files
	if fname_out is None:
		fname_out = fname
		fname_out = fname_out.split('.')[0]+'_tht_sat.nc'
	save_xarray_dataset_as_netcdf(fname_out, data, ["tht"])

def calculate_seasonal_average_from_netCDF(fname, var_name='pre', season="OND",
			       fname_out=None, mean=False,
				   start_time=None, end_time=None):
	"""This function calculates the seasonal average from netCDF file
	
	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	var_name :	str
		model variables to process
	mean : boolean
		True calulate the mean, False acculumate over time
	deltat : str
		time interval for temporal aggregation.
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".

	Returns
	-------
	xarray :
		2D time series mean or sum of tne dataset

	"""

	# read dataset
	data = preprocesses_netCDF(fname, var_name=var_name, mean=mean, deltat='M',
			    start_time=start_time, end_time=end_time)

	# get seasson
	data = data.where(data.time.dt.month.isin(season_name_to_number(season)))
	
	# get average from season
	data = resample_dataset(data, mean=True, deltat='Y')
	
	# save season as netcdf file
	# save files
	if fname_out is None:
		fname_out = fname
		fname_out = fname_out.split('.')[0]+'_'+season+'.nc'
	save_xarray_dataset_as_netcdf(fname_out, data, [var_name])

def extract_dataset(netcdf_path, region, clip_region=True,
	dataPP=None, maskPP=None, fname_out=None, save=False, bands=["pre"]):
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
	save: bool
		activate save option, default true
	fname_out : str
		path of outputs

	Returns
	-------
	dataset : xarray dataset
		concatenated datasets
	
	Example:
	--------
	>>> import geopandas as gpd
	>>> import cuwalid.tools.DRYP_pptools as pptools

	>>>	fname = "path_output_netcdf_file"
	>>>	shapefile_path = "path_output_netcdf_file"

	>>>	region = gpd.read_file(shapefile_path)

	>>>	pptools.extract_dataset(fname, region, clip_region=False,
	>>>		dataPP=None, maskPP=None, bands=["pre", "aet", "rch", "dis"], save=True)

	"""
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
	
	# save season as netcdf file
	if save is True:
		# save files
		if fname_out is None:
			fname_out = netcdf_path
			fname_out = fname_out.split('.')[0]+'_'+'clipped.nc'

		save_xarray_dataset_as_netcdf(fname_out, dataset, bands)
	else:
		return dataset

def clip_dataset_by_region(ds, region):
	"""This function clip netcdf files by region, projection should
	match WGS84, otherwise it will raise an error.
	
	Parameters
	----------
	dataset : data xarray
		dataset
	region : geodataframe
		name of variable to process

	Returns
	-------
	dataset : xarray dataset
	
	"""
	# Clip the data model
	ds_clipped = ds.rio.clip(region.geometry.values, region.crs)

	return ds_clipped
	

def calculate_aridity_index(dataset_pre, dataset_pet):
	"""Calculate the aridity index based on the UNEP:
	UNEP. World atlas of desertification - Second Edition. vol. SECOND 
	EDITION (United Nations Environment Program, 1997)
	
	Parameters
	----------
	dataset_pre : Dataxarray
		precipitation dataset
	dataset_pre : Dataxarray
		potential evapotranspiration dataset

	Returns
	-------
	DataArray
		Aridity index
	"""
	return dataset_pre/dataset_pet

def calculate_saturation(dataset, theta_wp, theta_sat):
	"""Calculate the saturation from soil water content, normalization
	of water content in relation to saturation
	
	Parameters
	----------
	dataset : Dataxarray
		soil moisture dataset
	theta_wp : numpy array
		soil moisture at wilting point
	theta_sat : numpy array
		soil moisture at saturation point (porosity)

	Returns
	-------
	DataArray
		saturation
	"""
	# Calculate saturation
	saturation = (dataset - theta_wp)/theta_sat

	return saturation

def preprocesses_netCDF(fname, var_name, mean=True, deltat='Y',
			start_time=None, end_time=None):
	"""This function read, slice, and resample netCDF files.

	Parameters
	----------
	fname :	str
		file name of the netcdf (from model outputs)
	var_name :	str
		model variables to process
	mean : boolean
		True calulate the mean, False acculumate over time
	deltat : str
		time interval for temporal aggregation.
	start_time : str
		starting date for the analysis, "DD-MM-YYYY".
	end_time : str
		final date for the analysis, "DD-MM-YYYY".

	Returns
	-------
	xarray :
		2D time series mean or sum of tne dataset

	"""
	dataset = read_dataset(fname, var_name=var_name)
	
	# slice dataset
	dataset = slice_dataset_time(dataset,
			start_time=start_time,
			end_time=end_time
			)	
	# resample dataset
	return resample_dataset(dataset, deltat=deltat, mean=mean)
	
def calculate_WRSI(dataset_aet, dataset_pet):
	"""Calculate Water Requirement Satisfaction Index"""
	return dataset_aet/dataset_pet

def calculate_anomaly(dataset, dataset_mean=None, dim="time"):
	"""Calculate anomaly
	anomaly = value - mean
	
	Parameters
	----------
	dataset : DataArray
		dataset to calculate the anomaly
	dataset_mean : DataArray
		mean value
	dim : str
		name of the axis to calculate mean (defail is "time")

	Returns
	-------
	DataArray
		amomalies

	"""
	if dataset_mean is None:
		dataset_mean = dataset.mean(dim=dim)
	
	return dataset-dataset_mean

def calculate_percentage_anomaly(dataset, dataset_mean=None, offset=None, dim="time"):
	"""Calculate anomaly
	anomaly = value - mean
	If mean value not availble it will calculate the mean values
	
	Parameters
	----------
	dataset : DataArray
		dataset to calculate the anomaly
	dataset_mean : DataArray
		mean value (optional)
	offset : DataArray
		offset value to shift mean (optional) 
	dim : str
		name of the axis to calculate mean (defail is "time")
		
	Returns
	-------
	DataArray
		amomalies

	"""
	# calculate mean value if not provided'
	if dataset_mean is None:
		dataset_mean = dataset.mean(dim=dim)
	
	# check if scale is provided
	if offset is not None:
		dataset_mean = dataset_mean - offset
	
	# calculate anomalies
	anomaly = dataset-dataset_mean
	
	return anomaly*100.0/dataset_mean

def calculate_weighted_stats_dataset(dataset, weight=None, dim='sim'):
	"""This function calculate the weighted mean and standard deviation
	of dataset

	Parameters
	----------
	dataset : DataArray
		dataset to calculate the anomaly
	dataset_mean : DataArray
		mean value (optional)
	offset : DataArray
		offset value to shift mean (optional) 
	dim : str
		name of the axis to calculate mean (defail is "time")
		
	Returns
	-------
	DataArray
		amomalies
	"""

	# Calculate the weighted mean
	if weight is None:
		weight = np.ones(len(dataset))

	weights = xr.DataArray(weight,
					dims=[dim],
					coords=[np.arange(len(weight))])
			
	weighted_mean = (dataset * weights).sum(dim=dim) / weight.sum()
		
	# Calculate the squared deviations
	squared_deviations = (dataset - weighted_mean) ** 2
		
	# Calculate the weighted sum of squared deviations
	weighted_sum_squared_deviations = (squared_deviations * weights).sum(dim=dim)
		
	# Calculate the weighted standard deviation
	weighted_std = np.sqrt(weighted_sum_squared_deviations / weights.sum())

	return weighted_mean, weighted_std

def create_ensamble_simulations(fname_list, var_name='tht'):
	"""This function create an ensamble of simulations. This function
	aggregate the datasets to the specified time step and calculate
	the mean values
	
	Parameters
	----------
	fname_list : list
		list of paths of model output files
	var_name : str
		variable to process
		
	Returns
	-------
	DataArray
		ensable of multiple simulations
	
	"""
	first_read = True

	# read all files from list
	for ifname in fname_list:
		idataset = preprocesses_netCDF(ifname, var_name, mean=True, deltat='Y',
			start_time=None, end_time=None).mean(dim="time")
		
		# concatenate all datasets
		if first_read is True:
			dataset = idataset.copy()
			first_read = False
		else:
			dataset = xr.concat([dataset, idataset], 'sim')

	return dataset

def save_xarray_dataset_as_netcdf(fname, data, var_name):
	# data has to be in the same dimentions
	# Create a xarray DataArray
	# Set the compression format
	encoding = {}
	for ivar in var_name:
		encoding.update({ivar: {'zlib': True, 'complevel': 9}})

	# Save the dataset to a netcdf file
	data.to_netcdf(fname, encoding=encoding)
	
	#return
def slice_dataset_time(dataset, start_time=None, end_time=None):
	# Slice the dataset between two dates
	if start_time is None:
		dataset = dataset.sel(time=slice(start_time, end_time))	    
	return dataset

def read_dataset(fname, var_name='tht'):
	# Open the first netCDF file
	# Returns dataset
	data = xr.open_dataset(fname)
	data = data[var_name]
	return data

def resample_dataset(data, mean=True, deltat='Y'):
	# calculate climatological mean
	if mean is True:
		data = data.resample(time=deltat).mean()
	else:
		data = data.resample(time=deltat).sum()	
	return data
	
def merge_xarray_dataset(dataset1, dataset2):
	return xr.merge([dataset1, dataset2])

def check_if_field_available_in_netCDF(fname, var_name):
	"""This function check it a variable is stored in the netCDF file"""
	var_available = False
	if var_name in list(xr.open_dataset(fname).variables):
		var_available = True
	return var_available

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

def get_month_first_letter(month_number):
    if 1 <= month_number <= 12:
        return calendar.month_name[month_number][0]
    else:
        return "Invalid month number"

def get_season_name(season):
	name = ""
	for imonth in season:
		name += get_month_first_letter(imonth)
	return name

def get_zone_from_dataset(dataset, mask):
	"""Get time series of a zone from a netCDF
	
	Parameters
	----------
	dataset : dataset
		dataset from which the mean will be extracted
	mask : boolean array
		masked array

	Returns
	-------
	numpy array

	"""
	zone_data = dataset.where(mask)
	zone_data = zone_data.mean(dim=('lat', 'lon'), skipna=True).squeeze()
	return zone_data.values

def get_dataframe_zone_from_netcdf(fname, fname_mask, field=['twsc'], regionid=None):
	"""Caclulate the mean values of zone from a netcdf and store it as
	dataframe
	
	Parameters
	-----------
	fname : str
		path of netcdf file
	mask : bo

	Returns
	-------
	dataframe
	
	"""
	# read raster dataset containg the region
	regions = np.array(np.flip(rasterio.open(fname_mask).read(1), 0), dtype=int)
	
	# create a boolean mask
	mask = np.zeros_like(regions, dtype=bool)
	
	# select region to extract
	if regionid is not None:
		# Set specific locations to True
		idr = np.where(regions == regionid)
		
	else:
		# specified all values greater than zeros
		idr = np.where(regions > 0)

	mask[idr] = True

	# create dataframe
	df = pd.DataFrame()
	df['Date'] = read_dataset(fname)['time']
	
	# hillslope
	for ifield in field:		
		df[ifield] = get_zone_from_dataset(
			read_dataset(fname, var_name=ifield),
			mask
			)
	return df

def get_point_from_dataset(dataset, x_coord, y_coord, field):
	# read model dataset
	data = dataset[field]
	time = dataset['time']
	# create dataframe
	df = pd.DataFrame()
	df['Date'] = time

	for i, ix_point in enumerate(x_coord):		
		# Select the grid point closest to the specified location
		ds_point = data.sel(lon=x_coord[i], lat=y_coord[i], method='nearest')
		df[field +"_"+str(i)] = ds_point.values

	return df

def get_dataframe_point_from_netcdf(fname, fname_csv, field='dis',
									xlabel='East', ylabel='North'):
	"""get point values along the time axis of a specified netcdf file at
	coordinets specifed in a csv file.
	
	Parameters
	-----------
	fname : str
		path of netcdf file
	fname_csv : str
		path of csv file containing point
	field : str
		name of the field to get values (default: dis)
	xlabel : str
		name of the head of the x coordinates, default is East
	ylabel : str
		name of the head of the y coordinates, default is North
		
	Returns
	-------
	dataframe
	
	"""
	# read model dataset
	dataset = xr.open_dataset(fname)

	# read filename of poitns
	points = pd.read_csv(fname_csv)

	# create array of coordinates
	x_coord = points[xlabel].values
	y_coord = points[ylabel].values

	# get points value from netcdf
	return get_point_from_dataset(dataset, x_coord, y_coord, field)

def get_ensamble_from_netcdf_list(fname_list, var_name, mean=True, save=True,
								  fname_output=None):
	"""This function read a list of netcdf paths and return a dataset
	or netCDF file containing all netCDFs"""

	first_read = True
	for ifname in fname_list:
		# Check if input file exist
		if os.path.exists(ifname):
			# read dataset and calculate the correlation
			idata = read_dataset(ifname, var_name=var_name)
			idata = slice_dataset_time(idata)
			
			if mean is True:
				idata = idata.mean(dim='time')
			else:
				idata = idata.cumsum(dim='time')
	
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