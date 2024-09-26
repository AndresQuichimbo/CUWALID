import argparse
import json
import os
import geopandas as gpd
from cuwalid.forecasting.components.impact_forecast import plot_map
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
	config_file: str
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
	with open(config_file, 'r') as file:
		try:
			config = json.load(file)
		except json.JSONDecodeError as e:
			print(f"Error reading JSON file: {e}")
			return

	# Check for required keys and provide feedback if missing
	required_keys = ["plot_scales", "seasons", "water_status", "year", "mask_path", "river_path"]
	for key in required_keys:
		if key not in config:
			print(f"Missing required key: {key} in the configuration file.")
			return

	# Extract parameters from JSON config
	plot_scales = config.get("plot_scales", ["Zoom"])
	country_names = config.get("country_names", ["Kenya"])
	place_name = config.get("place_names", [None])
	season = config.get("seasons", ["OND"])
	water_status = config.get("water_status", ["Flood"])
	year = config["year"]
	language = config.get("language", "English")
	output_dir = config.get("output_dir", "output")
	netcdf_path = config.get("netcdf_path", None)
	threshold_path = config.get("threshold_path", None)
	mask_path = config["mask_path"]
	river_path = config["river_path"]
	shape_path = config.get("shape_path", None)
	prev_output_path = config.get("prev_output_path", None)
	pp_path = config.get("pp_path", None)
	model_name = config.get("model_name", None)

	# Ensure the user provides either netcdf_path/threshold_path or prev_output_path/pp_path/model_name
	if netcdf_path is None or threshold_path is None:
		if prev_output_path is None or pp_path is None or model_name is None:
			raise ValueError("You must provide either 'netcdf_path' and 'threshold_path', "
							"or 'prev_output_path', 'pp_path', and 'model_name'.")

	# If netcdf_path and threshold_path are not provided, generate them using prev_output_path, pp_path, and model_name
	if netcdf_path is None and threshold_path is None:
		netcdf_path = os.path.join(prev_output_path, model_name + "_YYYY_grid.nc")
		threshold_path = os.path.join(pp_path, model_name + "_SSS")

	print("############################")
	print(netcdf_path)
	print(threshold_path)
	print("############################")


	if place_name != [None] and len(country_names)>1:
		print("Error: if creating maps for multiple countries at once, please remove place_name from the json input to create maps for all counties")
		return

	# Get list of all countries within the countries if the user doesn't provide a list
	if place_name == [None]:

		shapefile_county_dic = {
			"kenya": 'forecasting_dataset/kenya/kenya-county/ke_county.shp',
			"ethiopia": 'forecasting_dataset/ethiopia/Export_admin2.shp',
			"somalia": 'forecasting_dataset/somalia/somalia_regions.shp',
		}

		name_field_county_shp = {
			"kenya":'county',
			"ethiopia":'NAME_2',
			"somalia":'NAME',
		}

		# Get list of counties from each country given in the iput
		for country in country_names:
			print(f"Warning: no place name given, creating a map for each county within {country}")

			# Open shape file
			shapefile_county = os.path.abspath(os.path.join(os.path.dirname(__file__), shapefile_county_dic[country.lower()]))
			gdf = gpd.read_file(shapefile_county)

			# Get county list 
			place_name = gdf[name_field_county_shp[country.lower()]].tolist()

			# Create maps
			call_plot_maps(
				plot_scales=plot_scales, 
				country_name=country, 
				place_names=place_name, 
				seasons=season, 
				water_status=water_status, 
				year=year, 
				output_dir=output_dir, 
				language=language,
				netcdf_path=netcdf_path,
				threshold_path=threshold_path,
				mask_path=mask_path,
				river_path=river_path,
				shape_path=shape_path
			)
	elif len(country_names) == 1:
		call_plot_maps(
			plot_scales=plot_scales, 
			country_name=country_names[0], 
			place_names=place_name, 
			seasons=season, 
			water_status=water_status, 
			year=year, 
			output_dir=output_dir, 
			language=language,
			netcdf_path=netcdf_path,
			threshold_path=threshold_path,
			mask_path=mask_path,
			river_path=river_path,
			shape_path=shape_path
		)
	else:
		# Call the plotting function
		call_plot_maps(
			plot_scales=plot_scales, 
			country_name=country_names, 
			place_names=place_name, 
			seasons=season, 
			water_status=water_status, 
			year=year, 
			output_dir=output_dir, 
			language=language,
			netcdf_path=netcdf_path,
			threshold_path=threshold_path,
			mask_path=mask_path,
			river_path=river_path,
			shape_path=shape_path
		)

def call_plot_maps(plot_scales=["Zoom"],
		country_name="Kenya",
		place_names=[None],
		seasons=["MAM"],
		water_status=["Flood"],
		year=2010,
		output_dir="output",
		language="English",
		netcdf_path=None,
		threshold_path=None,
		mask_path=None,
		river_path=None,
		shape_path=None):
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
		for iplace_name in place_names:
			print(f"Place name {iplace_name}")
			for iiseason in seasons:
				for iiwater_status in water_status:
					try:
						plot_map(plot_scale=iplot_scale,
								country_name=country_name,
								place_name=iplace_name,
								iseason=iiseason,
								iwater_status=iiwater_status,
								iyear=year,
								ilanguage=language,
								output_dir=output_dir,
								netcdf_path=netcdf_path,
								threshold_path=threshold_path,
								mask_path=mask_path,
								river_path=river_path,
								shape_path=shape_path
								)
					except Exception as e:
						print(f"An exception occured {country_name} {iplace_name}")
						print(f"Error: {e}")
							  
# Main function to handle command-line arguments
if __name__ == '__main__':
	# Set up argument parser to get the JSON config file from command line
	parser = argparse.ArgumentParser(description="Plot maps based on JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	# Run the plot_maps_json function with the config file provided by the user
	plot_maps_json(args.config_file)