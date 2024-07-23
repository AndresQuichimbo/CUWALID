import cuwalid.tools.CUWALID_forecast_tools as cuwalid
import xarray as xr

def get_updated_TWSA_ensamble(model_path, model_name):
	# Specify model name, This will be the root name for the forecasting
	#model_name = "HAD_IMERGba_sim0"

	# model name previous step
	model_name_previous = "HAD_IMERGba_sim0_2022_ini_MAM"


	# Path of model output files
	#model_path = "D:\HAD\training\forecast\regional\outputs/"
	#model_path = "/home/c1755103/HAD/HAD_output/"
	#model_path = "/home/cuwalid/training/historical/regional/outputs/"#_13_grid.nc
	model_path_previous = "/home/cuwalid/training/historical/regional/outputs/"#_13_grid.nc

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

	nsim = 30
	nini = 0
	ifield = "twsc"
	# specify previous TWSC accumulated
	#fname_previous = model_path+model_name+"_"+ str(iyear-1) +'_grid_twsc.nc'
	fname_previous = model_path_previous+model_name_previous+'_grid_twsc.nc'
	#fname_current = fname_current.split('.')[0]+'_'+ifield+'.nc'

	fname  = [
	model_path+model_name+"_"+ str(isim) +'_grid.nc' for isim in range(nini, nsim)
	]

	data_previous = cuwalid.read_dataset(fname_previous, var_name='twsc')

	for ifname_ensamble in fname:#for isim in range(nsim):

		# specify current simulation path
		#fname_current = model_path+model_name+"_"+ str(iyear-1) +'_grid.nc'
			
		# read dataset
		data_current = cuwalid.read_dataset(ifname_ensamble, var_name='twsc')
		
		
		# Update datasets
		data = cuwalid.update_TWSA(data_current, data_previous)
		
		# save dataset as netcdf file
		fname_current = ifname_ensamble.split('.')[0]+'_'+ifield+'.nc'
		
		data.to_netcdf(fname_current)
