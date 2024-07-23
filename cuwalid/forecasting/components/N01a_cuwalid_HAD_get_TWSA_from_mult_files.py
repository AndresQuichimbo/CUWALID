#import netCDF4
import xarray as xr
import numpy as np
import cuwalid.tools.CUWALID_forecast_tools as cuwalid

def get_TWSA_from_mult_files(model_path, model_name, start_year, end_year):
	fname  = [
	#'/home/c1755103/HAD/HAD_output/HAD_IMERG_sim_28b_'+ str(iyear) +'_grid.nc' for iyear in range(2003, 2022)
	#'/home/c1755103/HAD/HAD_output/HAD_IMERGba_sim0_'+ str(iyear) +'_grid.nc' for iyear in range(2001, 2023)
	model_path+model_name+"_"+ str(iyear) +'_grid.nc' for iyear in range(start_year, end_year)
	]

	#imodel = "IMERGb_D2E_sim"

	field = ['twsc']

	# DO NOT MODIFY FROM HERE ---------------------------------------

	for ifield in field:
			
		# concatenate dataset at selected fields
		data_concat = cuwalid.concatenate_netCDF(
			fname, ifield, agg="M", dim='time'
			)
		
		# accummulate dataset, just in case of TWSA
		if ifield == 'twsc':
			data_concat = data_concat.cumsum(dim='time')

			# Define the path for the yearly NetCDF file
			fname_list = [
				ifname.split('.')[0]+'_'+ifield+'.nc' for ifname in fname
				]
		
		# Group by year and create a new dataset for each year
		grouped = data_concat.groupby('time.year')
		
		# loop over years
		idfname = 0
		for year, yearly_data in grouped:
			# Adjust the path and filename format as needed
			#output_filename = "/home/c1755103/HAD/HAD_output/HAD_IMERGb_sim_" + ifield + "_"+str(year)+".nc"
			
			# Save the yearly data to a NetCDF file
			output_filename = fname_list[idfname]
			yearly_data.to_netcdf(output_filename)
			idfname += 1