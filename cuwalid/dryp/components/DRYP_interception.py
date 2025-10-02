import numpy as np

class interception(object):

	def __init__(self, LAI_model='SAVI', LAI_function=None):

		""" Interception component
		Parameters
		-----------
		LAI_model:		model to estimate Leaf Area Index (LAI)
						Options: 'SAVI' (default), 'fixed', None
		LAI_function:	function to estimate LAI if LAI_model is 'fixed'
						Options: None (default)
		"""
		self.LAI_model = LAI_model
		self.LAI_function = LAI_function
		print("Run Interception component")
		pass
		
	def run_interception_one_step(self, rain, ETo, av,
		SAVI, savi_max, savi_min, LAI, lai_a, lai_b, fcw, Sc0, Kc):
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
		Scz0:		initial water content canopy
		
		Returns
		-------
		Pth:	Throughfall, precipitation minus interceptionn
		Ecw:	Canopy evaporation
		Scz:	Canopy water storage
		PET:	Potential evapotranspiration after canopy evaporation
		LAI:	Leaf Area Index
		Kc:		Crop factor
		"""
				
		#if Kc is not available:
		if av is not None:
			# Estimation of crop factor
			if Kc is None:
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
			#Sca_max = get_Scmax_from_LAI_and_fcw(fcw, LAI)
			Sca_max = av*get_Scmax_from_LAI(LAI)
			
			# maximum canopy saturation
			#Sca = Sca_max*(1-np.exp(-rain/Sca_max))
			Ecw = Sc0 + rain
			
			Ecw = np.where(Ecw > ETo, ETo, Ecw)

			# Potential canopy evaporation
			#Eca = av*ETo*Sc0/Sca_max
			
			Sca = Sc0 - Ecw + rain
			
			# Interception
			Pth = Sca - Sca_max

			Scz = np.where(Pth > 0, Sca_max, Sca)

			Pth = np.where(Pth > 0, Pth, 0.0)

			# limit evaporation to the amount of water available
			Pth[Pth < 0] = 0
			
			# Potential evapotranspiration after canopy evaporation
			PET = (ETo - Ecw)

			PET[PET < 0] = 0.0			
					
		else:
			Ecw = None
			LAI = None
			Kc = None
			Pth = rain
			PET = ETo
			Sc = None
			
		return Pth, Ecw, PET, LAI, Kc, Scz
		
	
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