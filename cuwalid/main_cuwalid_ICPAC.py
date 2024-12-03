import json
import os
import subprocess
import sys
sys.path.append("/home/cuwalid/CUWALID")
import numpy as np
from cuwalid.storm.main_storm import run_storm
from cuwalid.stopet.main_stoPET import run_stoPET
from cuwalid.dryp.main_DRYP import run_DRYP
from cuwalid.forecasting.main_hydro_forecast import run_hydro_forecast
from cuwalid.forecasting.main_impact_forecast import run_impact_forecast
from cuwalid.tools.DRYP_json_builder import create_ensamble, write_JSON_dryp_file
import cuwalid.tools.DRYP_json_builder as JSON_builder
import cuwalid.tools.CUWALID_forecast_tools as cuwalid_mtools

def run_cuwalid(cuwalid_input, forecasting_input):
	
	# Get input file as dictionary
	with open(cuwalid_input, 'r') as file:
		cuwalid_config = json.load(file)
	
	# General parameters 
	# read historical paths
	historical_model_name = cuwalid_config["historical"]['model_name']
	historical_model_path = cuwalid_config["historical"]['model_path']
	historical_postpp_path = cuwalid_config["historical"]['postpp_path']
	
	# read forecasting parameters
	forecast_model_name = cuwalid_config["forecasting"]['model_name']
	forecast_model_path = cuwalid_config["forecasting"]['model_path']
	forecast_postpp_path = cuwalid_config["forecasting"]['postpp_path']

	#threshold_path = historical_postpp_path + "netcdf/"+ historical_model_name+ "_SSS_extremes_quantiles.nc"

	season = cuwalid_config['season']
	#start_year = cuwalid_config['start_year']
	#end_year = cuwalid_config['end_year']
	#variables = cuwalid_config['variables']
	iyear = cuwalid_config["year"]
	nsim = cuwalid_config["NSIM"]
	
	start_date, end_date = cuwalid_mtools.get_dates_season(season, iyear)

	# SET UP MODEL AND PATHS
	# Run storm
	print("Run STORM simulation")
	if cuwalid_config["run_STORM"] is True:
		storm_input_path = cuwalid_config["MODELS"]["STORM"]["input"]
		with open(storm_input_path, 'r') as file:
			storm_input = json.load(file)
		# add code to modify input files
		# set up path for model putputs
		# set up model simulation name outputs
		#run_storm(storm_input)

	# Run StoPET
	print("Run stoPET simulation")
	if cuwalid_config["run_stoPET"] is True:
		stopet_input_path = cuwalid_config["MODELS"]["stoPET"]["input"]
		with open(stopet_input_path, 'r') as file:
			stoPET_input = json.load(file)
		# add code to modify input files
		# set up path for model putputs
		# set up model simulation name outputs
		#run_stoPET(stoPET_input)

	# Prepare Dryp files
	
#	nsim = cuwalid_config["storm"]["NUMSIMS"]
#	start_date = cuwalid_config["dryp_settings"]["SIMULATION_PERIOD"]["start_date"]
#	end_date = cuwalid_config["dryp_settings"]["SIMULATION_PERIOD"]["end_date"]
#	season = get_season(start_date)
#	iyear = int(start_date.split()[0])
#	mname = [cuwalid_config["dryp"]["model_name"] + season + "_" + str(iyear) + "_realization_" + str(isim) for isim in range(nsim)]
#	mname = [forecast_model_name + season + "_" + str(iyear) + "_realization_" + str(isim) for isim in range(nsim)]
#	fname_setting_file = "/home/cuwalid/training/forecast/regional/model/HAD_IMERG_par_setting_"+season+"_"+str(iyear)+".json"
#	fsim_forecasting = ["/home/cuwalid/training/forecast/regional/model/HAD_IMERG_input_"+season+"_"+str(iyear)+"_forecast_"+str(isim)+".json" for isim in range(nsim)]
	
	# set DRYP model simulations
	# create model names
#	mname = [forecast_model_name + season + "_" + str(iyear) + "_realization_" + str(isim) for isim in range(nsim)]
	mname = [season + "_" + str(iyear) + "_realization_" + str(isim) for isim in range(nsim)]
	# create model settings files names for realizations
	fname_setting_file = "/home/cuwalid/training/forecast/regional/model/HAD_IMERG_par_setting_"+season+"_"+str(iyear)+".json"
	# create model parameters files names for realizations
	fsim_forecasting = ["/home/cuwalid/training/forecast/regional/model/HAD_IMERG_input_test_"+season+"_"+str(iyear)+"_forecast_"+str(isim)+".json" for isim in range(nsim)]
	
	# set paths of forcing datasets and names
	folder_datasets_pet = "/home/cuwalid/training/forecast/regional/dataset/pet/"+season+"_"+str(iyear)+"_PET_forecast/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"
	folder_datasets_pre = "/home/cuwalid/training/forecast/regional/dataset/pre/"+season+"_"+str(iyear)+"/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"
	folder_datasets_pre = "/home/cuwalid/leo_test/CUWALID/storm_output/"+season+"_"+str(iyear)+"/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"
	local_directory = "/home/cuwalid/training/forecast/regional/model/" #D:/HAD/training/regional/model/"
	
	# run DRYP multiple simulations
	print("Run DRYP simulation")
	if cuwalid_config["run_DRYP"] is True:
		dryp_input_path = cuwalid_config["MODELS"]["DRYP"]["input"]
		dryp_settings_path = cuwalid_config["MODELS"]["DRYP"]["settings"]
		with open(dryp_input_path, 'r') as file:
			dryp_input = json.load(file)
		# get basefile of model parameters and settings files
		#fsim_input_file = local_directory + "HAD_IMERGcv_input_sim85.json"#"HAD_IMERG_input_sim_cuwalid.dmp"
	
	# TODO: Change pet to the same order naming as pre
	fname_pet = [folder_datasets_pet+"Forecast_PET_HAD_ens_"+str(isim)+"_"+season+"_"+str(iyear)+".nc" for isim in range(nsim)]
	fname_pre = [folder_datasets_pre + "Forecast_PRE_HAD_ens_" + str(iyear) + "_" + season + "_" + str(isim) + ".nc" for isim in range(nsim)]
	forcing_list = np.array(create_ensamble([fname_pet, fname_pre], nsamples=nsim))
	for ifsim_forecasting, imname, ifname_pre, ifname_pet in zip(fsim_forecasting, mname, forcing_list[:,1], forcing_list[:,0]):
		#write_JSON_dryp_file(
		JSON_builder.write_JSON_dryp_file_1(
			json_template=dryp_input,
			model_name=imname,
			path_pre=ifname_pre,
			path_pet=ifname_pet,
			destination=ifsim_forecasting,
			start_date=start_date,
			end_date=end_date,
			new_setting_file=fname_setting_file,
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
		print(command)
		# Run the command as a background process using subprocess
		#subprocess.Popen(command, shell=True)


	# print add water forecasting entry
	print("Run Water forecasting WaterCast")
	if cuwalid_config["run_WaterCast"] is True:
		HyCast_input_path = cuwalid_config["MODELS"]["WaterCast"]["HyCast"]
		ImCast_input_path = cuwalid_config["MODELS"]["WaterCast"]["ImCast"]

		# Add functions to modify paths and names according to the cofiguration files before runing the forecast
		# modify names
		# modify season and year

		run_hydro_forecast(HyCast_input_path)
		run_impact_forecast(ImCast_input_path)

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("Usage: python <script_name.py> <path_to_config.json>")
		sys.exit(1)

	cuwalid_path = sys.argv[1]
	forecasting_path = sys.argv[2]

	run_cuwalid(cuwalid_path, forecasting_path)