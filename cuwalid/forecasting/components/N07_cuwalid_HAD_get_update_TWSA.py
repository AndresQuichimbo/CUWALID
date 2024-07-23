import cuwalid.tools.CUWALID_forecast_tools as cuwalid
import xarray as xr

def get_update_TWSA(model_path, model_name):

    # Path of model output files
    #model_path = "D:\HAD\training\forecast\regional\outputs/"
    #model_path = "/home/c1755103/HAD/HAD_output/"
    #model_path = "/home/cuwalid/training/historical/regional/outputs/"#_13_grid.nc

    # path for post processing files, i.g. forecasting
    # Specific folders will be created inside this paht to store different
    # types of lie formats
    # /fig: for any king of figure
    # /netcdf: for *.nc files
    # /raster: for *.asc files
    # /csv: for comma delimited files, i.g. *.csv
    #postpp_path = "D:\HAD\training\forecast\regional\postpp/"
    #postpp_path = "/home/c1755103/HAD/HAD_postpp/"
    #postpp_path = "/home/cuwalid/training/historical/regional/postpp/"

    iyear = 2022

    ifield = "twsc"

    # specify current simulation path
    fname_current = model_path+model_name+'_grid.nc'# comment this line for yearly data
    #fname_current = model_path+model_name+"_"+ str(iyear-1) +'_grid.nc' # imcomment this line for yealy data

    # specify previous TWSC accumulated
    fname_previous = model_path+model_name+"_"+ str(iyear-1) +'_grid_twsc.nc'

    # read dataset
    data_current = cuwalid.read_dataset(fname_current, var_name='twsc')

    data_previous = cuwalid.read_dataset(fname_previous, var_name='twsc')

    # Update datasets
    data = cuwalid.update_TWSA(data_current, data_previous)

    # save dataset as netcdf file
    fname_current = fname_current.split('.')[0]+'_'+ifield+'.nc'

    data.to_netcdf(fname_current)