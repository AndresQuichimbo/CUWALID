import json
import os
import sys
from cuwalid.stopet.pet_forecast_generation import forecast_wrapper
from cuwalid.stopet.stoPET_v2_4dryp import seasonal_pet_for_dryp

def postprocessing_stopet(json_path):
    with open(json_path, 'r') as f:
        config = json.load(f)

    if not config.get("tercile_forecast_file"):
        print("No tercile_forecast_file defined in input JSON. Skipping.")
        return

    # Load necessary params
    tercile_file = config["tercile_forecast_file"]
    output_path = config["outputpath"]
    locname = config["locname"]
    tempAdj = config["tempAdj"]
    season = config.get("season_name", "unknown")
    temp_path = config.get("temp_path", "")
    seasonswitch = config['seasonswitch']
    season_name = config['seasonName']

    startyear = int(config["startyear"])
    endyear = int(config["endyear"])
    nsim = int(config["number_ensm"])
    nsim *= 2  # because StoPET doubles them

    print("Checking for ensemble outputs...")

    # Optionally validate that all ensemble outputs exist
    missing = []
    for i in range(nsim):
        expected_file = os.path.join(output_path, f"PET_sim{i}.nc")
        if not os.path.exists(expected_file):
            missing.append(expected_file)

    if missing:
        print(f"Warning: {len(missing)} missing ensemble output files.")
        for f in missing:
            print(f" - {f}")
        sys.exit(1)

    print("All ensemble outputs present. Running forecast wrapper...")

    seasonal_pet_for_dryp(output_path, locname, nsim, tempAdj, startyear, endyear, config["startdate"], config["enddate"], seasonswitch, season_name, temp_path)

    forecast_wrapper(
        tercile_file,
        output_path,
        startyear,
        config["startdate"],
        config["enddate"],
        locname,
        nsim,
        tempAdj,
        season,
        temp_path
    )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python postprocess_stopet.py <stopet_input.json>")
        sys.exit(1)
    postprocessing_stopet(sys.argv[1])
