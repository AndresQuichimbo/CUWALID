import os
from datetime import datetime
import json
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
		
		self.Mname = dryp_config["drylandmodel"]["Model name"]
		  

		#==================================================================        
		# MODEL PARAMETERS SETTINGS
		filename_simpar = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["MODEL PARAMETER SETTINGS FILE"]
		
		with open(filename_simpar, 'r') as f:
			settings_config = json.load(f)
		
		self.ini_date = datetime.strptime(settings_config["SIMULATION PERIOD AND TIME STEP"]["Initial date for simulation 1 (YYYY MM DD)"], '%Y %m %d')
		self.end_date = datetime.strptime(settings_config["SIMULATION PERIOD AND TIME STEP"]["Initial date for simulation 2 (YYYY MM DD)"], '%Y %m %d')
		self.dtOF = int(settings_config["SIMULATION PERIOD AND TIME STEP"]["OF Time step - dt_Pre (min)"])
		self.dtUZ = int(settings_config["SIMULATION PERIOD AND TIME STEP"]["GW Time step"])
		self.dtSZ = int(settings_config["SIMULATION PERIOD AND TIME STEP"]["GW Time step"])  # Assuming the same value

		netcdf_opt = settings_config["READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX"]["Read datasets: 0-csv 1-One-netCDF 2-Multi-netCDF"].split()
		time_step = settings_config["READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX"]["Dataset time step (minutes)"].split()
		reproj_opt = settings_config["READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX"]["Reproject datasets: 0- disable 1- enable"].split()
		interp_opt = settings_config["READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX"]["Interpolate datasets: 0- disable 1- enable"].split()
					
		# Datasets format
		self.netcf_pre = int(netcdf_opt[0])
		self.netcf_ETo = int(netcdf_opt[1])
		self.netcf_ABC = int(netcdf_opt[2])
		self.netcf_kc =  int(netcdf_opt[3])
		self.netcf_Flux = int(netcdf_opt[4])
		self.netcf_savi = int(netcdf_opt[5])
		self.netcf_savi_min = int(netcdf_opt[6])
		self.netcf_savi_max = int(netcdf_opt[7])
		
		# Dataset time step
		self.dt_pre = int(time_step[0])
		self.dt_ETo = int(time_step[1])
		self.dt_ABC = int(time_step[2])
		self.dt_kc =  int(time_step[3])
		self.dt_Flux = int(time_step[4])
		self.dt_savi = int(time_step[5])
		self.dt_savi_min = int(time_step[6])
		self.dt_savi_max = int(time_step[7])
		
		# Datasets reprojection
		self.reproject_pre = int(reproj_opt[0])
		self.reproject_ETo = int(reproj_opt[1])
		self.reproject_ABC = int(reproj_opt[2])
		self.reproject_kc =  int(reproj_opt[3])
		self.reproject_Flux = int(reproj_opt[4])
		self.reproject_savi = int(reproj_opt[5])
		self.reproject_savi_min = int(reproj_opt[6])
		self.reproject_savi_max = int(reproj_opt[7])
		
		# Datasets interpolate
		self.interpolate_pre = int(interp_opt[0])
		self.interpolate_ETo = int(interp_opt[1])
		self.interpolate_ABC = int(interp_opt[2])
		self.interpolate_kc =  int(interp_opt[3])
		self.interpolate_Flux = int(interp_opt[4])
		self.interpolate_savi = int(interp_opt[5])
		self.interpolate_savi_min = int(interp_opt[6])
		self.interpolate_savi_max = int(interp_opt[7])
						
		self.inf_method = bool(settings_config["MODEL COMPONENTS"]["Inf."])
		
		if self.inf_method > 3:
			self.inf_method = 0
		
		# read groundwater model activation
		aux_run_GW = settings_config["MODEL COMPONENTS"]["Run Groundwater-Enable Type: 0-Unc 1-func 2-Con"].split()
		self.run_GW = int(aux_run_GW[0])
		
		# groundwater aquifer functions
		if len(aux_run_GW) > 1:
			self.gw_func = int(aux_run_GW[1])
		else:
			self.gw_func = 0
		
		# save netcdf files of model results
		self.save_netcdf = False
		if settings_config["OUTPUT OPTIONS"]["Save state results in netcf files"]:
			self.save_netcdf = True
		
		# save results
		self.save_results = True
		
		# activate lakes
		self.lakes = int(settings_config["OUTPUT OPTIONS"]["not used 1"])
		
		# temporal aggregation of model outputs
		self.dt_results = settings_config["OUTPUT OPTIONS"]["Temporal aggregation results (eg. 3M Y H)"]
		
		# save discharge units
		self.save_dis_depth = settings_config["OUTPUT OPTIONS"]["Save discharge in volumetric rate units"]
		
		# TODO: Change this if statement
		if len(settings_config) >= 66:
			self.kFlux = float(settings_config["MODEL PARAMETERS FACTORS"]["Flux boundary condition factor"])
		else:
			self.kFlux = 1
		
		# TODO: Change this if statement
		if len(settings_config) >= 68:
			self.GW_Cond_factor = float(settings_config["MODEL PARAMETERS FACTORS"]["Aquifer specific yield factor"])
		else:
			self.GW_Cond_factor = 50
		
		# Unsaturated zone factors
		self.kdt_r = float(settings_config["MODEL PARAMETERS FACTORS"]["Runoff partition parameter (kdt-Sheeke)"])
		self.kDroot = float(settings_config["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])
		self.kAWC = 1.0
		self.kKsat = float(settings_config["MODEL PARAMETERS FACTORS"]["Infiltration rate factor - kKsat"])
		self.k_sigma_ks = float(settings_config["MODEL PARAMETERS FACTORS"]["Heterogeneity factor - k_sigma - (Upscaled GA)"])
		
		# River routing factors
		self.kKch = float(settings_config["MODEL PARAMETERS FACTORS"]["Transmission losses - Kch (m/h)"])
		self.kTch = float(settings_config["MODEL PARAMETERS FACTORS"]["Decay discharge - T - (hours)"])
		self.kpe = float(settings_config["MODEL PARAMETERS FACTORS"]["Channel width parameter (pe-not activated)"])
		
		# Saturated zone factors
		self.kKsat_gw = float(settings_config["MODEL PARAMETERS FACTORS"]["Aquifer saturated hydraulic conductivity"])
		self.kSy_gw = float(settings_config["MODEL PARAMETERS FACTORS"]["Aquifer specific yield factor"])
		
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
		settings_config["MODEL PARAMETERS FACTORS"]["Infiltration rate factor - kKsat"] = self.kKsat * self.unit_sim_k
		settings_config["MODEL PARAMETERS FACTORS"]["Transmission losses - Kch (m/h)"] = self.kKch * self.unit_sim_k
		settings_config["MODEL PARAMETERS FACTORS"]["Decay discharge - T - (hours)"] = self.kT_units * 3600.0 * self.kTch
		settings_config["MODEL PARAMETERS FACTORS"]["Aquifer saturated hydraulic conductivity"] = self.kKsat_gw * self.unit_sim_k
		
		# Get list of files required to parameterize the model
		self.fname_surface = get_list_of_surface_files(dryp_config, settings_config)
		self.fname_soil = get_list_of_soil_files(dryp_config, settings_config)
		self.fname_riparian = get_list_of_riparian_soil_files(dryp_config, settings_config)
		self.fname_aquifer = get_list_of_groundwater_files(dryp_config, settings_config)
		self.fname_interception_hillslope = get_list_of_interception_hillslope_files(dryp_config, settings_config)
		self.fname_interception_riparian = get_list_of_interception_riparian_files(dryp_config, settings_config)
		
		#==================================================================
		# Meterological data
		self.fname_TSPre = dryp_config["METEOROLOGICAL DATA"]["Precipitation"]
		self.fname_TSMeteo = dryp_config["METEOROLOGICAL DATA"]["Potential Evapotranspiration"]
		self.fname_TSABC = dryp_config["METEOROLOGICAL DATA"]["Water abstractions file"]
		
		# READ DATASETS PROJECTION
		self.fname_proj = None
		self.proj_model = None
		self.proj_data = None
		
		# TODO: Check this if statement
		if len(dryp_config["drylandmodel"]) == 98:
			self.fname_proj = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["DATASET PROJECTIONS AND COORDINANTES"]
			if os.path.exists(self.fname_proj):
				dfproj = pd.read_csv(self.fname_proj)
				self.proj_model = dfproj.PROJECTION[1]
				self.proj_data = dfproj.PROJECTION[4]
			else:
				print("Projection system not provided")
		
		self.fname_store = 'None'
		# TODO: Check this if statement
		if len(dryp_config["drylandmodel"]) == 100:
			self.fname_store = dryp_config["drylandmodel"][99]
		self.store = get_store_parameters(self.fname_store)
		
		# Vegetation parameters
		self.fname_TSKc = dryp_config["SURFACE COMPONENTS"]["Vegetation type Kc"]
		self.fname_Rip_width = dryp_config["SURFACE COMPONENTS"]["Soil land use"]
		self.fname_Rip_init = dryp_config["SURFACE COMPONENTS"]["Other"]
		
		# Output files maps
		self.DirOutput = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["Folder location results"]
		self.fname_DISpoints = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["Discharge point results"]
		self.fname_SMDpoints = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["Soil point results output"]
		self.fname_GWpoints = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["Groundwater point results"]
		
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
		self.fname_interception = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["INTERCEPTION MODEL"]
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

		self.fname_SoilDepth = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil Depth (D)"]  # root zone (D)
		self.kDroot = float(factors["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])  # k for soil depth

class get_list_of_interception_riparian_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		self.fname_interception = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["INTERCEPTION MODEL"]
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
		self.fname_SoilDepth = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil Depth (D)"]  # root zone (D)
		self.kDroot = float(factors["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])  # k for soil depth

class get_list_of_surface_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		self.fname_DEM = dryp_config["TERRAIN COMPONENTS"]["Topography (DEM)"]
		self.fname_Qo = dryp_config["TERRAIN COMPONENTS"]["Cell factor area"]
		self.fname_FlowDir = dryp_config["TERRAIN COMPONENTS"]["Flow Direction (fd)"]
		self.fname_kTchannel = dryp_config["TERRAIN COMPONENTS"]["River decay parameters"]
		self.fname_Mask = dryp_config["TERRAIN COMPONENTS"]["Basin Mask (catchment)"]
		self.fname_River = dryp_config["TERRAIN COMPONENTS"]["River length"]
		self.fname_RiverWidth = dryp_config["TERRAIN COMPONENTS"]["River width"]
		self.fname_RiverElev = dryp_config["TERRAIN COMPONENTS"]["River bottom elevation"]
		self.fname_Ksat = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Channel saturated hydraulic conductivity"]
		if self.fname_Ksat is None:
			self.fname_Ksat = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Saturated hydraulic conductivity"]
		self.fname_Q_ini = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Channel saturated hydraulic conductivity"]

		# TODO: Check this if statement
		if len(dryp_config["drylandmodel"]) == 96:
			self.fname_bc = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["BOUNDARY CONDITIONS OF"]
		else:
			self.fname_bc = 'None'
		
		self.fname_TSOF = 'None'
		self.filename_OF_points = 'None'
		
		if os.path.exists(self.fname_bc):
			fbc = pd.read_csv(self.fname_bc)
			self.fname_TSOF = fbc.OFBC[1]
			self.filename_OF_points = fbc.OFBC[3]
		
		self.fname_bathymetry = 'None'
		if os.path.exists(dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"]):
			fgw = pd.read_csv(dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"])
			self.fname_bathymetry = fgw.GROUNDWATER[18] # Constant flux boundary

		# TODO: Check this if statement
		if len(dryp_config["drylandmodel"]) == 94:
			self.fname_riparian_zone = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["RIPARIAN PROPERTIES"]
		else:
			self.fname_riparian_zone = 'none'
		
		self.fname_ripwidth = "none"
		if os.path.exists(self.fname_riparian_zone):
			frz = pd.read_csv(self.fname_riparian_zone)
			self.fname_ripwidth = frz.RIPARIAN[21]	# riparian width [-]

		self.kKch = float(factors["MODEL PARAMETERS FACTORS"]["Transmission losses - Kch (m/h)"])  # infiltration on channel
		self.kTch = float(factors["MODEL PARAMETERS FACTORS"]["Decay discharge - T - (hours)"])  # Runoff decay flow factor

class get_list_of_soil_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		self.fname_n = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil porosity: porosity"]  # porosity (n)
		self.fname_theta_r = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Theta residual"]  # Saturated infiltration rate (a-Ks)
		self.fname_theta_AWC = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Available Water content (AWC)"]  # Available water content (AWC)
		self.fname_theta_wp = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Wilting Point (wp)"]  # wilting point (wp)
		self.fname_SoilDepth = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil Depth (D)"]  # root zone (D)
		self.fname_b_SOIL = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil particle distribution parameter (b)"]  # Soil parameter alpha (b)
		self.fname_PSI = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil suction head"]  # Soil parameter alpha (alpha)
		self.fname_Ksat = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Saturated hydraulic conductivity"]  # Saturated infiltration rate (a-Ks)
		self.fname_sigma_ks = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["sigma_Ksat"]

		self.fname_theta = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Initial soil water content"]  # Initial water content [-]

		self.kdt_r = float(factors["MODEL PARAMETERS FACTORS"]["Runoff partition parameter (kdt-Sheeke)"])
		self.kDroot = float(factors["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])  # k for soil depth
		self.kAWC = 1.  # float(factors["MODEL PARAMETERS FACTORS"]["Available Water Content factor - kAWC"])  # k for AWC
		self.kKsat = float(factors["MODEL PARAMETERS FACTORS"]["Infiltration rate factor - kKsat"])  # k for soil infiltration
		self.k_sigma_ks = float(factors["MODEL PARAMETERS FACTORS"]["Heterogeneity factor - k_sigma - (Upscaled GA)"])

class get_list_of_riparian_soil_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		# TODO: Check if statement
		if len(dryp_config["drylandmodel"]) == 94:
			self.fname_riparian_zone = dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["RIPARIAN PROPERTIES"]
		else:
			self.fname_riparian_zone = 'None'

		if os.path.exists(self.fname_riparian_zone):
			frz = pd.read_csv(self.fname_riparian_zone)
			self.fname_n = frz.RIPARIAN[1]		# porosity (n)
			self.fname_theta_r = frz.RIPARIAN[3]	# residual water content
			self.fname_theta_AWC = frz.RIPARIAN[5]		# Available water content (AWC)
			self.fname_theta_wp = frz.RIPARIAN[7]		# wilting point (wp)
			self.fname_SoilDepth = frz.RIPARIAN[9] # riparian root zone depth (D)
			self.fname_b_SOIL = frz.RIPARIAN[11]	# Soil particle distribution (lambda)
			self.fname_PSI = frz.RIPARIAN[13]		# Air-entry pressure/suction head (psi)
			self.fname_Ksat = frz.RIPARIAN[15]  # Channel Sat. hydraulic conductivity (Ksat)
			self.fname_sigma_ks = frz.RIPARIAN[17] # riparian sigma Ksat
			# filename of initial conditions
			self.fname_theta = frz.RIPARIAN[19]	# Initial water content [-]
			# filename riparian channel width
			self.fname_ripwidth = frz.RIPARIAN[21]	# Initial water content [-]
		else:
			self.fname_n = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil porosity: porosity"]  # riparian porosity (n)
			self.fname_theta_r = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Theta residual"]  # riparian Saturated infiltration rate (a-Ks)
			self.fname_theta_AWC = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Available Water content (AWC)"]  # riparian Available water content (AWC)
			self.fname_theta_wp = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Wilting Point (wp)"]  # riparian wilting point (wp)
			self.fname_SoilDepth = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil Depth (D)"]  # riparian root zone (D)
			self.fname_b_SOIL = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil particle distribution parameter (b)"]  # riparian Soil parameter alpha (b)
			self.fname_PSI = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Soil suction head"]  # riparian Soil parameter alpha (alpha)
			self.fname_sigma_ks = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["sigma_Ksat"]  # riparian sigma Ksat
			self.fname_theta = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Initial soil water content"]  # riparian Initial water content [-]
			self.fname_Ksat = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Channel saturated hydraulic conductivity"]  # riparian Channel Saturated hydraulic conductivity (Ks)
			if self.fname_Ksat is None:
				self.fname_Ksat = dryp_config["SOIL AND SUBSURFACE PARAMETERS"]["Saturated hydraulic conductivity"]
			self.fname_ripwidth = "none"

		self.kDroot = float(factors["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])  # k for soil depth
		self.kAWC = 1.  # float(factors["MODEL PARAMETERS FACTORS"]["Available Water Content factor - kAWC"])  # k for AWC
		self.k_sigma_ks = float(factors["MODEL PARAMETERS FACTORS"]["Heterogeneity factor - k_sigma - (Upscaled GA)"])
		self.kKsat = float(factors["MODEL PARAMETERS FACTORS"]["Transmission losses - Kch (m/h)"])  # infiltration on channel
				
class get_list_of_groundwater_files(object):
	"""get list of file names for reading parameters"""

	def __init__(self, dryp_config, factors):
		"""Model parameter settings and input file names and location"""
		
		aux_run_GW = factors["MODEL COMPONENTS"]["Run Groundwater-Enable Type: 0-Unc 1-func 2-Con"].split()    
		self.run_GW = int(aux_run_GW[0])
		
		self.fname_GWdomain = dryp_config["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Groundwater Boundary condition (domain)"]  # GW Boundary conditions
		self.fname_SZ_Ksat = dryp_config["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Aquifer Sat. Hydraulic Conductivity (Ksat_aq)"]  # Saturated hydraulic conductivity (Ks)
		self.fname_SZ_Sy = dryp_config["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Specific Yield"]  # Specific yield
		self.fname_FHB = dryp_config["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Flux Boundary Conditions"]  # flux head boundary
		self.fname_CHB = dryp_config["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Head Boundary Conditions"]  # Constant flux boundary
		self.fname_SZ_bot = dryp_config["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Aquifer bottom elevation"]  # Aquifer bottom elevation
		
		self.fname_thickness = 'None'
		self.fname_b_aq = 'None'
		self.fname_aquifertype = 'None'
		self.fname_bathymetry = 'None'

		if os.path.exists(dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"]):
			fgw = pd.read_csv(dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"])
			self.fname_thickness = fgw.GROUNDWATER[1]
			self.fname_b_aq = fgw.GROUNDWATER[3]
			self.fname_aquifertype = fgw.GROUNDWATER[16] # Constant flux boundary
			self.fname_bathymetry = fgw.GROUNDWATER[18] # Constant flux boundary
		
		self.fname_SZ_botb = 'None'
		self.fname_SZ_Ksatb = 'None'
		self.fname_SZ_Syb = 'None'
		self.fname_SZ_Ssb = 'None'
		self.fname_GWinib = 'None'
		self.fname_mask_of = 'None'
		
		if self.run_GW > 0:
			if os.path.exists(dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"]):
				fgw = pd.read_csv(dryp_config["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"])
				self.fname_thickness = fgw.GROUNDWATER[1]
				self.fname_b_aq = fgw.GROUNDWATER[3]
				self.fname_aquifertype = fgw.GROUNDWATER[16] # Constant flux boundary
				self.fname_bathymetry = fgw.GROUNDWATER[18] # Constant flux boundary


		self.fname_GWini = dryp_config["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Initial Conditions Water table elevation"] 	# Initial water table
		self.fname_DEM = dryp_config["TERRAIN COMPONENTS"]["Topography (DEM)"]
		
		self.kKsat = float(factors["MODEL PARAMETERS FACTORS"]["Infiltration rate factor - kKsat"])  # k for hydraulic conductivity
		self.kSy = float(factors["MODEL PARAMETERS FACTORS"]["Heterogeneity factor - k_sigma - (Upscaled GA)"])  # k for specific yield

#def get_store_variables(fname):
	"""This function read a file of boolean values indicating the variables to be
	save as grid and csv file
	Parameters
	fname: dryp_config of the paramter setting file
	Returns
	store_var: python object containing dictionaries to with boolean values
	"""

	