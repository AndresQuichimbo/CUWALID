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
# locname should be similar to what is provided while runing stoPET but only for one of the tercile categories
# for example if locname is TanaBasin then we should provide TanaBasin_A. the script will read this and extract the name from
# what is given. This is important to locate the ensemble files in each pool. 

# the other variables should be similar to the stoPET run exactly as they are used to name files.

# ================ pre processing ICPAC forecast file =============##
def icpac_forecast_preprocessing(tercile_forecast_file, seasonName, startyear, locname):
    # Step 1: Invert latitude (invert latitudes in the dataset)
    tforc_datapath, filename = os.path.split(tercile_forecast_file)
    f = filename.split('.')
    fin = tercile_forecast_file
    fout = f[0] + '_inv.nc'
    
    # Open the dataset
    ds = xr.open_dataset(fin)
    
    # Invert latitudes (flip the latitude axis)
    ds = ds.isel(lat=slice(None, None, -1))  # Reverses the latitude axis
    
    # Save the modified dataset
    ds.to_netcdf(fout)

    # Step 2: Slice the data to fit the existing stoPET (using lat/lon bounding box)
    fin2 = fout
    fout2 = os.path.join(tforc_datapath, 'ICPAC_TempF_%s%s_%s.nc' % (seasonName, startyear, locname))
    
    # Open the dataset again
    ds2 = xr.open_dataset(fin2)

    # Slice the dataset based on the lon/lat box: lon=[31.1, 51.92], lat=[-6.82, 15.9]
    lon_min, lon_max = 31.1, 51.92
    lat_min, lat_max = -6.82, 15.9
    
    ds2 = ds2.sel(lon=slice(lon_min, lon_max), lat=slice(lat_max, lat_min))  # Note that latitudes are typically inverted (max to min)

    # Save the sliced dataset
    ds2.to_netcdf(fout2)

    return fout2


def forecast_wrapper(tercile_forecast_file, outputpath, startyear, startdate, enddate, locname, number_ensm, tempAdj, seasonName):  

  # We need to pre process the ICPAC forecast
  print('Preprocessing ICPAC forecast ...')
  temp_tercile_forecast_file = icpac_forecast_preprocessing(tercile_forecast_file, seasonName, startyear, locname)
  print('Preprocessing ICPAC forecast completed!') 
  
  
  print('PET forecasting started ...')  
  # this will read one file from the stoPET output to use as a template for the array length and time
  temp_output = os.path.join(outputpath, "..", "..", "..", "temp", str(startyear))
  if not os.path.isdir(temp_output):
      os.mkdir(temp_output)

  nc = Dataset(os.path.join(temp_output, seasonName, f'PET_{startyear}_{seasonName}_ens_0.nc'))
  lats = nc.variables['latitude'][:]
  lons = nc.variables['longitude'][:]
  time = nc.variables['time']
  tunits = time.units
  ori_data = nc.variables['pet'][:,:,:]
  
  # create array to append data
  ens_f = (np.ones((number_ensm, ori_data.shape[0], ori_data.shape[1], ori_data.shape[2]))) * np.nan  #//2
  
  # Fix the coastal areas by filling empty grid values
  nc = Dataset(temp_tercile_forecast_file) 
  above = fill_masked_ocean_2d(nc.variables['above'][:,:], (100./3))  
  normal = fill_masked_ocean_2d(nc.variables['normal'][:,:], (100./3)) 
  below = fill_masked_ocean_2d(nc.variables['below'][:,:], (100./3))  
  # below, normal, above    
  # first, second, third tercile
  tercileTf = ((np.asarray(np.stack([below, normal, above])))) / 100.  # get the decimals  

  # estimate the number of files in each tercile
  fnumbers = get_forecast(number_ensm, tercileTf)  # //2
  
  # Read the entire forecast loop as an array (ensemble, time, lat, lon)
  # This is required since the numba jit cant read files but only numpy array
  # Since we are reading all the files of pool it requre storage space
  pool_dir = os.path.join(temp_output, seasonName)
  ens_A = read_forecast_pool(number_ensm*2, ori_data, pool_dir, locname, tempAdj, startdate, enddate, startyear, seasonName) # ensemble number is multiplied by 2
  
  # Generate the tercile cut-off points 
  seasonSum, tercile_thresholds_1, tercile_thresholds_2 = compute_tercile_thresholds(ens_A)
  
  # save seasonal sum if needed
  np.save(os.path.join(outputpath, 'seasonal_sum_%s_%s.npy'%(seasonName, startyear)), seasonSum)
  # save the terciles for later plotting
  np.save(os.path.join(outputpath, 'tercile_1_stopet_%s_%s.npy'%(seasonName, startyear)), tercile_thresholds_1)
  np.save(os.path.join(outputpath, 'tercile_2_stopet_%s_%s.npy'%(seasonName, startyear)), tercile_thresholds_2)
  
  # loop through each grid and start extracting the respective timeseries 
  # make sure the number of files percentage is correct.
  # This means when you take 5% of 10 it is 0.5 this means we take 1 file for this category
  # this might reduce number of files for the other categories so make sure the sum is equal to 
  # total number of files we have (this is equal to the ensemble numbers).
  # run loop for selecting the forecast and write on a file
  
  # This is a parallel run using numba to redce computational time
  # but since we are reading all the files of pool it requre storage space
  # This will identify the indices to choose for the forecasting
  ensemble_indices = index_forecast_with_tercile(tercileTf, number_ensm, ens_A, fnumbers, ens_f, tercile_thresholds_1, tercile_thresholds_2, seasonSum)     
  
  # This will create the forecasted PET value 
  ensembleArray = forecast_pet(ensemble_indices, ens_A, ens_f) 
  
  # Write the output array into files     
  print("writing pet forecast files")                   
  writing_forecast_file(ensembleArray, seasonName, locname, startyear, outputpath, time, lats, lons, tunits) 
  
  print('PET forecasting completed!')


@jit(nopython=True, parallel=True)
def forecast_pet(ensemble_indices, ens_A, ens_f):
    for i in prange(ens_f.shape[2]):  # loop over rows (I)
        for j in range(ens_f.shape[3]):  # loop over cols (J)
            for e in range(ensemble_indices.shape[0]):  # loop over ensemble members (30)
                idx = int(ensemble_indices[e, i, j])  # cast index to int64
                ens_f[e, :, i, j] = ens_A[idx, :, i, j]  # assign values from ens_A to ens_f
    return ens_f


def fill_masked_ocean_2d(data, fillvalue):
    # fill ocean values with the nearest value
    # fill the masked part with nearest grid upto 5 grid in each direction
    # the order must be maintained to account for the way the coast is shaped
    data = xr.DataArray(data).ffill(f'dim_{1}', limit=2).values 
    data = xr.DataArray(data).bfill(f'dim_{0}', limit=3).values
    data = xr.DataArray(data).bfill(f'dim_{1}', limit=3).values 
    data = xr.DataArray(data).ffill(f'dim_{0}', limit=3).values
    data = xr.DataArray(data).ffill(f'dim_{1}', limit=5).values 
    data = xr.DataArray(data).bfill(f'dim_{0}', limit=3).values
    masked_data = np.ma.masked_where(np.isnan(data), data)
    
    masked_data = np.ma.masked_invalid(masked_data)

    # Replace the masked values (NaN) with a specific number, e.g., 99
    filled_data = masked_data.filled(fillvalue)
    return filled_data  


def read_forecast_pool(number_ensm, ori_data, outputpath, locname, tempAdj, startdate, enddate, startyear, season_Name):   
    # create array to append data of each ensembles
    ens_A = (np.ones((number_ensm, ori_data.shape[0], ori_data.shape[1], ori_data.shape[2]))) * np.nan

    # file name of the adjusted PET from stopet
    # Above
    for ens in range(0,number_ensm):
        filename = os.path.join(outputpath, f'PET_{startyear}_{season_Name}_ens_{ens}.nc')
        # read the file and append to the 4D array
        nca = Dataset(filename)
        pet_A = nca.variables['pet'][:,:,:]
        ens_A[ens,:,:,:] = pet_A 
    return ens_A
    
     
# numba parallel run function  
# decorate the function 
@jit(nopython=True, parallel=True)  
def index_forecast_with_tercile(tercileTf, number_ensm, ens_A, fnumbers, ens_f, tercile_thresholds_1, tercile_thresholds_2, seasonSum):
    # Initialize array to store final samples (number_ensm//2, X.shape[1], X.shape[2])
    final_samples = np.zeros((number_ensm, ens_f.shape[2], ens_f.shape[3]))    #//2
    
    # Loop through files and extract array of PET accordingly  
    for i in prange(ens_f.shape[2]):  # row, parallelized outer loop
        for j in range(ens_f.shape[3]):  # column
            
            # Extract the values for the current location (i, j)
            values = seasonSum[:, i, j]
            
            # Separate the values into terciles using precomputed thresholds
            tercile_1_indices = np.where(values <= tercile_thresholds_1[i, j])[0]
            tercile_2_indices = np.where((values > tercile_thresholds_1[i, j]) & (values <= tercile_thresholds_2[i, j]))[0]
            tercile_3_indices = np.where(values > tercile_thresholds_2[i, j])[0]
            
            # Now you have both the values and the corresponding indices
            tercile_1_values = values[tercile_1_indices]
            tercile_2_values = values[tercile_2_indices]
            tercile_3_values = values[tercile_3_indices]
            
            # sort values
            sorted_indices_t1 = sort_with_tercile_indices(tercile_1_values, tercile_1_indices)
            sorted_indices_t2 = sort_with_tercile_indices(tercile_2_values, tercile_2_indices)
            sorted_indices_t3 = sort_with_tercile_indices(tercile_3_values, tercile_3_indices)

            # Get the number of values needed in each tercile
            n_1 = fnumbers[0, i, j]  # Number for the first tercile
            n_2 = fnumbers[1, i, j]  # Number for the second tercile
            n_3 = fnumbers[2, i, j]  # Number for the third tercile

            # Initialize an array to store the samples for this (i, j)
            samples = np.zeros(number_ensm , dtype=np.int32)  # Using int32 for consistency  // 2

            idx = 0  # To track position in the samples array
            
            # Tercile 1 sampling (upper tercile)
            if len(tercile_1_indices) > 0 and n_1 > 0:
                random_samples = sample_with_tercile_strategy(sorted_indices_t1, n_1, 1)
                samples[idx:idx + n_1] = random_samples
                idx += n_1
            
            # Tercile 2 sampling (use all available values in the middle tercile)
            if len(tercile_2_indices) > 0 and n_2 > 0:
                random_samples = sample_with_tercile_strategy(sorted_indices_t2, n_2, 2)
                samples[idx:idx + n_2] = random_samples
                idx += n_2

            # Tercile 3 sampling (lower tercile)
            if len(tercile_3_indices) > 0 and n_3 > 0:
                random_samples = sample_with_tercile_strategy(sorted_indices_t3, n_3, 3)
                samples[idx:idx + n_3] = random_samples
                idx += n_3

            # Shuffle the samples (optional, but may add randomness to the sampling process)
            # np.random.shuffle(samples)  # Uncomment if shuffle is needed

            # Assign the sampled values to the corresponding (i, j) location in the final_samples array
            final_samples[:, i, j] = samples

    return final_samples


# Function to compute tercile thresholds outside of Numba function
def compute_tercile_thresholds(ens_A):
    X = np.sum(ens_A[:,:,:,:], axis=1) # 3d array
    tercile_thresholds_1 = np.percentile(X, 100 / 3, axis=0)
    tercile_thresholds_2 = np.percentile(X, 200 / 3, axis=0)
    return X, tercile_thresholds_1, tercile_thresholds_2


@njit
def sort_with_tercile_indices(tercile_values, tercile_indices):
    n = len(tercile_values)
    
    for i in range(n):
        # Find the minimum element in the remaining unsorted array
        min_index = i
        for j in range(i + 1, n):
            if tercile_values[j] < tercile_values[min_index]:
                min_index = j
        
        # Swap the found minimum element with the current element in x
        tercile_values[i], tercile_values[min_index] = tercile_values[min_index], tercile_values[i]
        
        # Swap the corresponding element in y to match
        tercile_indices[i], tercile_indices[min_index] = tercile_indices[min_index], tercile_indices[i]
    
    # Return the sorted y
    return tercile_indices
    
    
@njit
def sample_with_tercile_strategy(sorted_indices, n_needed, tercile):
    if len(sorted_indices) >= n_needed:  # Enough values available
        result = np.zeros(n_needed, dtype=np.int32)
        # Strategy based on tercile
        if tercile == 1:  # Upper half
            result[:1] = sorted_indices[0]  # pick the smallest value
            new_indices = np.random.choice(sorted_indices[1:], n_needed-1, replace=False)  #sorted_indices[:n_needed]
        elif tercile == 2:  # Random sample
            result[:1] = sorted_indices[0]
            new_indices = np.random.choice(sorted_indices[1:], n_needed-1, replace=False)
        elif tercile == 3:  # Lower half
            result[:1] = sorted_indices[-1]   # pick the largest value
            new_indices = np.random.choice(sorted_indices[:-1], n_needed-1, replace=False) #sorted_indices[-n_needed:]

        result[1:n_needed] = new_indices
        return result

    else:
        remaining_samples = n_needed - len(sorted_indices)

        # Strategy based on tercile
        if tercile == 1:  # Upper half
            extra_values = sorted_indices[len(sorted_indices) // 2:]
        elif tercile == 2:  # All values
            extra_values = sorted_indices
        elif tercile == 3:  # Lower half
            extra_values = sorted_indices[:len(sorted_indices) // 2]

        result = np.zeros(n_needed, dtype=np.int32)
        result[:len(sorted_indices)] = sorted_indices
        result[len(sorted_indices):] = np.random.choice(extra_values, remaining_samples, replace=True)
        return result


@jit(nopython=True, parallel=True)          
def check_forecast_percentage(forcvals, num_file):  
  """
  This function evaluate the forecasts and the number of
  files we have and return the exact number of files we need to add 
  # for the three tercile category.
  """
  y = np.rint(np.nextafter(forcvals, forcvals+1))
  z=np.sum(y) - num_file
  if z!=0:
    ind = np.argmax(y)
    y[ind] = y[ind] - z  
  return y

 
def writing_forecast_file(ensembleArray, seasonName, locname, startyear, outputpath, time, lats, lons, tunits): 
      
  # write the final ensembles on a netcdf file
  # file name of the adjusted PET from stopet 
  for f in range(ensembleArray.shape[0]):
    # read the each ensemble array
    pet_data = ensembleArray[f,:,:,:]
    # Qualiity check 
    # the newar by grid should be with in 10% diffrence from  the surrounding average
    data = smooth_grid_numba_parallel(pet_data)
    # write the output files


    filename = os.path.join(outputpath, f'Forecast_PET_{locname}_ens_{str(startyear)}_{seasonName}_{str(f)}.nc')
    print(f"filename: {filename}")
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


def get_forecast(number_ensm, tercileTf):  
    forcvals = tercileTf[:,:,:] * number_ensm # this is the forecast values
    # make sure the sum of the the above array is equal to the number of files
    # available. Here we need to make the floats rounded but still cant exceed
    # the numbe of file. 
    fnumbers = check_forecast_percentage(forcvals, number_ensm)
    fnumbers = fnumbers.astype(int)
    return fnumbers


@jit(nopython=True, parallel=True)
def check_forecast_percentage(forcvals, num_file):
    """
    This function evaluates the 3D forecasts along axis 0 and adjusts the
    rounded forecast values to ensure that the sum for each (i, j) position
    matches num_file[i, j].
    
    Parameters:
    forcvals: 3D array of forecasted values (shape: (3, 10, 10))
    num_file: 2D array representing the number of files required at each (i, j) position (shape: (10, 10))
    
    Returns:
    y: 3D array of rounded forecast values with adjusted sums.
    """
    
    # Initialize the result array to store the rounded values
    y = np.zeros_like(forcvals)
    
    # Iterate over the (i, j) positions in the 10x10 grid
    for i in prange(forcvals.shape[1]):  # Loop over the second dimension (10)
        for j in range(forcvals.shape[2]):  # Loop over the third dimension (10)
            
            # Get the forecast values for this (i, j) position along axis 0
            vals = forcvals[:, i, j]
            
            # Step 1: Round the forecast values
            rounded_vals = np.rint(vals)
            
            # Step 2: Calculate the difference between the sum and the desired num_file[i, j]
            z = np.sum(rounded_vals) - num_file
            
            # Step 3: Adjust the values to ensure the sum matches num_file[i, j]
            while z != 0:
                if z > 0:
                    # Reduce the largest value by 1 to reduce the sum
                    ind = np.argmax(rounded_vals)
                    if rounded_vals[ind] > 0:  # Ensure value does not go negative
                        rounded_vals[ind] -= 1
                        z -= 1
                elif z < 0:
                    # Increase the smallest value by 1 to increase the sum
                    ind = np.argmin(rounded_vals)
                    rounded_vals[ind] += 1
                    z += 1
            
            # Store the adjusted rounded values
            y[:, i, j] = rounded_vals
    
    return y


@njit(parallel=True)
def smooth_grid_numba_parallel(grid):
    # Get the dimensions of the grid
    depth, rows, cols = grid.shape

    # Create a copy of the grid to store the new values
    smoothed_grid = grid.copy()

    # Iterate over the depth (axis 0)
    for i in prange(depth):  # Parallelize over the depth dimension
        # Iterate over the 2D grid at each depth level, skipping the edges (as a 3x3 window can't be centered on them)
        for j in range(1, rows-1):
            for k in range(1, cols-1):
                # Calculate the sum of the surrounding cells in the 3x3 window
                surrounding_sum = (
                    grid[i, j-1, k-1] + grid[i, j-1, k] + grid[i, j-1, k+1] +
                    grid[i, j, k-1] + grid[i, j, k+1] +
                    grid[i, j+1, k-1] + grid[i, j+1, k] + grid[i, j+1, k+1]
                )
                surrounding_avg = surrounding_sum / 8.0

                # Check if the middle value exceeds or less than 10% of the surrounding average
                if (grid[i, j, k] > 1.1 * surrounding_avg) or (grid[i, j, k] < 0.9 * surrounding_avg):
                    # Set the middle value to the surrounding average
                    smoothed_grid[i, j, k] = surrounding_avg

    return smoothed_grid

# ======================================================================= #
if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("Usage: python <script_name.py> <path_to_config.json>")
        sys.exit(1)
    
    config_file = sys.argv[1]

    start = dt.datetime.now()

    print('Seasonal PET forecast in progress ...')

        # Load configuration file
    if type(config_file) == str:
        config = load_config(config_file)


    # Extract parameters from the config
    outputpath = config['root_outputpath']
    startyear = config['startyear']
    startdate = config['startdate']
    enddate = config['enddate']
    locname = config['locname']
    number_ensm = config['number_ensm']
    tempAdj = config['tempAdj']
    tercile_forecast_file = config['tercile_forecast_file']
    seasonName = config['seasonName']
    
    forecast_wrapper(tercile_forecast_file, outputpath, startyear, startdate, enddate, locname, number_ensm, tempAdj, seasonName)
    
    print('Seasonal PET forecast files finished successfully.')
    
    end=dt.datetime.now()
    print('Time of run: %s'%(end - start))
