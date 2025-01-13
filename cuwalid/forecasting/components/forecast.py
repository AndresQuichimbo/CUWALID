import cuwalid.tools.CUWALID_mfile_tools as cuwalid
import geopandas as gpd
import numpy as np
import xarray as xr
import pandas as pd
import os

def get_tercile_hindcast_fluxes(model_path, model_name, season, variables, postpp_path):
	"""This function calculates the probabilistic forecasting using the tercile approach
	"""
	iyear = 2022
	#ivar = "dis"
	#iseason = "MAM"
	#iseason = "OND"

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#season = ["MAM", "OND"]


	fname_var = model_path+model_name+"_YYYY_grid_VVV.nc"
	fname_threshold = postpp_path+"netcdf/" + model_name + "_SSS_quantiles.nc"
	#fname_threshold = postpp_path+"netcdf/" + model_name + "_SSS_extremes_quantiles.nc"
	#fname_var = "/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_YYYY_grid_VVV.nc"
	#fname_var = "/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_YYYY_grid.nc"
	#fname_threshold = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_SSS_quantiles.nc"
	#fname_q = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_mean.nc

	fname_var = fname_var.replace("YYYY", str(iyear))

	for iseason in season:
		#for ivar in ["dis", "twsc", "tht", "wrsi"]:
		for ivar in field:
			# choose path depending on variable
			if (ivar == "twsc") or (ivar == "wrsi"):
				ifname = fname_var.replace("VVV", ivar)
			else:
				ifname = fname_var.replace("_VVV", "")
			
			# chose path depending on the season
			if iseason is None:
				ifname_threshold = fname_threshold.replace("_SSS", "")
			else:
				ifname_threshold = fname_threshold.replace("SSS", iseason)
						
			# specify path for dataset
			#netcdf_path = "D:/HAD/output/HAD_IMERGb_sim_"+ str(iyear)+"_grid.nc"
			
			# specify paht for threshold dataset
			#nc_path_threshold = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_quantiles.nc"
			
			# get tercile forecasting
			tercile = cuwalid.get_tercile_probabilities_from_netcdf(ifname, ifname_threshold,
					var=ivar, season=iseason)
			
			# save as NETCDF files
			if iseason is None:
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
			else:
				#fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_"+ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
				#fname = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast.nc"
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
			
			# save probabilistic forecast as netcdf
			tercile.to_netcdf(fname_out)

def get_tercile_hindcast_extreme_values(model_path, model_name, season, variables, postpp_path):
	"""This function calculates the probabilistic forecasting using the tercile approach
	"""
	iyear = 2022
	#ivar = "dis"
	#iseason = "MAM"
	#iseason = "OND"

	# specified fields
	#field = cuwalid.drop_false_keys(variables)

	fname_var = model_path+model_name+"_YYYY_grid_VVV.nc"
	#fname_threshold = postpp_path+"netcdf/" + model_name + "_SSS_extremes_quantiles.nc"
	fname_threshold = postpp_path+"netcdf/" + model_name + "_SSS_quantiles.nc"

	#fname_var = "/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_YYYY_grid_VVV.nc"
	#fname_var = "/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_YYYY_grid.nc"
	#fname_threshold = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_SSS_quantiles.nc"
	#fname_q = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_mean.nc

	fname_var = fname_var.replace("YYYY", str(iyear))

	#var = ["dis", "twsc", "tht"]
	#var = ["dis"]#, "twsc", "tht"]
	field = cuwalid.drop_false_keys(variables)

	for iseason in season:
		for ivar in field:
			# choose path depending on variable
			if ivar == "twsc":
				ifname = fname_var.replace("VVV", ivar)
			else:
				ifname = fname_var.replace("_VVV", "")
			
			# chose path depending on the season
			if iseason is None:
				ifname_threshold = fname_threshold.replace("_SSS", "")
			else:
				ifname_threshold = fname_threshold.replace("SSS", iseason)
						
			# specify path for dataset
			#netcdf_path = "D:/HAD/output/HAD_IMERGb_sim_"+ str(iyear)+"_grid.nc"
			
			# specify paht for threshold dataset
			#nc_path_threshold = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_quantiles.nc"
			
			# get tercile forecasting
			tercile = cuwalid.get_tercile_probabilities_from_netcdf(ifname, ifname_threshold,
					var=ivar, season=iseason, idtercile=[3, 4], extremes="max")
			
			# save as NETCDF files
			if iseason is None:
				#fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
				fname_out = postpp_path+"netcdf/" + model_name + "_flow_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
			
			else:
				#fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_"+ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
				#fname = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast.nc"
				#fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
				fname_out = postpp_path+"netcdf/" + model_name + "_flow_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
			
			# save probabilistic forecast as netcdf
			tercile.to_netcdf(fname_out)

def extract_forecasting_variable(model_name,
								#model_path,
								plot_scale,
								season, variables,
								postpp_path,
								netcdf_path_list,
								shapefile_path,
								place_name,
								place_code,
								icode_field_shp,
								iname_field_shp,
								save_nc=False,
								iyear=2022
								):

	"""Function to get a set netCDF files for each place listed in place_name
	Each file is cliped only for the area whithin the boundaries of each place
	
	Parameters:
	-----------
	model_name: str
	model_path: str
	plot_scale: str
	season: list
	variables: list
	postpp_path: str
	netcdf_path: str
	shapefile_path: str
	place_name: list
	name_field_shp: str

	plot_scales : list of str, optional
		A list of zoom levels or plot scales for the maps (e.g., "Zoom", "National", "Regional").
		Defaults to ["Zoom"].
		
	country_name : str, optional
		The name of the country for which the maps are being generated. Defaults to "Kenya".
		
	place_names : list of str or [None], optional
		A list of specific places (e.g., counties) for which maps will be created.
		If [None], maps will be created for all counties in the country. Defaults to [None].
		
	seasons : list of str, optional
		A list of seasons for which the maps will be generated. Examples include "MAM" (March-April-May) 
		and "OND" (October-November-December). Defaults to ["MAM"].
		
	water_status : list of str, optional
		Water condition or status, such as "Flood", "Drought", etc. Defaults to ["Flood"].
		
	year : int, optional
		The year for which the maps are generated. Defaults to 2010.
		
	output_dir : str, optional
		The directory where the generated maps will be saved. Defaults to "output".
		
	language : str, optional
		The language for the map labels and outputs. Defaults to "English".
		
	netcdf_path : str, optional
		Path to the NetCDF file containing climate or forecast data. Defaults to None.
		
	threshold_path : str, optional
		Path to the threshold file used to determine warning or risk levels. Defaults to None.
		
	mask_path : str, optional
		Path to the file containing mask data for areas that should be excluded from the maps.
		Defaults to None.
		
	river_path : str, optional
		Path to the file containing river data to be overlaid on the map. Defaults to None.

	shape_path : str, optional
		Path to the optional shape file to overide built in shape files for HAD region. Defaults to None.

	
	Returns
	-------

	
	"""
	# PLOT TYPE
	#plot_scale = "Country"
	#plot_scale = "County"
	#plot_scale = "Ward"

	# SELECT WARD
	#place_name = "Isiolo"
	#place_name = "Meru"
	#place_name = "Samburu"
	#place_name = "Laikipia"
	#place_name = "Kinna"
	#place_name = "Burat"
	#place_name = "Somalia"
	#place_name = "Kenya"

	#place_name = {
	#	"Isiolo",
	#	"Meru",
	#	"Samburu",
	#	"Laikipia",
	#	}

	# SELCT TIME STEP TO PRINT AS EXAMPLE
	#time_plot = 15 # Example contain only 24 months

	## do not change this
	#name_field_shp = {
	#	"Zoom": "IEBC_WARDS",
	#	"Ward": "IEBC_WARDS",
	#	"County": "county",
	#	"Country": "NAME",	
	#	}

	#var = ["dis", "twsc", "tht", "wrsi", "flow"]
	#field = cuwalid.drop_false_keys(variables)
	field = variables
	#print(plot_scale, name_field_shp)
	#iname_field_shp = name_field_shp[plot_scale]

	# SPECIFY PATHS - GEOGRAPHICAL UNITS WGS64
	# Load the polygon shapefile using geopandas
	#shapefile_country = "D:/HAD/data/gis/Horn_Africa/Horn_africa_contry.shp"
	#shapefile_county = 'D:/kenya/GIS/kenya-county/ke_county.shp'

	#shapefile_country = "/home/c1755103/WS/HAD/Data/gis/wgs84/Horn_africa_contry.shp"
	#shapefile_path = "/home/c1755103/WS/HAD/Data/gis/wgs84/kenya/kenya-county/ke_county.shp"

	#netcdf_path = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast.nc"
	#"/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_"+ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
	#netcdf_path = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_VVV_SSS_2022_probabilistic_tercile_forecast.nc"
	
	# list of labels for of the terciles
	tercile = ["AN", "NN", "BN"]
	#print(season, place_code, place_name)

	for iseason in season:
		# create list to store data
		# name list
		#fname = []
		# season list
		season_list = []
		# store variable
		variable_list = []
		# store place name
		place_list = []
		# store place name
		code_list = []
		# water status
		status_list = []
		# name code list
		code_name_list = []		
		# loop over list of files
		area_list = []
	
		for iplace_name, iplace_code in zip(place_name, place_code):
			# field should match the list of netCDF files
			for ivar, inetcdf_path in zip(field, netcdf_path_list):
				# read shapefile and select area/region
				if plot_scale == "County":
					region = gpd.read_file(shapefile_path)
				#print(shapefile_path, iname_field_shp)
				#print(region)
				if iplace_code is None:
					region = region[(region[iname_field_shp] == iplace_name)]
				else:
					region = region[(region[icode_field_shp] == iplace_code)]
				#print(region, iplace_code, iplace_name)
				if len(region) > 0:
					# chose path depending on the season
					if iseason is None:
						inetcdf_path = inetcdf_path.replace("_SSS", "")
					else:
						inetcdf_path = inetcdf_path.replace("SSS", iseason)

					#print(iplace_code, iplace_name)
					#print(len(region.index), iplace_code, iplace_name)
					#print(region, iplace_code)
					#print(inetcdf_path)
					inetcdf_path = inetcdf_path.replace("VVV", ivar)
					dataset = cuwalid.extract_dataset(inetcdf_path, region)
					#print(region, iplace_code)

					if save_nc is True:
						# save dataset as netcdf
						fname_nc = os.path.join(
							postpp_path,
							"netcdf",
							f"{model_name}_{iseason}_{iplace_name}_{ivar}_probabilistic_tercile_forecast_region.nc"
						)

						#fname = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast_region.nc"

						dataset.to_netcdf(fname_nc)

					# store season
					season_list.append(iseason)
					# store variable
					variable_list.append(ivar)
					# store place name
					place_list.append(iplace_name)
					# store place name
					code_list.append(iplace_code)
					# store code name list
					code_name_list.append(model_name+"_"+str(iplace_code))

					# CALUCATE AREAS FOR EACH TERCILE
					area = []
					for itercile in tercile:
						# read tercile
						#data = read_dataset(ifname, var_name=itercile).values
						data = dataset[itercile].values
						# count terciles with higher probability
						data[data > 0.33] = 1
						data[data <= 0.33] = 0
						# create list areas
						area.append(np.nansum(data))

					# calculate percentages
					area_list.append(area*1/np.sum(area))

					# get status value
					if ivar == "Flood":
						status_list.append(2-area.index(max(area)))
					else:
						status_list.append(area.index(max(area)))

				
			# change to numpy array
			area = np.array(area_list)
			# save as dataframe


		# create dataframe of contributin areas
		df = pd.DataFrame()
		df["name"] = code_name_list
		df["place"] = place_list
		df["season"] = season_list
		df["variable"] = variable_list
		df["status"] = status_list
		for i, itercile in enumerate(tercile):
			df[itercile] = area[:, i]

		fname = os.path.join(
			postpp_path,
			"csv",
			f"{model_name}_{iseason}_{iyear}_county_areas.csv"
		)
		df.to_csv(fname, index=False)
				

def read_dataset(fname, var_name='tht'):
	# Open the first netCDF file
	# output dataset
	data = xr.open_dataset(fname)
	data = data[var_name]
	return data


def get_areas_terciles(model_path, model_name, season, variables, postpp_path):
	"""Function to extract values form selected areas
	
	Parameters
	----------
	model_path: str
		paht for model netcdf file
	model_name: str
		model name
	season: str
		season eg. OND
	variables: str
		variables to plot
	postpp_path: str
		paht for storing outputs

	Returns
	-------
	
	"""
		
	# ==================================================

	#fname = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast_region.nc"
	#fname = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_MAM_Laikipia_dis_2022_probabilistic_binary_forecast_region.nc"
	tercile = ["AN", "NN", "BN"]
	#tercile = ["AN", "BN"]

	place_name = {
		"Isiolo",
		"Meru",
		"Samburu",
		"Laikipia",
		}

	# create list of names
	#var = ["dis", "twsc", "tht", "wrsi", "flow"]
	field = cuwalid.drop_false_keys(variables)

	# name list
	fname = []
	# season list
	season_list = []
	# store variable
	variable_list = []
	# store place name
	place_list = []

	# create list of names and places
	for iseason in season:
		for iplace_name in place_name:
			for ivar in field:
				# create name
				fname.append(postpp_path + "netcdf/" +
						model_name + "_" +
						iseason +"_"+iplace_name+"_"+ivar+
						"_probabilistic_tercile_forecast_region.nc"
						)
				# store season
				season_list.append(iseason)
				# store variable
				variable_list.append(ivar)
				# store place name
				place_list.append(iplace_name)
				
	# CALUCATE AREAS FOR EACH TERCILE
	# loop over list of files
	area_list = []
	for ifname in fname:
		# read dataset and extract selected tercile
		area = []
		for itercile in tercile:
			# read tercile
			data = read_dataset(ifname, var_name=itercile).values
			# count terciles with higher probability
			data[data > 0.33] = 1
			data[data <= 0.33] = 0
			# create list areas
			area.append(np.nansum(data))
		
		# calculate percentages
		area_list.append(area*1/np.sum(area))
		
	# change to numpy array
	area = np.array(area_list)
	# save as dataframe


	# create dataframe of contributin areas
	df = pd.DataFrame()
	df["place"] = place_list
	df["season"] = season_list
	df["variable"] = variable_list
	for i, itercile in enumerate(tercile):
		df[itercile] = area[:, i]

	fname = postpp_path + "csv/" + model_name+"_county_areas.csv"
	df.to_csv(fname)
	#print(area)
	

def get_update_TWSA(model_path, model_name, iyear=2022):

    # Path of model output files
    #model_path = "D:\HAD\training\forecast\regional\outputs/"
    #model_path = "/home/c1755103/HAD/HAD_output/"
    #model_path = "/home/cuwalid/training/historical/regional/outputs/"#_13_grid.nc

    # path for post processing files, i.g. forecasting
    # Specific folders will be created inside this paht to store different
    # types of lie formats
    # /fig: for any king of figure
    # /netcdf: for *.nc files
    # /raster: for *.asc files
    # /csv: for comma delimited files, i.g. *.csv
    #postpp_path = "D:\HAD\training\forecast\regional\postpp/"
    #postpp_path = "/home/c1755103/HAD/HAD_postpp/"
    #postpp_path = "/home/cuwalid/training/historical/regional/postpp/"

    #iyear = 2022

    ifield = "twsc"
	
    # specify current simulation path
    #fname_current = model_path+model_name+'_grid.nc'# comment this line for yearly data
    fname_current = model_path+model_name+"_"+ str(iyear-1) +'_grid.nc' # imcomment this line for yealy data

	# check the most current year
    #current_year = 0
    #available_year = False
    #while available_year:
    #    if os.path.exists(fname_current):
    #        available_year = True
    #    else:
    #        iyear = iyear-1
    #        fname_current = model_path+model_name+"_"+ str(iyear-1) +'_grid.nc' # imcomment this line for yealy data
    #        current_year += 1


    # specify previous TWSC accumulated
    fname_previous = model_path+model_name+"_"+ str(iyear-1) +'_grid_twsc.nc'

    # read dataset
    data_current = cuwalid.read_dataset(fname_current, var_name='twsc')

    data_previous = cuwalid.read_dataset(fname_previous, var_name='twsc')

    # Update datasets
    data = cuwalid.update_TWSA(data_current, data_previous)

    # save dataset as netcdf file
    fname_current = fname_current.split('.')[0]+'_'+ifield+'.nc'

    data.to_netcdf(fname_current)
	

def get_updated_TWSA_ensamble(model_path, model_name, model_name_historical, postpp_path_historical, season=None, iyear=2022, nsim=30):
	"""This function
	
	Parameters
    ----------
    model_path : str
        Path to the directory containing the model data.
    model_name : str
        Name of the model to retrieve forecasts from.
    season : str
        Season for which the forecasts are required (e.g., 'OND', 'MAM').
    variables : list of str
        List of variable names to include in the forecast (e.g., ['pet', 'pre']).
    postpp_path : str
        Path to the post-processing configuration or scripts.
    threshold_path : str
        Path to the file containing threshold values for the variables.

    Returns
    -------
    xarray
        A dictionary containing processed deterministic forecasts for each ensemble member. The structure 
        typically includes ensemble members, their corresponding forecasts, and any additional post-processed 
        data.

    Notes
    -----
    - Ensure that the `model_path` contains the necessary data files for the specified `model_name`.
    - The `postpp_path` should point to valid configurations or scripts for applying post-processing methods.
    - Thresholds provided in `threshold_path` should match the variables specified.

    Examples
    --------
    >>> forecasts = get_deterministic_forecast_ensemble(
    ...     model_path="/data/models/",
    ...     model_name="GFS",
    ...     season="OND",
    ...     variables=["pre", "pet"],
    ...     postpp_path="/config/postprocessing/",
    ...     threshold_path="/config/thresholds/"
    ... )
    >>> print(forecasts["mean"])
    [0.5, 0.2, 0.8]
	
	
	"""
	# get initial initial conditions for TWSA
	imonth = cuwalid.season_name_to_number(season)[0]-1
	if imonth == 0:
		imonth = 12
	# Specify model name, This will be the root name for the forecasting
	#model_name = "HAD_IMERGba_sim0"

	# model name previous step
	#model_name_historical = "HAD_IMERGba_sim0_2022_ini_MAM"


	# Path of model output files
	#model_path = "D:\HAD\training\forecast\regional\outputs/"
	#model_path = "/home/c1755103/HAD/HAD_output/"
	#model_path = "/home/cuwalid/training/historical/regional/outputs/"#_13_grid.nc
	#model_path_previous = "/home/cuwalid/training/historical/regional/outputs/"#_13_grid.nc

	# path for post processing files, i.g. forecasting
	# Specific folders will be created inside this paht to store different
	# types of lie formats
	# /fig: for any king of figure
	# /netcdf: for *.nc files
	# /raster: for *.asc files
	# /csv: for comma delimited files, i.g. *.csv
	#postpp_path = "D:\HAD\training\forecast\regional\postpp/"
	#postpp_path = "/home/c1755103/HAD/HAD_postpp/"
	#postpp_path = "/home/cuwalid/training/historical/regional/postpp/"

	#iyear = 2022

	#nsim = 30
	nini = 0
	ifield = "twsc"
	# specify previous TWSC accumulated
	#fname_previous = model_path+model_name+"_"+ str(iyear-1) +'_grid_twsc.nc'
	#fname_previous = model_path_historical+model_name_historical+'_grid_twsc.nc'
	#fname_previous = model_path_historical+model_name_historical+"_"+ str(iyear-1) +'_grid_twsc.nc'
	#fname_current = fname_current.split('.')[0]+'_'+ifield+'.nc'
	fname_previous = postpp_path_historical+"netcdf/" + model_name_historical + "_" + str(imonth) + "_monthly_mean.nc"

	# check the most current year
	fname  = [
	model_path+model_name+"_"+ str(isim) +'_grid.nc' for isim in range(nini, nsim)
	]

	data_previous = cuwalid.read_dataset(fname_previous, var_name='twsc')

	for ifname_ensamble in fname:#for isim in range(nsim):
		# test if file exist
		if os.path.exists(ifname_ensamble):
			# specify current simulation path
			#fname_current = model_path+model_name+"_"+ str(iyear-1) +'_grid.nc'

			# read dataset
			data_current = cuwalid.read_dataset(ifname_ensamble, var_name='twsc')

			# Update datasets
			data = cuwalid.update_TWSA(data_current, data_previous)

			# save dataset as netcdf file
			fname_current = ifname_ensamble.split('.')[0]+'_'+ifield+'.nc'

			data.to_netcdf(fname_current)
		else:
			print(ifname_ensamble+" File does not found, skip this file from the analysis")
# ==============================================================
def get_ensamble_forecasting(model_path, model_name, variables, season, postpp_path, nsim=30):
	"""This funtion create an ensamble of model simulation for each
	variable especify in the 'config_forecasting.py' file.

	WARNING! Values of total water storage needs to be updated for
	all the simulations

	Parameters
    ----------
    model_path : str
        Path to the directory containing the model data.
    model_name : str
        Name of the model to retrieve forecasts from.
    season : str
        Season for which the forecasts are required (e.g., 'OND', 'MAM').
    variables : list of str
        List of variable names to include in the forecast (e.g., ['pet', 'pre']).
    postpp_path : str
        Path to the post-processing configuration or scripts.

    Returns
    -------
    xarray
        A dictionary containing processed deterministic forecasts for each ensemble member. The structure 
        typically includes ensemble members, their corresponding forecasts, and any additional post-processed 
        data.

    Notes
    -----
    - Ensure that the `model_path` contains the necessary data files for the specified `model_name`.
    - The `postpp_path` should point to valid configurations or scripts for applying post-processing methods.
    - Thresholds provided in `threshold_path` should match the variables specified.

    Examples
    --------
    >>> forecasts = get_deterministic_forecast_ensemble(
    ...     model_path="/data/models/",
    ...     model_name="GFS",
    ...     season="OND",
    ...     variables=["pre", "pet"],
    ...     postpp_path="/config/postprocessing/",
    ...     threshold_path="/config/thresholds/"
    ... )
    >>> print(forecasts["mean"])
    [0.5, 0.2, 0.8]

	"""

	#model_name = "MAM_2022_realization"

	#model_path = "/home/cuwalid/training/forecast/regional/outputs/"#_13_grid.nc

	#postpp_path = "/home/cuwalid/training/forecast/regional/postpp/"

	#nsim = 30
	# get and save mean average values from netcdf
	nini = 0

	fname  = [
	model_path+model_name+"_"+ str(isim) +'_grid.nc' for isim in range(nini, nsim)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2023)
	#'/user/work/km19051/HAD_output/HAD_1k_10y_gw_ch_ksat_1_v2_IMERG_sim_28_grid.nc',
	]

	#season = ["MAM"]#, "OND"]

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#field = [#'pre', 'pet',
	#	#'aet', 'tht', 'egw',
	#	#'inf', 'run',
	#	#'rch', 'fch', #'gdh',
	#	#'dis',
	#	'tls',# 'wte',
	#	#"twsc",
	#	]

	for iseason in season:
		for ivar in field:
			
			fname_list = fname.copy()
			# check if is the riparian area
			if (ivar == 'fch') or (ivar == 'tls') or (ivar == 'ssz'):
				fname_list = [
					ifname.split('.')[0]+'rp.nc' for ifname in fname_list
					]
					
			if (ivar == 'twsc') or (ivar == 'wrsi'):# or (ivar == 'ssz'):
				fname_list = [
					ifname.split('.')[0]+'_'+ivar+'.nc' for ifname in fname_list
					]
			#print(fname_list)
			mean = False
			if (ivar == 'tht') or (ivar == 'wte'):
				mean = True
			# get average values for all variables from a list of netcdf files
			dataset = cuwalid.get_ensamble_from_netcdf_list(fname_list,
									ivar, mean=mean,
									delta=None, season=iseason,
									fname_output=None)
		
			# save files
			#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
			#fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_" + imodel + "_mean.nc"
			if iseason is None:
				fname_out = postpp_path+"netcdf/" + model_name + "_" + ivar + "_ensamble.nc"
			else:
				fname_out = postpp_path+"netcdf/" + model_name + "_" + iseason + "_" + ivar +"_ensamble.nc"
			#cuwalid.save_xarray_dataset_as_netcdf(fname_out, dataset, field)
			dataset.to_netcdf(fname_out)

def get_postprocessed_variables_forecast(model_path, model_name, nsim=30):
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
	nini = 0

	fname  = [
	model_path+model_name+"_"+ str(isim) +'_grid.nc' for isim in range(nini, nsim)
	]

	# specified fields
	#field = cuwalid.drop_false_keys(variables)
	field = ["wrsi", "aet"]
	for ivar in field:
		
		fname_list = fname.copy()
		# check if is the riparian area
		if (ivar == 'fch') or (ivar == 'tls') or (ivar == 'ssz'):
			fname_list = [
				ifname.split('.')[0]+'rp.nc' for ifname in fname_list
				]
				
		if (ivar == 'twsc') or (ivar == 'wrsi'):# or (ivar == 'ssz'):
			fname_list = [
				ifname.split('.')[0]+'_'+ivar+'.nc' for ifname in fname_list
				]

	# DO NOT MODIFY FROM HERE ---------------------------------------
	cuwalid.get_postprocessed_hydro_variables_mfiles(fname)


def get_probabilistic_tercile_forecast_ensamble(model_path, model_name, season, variables, postpp_path, threshold_path, iyear=2022):
	"""This function calculates the probabilistic forecasting using the tercile approach

	Parameters
    ----------
    model_path : str
        Path to the directory containing the model data.
    model_name : str
        Name of the model to retrieve forecasts from.
    season : str
        Season for which the forecasts are required (e.g., 'OND', 'MAM').
    variables : list of str
        List of variable names to include in the forecast (e.g., ['pet', 'pre']).
    postpp_path : str
        Path to the post-processing configuration or scripts.
    threshold_path : str
        Path to the file containing threshold values for the variables.

    Returns
    -------
    xarray
        A dictionary containing processed deterministic forecasts for each ensemble member. The structure 
        typically includes ensemble members, their corresponding forecasts, and any additional post-processed 
        data.

    Notes
    -----
    - Ensure that the `model_path` contains the necessary data files for the specified `model_name`.
    - The `postpp_path` should point to valid configurations or scripts for applying post-processing methods.
    - Thresholds provided in `threshold_path` should match the variables specified.

    Examples
    --------
    >>> forecasts = get_deterministic_forecast_ensemble(
    ...     model_path="/data/models/",
    ...     model_name="GFS",
    ...     season="OND",
    ...     variables=["pre", "pet"],
    ...     postpp_path="/config/postprocessing/",
    ...     threshold_path="/config/thresholds/"
    ... )
    >>> print(forecasts["mean"])
    [0.5, 0.2, 0.8]

	"""
	#model_name = "MAM_2022_realization"

	#iyear = 2022
	#ivar = "dis"
	#iseason = "MAM"
	#iseason = "OND"

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#season = ["MAM", "OND"]
	#season = ["MAM"]

	#model_path = "/home/cuwalid/training/forecast/regional/outputs/"#_13_grid.nc

	#postpp_path = "/home/cuwalid/training/forecast/regional/postpp/"

	fname_ensamble = postpp_path+"netcdf/" + model_name + "_SSS_VVV_ensamble.nc"

	# filename path of threshold
	#threshold_path = "/home/cuwalid/training/historical/regional/postpp/netcdf/HAD_IMERGba_sim0_MAM_extremes_quantiles.nc"
	#threshold_path = threshold_path+"HAD_IMERGba_sim0_MAM_extremes_quantiles.nc"


	#fname_var = fname_var.replace("YYYY", str(iyear))
	for iseason in season:
		#for ivar in ["dis", "twsc", "tht", "wrsi"]:
		for ivar in field:
			## choose path depending on variable
			#if (ivar == "twsc") or (ivar == "wrsi"):
			#	ifname = fname_ensamble.replace("VVV", ivar)
			#else:
			#	ifname = fname_ensamble.replace("_VVV", "")
			
			# chose path depending on the season
			#fname_threshold = threshold_path.copy()
			if iseason is None:
				ifname_threshold = threshold_path.replace("_SSS", "")
				ifname = fname_ensamble.replace("_VVV", "")
				ifname = ifname.replace("_SSS", "")
			else:
				ifname_threshold = threshold_path.replace("SSS", iseason)
				ifname = fname_ensamble.replace("VVV", ivar)
				ifname = ifname.replace("SSS", iseason)
						
			# specify path for dataset
			#netcdf_path = "D:/HAD/output/HAD_IMERGb_sim_"+ str(iyear)+"_grid.nc"
			
			# specify paht for threshold dataset
			#nc_path_threshold = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_quantiles.nc"
			
			# get tercile forecasting
			tercile = cuwalid.get_tercile_probabilities_from_ensamble_netcdf(
					ifname, ifname_threshold,
					var=ivar, season=iseason)
			
			# save as NETCDF files
			if iseason is None:
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
			else:
				#fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_"+ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
				#fname = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast.nc"
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
			
			# save probabilistic forecast as netcdf
			tercile.to_netcdf(fname_out)
			

def get_deterministic_forecast_ensamble(model_path, model_name, season, variables, postpp_path, threshold_path, iyear=2022):
	"""This function calculates the probabilistic forecasting using the tercile approach
	from the ensamble dataset. It will create a file for each analised variable

	Parameters
    ----------
    model_path : str
        Path to the directory containing the model data.
    model_name : str
        Name of the model to retrieve forecasts from.
    season : str
        Season for which the forecasts are required (e.g., 'OND', 'MAM').
    variables : list of str
        List of variable names to include in the forecast (e.g., ['pet', 'pre']).
    postpp_path : str
        Path to the post-processing configuration or scripts.
    threshold_path : str
        Path to the file containing threshold values for the variables.

    Returns
    -------
    xarray
        A dictionary containing processed deterministic forecasts for each ensemble member. The structure 
        typically includes ensemble members, their corresponding forecasts, and any additional post-processed 
        data.

    Notes
    -----
    - Ensure that the `model_path` contains the necessary data files for the specified `model_name`.
    - The `postpp_path` should point to valid configurations or scripts for applying post-processing methods.
    - Thresholds provided in `threshold_path` should match the variables specified.

    Examples
    --------
    >>> forecasts = get_deterministic_forecast_ensemble(
    ...     model_path="/data/models/",
    ...     model_name="GFS",
    ...     season="OND",
    ...     variables=["pre", "pet"],
    ...     postpp_path="/config/postprocessing/",
    ...     threshold_path="/config/thresholds/"
    ... )
    >>> print(forecasts["mean"])
    [0.5, 0.2, 0.8]

	"""

	#iyear = 2022

	#season = ["MAM", "OND"]
	#ivar = "dis"
	#iseason = "MAM"
	#iseason = "OND"

	# model name
	#model_name = "MAM_2022_realization"

	# list of season to calculate
	#season = ["MAM"]

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	# model simulation results path
	#model_path = "/home/cuwalid/training/forecast/regional/outputs/"#_13_grid.nc

	# path of postprocessing
	#postpp_path = "/home/cuwalid/training/forecast/regional/postpp/"

	# get ensamble name
	fname_ensamble = postpp_path+"netcdf/" + model_name + "_SSS_VVV_ensamble.nc"

	# filename path of threshold
	#threshold_path = "/home/cuwalid/training/historical/regional/postpp/netcdf/HAD_IMERGba_sim0_SSS_mean.nc"

	# replace year
	#postpp_path = postpp_path.replace("YYYY", str(iyear))
	#threshold_path = threshold_path.replace("YYYY", str(iyear))

	for iseason in season:
		#for ivar in ["dis", "twsc", "tht", "wrsi"]:
		for ivar in field:
			## choose path depending on variable
			#if (ivar == "twsc") or (ivar == "wrsi"):
			#	ifname = fname_ensamble.replace("VVV", ivar)
			#else:
			#	ifname = fname_ensamble.replace("_VVV", "")
			
			# chose path depending on the season
			#fname_threshold = threshold_path.copy()
			if iseason is None:
				ifname_threshold = threshold_path.replace("_SSS", "")
				ifname = fname_ensamble.replace("_VVV", "")
				ifname = ifname.replace("_SSS", "")
			else:
				ifname_threshold = threshold_path.replace("SSS", iseason)
				ifname = fname_ensamble.replace("VVV", ivar)
				ifname = ifname.replace("SSS", iseason)
						
			# get mean values
			mean = cuwalid.read_dataset(ifname, var_name=ivar).mean(dim="sim")
			mean = mean.rename("average")
			#print(mean)
			#print(cuwalid.read_dataset(ifname_threshold, var_name=ivar))
			# get anomaly
			anomaly = mean - cuwalid.read_dataset(ifname_threshold, var_name=ivar)
			anomaly = anomaly.rename("anomaly")
			#print(anomaly)
			# get variability
			std = cuwalid.read_dataset(ifname, var_name=ivar).std(dim="sim")
			std = std.rename("Variability")
			#print(std)
			# store all variables in one netcdf file
			det_forecast = xr.merge([mean, anomaly, std])
			
			# save as NETCDF files
			if iseason is None:
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+str(iyear)+"_deterministic_forecast.nc"
			else:
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_deterministic_forecast.nc"
			
			# save probabilistic forecast as netcdf
			det_forecast.to_netcdf(fname_out)