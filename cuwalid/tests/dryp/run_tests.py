import subprocess
import platform
import os

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, 'scripts')

# Define the list of shell commands with absolute paths
commands = [
    f"python {os.path.join(scripts_dir, 'test_precipitation.py')}",
    f"python {os.path.join(scripts_dir, 'test_precipitation_csv.py')}",
    f"python {os.path.join(scripts_dir, 'test_infiltration.py')}",
    f"python {os.path.join(scripts_dir, 'test_soil_layer.py')}",
    f"python {os.path.join(scripts_dir, 'test_flow_accum_fortran.py')}",
    f"python {os.path.join(scripts_dir, 'test_gw_sw_interaction.py')}",
    f"python {os.path.join(scripts_dir, 'test_groundwater_multyaq_ss.py')}",
    f"python {os.path.join(scripts_dir, 'test_groundwater_multyaq.py')}",
    f"python {os.path.join(scripts_dir, 'test_groundwater_ss_slopefactor.py')}",
    f"python {os.path.join(scripts_dir, 'test_groundwater.py')}",
    f"python {os.path.join(scripts_dir, 'test_save_necdf.py')}",
    f"python {os.path.join(scripts_dir, 'test_save_csv.py')}",
    f"python {os.path.join(scripts_dir, 'test_dryp_model.py')}",
    f"python {os.path.join(scripts_dir, 'test_dryp_tilted_V.py')}",
    f"python {os.path.join(scripts_dir, 'test_dryp.py')}",
    f"python {os.path.join(scripts_dir, 'test_basin_delineation.py')}"
]

# Function to run commands based on platform
def run_commands(commands):
    for cmd in commands:
        print(f"Running command: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running command: {cmd}")
            print(f"Return code: {e.returncode}")
            print(f"Output: {e.output}")
            print(f"Error output: {e.stderr}")

run_commands(commands)
