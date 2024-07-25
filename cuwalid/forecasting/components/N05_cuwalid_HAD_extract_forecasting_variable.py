#import numpy as np
#import xarray as xr
#import rasterio
import geopandas as gpd
#import rioxarray
import cuwalid.tools.CUWALID_forecast_tools as cuwalid

def extract_forecasting_variable(model_name, model_path, season, variables, postpp_path):

	# PLOT TYPE
	plot_scale = "Country"
	plot_scale = "County"
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

	place_name = {
		"Isiolo",
		"Meru",
		"Samburu",
		"Laikipia",
		}

	# SELCT TIME STEP TO PRINT AS EXAMPLE
	#time_plot = 15 # Example contain only 24 months

	# do not change this
	name_field_shp = {
		"Zoom": "IEBC_WARDS",
		"Ward": "IEBC_WARDS",
		"County": "county",
		"Country": "NAME",	
		}

	#var = ["dis", "twsc", "tht", "wrsi", "flow"]
	field = cuwalid.drop_false_keys(variables)
		
	iname_field_shp = name_field_shp[plot_scale]

	# SPECIFY PATHS - GEOGRAPHICAL UNITS WGS64
	# Load the polygon shapefile using geopandas
	#shapefile_country = "D:/HAD/data/gis/Horn_Africa/Horn_africa_contry.shp"
	#shapefile_county = 'D:/kenya/GIS/kenya-county/ke_county.shp'

	shapefile_country = "/home/c1755103/WS/HAD/Data/gis/wgs84/Horn_africa_contry.shp"
	shapefile_county = "/home/c1755103/WS/HAD/Data/gis/wgs84/kenya/kenya-county/ke_county.shp"

	#netcdf_path = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast.nc"
	#"/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_"+ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
	netcdf_path = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_VVV_SSS_2022_probabilistic_tercile_forecast.nc"
	for iseason in season:
		for iplace_name in place_name:
			for ivar in field:
				# read shapefile and select area/region
				if plot_scale == "County":
					region = gpd.read_file(shapefile_county)
					
				region = region[(region[iname_field_shp] == iplace_name)]
				
				# chose path depending on the season
				if iseason is None:
					inetcdf_path = netcdf_path.replace("_SSS", "")
				else:
					inetcdf_path = netcdf_path.replace("SSS", iseason)
				
				inetcdf_path = inetcdf_path.replace("VVV", ivar)
				dataset = cuwalid.extract_dataset(inetcdf_path, region)
				
				# save dataset as netcdf
				fname = (postpp_path + "netcdf/" +
						model_name + "_" +
						iseason +"_"+iplace_name+"_"+ivar+
						"_2022_probabilistic_tercile_forecast_region.nc"
						)
				#fname = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast_region.nc"
			
				dataset.to_netcdf(fname)