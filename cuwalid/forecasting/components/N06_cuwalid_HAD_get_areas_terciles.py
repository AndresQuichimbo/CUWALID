import numpy as np
import xarray as xr
import pandas as pd

def read_dataset(fname, var_name='tht'):
	# Open the first netCDF file
	# output dataset
	data = xr.open_dataset(fname)
	data = data[var_name]
	return data


def get_areas_terciles(model_path, model_name, season, postpp_path):
		
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
	var = ["dis", "twsc", "tht", "wrsi", "flow"]

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
			for ivar in var:
				# create name
				fname.append(postpp_path + "netcdf/" +
						model_name + "_" +
						iseason +"_"+iplace_name+"_"+ivar+
						"_2022_probabilistic_tercile_forecast_region.nc"
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