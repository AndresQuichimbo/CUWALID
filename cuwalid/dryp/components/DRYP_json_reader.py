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
		with open(filename_inputs, 'r') as f:
			filename = json.load(f)
		
		self.Mname = filename["drylandmodel"]["Model name"]

		#==================================================================        
		# MODEL PARAMETERS SETTINGS
		filename_simpar = filename["RESULTS AND OUTPUT DIRECTORIES"]["MODEL PARAMETER SETTINGS FILE"]
		
		with open(filename_simpar, 'r') as f:
			fsimpar = json.load(f)
		
		self.ini_date = datetime.strptime(fsimpar["DWAPM_SET"]["SIMULATION PERIOD AND TIME STEP"]["Initial date for simulation 1 (YYYY MM DD)"], '%Y %m %d')
		self.end_date = datetime.strptime(fsimpar["DWAPM_SET"]["SIMULATION PERIOD AND TIME STEP"]["Initial date for simulation 2 (YYYY MM DD)"], '%Y %m %d')
		self.dtOF = int(fsimpar["DWAPM_SET"]["SIMULATION PERIOD AND TIME STEP"]["OF Time step - dt_Pre (min)"])
		self.dtUZ = int(fsimpar["DWAPM_SET"]["SIMULATION PERIOD AND TIME STEP"]["GW Time step"])
		self.dtSZ = int(fsimpar["DWAPM_SET"]["SIMULATION PERIOD AND TIME STEP"]["GW Time step"])  # Assuming the same value

		netcdf_opt = fsimpar["DWAPM_SET"]["READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX"]["Read datasets: 0-csv 1-One-netCDF 2-Multi-netCDF"].split()
		time_step = fsimpar["DWAPM_SET"]["READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX"]["Dataset time step (minutes)"].split()
		reproj_opt = fsimpar["DWAPM_SET"]["READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX"]["Reproject datasets: 0- disable 1- enable"].split()
		interp_opt = fsimpar["DWAPM_SET"]["READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX"]["Interpolate datasets: 0- disable 1- enable"].split()
					
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
						
		self.inf_method = bool(fsimpar["DWAPM_SET"]["MODEL COMPONENTS"]["Inf."])
		
		if self.inf_method > 3:
			self.inf_method = 0
		
		# read groundwater model activation
		aux_run_GW = fsimpar["DWAPM_SET"]["MODEL COMPONENTS"]["Run Groundwater-Enable Type: 0-Unc 1-func 2-Con"].split()
		self.run_GW = int(aux_run_GW[0])
		
		# groundwater aquifer functions
		if len(aux_run_GW) > 1:
			self.gw_func = int(aux_run_GW[1])
		else:
			self.gw_func = 0
		
		# save netcdf files of model results
		self.save_netcdf = False
		if int(fsimpar["DWAPM_SET"]["OUTPUT OPTIONS"]["Save state results in netcf files"]) > 0:
			self.save_netcdf = True
		
		# save results
		self.save_results = True
		
		# activate lakes
		self.lakes = int(fsimpar["DWAPM_SET"]["OUTPUT OPTIONS"]["not used 1"])
		
		# temporal aggregation of model outputs
		self.dt_results = fsimpar["DWAPM_SET"]["OUTPUT OPTIONS"]["Temporal aggregation results (eg. 3M Y H)"]
		
		# save discharge units
		self.save_dis_depth = int(fsimpar["DWAPM_SET"]["OUTPUT OPTIONS"]["Save discharge in volumetric rate units"])
		
		if len(fsimpar["DWAPM_SET"]) >= 66:
			self.kFlux = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Flux boundary condition factor"])
		else:
			self.kFlux = 1
		
		if len(fsimpar["DWAPM_SET"]) >= 68:
			self.GW_Cond_factor = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Aquifer specific yield factor"])
		else:
			self.GW_Cond_factor = 50
		
		# Unsaturated zone factors
		self.kdt_r = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Runoff partition parameter (kdt-Sheeke)"])
		self.kDroot = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])
		self.kAWC = 1.0
		self.kKsat = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Infiltration rate factor - kKsat"])
		self.k_sigma_ks = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Heterogeneity factor - k_sigma - (Upscaled GA)"])
		
		# River routing factors
		self.kKch = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Transmission losses - Kch (m/h)"])
		self.kTch = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Decay discharge - T - (hours)"])
		self.kpe = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Channel width parameter (pe-not activated)"])
		
		# Saturated zone factors
		self.kKsat_gw = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Aquifer saturated hydraulic conductivity"])
		self.kSy_gw = float(fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Aquifer specific yield factor"])
		
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
		fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Infiltration rate factor - kKsat"] = self.kKsat * self.unit_sim_k
		fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Transmission losses - Kch (m/h)"] = self.kKch * self.unit_sim_k
		fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Decay discharge - T - (hours)"] = self.kT_units * 3600.0 * self.kTch
		fsimpar["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Aquifer saturated hydraulic conductivity"] = self.kKsat_gw * self.unit_sim_k
		
		# Get list of files required to parameterize the model
		self.fname_surface = get_list_of_surface_files(filename, fsimpar)
		self.fname_soil = get_list_of_soil_files(filename, fsimpar)
		self.fname_riparian = get_list_of_riparian_soil_files(filename, fsimpar)
		self.fname_aquifer = get_list_of_groundwater_files(filename, fsimpar)
		self.fname_interception_hillslope = get_list_of_interception_hillslope_files(filename, fsimpar)
		self.fname_interception_riparian = get_list_of_interception_riparian_files(filename, fsimpar)
		
		#==================================================================
		# Meterological data
		self.fname_TSPre = filename["METEOROLOGICAL DATA"]["Precipitation"]
		self.fname_TSMeteo = filename["METEOROLOGICAL DATA"]["Potential Evapotranspiration"]
		self.fname_TSABC = filename["METEOROLOGICAL DATA"]["Water abstractions file"]
		
		# READ DATASETS PROJECTION
		self.fname_proj = None
		self.proj_model = None
		self.proj_data = None
		
        # TODO: Check this if statement
		if len(filename["drylandmodel"]) == 98:
			self.fname_proj = filename["RESULTS AND OUTPUT DIRECTORIES"]["DATASET PROJECTIONS AND COORDINANTES"]
			if os.path.exists(self.fname_proj):
				with open(self.fname_proj, 'r') as f:
					dfproj = json.load(f)
					self.proj_model = dfproj["PROJECTION"][1]
					self.proj_data = dfproj["PROJECTION"][4]
			else:
				print("Projection system not provided")
		
		self.fname_store = 'None'
		if len(filename["drylandmodel"]) == 100:
			self.fname_store = filename["drylandmodel"][99]
		self.store = get_store_parameters(self.fname_store)
		
		# Vegetation parameters
		self.fname_TSKc = filename["SURFACE COMPONENTS"]["Vegetation type Kc"]
		self.fname_Rip_width = filename["SURFACE COMPONENTS"]["Soil land use"]
		self.fname_Rip_init = filename["SURFACE COMPONENTS"]["Other"]
		
		# Output files maps
		self.DirOutput = filename["RESULTS AND OUTPUT DIRECTORIES"]["Folder location results"]
		self.fname_DISpoints = filename["RESULTS AND OUTPUT DIRECTORIES"]["Discharge point results"]
		self.fname_SMDpoints = filename["RESULTS AND OUTPUT DIRECTORIES"]["Soil point results output"]
		self.fname_GWpoints = filename["RESULTS AND OUTPUT DIRECTORIES"]["Groundwater point results"]
		
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

    def __init__(self, filename, factors):
        """Model parameter settings and input file names and location"""
        self.fname_interception = filename["RESULTS AND OUTPUT DIRECTORIES"]["INTERCEPTION MODEL"]
        if os.path.exists(self.fname_interception):
            with open(self.fname_interception, 'r') as f:
                fcp = json.load(f)
                # Soil component
                self.fname_av = fcp["INTERCEPTION"][1]
                self.fname_savi = fcp["INTERCEPTION"][3]
                self.fname_laia = fcp["INTERCEPTION"][5]
                self.fname_laib = fcp["INTERCEPTION"][7]
                self.fname_savi_min = fcp["INTERCEPTION"][9]
                self.fname_savi_max = fcp["INTERCEPTION"][11]
                self.fname_lai = fcp["INTERCEPTION"][13]
                self.fname_tap_depth = fcp["INTERCEPTION"][27]
                self.fname_extintion_depth = fcp["INTERCEPTION"][29]
                # filename of initial conditions
                self.fname_fcw_canopy = fcp["INTERCEPTION"][31]
                self.fname_Sc0_canopy = fcp["INTERCEPTION"][33]
        else:
            # Default values
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

        self.fname_SoilDepth = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil Depth (D)"]  # root zone (D)
        self.kDroot = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])  # k for soil depth

class get_list_of_interception_riparian_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, filename, factors):
        """Model parameter settings and input file names and location"""
        self.fname_interception = filename["RESULTS AND OUTPUT DIRECTORIES"]["INTERCEPTION MODEL"]
        if os.path.exists(self.fname_interception):
            with open(self.fname_interception, 'r') as f:
                fcp = json.load(f)
                # Riparian component
                self.fname_av = fcp["INTERCEPTION"][15]
                self.fname_savi = fcp["INTERCEPTION"][15]
                self.fname_laia = fcp["INTERCEPTION"][17]
                self.fname_laib = fcp["INTERCEPTION"][19]
                self.fname_savi_min = fcp["INTERCEPTION"][21]
                self.fname_savi_max = fcp["INTERCEPTION"][23]
                self.fname_lai = fcp["INTERCEPTION"][25]
                self.fname_tap_depth = fcp["INTERCEPTION"][27]
                self.fname_extintion_depth = fcp["INTERCEPTION"][29]
                # filename of initial conditions
                self.fname_fcw_canopy = fcp["INTERCEPTION"][31]
                self.fname_Sc0_canopy = fcp["INTERCEPTION"][33]
        else:
            # Default values
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
        self.fname_SoilDepth = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil Depth (D)"]  # root zone (D)
        self.kDroot = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])  # k for soil depth

class get_list_of_surface_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, filename, factors):
        """Model parameter settings and input file names and location"""
        self.fname_DEM = filename["TERRAIN COMPONENTS"]["Topography (DEM)"]
        self.fname_Qo = filename["TERRAIN COMPONENTS"]["Cell factor area"]
        self.fname_FlowDir = filename["TERRAIN COMPONENTS"]["Flow Direction (fd)"]
        self.fname_kTchannel = filename["TERRAIN COMPONENTS"]["River decay parameters"]
        self.fname_Mask = filename["TERRAIN COMPONENTS"]["Basin Mask (catchment)"]
        self.fname_River = filename["TERRAIN COMPONENTS"]["River length"]
        self.fname_RiverWidth = filename["TERRAIN COMPONENTS"]["River width"]
        self.fname_RiverElev = filename["TERRAIN COMPONENTS"]["River bottom elevation"]
        self.fname_Ksat = filename["SOIL AND SUBSURFACE PARAMETERS"]["Channel saturated hydraulic conductivity"]
        if self.fname_Ksat is None:
            self.fname_Ksat = filename["SOIL AND SUBSURFACE PARAMETERS"]["Saturated hydraulic conductivity"]
        self.fname_Q_ini = filename["SOIL AND SUBSURFACE PARAMETERS"]["Channel saturated hydraulic conductivity"]

        # TODO: Check this if statement
        if len(filename["drylandmodel"]) == 96:
            self.fname_bc = filename["RESULTS AND OUTPUT DIRECTORIES"]["BOUNDARY CONDITIONS OF"]
        else:
            self.fname_bc = 'None'
        
        self.fname_TSOF = 'None'
        self.filename_OF_points = 'None'
        
        if os.path.exists(self.fname_bc):
            with open(self.fname_bc, 'r') as f:
                fbc = json.load(f)
                self.fname_TSOF = fbc["OFBC"][1]
                self.filename_OF_points = fbc["OFBC"][3]
        
        self.fname_bathymetry = 'None'
        if os.path.exists(filename["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"]):
            with open(filename["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"], 'r') as f:
                fgw = json.load(f)
                self.fname_bathymetry = fgw["GROUNDWATER"][18]  # Constant flux boundary

        # TODO: Check this if statement
        if len(filename["drylandmodel"]) == 94:
            self.fname_riparian_zone = filename["RESULTS AND OUTPUT DIRECTORIES"]["RIPARIAN PROPERTIES"]
        else:
            self.fname_riparian_zone = 'none'
        
        self.fname_ripwidth = "none"
        if os.path.exists(self.fname_riparian_zone):
            with open(self.fname_riparian_zone, 'r') as f:
                frz = json.load(f)
                self.fname_ripwidth = frz["RIPARIAN"][21]  # riparian width [-]

        self.kKch = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Transmission losses - Kch (m/h)"])  # infiltration on channel
        self.kTch = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Decay discharge - T - (hours)"])  # Runoff decay flow factor

class get_list_of_soil_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, filename, factors):
        """Model parameter settings and input file names and location"""
        self.fname_n = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil porosity: porosity"]  # porosity (n)
        self.fname_theta_r = filename["SOIL AND SUBSURFACE PARAMETERS"]["Theta residual"]  # Saturated infiltration rate (a-Ks)
        self.fname_theta_AWC = filename["SOIL AND SUBSURFACE PARAMETERS"]["Available Water content (AWC)"]  # Available water content (AWC)
        self.fname_theta_wp = filename["SOIL AND SUBSURFACE PARAMETERS"]["Wilting Point (wp)"]  # wilting point (wp)
        self.fname_SoilDepth = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil Depth (D)"]  # root zone (D)
        self.fname_b_SOIL = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil particle distribution parameter (b)"]  # Soil parameter alpha (b)
        self.fname_PSI = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil suction head"]  # Soil parameter alpha (alpha)
        self.fname_Ksat = filename["SOIL AND SUBSURFACE PARAMETERS"]["Saturated hydraulic conductivity"]  # Saturated infiltration rate (a-Ks)
        self.fname_sigma_ks = filename["SOIL AND SUBSURFACE PARAMETERS"]["sigma_Ksat"]

        self.fname_theta = filename["SOIL AND SUBSURFACE PARAMETERS"]["Initial soil water content"]  # Initial water content [-]

        self.kdt_r = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Runoff partition parameter (kdt-Sheeke)"])
        self.kDroot = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])  # k for soil depth
        self.kAWC = 1.  # float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Available Water Content factor - kAWC"])  # k for AWC
        self.kKsat = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Infiltration rate factor - kKsat"])  # k for soil infiltration
        self.k_sigma_ks = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Heterogeneity factor - k_sigma - (Upscaled GA)"])

class get_list_of_riparian_soil_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, filename, factors):
        """Model parameter settings and input file names and location"""
        # TODO: Check if statement
        if len(filename["drylandmodel"]) == 94:
            self.fname_riparian_zone = filename["RESULTS AND OUTPUT DIRECTORIES"]["RIPARIAN PROPERTIES"]
        else:
            self.fname_riparian_zone = 'None'

        if os.path.exists(self.fname_riparian_zone):
            with open(self.fname_riparian_zone, 'r') as f:
                frz = json.load(f)
                self.fname_n = frz["RIPARIAN"][1]  # porosity (n)
                self.fname_theta_r = frz["RIPARIAN"][3]  # residual water content
                self.fname_theta_AWC = frz["RIPARIAN"][5]  # Available water content (AWC)
                self.fname_theta_wp = frz["RIPARIAN"][7]  # wilting point (wp)
                self.fname_SoilDepth = frz["RIPARIAN"][9]  # riparian root zone depth (D)
                self.fname_b_SOIL = frz["RIPARIAN"][11]  # Soil particle distribution (lambda)
                self.fname_PSI = frz["RIPARIAN"][13]  # Air-entry pressure/suction head (psi)
                self.fname_Ksat = frz["RIPARIAN"][15]  # Channel Sat. hydraulic conductivity (Ksat)
                self.fname_sigma_ks = frz["RIPARIAN"][17]  # riparian sigma Ksat
                self.fname_theta = frz["RIPARIAN"][19]  # Initial water content [-]
                self.fname_ripwidth = frz["RIPARIAN"][21]  # riparian width [-]
        else:
            self.fname_n = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil porosity: porosity"]  # riparian porosity (n)
            self.fname_theta_r = filename["SOIL AND SUBSURFACE PARAMETERS"]["Theta residual"]  # riparian Saturated infiltration rate (a-Ks)
            self.fname_theta_AWC = filename["SOIL AND SUBSURFACE PARAMETERS"]["Available Water content (AWC)"]  # riparian Available water content (AWC)
            self.fname_theta_wp = filename["SOIL AND SUBSURFACE PARAMETERS"]["Wilting Point (wp)"]  # riparian wilting point (wp)
            self.fname_SoilDepth = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil Depth (D)"]  # riparian root zone (D)
            self.fname_b_SOIL = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil particle distribution parameter (b)"]  # riparian Soil parameter alpha (b)
            self.fname_PSI = filename["SOIL AND SUBSURFACE PARAMETERS"]["Soil suction head"]  # riparian Soil parameter alpha (alpha)
            self.fname_sigma_ks = filename["SOIL AND SUBSURFACE PARAMETERS"]["sigma_Ksat"]  # riparian sigma Ksat
            self.fname_theta = filename["SOIL AND SUBSURFACE PARAMETERS"]["Initial soil water content"]  # riparian Initial water content [-]
            self.fname_Ksat = filename["SOIL AND SUBSURFACE PARAMETERS"]["Channel saturated hydraulic conductivity"]  # riparian Channel Saturated hydraulic conductivity (Ks)
            if self.fname_Ksat is None:
                self.fname_Ksat = filename["SOIL AND SUBSURFACE PARAMETERS"]["Saturated hydraulic conductivity"]
            self.fname_ripwidth = "none"

        self.kDroot = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Soil Depth factor - kDroot (mm)"])  # k for soil depth
        self.kAWC = 1.  # float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Available Water Content factor - kAWC"])  # k for AWC
        self.k_sigma_ks = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Heterogeneity factor - k_sigma - (Upscaled GA)"])
        self.kKsat = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Transmission losses - Kch (m/h)"])  # infiltration on channel
				
class get_list_of_groundwater_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, filename, factors):
        """Model parameter settings and input file names and location"""
        
        aux_run_GW = factors["DWAPM_SET"]["MODEL COMPONENTS"]["Run Groundwater-Enable Type: 0-Unc 1-func 2-Con"].split()    
        self.run_GW = int(aux_run_GW[0])
        
        self.fname_GWdomain = filename["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Groundwater Boundary condition (domain)"]  # GW Boundary conditions
        self.fname_SZ_Ksat = filename["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Aquifer Sat. Hydraulic Conductivity (Ksat_aq)"]  # Saturated hydraulic conductivity (Ks)
        self.fname_SZ_Sy = filename["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Specific Yield"]  # Specific yield
        self.fname_FHB = filename["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Flux Boundary Conditions"]  # flux head boundary
        self.fname_CHB = filename["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Head Boundary Conditions"]  # Constant flux boundary
        self.fname_SZ_bot = filename["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Aquifer bottom elevation"]  # Aquifer bottom elevation
        
        self.fname_thickness = 'None'
        self.fname_b_aq = 'None'
        self.fname_aquifertype = 'None'
        self.fname_bathymetry = 'None'

        if os.path.exists(filename["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"]):
            with open(filename["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"], 'r') as f:
                fgw = json.load(f)
                self.fname_thickness = fgw["GROUNDWATER"][1]
                self.fname_b_aq = fgw["GROUNDWATER"][3]
                self.fname_aquifertype = fgw["GROUNDWATER"][16]  # Constant flux boundary
                self.fname_bathymetry = fgw["GROUNDWATER"][18]  # Constant flux boundary
        
        self.fname_SZ_botb = 'None'
        self.fname_SZ_Ksatb = 'None'
        self.fname_SZ_Syb = 'None'
        self.fname_SZ_Ssb = 'None'
        self.fname_GWinib = 'None'
        self.fname_mask_of = 'None'
        
        if self.run_GW > 0:
            if os.path.exists(filename["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"]):
                with open(filename["RESULTS AND OUTPUT DIRECTORIES"]["GROUNDWATER ADITIONAL PARAMETER FILES"], 'r') as f:
                    fgw = json.load(f)
                    self.fname_SZ_botb = fgw["GROUNDWATER"][6]  # Aquifer bottom elevation
                    self.fname_SZ_Ksatb = fgw["GROUNDWATER"][8]  # Saturated hydraulic conductivity (Ks)
                    self.fname_SZ_Syb = fgw["GROUNDWATER"][10]  # Specific yield
                    self.fname_SZ_Ssb = fgw["GROUNDWATER"][12]  # Specific yield
                    self.fname_GWinib = fgw["GROUNDWATER"][14]  # Initial water table
                    self.fname_mask_of = fgw["GROUNDWATER"][16]  # Constant flux boundary
                    self.fname_thickness = fgw["GROUNDWATER"][18]


        self.fname_GWini = filename["GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS"]["Initial Conditions Water table elevation"] 	# Initial water table
        self.fname_DEM = filename["TERRAIN COMPONENTS"]["Topography (DEM)"]
        
        self.kKsat = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Infiltration rate factor - kKsat"])  # k for hydraulic conductivity
        self.kSy = float(factors["DWAPM_SET"]["MODEL PARAMETERS FACTORS"]["Heterogeneity factor - k_sigma - (Upscaled GA)"])  # k for specific yield

#def get_store_variables(fname):
    """This function read a file of boolean values indicating the variables to be
	save as grid and csv file
	Parameters
	fname: filename of the paramter setting file
	Returns
	store_var: python object containing dictionaries to with boolean values
	"""

	