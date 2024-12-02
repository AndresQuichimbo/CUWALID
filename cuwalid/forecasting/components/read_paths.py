import os
import sys
import json

#import rasterio
import cuwalid.forecasting.components.default_parameter_dataset as default_dataset

class get_paths(object):
	"""Function to read all variables and path required for running the 
	impact based forecascasting component. This fuction first check if
	a set of datasets has been provided, otherwise it look at the default
	dataset (Africa region). All paths and variables available for the specied
	place are uploaded. The output python object is used in the impact_forecasting.py
	function"""
	
	def __init__(self, plot_scale, region, country_name, iwater_status,
			  iyear, iseason, shape_path_list=None, place_code_field=False,
			  netcdf_path=None, threshold_path=None, mask_path=None,
			  river_shapefile_path=None, river_path=None,# output_path=None,
			  ):
		"""Initialize paths and variables name

		Parameters
		----------
		plot_scale : str
		    The scale factor for plotting. Determines the zoom level or extent of the plot.
		region : str
		    The name of the geographical region to analyze or plot (e.g., "Europe", "Asia").
		country_name : str
		    The name of the specific country within the region to focus on (e.g., "France", "Kenya").
		iwater_status : str
		    A status indicator related to water, where the meaning of values is defined by the dataset.
		iyear : int
		    The year of the data to be processed or analyzed (e.g., 2023).
		iseason : str
		    The season of the data to be analyzed (e.g., "MAM", "OND").
		shape_path : str, optional
		    Path to the shapefile for geographical boundaries. Default is None.
		place_code_field : bool, optional
		    Indicates whether a place code field or name should be used for place names. Default is False.
		netcdf_path : str, optional
		    Path to the NetCDF file containing relevant data. Default is None.
		threshold_path : str, optional
		    Path to a file containing threshold values, used in analysis or visualization. Default is None.
		mask_path : str, optional
		    Path to the mask file to apply for filtering data or restricting the region. Default is None.
		river_path : str, optional
		    Path to the file containing river data, if applicable. Default is None.
		"""
		# read dataset from json file provided as shape_path
		dataset_list = read_dataset_list_json(shape_path_list)
		if shape_path_list is None:
			shapefile_country = os.path.abspath(
				os.path.join(os.path.dirname(__file__), '..', default_dataset.shapefile_country_dic[region]))
			
			shapefile_county = os.path.abspath(
				os.path.join(
					os.path.dirname(__file__), '..', default_dataset.shapefile_level_1_dic[country_name.lower()]))
			
			shapefile_level_2 = os.path.abspath(
				os.path.join(
					os.path.dirname(__file__), '..', default_dataset.shapefile_level_2_dic[country_name.lower()]))
			
			# rewrite
			if plot_scale == "Wards":
				shapefile_wards = os.path.abspath(
					os.path.join(
						os.path.dirname(__file__), '..', default_dataset.shapefile_wards_dic[country_name.lower()]))
				
			if mask_path is None:
				mask_path = os.path.abspath(
				os.path.join(
					os.path.dirname(__file__), '..', default_dataset.fname_mask_dic[iwater_status]))
				
		else:
			shapefile_country = default_dataset.shapefile_country_dic[region]
			
			if plot_scale == "County":
				#shapefile_county = shape_path
				shapefile_county = dataset_list.shapefile_level_1_dic[country_name.lower()]
			
			elif plot_scale == "Wards":
				#shapefile_wards = shape_path
				shapefile_wards = dataset_list.shapefile_wards_dic[country_name.lower()]
			
			shapefile_level_2 = dataset_list.shapefile_level_2_dic[country_name.lower()]

			if mask_path is None:
				mask_path = dataset_list.fname_mask_dic[iwater_status]
	
		# river shape file
		if river_shapefile_path is None:
			self.rivers_shapefile = os.path.abspath(
			os.path.join(os.path.dirname(__file__), '..', default_dataset.rivers_shape_path))
		else:
			self.rivers_shapefile = dataset_list.rivers_shape_path
		#print(self.rivers_shapefile)
		# load dataset of model outputs
		if netcdf_path is None:
			netcdf_path = default_dataset.default_netcdf.replace("YYYY", str(iyear))
		else:
			if "YYYY" in netcdf_path:
				netcdf_path = netcdf_path.replace("YYYY", str(iyear))
			#else:
			#	print("The netcdf_path requires text 'YYYY' to replace with the the year being processed")
			#	sys.exit(1)
		#print(netcdf_path)
		
		# read water status
		if iwater_status == "Groundwater":
			var = "twsc"
			# If netcdf path is None use the default
			if netcdf_path == None:
				print("Using default netcdf path")
				netcdf_path = "forecasting_dataset/HAD/output/HAD_IMERGba_sim0_"+ str(iyear)+ "_grid_" + var + ".nc"
			else:
				netcdf_path.replace("YYYY", str(iyear))

			if "YYYY" in netcdf_path:
				netcdf_path = netcdf_path.replace("YYYY", str(iyear))
		
		# load dataset for thresholds
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
		
		## read river mask
		#if river_path is None:
		#	print("Using default river path")
		#	river_path =  "forecasting_dataset\HAD\input_model\HAD_riv_length_utm.asc"
		##else:
		##	friver = river_path
		
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
			"Zoom" : default_dataset.name_field_county_shp,
			"County" : default_dataset.name_county_shp,
			#"Country" : name_field_county_shp,
			}
		name_field_code = {
			"Zoom" : default_dataset.name_field_county_shp,
			"County" : default_dataset.code_county_shp,
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
			self.shapefile_level_2 = None
			#wards = gpd.read_file(shapefile_wards)
			#wards = wards[(wards["IEBC_WARDS"] == place_name)]
		elif plot_scale == "County":
			self.fname_place = shapefile_county
			self.shapefile_level_2 = shapefile_level_2
			#wards = gpd.read_file(shapefile_county)
			#wards = wards[(wards["county"] == place_name)]
		elif plot_scale == "Country":
			self.fname_place = shapefile_county
			self.shapefile_level_2 = shapefile_level_2
			#wards = gpd.read_file(shapefile_county)
			#wards = wards[(wards["NAME"] == place_name)]

		# store all variables in python object
		self.mask_path = mask_path
		#self.river_path = river_path
		self.nc_path_threshold = nc_path_threshold
		self.netcdf_path = netcdf_path
		#print(shapefile_country)
		#self.shapefile_country = shapefile_country

class read_dataset_list_json(object):
	"""This function read the parameter_dataset_list from a json file, if json
	file not provided, default values from default_parameter_dataset.py are used
	"""
	def __init__(self, parameter_dataset_list_file):

		if parameter_dataset_list_file is not None:
			with open(parameter_dataset_list_file, 'r') as file:
				dataset_list = json.load(file)

			self.name_short_country = dataset_list.get("name_short_country")
			self.name_field_county_shp = dataset_list.get("name_field_county_shp")
			self.code_county_shp = dataset_list.get("code_county_shp")
			self.name_county_shp = dataset_list.get("name_county_shp")
			#self.name_field_shp = dataset_list.get("name_field_shp")
			self.shapefile_country_dic = dataset_list.get("shapefile_country_dic")
			self.shapefile_level_1_dic = dataset_list.get("shapefile_level_1_dic")
			self.shapefile_level_2_dic = dataset_list.get("shapefile_level_2_dic")
			self.shapefile_wards_dic = dataset_list.get("shapefile_wards_dic")
			self.fname_places_list_file = dataset_list.get("fname_places_list_file")
			self.rivers_shape_path = dataset_list.get("rivers_shape_path")
			self.default_netcdf = dataset_list.get("default_netcdf")
			self.fname_mask_dic = dataset_list.get("fname_mask_dic")
		else:
			self.name_short_country = default_dataset.name_short_country
			self.name_field_county_shp = default_dataset.name_field_county_shp
			self.code_county_shp = default_dataset.code_county_shp
			self.name_county_shp = default_dataset.name_county_shp
			#self.name_field_shp = default_dataset.name_field_shp
			self.shapefile_country_dic = default_dataset.shapefile_country_dic
			self.shapefile_level_1_dic = default_dataset.shapefile_level_1_dic
			self.shapefile_level_2_dic = default_dataset.shapefile_level_2_dic
			self.shapefile_wards_dic = default_dataset.shapefile_wards_dic 
			self.fname_places_list_file = default_dataset.fname_places_list_file
			self.rivers_shape_path = default_dataset.rivers_shape_path
			self.default_netcdf = default_dataset.default_netcdf
			self.fname_mask_dic = default_dataset.fname_mask_dic