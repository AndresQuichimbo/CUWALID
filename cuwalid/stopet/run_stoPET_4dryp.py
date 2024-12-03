import sys
import os
import numpy as np
from cuwalid.stopet.stoPET_v2_4dryp import *


# this run_stoPET() function will generate the PET 
def run_stoPET_4_dryp(datapath, outputpath, runtype, startyear, endyear, seasonswitch, startdate, enddate, 
		 latval, lonval, latval_min, latval_max, lonval_min, lonval_max,locname, number_ensm, 
		 tempAdj, deltat, udpi_pet, slice_only):

	# here we need to duble the number of ensembles to generate more values for 
	# the pool.
	number_ensm = int(number_ensm * 2)

	# create a folder to save the data
	if not os.path.isdir(os.path.join(outputpath, 'result/')):
		os.mkdir(os.path.join(outputpath, 'result/'))    

	# this will run stoPET in a loop (This will take more time to finishe the job)
	stoPET_model_main(datapath, outputpath, runtype, startyear, endyear, seasonswitch, startdate, enddate, 
			latval, lonval, latval_min, latval_max, lonval_min, lonval_max,locname, number_ensm, 
			tempAdj, deltat, udpi_pet, slice_only)


def stoPET_model_main(datapath, outputpath, runtype, startyear, endyear, 
	seasonswitch, startdate, enddate, latval, lonval, 
	latval_min, latval_max, lonval_min, lonval_max,
	locname, number_ensm, tempAdj, deltat, udpi_pet, slice_only):
		
# Here we generate the random normal distribution values based on
    # mean shif and the between (hpet and stopetv1) and we use the variabbility
    # from hpet to produce values distribution is similar to the distribution of hpet (2000 - 2023)
    # currently this only works for african continet only.
    extra_noise = mean_shift_rand_values(datapath, number_ensm, startyear, endyear)

    ## ------ NO CHANGES BELLOW THIS -------------##
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
            if slice_only == 0:
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
              # extract seasonal value and remove the annual files
              # prepare the files for the DRYP model input format
              # this only works for regional data as DRYP requires a catchment to run 
              seasonal_pet_for_dryp(outputpath, locname, number_ensm, tempAdj, startyear, endyear, startdate, enddate, seasonswitch)
            
      else:
            raise ValueError('runtype only takes single and regional ... please check!')



