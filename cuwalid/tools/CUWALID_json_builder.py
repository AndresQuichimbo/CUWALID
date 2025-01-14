
import json
import numpy as np
import calendar

def write_JSON_dryp_files(json_template, model_name, path_pre, path_pet, destination, path_outputs=None,
						   start_date="2024 03 01", end_date="2024 05 31", new_setting_file=None):
	""" This function create the simulation and setting file for running DRYP. New
	files are created  based on files provided as original files, this function
	changes the model name, precipitation and potential evapotranspiration
	paths.
	WARNING: if no new filename is provided it will replace the original file
	
	Parameters:
	-----------
	json_template : string
			model input, as a dictionary
	model_name : string
			model name for the new file
	path_pre : string
			precipitation dataset name, including path
	path_pet : string
			potential evapotranspiration dataset name, including path
	start_date : string
			date in the following format "YYYY-MM-DD" (e.g. 2002-01-01)
	end_date : string
			date in the following format "YYYY-MM-DD" (e.g. 2002-03-01)
	new_setting_file : bool
			If True it create the setting dryp file
	"""

	# Change necesarry variables in template
	json_template["model_name"] = model_name
	json_template["METEO"]["path_pre"] = path_pre
	json_template["METEO"]["path_pet"] = path_pet

	if path_outputs is not None:
		json_template["OUTPUT"]["path_output"] = path_outputs
	
	
	# create new settings file
	if new_setting_file is not None:

		# Get input file as dictionary
		settings_file_path = json_template["OUTPUT"]["path_setting"]
		with open(settings_file_path, 'r') as file:
			settings_file_template = json.load(file)
		# Change settings file location
		json_template["OUTPUT"]["path_setting"] = new_setting_file
		
		## Change variables in settings file
		#json_template["dryp_settings"]["SIMULATION_PERIOD"]["start_date"] = start_date
		#json_template["dryp_settings"]["SIMULATION_PERIOD"]["end_date"] = end_date
		settings_file_template["SIMULATION_PERIOD"]["start_date"] = start_date
		settings_file_template["SIMULATION_PERIOD"]["end_date"] = end_date


	# Save the `dryp` part to the json_destination file
	#dryp_data = json_template["dryp"]
	with open(json_destination, "w") as dest_file:
		#json.dump(dryp_data, dest_file, indent=4)
		json.dump(json_template, dest_file, indent=4)

	# Save the `dryp_settings` part to the new settings file
	if new_setting_file is not None:
		#dryp_settings_data = settings_file_template["dryp_settings"]
		#dryp_settings_data = json_template["dryp_settings"]
		with open(new_setting_file, "w") as settings_file:
			#json.dump(dryp_settings_data, settings_file, indent=4)
			json.dump(settings_file_template, settings_file, indent=4)


def write_JSON_dtorm_file(json_template, model_name, path_pre, path_pet, destination, start_date="2024 03 01", end_date="2024 05 31", new_setting_file=None):
	""" This function create the simulation and setting file for running DRYP. New
	files are created  based on files provided as original files, this function
	changes the model name, precipitation and potential evapotranspiration
	paths.
	WARNING: if no new filename is provided it will replace the original file
	
	Parameters:
	-----------
	json_template : string
			model input, as a dictionary
	model_name : string
			model name for the new file
	path_pre : string
			precipitation dataset name, including path
	path_pet : string
			potential evapotranspiration dataset name, including path
	start_date : string
			date in the following format "YYYY-MM-DD" (e.g. 2002-01-01)
	end_date : string
			date in the following format "YYYY-MM-DD" (e.g. 2002-03-01)
	new_setting_file : bool
			If True it create the setting dryp file
	"""

	pass

def write_JSON_stopet_file(json_template, model_name, path_pre, path_pet, destination, start_date="2024 03 01", end_date="2024 05 31", new_setting_file=None):
	""" This function create the simulation and setting file for running DRYP. New
	files are created  based on files provided as original files, this function
	changes the model name, precipitation and potential evapotranspiration
	paths.
	WARNING: if no new filename is provided it will replace the original file
	
	Parameters:
	-----------
	json_template : string
			model input, as a dictionary
	model_name : string
			model name for the new file
	path_pre : string
			precipitation dataset name, including path
	path_pet : string
			potential evapotranspiration dataset name, including path
	start_date : string
			date in the following format "YYYY-MM-DD" (e.g. 2002-01-01)
	end_date : string
			date in the following format "YYYY-MM-DD" (e.g. 2002-03-01)
	new_setting_file : bool
			If True it create the setting dryp file
	"""

	pass


def create_ensamble(pools, nsamples=30):
	"""
	Parameters
	-----------
	forecast_pet: path-list for forecasted evapotranspiration
	forecast_pet: path-list for forecasted precipitation
	"""
	#print(sorted(glob.glob(f'{forecast_pet}/*_MAM_*.nc')))
	#pools = list(map(lambda x: sorted(glob.glob(f'{x}/*_MAM_*.nc')), [forecast_pet, forecast_pre]))
	#print(pools)
	plist = np.asarray([f'{x}+{y}+' for x in pools[0] for y in pools[1]])
	# the sampling is done here
	#what_ = np.random.default_rng().choice(plist, size=nsamples, replace=False).tolist()
	what_ = np.random.default_rng(seed=42).choice(plist, size=nsamples, replace=False).tolist()
	# returns a list of nsamples-pairs, e.g., [['pet_20', 'pre_1'], ['pet_0', 'pre_29'], [...], ...]
	pairs = list(map(lambda x: x.split('+'), what_))
	return pairs



def last_day_of_month(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return last_day
