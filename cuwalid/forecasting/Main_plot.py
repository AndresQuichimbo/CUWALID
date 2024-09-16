import argparse
import json
from cuwalid.forecasting.components.impact_forecast import plot_map
#from aux_HAD_plot_probabilistic_forecasting_map import plot_map

# Function to plot maps based on the configuration in the JSON file
def plot_maps_json(config_file):
	# Open and load the JSON config file
	with open(config_file, 'r') as file:
		try:
			config = json.load(file)
		except json.JSONDecodeError as e:
			print(f"Error reading JSON file: {e}")
			return

	# Check for required keys and provide feedback if missing
	required_keys = ["plot_scales", "place_names", "seasons", "water_status", "year", "netcdf_path", "threshold_path", "mask_path", "river_path"]
	for key in required_keys:
		if key not in config:
			print(f"Missing required key: {key} in the configuration file.")
			return

	# Extract parameters from JSON config
	plot_scales = config.get("plot_scales", ["Zoom"])
	country_name = config.get("country_name", "Kenya")
	place_name = config.get("place_names", ["Isiolo"])
	season = config.get("seasons", ["OND"])
	water_status = config.get("water_status", ["Flood"])
	year = config["year"]
	language = config.get("language", "English")
	output_dir = config.get("output_dir", "output")
	netcdf_path = config["netcdf_path"]
	threshold_path = config["threshold_path"]
	mask_path = config["mask_path"]
	river_path = config["river_path"]


	# Call the plotting function
	call_plot_maps(
		plot_scales=plot_scales, 
		country_name=country_name, 
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
	)



def call_plot_maps(plot_scales=["Zoom"],
		country_name="Kenya",
		place_names=["Isiolo"],
		seasons=["MAM"],
		water_status=["Flood"],
		year=2010,
		output_dir="output",
		language="English",
		netcdf_path=None,
		threshold_path=None,
		mask_path=None,
		river_path=None):

	"""Function to call the plot map function
	it requires all parameters of the ploting funciton
	
	you can run from the anaconda command prompt
	>>> python aux_HAD_plot_forecasting_maps.py

	Parameters
	----------
	plot_scales: [str]
		default ["zoom"]
	place_name: [str]
		default ["isiolo"]
	iseason: [str]
		default ["MAM"]
	iwater_status: [str]
		default ["flood"]
	year: int
		default 2010
	output_dir: str
		default "output"
	ilanguage: str
		default "english"
	
	Returns
	-------

	"""


	#plot_map(plot_scale="Zoom", place_name="Burat", iseason="OND", iwater_status="Flood", year=2010, ilanguage="English")
	for iplot_scale in plot_scales:
		for iplace_name in place_names:
			for iiseason in seasons:
				for iiwater_status in water_status:
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
							)
							  
# Main function to handle command-line arguments
if __name__ == '__main__':
	# Set up argument parser to get the JSON config file from command line
	parser = argparse.ArgumentParser(description="Plot maps based on JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	# Run the plot_maps_json function with the config file provided by the user
	plot_maps_json(args.config_file)