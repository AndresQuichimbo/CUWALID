import os
import sys
#import rasterio
from cuwalid.forecasting.components.default_parameter_dataset import *

class get_paths(object):
	"""Function to read all variables and path required for running the 
	impact based forecascasting component"""
	
	def __init__(self, plot_scale, region, country_name, iwater_status, iyear, iseason, shape_path=None, place_code_field=False, netcdf_path=None, threshold_path=None, river_path=None, mask_path=None):
		"""Initialize paths and variables name
		"""
		if shape_path == None:
			shapefile_country = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', shapefile_country_dic[region]))
			shapefile_county = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', shapefile_county_dic[country_name.lower()]))
			# rewrite
			if plot_scale == "Wards":
				shapefile_wards = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', shapefile_wards_dic[country_name.lower()]))
		else:
			if plot_scale == "County":
				shapefile_county = shape_path
			elif plot_scale == "Wards":
				shapefile_wards = shape_path
				
		# river shape file
		self.rivers_shapefile = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', rivers_shape_path))
		
		# load dataset of model outputs
		#netcdf_path = "forecasting_dataset/HAD/output/HAD_IMERGba_sim0_"+ str(iyear)+"_grid.nc"
		#netcdf_path = 'forecasting_dataset/HAD/output/HAD_IMERG_sim_ini_grid.nc'
		
		if netcdf_path == None:
			netcdf_path = default_netcdf.replace("YYYY", str(iyear))
		else:
			if "YYYY" in netcdf_path:
				netcdf_path = netcdf_path.replace("YYYY", str(iyear))
			else:
				print("The netcdf_path requires text 'YYYY' to replace with the the year being processed")
				sys.exit(1)
		
		if iwater_status == "Groundwater":
			var = "twsc"
			# If netcdf path is None use the default
			if netcdf_path == None:
				print("Using default netcdf path")
				netcdf_path = "forecasting_dataset/HAD/output/HAD_IMERGba_sim0_"+ str(iyear)+ "_grid_" + var + ".nc"
			else:
				netcdf_path.replace("YYYY", str(iyear))
		
		
		# load dataset for thresholds
		#nc_path_threshold = "forecasting_dataset/HAD/postpp/HAD_IMERGb_D2E_sim_" + iseason + "_quantiles.nc"
		if threshold_path == None:
			print("Using default threshold path")
			nc_path_threshold = "forecasting_dataset/HAD/postpp/HAD_IMERGb_D2E_sim_SSS".replace("SSS", iseason)
		else:
			if "SSS" in threshold_path:
				nc_path_threshold = threshold_path.replace("SSS", iseason)
			else:
				print("The threshold_path requires text 'SSS' to replace with the the year being processed")
				sys.exit(1)
		
		if (iwater_status == "Surface") or (iwater_status == "Flood"):
			nc_path_threshold = nc_path_threshold + "_flow_quantiles.nc"
		else:
			nc_path_threshold = nc_path_threshold + "_quantiles.nc"
		
		if mask_path == None:
			print("Using default mask path")
			mask_path = "forecasting_dataset\HAD\input_model\HAD_mask_utm_m.asc"
		#else:
		#	fmask = mask_path
		
		if river_path == None:
			print("Using default river path")
			river_path =  "forecasting_dataset\HAD\input_model\HAD_riv_length_utm.asc"
		#else:
		#	friver = river_path
		
		## Changing the country name depending on the country plotting. e.g. "kenya": "county"
		#name_field_shp["County"] = name_field_county_shp[country_name.lower()]
		
		# =========================================================
		# DO NOT CHANGE FROM THIS LINE
		# =========================================================
		# SPECIFY projection
		# define new projection (output) #!with.PYPROJ.library
		#netcdfPP = rasterio.crs.CRS.from_string(
		#"+proj=laea +lat_0=5 +lon_0=20 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
		#)
		# define current projection (input)
		#mapPP = 'EPSG:4326'
		# ===========================================================
		# READ DATA FROM REGIONAL DATASET FROM LOCAL REPO
		# ----------------------------------------------------------
		# load shapefiles
		# name field for shapefile
		name_field_name = {
			"Zoom" : name_field_county_shp,
			"County" : name_county_shp,
			#"Country" : name_field_county_shp,
			}
		name_field_code = {
			"Zoom" : name_field_county_shp,
			"County" : code_county_shp,
			#"Country" : name_field_county_shp,
			}
		
		# select the field to use as polygon attribute
		if place_code_field is False:
			self.iname_field_shp = name_field_name[plot_scale]
		else:		
			self.iname_field_shp = name_field_code[plot_scale]
		# additional files to plot as well as boundaries)
		# Select the ward that is requiested to plot
		if (plot_scale == "Zoom") or (plot_scale == "Ward"):
			self.fname_place = shapefile_wards
			#wards = gpd.read_file(shapefile_wards)
			#wards = wards[(wards["IEBC_WARDS"] == place_name)]
		elif plot_scale == "County":
			self.fname_place = shapefile_county
			#wards = gpd.read_file(shapefile_county)
			#wards = wards[(wards["county"] == place_name)]
		elif plot_scale == "Country":
			self.fname_place = shapefile_county
			#wards = gpd.read_file(shapefile_county)
			#wards = wards[(wards["NAME"] == place_name)]

		# store all variables in python object
		self.mask_path = mask_path
		self.river_path = river_path
		self.nc_path_threshold = nc_path_threshold
		self.netcdf_path = netcdf_path
		self.shapefile_country = shapefile_country