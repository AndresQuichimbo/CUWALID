#import netCDF4
import xarray as xr
import numpy as np
import cuwalid.tools.CUWALID_forecast_tools as cuwalid

def get_additional_variables_multi_netcdf(model_path, model_name, start_year, end_year):

	fname  = [
	#'/home/c1755103/HAD/HAD_output/HAD_IMERG_sim_28b_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2022)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2001, 2023)
	model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	]

	#imodel = "IMERGb_D2E_sim"

	field = ["wrsi", "aet"]

	# DO NOT MODIFY FROM HERE ---------------------------------------

	for ifield in field:
		
		for ifname in fname:
			if ifield == "wrsi":
				# Calculate WRSI 
				data = cuwalid.read_dataset(ifname, "aet")/cuwalid.read_dataset(ifname, "pet")
				data = data.rename("wrsi")
			else:
				# Calculate total evaporation
				data = cuwalid.read_dataset(ifname, "aet")+cuwalid.read_dataset(ifname, "egw")
				data = data.rename("aet")

			# Define the path for the yearly NetCDF file
			fname_output = ifname.split('.')[0]+'_'+ifield+'.nc'
			
			# Group by year and create a new dataset for each year
			
			# loop over years
			data.to_netcdf(fname_output)
	