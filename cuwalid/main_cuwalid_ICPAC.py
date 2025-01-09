import argparse
import json
import os
import subprocess
import sys
sys.path.append("/home/cuwalid/CUWALID")
import numpy as np
from cuwalid.storm.main_storm import run_storm
from cuwalid.storm.pdfs_ import compute_icpac, masking
from cuwalid.stopet.main_stopet import run_stoPET
from cuwalid.dryp.main_DRYP import run_DRYP
from cuwalid.forecasting.main_hydro_forecast import run_hydro_forecast
import cuwalid.forecasting.main_impact_forecast as fcast
from cuwalid.tools.DRYP_json_builder import create_ensamble, write_JSON_dryp_file
import cuwalid.tools.CUWALID_json_builder as JSON_builder
import cuwalid.tools.CUWALID_mfile_tools as cuwalid_mtools

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

	# read storm input file path
	storm_file = cuwalid_config["Tercile_Tem_path"]

	# read stopet input file path
	tercile_forecast_file = cuwalid_config["Tercile_Pre_path"]

	#threshold_path = historical_postpp_path + "netcdf/"+ historical_model_name+ "_SSS_extremes_quantiles.nc"

	season = cuwalid_config['season'][0]
	#start_year = cuwalid_config['start_year']
	#end_year = cuwalid_config['end_year']
	#variables = cuwalid_config['variables']
	iyear = cuwalid_config["year"]
	nsim = cuwalid_config["NSIM"]
	start_date, end_date = cuwalid_mtools.get_dates_season(season, iyear)

	# SET UP MODEL PATHS
	# Leo make sure that this folder exist otherwise create new ones
	# I guess ww should also ask if (using a boolead entry) if this paths need to 
	# be updated in the dryp, storm, or stopet.
	forecast_path_storm_output = forecast_path + "dataset/pre/"+season+"_"+str(iyear)+"/"
	forecast_path_stopet_output = forecast_path + "postpp/pet/"+season+"_"+str(iyear)+"/"
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

		# Convert .nc file into .shp
		space = masking(catchment=storm_input["SHP_FILE"])
		output_name = f"Ens_Prec_*{storm_input["SEASON_TAG"]}*-avgRaw{storm_input["SEED_YEAR"]}.nc"
		compute_icpac(space, storm_input["TER_FILE"], storm_input["SEED_YEAR"], storm_input["SEASON_TAG"], "", output_name)

		run_storm(storm_input)

		# add code to modify input files
		# set up path for model putputs
		# set up model simulation name outputs
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
		stoPET_input["startyear"] = iyear
		stoPET_input["startdate"] = start_date
		stoPET_input["enddate"] = end_date
		stoPET_input["trial_number"] = nsim
		stoPET_input["seasonName"] =season
		stoPET_input["tercile_forecast_file"] = tercile_forecast_file

		run_stoPET(stoPET_input)

	else:
		print("stoPET is not executed")

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
	# create model settings file names for realizations
	#fname_setting_file = "/home/cuwalid/training/forecast/regional/model/HAD_IMERG_par_setting_"+season+"_"+str(iyear)+".json"
	fname_setting_file = forecast_path_dryp_model+"Hydro_model_forecast_settings_"+season+"_"+str(iyear)+".json"
	# create model parameter file names for realizations
	#fsim_forecasting = ["/home/cuwalid/training/forecast/regional/model/HAD_IMERG_input_test_"+season+"_"+str(iyear)+"_forecast_"+str(isim)+".json" for isim in range(nsim)]
	fsim_forecasting = [forecast_path_dryp_model+"Hydro_model_forecast_input_"+ season +"_"+str(iyear)+ "_" +str(isim)+".json" for isim in range(nsim)]
	
	# set paths of forcing datasets and names
	#forecast_path_stopet_output = "/home/cuwalid/training/forecast/regional/dataset/pet/"+season+"_"+str(iyear)+"_PET_forecast/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"
	#forecast_path_storm_output = "/home/cuwalid/training/forecast/regional/dataset/pre/"+season+"_"+str(iyear)+"/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"
	#forecast_path_storm_output = "/home/cuwalid/leo_test/CUWALID/storm_output/"+season+"_"+str(iyear)+"/"#Forecast_PET_HAD_ens_0_MAM_2024.nc"

	local_directory = "/home/cuwalid/training/forecast/regional/model/" #D:/HAD/training/regional/model/"
	
	# run DRYP multiple simulations
	if cuwalid_config["run_DRYP"] is True:
		print("Executing DRYP simulations")
		dryp_input_path = cuwalid_config["MODELS"]["DRYP"]["input"]
		dryp_settings_path = cuwalid_config["MODELS"]["DRYP"]["settings"]
		with open(dryp_input_path, 'r') as file:
			dryp_input = json.load(file)
		# get basefile of model parameters and settings files
		#fsim_input_file = local_directory + "HAD_IMERGcv_input_sim85.json"#"HAD_IMERG_input_sim_cuwalid.dmp"
	
		# TODO: Change pet to the same order naming as pre
		fname_pet = [forecast_path_stopet_output+ "Forecast_PET_HAD_ens_" + str(iyear) + "_" + season + "_" + str(isim) + ".nc" for isim in range(nsim)]
		fname_pre = [forecast_path_storm_output + "Forecast_PRE_HAD_ens_" + str(iyear) + "_" + season + "_" + str(isim) + ".nc" for isim in range(nsim)]
		forcing_list = np.array(JSON_builder.create_ensamble([fname_pet, fname_pre], nsamples=nsim))
		for ifsim_forecasting, imname, ifname_pre, ifname_pet in zip(fsim_forecasting, mname, forcing_list[:,1], forcing_list[:,0]):
			#write_JSON_dryp_file(
			JSON_builder.write_JSON_dryp_files(
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
		#fsim_forecasting_list = ["HAD_IMERG_input_"+season+"_"+str(iyear)+"_forecast_"+str(isim)+".json" for isim in range(nsim)]
		#fsim_forecasting_list = ["Hydro_model_forecast_input_"+season+"_"+str(iyear)+ "_" +str(isim)+".json" for isim in range(nsim)]
		
		# LEO change this to a local directory automatically selected
		log_dir = "logs"  # Adjust to your desired log directory
		# Make sure the log directory exists
		os.makedirs(log_dir, exist_ok=True)
		#for ifsim_forecasting in fsim_forecasting_list:
		for ifsim_forecasting in fsim_forecasting:
			# Remove the .json extension for the log file name
			base_name = os.path.splitext(ifsim_forecasting)[0]

			# Generate a unique log file name for each process
			log_file = os.path.join(log_dir, f"{base_name}_output.log")
			# Build the command to run the simulation and redirect both stdout and stderr to the log file
			#command = f"nohup python -m cuwalid.dryp.main_DRYP /home/cuwalid/training/forecast/regional/model/{ifsim_forecasting} > {log_file} 2>&1 &"
			#command = f"nohup python -m cuwalid.dryp.main_DRYP {forecast_path_dryp_model+ifsim_forecasting} > {log_file} 2>&1 &"
			command = f"nohup python -m cuwalid.dryp.main_DRYP {ifsim_forecasting} > {log_file} 2>&1 &"
			print(command)
			# Run the command as a background process using subprocess
			#subprocess.Popen(command, shell=True)
	else:
		print("DRYP is not executed")


	# print add water forecasting entry
	if cuwalid_config["run_WaterCast"] is True:
		print("Executing Water forecasting: WaterCast")
		HyCast_input_path = cuwalid_config["MODELS"]["WaterCast"]["HyCast"]
		ImCast_input_path = cuwalid_config["MODELS"]["WaterCast"]["ImCast"]

		# Add functions to modify paths and names according to the cofiguration files before runing the forecast
		# modify names
		# modify season and year

		print("Executing hydrological forecasting: HyCast")
		#run_hydro_forecast(HyCast_input_path)
		
		print("Executing Impact-based water forecasting: ImCast")
		#fcast.plot_maps_json(ImCast_input_path)

if __name__ == '__main__':
	# Set up argument parser to get the JSON config file from command line
	parser = argparse.ArgumentParser(description="Execute CUWALID based on JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	# Run the cuwalid forecast function with the config file provided by the user
	run_cuwalid(args.config_file)