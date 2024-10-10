# READ ME
#This config file is used to provide all the required 
# data and parameters to run the stoPET model and generate the 
# required seasonl forecasts accounting for the ICPAC temerature forecast
# given as a seasonal probability. 

# This will be used in both running the run_stoPET.py to generate multiple files
# of forecast pools with above, normal and below average forecasts.
# and finally use d in the forecast_generation.py for producing the final
# PET forecasts for the season accounting ICPAC temperature forecast.

## ----- CHANGE THE INPUT VARIABLES HERE -----##
# this is the data pathe where the stoPET parameter files are keept
datapath = '/user/home/fp20123/v2_stopet/stopet_parameter_files/'

# this is the output path where you want to keep the generated PET files
root_outputpath = '/user/work/fp20123/v2_stopet/'


# this is where you decide wherether to run a 'regional' model or 'single' point model
runtype =  'regional' 

# the number of years to generate data for
startyear = 2022
endyear = 2022
  
# this is the seasonal julian dates required as a start date and end date
seasonswitch = 1 
startdate = 274 
enddate = 365
seasonName = 'OND'

# Single point stoPET run
latval = 1.0
lonval = 35.0

# Regional stoPET run (Kenya)
latval_min = -7.0
latval_max = 16.0
lonval_min = 31.0
lonval_max = 52.1 

# this is the final number of ensembles you will have
# this is how many times the model will run to generate
# a weighted PET value by ICPAC forecast.
trial_number = 6
# this is the number of ensembles you want to generate
# with in each realization
# HERE THE NUMBER SHOULD BE DIVISIBLE BY 3
number_ensm = 3

# this is the method you use for adjusting the PET to account for change in temperature
tempAdj = 2

# this is the change in temperature you prefer to have if you use tempAdj = 2
deltat = 0.0

# this is where you provide a sting of name to identify your region or point e.g. 'tana_basin'
locname = 'HAD' 

# this is the user defined percentage change in PET if you use tempAdj = 1
udpi_pet = 5

# This is the file containing the ICPAC seasonal tercile temperature forecast.
# provide the full path where it is located
tercile_forecast_file = '/user/home/fp20123/v2_stopet/ICPAC_TempF_OND2022_HAD.nc'    


  


