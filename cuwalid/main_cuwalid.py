import argparse
import json
import os
import subprocess
import sys
import time
import numpy as np
from cuwalid.storm.main_storm import run_storm
from cuwalid.storm.pdfs_ import compute_icpac, masking
from cuwalid.stopet.main_stopet import run_stoPET
from cuwalid.stopet.pet_forecast_generation import forecast_wrapper
from cuwalid.dryp.main_DRYP import run_DRYP
from cuwalid.forecasting.main_hydro_forecast import run_hydro_forecast
import cuwalid.forecasting.main_impact_forecast as fcast
from cuwalid.tools.DRYP_json_builder import create_ensamble, write_JSON_dryp_file
import cuwalid.tools.CUWALID_json_builder as JSON_builder
import cuwalid.tools.CUWALID_mfile_tools as cuwalid_mtools
from cuwalid.tools.CUWALID_make_dirs import create_directory_structure

def run_cuwalid(cuwalid_input):
	
	# Get input file as dictionary
	with open(cuwalid_input, 'r') as file:
		cuwalid_config = json.load(file)

	# read forecasting parameters
	#forecast_model_name = cuwalid_config["forecasting_model_name"]

	forecast_path = cuwalid_config["output_dir"]
	#forecast_path = os.path.join(cuwalid_config["output_dir"], "forecast/regional")

	# read storm input file path
	storm_tercile_file = cuwalid_config["Tercile_Pre_path"]

	# read stopet input file path
	stopet_tercile_file = cuwalid_config["Tercile_Tem_path"]

	season = cuwalid_config['season'][0]
	iyear = cuwalid_config["year"]
	nsim_meteo = cuwalid_config["NSIM"]
	# check if cowalid_config has the variable "nsim_dryp" otherwise add that variable
	if "NSIM_HYDRO" in cuwalid_config:
		nsim_hydro = cuwalid_config["NSIM_HYDRO"]
	else:
		cuwalid_config["NSIM_HYDRO"] = nsim_meteo
		nsim_hydro = nsim_meteo

	start_date, end_date = cuwalid_mtools.get_dates_season(season, iyear)
	start_day, end_day = cuwalid_mtools.date_to_day_of_year(start_date), cuwalid_mtools.date_to_day_of_year(end_date)

	# Find if the user wants to run in parallel when possible
	sim_in_parallel = cuwalid_config.get("sim_in_parallel", False)

	# Create directory structure for cuwalid system where user ran code
	create_directory_structure(forecast_path, season, iyear)

	# create a temporary file folder
	temp_folder = os.path.join(forecast_path, "temp")

	forecast_path_storm_output = os.path.join(forecast_path, f"{season}_{str(iyear)}", "dataset/pre/")
	forecast_path_stopet_output = os.path.join(forecast_path, f"{season}_{str(iyear)}", "dataset/pet/")
	forecast_path_dryp_model = os.path.join(forecast_path, f"{season}_{str(iyear)}", "model")
	forecast_path_dryp_output = os.path.join(forecast_path, f"{season}_{str(iyear)}", "output")
	forecast_path_dryp_postpp = os.path.join(forecast_path, f"{season}_{str(iyear)}", "postpp")

	# RUN MODEL COMPONENTS AND ANY ADDITIONAL PROCESS

	# =====================================================================
	# Run storm
	# =====================================================================
	if cuwalid_config["run_STORM"] is True:
		print("Run STORM simulation")
		storm_input_path = cuwalid_config["MODELS"]["STORM"]["input"]
		with open(storm_input_path, 'r') as file:
			storm_input = json.load(file)

		# Change storms input based on cuwalid inputs settings
		storm_input["SEASON_TAG"] = season
		storm_input["SEED_YEAR"] = iyear
		storm_input["NUMSIMS"] = nsim_meteo
		storm_input["OUT_PATH"] = forecast_path_storm_output
		storm_input["sim_in_parallel"] = sim_in_parallel

		# Create path for converted .shp file and set this to the new TER_FILE
		shp_output = os.path.join(forecast_path_storm_output, f"tercilesICPAC_{storm_input['SEASON_TAG']}_{storm_input['SEED_YEAR']}.shp")
		storm_input["TER_FILE"] = shp_output

		# Convert .nc file into .shp
		space = masking(storm_input["SHP_FILE"])
		print("Computing shp file")
		compute_icpac(space, storm_tercile_file, storm_input["TER_FILE"], storm_input["ZON_FILE"])
		print("Finished creating shp file")

		run_storm(storm_input)

	else:
		print("storm is not executed")

	# =====================================================================
	# Run StoPET
	# =====================================================================
	if cuwalid_config["run_stoPET"] is True:
		print("Run stoPET simulation")
		stopet_input_path = cuwalid_config["MODELS"]["stoPET"]["input"]
		with open(stopet_input_path, 'r') as file:
			stoPET_input = json.load(file)

		stoPET_input["outputpath"] = os.path.join(forecast_path_stopet_output)
		stoPET_input["temp_path"] = temp_folder
		stoPET_input["startyear"] = iyear
		stoPET_input["endyear"] = iyear
		stoPET_input["startdate"] = start_day
		stoPET_input["enddate"] = end_day
		stoPET_input["number_ensm"] = nsim_meteo
		stoPET_input["seasonName"] = season
		stoPET_input["tercile_forecast_file"] = stopet_tercile_file

		run_stoPET(stoPET_input)

		# Converting sim*2 number of files from stopet into sim number of files for dryp to use
		print("Converting stopet output into files for dryp")
		print(f"tercile file {stoPET_input['tercile_forecast_file']}")
		if stoPET_input["tercile_forecast_file"]:
			forecast_wrapper(stoPET_input["tercile_forecast_file"], forecast_path_stopet_output, iyear, start_day, end_day, stoPET_input["locname"], nsim_meteo, stoPET_input["tempAdj"], season, stoPET_input["temp_path"])

	else:
		print("stoPET is not executed")

	# =====================================================================
	# set DRYP model simulations
	# =====================================================================
	# create model names
	mname = [season + "_" + str(iyear) + "_realization_" + str(isim) for isim in range(nsim_hydro)]
	# create model settings file names for realizations
	fname_setting_file = os.path.join(forecast_path_dryp_model,"Hydro_model_forecast_settings_"+season+"_"+str(iyear)+".json")
	# create model parameter file names for realizations
	fsim_forecasting = [os.path.join(forecast_path_dryp_model,"Hydro_model_forecast_input_"+ season +"_"+str(iyear)+ "_" +str(isim)+".json") for isim in range(nsim_hydro)]
	
	# forecasting dryp model name
	forecast_model_name = season + "_" + str(iyear) + "_realization"
	
	# run DRYP multiple simulations
	if cuwalid_config["run_DRYP"] is True:
		print("Executing DRYP simulations")
		dryp_input_path = cuwalid_config["MODELS"]["DRYP"]["input"]
		with open(dryp_input_path, 'r') as file:
			dryp_input = json.load(file)

		dryp_settings_path = cuwalid_config["MODELS"]["DRYP"]["settings"]
		dryp_input["OUTPUT"]["path_setting"] = dryp_settings_path

		fname_pet = [forecast_path_stopet_output + "Forecast_PET_HAD_ens_" + str(iyear) + "_" + season + "_" + str(isim) + ".nc" for isim in range(nsim_meteo)]
		fname_pre = [forecast_path_storm_output + "Forecast_PRE_HAD_ens_" + str(iyear) + "_" + season + "_" + str(isim) + ".nc" for isim in range(nsim_meteo)]
		forcing_list = np.array(JSON_builder.create_ensamble([fname_pet, fname_pre], nsamples=nsim_hydro))

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
				dryp_output=forecast_path_dryp_output,
				start_date=start_date,
				end_date=end_date,
				new_setting_file=fname_setting_file,
			)

			# Prepare the log file and command for each process
			log_dir = "logs"
			os.makedirs(log_dir, exist_ok=True)
			base_name = os.path.splitext(os.path.basename(ifsim_forecasting))[0]
			log_file = os.path.join(log_dir, f"{base_name}_output.log")

			# Command to run the DRYP simulation in the background
			if sim_in_parallel:
				print("Running DRYP in parallel")
				command = f"nohup python -u -m cuwalid.dryp.main_DRYP {ifsim_forecasting} > {log_file} 2>&1 &"
				print(f"Executing: {command}")
			else:
				print("Running DRYP in sequence")
				command = ifsim_forecasting
			
			commands.append(command)


		# Run the first batch in parallel
		processes = []
		for command in commands:
			print(f"Executing: {command}")
			if sim_in_parallel: # run simulations in paralell using nohup
				process = subprocess.Popen(command, shell=True)
				processes.append(process)
				time.sleep(5)
			else: # Run in sequence
				run_DRYP(command)

		print("DRYP is running, check logs")
	else:
		print("DRYP is not executed")


	# =====================================================================
	# print add water forecasting entry
	# =====================================================================
	if cuwalid_config["run_WaterCast"] is True:
		print("Executing Water forecasting: WaterCast")
		HyCast_input_path = cuwalid_config["MODELS"]["WaterCast"]["HyCast"]
		ImCast_input_path = cuwalid_config["MODELS"]["WaterCast"]["ImCast"]

		# =====================================================================
		# Run hydrological forecasting
		# =====================================================================
		print("Executing hydrological forecasting: HyCast")
		# Open json config
		with open(HyCast_input_path, 'r') as file:
			HyCast_input = json.load(file)

		# Modify vairables for forecasting
		forecasting_input = {
			"model_name": forecast_model_name,
			"main_path": forecast_path_dryp_model+"/",#f"forecast/regional/{season}_{str(iyear)}/",
			"model_path": forecast_path_dryp_output+"/",#f"forecast/regional/{season}_{str(iyear)}/output/",
			"postpp_path": forecast_path_dryp_postpp+"/",#f"forecast/regional/{season}_{str(iyear)}/postpp/",
		}
		HyCast_input["forecasting"] = forecasting_input

		#default_historical = {
		#	"model_name": "historical model",
		#	"main_path": f"forecast/regional/{season}_{str(iyear)}/",
		#	"model_path": f"forecast/regional/{season}_{str(iyear)}/output/",
		#	"postpp_path": f"forecast/regional/{season}_{str(iyear)}/postpp/",
		#}

		#historical_config = cuwalid_config.get("historical", default_historical)
		#HyCast_input["historical"] = historical_config

		HyCast_input["season"] = cuwalid_config["season"]
		#HyCast_input["start_year"] = cuwalid_config["start_year"]
		#HyCast_input["end_year"] = cuwalid_config["end_year"]
		HyCast_input["year"] = cuwalid_config["year"]
		#HyCast_input["nsim"] = cuwalid_config["NSIM"]
		HyCast_input["nsim"] = cuwalid_config["NSIM_HYDRO"]

		run_hydro_forecast(HyCast_input)

		# =====================================================================
		# Run impact forecasting
		# =====================================================================
		print("Executing Impact-based water forecasting: ImCast")
		# Open json config
		with open(ImCast_input_path, 'r') as file:
			ImCast_input = json.load(file)

		# Modify variables to intergrate previous outputs
		ImCast_input["seasons"] = cuwalid_config["season"]
		ImCast_input["year"] = cuwalid_config["year"]
		ImCast_input["model_name"] = forecast_model_name
		ImCast_input["output_dir"] = forecast_path_dryp_postpp

		# make a copy of impact forecast files
		iImCast_input = ImCast_input.copy()

		if sim_in_parallel: # parallelise the map plotting for speeding up map generation
			print("Running map plotting in parallel")
			for icountry in ImCast_input["country"]:
				for iwater in ImCast_input["water_status"]:
					for ilanguage in ImCast_input.get("language", ["English"]):
						
						# Modify variables to make one specific map
						iImCast_input["language"] = [ilanguage]
						iImCast_input["water_status"] = [iwater]
						iImCast_input["country"] = [icountry]
						
						forecasting_folder = os.path.join(temp_folder, "plot_jsons")
						os.makedirs(forecasting_folder, exist_ok=True)  
						ifsim_forecasting_file = os.path.join(forecasting_folder, f"map_input_{icountry}_{iwater}_{ilanguage}.json")
						print("Creating map for:")
						print(icountry, iwater, ilanguage)
						
						flog = os.path.join("logs", f"{icountry}_{iwater}_{ilanguage}.out")
						with open(ifsim_forecasting_file, "w") as ImCast_input_file:
							#json.dump(dryp_data, dest_file, indent=4)
							json.dump(iImCast_input, ImCast_input_file, indent=4)
						
						time.sleep(5)
						# Command to run the DRYP simulation in the background
						command = f"nohup python -u -m cuwalid.forecasting.main_impact_forecast {ifsim_forecasting_file} > {flog}&"
						print(f"Executing: {command}")
						print(command)
						process = subprocess.Popen(command, shell=True)
		else: # plot maps in sequence
			print("Running map plotting in sequence")
			fcast.plot_maps_json(ImCast_input)


if __name__ == '__main__':
	# Set up argument parser to get the JSON config file from command line
	parser = argparse.ArgumentParser(description="Execute CUWALID based on JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	# Run the cuwalid forecast function with the config file provided by the user
	run_cuwalid(args.config_file)