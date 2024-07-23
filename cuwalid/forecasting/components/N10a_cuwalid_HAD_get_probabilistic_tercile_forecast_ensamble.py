import cuwalid.tools.CUWALID_forecast_tools as cuwalid

def get_probabilistic_tercile_forecast_ensamble(model_path, model_name, season, variables, postpp_path):
	"""This function calculates the probabilistic forecasting using the tercile approach
	"""
	#model_name = "MAM_2022_realization"

	iyear = 2022
	#ivar = "dis"
	#iseason = "MAM"
	#iseason = "OND"

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#season = ["MAM", "OND"]
	#season = ["MAM"]

	#model_path = "/home/cuwalid/training/forecast/regional/outputs/"#_13_grid.nc

	#postpp_path = "/home/cuwalid/training/forecast/regional/postpp/"

	fname_ensamble = postpp_path+"netcdf/" + model_name + "_SSS_VVV_ensamble.nc"

	# filename path of threshold
	threshold_path = "/home/cuwalid/training/historical/regional/postpp/netcdf/HAD_IMERGba_sim0_MAM_extremes_quantiles.nc"


	#fname_var = fname_var.replace("YYYY", str(iyear))
	for iseason in season:
		#for ivar in ["dis", "twsc", "tht", "wrsi"]:
		for ivar in field:
			## choose path depending on variable
			#if (ivar == "twsc") or (ivar == "wrsi"):
			#	ifname = fname_ensamble.replace("VVV", ivar)
			#else:
			#	ifname = fname_ensamble.replace("_VVV", "")
			
			# chose path depending on the season
			#fname_threshold = threshold_path.copy()
			if iseason is None:
				ifname_threshold = threshold_path.replace("_SSS", "")
				ifname = fname_ensamble.replace("_VVV", "")
				ifname = ifname.replace("_SSS", "")
			else:
				ifname_threshold = threshold_path.replace("SSS", iseason)
				ifname = fname_ensamble.replace("VVV", ivar)
				ifname = ifname.replace("SSS", iseason)
						
			# specify path for dataset
			#netcdf_path = "D:/HAD/output/HAD_IMERGb_sim_"+ str(iyear)+"_grid.nc"
			
			# specify paht for threshold dataset
			#nc_path_threshold = "D:/HAD/postpp/netcdf/HAD_IMERGb_D2E_sim_" + iseason + "_quantiles.nc"
			
			# get tercile forecasting
			tercile = cuwalid.get_tercile_probabilities_from_ensamble_netcdf(
					ifname, ifname_threshold,
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