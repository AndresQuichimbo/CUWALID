import argparse
import json
import os
import numpy as np
import cuwalid.tools.CUWALID_json_builder as JSON_builder
import cuwalid.tools.CUWALID_mfile_tools as cuwalid_mtools
from cuwalid.tools.CUWALID_make_dirs import create_directory_structure
from cuwalid.storm.pdfs_ import compute_icpac, masking
from cuwalid.tools.generate_bash_scripts import write_bash

def generate_jsons(config_path):
    with open(config_path, 'r') as file:
        cuwalid_config = json.load(file)

    forecast_path = cuwalid_config["output_dir"]
    season = cuwalid_config['season'][0]
    iyear = cuwalid_config["year"]
    nsim = cuwalid_config["NSIM"]
    storm_tercile_file = cuwalid_config["Tercile_Pre_path"]
    stopet_tercile_file = cuwalid_config["Tercile_Tem_path"]
    start_date, end_date = cuwalid_mtools.get_dates_season(season, iyear)
    start_day, end_day = cuwalid_mtools.date_to_day_of_year(start_date), cuwalid_mtools.date_to_day_of_year(end_date)

    create_directory_structure(forecast_path, season, iyear)

    # Paths
    temp_folder = os.path.join(forecast_path, "temp")
    forecast_path_storm_output = os.path.join(forecast_path, f"{season}_{iyear}", "dataset/pre/")
    forecast_path_stopet_output = os.path.join(forecast_path, f"{season}_{iyear}", "dataset/pet/")
    forecast_path_dryp_model = os.path.join(forecast_path, f"{season}_{iyear}", "model")
    forecast_path_dryp_output = os.path.join(forecast_path, f"{season}_{iyear}", "output")

    # === STORM JSON generation ===
    storm_jsons = []
    if cuwalid_config["run_STORM"]:
        print("Preparing STORM inputs...")
        with open(cuwalid_config["MODELS"]["STORM"]["input"], 'r') as file:
            storm_input = json.load(file)

        storm_input["SEASON_TAG"] = season
        storm_input["SEED_YEAR"] = iyear
        storm_input["NUMSIMS"] = nsim
        storm_input["OUT_PATH"] = forecast_path_storm_output
        storm_input["TER_FILE"] = os.path.join(forecast_path_storm_output, f"tercilesICPAC_{season}_{iyear}.shp")

        space = masking(storm_input["SHP_FILE"])
        compute_icpac(space, storm_tercile_file, storm_input["TER_FILE"], storm_input["ZON_FILE"])

        storm_json_path = os.path.join(forecast_path_storm_output, f"storm_input_{season}_{iyear}.json")
        with open(storm_json_path, 'w') as f:
            json.dump(storm_input, f, indent=4)
        storm_jsons.append(storm_json_path)

    # === StoPET JSON generation ===
    stopet_jsons = []
    if cuwalid_config["run_stoPET"]:
        print("Preparing StoPET inputs...")
        with open(cuwalid_config["MODELS"]["stoPET"]["input"], 'r') as file:
            stopet_input = json.load(file)

        stopet_input.update({
            "outputpath": forecast_path_stopet_output,
            "temp_path": temp_folder,
            "startyear": iyear,
            "endyear": iyear,
            "startdate": start_day,
            "enddate": end_day,
            "number_ensm": nsim,
            "seasonName": season,
            "tercile_forecast_file": stopet_tercile_file,
        })

        stopet_json_path = os.path.join(forecast_path_stopet_output, f"stopet_input_{season}_{iyear}.json")
        with open(stopet_json_path, 'w') as f:
            json.dump(stopet_input, f, indent=4)
        stopet_jsons.append(stopet_json_path)

    # === DRYP JSON generation ===
    dryp_jsons = []
    if cuwalid_config["run_DRYP"]:
        print("Preparing DRYP simulation JSONs...")
        with open(cuwalid_config["MODELS"]["DRYP"]["input"], 'r') as file:
            dryp_input = json.load(file)

        model_names = [f"{season}_{iyear}_realization_{i}" for i in range(nsim)]
        setting_file = os.path.join(forecast_path_dryp_model, f"Hydro_model_forecast_settings_{season}_{iyear}.json")
        json_paths = [os.path.join(forecast_path_dryp_model, f"Hydro_model_forecast_input_{season}_{iyear}_{i}.json") for i in range(nsim)]

        pet_files = [os.path.join(forecast_path_stopet_output, f"Forecast_PET_HAD_ens_{iyear}_{season}_{i}.nc") for i in range(nsim)]
        pre_files = [os.path.join(forecast_path_storm_output, f"Forecast_PRE_HAD_ens_{iyear}_{season}_{i}.nc") for i in range(nsim)]

        forcing_list = np.array(JSON_builder.create_ensamble([pet_files, pre_files], nsamples=nsim))

        for dryp_json, model_name, pre_path, pet_path in zip(json_paths, model_names, forcing_list[:, 1], forcing_list[:, 0]):
            JSON_builder.write_JSON_dryp_files(
                json_template=dryp_input,
                model_name=model_name,
                path_pre=pre_path,
                path_pet=pet_path,
                json_destination=dryp_json,
                dryp_output=forecast_path_dryp_output,
                start_date=start_date,
                end_date=end_date,
                new_setting_file=setting_file,
            )
            dryp_jsons.append(dryp_json)

    # === Write lists of generated JSON files ===
    def write_list_file(file_list, file_path):
        with open(file_path, "w") as f:
            for path in file_list:
                f.write(path + "\n")

    print("Writing JSON file lists...")
    write_list_file(storm_jsons, os.path.join(forecast_path, "storm_jsons.txt"))
    write_list_file(stopet_jsons, os.path.join(forecast_path, "stopet_jsons.txt"))
    write_list_file(dryp_jsons, os.path.join(forecast_path, "dryp_jsons.txt"))

    print("All JSONs generated and file lists saved.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate JSON files for STORM, StoPET, and DRYP.")
    parser.add_argument("config_file", type=str, help="Path to CUWALID configuration JSON")
    args = parser.parse_args()
    generate_jsons(args.config_file)
