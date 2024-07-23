#import netCDF4
import xarray as xr
import numpy as np
import cuwalid.tools.CUWALID_forecast_tools as cuwalid

# ==============================================================
def get_ensamble_forecasting(model_path, model_name, variables, postpp_path):
	"""This funtion create an ensamble of model simulation for each
	variable especify in the 'config_forecasting.py' file.

	WARNING! Values of total water storage needs to be updated for
	all the simulations
	"""

	#model_name = "MAM_2022_realization"

	#model_path = "/home/cuwalid/training/forecast/regional/outputs/"#_13_grid.nc

	#postpp_path = "/home/cuwalid/training/forecast/regional/postpp/"

	nsim = 30
	# get and save mean average values from netcdf
	nini = 1

	fname  = [
	model_path+model_name+"_"+ str(isim) +'_grid.nc' for isim in range(nini, nsim)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2023)
	#'/user/work/km19051/HAD_output/HAD_1k_10y_gw_ch_ksat_1_v2_IMERG_sim_28_grid.nc',
	]

	season = ["MAM"]#, "OND"]

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#field = [#'pre', 'pet',
	#	#'aet', 'tht', 'egw',
	#	#'inf', 'run',
	#	#'rch', 'fch', #'gdh',
	#	#'dis',
	#	'tls',# 'wte',
	#	#"twsc",
	#	]

	for iseason in season:
		for ivar in field:
			fname_list = fname.copy()
			
			fname_list = fname.copy()
			# check if is the riparian area
			if (ivar == 'fch') or (ivar == 'tls') or (ivar == 'ssz'):
				fname_list = [
					ifname.split('.')[0]+'rp.nc' for ifname in fname_list
					]
					
			if (ivar == 'twsc') or (ivar == 'wrsi'):# or (ivar == 'ssz'):
				fname_list = [
					ifname.split('.')[0]+'_'+ivar+'.nc' for ifname in fname_list
					]
			#print(fname_list)
			mean = False
			if (ivar == 'tht') or (ivar == 'wte'):
				mean = True
			# get average values for all variables from a list of netcdf files
			dataset = cuwalid.get_ensamble_from_netcdf_list(fname_list,
									ivar, mean=mean,
									delta=None, season=iseason,
									fname_output=None)
		
			# save files
			#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
			#fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_" + imodel + "_mean.nc"
			if iseason is None:
				fname_out = postpp_path+"netcdf/" + model_name + "_" + ivar + "_ensamble.nc"
			else:
				fname_out = postpp_path+"netcdf/" + model_name + "_" + iseason + "_" + ivar +"_ensamble.nc"
			#cuwalid.save_xarray_dataset_as_netcdf(fname_out, dataset, field)
			dataset.to_netcdf(fname_out)
