import numpy as np
import os
import sys
import datetime as dt
from netCDF4 import Dataset, num2date
from numba import jit, njit, prange
import xarray as xr

from cuwalid.stopet.helper_functions import load_config
# this imports all the required parameters
# ===================================== #
# READ ME
# This script is prepared to generate the ensemble forecasts for PET
# based on the seasonal temperature forecast provided by ICPAC.
# Before runnig this script one should have prepared the forecast pools of PET
# by runing the stoPET model first. The number of ensembles provided  here 
# should be equal or less than what is available in each pool of stoPET forecast.

# changes can be made in the function forecast_wrapper()
# the other variables should be similar to the stoPET run exactly as they are used to name files.

def run_pet_forecast(config_file):

    # Load configuration from the JSON file
    config = load_config(config_file)

    # Extract parameters from the config
    tercile_forecast_file = config['tercile_forecast_file']
    root_outputpath = config['root_outputpath']
    startyear = config['startyear']
    startdate = config['startdate']
    enddate = config['enddate']
    locname = config['locname']
    number_ensm = config['number_ensm']
    tempAdj = config['tempAdj']
    seasonName = config['seasonName']
    trial_number = config.get('trial_number', 1)  # Default to 1 if not provided

    # Move the sliced seasonal files to a folder called pool
    move_files(root_outputpath, number_ensm, trial_number, startdate, enddate, tempAdj, locname, startyear)

    # Process each trial for the specified trial number
    for i in range(0, trial_number):
        outputpath = os.path.join(root_outputpath, f'result_R{i}/')
        forecast_wrapper(tercile_forecast_file, root_outputpath, outputpath, startyear, startdate, enddate, locname, number_ensm, tempAdj, seasonName, i)
        print(f'R_{i}')
      

def forecast_wrapper(tercile_forecast_file, root_outputpath, outputpath, startyear, startdate, enddate, locname, number_ensm, tempAdj, seasonName, i):  

  # this will reasd one file ffrom the stoPET output to use as a template for the array length and time E_0_stoPET_2_60_151_2022.nc
  nc = Dataset(outputpath + 'pool/E_0_stoPET_%s_%s_%s_%s.nc'%(tempAdj, startdate, enddate, startyear))
  lats = nc.variables['latitude'][:]
  lons = nc.variables['longitude'][:]
  time = nc.variables['time']
  tunits = time.units
  ori_data = nc.variables['pet'][:,:,:]
  
  # create array to append data
  ens_f = (np.ones((number_ensm, ori_data.shape[0], ori_data.shape[1], ori_data.shape[2]))) * np.nan
  # this is just for now 
  # or_data is used to identify array shape so must be same as the origional
  # stopet generated data array for the season (time,lat,lon)
  
  # Tead  ICPAC forecast and Fill empty values in the array
  # this is required to have some values over the ocean in coastal 
  # areas to set up boundary condition.
  nc = Dataset(tercile_forecast_file) 
  above = fill_masked_ocean_2d(nc.variables['above'][:,:]) #nc.variables['above'][:,:] 
  normal = fill_masked_ocean_2d(nc.variables['normal'][:,:]) #nc.variables['normal'][:,:] 
  below = fill_masked_ocean_2d(nc.variables['below'][:,:]) #nc.variables['below'][:,:]  
  # tercile frorecast array
  # we need the decimal not the percentge so we divide by 100
  # we need the probabilies to bu assiged to each ensemble so 
  # we multiply by  3 / number_ensm. This will be the probability of each ensemble
  # NOTE: always choose ensemble numbers divisble by 3 (6,12,15,30)
  
  tercileTf = ((np.asarray(np.stack([above,normal,below]))) / 100.) * (3. / number_ensm) 
  
  # Read the entire forecast loop as an array (ensemble, time, lat, lon)
  # This is required since the numba jit cant read files but only numpy array
  # Since we are reading all the files of pool it requre storage space
  ens_All = read_forecast_pool(number_ensm, ori_data, outputpath, locname, tempAdj, startdate, enddate, startyear)
  
  # This is a parallel run using numba to redce computational time
  # but since we are reading all the files of pool it requre storage space
  ensembleArray = forecast_with_tercile(tercileTf, number_ensm, ens_All, ens_f)      
  
  # Write the output array into files                        
  writing_forecast_file(ensembleArray, seasonName, locname, startyear, root_outputpath, time, lats, lons, tunits, i) 


def move_files(root_outputpath, number_ensm, trial_number, startdate, enddate, tempAdj, locname, startyear):
  # create a folder to save the copy of the seasonal data
  for i in range(0,trial_number):
    if not os.path.isdir(root_outputpath + 'result_R%s/pool/'%i):
      os.mkdir(root_outputpath + 'result_R%s/pool/'%i)  
  # cppy the ensemble from each realization to a single folder called pool
  for i in range(0,trial_number):
    path = root_outputpath + 'result_R%s/'%i
    for j in range(0,number_ensm):
      command = 'mv %s%s_E%s_StoPET/stoPET_%s_%s_%s_%s.nc %spool/E_%s_stoPET_%s_%s_%s_%s.nc'%(path,locname,j,tempAdj,startdate,enddate,startyear,path,j,tempAdj,startdate, enddate,startyear)
      os.system(command)
  print('Files moved to pool!')


def read_forecast_pool(number_ensm, ori_data, outputpath, locname, tempAdj, startdate, enddate, startyear):
    # create array to append data of each ensembles
    ens_all = (np.ones((number_ensm, ori_data.shape[0], ori_data.shape[1], ori_data.shape[2]))) * np.nan

    # concatenate all ensembles into one single array 
    for ens in range(0,number_ensm):
        # read the file and append to the 4D array
        nc = Dataset(outputpath + 'pool/E_%s_stoPET_%s_%s_%s_%s.nc'%(ens, tempAdj, startdate, enddate, startyear))
        pet = nc.variables['pet'][:,:,:]
        ens_all[ens,:,:,:] = pet
    
    return ens_all


def forecast_with_tercile(tercileTf, number_ensm, ens_All, ens_f):
    
    # make a seasonal sum
    season_sum = np.sum(ens_All, axis=1) # [30, lat,lon]
    
    # find the tercile boundaries 33.33 and 66.67
    p_33 = np.percentile(season_sum, 33.33, axis=0) # [lat, lon]
    p_66 = np.percentile(season_sum, 66.67, axis=0) # [lat, lon]
    
    # Reshape the percentiles to match dimensions for broadcasting
    percentile_33 = p_33[np.newaxis, :, :]  # Now (30, lat, lon)
    percentile_66 = p_66[np.newaxis, :, :]  # Now (30, lat, lon)

    # allocate the tercile ercentage to each grid
    mask_above = season_sum >= percentile_66
    above = np.where(mask_above, tercileTf[0,:,:], tercileTf[1,:,:])
    
    mask_below = season_sum <= percentile_33
    below = np.where(mask_below, tercileTf[2,:,:], above) # [30,lat,lon]
   
    # Multiply the timeseries by the weight
    # Reshape the weights to match dimensions for broadcasting
    below_broadcasted = below[:, np.newaxis, :, :]  # Now (30, 1, lat, lon)
    weighted_val = ens_All * below_broadcasted
    # final weithed average
    weighted_average = np.sum(weighted_val, axis=0) # [2208, lat, lon]
    
    return weighted_average
      
     
def writing_forecast_file(ensembleArray, seasonName, locname, startyear, root_outputpath, time, lats, lons, tunits, i): 
      
  # write the final ensembles on a netcdf file
  # create a folder to save the data
  if not os.path.isdir(root_outputpath + 'ensemble_forecast/'):
    os.mkdir(root_outputpath + 'ensemble_forecast/')
  # file name of the adjusted PET from stopet 
  
  # read the each ensemble array
  data = ensembleArray[:,:,:]
  
  # mask ocean values here we don't need them anymore
  # most values are above 10 mm per hour since we set that in stoPET to make
  # make the functions run. Mask all values above 5 mm perh hour
  data = np.ma.masked_where(data>5., data)

  # write the output files
  outpath = root_outputpath + 'ensemble_forecast/'
  filename = (outpath + 'Forecast_PET_%s_ens_%s_%s_%s.nc')%(locname,i,seasonName,startyear)  # i which is ensembele for now it is only 0
  varname = 'pet'
  timevals = time[:]
  forecast_nc_write(data, lats, lons, varname, timevals, tunits, filename)
  
  return None          

     
def forecast_nc_write(data, lat, lon, varname, timevals, tunits, filename):
    """
    this function write the PET on a netCDF file.

    :param: data: data to be written (time,lat,lon)
    :param: lat: latitude
    :param: lon: longitude
    :param: varname: name of the variable to be written (e.g. 'pet')
    :param: tunits: time units for the data (e.g. 'days since 1981-01-01')
    :param:filename: the file name to write the values with .nc extension

    :return:  produce a netCDF file in the same directory.
    """
    
    ds = Dataset(filename, mode='w', format='NETCDF4_CLASSIC')

    time = ds.createDimension('time', None)
    latitude = ds.createDimension('latitude', len(lat))
    longitude = ds.createDimension('longitude', len(lon))
   
    time = ds.createVariable('time', np.float32, ('time',))
    latitude = ds.createVariable('latitude', np.float32, ('latitude',))
    longitude = ds.createVariable('longitude', np.float32, ('longitude',))

    # check if the data is 2d or 3d
    if len(data.shape) == 4: # 4D array
        pet_val = ds.createVariable(varname, 'f4', ('time','hours','latitude','longitude'), zlib=True)
        time.units = tunits  
        time.calendar = 'proleptic_gregorian'
        time[:] = timevals
        latitude[:] = lat
        longitude [:] = lon
        pet_val[:,:,:,:] = data
        pet_val.units='mm/hr'
        latitude.units='degrees_north'
        longitude.units='degrees_east'

    elif len(data.shape) == 3: # 3D array
        pet_val = ds.createVariable(varname, 'f4', ('time','latitude','longitude'), zlib=True)
        time.units = tunits  
        time.calendar = 'proleptic_gregorian'
        time[:] = timevals
        latitude[:] = lat
        longitude [:] = lon
        pet_val[:,:,:] = data
        pet_val.units='mm/hr'
        latitude.units='degrees_north'
        longitude.units='degrees_east'
    
    elif len(data.shape) == 2: # 2D array
        pet_val = ds.createVariable(varname, 'f4', ('latitude','longitude'), zlib=True)
        latitude[:] = lat
        longitude [:] = lon
        pet_val[:,:] = data
        pet_val.units='mm/hr'
        latitude.units='degrees_north'
        longitude.units='degrees_east'

    else:
        raise ValueError('the function can only write a 2D, 3D and 4D array data!')

    ds.close()
    
    return None   


def fill_masked_ocean_2d(data):
    # fill ocean values with the nearest value
    # fill the masked part with nearest grid upto 5 grid in each direction
    # the order must be maintained to account for the way the coast is shaped
    data = xr.DataArray(data).ffill(f'dim_{1}', limit=2).values 
    data = xr.DataArray(data).bfill(f'dim_{0}', limit=3).values
    data = xr.DataArray(data).bfill(f'dim_{1}', limit=3).values 
    data = xr.DataArray(data).ffill(f'dim_{0}', limit=3).values
    data = xr.DataArray(data).ffill(f'dim_{1}', limit=5).values 
    data = xr.DataArray(data).bfill(f'dim_{0}', limit=3).values
    # fill everything foreward
    data = xr.DataArray(data).ffill(f'dim_{1}').values
    masked_data = np.ma.masked_where(np.isnan(data), data)
    
    masked_data = np.ma.masked_invalid(masked_data)

    # Replace the masked values (NaN) with a specific number, e.g., 99
    filled_data = masked_data.filled(-99)
    return filled_data    
# ======================================================================= #
# Main function to run the script
if __name__ == '__main__':
    # Check if the script received the correct number of arguments
    if len(sys.argv) != 2:
        print("Usage: python <script_name.py> <path_to_config.json>")
        sys.exit(1)

    # Pass the JSON file path to run_pet_forecast
    config_file = sys.argv[1]
    
    start = dt.datetime.now()
    print('Seasonal PET forecast in progress ...')

    run_pet_forecast(config_file)

    print('Seasonal PET forecast files finished successfully.')
    
    end = dt.datetime.now()
    print('Time of run: %s' % (end - start))
