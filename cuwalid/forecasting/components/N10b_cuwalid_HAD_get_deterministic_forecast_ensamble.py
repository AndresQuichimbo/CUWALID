import cuwalid.tools.CUWALID_forecast_tools as cuwalid
import xarray as xr

def get_deterministic_forecast_ensamble(model_path, model_name, season, variables, postpp_path):
	"""This function calculates the probabilistic forecasting using the tercile approach
	from the ensamble dataset. It will create a file for each analised variable
	"""

	iyear = 2022

	#season = ["MAM", "OND"]
	#ivar = "dis"
	#iseason = "MAM"
	#iseason = "OND"

	# model name
	#model_name = "MAM_2022_realization"

	# list of season to calculate
	#season = ["MAM"]

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	# model simulation results path
	#model_path = "/home/cuwalid/training/forecast/regional/outputs/"#_13_grid.nc

	# path of postprocessing
	#postpp_path = "/home/cuwalid/training/forecast/regional/postpp/"

	# get ensamble name
	fname_ensamble = postpp_path+"netcdf/" + model_name + "_SSS_VVV_ensamble.nc"

	# filename path of threshold
	threshold_path = "/home/cuwalid/training/historical/regional/postpp/netcdf/HAD_IMERGba_sim0_SSS_mean.nc"

	# replace year
	#postpp_path = postpp_path.replace("YYYY", str(iyear))
	#threshold_path = threshold_path.replace("YYYY", str(iyear))

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
						
			# get mean values
			mean = cuwalid.read_dataset(ifname, var_name=ivar).mean(dim="sim")
			mean = mean.rename("average")
			#print(mean)
			#print(cuwalid.read_dataset(ifname_threshold, var_name=ivar))
			# get anomaly
			anomaly = mean - cuwalid.read_dataset(ifname_threshold, var_name=ivar)
			anomaly = anomaly.rename("anomaly")
			#print(anomaly)
			# get variability
			std = cuwalid.read_dataset(ifname, var_name=ivar).std(dim="sim")
			std = std.rename("Variability")
			#print(std)
			# store all variables in one netcdf file
			det_forecast = xr.merge([mean, anomaly, std])
			
			# save as NETCDF files
			if iseason is None:
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+str(iyear)+"_deterministic_forecast.nc"
			else:
				fname_out = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_deterministic_forecast.nc"
			
			# save probabilistic forecast as netcdf
			det_forecast.to_netcdf(fname_out)