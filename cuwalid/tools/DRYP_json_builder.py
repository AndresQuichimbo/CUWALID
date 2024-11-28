
import json
import numpy as np


def write_JSON_dryp_file(json_template, model_name, path_pre, path_pet, start_date="2024 03 01", end_date="2024 05 31", destination=None, new_setting_file=None):

	# Change necesarry variables in template
	json_template["dryp"]["model_name"] = model_name
	json_template["dryp"]["METEO"]["path_pre"] = path_pre
	json_template["dryp"]["METEO"]["path_pet"] = path_pet

	
	# create new settings file
	if new_setting_file is not None:
		# Change settings file location
		json_template["dryp"]["OUTPUT"]["path_setting"] = new_setting_file
		# Change variables in settings file
		json_template["dryp_settings"]["SIMULATION_PERIOD"]["start_date"] = start_date
		json_template["dryp_settings"]["SIMULATION_PERIOD"]["end_date"] = end_date

	# Save the `dryp` part to the destination file
	if destination is not None:
		dryp_data = json_template["dryp"]
		with open(destination, "w") as dest_file:
			json.dump(dryp_data, dest_file, indent=4)

	# Save the `dryp_settings` part to the new settings file
	if new_setting_file is not None:
		dryp_settings_data = json_template["dryp_settings"]
		with open(new_setting_file, "w") as settings_file:
			json.dump(dryp_settings_data, settings_file, indent=4)
		



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