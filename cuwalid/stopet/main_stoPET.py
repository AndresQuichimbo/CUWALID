import argparse
import os
import json
import numpy as np
import time
from cuwalid.stopet.stoPET_v1 import stoPET_wrapper_singlepoint, stoPET_wrapper_regional

def run_stoPET(input_file):
	# Load the configuration from the input file
	with open(input_file, 'r') as f:
		config = json.load(f)

	# Extract the required variables from the configuration
	script_dir = os.path.dirname(os.path.abspath(__file__))
	data_path = os.path.join(script_dir, 'stopet_parameters')
	output_path = os.path.join('stopet_output')
	os.makedirs(output_path, exist_ok=True)

	# Check for the presence of required data files
	required_files = ['stopet_parameters.nc', 'monthly_cont_percentage.nc']
	missing_files = [file for file in required_files if not os.path.exists(os.path.join(data_path, file))]

	if missing_files:
		print("Error: The following required data files are missing:")
		for file in missing_files:
			print(f" - {file}")
		print("Please run the following command to download the necessary files:")
		print("    python -m cuwalid.tools.download_data")
		return

	runtype = config['runtype']
	startyear = config['startyear']
	endyear = config['endyear']
	latval = config['latval']
	lonval = config['lonval']
	latval_min = config['latval_min']
	latval_max = config['latval_max']
	lonval_min = config['lonval_min']
	lonval_max = config['lonval_max']
	locname = config['locname']
	number_ensm = config['number_ensm']
	tempAdj = config['tempAdj']
	deltat = config['deltat']
	udpi_pet = config['udpi_pet']

	# Run the stoPET functions based on the runtype
	if runtype == 'single':
		for ens_num in np.arange(0, number_ensm):
			stoPET_wrapper_singlepoint(startyear, endyear, latval, lonval, locname,
									   ens_num, data_path, output_path, tempAdj, deltat, udpi_pet)
	elif runtype == 'regional':
		for ens_num in np.arange(0, number_ensm):
			stoPET_wrapper_regional(startyear, endyear, latval_min, latval_max, lonval_min, lonval_max,
									locname, ens_num, data_path, output_path, tempAdj, deltat, udpi_pet)
	else:
		raise ValueError('runtype only takes "single" and "regional" ... please check!')

# Main function to handle command-line arguments
if __name__ == '__main__':
	# Set up argument parser to get the JSON config file from command line
	parser = argparse.ArgumentParser(description="Run StoPET based on JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	start = time.time()
	# Run the plot_maps_json function with the config file provided by the user
	run_stoPET(args.config_file)
	end = time.time()
	print('Time of run: %s'%(end - start))
