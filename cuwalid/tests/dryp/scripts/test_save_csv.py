from context import dryp
import os
import numpy as np
import pandas as pd
from datetime import datetime
from cuwalid.dryp.components.DRYP_store_functions import (
	GlobalGridVar)

def test_save_variables():
    ncols = 5
    nrows = 5
    lat = np.linspace(0, 10, nrows)
    lon = np.linspace(0, 10, ncols)

    grid_size = ncols*nrows

    ini_date = datetime.strptime("2000 1 1", '%Y %m %d')
    end_date = datetime.strptime("2000 2 3", '%Y %m %d')
		
    dt = 1440
    dt_results = 'M'
    save_results = True
    
    date_sim_dt = pd.date_range(ini_date, end_date,
			freq = str(int(dt))+'min')
    
    date_sim_dt = date_sim_dt[:-1]

    # specified which variables to store
    store_var = {"pre": True, "pet":True, "aet":False,
                 "inf":False, "tht":True,}

    state_var = GlobalGridVar(ini_date,
			   dt_results, save_results, store_var=store_var)

    nodes = 3

    fname = "test_save_csv"

    for i in range(len(date_sim_dt)):
        
        state_var.store_variables(date_sim_dt, i,
		    {"pre": np.ones(1),
            "pet": np.ones(nodes),
            "tht": np.ones(nodes+1),})

    # save grided model result datasets
    state_var.save_csv_var(fname, multi_files=False)

    # calculate the solution
    answer = np.concatenate([np.full(1, 31.0),
            np.full(nodes, 31.0),
            np.full(nodes+1, 1.0)])
    
    # read results
    df = pd.read_csv(fname+'.csv')
    out = np.array(df.iloc[0].values[1:])
    
    assert np.allclose(list(out), list(answer))
    print('Save csv files: Test runs successfully')

    # remove the test dataset created
    os.remove(fname+'.csv') if os.path.exists(fname+'.csv') else None

if __name__ == '__main__':
	test_save_variables()