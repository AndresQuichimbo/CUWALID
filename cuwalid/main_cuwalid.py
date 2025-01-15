import argparse
import json
import os
import subprocess
import sys
#sys.path.append("/home/cuwalid/CUWALID")
import numpy as np
from cuwalid.storm.main_storm import run_storm
from cuwalid.storm.pdfs_ import compute_icpac, masking
from cuwalid.stopet.main_stopet import run_stoPET
from cuwalid.dryp.main_DRYP import run_DRYP
from cuwalid.forecasting.main_hydro_forecast import run_hydro_forecast
import cuwalid.forecasting.main_impact_forecast as fcast
from cuwalid.tools.DRYP_json_builder import create_ensamble, write_JSON_dryp_file
from cuwalid.tools.download_data import check_and_download
import cuwalid.tools.CUWALID_json_builder as JSON_builder
import cuwalid.tools.CUWALID_mfile_tools as cuwalid_mtools
from cuwalid.tools.CUWALID_make_dirs import create_directory_structure

def run_cuwalid(cuwalid_input):
	
	# Get input file as dictionary
	with open(cuwalid_input, 'r') as file:
		cuwalid_config = json.load(file)


	# General parameters 
	# read historical paths
	historical_model_name = cuwalid_config["historical"]['model_name']
	historical_path = cuwalid_config["historical"]['main_path']
	historical_model_path = cuwalid_config["historical"]['model_path']
	historical_postpp_path = cuwalid_config["historical"]['postpp_path']
	
	# read forecasting parameters
	forecast_model_name = cuwalid_config["forecasting"]['model_name']
	forecast_path = cuwalid_config["forecasting"]['main_path']
	forecast_model_path = cuwalid_config["forecasting"]['model_path']
	forecast_postpp_path = cuwalid_config["forecasting"]['postpp_path']

	# I have disable it to allows make it work in my script
##	# read historical paths
##	historical_model_name = cuwalid_config["historical_model_name"]
##
##	# read forecasting parameters
##	forecast_model_name = cuwalid_config["forecasting_model_name"]
##
##	forecast_path = os.path.join(cuwalid_config["output_dir"], "forecast/regional")
	
	# read stopet input file path
	tercile_forecast_file = cuwalid_config["Tercile_Pre_path"]

	season = cuwalid_config['season'][0]
	iyear = cuwalid_config["year"]
	nsim = cuwalid_config["NSIM"]
	start_date, end_date = cuwalid_mtools.get_dates_season(season, iyear)
	start_day, end_day = cuwalid_mtools.date_to_day_of_year(start_date), cuwalid_mtools.date_to_day_of_year(end_date)

	forecast_path = os.path.join(forecast_path, f"{season}_{str(iyear)}")+"/"

	# read storm input file path
	storm_file = cuwalid_config["Tercile_Tem_path"]

	# Create directory structure for cuwalid system where user ran code
	create_directory_structure("", season, iyear)

##	forecast_path_storm_output = os.path.join(forecast_path, f"{season}_{str(iyear)}", "dataset/pre/")
##	forecast_path_stopet_output = os.path.join(forecast_path, f"{season}_{str(iyear)}", "dataset/pet/")
##	forecast_path_dryp_model = os.path.join(forecast_path, f"{season}_{str(iyear)}", "model")
##	forecast_path_dryp_output = os.path.join(forecast_path, f"{season}_{str(iyear)}", "output")
##	forecast_path_dryp_postpp = os.path.join(forecast_path, f"{season}_{str(iyear)}", "postpp")

	# I have added this to run this in my session so delete if it does not apply
	forecast_path_storm_output = forecast_path + "dataset/pre/"+season+"_"+str(iyear)+"/"
	forecast_path_stopet_output = forecast_path + "dataset/pet/"+season+"_"+str(iyear)+"/"
	forecast_path_dryp_model = forecast_path + "model/"
	forecast_path_dryp_output = forecast_path + "output/"
	forecast_path_dryp_postpp = forecast_path + "postpp/"

	
	# RUN MODEL COMPONENTS AND ANY ADDITIONAL PROCESS
	# Run storm
	if cuwalid_config["run_STORM"] is True:
		print("Run STORM simulation")
		storm_input_path = cuwalid_config["MODELS"]["STORM"]["input"]
		with open(storm_input_path, 'r') as file:
			storm_input = json.load(file)

		# Change storms input based on cuwalid inputs settings
		storm_input["SEASON_TAG"] = season
		storm_input["SEED_YEAR"] = iyear
		storm_input["NUMSIMS"] = nsim
		storm_input["OUT_PATH"] = forecast_path_storm_output

		# Create path for converted .shp file and set this to the new TER_FILE
		shp_output = os.path.join(forecast_path_storm_output, f"tercilesICPAC_{storm_input['SEASON_TAG']}_{storm_input['SEED_YEAR']}.shp")
		storm_input["TER_FILE"] = shp_output

		# Convert .nc file into .shp
		space = masking(storm_input["SHP_FILE"])
		compute_icpac(space, storm_file, storm_input["TER_FILE"], storm_input["ZON_FILE"])

		run_storm(storm_input)

	else:
		print("storm is not executed")

	
	# Run StoPET
	if cuwalid_config["run_stoPET"] is True:
		print("Run stoPET simulation")
		stopet_input_path = cuwalid_config["MODELS"]["stoPET"]["input"]
		with open(stopet_input_path, 'r') as file:
			stoPET_input = json.load(file)

		stoPET_input["outputpath"] = forecast_path_stopet_output
		stoPET_input["startyear"] = iyear
		stoPET_input["endyear"] = iyear
		stoPET_input["startdate"] = start_day
		stoPET_input["enddate"] = end_day
		stoPET_input["trial_number"] = nsim
		stoPET_input["number_ensm"] = nsim
		stoPET_input["seasonName"] =season
		stoPET_input["tercile_forecast_file"] = tercile_forecast_file

		run_stoPET(stoPET_input)

	else:
		print("stoPET is not executed")

	
	# set DRYP model simulations
	# create model names
	mname = [season + "_" + str(iyear) + "_realization_" + str(isim) for isim in range(nsim)]
	# create model settings file names for realizations
	fname_setting_file = os.path.join(forecast_path_dryp_model,"Hydro_model_forecast_settings_"+season+"_"+str(iyear)+".json")
	# create model parameter file names for realizations
	fsim_forecasting = [os.path.join(forecast_path_dryp_model,"Hydro_model_forecast_input_"+ season +"_"+str(iyear)+ "_" +str(isim)+".json") for isim in range(nsim)]
	
	
	# run DRYP multiple simulations
	if cuwalid_config["run_DRYP"] is True:
		print("Executing DRYP simulations")
		dryp_input_path = cuwalid_config["MODELS"]["DRYP"]["input"]
		dryp_settings_path = cuwalid_config["MODELS"]["DRYP"]["settings"]
		with open(dryp_input_path, 'r') as file:
			dryp_input = json.load(file)

		# TODO: Change pet to the same order naming as pre
		#fname_pet = [forecast_path_stopet_output+ "Forecast_PET_HAD_ens_" + str(iyear) + "_" + season + "_" + str(isim) + ".nc" for isim in range(nsim)]
		#fname_pre = [forecast_path_storm_output + "Forecast_PRE_HAD_ens_" + str(iyear) + "_" + season + "_" + str(isim) + ".nc" for isim in range(nsim)]
		fname_pet = [forecast_path_stopet_output+ "Forecast_PET_HAD_ens_" + str(isim) + "_" + season + "_" + str(iyear) + ".nc" for isim in range(nsim)]
		fname_pre = [forecast_path_storm_output + "Forecast_PRE_HAD_ens_" + str(isim) + "_" + season + "_" + str(iyear) + ".nc" for isim in range(nsim)]
		forcing_list = np.array(JSON_builder.create_ensamble([fname_pet, fname_pre], nsamples=nsim))

		# Create the list of commands for each simulation
		commands = []
		for ifsim_forecasting, imname, ifname_pre, ifname_pet in zip(fsim_forecasting, mname, forcing_list[:, 1], forcing_list[:, 0]):
			# Generate JSON for each simulation (same as before)
			JSON_builder.write_JSON_dryp_files(
				json_template=dryp_input,
				model_name=imname,
				path_pre=ifname_pre,
				path_pet=ifname_pet,
				json_destination=ifsim_forecasting,
				dryp_output= forecast_path_dryp_output,
				start_date=start_date,
				end_date=end_date,
				new_setting_file=fname_setting_file,
				path_outputs=forecast_path_dryp_output,
			)

			# Prepare the log file and command for each process
			log_dir = "logs"  
			os.makedirs(log_dir, exist_ok=True)
			base_name = os.path.splitext(os.path.basename(ifsim_forecasting))[0]
			log_file = os.path.join(log_dir, f"{base_name}_output.log")

			# Command to run the DRYP simulation in the background
			command = f"nohup python -u -m cuwalid.dryp.main_DRYP {ifsim_forecasting} > {log_file} 2>&1 &"
			print(f"Executing: {command}")
			commands.append(command)

		# Run each command in parallel using subprocess
		processes = []
		for command in commands:
			process = subprocess.Popen(command, shell=True)
			processes.append(process)

		# Wait for all subprocesses to finish
		for process in processes:
			process.wait()  # This will block until the process completes

		print("All DRYP simulations are finished.")
	else:
		print("DRYP is not executed")


	# print add water forecasting entry
	if cuwalid_config["run_WaterCast"] is True:
		print("Executing Water forecasting: WaterCast")
		HyCast_input_path = cuwalid_config["MODELS"]["WaterCast"]["HyCast"]
		
		with open(HyCast_input_path, 'r') as file:
			HyCast_input = json.load(file)
		
		# modify names
		# modify season and year
		HyCast_input["forecasting"]["model_name"] = season + "_" + str(iyear) + "_realization"
		HyCast_input["forecasting"]["model_path"] = forecast_path_dryp_output #+ "/"
		HyCast_input["forecasting"]["postpp_path"] = forecast_path_dryp_postpp
		HyCast_input["year"] = iyear
		HyCast_input["seasons"] = season
		#print(HyCast_input)
		print("Executing hydrological forecasting: HyCast")
		run_hydro_forecast(HyCast_input)

		# Impact base forecasting
		ImCast_input_path = cuwalid_config["MODELS"]["WaterCast"]["ImCast"]

		with open(ImCast_input_path, 'r') as file:
			ImCast_input = json.load(file)
		
		# modify names
		# modify season and year
		ImCast_input["model_name"] = season + "_" + str(iyear) + "_realization"
		ImCast_input["model_path"] = forecast_path_dryp_output #+ #"/"
		ImCast_input["postpp_path"] = forecast_path_dryp_postpp
		ImCast_input["output_dir"] = forecast_path_dryp_postpp
		ImCast_input["year"] = iyear
		ImCast_input["season"] = season
		#print(ImCast_input)
		print("Executing Impact-based water forecasting: ImCast")
		fcast.plot_maps_json(ImCast_input)

if __name__ == '__main__':
	# Set up argument parser to get the JSON config file from command line
	parser = argparse.ArgumentParser(description="Execute CUWALID based on JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	# Run the cuwalid forecast function with the config file provided by the user
	run_cuwalid(args.config_file)