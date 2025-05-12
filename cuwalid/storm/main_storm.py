import json
import sys
from cuwalid.storm.rainfall import wrapper
from cuwalid.storm.checks_ import welcome, assertion
from cuwalid.storm.parameters import *

def run_storm(json_input):

    if type(json_input) == str:
        # Load JSON data
        with open(json_input, 'r') as file:
            config = json.load(file)
    else:
        config = json_input

    NUMSIMS = config["NUMSIMS"]
    NUMSIMYRS= config["NUMSIMYRS"]
    SEASON_TAG = config["SEASON_TAG"]
    SEED_YEAR = config["SEED_YEAR"]
    OUT_PATH = config["OUT_PATH"]
    TER_FILE = config["TER_FILE"]
    PDF_FILE = config["PDF_FILE"]
    DEM_FILE = config["DEM_FILE"]
    SHP_FILE = config["SHP_FILE"]
    ZON_FILE = config["ZON_FILE"]
    
    # Get option for parallel processing
    sim_in_parallel = config.get("sim_in_parallel", False)


    willkommen = welcome(NUMSIMS, NUMSIMYRS, SEED_YEAR, SEASON_TAG, OUT_PATH)
    assertion(willkommen.wet_hash, NUMSIMS, NUMSIMYRS, DEM_FILE, SHP_FILE)
    NC_NAMES = willkommen.ncs
    
    wrapper(
        NC_NAMES, SEED_YEAR, NUMSIMS, NUMSIMYRS, SEASON_TAG, TER_FILE, PDF_FILE, SHP_FILE, ZON_FILE, sim_in_parallel
    )


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python <script_name.py> <path_to_config.json>")
        sys.exit(1)
    
    config_file = sys.argv[1]

    run_storm(config_file)