#import netCDF4
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

def get_anomalies_multi_netcdf(model_path, model_name, start_year, end_year, season, variables, postpp_path):

	# ===============================================================

	# path of simulation files
	fname  = [
		model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	]

	#fname_lta = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGag_sim0_mean.nc"

	# path of mean values
	#var = ['pre', 'inf', 'pet', 'rch', 'aet', 'gdh', 'egw', 'fch', 'twsc', 'run']
	field = ['pre', 'pet',
		'aet', 'tht', 'egw',
		#'inf', 'run',
		'rch', 'fch',
		#'gdh',
		'dis', 'tls',
		'wte',
		"twsc",
		]

	#months = [None, [3,4,5], [10,11,12]]

	# loop 
	for ifield in field:
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
		
		#for iseason, imonths in zip(season, months):
		for iseason in season:

			# read datasets
			# read long term average values
			if iseason is None:
				#fname_lta = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
				fname_lta = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_" + model_name + "_mean.nc"
			else:
				#fname_lta = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
				fname_lta = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_" + model_name + '_' + iseason + "_mean.nc"
			
			lta = read_dataset(fname_lta, var_name=ifield)	
			
			# check if is the riparian area
			fname_list = fname.copy()
			if (ifield == 'fch') or (ifield == 'tls') or (ifield == 'ssz'):
				fname_list = [
					ifname.split('.')[0]+'rp.nc' for ifname in fname_list
					]
			if ifield == "twsc":
				fname_list = [
					ifname.split('.')[0]+'_'+ifield+'.nc' for ifname in fname_list
					]
			
			# loop over all continues simulation files
			concat_first_read = True
			for ifname in fname_list:
				# read season
				data = read_dataset(ifname, var_name=ifield)
				
				# if seasonal average, select months
				if iseason is not None:
					data = data.where(data.time.dt.month.isin(
							season_name_to_number(iseason))
							)
				# calculate annual average to reduce the use of memory
				data = resample_dataset(data, mean=mean, delt='Y')
				
				# calculate anomalies
				data = data - lta
				
				# aggregate into one array
				if concat_first_read is True:
					dataconcatenat = data.copy()
					concat_first_read = False
				else:
					dataconcatenat = xr.concat([dataconcatenat, data], dim="time")
				
			# save files
			if iseason is None:
				#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
				fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_" + model_name + "_" + ifield + "_anomalies.nc"
			else:
				#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_season_mean.nc'
				fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_" + model_name + "_" + iseason + "_" + ifield +"_anomalies.nc"
			#print(fname_out)
			save_xarray_dataset_as_netcdf(fname_out, dataconcatenat, [ifield])

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

def read_dataset(fname, var_name='tht'):
	# Open the first netCDF file
	# output dataset
	data = xr.open_dataset(fname)
	data = data[var_name]
	return data

def resample_dataset(data, mean=True, delt='Y'):
	# calculate climatological mean
	# output an array
	if mean is True:
		data = data.resample(time=delt, skipna=True).mean()
	else:
		data = data.resample(time=delt, skipna=True).sum()
	return data

def season_name_to_number(season):
	"""This function read a string representing seasons and return a
	list of numbers indicating months
	
	Parameters
	----------
	season : str
		season represented by three capital letters (e.g. "OND")

	Returns
	-------
	list
		list of months
	"""

	if season == "MAM":
		season = [3,4,5]
	elif season == "OND":
		season = [10,11,12]

	return season

