import os
from datetime import datetime
import json
import sys
import numpy as np
import pandas as pd
from cuwalid.dryp.components.DRYP_store_parameters import get_store_parameters
from cuwalid.dryp.components.DRYP_default_parameters import default_input
from cuwalid.dryp.components.DRYP_default_settings import default_settings

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

		print()
		print("reading config file...")
		print()
		clean_input(default_input, dryp_config)
		dryp_config = default_input
		
		self.Mname = dryp_config["model_name"]
		  
		#==================================================================        
		# MODEL PARAMETERS SETTINGS		

		filename_simpar = dryp_config["OUTPUT"]["path_setting"]
		
		with open(filename_simpar, 'r') as f:
			settings_config = json.load(f)
		
		print()
		print("Reading settings file...")
		print()
		clean_input(default_settings, settings_config)
		settings_config = default_settings

		
		self.ini_date = datetime.strptime(settings_config["SIMULATION_PERIOD"]["start_date"], '%Y %m %d')
		self.end_date = datetime.strptime(settings_config["SIMULATION_PERIOD"]["end_date"], '%Y %m %d')
		self.dtOF = int(settings_config["TIMESTEP_SETTINGS"]["dt_of"])
		self.dtUZ = int(settings_config["TIMESTEP_SETTINGS"]["dt_gw"])
		self.dtSZ = int(settings_config["TIMESTEP_SETTINGS"]["dt_gw"])  # Assuming the same value

		self.data_reading = settings_config["READING"]["data_reading"]
		self.data_step = settings_config["READING"]["data_step"]
		self.data_reproject = settings_config["READING"]["data_reproject"]
		self.data_interpolate = settings_config["READING"]["data_interp"]
		self.data_projection = settings_config["READING"]["data_projection"]
		self.PROJECTION = settings_config["PROJECTION"]

		self.inf_method = bool(settings_config["COMPONENTS"]["method_inf"])

		if self.inf_method > 3:
			self.inf_method = 0

		# Read groundwater model activation
		#aux_run_GW = settings_config["COMPONENTS"]["method_gw"].split()
		self.run_GW = bool(settings_config["COMPONENTS"]["run_gw"])
		#self.run_GW = int(aux_run_GW[0])

		# Groundwater aquifer functions
		self.gw_func = int(settings_config["COMPONENTS"]["method_gw"])

		# Save netcdf files of model results
		self.save_netcdf = bool(settings_config["OUTPUT"]["output_grid"])

		# Save results
		self.save_results = True

		# Temporal aggregation of model outputs
		self.dt_results = settings_config["OUTPUT"]["output_dt"]
		self.dt_results_csv = settings_config["OUTPUT"]["output_dt_csv"]

		# Save discharge units
		#self.save_dis_depth = settings_config["OUTPUT"]["Save discharge in volumetric rate units"]

		self.kFlux = float(settings_config["GLOBAL_FACTORS"]["of_kflow"] or 1)
		self.GW_Cond_factor = float(settings_config["GLOBAL_FACTORS"]["sz_ksy"] or 50)

		# Unsaturated zone factors
		self.kdt_r = float(settings_config["GLOBAL_FACTORS"]["uz_kdt"])
		self.kDroot = float(settings_config["GLOBAL_FACTORS"]["uz_kdroot"])
		self.kAWC = 1.0
		self.kKsat = float(settings_config["GLOBAL_FACTORS"]["uz_kkast"])
		self.k_sigma_ks = float(settings_config["GLOBAL_FACTORS"]["uz_ksigma"])

		# River routing factors
		self.kKch = float(settings_config["GLOBAL_FACTORS"]["riv_kksat"])
		self.kTch = float(settings_config["GLOBAL_FACTORS"]["riv_kdecay"])
		self.kpe = float(settings_config["GLOBAL_FACTORS"]["riv_kwidth"])

		# Saturated zone factors
		self.kKsat_gw = float(settings_config["GLOBAL_FACTORS"]["sz_kksat"])
		self.kSy_gw = float(settings_config["GLOBAL_FACTORS"]["sz_ksy"])

		# Read model time step conditions
		# specified simulation time step
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

		# set sore time step
		self.nstep_day = 1440/self.dt
		
		# specify if maximum values are stored
		self.store_max = False
		if self.nstep_day <= 24:
			self.store_max = True		

		# set up units
		self.unit_change_manning = (1 / (self.dt * 60)) ** (3 / 5)
		self.Agg_method = str(self.dt) + 'T'
		self.river_banks = 100.0
		self.run_FAc = 1
		self.dt_OF = 1
		self.ndays = (self.end_date - self.ini_date).days

		# Update final parameters
		settings_config["GLOBAL_FACTORS"]["uz_kkast"] = self.kKsat * self.unit_sim_k
		settings_config["GLOBAL_FACTORS"]["riv_kksat"] = self.kKch * self.unit_sim_k
		settings_config["GLOBAL_FACTORS"]["riv_kdecay"] = self.kT_units * 3600.0 * self.kTch
		settings_config["GLOBAL_FACTORS"]["sz_kksat"] = self.kKsat_gw * self.unit_sim_k

		# Get list of files required to parameterize the model
		self.fname_surface = get_list_of_surface_files(dryp_config, settings_config)
		self.fname_soil = get_list_of_soil_files(dryp_config, settings_config)
		self.fname_riparian = get_list_of_riparian_soil_files(dryp_config, settings_config)
		self.fname_aquifer = get_list_of_groundwater_files(dryp_config, settings_config)
		self.fname_interception_hillslope = get_list_of_interception_hillslope_files(dryp_config, settings_config)
		self.fname_interception_riparian = get_list_of_interception_riparian_files(dryp_config, settings_config)
		self.fname_water_bodies = get_list_of_water_bodies_files(dryp_config, settings_config)

		#==================================================================
		# Meteorological data
		self.fname_TSPre = dryp_config["METEO"]["path_pre"]
		self.fname_TSMeteo = dryp_config["METEO"]["path_pet"]
		self.fname_TSABC = dryp_config["METEO"]["path_aof"]
		self.fname_TSlai = dryp_config["METEO"]["path_lai"]
		self.fname_TSsavi = dryp_config["METEO"]["path_savi"]
		self.fname_TSkc = dryp_config["METEO"]["path_kc"]
		self.fname_TSOF = dryp_config["METEO"]["path_TSOF"]
		self.fname_TSUZ = dryp_config["METEO"]["path_TSUZ"]
		self.fname_TSSZ = dryp_config["METEO"]["path_TSSZ"]
		self.fname_TSav = dryp_config["METEO"]["path_TSav"]
		self.fname_savi_min = None
		self.fname_savi_max = None
		
		# READ DATASETS PROJECTION
		self.fname_proj = None
		self.proj_model = None
		self.proj_data = None

		# read store paramters
		self.fname_store = None
		if len(dryp_config.get("drylandmodel", {})) == 100:
			self.fname_store = dryp_config["drylandmodel"][99]
		self.store = get_store_parameters(self.fname_store)

		# Vegetation parameters
		self.fname_TSKc = dryp_config["VEGETATION"]["path_veg_kc"]
		self.fname_Rip_width = dryp_config["VEGETATION"]["path_veg_lulc"]
		self.fname_Rip_init = dryp_config["VEGETATION"].get("path_veg_nn")

		# Output files maps
		self.DirOutput = dryp_config["OUTPUT"]["path_output"]
		self.fname_DISpoints = dryp_config["OUTPUT"]["path_out_sz"]
		self.fname_SMDpoints = dryp_config["OUTPUT"]["path_out_uz"]
		self.fname_GWpoints = dryp_config["OUTPUT"]["path_out_oz"]

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

        # Soil component
        self.fname_av = dryp_config["INTERCEPTION"]["path_veg_lulc_frac"]
        self.fname_savi = dryp_config["INTERCEPTION"]["path_veg_hs_savi"]
        self.fname_laia = dryp_config["INTERCEPTION"]["path_veg_hs_par_a"]
        self.fname_laib = dryp_config["INTERCEPTION"]["path_veg_hs_par_b"]
        self.fname_savi_min = dryp_config["INTERCEPTION"]["path_veg_hs_savi_min"]
        self.fname_savi_max = dryp_config["INTERCEPTION"]["path_veg_hs_savi_max"]
        self.fname_lai = dryp_config["INTERCEPTION"]["path_veg_hs_lai"]
        self.fname_tap_depth = dryp_config["INTERCEPTION"]["path_veg_hs_tap_depth"]
        self.fname_extintion_depth = dryp_config["INTERCEPTION"]["path_veg_hs_extinction_depth"]
        # filename of initial conditions
        self.fname_fcw_canopy = dryp_config["INTERCEPTION"]["path_veg_rp_fcw"]
        self.fname_Sc0_canopy = dryp_config["INTERCEPTION"]["path_veg_rp_sca"]

        self.fname_SoilDepth = dryp_config["UNSATURATED"]["path_uz_rootdepth"]
        self.kDroot = float(factors["GLOBAL_FACTORS"]["uz_kdroot"])


class get_list_of_interception_riparian_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, dryp_config, factors):
        """Model parameter settings and input file names and location"""

        # Riparian component
        self.fname_av = dryp_config["INTERCEPTION"]["path_veg_hs_savi"]
        self.fname_savi = dryp_config["INTERCEPTION"]["path_veg_hs_savi"]
        # self.fname_kc = fcp.INTERCEPTION[3]
        # self.fname_avc = fcp.INTERCEPTION[5]
        self.fname_laia = dryp_config["INTERCEPTION"]["path_veg_rp_par_a"]
        self.fname_laib = dryp_config["INTERCEPTION"]["path_veg_rp_par_b"]
        self.fname_savi_min = dryp_config["INTERCEPTION"]["path_veg_rp_savi_min"]
        self.fname_savi_max = dryp_config["INTERCEPTION"]["path_veg_rp_savi_max"]
        self.fname_lai = dryp_config["INTERCEPTION"]["path_veg_rp_lai"]
        self.fname_tap_depth = dryp_config["INTERCEPTION"]["path_veg_rp_tap_depth"]
        self.fname_extintion_depth = dryp_config["INTERCEPTION"]["path_veg_rp_extinction_depth"]
        # filename of initial conditions
        self.fname_fcw_canopy = dryp_config["INTERCEPTION"]["path_veg_rp_fcw"]
        self.fname_Sc0_canopy = dryp_config["INTERCEPTION"]["path_veg_rp_sca"]

        self.fname_SoilDepth = dryp_config["UNSATURATED"]["path_uz_rootdepth"]
        self.kDroot = float(factors["GLOBAL_FACTORS"]["uz_kdroot"])


class get_list_of_surface_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, dryp_config, factors):
        """Model parameter settings and input file names and location"""
        self.fname_DEM = dryp_config["TERRAIN"]["path_dem"]
        self.fname_Qo = dryp_config["TERRAIN"]["path_Qo"]
        self.fname_FlowDir = dryp_config["TERRAIN"]["path_fdl"]
        self.fname_kTchannel = dryp_config["TERRAIN"]["path_riv_decay"]
        self.fname_Mask = dryp_config["TERRAIN"]["path_mask"]
        self.fname_River = dryp_config["TERRAIN"]["path_riv_len"]
        self.fname_RiverWidth = dryp_config["TERRAIN"]["path_riv_width"]
        self.fname_RiverElev = dryp_config["TERRAIN"]["path_riv_elev"]
        self.fname_Ksat = dryp_config["UNSATURATED"]["path_riv_ksat"]
        if self.fname_Ksat is None:
            self.fname_Ksat = dryp_config["UNSATURATED"]["path_uz_ksat"]
        self.fname_Q_ini = dryp_config["UNSATURATED"]["path_riv_ksat"]
        
		# read boundary conditions 
        self.fname_of_bc_flux = dryp_config["TERRAIN"]["path_of_bc_flux"]
        
		#if len(dryp_config.get("drylandmodel", {})) == 96:
        #    self.fname_bc = dryp_config["OUTPUT"]["path_of_settings"]
        #else:
        #    self.fname_bc = None

        #self.fname_TSOF = None
        #self.filename_OF_points = None

        #if self.fname_of_bc_flux is not None:# and os.path.exists(self.fname_bc):
        #    fbc = pd.read_csv(self.fname_bc)
        #    #self.fname_TSOF = fbc.OFBC[1]
        #    #self.filename_OF_points = fbc.OFBC[3]

        self.fname_bathymetry = dryp_config["WATER_BODIES"]["path_lake_depth"]
        #self.fname_bathymetry = None
        #if dryp_config["OUTPUT"].get("path_gw_settings") is not None and os.path.exists(dryp_config["OUTPUT"]["path_gw_settings"]):
        #    fgw = pd.read_csv(dryp_config["OUTPUT"]["path_gw_settings"])
        #    self.fname_bathymetry = fgw.GROUNDWATER[18]  # Constant flux boundary

        ## TODO: Check this if statement
        #if len(dryp_config.get("drylandmodel", {})) == 94:
        #    self.fname_riparian_zone = dryp_config["OUTPUT"]["path_rp_settings"]
        #else:
        #    self.fname_riparian_zone = None

        self.fname_ripwidth = None
        #if self.fname_riparian_zone is not None and os.path.exists(self.fname_riparian_zone):
        #    frz = pd.read_csv(self.fname_riparian_zone)
        #    self.fname_ripwidth = frz.RIPARIAN[21]  # riparian width [-]

        self.kKch = float(factors["GLOBAL_FACTORS"]["riv_kksat"])
        self.kTch = float(factors["GLOBAL_FACTORS"]["riv_kdecay"])


class get_list_of_soil_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, dryp_config, factors):
        """Model parameter settings and input file names and location"""
        self.fname_n = dryp_config["UNSATURATED"]["path_uz_theta_sat"]  # porosity (n)
        self.fname_theta_r = dryp_config["UNSATURATED"]["path_uz_theta_res"]  # Saturated infiltration rate (a-Ks)
        self.fname_theta_AWC = dryp_config["UNSATURATED"]["path_uz_theta_awc"]  # Available water content (AWC)
        self.fname_theta_wp = dryp_config["UNSATURATED"]["path_uz_theta_wp"]  # wilting point (wp)
        self.fname_SoilDepth = dryp_config["UNSATURATED"]["path_uz_rootdepth"]  # root zone (D)
        self.fname_b_SOIL = dryp_config["UNSATURATED"]["path_uz_lambda"]  # Soil parameter alpha (b)
        self.fname_PSI = dryp_config["UNSATURATED"]["path_uz_psi"]  # Soil parameter alpha (alpha)
        self.fname_Ksat = dryp_config["UNSATURATED"]["path_uz_ksat"]  # Saturated infiltration rate (a-Ks)
        self.fname_sigma_ks = dryp_config["UNSATURATED"]["path_uz_sigmaksat"]

        self.fname_theta = dryp_config["UNSATURATED"]["path_uz_theta"]  # Initial water content [-]

        self.fname_uz_bc_flux = dryp_config["UNSATURATED"]["path_uz_bc_flux"]
        

        self.kdt_r = float(factors["GLOBAL_FACTORS"]["uz_kdt"])
        self.kDroot = float(factors["GLOBAL_FACTORS"]["uz_kdroot"])  # k for soil depth
        self.kAWC = 1.0  # float(factors["GLOBAL_FACTORS"]["uz_kawc"])  # k for AWC
        self.kKsat = float(factors["GLOBAL_FACTORS"]["uz_kkast"])  # k for soil infiltration
        self.k_sigma_ks = float(factors["GLOBAL_FACTORS"]["uz_ksigma"])


class get_list_of_riparian_soil_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, dryp_config, factors):
        """Model parameter settings and input file names and location"""
        self.fname_riparian_zone = None

        if "RIPARIAN" in dryp_config:
            self.fname_n = dryp_config["RIPARIAN"]["path_rp_theta_sat"]  # porosity (n)
            self.fname_theta_r = dryp_config["RIPARIAN"]["path_rp_theta_res"]  # residual water content
            self.fname_theta_AWC = dryp_config["RIPARIAN"]["path_rp_theta_awc"]  # Available water content (AWC)
            self.fname_theta_wp = dryp_config["RIPARIAN"]["path_rp_theta_wp"]  # wilting point (wp)
            self.fname_SoilDepth = dryp_config["RIPARIAN"]["path_rp_rootdepth"]  # riparian root zone depth (D)
            self.fname_b_SOIL = dryp_config["RIPARIAN"]["path_rp_lambda"]  # Soil particle distribution (lambda)
            self.fname_PSI = dryp_config["RIPARIAN"]["path_rp_psi"]  # Air-entry pressure/suction head (psi)
            self.fname_Ksat = dryp_config["RIPARIAN"]["path_rp_ksat"]  # Channel Sat. hydraulic conductivity (Ksat)
            self.fname_sigma_ks = dryp_config["RIPARIAN"]["path_rp_sigmaksat"]  # riparian sigma Ksat
            # filename of initial conditions
            self.fname_theta = dryp_config["RIPARIAN"]["path_rp_theta"]  # Initial water content [-]
            # filename riparian channel width
            self.fname_ripwidth = dryp_config["RIPARIAN"]["path_rp_width"]  # Initial water content [-]
        else:
            print("RIPARIAN parameters not provided")
            self.fname_n = dryp_config["UNSATURATED"]["path_uz_theta_sat"]  # riparian porosity (n)
            self.fname_theta_r = dryp_config["UNSATURATED"]["path_uz_theta_res"]  # riparian Saturated infiltration rate (a-Ks)
            self.fname_theta_AWC = dryp_config["UNSATURATED"]["path_uz_theta_awc"]  # riparian Available water content (AWC)
            self.fname_theta_wp = dryp_config["UNSATURATED"]["path_uz_theta_wp"]  # riparian wilting point (wp)
            self.fname_SoilDepth = dryp_config["UNSATURATED"]["path_uz_rootdepth"]  # riparian root zone (D)
            self.fname_b_SOIL = dryp_config["UNSATURATED"]["path_uz_lambda"]  # riparian Soil parameter alpha (b)
            self.fname_PSI = dryp_config["UNSATURATED"]["path_uz_psi"]  # riparian Soil parameter alpha (alpha)
            self.fname_sigma_ks = dryp_config["UNSATURATED"]["path_uz_sigmaksat"]  # riparian sigma Ksat
            self.fname_theta = dryp_config["UNSATURATED"]["path_uz_theta"]  # riparian Initial water content [-]
            self.fname_Ksat = dryp_config["UNSATURATED"]["path_riv_ksat"]  # riparian Channel Saturated hydraulic conductivity (Ks)
            if self.fname_Ksat is None:
                self.fname_Ksat = dryp_config["UNSATURATED"]["path_uz_ksat"]
            self.fname_ripwidth = None

        self.kDroot = float(factors["GLOBAL_FACTORS"]["uz_kdroot"])  # k for soil depth
        self.kAWC = float(factors["GLOBAL_FACTORS"]["uz_kawc"])
        self.k_sigma_ks = float(factors["GLOBAL_FACTORS"]["uz_ksigma"])
        self.kKsat = float(factors["GLOBAL_FACTORS"]["riv_kksat"])  # infiltration on channel


class get_list_of_groundwater_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, dryp_config, factors):
        """Model parameter settings and input file names and location"""
        
        #aux_run_GW = factors["COMPONENTS"]["method_gw"].split()
        self.run_GW = bool(factors["COMPONENTS"]["run_gw"])
        
        self.fname_GWdomain = dryp_config["SATURATED"]["path_sz_mask"]  # GW Boundary conditions
        self.fname_SZ_Ksat = dryp_config["SATURATED"]["path_sz_ksat"]  # Saturated hydraulic conductivity (Ks)
        self.fname_SZ_Sy = dryp_config["SATURATED"]["path_sz_sy"]  # Specific yield
        self.fname_FHB = dryp_config["SATURATED"]["path_sz_bc_flux"]  # flux head boundary
        self.fname_CHB = dryp_config["SATURATED"]["path_sz_bc_head"]  # Constant flux boundary
        self.fname_SZ_bot = dryp_config["SATURATED"]["path_sz_bottom"]  # path_sz_bottom
        
        self.fname_thickness = dryp_config["SATURATED"]["path_sz_depth"]
        self.fname_b_aq = dryp_config["SATURATED"]["path_sz_bdd"]
        self.fname_aquifertype = dryp_config["SATURATED"]["path_sz_type"]
        #self.fname_bathymetry = dryp_config["GROUNDWATER"]["path_gw_lake_elev"]
        self.fname_bathymetry = dryp_config["WATER_BODIES"]["path_lake_depth"]

		# read boundary conditions 
        self.fname_sz_bc_flux = dryp_config["SATURATED"]["path_sz_bc_flux"]

        self.fname_SZ_botb = None
        self.fname_SZ_Ksatb = None
        self.fname_SZ_Syb = None
        self.fname_SZ_Ssb = None
        self.fname_GWinib = None
        self.fname_mask_of = None
        
        if self.run_GW > 0:
            self.fname_SZ_botb = dryp_config["GROUNDWATER"]["path_gw_2l_bottom"]
            self.fname_SZ_Ksatb = dryp_config["GROUNDWATER"]["path_gw_2l_ksat"]
            self.fname_SZ_Syb = dryp_config["GROUNDWATER"]["path_gw_2l_sy"]
            self.fname_SZ_Ssb = dryp_config["GROUNDWATER"]["path_gw_2l_ss"]
            self.fname_GWinib = dryp_config["GROUNDWATER"]["path_gw_2l_wte"]
            #self.fname_FHBb = fgw.GROUNDWATER[59]  # flux head boundary
            #self.fname_CHBb = fgw.GROUNDWATER[61]  # Constant flux boundary
            # only for Manny's model
            self.fname_mask_of = dryp_config["SATURATED"]["path_sz_type"]
            #self.fname_lakes_elevation = dryp_config["GROUNDWATER"]["path_gw_lake_elev"]
            self.fname_lakes_elevation = dryp_config["WATER_BODIES"]["path_lake_depth"]

        self.fname_GWini = dryp_config["SATURATED"]["path_sz_wte"]  # Initial water table
        self.fname_DEM = dryp_config["TERRAIN"]["path_dem"]
        
        self.kKsat = float(factors["GLOBAL_FACTORS"]["uz_kkast"])  # k for hydraulic conductivity
        self.kSy = float(factors["GLOBAL_FACTORS"]["uz_ksigma"])  # k for specific yield

class get_list_of_water_bodies_files(object):
    """get list of file names for reading parameters"""

    def __init__(self, dryp_config, factors):
        """Model parameter settings and input file names and location"""

        # water bodies component
        self.fname_bathymetry = dryp_config["WATER_BODIES"]["path_lake_depth"]
        self.fname_pnd_hmax = dryp_config["WATER_BODIES"]["path_pnd_hmax"]
        self.fname_pnd_Amax = dryp_config["WATER_BODIES"]["path_pnd_Amax"]
        self.fname_pnd_Vo = dryp_config["WATER_BODIES"]["path_pnd_Vo"]
		


def clean_input(default_dict, user_input, path="", base_path=None):
	# Check if a 'path_input' is provided, and use it as the base path
	if 'path_input' in user_input:
		base_path = user_input['path_input']

	for key, default_value in default_dict.items():
		full_path = f"{path}.{key}" if path else key
		#print(key)
		# Check if the key exists in user_input
		if key in user_input:
			user_value = user_input[key]
			#print(user_input[key])
			# If the value is a dictionary, recurse into it
			if isinstance(default_value, dict):
				if isinstance(user_value, dict):
					# Recursively update the nested dictionary
					clean_input(default_value, user_value, full_path, base_path)
				else:
					print(f"Warning: '{full_path}' should be a dictionary. Using default.")
			else:
				# If the key starts with 'path_' and user_value is not None, prepend base_path
				if key.startswith("path_") and user_value is not None:
					if base_path and not user_value.startswith(base_path) and key != "path_setting" and key !=  "path_output":
						user_value = os.path.normpath(os.path.join(base_path, user_value))
					default_dict[key] = user_value
				elif user_value is not None:
					default_dict[key] = user_value
				elif user_value is None and default_dict[key] == "required":
					print(f"ERROR: {key} is required but not found in configuration json. Program will terminate.")
					sys.exit(1)
				else:
					print(f"Warning: '{full_path}' set as null. Using default.")
		
		else:
			# If the key is missing in user input
			if default_value == "required":
				raise ValueError(f"Error: '{full_path}' is required but was not provided.")
			else:
				print(f"Warning: '{full_path}' was not provided. Using default.")

	# Check for any extra keys in user_input that aren't in default_dict
	for key in user_input:
		if key not in default_dict:
			print(f"Warning: '{path}.{key}' is not a recognized key and will be ignored.")


"""def get_store_variables(fname):
	This function read a file of boolean values indicating the variables to be
	save as grid and csv file
	Parameters
	fname: dryp_config of the paramter setting file
	Returns
	store_var: python object containing dictionaries to with boolean values
	"""	