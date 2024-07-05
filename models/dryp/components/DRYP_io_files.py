import os
from datetime import datetime
import numpy as np
import pandas as pd
from models.dryp.components.DRYP_store_parameters import get_store_parameters

class get_model_settings(object):
	"""
	"""
	def __init__(self, filename_inputs, first_read=1):
		"""Model paramter settings and input file namens and location
		"""
		self.first_read = first_read
		# =================================================================
		filename = pd.read_csv(filename_inputs)
		self.Mname = filename.drylandmodel[1]
				
		#==================================================================		
		# MODEL PARAMETERS SETTINGS		
		filename_simpar = filename.drylandmodel[87]
		fsimpar = pd.read_csv(filename_simpar)
		
		self.ini_date = datetime.strptime(fsimpar.DWAPM_SET[2], '%Y %m %d')
		self.end_date = datetime.strptime(fsimpar.DWAPM_SET[4], '%Y %m %d')
		self.dtOF = int(fsimpar.DWAPM_SET[6])
		self.dtUZ = int(fsimpar.DWAPM_SET[8])
		self.dtSZ = int(fsimpar.DWAPM_SET[10])
		
		netcdf_opt = fsimpar.DWAPM_SET[13].split()
		time_step = fsimpar.DWAPM_SET[15].split()
		reproj_opt = fsimpar.DWAPM_SET[17].split()
		interp_opt = fsimpar.DWAPM_SET[19].split()
				
		# Datasets format
		self.netcf_pre = int(netcdf_opt[0])
		self.netcf_ETo = int(netcdf_opt[1])
		self.netcf_ABC = int(netcdf_opt[2])
		self.netcf_kc =  int(netcdf_opt[3])
		self.netcf_Flux =int(netcdf_opt[4])
		self.netcf_savi =int(netcdf_opt[5])
		self.netcf_savi_min =int(netcdf_opt[6])
		self.netcf_savi_max =int(netcdf_opt[7])
		
		# Dataset time step
		self.dt_pre = int(time_step[0])
		self.dt_ETo = int(time_step[1])
		self.dt_ABC = int(time_step[2])
		self.dt_kc =  int(time_step[3])
		self.dt_Flux =int(time_step[4])
		self.dt_savi =int(time_step[5])
		self.dt_savi_min = int(time_step[6])
		self.dt_savi_max = int(time_step[7])
		
		# Datasets reprojection
		self.reproject_pre = int(reproj_opt[0])
		self.reproject_ETo = int(reproj_opt[1])
		self.reproject_ABC = int(reproj_opt[2])
		self.reproject_kc =  int(reproj_opt[3])
		self.reproject_Flux =int(reproj_opt[4])
		self.reproject_savi =int(reproj_opt[5])
		self.reproject_savi_min = int(reproj_opt[6])
		self.reproject_savi_max = int(reproj_opt[7])
		
		# Datasets interpolate
		self.interpolate_pre = int(interp_opt[0])
		self.interpolate_ETo = int(interp_opt[1])
		self.interpolate_ABC = int(interp_opt[2])
		self.interpolate_kc =  int(interp_opt[3])
		self.interpolate_Flux =int(interp_opt[4])	
		self.interpolate_savi =int(interp_opt[5])
		self.interpolate_savi_min = int(interp_opt[6])
		self.interpolate_savi_max = int(interp_opt[7])
					
						
		self.inf_method = bool(fsimpar.DWAPM_SET[22])
		
		if self.inf_method > 3:
			self.inf_method = 0
		
		# read groundwater model activation
		aux_run_GW = fsimpar.DWAPM_SET[24].split()	
		self.run_GW = int(aux_run_GW[0])
		# groundwater aquifer funtions
		# 0:	Unconfined
		# 1:	Constant
		# 2:	exponential
		# 3:	multiple functions
		if len(aux_run_GW) > 1:
			self.gw_func = int(aux_run_GW[1])
		else:
			self.gw_func = 0
		
		# save netcdf files of model results
		#self.save_csv = int(fsimpar.DWAPM_SET[31])
		
		# save netcdf files of model results
		self.save_netcdf = False
		if int(fsimpar.DWAPM_SET[33]) > 0:
			self.save_netcdf = True
		
		# save netcdf files of model results
		#self.save_results = int(fsimpar.DWAPM_SET[33])
		self.save_results = True
		
		# activate lakes
		self.lakes = int(fsimpar.DWAPM_SET[43])
		
		# temporal agregation of model outputs
		self.dt_results = fsimpar.DWAPM_SET[35]
		# save discharge units
		# 0: volumetric
		# 1: depth
		self.save_dis_depth = int(fsimpar.DWAPM_SET[39])
		
		if len(fsimpar.DWAPM_SET) == 66:
			self.kFlux = float(fsimpar.DWAPM_SET[66])
		else:
			self.kFlux = 1
			
		if len(fsimpar.DWAPM_SET) == 68:
			self.GW_Cond_factor = float(fsimpar.DWAPM_SET[68])
		else:
			self.GW_Cond_factor = 50
		
		#
		# Unsaturated zone factors =========================================
		self.kdt_r = float(fsimpar.DWAPM_SET[46])
		self.kDroot = float(fsimpar.DWAPM_SET[48])	# k for soil depth
		self.kAWC = 1.#float(fsimpar.DWAPM_SET[50])	# k for AWC
		self.kKsat = float(fsimpar.DWAPM_SET[52])		# k for soil infiltration
		self.k_sigma_ks = float(fsimpar.DWAPM_SET[54])
		
		# River routing factors ============================================
		self.kKch = float(fsimpar.DWAPM_SET[56])	# infiltration on channel
		self.kTch = float(fsimpar.DWAPM_SET[58])	# Runoff decay flow factor
		self.kpe = float(fsimpar.DWAPM_SET[60])
		
		# Saturated zone factors ===========================================
		self.kKsat_gw = float(fsimpar.DWAPM_SET[62])	# Ksat factor
		self.kSy_gw = float(fsimpar.DWAPM_SET[64])		# Sy factor
		
		# Read model time step conditions
		self.dt = np.min([self.dtOF, self.dtUZ, self.dtSZ])
		
		if self.dt > 60:
			self.dt_sub_hourly = 1
			self.dt_hourly = int(1440/self.dt)
			self.unit_sim = self.dt/1440		#change mm/d -> mm/dt
			self.unit_sim_k = self.dt*24/1440	#change mm/h -> mm/dt
			self.kT_units = self.dt/60
		else:
			self.dt_sub_hourly = int(60/self.dt)
			self.dt_hourly = 24
			self.unit_sim = self.dt/60			#change mm/d -> mm/dt
			self.unit_sim_k = self.dt/60		#change mm/h -> mm/dt
			self.kT_units = self.dt/60
		self.unit_change_manning = (1/(self.dt*60))**(3/5)
		self.Agg_method = str(self.dt)+'T'
		#self.kpkKch = 1.0							# initial kKch increase for TL
		#self.T_str_channel = 0.0					# duration of initial kKch increase for TL
		#self.kKch = self.kKch*self.unit_sim_k
		self.river_banks = 100.0 					# Riparian zone with [m]
		self.run_FAc = 1
		self.dt_OF = 1
		self.ndays = (self.end_date - self.ini_date).days
		
		# ipdate final parameters
		# read factore
		#self.kTch = float(fsimpar.DWAPM_SET[58])
		fsimpar.DWAPM_SET[52] = self.kKsat*self.unit_sim_k
		fsimpar.DWAPM_SET[56] = self.kKch*self.unit_sim_k
		fsimpar.DWAPM_SET[58] = self.kT_units*3600.0*self.kTch
		fsimpar.DWAPM_SET[62] = self.kKsat_gw*self.unit_sim_k
		#print(type(fsimpar))
		# get list of files required to parametererisa the model
		# this files can be saved in any python object as long as they
		# keep the same name, this allows the use of DRYP_io component
		self.fname_surface = get_list_of_surface_files(filename, fsimpar)
		self.fname_soil = get_list_of_soil_files(filename, fsimpar)
		self.fname_riparian = get_list_of_riparian_soil_files(filename, fsimpar)
		self.fname_aquifer = get_list_of_groundwater_files(filename, fsimpar)
		self.fname_interception_hillslope = get_list_of_interception_hillslope_files(filename, fsimpar)
		self.fname_interception_riparian = get_list_of_interception_riparian_files(filename, fsimpar)
		
		#==================================================================
		# Meterological data ==============================================
		self.fname_TSPre = filename.drylandmodel[66]	# Precipitation file
		self.fname_TSMeteo = filename.drylandmodel[68]	# Evapotranspiration file
		self.fname_TSABC = filename.drylandmodel[70]	# Abstraction file: AOF, AUZ, ASZ
		#self.fname_savi = filename.drylandmodel[70]
		#self.fname_kc = filename.drylandmodel[72]
		
		# READ DATASETS PROJECTION ==========================================		
		self.fname_proj = None
		self.proj_model = None
		self.proj_data = None
		# check if information of projection is availble
		if len(filename) == 98: # this component needs to be well integrates!!
			self.fname_proj = filename.drylandmodel[97]
			if os.path.exists(self.fname_proj):
				dfproj = pd.read_csv(self.fname_proj)
				self.proj_model = dfproj.PROJECTION[1]
				self.proj_data = dfproj.PROJECTION[4]
			else:
				print("Projection system not provided")
		
		self.fname_store = 'None'
		if len(filename) == 100: # this component needs to be well integrates!!
			self.fname_store = filename.drylandmodel[99]
		self.store = get_store_parameters(self.fname_store)
			#if os.path.exists(self.fname_store):
				#dfproj = pd.read_csv(self.fname_proj)
				#self.proj_model = dfproj.PROJECTION[1]
				#self.proj_data = dfproj.PROJECTION[4]
			#else:
			#	get_store_paramters(self.fname_store)

		# Vegetation parameters ==========================================
		self.fname_TSKc = filename.drylandmodel[21]	# Vegetation parameter Kc
		self.fname_Rip_width = filename.drylandmodel[23]#Available
		self.fname_Rip_init = filename.drylandmodel[25] #Available
		# Output files maps ===================================== Print = 
		self.DirOutput = filename.drylandmodel[81]		# Output directory
		#reading output points
		self.fname_DISpoints = filename.drylandmodel[75]	# Discharge points
		self.fname_SMDpoints = filename.drylandmodel[77]	# Soil moisture points
		self.fname_GWpoints = filename.drylandmodel[79]	# Groundwater observation points
		
		print("Model Name: ", self.Mname)

		# Create directories for saving results
		# Directory *DirOutput* Created
		# Directory *outputcirnetcdf* already exists
		#print('************************************************************')
		print('********************* Output Directory **********************')
		if not os.path.exists(self.DirOutput):
			os.mkdir(self.DirOutput)
			print("Directory ", self.DirOutput, " Created ")
		else:
			print("Directory ", self.DirOutput, " already exists")
				
		# Output filenames
		self.fnameTS_grid = self.DirOutput+'/' + self.Mname + '_grid'
		self.fnameTS_point = self.DirOutput+'/' + self.Mname + '_p_'
		self.fnameTS_UZ  = self.DirOutput+'/' + self.Mname + '_UZ_'
		self.fnameTS_RZ  = self.DirOutput+'/' + self.Mname + '_RZ_'
		self.fnameTS_RZ_avg  = self.DirOutput+'/' + self.Mname + '_RZ_avg'
		self.fnameTS_avg = self.DirOutput+'/' + self.Mname + '_avg'
				

class get_list_of_interception_hillslope_files(object):
	"""get list of file names for reading parameters
		"""

	def __init__(self, filename, factors):
		"""Model paramter settings and input file namens and location
		"""	
		#==================================================================
		# READING MODEL PARAMETER FILES ===================================
		# INTERCEPTION COMPONENT
		self.fname_interception = filename.drylandmodel[91]
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

		self.fname_SoilDepth = filename.drylandmodel[36] # root zone (D)

		# Unsaturated zone factors =========================================
		#self.kdt_r = float(factors.DWAPM_SET[46])
		self.kDroot = float(factors.DWAPM_SET[48])	# k for soil depth

class get_list_of_interception_riparian_files(object):
	"""get list of file names for reading parameters
		"""

	def __init__(self, filename, factors):
		"""Model paramter settings and input file namens and location
		"""
		self.fname_interception = filename.drylandmodel[91]
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
		self.fname_SoilDepth = filename.drylandmodel[36] # root zone (D)
		# Unsaturated zone factors =========================================
		#self.kdt_r = float(factors.DWAPM_SET[46])
		self.kDroot = float(factors.DWAPM_SET[48])	# k for soil depth

class get_list_of_surface_files(object):
	"""get list of file names for reading parameters
	"""

	def __init__(self, filename, factors):
		"""Model paramter settings and input file namens and location
		"""

		# SURFACE COMPONENT ======================================== SZ = 
		self.fname_DEM = filename.drylandmodel[4]
		#self.fname_Area = filename.drylandmodel[6]
		self.fname_Qo = filename.drylandmodel[6]
		self.fname_FlowDir = filename.drylandmodel[8]
		self.fname_kTchannel = filename.drylandmodel[10]
		self.fname_Mask = filename.drylandmodel[12]
		self.fname_River = filename.drylandmodel[14]
		self.fname_RiverWidth = filename.drylandmodel[16]
		self.fname_RiverElev = filename.drylandmodel[18]
		self.fname_Ksat = filename.drylandmodel[48]
		if self.fname_Ksat is None:
			self.fname_Ksat = filename.drylandmodel[42]
		# filename of initial conditions
		self.fname_Q_ini = filename.drylandmodel[48]

		# Boundary conditions ======================================== rz =
		if len(filename) == 96:
			self.fname_bc = filename.drylandmodel[95]
		else:
			self.fname_bc = 'None'
		
		self.fname_TSOF = 'None'
		self.filename_OF_points = 'None'
		
		if os.path.exists(self.fname_bc):
			fbc = pd.read_csv(self.fname_bc)
			self.fname_TSOF = fbc.OFBC[1]
			self.filename_OF_points = fbc.OFBC[3]
		
		self.fname_bathymetry = 'None'#filename.drylandmodel[4]

		if os.path.exists(filename.drylandmodel[89]):
			fgw = pd.read_csv(filename.drylandmodel[89])
			self.fname_bathymetry = fgw.GROUNDWATER[18] # Constant flux boundary

		# riparian width
		if len(filename) == 94:
			self.fname_riparian_zone = filename.drylandmodel[93]
		else:
			self.fname_riparian_zone = 'none'
		
		self.fname_ripwidth = "none"
		if os.path.exists(self.fname_riparian_zone):
			frz = pd.read_csv(self.fname_riparian_zone)
			self.fname_ripwidth = frz.RIPARIAN[21]	# riparian width [-]

		# River routing factors ============================================
		self.kKch = float(factors.DWAPM_SET[56])	# infiltration on channel
		self.kTch = float(factors.DWAPM_SET[58])	# Runoff decay flow factor
		#self.kpe = float(fsimpar.DWAPM_SET[60])
		
		pass

class get_list_of_soil_files(object):
	"""get list of file names for reading parameters
	"""

	def __init__(self, filename, factors):
		"""Model paramter settings and input file namens and location
		"""

		# UNSATURATED COMPONENT ===================================== UZ = 
		self.fname_n = filename.drylandmodel[28]		# porosity (n)
		self.fname_theta_r = filename.drylandmodel[30]	# Saturated infiltration rate (a-Ks)
		self.fname_theta_AWC = filename.drylandmodel[32]		# Available water content (AWC)
		self.fname_theta_wp = filename.drylandmodel[34]		# wilting point (wp)
		self.fname_SoilDepth = filename.drylandmodel[36] # root zone (D)
		self.fname_b_SOIL = filename.drylandmodel[38]	# Soil parameter alpha (b)
		self.fname_PSI = filename.drylandmodel[40]		# Soil parameter alpha (alpha)
		self.fname_Ksat = filename.drylandmodel[42] # Saturated infiltration rate (a-Ks)
		self.fname_sigma_ks = filename.drylandmodel[44]
		
		# filename of inital conditions
		self.fname_theta = filename.drylandmodel[46]	# Initial water content [-]
		
		# Unsaturated zone factors =========================================
		self.kdt_r = float(factors.DWAPM_SET[46])
		self.kDroot = float(factors.DWAPM_SET[48])	# k for soil depth
		self.kAWC = 1.#float(factors.DWAPM_SET[50])	# k for AWC
		self.kKsat = float(factors.DWAPM_SET[52])	# k for soil infiltration
		self.k_sigma_ks = float(factors.DWAPM_SET[54])
		
		pass

class get_list_of_riparian_soil_files(object):
	"""get list of file names for reading parameters
	"""

	def __init__(self, filename, factors):
		"""Model paramter settings and input file namens and location
		"""

		# RIPARIAN COMPONENT ======================================== rz =
		if len(filename) == 94:
			self.fname_riparian_zone = filename.drylandmodel[93]
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
			self.fname_n = filename.drylandmodel[28]		# riparian porosity (n)
			self.fname_theta_r = filename.drylandmodel[30]	# riparian Saturated infiltration rate (a-Ks)
			self.fname_theta_AWC = filename.drylandmodel[32]		# riparian Available water content (AWC)
			self.fname_theta_wp = filename.drylandmodel[34]		# riparian wilting point (wp)
			self.fname_SoilDepth = filename.drylandmodel[36]# riparian root zone (D)
			self.fname_b_SOIL = filename.drylandmodel[38]	# riparian Soil parameter alpha (b)
			self.fname_PSI = filename.drylandmodel[40]		# riparian Soil parameter alpha (alpha)
			self.fname_sigma_ks = filename.drylandmodel[44] # riparian sigma Ksat
			self.fname_theta = filename.drylandmodel[46]	# riparian Initial water content [-]
			self.fname_Ksat = filename.drylandmodel[48]  # riparian Channel Saturated hydraulic conductivity (Ks)
			if self.fname_Ksat is None:
				self.fname_Ksat = filename.drylandmodel[42]
			# filename of inital conditions
			self.fname_theta = filename.drylandmodel[46]	# Initial water content [-]
			self.fname_ripwidth = "none"
		
		# Unsaturated zone factors =========================================
		#self.kdt_r = float(factors.DWAPM_SET[46])
		self.kDroot = float(factors.DWAPM_SET[48])	# k for soil depth
		self.kAWC = 1.#float(fsimpar.DWAPM_SET[50])	# k for AWC
		#self.kKsat = float(factors.DWAPM_SET[52])	# k for soil infiltration
		self.k_sigma_ks = float(factors.DWAPM_SET[54])
		
		# River routing factors ============================================
		self.kKsat = float(factors.DWAPM_SET[56])	# infiltration on channel
		#self.kTch = float(factors.DWAPM_SET[58])	# Runoff decay flow factor
		
				
class get_list_of_groundwater_files(object):
	"""get list of file names for reading parameters
	"""

	def __init__(self, filename, factors):
		"""Model paramter settings and input file namens and location
		"""	
		
		# read groundwater model activation
		aux_run_GW = factors.DWAPM_SET[24].split()	
		self.run_GW = int(aux_run_GW[0])
		
		# Groundwater components ==================================== GW = 
		self.fname_GWdomain = filename.drylandmodel[51]# GW Boundary conditions
		self.fname_SZ_Ksat = filename.drylandmodel[53] # Saturated hydraulic conductivity (Ks)
		self.fname_SZ_Sy = filename.drylandmodel[55] 	# Specific yield
		self.fname_FHB = filename.drylandmodel[59]		# flux head boundary
		self.fname_CHB = filename.drylandmodel[61]		# Constant flux boundary
		self.fname_SZ_bot = filename.drylandmodel[63]	# Aquifer bottom elevation
		
		# additional parameters
		self.fname_thickness = 'None'
		self.fname_b_aq = 'None'
		self.fname_aquifertype = 'None'
		self.fname_bathymetry = 'None'

		if os.path.exists(filename.drylandmodel[89]):
			fgw = pd.read_csv(filename.drylandmodel[89])
			self.fname_thickness = fgw.GROUNDWATER[1]
			self.fname_b_aq = fgw.GROUNDWATER[3]
			self.fname_aquifertype = fgw.GROUNDWATER[16] # Constant flux boundary
			self.fname_bathymetry = fgw.GROUNDWATER[18] # Constant flux boundary
		
		# groundwater second layer ========================================
		self.fname_SZ_botb = 'None'
		self.fname_SZ_Ksatb = 'None'
		self.fname_SZ_Syb = 'None'
		self.fname_SZ_Ssb = 'None'
		self.fname_GWinib = 'None'
		#self.fname_FHBb = 'None'
		#self.fname_CHBb = 'None'
		self.fname_mask_of = 'None'
		
		
		if self.run_GW > 0:
			if os.path.exists(filename.drylandmodel[89]):
				fgw = pd.read_csv(filename.drylandmodel[89])
				#print(fgw.GROUNDWATER)
				self.fname_SZ_botb = fgw.GROUNDWATER[6]	# Aquifer bottom elevation
				self.fname_SZ_Ksatb = fgw.GROUNDWATER[8] # Saturated hydraulic conductivity (Ks)
				self.fname_SZ_Syb = fgw.GROUNDWATER[10] 	# Specific yield
				self.fname_SZ_Ssb = fgw.GROUNDWATER[12] 	# Specific yield
				self.fname_GWinib = fgw.GROUNDWATER[14] 	# Initial water table
				#self.fname_FHBb = fgw.GROUNDWATER[59]		# flux head boundary
				#self.fname_CHBb = fgw.GROUNDWATER[61]		# Constant flux boundary
				# only for Manny's model
				self.fname_mask_of = fgw.GROUNDWATER[16]	# Constant flux boundary
				self.fname_lakes_elevation = fgw.GROUNDWATER[18]
		#print(self.fname_lakes_elevation)

		self.fname_GWini = filename.drylandmodel[57] 	# Initial water table
		self.fname_DEM = filename.drylandmodel[4]
		# Saturated zone factors ===========================================
		self.kKsat = float(factors.DWAPM_SET[62])	# Ksat factor
		self.kSy = float(factors.DWAPM_SET[64])		# Sy factor

#def get_store_variables(fname):
	"""This function read a file of boolean values indicating the variables to be
	save as grid and csv file
	Parameters
	fname: filename of the paramter setting file
	Returns
	store_var: python object containing dictionaries to with boolean values
	"""

	