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
def run_stoPET_in_hpc(trial,   datapath, root_outputpath, runtype, startyear, endyear, seasonswitch, startdate, enddate, 
                 latval, lonval, latval_min, latval_max, lonval_min, lonval_max,locname, number_ensm, 
                 tempAdj, deltat, udpi_pet, trial_number):

    # here we need to choose the trial number that is similar
    # to what the user puts. This is to over ride what is imported from 
    # the config file as the value there is the total number and here we need the specific
    # trial number to generate the folders where the output will be saved.
    trial_numbers = np.arange(trial_number)
    index = np.where(trial_numbers == trial)[0][0] 
    trial_number = int(trial_numbers[index])
    print(trial_number)
    
    # create a folder to save the data
    if not os.path.isdir(root_outputpath + 'result_R%s/'%trial_number):
      os.mkdir(root_outputpath + 'result_R%s/'%trial_number)    
    # this folder will be used to save the ensembles generated on each realization
    # here the output path will change to the new folder created within the origional
    # output root path with result_R* where * is the number of the trial.
    outputpath = root_outputpath + 'result_R%s/'%trial_number

    ## ------ NO CHANGES BELLOW THIS -------------##
    # Here we generate the random normal distribution values based on
    # mean shif and the between (hpet and stopetv1) and we use the variabbility
    # from hpet to produce values distribution is similar to the distribution of hpet (2000 - 2023)
    # currently this only works for african continet only.
    extra_noise = mean_shift_rand_values(datapath, number_ensm, startyear, endyear)
    
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
                            locname, ens_num, datapath, outputpath, tempAdj, deltat, udpi_pet, seasonswitch, randnoise)
      else:
            raise ValueError('runtype only takes single and regional ... please check!')
    
    if seasonswitch == 1:
      if runtype == 'single':
            for ens_num in np.arange(0,number_ensm):
                    stoPET_wrapper_singlepoint(startyear, endyear, latval, lonval, locname,
                            ens_num,datapath, outputpath, tempAdj, deltat, udpi_pet)  #, seasonswitch, startdate, enddate
      elif runtype == 'regional':
            for ens_num in np.arange(0,number_ensm):
                    # select the gererated mean shift for the ensemble
                    randnoise = extra_noise[:, ens_num, :, :, :]
                    stoPET_wrapper_regional(startyear, endyear, latval_min, latval_max, lonval_min, lonval_max,
                            locname, ens_num, datapath, outputpath, tempAdj, deltat, udpi_pet, seasonswitch, randnoise)
            # extract seasonal value and remove the annual files
            # prepare the files for the DRYP model input format
            # this only works for regional data as DRYP requires a catchment to run 
            seasonal_pet_for_dryp(outputpath, locname, number_ensm, tempAdj, startyear, endyear, startdate, enddate, seasonswitch)
            
      else:
            raise ValueError('runtype only takes single and regional ... please check!')
    
##-----------------------------------------------------------------------##
if __name__ == '__main__':
    start = dt.datetime.now()

    run_stoPET(int(sys.argv[1]),  datapath, root_outputpath, runtype, startyear, endyear, seasonswitch, startdate, enddate, 
                 latval, lonval, latval_min, latval_max, lonval_min, lonval_max,locname, number_ensm, 
                 tempAdj, deltat, udpi_pet, trial_number)
    print('Seasonal PET extraction finished successfully.')
    
    end=dt.datetime.now()
    print('Time of run: %s'%(end - start))


