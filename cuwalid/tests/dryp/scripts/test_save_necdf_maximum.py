import os
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime
from cuwalid.dryp.components.DRYP_store_functions import (
	GlobalGridVar)

def read_dataset(fname, var_name='tht'):
	# Open the first netCDF file
	# output dataset
	data = xr.open_dataset(fname)
	data = data[var_name]
	return data

def test_save_maximum():
    ncols = 5
    nrows = 5
    lat = np.linspace(0, 10, nrows)
    lon = np.linspace(0, 10, ncols)

    grid_size = ncols*nrows

    ini_date = datetime.strptime("2000 1 1", '%Y %m %d')
    end_date = datetime.strptime("2000 3 5", '%Y %m %d')
		
    dt = 720
    dt_results = 'M'
    save_results = True
    
    date_sim_dt = pd.date_range(ini_date, end_date,
			freq = str(int(dt))+'min')
    
    # specified which variables to store
    store_var = {"pre": True, "pet":False, "aet":False,
                 "inf":False, "tht":True,}

    date_sim_dt = date_sim_dt[:-1]

    state_var = GlobalGridVar(ini_date,
			   dt_results, save_results,
                store_var=store_var,
                store_max=True, nstep_day=1440/dt
               )

    nodes = np.arange(int(grid_size/2))

    fname = "test_save_netcdf_max.nc"

    for i in range(len(date_sim_dt)):
        if i == 10*1440/dt:
              rain = 10
        else:
              rain = 0
                      
        state_var.store_variables(date_sim_dt, i,
		{"pre": np.full(nodes.size, rain),
            "tht": np.full(nodes.size, 1.0),})

    # save grided model result datasets
    state_var.save_netCDF_var(fname,
			   lat, lon, nodes#, var_name
			   )
    
    # test maximum
    answer = np.full(grid_size, np.nan)
    answer[nodes] = 10.0
    answer = answer.reshape((nrows, ncols))
    out = read_dataset(fname, var_name='pre').values[0]
    #print(read_dataset(fname, var_name='pre').values)
    #print(out)
    #print(answer)
    assert np.allclose(out, answer, equal_nan=True)
    print('Save maximum dataset: Test runs successfully')
    
    # remove the test dataset created
    os.remove(fname) if os.path.exists(fname) else None
    

if __name__ == '__main__':
	test_save_maximum()