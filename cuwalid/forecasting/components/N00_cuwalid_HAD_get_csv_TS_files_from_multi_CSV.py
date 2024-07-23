import os
import numpy as np
import pandas as pd

#model_name = "IMERGba_sim0"
#model_path = "'/home/c1755103/HAD/HAD_output/"

# DO NOT MODIFY FROM HERE =====================================
# this function is used for the historical simulations
# this function concatenate all csv files generates by the model

def get_csv_TS_files_from_multi_CSV(model_path, model_name, start_year, end_year):
	csv_file = [
	"_RZ_avg.csv",
	"_p_wte.csv",
	"_p_tht.csv",
	"_p_ssz.csv",
	"_p_rch.csv",
	"_p_inf.csv",
	"_p_gdh.csv",
	"_p_dis.csv",
	"_p_aet.csv",
	"_avg.csv",
	]

	for icsv_file in csv_file:
		fname = [
			#"/user/work/km19051/HAD_output/HAD_IMERG_sim_84_"+str(year)+"_avg.csv" for year in range(2000, 2006)
			#"/user/work/km19051/HAD_output/HAD_IMERG_sim_84_"+str(year)+"_p_dis.csv" for year in range(2000, 2006)
			model_path+model_name+"_"+ str(iyear) + icsv_file for iyear in range(start_year, end_year)
			]
		first_read = True
		for ifname in fname:
			if first_read == True:
				data = pd.read_csv(ifname)
				first_read = False
			else:
				data = pd.concat([data, pd.read_csv(ifname)], ignore_index=True)
		
		#fname = "/home/c1755103/HAD/HAD_output/HAD_IMERG_sim_73_p_dis.csv"
		fname = model_path+model_name+icsv_file
		data.to_csv(fname, index=False)

