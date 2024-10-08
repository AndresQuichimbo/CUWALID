import numpy as np

class interception(object):

	def __init__(self,):
		
		print("Run Interception component")
		pass
		
	def run_interception_one_step(self, rain, ETo, av,
		SAVI, savi_max, savi_min, LAI, lai_a, lai_b, fcw, Sc0):
		"""	Canopy compartment, calculates interception and
		evaporation from canopy.
		
		Parameters
		-----------
		rain:		precipitation
		av:			fraction of vegetation cover [-]
		SAVI:		Soil-Adjusted Vegetation Index
		Kc:			crop coefficient factor
		env_state:	grid:	z:		Topograhic elevation
							h:		water table
		
		fcw:		biome-dependent coeficient		
		Sc0:		initial water content canopy
		
		Returns
		-------
		Pth:	Throughfall, precipitation minus interceptionn
		Eca:	Canopy evaporation
		"""
				
		#if Kc is not available:
		if av is not None:
			# Estimation of crop factor
			if SAVI is not None:
				Kc = get_vegetation_factor(SAVI, savi_min, savi_max)
			else:
				Kc = 1
			
			if LAI is None:	
				# Estimation of Leaf area index
				if SAVI is not None:
					LAI = get_LAI_from_SAVI(SAVI, lai_a, lai_b)
				else:
					LAI = 0
			
			# Maximum amount of water store by canopy
			Sca_max = get_Scmax_from_LAI_and_fcw(fcw, LAI)
			
			# maximum canopy saturation
			Sca = Sca_max*(1-np.exp(-rain/Sca_max))
			
			#Sca_aux = Sca - Sc0
			
			#Sca[Sca_aux < 0] = Sc0[Sca_aux < 0]
			# add precipitation duration
			#aux_rain = np.array(rain)
			#aux_rain[aux_rain > 0] = 1
						
			# Available storage
			#Sca_aux[Sca_aux < 0] = 0.0
			#Sct = (Sca_max - Sc0)
			
			# Potential canopy evaporation
			Eca = av*ETo*Sca/Sca_max
			
			# canopy evaporation
			#Eca = Sc0 - Ecap
			
			# throughfall
			Pth = rain - Eca + Sc0
			#print(rain[50], Eca[50], Sca_max[50], Sc0[50], Pth[50], av[50])
			# limit evaporation to the amount of water available
			Pth[Pth < 0] = 0
			
			# Update canopy evaporation
			Eca = rain - Pth + Sc0
			
			# Update throufall to allow canopy storage
			Pth = Pth - av*(Sca_max) + Sc0
			
			# reduce throughfall by the canopy storage
			Pth[Pth < 0] = 0
			
			#print(rain[50], Eca[50], Sca_max[50], Sc0[50], Pth[50], av[50])
			#Eca[Eca > Sca_max] = Sca_max[Eca > Sca_max]
			
			# Mass balance			
			Sc = rain - Pth - Eca + Sc0
			#Eca = av*Eca
			
			# Potential evapotranspiration after canopy evaporation
			PET = (ETo - Eca)
						
			# Interception
			#I = av*Sca + Eca
			
			# Throughfall
			#Pth = rain - I
			
			# make throufall do not exced the precipitaiton
			#Pth[Pth<0] = 0.0
					
		else:
			Eca = None
			LAI = None
			Kc = None
			Pth = rain
			PET = ETo
			Sc = None
			
		return Pth, Eca, PET, LAI, Kc, Sc
		
	
def get_vegetation_factor(savi, savi_min, savi_max):
	"""Crop factor calculation kc for ETo
	
	Parameters
	-----------
	savi:		Soil-Adjusted Vegetation Index
	savi_min: 	min Soil-Adjusted Vegetation Index
	savi_max: 	max Soil-Adjusted Vegetation Index
	
	Returns
	-------
	kc:			Crop factor
	"""
	
	nu = 1.0
	
	kc = 1 - (savi_max - savi)/(savi_max - savi_min)
	
	#kc = kc**nu
	
	return kc
		

def get_LAI_from_SAVI(SAVI, a, b):
	"""Calculate LAI from SAVI
	
	Parameters
	----------
	SAVI:	Soil adjusted vegetation index
	a:		Coeficient of exponential function
	b: 		power value for exponential function
	
	Returns
	------
	LAI:	leaf area index
	"""
	
	LAI = a*np.exp(b*SAVI) 
	
	return LAI
	

def get_Scmax_from_LAI(LAI):
	"""Calculate maximum amount of water store by canopy
	
	Parameters
	----------
	LAI:	leaf area index
	
	Returns
	------
	Sca_max:	Maximum amount of water store by canopy
	"""
	
	Sca_max = 0.935 + 0.498*LAI - 0.00575*(LAI**2)
	
	return Sca_max
	
def get_Scmax_from_LAI_and_fcw(fcw, LAI):
	"""Calculate maximum amount of water store by canopy
	exponential approach
	http://refhub.elsevier.com/S0022-1694(19)30648-1/h0170
	
	Parameters
	----------
	LAI:	leaf area index [-]
	fcw:	biome-dependent coeficient [-]
	
	Returns
	------
	Sca_max:	Maximum amount of water store by canopy
	"""
	
	Sca_max = fcw*np.log(1+LAI)
	
	return Sca_max