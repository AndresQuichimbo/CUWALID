import json
import sys
from cuwalid.storm.rainfall import wrapper
from cuwalid.storm.checks_ import welcome

def run_storm(json_input):

    if type(json_input) == str:
        # Load JSON data
        with open(json_input, 'r') as file:
            config = json.load(file)
    else:
        config = json_input

    willkommen = welcome(config["NUMSIMS"], config["NUMSIMYRS"], config["PTOT_SC"], config["PTOT_SF"], config["STORMINESS_SC"], config["STORMINESS_SF"], config["OUT_PATH"], )
    NC_NAMES = willkommen.ncs
    
    wrapper(
        NC_NAMES, config
    )


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python <script_name.py> <path_to_config.json>")
        sys.exit(1)
    
    config_file = sys.argv[1]

    run_storm(config_file)