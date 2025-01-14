import argparse
import json
import os
import geopandas as gpd
from cuwalid.forecasting.components.helper_functions import load_config
from cuwalid.forecasting.components.plot_impact_forecast import plot_map
import cuwalid.forecasting.components.forecast as forecast
import cuwalid.forecasting.components.read_paths as paths
from cuwalid.forecasting.components.map_properties import water_var
#from aux_HAD_plot_probabilistic_forecasting_map import plot_map

# Function to plot maps based on the configuration in the JSON file
def plot_maps_json(config_file):
	"""Function to read a JSON config file and call the map plotting function.

	This function reads a configuration file in JSON format to extract the parameters
	needed to plot maps, including plot scales, country names, place names, seasons, 
	water status, year, output directory, and other file paths. It then either creates 
	maps for specified places or generates maps for all counties within the specified 
	country if no place names are given.

	Parameters
	----------
	config_file: str or dictionary (that represents the json input structure)
		The path to the JSON configuration file that contains the input parameters.

	JSON Configuration Keys:
	------------------------
	plot_scales: [str]
		Scales for plotting the maps. Defaults to ["Zoom"] if not provided.
	country_name: [str]
		List of country names. Defaults to ["Kenya"] if not provided.
	place_names: [str]
		List of specific place names. Defaults to [None], meaning maps will be created 
		for all counties in the specified country.
	seasons: [str]
		Seasons for which the maps are being plotted (e.g., "MAM", "OND"). Defaults to ["OND"].
	water_status: [str]
		Status of water conditions (e.g., "Flood", "Drought"). Defaults to ["Flood"].
	year: int
		Year for which the maps are generated.
	language: str
		The language used in the output maps. Defaults to "English".
	output_dir: str
		Directory where the output maps will be saved. Defaults to "output".
	netcdf_path: str
		Path to the NetCDF file containing the climate data.
	threshold_path: str
		Path to the file containing the threshold data.
	mask_path: str
		Path to the file that contains mask data.
	river_path: str
		Path to the file containing river data.

	Returns
	-------
	None
		This function does not return a value but calls the plotting function to generate maps.

	Example
	-------
	>>> plot_maps_json("config.json")

	Notes
	-----
	- If no place names are provided (i.e., place_names == [None]), the function generates maps 
	  for all counties within the specified countries.
	- If attempting to create maps for multiple countries at once, ensure that place_names is not 
	  specified in the JSON file, as this will cause an error.
	"""

	# Load configuration file
	if type(config_file) == str:
		config = load_config(config_file)
	else:
		config = config_file

	#with open(config_file, 'r') as file:
	#	try:
	#		config = json.load(file)
	#	except json.JSONDecodeError as e:
	#		print(f"Error reading JSON file: {e}")
	#		return

	# Check for required keys and provide feedback if missing
	# required_keys = ["plot_scales", "seasons", "water_status", "year", "mask_path", "river_path"]

	required_keys = ["plot_scales", "seasons", "water_status", "year"]

	for key in required_keys:
		if key not in config:
			print(f"Missing required key: {key} in the configuration file.")
			return

	# Extract parameters from JSON config
	create_dataset = config.get("create_dataset", False)
	create_table = config.get("create_table", True)
	create_map = config.get("create_map", True)
	
	plot_scales = config.get("plot_scales", ["Zoom"])
	country_names = config.get("country", ["Kenya"])
	place_name = config.get("place_names", None)
	season = config.get("seasons", ["OND"])
	water_status = config.get("water_status", ["Flood"])
	year = config["year"]
	language = config.get("language", "English")
	output_dir = config.get("output_dir", "output")
	netcdf_path = config.get("netcdf_path", None)
	#threshold_path = config.get("threshold_path", None)
	#mask_path = config["mask_path"]
	#river_path = config.get("river_path", None)
	#shape_path = config.get("shape_path", None)
	#prev_output_path = config.get("prev_output_path", None)
	#pp_path = config.get("pp_path", None)
	model_name = config.get("model_name", None)
	#print(river_path)
	dataset_parameter_list = config.get("parameter_dataset_list", None)

	print(f"testing {dataset_parameter_list}")
	#print(dataset_parameter_list)
	if dataset_parameter_list is not None:
		dataset_parameters = paths.read_dataset_list_json(dataset_parameter_list)
		#print(dataset_parameters.code_county_shp,dataset_parameters.shapefile_level_1_dic,
		#						dataset_parameters.name_county_shp)

	# check model variable names are available
	# fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc" 
	#if netcdf_path is None:
	# get list of variables names form water status
	netcdf_path_list = []
	for iwater_status in water_status:
		if netcdf_path is None:	
			ivar = water_var[iwater_status]
			netcdf_path_aux = os.path.join(output_dir, "netcdf", f"{model_name}_{ivar}_{season[0]}_{year}_probabilistic_tercile_forecast.nc")
			netcdf_path_list.append(netcdf_path_aux)
		else:
			netcdf_path_list.append(netcdf_path)
	##### Ensure the user provides either netcdf_path/threshold_path
	#####  or prev_output_path/pp_path/model_name
	####if netcdf_path is None or threshold_path is None:
	####	if prev_output_path is None or pp_path is None or model_name is None:
	####		raise ValueError("You must provide either 'netcdf_path' and 'threshold_path', "
	####						"or 'prev_output_path', 'pp_path', and 'model_name'.")

	##### If netcdf_path and threshold_path are not provided, 
	##### generate them using prev_output_path, pp_path, and model_name
	####if netcdf_path is None and threshold_path is None:
	####	netcdf_path = os.path.join(prev_output_path, model_name + "_YYYY_grid.nc")
	####	threshold_path = os.path.join(pp_path, model_name + "_SSS")


	if (place_name is not None) and (len(country_names) > 1):
		print("Error: if creating maps for multiple countries at once, please remove place_name from the json input to create maps for all counties")
		return
	print("WARNING!")
	print("Run function only if hydrological forecasting has been performed")

	read_country_list = False	
	if place_name is None:
		read_country_list = True
	
	# Create maps
	for icountry in country_names:
		#for iplace in place_name:
		#if place_name is None:
		if read_country_list is True:
			place_name, place_code, iname_short_country = get_list_places(
							icountry,
							dataset_parameters.shapefile_level_1_dic,
							dataset_parameters.name_county_shp,
							dataset_parameters.code_county_shp,
							dataset_parameters.name_short_country
							#place_name=place_name
							)
		else:
			place_code = [None]
			iname_short_country = get_list_places(
							icountry,
							dataset_parameters.shapefile_level_1_dic,
							dataset_parameters.name_county_shp,
							dataset_parameters.code_county_shp,
							dataset_parameters.name_short_country
							#place_name=place_name
							)[2]
			
		#print(dataset_parameters.shapefile_level_1_dic[icountry])
		if create_map is True:	
			print("Plot Impact forecasting maps")
			call_plot_maps(
				plot_scales=plot_scales, 
				country_name=icountry, 
				country_code=iname_short_country, 
				place_names=place_name, 
				place_codes=place_code, 
				seasons=season, 
				water_status=water_status, 
				year=year, 
				output_dir=output_dir+"fig/", 
				language=language,
				netcdf_path_list=netcdf_path_list,
				#threshold_path=threshold_path,
				#mask_path=mask_path,
				#river_path=river_path,
				#shape_path=dataset_parameters.shapefile_level_1_dic[icountry]
				shape_path=dataset_parameter_list
				)
		# function to get netcdf files from regional files at each selected place
		if create_dataset is True or create_table is True:
			if create_table is True:
				print("Create one CSV file for each country")
			if create_dataset is True:
				print("Create netCDF files for each selected place")
			
    	    # funtion to calculate areas for county provided in the list
   		    #forecast.get_areas_terciles(model_path, forecast_model_name, season, variables, postpp_path)
			#print(place_name, place_code)
			#print(dataset_parameters.code_county_shp[icountry])
			#print(dataset_parameters.code_county_shp[icountry])
			forecast.extract_forecasting_variable(
							dataset_parameters.name_short_country[icountry],
							#model_name,
							#model_path,
							plot_scales[0],#=plot_scales,
							season=season,
							variables=water_status,
							postpp_path=output_dir,
							netcdf_path_list=netcdf_path_list,
							shapefile_path=dataset_parameters.shapefile_level_1_dic[icountry],
							place_name=place_name,
							place_code=place_code,
							icode_field_shp=dataset_parameters.code_county_shp[icountry],
							iname_field_shp=dataset_parameters.name_county_shp[icountry],
							save_nc=create_dataset
							)
				
def get_list_places(country, shapefile_level_1_dic, name_county_shp,
					code_county_shp, name_short_country):#, place_name=None):
	"""Function to get list of countries and places to print and plot
	
	Parameters:
	-----------
	country_names: list
		list of countries
	place_name : list
		list of places

	Returns
	-------
	
	"""

	shapefile_county = shapefile_level_1_dic[country.lower()]
	name_short_country = name_short_country[country.lower()]
	gdf = gpd.read_file(shapefile_county)
	place_name = gdf[name_county_shp[country.lower()]].tolist()
	place_code = gdf[code_county_shp[country.lower()]].tolist()
	
	#else:
	#		if len(country_names) == 1:
	#			country_names = country_names[0]


	return place_name, place_code, name_short_country



def call_plot_maps(plot_scales=["Zoom"],
		country_name="Kenya",
		country_code="KE",
		place_names=[None],
		place_codes=[None],
		seasons=["MAM"],
		water_status=["Flood"],
		year=2010,
		output_dir="output",
		language=["English",],
		netcdf_path_list=None,
		threshold_path=None,
		mask_path=None,
		river_path=None,
		shape_path=None
		):
	"""
	Function to call the map plotting function for specified regions and conditions.
	
	This function generates maps based on various geographic and environmental conditions. 
	It loops through the provided parameters and calls the `plot_map` function to create maps for 
	specific places (counties), seasons, water statuses, and scales. You can use this function to 
	generate maps for one or multiple places across different conditions.

	You can run this function from the Anaconda command prompt using the following command:
	>>> python aux_HAD_plot_forecasting_maps.py

	Parameters
	----------
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
	None
		This function does not return any values. It generates the specified maps and saves them 
		to the output directory.

	Example
	-------
	>>> call_plot_maps(
			plot_scales=["Zoom"],
			country_name="Kenya",
			place_names=["Isiolo", "Nairobi"],
			seasons=["MAM", "OND"],
			water_status=["Flood", "Drought"],
			year=2020,
			output_dir="output",
			language="English",
			netcdf_path="/path/to/netcdf_file.nc",
			threshold_path="/path/to/threshold_file.csv",
			mask_path="/path/to/mask_file.shp",
			river_path="/path/to/river_file.shp",
			shape_path="/path/to/shape_path.shp",
		)

	Notes
	-----
	- This function loops through all combinations of the provided parameters (plot scales, places, seasons, 
	  and water statuses) and generates a map for each combination.
	- If `place_names` is set to [None], the function will automatically generate maps for all counties 
	  within the specified country.
	"""


	#plot_map(plot_scale="Zoom", place_name="Burat", iseason="OND", iwater_status="Flood", year=2010, ilanguage="English")
	for iplot_scale in plot_scales:
		for iplace_name, iplace_code in zip(place_names, place_codes):
			print(f"Place name {iplace_name}")
			for iiseason in seasons:
				for iiwater_status, inetcdf_path in zip(water_status, netcdf_path_list):
					if iplace_code is not None:
						ifname_fig = (
							country_code+ "_" +
							str(iplace_code)+ "_" +
							iiwater_status+ "_" +
							iiseason + "_" +
							str(year)# + "_"
							)
					else:
						ifname_fig = (
						country_code+ "_" +
						iplace_name+ "_" +
						iiwater_status+ "_" +
						iiseason + "_" +
						str(year)#+".png"# + "_"
						)
					#try:
					plot_map(plot_scale=iplot_scale,
								country_name=country_name,
								place_name=iplace_name,
								iwater_status=iiwater_status,
								iyear=year,
								iseason=iiseason,
								language=language,
								shape_path_list=shape_path,
								output_dir=output_dir,
								netcdf_path=inetcdf_path,
								threshold_path=threshold_path,
								mask_path=mask_path,
								river_path=river_path,
								fname_output=ifname_fig
								)
					#except Exception as e:
					#	print(f"An exception occured {country_name} {iplace_name}")
					#	print(f"Error: {e}")
							  
# Main function to handle command-line arguments
if __name__ == '__main__':
	# Set up argument parser to get the JSON config file from command line
	parser = argparse.ArgumentParser(description="Plot maps based on JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	# Run the plot_maps_json function with the config file provided by the user
	plot_maps_json(args.config_file)