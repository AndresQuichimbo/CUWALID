import json
import subprocess
import sys

import numpy as np
from cuwalid.storm.main_storm import run_storm
from cuwalid.stopet.main_stoPET import run_stoPET
from cuwalid.dryp.main_DRYP import run_DRYP
from cuwalid.tools.DRYP_json_builder import create_ensamble, write_JSON_dryp_file

def run_cuwalid(json_input):

	# Get input file as dictionary
	with open(json_input, 'r') as file:
		config = json.load(file)
		
	# Run storm
	storm_input = config["storm"]
	run_storm(storm_input)

	# Run StoPET
	stopet_input = config["stopet"]
	run_stoPET(stopet_input)

	# Prepare Dryp files
	nsim = 30
	season = "OND"
	iyear = 2022

	mname = config["dryp"]["model_name"]
	start_date = config["dryp_settings"]["SIMULATION_PERIOD"]["start_date"]
	end_date = config["dryp_settings"]["SIMULATION_PERIOD"]["end_date"]

	fname_setting_file = "/home/cuwalid/training/forecast/regional/model/HAD_IMERG_par_setting_"+season+"_"+str(iyear)+".json"
	fsim_forecasting = ["/home/cuwalid/training/forecast/regional/model/HAD_IMERG_input_"+season+"_"+str(iyear)+"_forecast_"+str(isim)+".json" for isim in range(30)]
	
	folder_datasets_pet = "/home/cuwalid/training/forecast/regional/dataset/pet/"+season+"_"+str(iyear)+"_PET_forecast/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"
	folder_datasets_pre = "/home/cuwalid/training/forecast/regional/dataset/pre/"+season+"_"+str(iyear)+"/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"

	local_directory = "/home/cuwalid/training/forecast/regional/model/" #D:/HAD/training/regional/model/"
	fsim_input_file = local_directory + "HAD_IMERGcv_input_sim85.json"#"HAD_IMERG_input_sim_cuwalid.dmp"

	fname_pet = [folder_datasets_pet+"Forecast_PET_HAD_ens_"+str(isim)+"_"+season+"_"+str(iyear)+".nc" for isim in range(nsim)]
	fname_pre = [folder_datasets_pre+"Forecast_PRE_HAD_ens_"+str(isim)+"_"+season+"_"+str(iyear)+".nc" for isim in range(nsim)]

	forcing_list = np.array(create_ensamble([fname_pet, fname_pre], nsamples=30))

	for ifsim_forecasting, imname, ifname_pre, ifname_pet in zip(fsim_forecasting, mname, forcing_list[:,1], forcing_list[:,0]):
		write_JSON_dryp_file(
			json_template=fsim_input_file,
			model_name= imname,
			path_pre= ifname_pre,
			path_pet= ifname_pet,
			start_date= start_date,
			end_date=end_date,
			destination = ifsim_forecasting,
			save_fname=fname_setting_file
		)

	# Get dryp input file list
	fsim_forecasting_list = ["HAD_IMERG_input_"+season+"_"+str(iyear)+"_forecast_"+str(isim)+".json" for isim in range(30)]

	# Run dryp as parralel process
	for ifsim_forecasting in fsim_forecasting_list:
		command = f"python -m cuwalid.dryp.main_DRYP /home/cuwalid/training/forecast/regional/model/{ifsim_forecasting}"
		subprocess.Popen(command, shell=True)


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("Usage: python <script_name.py> <path_to_config.json>")
		sys.exit(1)

	config_file = sys.argv[1]

	run_cuwalid(config_file)