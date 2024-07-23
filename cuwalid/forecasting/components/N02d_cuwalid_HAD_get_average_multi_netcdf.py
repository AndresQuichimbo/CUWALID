#import netCDF4
import xarray as xr
import numpy as np
import cuwalid.tools.CUWALID_forecast_tools as cuwalid

def get_average_multi_netcdf(model_path, model_name, start_year, end_year, season, variables, postpp_path):

	# get and save mean average values from netcdf
	fname  = [
	model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2023)
	#'/user/work/km19051/HAD_output/HAD_1k_10y_gw_ch_ksat_1_v2_IMERG_sim_28_grid.nc',
	]

	#imodel = "IMERGba_sim0"

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#field = ['pre', 'pet',
	#	'aet', 'tht', 'egw',
	#	#'inf', 'run',
	#	'rch', 'fch', #'gdh',
	#	'dis', 'tls', 'wte',
	#	"twsc",
	#	]

	for iseason in season:
		# get average values for all variables from a list of netcdf files
		dataset = cuwalid.get_average_all_variables_from_list(fname, field, iseason)
		
		# save files
		#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
		#fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_" + imodel + "_mean.nc"
		if iseason is None:
			fname_out = postpp_path+"netcdf/" + model_name + "_mean.nc"
		else:
			fname_out = postpp_path+"netcdf/" + model_name + "_" + iseason + "_mean.nc"
		cuwalid.save_xarray_dataset_as_netcdf(fname_out, dataset, field)
