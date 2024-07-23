#import netCDF4
import xarray as xr
import numpy as np
import cuwalid.tools.CUWALID_forecast_tools as cuwalid


def get_extremes_quantiles_multi_netcdf(model_path, model_name, start_year, end_year, season, variables, postpp_path):
		
	# ==============================================================
	# DO NOT MODIFY FROM HERE -------------------------------------
	# get and save mean average values from netcdf
	fname  = [
	model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2023)
	]

	#model_name = "IMERGba_sim0"

	# specified fields
	field = cuwalid.drop_false_keys(variables)


	#field = ['pre', 'pet',
	#	'aet', 'tht', 'egw',
	#	#'inf', 'run',
	#	'rch', 'fch', #'gdh',
	#	'dis', #'tls', 'wte',
	#	"twsc",
	#	]

	# loop over all specified variables
	q1 = 0.33
	q2 = 0.50
	q3 = 0.66
	q4 = 0.05
	q5 = 0.95

	season = [None, 'MAM', 'OND']
	season = ['MAM']#, 'OND']

	for iseason in season:
		
		first_read = True
		for ifield in field:
			
			# CHANGE NAMES TO ADD MORE VARIABLES
			# using anomalies
			fname_list = fname.copy()
			if (ifield == "twsc") or (ifield == "wrsi"):
				fname_list = [
					ifname.split('.')[0]+'_'+ifield+'.nc' for ifname in fname
					]
			
			# concatenate dataset at selected fields
			data_concat = cuwalid.concatenate_netCDF(
				fname_list, ifield, agg="M", dim='time'
				)
			
			## accummulate dataset, just in case of TWSA
			#if ifield == 'twsc':
			#	data_concat = data_concat.cumsum(dim='time')
			
			mean = False
			if (ifield == 'tht') or (ifield == 'wte'):
				mean = True
			
			if iseason is not None:
				# get seasson
				data_concat = data_concat.where(
					data_concat.time.dt.month.isin(
					cuwalid.season_name_to_number(iseason)))
				
			# resample dataset
			data_concat = cuwalid.resample_dataset(data_concat,
						mean=mean, delt='Y'
						)
			
			# calculate quantiles values of each variable, and store
			# it as dataset
			data_concat = xr.concat([
								data_concat.quantile(q1, dim='time'),
								data_concat.quantile(q2, dim='time'),
								data_concat.quantile(q3, dim='time'),
								data_concat.quantile(q4, dim='time'),
								data_concat.quantile(q5, dim='time')
								],
								dim="time")
			
			if first_read == True:
				dataset = data_concat.copy()
				first_read = False
			else:
				dataset = xr.merge([dataset, data_concat])
			
		# save as NETCDF files
		if iseason is None:
			#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
			fname_out = postpp_path+"netcdf/" + model_name + "_extremes_quantiles.nc"
		else:
			#fname_out = '/user/work/km19051/HAD_postpp/netcfd/HAD_'+imodel+'_wte_mean.nc'
			fname_out = postpp_path+"netcdf/" + model_name + '_' + iseason + "_extremes_quantiles.nc"
		
		cuwalid.save_xarray_dataset_as_netcdf(fname_out, dataset, field)

			