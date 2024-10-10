import os
import json

# This function loads the configuration from the JSON file
def load_config(input_file):
    with open(input_file, 'r') as f:
        config = json.load(f)
    return config

# This function checks for the presence of required files and prints a warning if files are missing
def check_missing_files(datapath, required_files):
    missing_files = [file for file in required_files if not os.path.exists(os.path.join(datapath, file))]
    if missing_files:
        print("Warning: The following required data files are missing:")
        for file in missing_files:
            print(f" - {file}")
        print("Please run the following command to download the necessary files:")
        print("    python -m cuwalid.tools.download_data")
    return missing_files

# Helper function for folder creation
def create_output_folder(root_outputpath, trial_number):
    output_folder = os.path.join(root_outputpath, f'result_R{trial_number}/')
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
    return output_folder