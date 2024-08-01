import os
from datetime import datetime
import json
import sys
import numpy as np
import pandas as pd
from cuwalid.dryp.components.DRYP_store_parameters import get_store_parameters

class get_model_settings(object):
	"""
	"""
	def __init__(self, filename_inputs, first_read=1):
		"""Model parameter settings and input file names and location"""
		self.first_read = first_read
		
		# =================================================================
		# Get all variables
		with open(filename_inputs, 'r') as f:
			dryp_config = json.load(f)
		
		self.Mname = get_variable(dryp_config, "drylandmodel", "model_name")
		  
		#==================================================================        
		# MODEL PARAMETERS SETTINGS		

		filename_simpar = get_variable(dryp_config, "OUTPUT", "path_setting")
		
		with open(filename_simpar, 'r') as f:
			settings_config = json.load(f)
		
		self.ini_date = datetime.strptime(get_variable(settings_config, "SETTINGS", "start_date"), '%Y %m %d')
		self.end_date = datetime.strptime(get_variable(settings_config, "SETTINGS", "end_date"), '%Y %m %d')
		self.dtOF = int(get_variable(settings_config, "SETTINGS", "dt_of"))
		self.dtUZ = int(get_variable(settings_config, "SETTINGS", "dt_gw"))
		self.dtSZ = int(get_variable(settings_config, "SETTINGS", "dt_gw"))  # Assuming the same value

		netcdf_opt = get_variable(settings_config, "READING", "data_read").split()
		time_step = get_variable(settings_config, "READING", "data_step").split()
		reproj_opt = get_variable(settings_config, "READING", "data_reproject").split()
		interp_opt = get_variable(settings_config, "READING", "data_interp").split()

		# Datasets format
		self.netcf_pre = int(netcdf_opt[0])
		self.netcf_ETo = int(netcdf_opt[1])
		self.netcf_ABC = int(netcdf_opt[2])
		self.netcf_kc = int(netcdf_opt[3])
		self.netcf_Flux = int(netcdf_opt[4])
		self.netcf_savi = int(netcdf_opt[5])
		self.netcf_savi_min = int(netcdf_opt[6])
		self.netcf_savi_max = int(netcdf_opt[7])

		# Dataset time step
		self.dt_pre = int(time_step[0])
		self.dt_ETo = int(time_step[1])
		self.dt_ABC = int(time_step[2])
		self.dt_kc = int(time_step[3])
		self.dt_Flux = int(time_step[4])
		self.dt_savi = int(time_step[5])
		self.dt_savi_min = int(time_step[6])
		self.dt_savi_max = int(time_step[7])

		# Datasets reprojection
		self.reproject_pre = int(reproj_opt[0])
		self.reproject_ETo = int(reproj_opt[1])
		self.reproject_ABC = int(reproj_opt[2])
		self.reproject_kc = int(reproj_opt[3])
		self.reproject_Flux = int(reproj_opt[4])
		self.reproject_savi = int(reproj_opt[5])
		self.reproject_savi_min = int(reproj_opt[6])
		self.reproject_savi_max = int(reproj_opt[7])

		# Datasets interpolate
		self.interpolate_pre = int(interp_opt[0])
		self.interpolate_ETo = int(interp_opt[1])
		self.interpolate_ABC = int(interp_opt[2])
		self.interpolate_kc = int(interp_opt[3])
		self.interpolate_Flux = int(interp_opt[4])
		self.interpolate_savi = int(interp_opt[5])
		self.interpolate_savi_min = int(interp_opt[6])
		self.interpolate_savi_max = int(interp_opt[7])

		self.inf_method = bool(get_variable(settings_config, "COMPONENTS", "method_inf"))

		if self.inf_method > 3:
			self.inf_method = 0

		# read groundwater model activation
		aux_run_GW = get_variable(settings_config, "COMPONENTS", "method_gw").split()
		self.run_GW = int(aux_run_GW[0])

		# groundwater aquifer functions
		self.gw_func = int(aux_run_GW[1]) if len(aux_run_GW) > 1 else 0

		# save netcdf files of model results
		self.save_netcdf = bool(get_variable(settings_config, "OUTPUT", "output_grid"))

		# save results
		self.save_results = True

		# activate lakes
		self.lakes = int(get_variable(settings_config, "OUTPUT", "not used 1"))

		# temporal aggregation of model outputs
		self.dt_results = get_variable(settings_config, "OUTPUT", "output_dt")

		# save discharge units
		self.save_dis_depth = get_variable(settings_config, "OUTPUT", "Save discharge in volumetric rate units")

		self.kFlux = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_of_kflow") or 1)
		self.GW_Cond_factor = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_sz_ksy") or 50)

		# Unsaturated zone factors
		self.kdt_r = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_uz_kdt"))
		self.kDroot = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_uz_kdroot"))
		self.kAWC = 1.0
		self.kKsat = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_uz_kkast"))
		self.k_sigma_ks = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_uz_ksigma"))

		# River routing factors
		self.kKch = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_riv_kksat"))
		self.kTch = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_riv_kdecay"))
		self.kpe = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_riv_kwidth"))

		# Saturated zone factors
		self.kKsat_gw = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_sz_kksat"))
		self.kSy_gw = float(get_variable(settings_config, "GLOBAL_FACTORS", "factor_sz_ksy"))

		# Read model time step conditions
		self.dt = np.min([self.dtOF, self.dtUZ, self.dtSZ])

		if self.dt > 60:
			self.dt_sub_hourly = 1
			self.dt_hourly = int(1440 / self.dt)
			self.unit_sim = self.dt / 1440
			self.unit_sim_k = self.dt * 24 / 1440
			self.kT_units = self.dt / 60
		else:
			self.dt_sub_hourly = int(60 / self.dt)
			self.dt_hourly = 24
			self.unit_sim = self.dt / 60
			self.unit_sim_k = self.dt / 60
			self.kT_units = self.dt / 60

		self.unit_change_manning = (1 / (self.dt * 60)) ** (3 / 5)
		self.Agg_method = str(self.dt) + 'T'
		self.river_banks = 100.0
		self.run_FAc = 1
		self.dt_OF = 1
		self.ndays = (self.end_date - self.ini_date).days

		# Update final parameters
		settings_config["GLOBAL_FACTORS"]["factor_uz_kkast"] = self.kKsat * self.unit_sim_k
		settings_config["GLOBAL_FACTORS"]["factor_riv_kksat"] = self.kKch * self.unit_sim_k
		settings_config["GLOBAL_FACTORS"]["factor_riv_kdecay"] = self.kT_units * 3600.0 * self.kTch
		settings_config["GLOBAL_FACTORS"]["factor_sz_kksat"] = self.kKsat_gw * self.unit_sim_k

		# Get list of files required to parameterize the model
		self.fname_surface = get_list_of_surface_files(dryp_config, settings_config)
		self.fname_soil = get_list_of_soil_files(dryp_config, settings_config)
		self.fname_riparian = get_list_of_riparian_soil_files(dryp_config, settings_config)
		self.fname_aquifer = get_list_of_groundwater_files(dryp_config, settings_config)
		self.fname_interception_hillslope = get_list_of_interception_hillslope_files(dryp_config, settings_config)
		self.fname_interception_riparian = get_list_of_interception_riparian_files(dryp_config, settings_config)

		#==================================================================
		# Meteorological data
		self.fname_TSPre = get_variable(dryp_config, "METEO", "path_pre")
		self.fname_TSMeteo = get_variable(dryp_config, "METEO", "path_pet")
		self.fname_TSABC = get_variable(dryp_config, "METEO", "path_aof")

		# READ DATASETS PROJECTION
		self.fname_proj = None
		self.proj_model = None
		self.proj_data = None

		if len(dryp_config.get("drylandmodel", {})) == 98:
			self.fname_proj = get_variable(dryp_config, "OUTPUT", "path_projection")
			if os.path.exists(self.fname_proj):
				dfproj = pd.read_csv(self.fname_proj)
				self.proj_model = dfproj.PROJECTION[1]
				self.proj_data = dfproj.PROJECTION[4]
			else:
				print("Projection system not provided")

		self.fname_store = 'None'
		if len(dryp_config.get("drylandmodel", {})) == 100:
			self.fname_store = dryp_config["drylandmodel"][99]
		self.store = get_store_parameters(self.fname_store)

		# Vegetation parameters
		self.fname_TSKc = get_variable(dryp_config, "VEGETATION", "path_veg_kc")
		self.fname_Rip_width = get_variable(dryp_config, "VEGETATION", "path_veg_lulc")
		self.fname_Rip_init = get_variable(dryp_config, "VEGETATION", "path_veg_nn")

		# Output files maps
		self.DirOutput = get_variable(dryp_config, "OUTPUT", "path_output")
		self.fname_DISpoints = get_variable(dryp_config, "OUTPUT", "path_out_sz")
		self.fname_SMDpoints = get_variable(dryp_config, "OUTPUT", "path_out_uz")
		self.fname_GWpoints = get_variable(dryp_config, "OUTPUT", "path_out_oz")

		print("Model Name: ", self.Mname)

		# Create directories for saving results
		print('********************* Output Directory **********************')
		if not os.path.exists(self.DirOutput):
			os.mkdir(self.DirOutput)
			print("Directory ", self.DirOutput, " Created ")
		else:
			print("Directory ", self.DirOutput, " already exists")

		# Output filenames
		self.fnameTS_grid = os.path.join(self.DirOutput, self.Mname + '_grid')
		self.fnameTS_point = os.path.join(self.DirOutput, self.Mname + '_p_')
		self.fnameTS_UZ = os.path.join(self.DirOutput, self.Mname + '_UZ_')
		self.fnameTS_RZ = os.path.join(self.DirOutput, self.Mname + '_RZ_')
		self.fnameTS_RZ_avg = os.path.join(self.DirOutput, self.Mname + '_RZ_avg')
		self.fnameTS_avg = os.path.join(self.DirOutput, self.Mname + '_avg')			

class get_list_of_interception_hillslope_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		self.fname_interception = get_variable(dryp_config, "OUTPUT", "path_vg_settings")
		if os.path.exists(self.fname_interception):
			fcp = pd.read_csv(self.fname_interception)
			# Soil component
			self.fname_av = fcp.INTERCEPTION[1]
			self.fname_savi = fcp.INTERCEPTION[3]
			self.fname_laia = fcp.INTERCEPTION[5]
			self.fname_laib = fcp.INTERCEPTION[7]
			self.fname_savi_min = fcp.INTERCEPTION[9]
			self.fname_savi_max = fcp.INTERCEPTION[11]
			self.fname_lai = fcp.INTERCEPTION[13]
			self.fname_tap_depth = fcp.INTERCEPTION[27]
			self.fname_extintion_depth = fcp.INTERCEPTION[29]
			# filename of initial conditions
			self.fname_fcw_canopy = fcp.INTERCEPTION[31]
			self.fname_Sc0_canopy = fcp.INTERCEPTION[33]
		else:
			#Soil component
			self.fname_savi = 'None'
			self.fname_av = 'None'
			self.fname_laia = 'None'
			self.fname_laib = 'None'
			self.fname_savi_max = 'None'
			self.fname_savi_min = 'None'
			self.fname_lai = 'None'
			self.fname_tap_depth = 'None'
			self.fname_extintion_depth = 'None'
			self.fname_fcw_canopy = 'None'
			self.fname_Sc0_canopy = 'None'

		self.fname_SoilDepth = get_variable(dryp_config, "UNSATURATED", "path_uz_root")
		self.kDroot = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kdroot"))

class get_list_of_interception_riparian_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		self.fname_interception = get_variable(dryp_config, "OUTPUT", "path_vg_settings")
		if os.path.exists(self.fname_interception):
			fcp = pd.read_csv(self.fname_interception)
			#Riparian component
			self.fname_av = fcp.INTERCEPTION[15]
			self.fname_savi = fcp.INTERCEPTION[15]
			#self.fname_kc = fcp.INTERCEPTION[3]
			#self.fname_avc = fcp.INTERCEPTION[5]
			self.fname_laia = fcp.INTERCEPTION[17]
			self.fname_laib = fcp.INTERCEPTION[19]
			self.fname_savi_min = fcp.INTERCEPTION[21]
			self.fname_savi_max = fcp.INTERCEPTION[23]
			self.fname_lai = fcp.INTERCEPTION[25]
			self.fname_tap_depth = fcp.INTERCEPTION[27]
			self.fname_extintion_depth = fcp.INTERCEPTION[29]
			# filename of initial conditions
			self.fname_fcw_canopy = fcp.INTERCEPTION[31]
			self.fname_Sc0_canopy = fcp.INTERCEPTION[33]
		else:
			#Soil component
			self.fname_savi = 'None'
			self.fname_av = 'None'
			self.fname_laia = 'None'
			self.fname_laib = 'None'
			self.fname_savi_max = 'None'
			self.fname_savi_min = 'None'
			self.fname_lai = 'None'
			self.fname_tap_depth = 'None'
			self.fname_extintion_depth = 'None'
			self.fname_fcw_canopy = 'None'
			self.fname_Sc0_canopy = 'None'

		self.fname_SoilDepth = get_variable(dryp_config, "UNSATURATED", "path_uz_root")
		self.kDroot = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kdroot"))

class get_list_of_surface_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		self.fname_DEM = get_variable(dryp_config, "TERRAIN", "path_dem")
		self.fname_Qo = get_variable(dryp_config, "TERRAIN", "path_Qo")
		self.fname_FlowDir = get_variable(dryp_config, "TERRAIN", "path_fdl")
		self.fname_kTchannel = get_variable(dryp_config, "TERRAIN", "path_riv_decay")
		self.fname_Mask = get_variable(dryp_config, "TERRAIN", "path_mask")
		self.fname_River = get_variable(dryp_config, "TERRAIN", "path_riv_len")
		self.fname_RiverWidth = get_variable(dryp_config, "TERRAIN", "path_riv_width")
		self.fname_RiverElev = get_variable(dryp_config, "TERRAIN", "path_riv_elev")
		self.fname_Ksat = get_variable(dryp_config, "UNSATURATED", "path_riv_ksat")
		if self.fname_Ksat is None:
			self.fname_Ksat = get_variable(dryp_config, "UNSATURATED", "path_uz_ksat")
		self.fname_Q_ini = get_variable(dryp_config, "UNSATURATED", "path_riv_ksat")

		# TODO: Check this if statement
		if len(get_variable(dryp_config, "drylandmodel")) == 96:
			self.fname_bc = get_variable(dryp_config, "OUTPUT", "path_of_settings")
		else:
			self.fname_bc = 'None'

		self.fname_TSOF = 'None'
		self.filename_OF_points = 'None'

		if os.path.exists(self.fname_bc):
			fbc = pd.read_csv(self.fname_bc)
			self.fname_TSOF = fbc.OFBC[1]
			self.filename_OF_points = fbc.OFBC[3]

		self.fname_bathymetry = 'None'
		if os.path.exists(get_variable(dryp_config, "OUTPUT", "path_gw_settings")):
			fgw = pd.read_csv(get_variable(dryp_config, "OUTPUT", "path_gw_settings"))
			self.fname_bathymetry = fgw.GROUNDWATER[18]  # Constant flux boundary

		# TODO: Check this if statement
		if len(get_variable(dryp_config, "drylandmodel")) == 94:
			self.fname_riparian_zone = get_variable(dryp_config, "OUTPUT", "path_rp_settings")
		else:
			self.fname_riparian_zone = 'none'

		self.fname_ripwidth = "none"
		if os.path.exists(self.fname_riparian_zone):
			frz = pd.read_csv(self.fname_riparian_zone)
			self.fname_ripwidth = frz.RIPARIAN[21]  # riparian width [-]

		self.kKch = float(get_variable(factors, "GLOBAL_FACTORS", "factor_riv_kksat"))
		self.kTch = float(get_variable(factors, "GLOBAL_FACTORS", "factor_riv_kdecay"))

class get_list_of_soil_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		self.fname_n = get_variable(dryp_config, "UNSATURATED", "path_uz_theta_sat")  # porosity (n)
		self.fname_theta_r = get_variable(dryp_config, "UNSATURATED", "path_uz_theta_res")  # Saturated infiltration rate (a-Ks)
		self.fname_theta_AWC = get_variable(dryp_config, "UNSATURATED", "path_uz_theta_awc")  # Available water content (AWC)
		self.fname_theta_wp = get_variable(dryp_config, "UNSATURATED", "path_uz_theta_wp")  # wilting point (wp)
		self.fname_SoilDepth = get_variable(dryp_config, "UNSATURATED", "path_uz_root")  # root zone (D)
		self.fname_b_SOIL = get_variable(dryp_config, "UNSATURATED", "path_uz_lambda")  # Soil parameter alpha (b)
		self.fname_PSI = get_variable(dryp_config, "UNSATURATED", "path_uz_psi")  # Soil parameter alpha (alpha)
		self.fname_Ksat = get_variable(dryp_config, "UNSATURATED", "path_uz_ksat")  # Saturated infiltration rate (a-Ks)
		self.fname_sigma_ks = get_variable(dryp_config, "UNSATURATED", "path_uz_sigmaksat")

		self.fname_theta = get_variable(dryp_config, "UNSATURATED", "path_uz_theta")  # Initial water content [-]

		self.kdt_r = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kdt"))
		self.kDroot = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kdroot"))  # k for soil depth
		self.kAWC = 1.0  # float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kawc"))  # k for AWC
		self.kKsat = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kkast"))  # k for soil infiltration
		self.k_sigma_ks = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_ksigma"))

class get_list_of_riparian_soil_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		# TODO: Check if statement
		if len(get_variable(dryp_config, "drylandmodel")) == 94:
			self.fname_riparian_zone = get_variable(dryp_config, "OUTPUT", "path_rp_settings")
		else:
			self.fname_riparian_zone = 'None'

		if os.path.exists(self.fname_riparian_zone):
			frz = pd.read_csv(self.fname_riparian_zone)
			self.fname_n = frz.RIPARIAN[1]        # porosity (n)
			self.fname_theta_r = frz.RIPARIAN[3]  # residual water content
			self.fname_theta_AWC = frz.RIPARIAN[5]  # Available water content (AWC)
			self.fname_theta_wp = frz.RIPARIAN[7]  # wilting point (wp)
			self.fname_SoilDepth = frz.RIPARIAN[9] # riparian root zone depth (D)
			self.fname_b_SOIL = frz.RIPARIAN[11]  # Soil particle distribution (lambda)
			self.fname_PSI = frz.RIPARIAN[13]      # Air-entry pressure/suction head (psi)
			self.fname_Ksat = frz.RIPARIAN[15]  # Channel Sat. hydraulic conductivity (Ksat)
			self.fname_sigma_ks = frz.RIPARIAN[17] # riparian sigma Ksat
			# filename of initial conditions
			self.fname_theta = frz.RIPARIAN[19]    # Initial water content [-]
			# filename riparian channel width
			self.fname_ripwidth = frz.RIPARIAN[21] # Initial water content [-]
		else:
			self.fname_n = get_variable(dryp_config, "UNSATURATED", "path_uz_theta_sat")  # riparian porosity (n)
			self.fname_theta_r = get_variable(dryp_config, "UNSATURATED", "path_uz_theta_res")  # riparian Saturated infiltration rate (a-Ks)
			self.fname_theta_AWC = get_variable(dryp_config, "UNSATURATED", "path_uz_theta_awc")  # riparian Available water content (AWC)
			self.fname_theta_wp = get_variable(dryp_config, "UNSATURATED", "path_uz_theta_wp")  # riparian wilting point (wp)
			self.fname_SoilDepth = get_variable(dryp_config, "UNSATURATED", "path_uz_root")  # riparian root zone (D)
			self.fname_b_SOIL = get_variable(dryp_config, "UNSATURATED", "path_uz_lambda")  # riparian Soil parameter alpha (b)
			self.fname_PSI = get_variable(dryp_config, "UNSATURATED", "path_uz_psi")  # riparian Soil parameter alpha (alpha)
			self.fname_sigma_ks = get_variable(dryp_config, "UNSATURATED", "path_uz_sigmaksat")  # riparian sigma Ksat
			self.fname_theta = get_variable(dryp_config, "UNSATURATED", "path_uz_theta")  # riparian Initial water content [-]
			self.fname_Ksat = get_variable(dryp_config, "UNSATURATED", "path_riv_ksat")  # riparian Channel Saturated hydraulic conductivity (Ks)
			if self.fname_Ksat is None:
				self.fname_Ksat = get_variable(dryp_config, "UNSATURATED", "path_uz_ksat")
			self.fname_ripwidth = "none"

		self.kDroot = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kdroot"))  # k for soil depth
		self.kAWC = 1.0  # float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kawc"))  # k for AWC
		self.k_sigma_ks = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_ksigma"))
		self.kKsat = float(get_variable(factors, "GLOBAL_FACTORS", "factor_riv_kksat"))  # infiltration on channel

class get_list_of_groundwater_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		
		aux_run_GW = get_variable(factors, "COMPONENTS", "method_gw").split()    
		self.run_GW = int(aux_run_GW[0])
		
		self.fname_GWdomain = get_variable(dryp_config, "SATURATED", "path_sz_mask")  # GW Boundary conditions
		self.fname_SZ_Ksat = get_variable(dryp_config, "SATURATED", "path_sz_ksat")  # Saturated hydraulic conductivity (Ks)
		self.fname_SZ_Sy = get_variable(dryp_config, "SATURATED", "path_sz_sy")  # Specific yield
		self.fname_FHB = get_variable(dryp_config, "SATURATED", "path_sz_bc_flux")  # flux head boundary
		self.fname_CHB = get_variable(dryp_config, "SATURATED", "path_sz_bc_head")  # Constant flux boundary
		self.fname_SZ_bot = get_variable(dryp_config, "SATURATED", "path_sz_bottom")  # path_sz_bottom
		
		self.fname_thickness = 'None'
		self.fname_b_aq = 'None'
		self.fname_aquifertype = 'None'
		self.fname_bathymetry = 'None'

		gw_additional_params_path = get_variable(dryp_config, "OUTPUT", "path_gw_settings")
		
		if os.path.exists(gw_additional_params_path):
			fgw = pd.read_csv(gw_additional_params_path)
			self.fname_thickness = fgw.GROUNDWATER[1]
			self.fname_b_aq = fgw.GROUNDWATER[3]
			self.fname_aquifertype = fgw.GROUNDWATER[16]  # Constant flux boundary
			self.fname_bathymetry = fgw.GROUNDWATER[18]  # Constant flux boundary
		
		self.fname_SZ_botb = 'None'
		self.fname_SZ_Ksatb = 'None'
		self.fname_SZ_Syb = 'None'
		self.fname_SZ_Ssb = 'None'
		self.fname_GWinib = 'None'
		self.fname_mask_of = 'None'
		
		if self.run_GW > 0:
			if os.path.exists(gw_additional_params_path):
				fgw = pd.read_csv(gw_additional_params_path)
				self.fname_thickness = fgw.GROUNDWATER[1]
				self.fname_b_aq = fgw.GROUNDWATER[3]
				self.fname_aquifertype = fgw.GROUNDWATER[16]  # Constant flux boundary
				self.fname_bathymetry = fgw.GROUNDWATER[18]  # Constant flux boundary

		self.fname_GWini = get_variable(dryp_config, "SATURATED", "path_sz_wte")  # Initial water table
		self.fname_DEM = get_variable(dryp_config, "TERRAIN", "path_dem")
		
		self.kKsat = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_kkast"))  # k for hydraulic conductivity
		self.kSy = float(get_variable(factors, "GLOBAL_FACTORS", "factor_uz_ksigma"))  # k for specific yield

def get_variable(json, var_1, var_2=None):
	if var_2 is None:
		if var_1 in json:
			variable = json[var_1]
		elif var_1 in default_variables:
			variable = default_variables[var_1]
			if variable == 'required':
				print(f"ERROR: {var_1} is required but not found in configuration json. Program will terminate.")
				sys.exit(1)
			print(f"WARNING: {var_1} not found in configuration json. Using default of {variable}")
		else:
			variable = 'None'
			print(f"WARNING: {var_1} not found in configuration json. Using default of {variable}")
	else:
		if var_1 in json:
			if var_2 in json[var_1]:
				variable = json[var_1][var_2]
			elif var_2 in default_variables:
				variable = default_variables[var_2]
				if variable == 'required':
					print(f"ERROR: {var_1}:{var_2} is required but not found in configuration json. Program will terminate.")
					sys.exit(1)
				print(f"WARNING: {var_1}:{var_2} not found in configuration json. Using default of {variable}")
			else:
				variable = 'None'
		else:
			print(f"WARNING: {var_1}:{var_2} not found in configuration json. Using default of None")

	return variable

default_variables = {
	"path_dem": "required",
	"start_date": "required",
	"end_date": "required",
	"dt_of": 60,
	"dt_gw": 60,
	"read_pre": 0,
	"read_pet": 0,
	"read_abs": 0,
	"read_kc": 0,
	"read_savi": 0,
	"read_flux": 0,
	"dt_pre": 60,
	"dt_pet": 60,
	"dt_abs": 60,
	"dt_kc": 60,
	"dt_savi": 60,
	"dt_flux": 60,
	"rproj_pre": True,
	"rproj_pet": True,
	"rproj_abs": True,
	"rproj_kc": True,
	"rproj_savi": True,
	"activate_gw": True,
	"method_gw": 1,
	"output_csv": True,
	"output_grid": False,
	"output_dt": "1M",
	"factor_uz_kdt": 1,
	"factor_uz_kdroot": 1,
	"factor_uz_kawc": 1,
	"factor_uz_kkast": 1,
	"factor_uz_ksigma": 1,
	"factor_riv_kksat": 1,
	"factor_riv_kdecay": 1,
	"factor_riv_kwidth": 1,
	"factor_sz_kksat": 1,
	"factor_sz_ksy": 1,
	"factor_of_kflow": 1,
}

"""def get_store_variables(fname):
	This function read a file of boolean values indicating the variables to be
	save as grid and csv file
	Parameters
	fname: dryp_config of the paramter setting file
	Returns
	store_var: python object containing dictionaries to with boolean values
	"""	