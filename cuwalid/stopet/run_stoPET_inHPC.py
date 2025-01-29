import sys
import os
import numpy as np
from cuwalid.stopet.stoPET_v2_4dryp import *

# READ ME
# In order to make the ensemble forecasts for running DRYP 
# here we produce the ensemble pools for the PET 
# to do this we need to run the model multiple times (Realizations) (e.g. 30)
# at each run the model will produce 30 ensembles of PET. This will give
# us 30 x 30 ensembles but each realization will be treated separately 
# to produce a weighted average of PET ensemble using the ICPAC tercile forecasts.

# N. B. Use realization number that you want the final number of ensebles to be.
# the number of ensebles should be DIVISIBLE by 3.

# other changes can be made inside the run_stoPET() function 
def run_stoPET_in_hpc(datapath, outputpath, runtype, startyear, endyear, seasonswitch, startdate, enddate, 
                 latval, lonval, latval_min, latval_max, lonval_min, lonval_max,locname, number_ensm, 
                 tempAdj, deltat, udpi_pet, slice_only, season_name, temp_path=""):

    
    ## ------ NO CHANGES BELLOW THIS -------------##
    # here we need to duble the number of ensembles to generate more values for 
    # the pool.
    number_ensm = int(number_ensm * 2)
    # Here we generate the random normal distribution values based on
    # mean shif and the between (hpet and stopetv1) and we use the variabbility
    # from hpet to produce values distribution is similar to the distribution of hpet (2000 - 2023)
    # currently this only works for african continet only.
    # set the randomnes always to be constant
#    np.random.seed(21)  # Set the seed to 21
    
    extra_noise = mean_shift_rand_values(datapath, number_ensm, startyear, endyear)
    
    # Once this mean shift are completed reset the radomness to None
#    np.random.seed(None)  # Reset the seed (None ensures randomness)
    print('Generating the mean shift completed!')
 
    # ************************
    if seasonswitch == 0:
      if runtype == 'single':
            for ens_num in np.arange(0,number_ensm):
                    stoPET_wrapper_singlepoint(startyear, endyear, latval, lonval, locname,
                            ens_num,datapath, outputpath, tempAdj, deltat, udpi_pet)  #, seasonswitch, startdate, enddate
      elif runtype == 'regional':
            for ens_num in np.arange(0,number_ensm):
                    # select the gererated mean shift for the ensemble
                    randnoise = extra_noise[:, ens_num, :, :, :]
                    stoPET_wrapper_regional(startyear, endyear, latval_min, latval_max, lonval_min, lonval_max,
                            locname, ens_num, datapath, outputpath, tempAdj, deltat, udpi_pet, seasonswitch, randnoise, temp_path)
      else:
            raise ValueError('runtype only takes single and regional ... please check!')
    
    if seasonswitch == 1:
      if runtype == 'single':
            for ens_num in np.arange(0,number_ensm):
                    stoPET_wrapper_singlepoint(startyear, endyear, latval, lonval, locname,
                            ens_num,datapath, outputpath, tempAdj, deltat, udpi_pet)  #, seasonswitch, startdate, enddate
      elif runtype == 'regional':
            if slice_only == 0:
              for ens_num in np.arange(0,number_ensm):
                    # select the gererated mean shift for the ensemble
                    randnoise = extra_noise[:, ens_num, :, :, :]
                    stoPET_wrapper_regional(startyear, endyear, latval_min, latval_max, lonval_min, lonval_max,
                            locname, ens_num, datapath, outputpath, tempAdj, deltat, udpi_pet, seasonswitch, randnoise, temp_path)
              # extract seasonal value and remove the annual files
              # prepare the files for the DRYP model input format
              # this only works for regional data as DRYP requires a catchment to run 
              seasonal_pet_for_dryp(outputpath, locname, number_ensm, tempAdj, startyear, endyear, startdate, enddate, seasonswitch, season_name, temp_path)
            else:
              # extract seasonal value and remove the annual files
              # prepare the files for the DRYP model input format
              # this only works for regional data as DRYP requires a catchment to run 
              seasonal_pet_for_dryp(outputpath, locname, number_ensm, tempAdj, startyear, endyear, startdate, enddate, seasonswitch, season_name, temp_path)
            
      else:
            raise ValueError('runtype only takes single and regional ... please check!')

