import subprocess
import platform

# Define the list of shell commands
commands = [
    "python scripts/test_precipitation.py",
    "python scripts/test_precipitation_csv.py",
    "python scripts/test_infiltration.py",
    "python scripts/test_soil_layer.py",
    "python scripts/test_flow_accum_fortran.py",
    "python scripts/test_gw_sw_interaction.py",
    "python scripts/test_groundwater_multyaq_ss.py",
    "python scripts/test_groundwater_multyaq.py",
    "python scripts/test_groundwater_ss_slopefactor.py",
    "python scripts/test_groundwater.py",
    "python scripts/test_save_necdf.py",
    "python scripts/test_save_csv.py",
    "python scripts/test_dryp_model.py",
    "python scripts/test_dryp_tilted_V.py",
    "python scripts/test_dryp.py",
    "python scripts/test_basin_delineation.py"
]

# Function to run commands based on platform
def run_commands(commands):
    for cmd in commands:
        print(f"Running command: {cmd}")
        subprocess.run(cmd, shell=True, check=True)

# Check platform and execute commands
if platform.system() == "Windows" or platform.system() == "Linux":
    run_commands(commands)
else:
    print("Unsupported platform. Please run these commands manually.")
