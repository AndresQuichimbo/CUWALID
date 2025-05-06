import sys
import json
import os
import numpy as np
from cuwalid.stopet.run_stoPET_inHPC import run_stoPET_in_hpc
from cuwalid.stopet.stoPET_v2_4dryp import mean_shift_rand_values, stoPET_wrapper_singlepoint, stoPET_wrapper_regional

def run_stopet_for_ensemble(json_path, ens_index):
    # Load config
    with open(json_path, 'r') as f:
        config = json.load(f)

    # Get stopet parameter files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datapath = os.path.join(script_dir, '..', 'stopet', 'stopet_parameters')

    # Extract config values
    slice_only = config.get('slice_only', 1)
    outputpath = config['outputpath']
    runtype = config['runtype']
    startyear = config['startyear']
    endyear = config['endyear']
    seasonswitch = config['seasonswitch']
    startdate = int(config['startdate'])
    enddate = int(config['enddate'])
    latval = config['latval']
    lonval = config['lonval']
    latval_min = config['latval_min']
    latval_max = config['latval_max']
    lonval_min = config['lonval_min']
    lonval_max = config['lonval_max']
    locname = config['locname']
    number_ensm = config['number_ensm']
    tempAdj = config['tempAdj']
    deltat = config['deltat']
    udpi_pet = config['udpi_pet']
    season_name = config['seasonName']
    temp_path = config.get("temp_path", "")

    if ens_index >= number_ensm:
        print(f"Ensemble index {ens_index} exceeds total ensemble size {number_ensm}")
        return

    # Get extra noise
    extra_noise = mean_shift_rand_values(datapath, number_ensm, startyear, endyear)
    randnoise = extra_noise[:, ens_index, :, :, :]  # one ensemble

    print(f"Running StoPET for ensemble {ens_index}")

    if runtype == 'single':
        stoPET_wrapper_singlepoint(
            startyear, endyear, latval, lonval, locname,
            ens_index, datapath, outputpath, tempAdj, deltat, udpi_pet
        )
    elif runtype == 'regional':
        stoPET_wrapper_regional(
            startyear, endyear, latval_min, latval_max, lonval_min, lonval_max,
            locname, ens_index, datapath, outputpath, tempAdj, deltat, udpi_pet,
            seasonswitch, randnoise, temp_path
        )
    else:
        raise ValueError("runtype must be 'single' or 'regional'")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_stopet_single.py <stopet_input.json> <ensemble_index>")
        sys.exit(1)

    json_path = sys.argv[1]
    ens_index = int(sys.argv[2])
    run_stopet_for_ensemble(json_path, ens_index)
