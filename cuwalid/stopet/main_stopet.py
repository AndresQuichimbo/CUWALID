import os
import datetime as dt
import sys
from cuwalid.stopet.helper_functions import check_missing_files, load_config
from cuwalid.stopet.run_stoPET_4dryp import run_stoPET_4_dryp
from cuwalid.stopet.run_stoPET_inHPC import run_stoPET_in_hpc

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

    execution_type = config['execution_type']

    if execution_type not in ['dryp', 'hpc']:
        print("Error: Invalid 'execution_type'. Please choose 'dryp' or 'hpc'.")
        sys.exit(1)

    # Extract parameters from the config
    slice_only = config.get('slice_only', 1)
    outputpath = config['outputpath']
    runtype = config['runtype']
    startyear = config['startyear']
    endyear = config['endyear']
    seasonswitch = config['seasonswitch']
    startdate = config['startdate']
    enddate = config['enddate']
    latval = config['latval']
    lonval = config['lonval']
    latval_min = config['latval_min']
    latval_max = config['latval_max']
    lonval_min = config['lonval_min']
    lonval_max = config['lonval_max']
    locname = config['locname']
    print(f'locname={locname}')
    number_ensm = config['number_ensm']
    tempAdj = config['tempAdj']
    deltat = config['deltat']
    udpi_pet = config['udpi_pet']

    if execution_type == 'dryp':
        run_stoPET_4_dryp(
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
            slice_only=slice_only
        )
    elif execution_type == 'hpc':
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
            slice_only=slice_only
        )

    print('Seasonal PET extraction finished successfully.')

    # End the run and print the runtime
    end = dt.datetime.now()
    print('Time of run: %s' % (end - start))


# Command-line execution
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python <script_name.py> <path_to_config.json>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    run_stoPET(config_file)
