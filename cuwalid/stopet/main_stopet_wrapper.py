import os
import datetime as dt
import sys
from cuwalid.stopet.helper_functions import check_missing_files, load_config
from cuwalid.stopet.run_stoPET_inHPC import run_stoPET_in_hpc
from cuwalid.stopet.pet_forecast_generation import forecast_wrapper

def run_stoPET(config_file):
    start = dt.datetime.now()

    # Get stopet parameter files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datapath = os.path.join(script_dir, 'stopet_parameters')

    # Check for the presence of required data files
    required_files = [
        'dpetdt.nc', 'hpet_slope.nc', 'meanshift_had.nc', 
        'monthly_cont_percentage.nc', 'stdshift_had.nc', 'stopet_parameters.nc'
    ]
    missing_files = check_missing_files(datapath, required_files)

    # Stop execution if files are missing
    if missing_files:
        print("Error: Some necessary parameter files are missing.")
        print("Please run the command below to download:")
        print("python -m cuwalid.tools.download_data")
        sys.exit(1)

    # Load configuration file
    if type(config_file) == str:
        config = load_config(config_file)
    else:
        config = config_file

    execution_type = config.get('execution_type', None)

    if execution_type:
        print("Execution type is not depreciated as both methods are combined now. Please feel free to delete it from the config file.")

    # Extract parameters from the config
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

    # Run StoPET
    run_stoPET_in_hpc(
        datapath=datapath,
        outputpath=outputpath,
        runtype=runtype,
        startyear=startyear,
        endyear=endyear,
        seasonswitch=seasonswitch,
        startdate=startdate,
        enddate=enddate,
        latval=latval,
        lonval=lonval,
        latval_min=latval_min,
        latval_max=latval_max,
        lonval_min=lonval_min,
        lonval_max=lonval_max,
        locname=locname,
        number_ensm=number_ensm,
        tempAdj=tempAdj,
        deltat=deltat,
        udpi_pet=udpi_pet,
        slice_only=slice_only,
        season_name=season_name,
        temp_path = temp_path
    )

    print('Seasonal PET extraction finished successfully.')

    # === Postprocessing ===
    print("Converting StoPET output into files for DRYP...")


    # Convert the StoPET output files for DRYP
    forecast_path_stopet_output = config['outputpath']  # Example path
    season = config['seasonName']
    iyear = config['startyear']  # or whatever year is needed
    start_day = config['startdate']
    end_day = config['enddate']
    nsim = config['number_ensm']
    forecast_wrapper(
        config["tercile_forecast_file"], 
        forecast_path_stopet_output, 
        iyear, start_day, end_day,  # Dates
        config["locname"],  # Location name
        nsim, config["tempAdj"],  # Temperature adjustments
        season, config["temp_path"]
    )

    print("Postprocessing completed.")

    # End the run and print the runtime
    end = dt.datetime.now()
    print('Total runtime: %s' % (end - start))


# Command-line execution
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python <script_name.py> <path_to_config.json>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    run_stoPET(config_file)
