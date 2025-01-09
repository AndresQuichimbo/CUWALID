import json
import os
import subprocess
import sys

import numpy as np
from cuwalid.storm.main_storm import run_storm
from cuwalid.storm.pdfs_ import compute_icpac, masking
from cuwalid.stopet.main_stopet import run_stoPET
from cuwalid.dryp.main_DRYP import run_DRYP
from cuwalid.tools.DRYP_json_builder import create_ensamble, write_JSON_dryp_file

def run_cuwalid(cuwalid_input, forecasting_input):

	# Get input file as dictionary
	with open(cuwalid_input, 'r') as file:
		cuwalid_config = json.load(file)
		
	# Run storm
	storm_input = cuwalid_config["storm"]

	# Convert .nc file into .shp
	space = masking(catchment=stopet_input["SHP_FILE"])
	compute_icpac(storm_input["TER_FILE"])

	run_storm(storm_input)

	# Run StoPET
	stopet_input = cuwalid_config["stopet"]
	run_stoPET(stopet_input)

	# Prepare Dryp files
	  
	nsim = cuwalid_config["storm"]["NUMSIMS"]

	start_date = cuwalid_config["dryp_settings"]["SIMULATION_PERIOD"]["start_date"]
	end_date = cuwalid_config["dryp_settings"]["SIMULATION_PERIOD"]["end_date"]

	season = get_season(start_date)
	iyear = int(start_date.split()[0])

	mname = [cuwalid_config["dryp"]["model_name"] + season + "_" + str(iyear) + "_realization_" + str(isim) for isim in range(nsim)]

	fname_setting_file = "/home/cuwalid/training/forecast/regional/model/HAD_IMERG_par_setting_"+season+"_"+str(iyear)+".json"
	fsim_forecasting = ["/home/cuwalid/training/forecast/regional/model/HAD_IMERG_input_"+season+"_"+str(iyear)+"_forecast_"+str(isim)+".json" for isim in range(nsim)]
	
	folder_datasets_pet = "/home/cuwalid/training/forecast/regional/dataset/pet/"+season+"_"+str(iyear)+"/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"
	folder_datasets_pre = "/home/cuwalid/training/forecast/regional/dataset/pre/"+season+"_"+str(iyear)+"/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"
	#folder_datasets_pre = "/home/cuwalid/leo_test/CUWALID/storm_output/"+season+"_"+str(iyear)+"/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"

	local_directory = "/home/cuwalid/training/forecast/regional/model/" #D:/HAD/training/regional/model/"
	fsim_input_file = local_directory + "HAD_IMERGcv_input_sim85.json"#"HAD_IMERG_input_sim_cuwalid.dmp"

	# TODO: Change pet to the same order naming as pre
	fname_pet = [folder_datasets_pet + "Forecast_PET_HAD_ens_" + str(isim) + "_" + season + "_" + str(iyear) + ".nc" for isim in range(nsim)]
	fname_pre = [folder_datasets_pre + "Forecast_PRE_HAD_ens_" + str(isim) + "_" + season + "_" + str(iyear) + ".nc" for isim in range(nsim)]

	forcing_list = np.array(create_ensamble([fname_pet, fname_pre], nsamples=nsim))

	for ifsim_forecasting, imname, ifname_pre, ifname_pet in zip(fsim_forecasting, mname, forcing_list[:,1], forcing_list[:,0]):
		write_JSON_dryp_file(
			json_template=cuwalid_config,
			model_name= imname,
			path_pre= ifname_pre,
			path_pet= ifname_pet,
			destination = ifsim_forecasting,
			start_date= start_date,
			end_date=end_date,
		)

	# Get dryp input file list
	fsim_forecasting_list = ["HAD_IMERG_input_"+season+"_"+str(iyear)+"_forecast_"+str(isim)+".json" for isim in range(nsim)]

	log_dir = "/home/cuwalid/leo_test/CUWALID/logs"  # Adjust to your desired log directory

	# Make sure the log directory exists
	os.makedirs(log_dir, exist_ok=True)

	for ifsim_forecasting in fsim_forecasting_list:
		# Remove the .json extension for the log file name
		base_name = os.path.splitext(ifsim_forecasting)[0]
		
		# Generate a unique log file name for each process
		log_file = os.path.join(log_dir, f"{base_name}_output.log")
		# Build the command to run the simulation and redirect both stdout and stderr to the log file
		command = f"nohup python -m cuwalid.dryp.main_DRYP /home/cuwalid/training/forecast/regional/model/{ifsim_forecasting} > {log_file} 2>&1 &"
		
		# Run the command as a background process using subprocess
		subprocess.Popen(command, shell=True)

def get_season(date_string):
	# Parse the date string into year, month, day
	year, month, day = map(int, date_string.split())
	
	# Define the season mapping for MAM and OND
	if month in (3, 4, 5):
		return "MAM"  # March, April, May
	elif month in (10, 11, 12):
		return "OND"  # October, November, December
	else:
		return "INVALID_SEASON"  # If not in MAM or OND


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("Usage: python <script_name.py> <path_to_config.json>")
		sys.exit(1)

	cuwalid_path = sys.argv[1]
	forecasting_path = sys.argv[2]

	run_cuwalid(cuwalid_path, forecasting_path)