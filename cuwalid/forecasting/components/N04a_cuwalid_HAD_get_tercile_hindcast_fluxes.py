import cuwalid.tools.CUWALID_forecast_tools as cuwalid


def get_tercile_hindcast_fluxes(model_path, model_name, variables,postpp_path):
	"""This function calculates the probabilistic forecasting using the tercile approach
	"""
	iyear = 2022
	#ivar = "dis"
	#iseason = "MAM"
	#iseason = "OND"

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#season = ["MAM", "OND"]
	season = ["MAM"]

	fname_var = model_path+model_name+"_YYYY_grid_VVV.nc"
	fname_threshold = postpp_path+"netcdf/" + model_name + "_SSS_quantiles.nc"
	fname_threshold = postpp_path+"netcdf/" + model_name + "_SSS_extremes_quantiles.nc"
	#fname_var = "/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_YYYY_grid_VVV.nc"
	#fname_var = "/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_YYYY_grid.nc"
	#fname_threshold = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_SSS_quantiles.nc"
	#fname_q = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_mean.nc

	fname_var = fname_var.replace("YYYY", str(iyear))

	for iseason in season:
		#for ivar in ["dis", "twsc", "tht", "wrsi"]:
		for ivar in ["wrsi"]:
			# choose path depending on variable
			if (ivar == "twsc") or (ivar == "wrsi"):
				ifname = fname_var.replace("VVV", ivar)
			else:
				ifname = fname_var.replace("_VVV", "")
			
			# chose path depending on the season
			if iseason is None:
				ifname_threshold = fname_threshold.replace("_SSS", "")
			else:
				ifname_threshold = fname_threshold.replace("SSS", iseason)
						
			# specify path for dataset
			#netcdf_path = "D:/HAD/output/HAD_IMERGb_sim_"+ str(iyear)+"_grid.nc"
			
			# specify paht for threshold dataset
			#nc_path_threshold = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_quantiles.nc"
			
			# get tercile forecasting
			tercile = cuwalid.get_tercile_probabilities_from_netcdf(ifname, ifname_threshold,
					var=ivar, season=iseason)
			
			# save as NETCDF files
			if iseason is None:
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
			else:
				#fname_out = "/home/c1755103/HAD/HAD_postpp/netcdf/HAD_IMERGba_sim0_"+ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
				#fname = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_probabilistic_tercile_forecast.nc"
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_probabilistic_tercile_forecast.nc"
			
			# save probabilistic forecast as netcdf
			tercile.to_netcdf(fname_out)
			