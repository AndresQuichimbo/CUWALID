import os
import pandas as pd
import xarray as xr
import numpy as np
import cuwalid.tools.CUWALID_mfile_tools as cuwalid
import matplotlib.pyplot as plt

def get_csv_TS_files_from_multi_CSV(model_path, model_name, start_year, end_year):
	csv_file = [
	"_avgrp.csv",
	"_avgpnd.csv",
	"_p_wte.csv",
	"_p_tht.csv",
	"_p_ssz.csv",
	"_p_rch.csv",
	"_p_inf.csv",
	"_p_gdh.csv",
	"_p_dis.csv",
	"_p_aet.csv",
	"_avg.csv",
	]

	for icsv_file in csv_file:
		fname = [
			#"/user/work/km19051/HAD_output/HAD_IMERG_sim_84_"+str(year)+"_avg.csv" for year in range(2000, 2006)
			#"/user/work/km19051/HAD_output/HAD_IMERG_sim_84_"+str(year)+"_p_dis.csv" for year in range(2000, 2006)
			model_path+model_name+"_"+ str(iyear) + icsv_file for iyear in range(start_year, end_year)
			]
		first_read = True
		for ifname in fname:
			if first_read == True:
				data = pd.read_csv(ifname)
				first_read = False
			else:
				data = pd.concat([data, pd.read_csv(ifname)], ignore_index=True)
		
		#fname = "/home/c1755103/HAD/HAD_output/HAD_IMERG_sim_73_p_dis.csv"
		fname = model_path+model_name+icsv_file
		data.to_csv(fname, index=False)
		
def get_TWSA_from_mult_files(model_path, model_name, start_year, end_year):
	""" Get TWSA - total water storage anomalies form multiple netcdf files

	Parameters:
	-----------
	model_path: path (str)
		folder path of model outputs files
	model_name: str
		model name
	start_year: int
		starting year of the analysis
	end_year: int
		starting year of the analysis

	Returns
	-------

	"""

	fname = get_name_list_historical_netcdf_files(model_path, model_name, start_year, end_year)
	#fname  = [
	#'/home/c1755103/HAD/HAD_output/HAD_IMERG_sim_28b_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2022)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2001, 2023)
	#model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	#]

	#imodel = "IMERGb_D2E_sim"

	field = ['twsc']

	# DO NOT MODIFY FROM HERE ---------------------------------------

	for ifield in field:
			
		# concatenate dataset at selected fields
		data_concat = cuwalid.concatenate_netCDF(
			fname, ifield, agg="M", dim='time'
			)
		
		# accummulate dataset, just in case of TWSA
		if ifield == 'twsc':
			data_concat = data_concat.cumsum(dim='time')

			# Define the path for the yearly NetCDF file
			fname_list = [
				ifname.split('.')[0]+'_'+ifield+'.nc' for ifname in fname
				]
		
		# Group by year and create a new dataset for each year
		grouped = data_concat.groupby('time.year')
		
		# loop over years
		idfname = 0
		for year, yearly_data in grouped:
			# Adjust the path and filename format as needed
			#output_filename = "/home/c1755103/HAD/HAD_output/HAD_IMERGb_sim_" + ifield + "_"+str(year)+".nc"
			
			# Save the yearly data to a NetCDF file
			output_filename = fname_list[idfname]
			yearly_data.to_netcdf(output_filename)
			idfname += 1
			
def get_additional_variables_multi_netcdf(model_path, model_name, start_year, end_year):
	""" Get WRSI water satisfaction index and total evapotranspiration
	

	Parameters:
	-----------
	model_path: path (str)
		folder path of model outputs files
	model_name: str
		model name
	start_year: int
		starting year of the analysis
	end_year: int
		starting year of the analysis

	Returns
	-------

	"""
	# get list of name
	fname = get_name_list_historical_netcdf_files(model_path, model_name, start_year, end_year)
		
	#fname  = [
	#'/home/c1755103/HAD/HAD_output/HAD_IMERG_sim_28b_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2022)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2001, 2023)
	#model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	#]

	#imodel = "IMERGb_D2E_sim"

	field = ["wrsi", "aet"]

	# DO NOT MODIFY FROM HERE ---------------------------------------
	cuwalid.get_postprocessed_hydro_variables_mfiles(fname)
	#for ifield in field:
	#	
	#	for ifname in fname:
	#		if ifield == "wrsi":
	#			# Calculate WRSI 
	#			data = cuwalid.read_dataset(ifname, "aet")/cuwalid.read_dataset(ifname, "pet")
	#			data = data.rename("wrsi")
	#		else:
	#			# Calculate total evaporation
	#			data = cuwalid.read_dataset(ifname, "aet")+cuwalid.read_dataset(ifname, "egw")
	#			data = data.rename("aet")

	#		# Define the path for the yearly NetCDF file
	#		fname_output = ifname.split('.')[0]+'_'+ifield+'.nc'
	#		
	#		# Group by year and create a new dataset for each year
	#		
	#		# loop over years
	#		data.to_netcdf(fname_output)
			

def get_percentiles_multi_files(model_path, model_name, start_year, end_year, season, variables, postpp_path):
	""" Get TWSA - total water storage anomalies form multiple netcdf files

	Parameters:
	-----------
	model_path: path (str)
		folder path of model outputs files
	model_name: str
		model name
	start_year: int
		starting year of the analysis
	end_year: int
		starting year of the analysis

	Returns
	-------

	"""
	#fname = get_name_list_historical_netcdf_files(model_path, model_name, start_year, end_year)
	
	# ==============================================================
	# DO NOT MODIFY FROM HERE -------------------------------------
	# get and save mean average values from netcdf
	#fname  = [
	#model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2023)
	#]

	#model_name = "IMERGba_sim0"

	# specified fields
	field = cuwalid.drop_false_keys(variables)


	#field = ['pre', 'pet',
	#	'aet', 'tht', 'egw',
	#	#'inf', 'run',
	#	'rch', 'fch', #'gdh',
	#	'dis', 'tls', 'wte',
	#	"twsc",
	#	]

	# loop over all specified variables
	q1 = 0.33
	q2 = 0.50
	q3 = 0.66

	#season = [None, 'MAM', 'OND']

	for iseason in season:
		
		first_read = True
		for ifield in field:
			
			# CHANGE NAMES TO ADD MORE VARIABLES
			# using anomalies
			if (ifield == "twsc") or (ifield == "wrsi"):# or (ifield == "flood"):
				fname = get_name_list_historical_netcdf_files(model_path, model_name,
												  start_year, end_year,
												  ifield=ifield
												  )

				#fname_list = [
				#	ifname.split('.')[0]+'_'+ifield+'.nc' for ifname in fname
				#	]

				# concatenate dataset at selected fields
				#data_concat = cuwalid.concatenate_netCDF(
				#	fname_list, ifield, agg="M", dim='time'
				#	)
			#elif ifield == "flood":
			#	fname = get_name_list_historical_netcdf_files(model_path, model_name,
			#									  start_year, end_year,
			#									  ifield=ifield
			#									  )
			else:# or (ifield == "flood")
				fname = get_name_list_historical_netcdf_files(model_path, model_name,
												  start_year, end_year)
	

			# concatenate dataset at selected fields
			if  ifield == "flood":
				data_concat = cuwalid.concatenate_netCDF(
						fname, ifield, agg="M", dim='time'
						)
				# rename variable
				data_concat = data_concat.rename('flood')

			else:
				data_concat = cuwalid.concatenate_netCDF(
						fname, ifield, agg="M", dim='time'
						)
			
			# accummulate dataset, just in case of TWSA
			if ifield == 'twsc':
				data_concat = data_concat.cumsum(dim='time')
			
			mean = False
			if (ifield == 'tht') or (ifield == 'wte'):
				mean = True
			
			if  ifield != "flood":
				if iseason is not None:
					# get seasson
					data_concat = data_concat.where(
						data_concat.time.dt.month.isin(
						cuwalid.season_name_to_number(iseason)))
				
			# resample dataset
			if  ifield == "flood":
				data_concat = cuwalid.resample_dataset(data_concat,
						extremes="max", delt='Y'
						)
			else:
				data_concat = cuwalid.resample_dataset(data_concat,
						mean=mean, delt='Y'
						)
			
			# calculate quantiles values of each variable, and store
			# it as dataset
			data_concat = xr.concat([data_concat.quantile(q1, dim='time'),
								data_concat.quantile(q2, dim='time'),
								data_concat.quantile(q3, dim='time')],
								dim="time")
			
			if first_read == True:
				dataset = data_concat.copy()
				first_read = False
			else:
				dataset = xr.merge([dataset, data_concat])
			
		# save as NETCDF files
		if iseason is None:
			#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
			fname_out = postpp_path+"netcdf/" + model_name + "_quantiles.nc"
		else:
			#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
			fname_out = postpp_path+"netcdf/" + model_name + '_' + iseason + "_quantiles.nc"
		
		cuwalid.save_xarray_dataset_as_netcdf(fname_out, dataset, field)

			
def get_extremes_quantiles_multi_netcdf(model_path, model_name, start_year, end_year, season, variables, postpp_path):
	""" Get TWSA - total water storage anomalies form multiple netcdf files

	Parameters:
	-----------
	model_path: path (str)
		folder path of model outputs files
	model_name: str
		model name
	start_year: int
		starting year of the analysis
	end_year: int
		starting year of the analysis

	Returns
	-------

	"""
	#fname = get_name_list_historical_netcdf_files(model_path, model_name, start_year, end_year)
	
			
	# ==============================================================
	# DO NOT MODIFY FROM HERE -------------------------------------
	# get and save mean average values from netcdf
	#fname  = [
	#model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2023)
	#]

	#model_name = "IMERGba_sim0"

	# specified fields
	field = cuwalid.drop_false_keys(variables)


	#field = ['pre', 'pet',
	#	'aet', 'tht', 'egw',
	#	#'inf', 'run',
	#	'rch', 'fch', #'gdh',
	#	'dis', #'tls', 'wte',
	#	"twsc",
	#	]

	# loop over all specified variables
	q1 = 0.33
	q2 = 0.50
	q3 = 0.66
	q4 = 0.05
	q5 = 0.95

	#season = [None, 'MAM', 'OND']
	#season = ['MAM']#, 'OND']

	for iseason in season:
		
		first_read = True
		for ifield in field:
			# CHANGE NAMES TO ADD MORE VARIABLES
			# using anomalies
			#fname_list = fname.copy()

			if (ifield == "twsc") or (ifield == "wrsi"):
				fname = get_name_list_historical_netcdf_files(model_path, model_name,
												  start_year, end_year,
												  ifield=ifield
												  )
			else:
				fname = get_name_list_historical_netcdf_files(model_path, model_name,
												  start_year, end_year)	

				#fname_list = [
				#	ifname.split('.')[0]+'_'+ifield+'.nc' for ifname in fname
				#	]
			
			# concatenate dataset at selected fields
			data_concat = cuwalid.concatenate_netCDF(
				fname, ifield, agg="M", dim='time'
				)
			
			## accummulate dataset, just in case of TWSA
			#if ifield == 'twsc':
			#	data_concat = data_concat.cumsum(dim='time')
			
			mean = False
			if (ifield == 'tht') or (ifield == 'wte'):
				mean = True
			
			if iseason is not None:
				# get seasson
				data_concat = data_concat.where(
					data_concat.time.dt.month.isin(
					cuwalid.season_name_to_number(iseason)))
				
			# resample dataset
			data_concat = cuwalid.resample_dataset(data_concat,
						mean=mean, delt='Y'
						)
			
			# calculate quantiles values of each variable, and store
			# it as dataset
			data_concat = xr.concat([
								data_concat.quantile(q1, dim='time'),
								data_concat.quantile(q2, dim='time'),
								data_concat.quantile(q3, dim='time'),
								data_concat.quantile(q4, dim='time'),
								data_concat.quantile(q5, dim='time')
								],
								dim="time")
			
			if first_read == True:
				dataset = data_concat.copy()
				first_read = False
			else:
				dataset = xr.merge([dataset, data_concat])
			
		# save as NETCDF files
		if iseason is None:
			#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
			fname_out = postpp_path+"netcdf/" + model_name + "_extremes_quantiles.nc"
		else:
			#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
			fname_out = postpp_path+"netcdf/" + model_name + '_' + iseason + "_extremes_quantiles.nc"
		
		cuwalid.save_xarray_dataset_as_netcdf(fname_out, dataset, field)

			
def get_average_multi_netcdf(model_path, model_name, start_year, end_year, season, variables, postpp_path):
	""" Get TWSA - total water storage anomalies form multiple netcdf files

	Parameters:
	-----------
	model_path: path (str)
		folder path of model outputs files
	model_name: str
		model name
	start_year: int
		starting year of the analysis
	end_year: int
		starting year of the analysis

	Returns
	-------

	"""
	fname = get_name_list_historical_netcdf_files(model_path, model_name, start_year, end_year)
	
	
	# get and save mean average values from netcdf
	#fname  = [
	#model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2023)
	#'/user/work/km19051/HAD_output/HAD_1k_10y_gw_ch_ksat_1_v2_IMERG_sim_28_grid.nc',
	#]

	#imodel = "IMERGba_sim0"

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#field = ['pre', 'pet',
	#	'aet', 'tht', 'egw',
	#	#'inf', 'run',
	#	'rch', 'fch', #'gdh',
	#	'dis', 'tls', 'wte',
	#	"twsc",
	#	]

	for iseason in season:
		# get average values for all variables from a list of netcdf files
		dataset = cuwalid.get_average_all_variables_from_list(fname, field, iseason)
		
		# save files
		#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
		#fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_" + imodel + "_mean.nc"
		if iseason is None:
			fname_out = postpp_path+"netcdf/" + model_name + "_mean.nc"
		else:
			fname_out = postpp_path+"netcdf/" + model_name + "_" + iseason + "_mean.nc"
		cuwalid.save_xarray_dataset_as_netcdf(fname_out, dataset, field)


def get_anomalies_multi_netcdf(model_path, model_name, start_year, end_year, season, variables, postpp_path):
	""" Get TWSA - total water storage anomalies form multiple netcdf files

	Parameters:
	-----------
	model_path: path (str)
		folder path of model outputs files
	model_name: str
		model name
	start_year: int
		starting year of the analysis
	end_year: int
		starting year of the analysis

	Returns
	-------

	"""
	fname = get_name_list_historical_netcdf_files(model_path, model_name, start_year, end_year)
	
	
	# ===============================================================

	# path of simulation files
	#fname  = [
	#	model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	#]

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
							cuwalid.season_name_to_number(iseason))
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

def get_monthly_average_multi_netcdf(model_path, model_name, start_year, end_year, variables, postpp_path):
	"""Function to ger files with monthly average values of each variable from
	multi-files model simulation
	Parameter
	---------
	
	Returns
	-------

		
	"""
	# get list of files
	fname = get_name_list_historical_netcdf_files(model_path, model_name, start_year, end_year)
	
	# specified fields
	field = cuwalid.drop_false_keys(variables)

	# loop through all months
	for imonth in range(1, 13):
		# Open the NetCDF file
		variables_file = list(xr.open_dataset(fname[0]).variables.keys())
		
		# get average values for all variables from a list of netcdf files
		#dataset = cuwalid.get_average_all_variables_from_list(fname, variables_file, imonth)
		dataset = cuwalid.get_average_all_variables_from_list(fname, field, imonth)
		
		## get average of additional files
		#if variables["wrsi"] is True:
		#	fname_aux = get_name_list_historical_netcdf_files(model_path, model_name,
		#										 start_year, end_year, ifield="wrsi")
		#	
		#	# get average values for all variables from a list of netcdf files
		#	dataset_aux = cuwalid.get_average_all_variables_from_list(fname_aux, ["wrsi"], imonth)
		#	
		#	dataset = xr.merge([dataset, dataset_aux])
		# save results
		fname_out = postpp_path+"netcdf/" + model_name + "_" + str(imonth) + "_monthly_mean.nc"
		cuwalid.save_xarray_dataset_as_netcdf(fname_out, dataset, field)

	return

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

def get_name_list_historical_netcdf_files(model_path, model_name, start_year, end_year, ifield=None):
	""" Get list of name of historical files when multiple files are
	are analysed

	Parameters:
	-----------
	model_path: path (str)
		folder path of model outputs files
	model_name: str
		model name
	start_year: int
		starting year of the analysis
	end_year: int
		starting year of the analysis

	Returns
	-------

	"""
	fname  = [
	#'/home/c1755103/HAD/HAD_output/HAD_IMERG_sim_28b_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2022)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2001, 2023)
	model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	]

	if ifield is not None:
		fname = [ifname.split('.')[0]+'_'+ifield+'.nc' for ifname in fname]
	
	#if ifield == "flood":
	#	fname = [ifname.split('.')[0]+'max.nc' for ifname in fname]
		
	return fname