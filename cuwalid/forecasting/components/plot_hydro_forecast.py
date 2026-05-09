#import pyproj as pp
import os
import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import cuwalid.tools.CUWALID_mfile_tools as cuwalid
import cuwalid.tools.CUWALID_view_tool as cuwalidplt

def plot_tercile_probability_forecast(model_path, model_name, season, variables, postpp_path, iyear=2022, path_mask=None, path_river=None, shapefile_county=None):
	"""This function creates a figure from the tercile forecats
	file. Variabkes names of the file must be: "AN", "NN, "BN".
	"""

	# load dataset of mask for basin and streams
	if path_mask is None:
		path_mask = "../HAD/WS/input_model/HAD_mask_utm.asc"
	if path_river is None:
		path_river =  "../HAD/WS/input_model/HAD_riv_length_utm.asc"


	# path of shapefile to include in the plot
	#shapefile_county = "D:/HAD/data/gis/Horn_Africa/Horn_africa_contry.shp"
	#shapefile_county = "/home/cuwalid/Datasets/data/shp/wgs84/HAD_regional_basin.shp"

	# specified fields
	field = cuwalid.drop_false_keys(variables)


	for iseason in season:
		for ivar in field:
			# Ensure directories for `netcdf` and `fig` exist
			netcdf_dir = os.path.join(postpp_path, "netcdf")
			fig_dir = os.path.join(postpp_path, "fig")
			os.makedirs(netcdf_dir, exist_ok=True)
			os.makedirs(fig_dir, exist_ok=True)

			# Save as NETCDF files
			if iseason is None:
				fname = os.path.join(netcdf_dir, f"{model_name}_{ivar}_{iyear}_probabilistic_tercile_forecast.nc")
			else:
				fname = os.path.join(netcdf_dir, f"{model_name}_{ivar}_{iseason}_{iyear}_probabilistic_tercile_forecast.nc")

			data = xr.open_dataset(fname)
			im = cuwalidplt.plot_probabilistic_tercile_forecast(
				data,
				title="Probabilistic Forecasting\n" +
				cuwalidplt.get_label_variable(ivar),
				reproject=True,
				fshapefile=shapefile_county,
				fmask=path_mask,
				cmap_type="outflow" if ivar in ["pet", "aet"] else "inflow"
			)

			# Ensure the `fig` directory exists and save the plot
			if iseason is None:
				fname_fig = os.path.join(fig_dir, f"{model_name}_{ivar}_{iyear}_probabilistic_tercile_forecast.png")
			else:
				fname_fig = os.path.join(fig_dir, f"{model_name}_{ivar}_{iseason}_{iyear}_probabilistic_tercile_forecast.png")

			# Save the figure
			plt.savefig(fname_fig, dpi=300)


	
def plot_deterministic_forecast(model_path, model_name, season, variables, postpp_path, iyear=2022):
	"""This function creates a figure from the tercile forecats
	file. Variabkes names of the file must be: "AN", "NN, "BN".
	"""

	# load dataset of mask for basin and streams
	path_mask = "../HAD/WS/input_model/HAD_mask_utm.asc"
	path_river =  "../HAD/WS/input_model/HAD_riv_length_utm.asc"

	# path of shapefile to include in the plot
	#shapefile_county = "D:/HAD/data/gis/Horn_Africa/Horn_africa_contry.shp"
	shapefile_county = "/home/cuwalid/Datasets/data/shp/wgs84/HAD_regional_basin.shp"

	# specified fields
	field = cuwalid.drop_false_keys(variables)

	#ifname = fname_ensamble.replace("_VVV", "")

	#iyear = 2022
	#iseason = "MAM"

	for iseason in season:
		#fname = "/home/cuwalid/training/forecast/regional/postpp/netcdf/MAM_2022_realization_tht_MAM_2022_deterministic_forecast.nc"
		#fname = "D:/HAD/postpp/netcdf/MAM_2022_realization_pet_MAM_2022_probabilistic_tercile_forecast.nc"
		for ivar in field:
			# save as NETCDF files
			if iseason is None:
				fname = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+str(iyear)+"_deterministic_forecast.nc"
			else:
				fname = postpp_path+"netcdf/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_deterministic_forecast.nc"
				
			data = xr.open_dataset(fname)
			im = cuwalidplt.plot_deterministic_forecast(data,
					title="Deterministic Forecast\n"+cuwalidplt.get_label_variable(ivar),
					reproject=True, fshapefile=shapefile_county,
					plot_anomaly=True,
					fmask=path_mask)
				
			if iseason is None:
				fname_fig = postpp_path+"fig/" + model_name + "_" +ivar+"_"+str(iyear)+"_deterministic_forecast.png"
			else:
				fname_fig = postpp_path+"fig/" + model_name + "_" +ivar+"_"+iseason+"_"+str(iyear)+"_deterministic_forecast.png"
				
			#fname_fig = "D:/HAD/postpp/fig/IMERGag_sim0_MAM_tercile_forecasting_example.png"
			plt.savefig(fname_fig, dpi=300)
			#plt.show()