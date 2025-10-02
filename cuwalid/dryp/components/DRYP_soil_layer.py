import numpy as np

class swbm(object):

	def __init__(self, dt):
		"""run the soil layer component for estimating actual
		evpotranspiration and groundwater recharge. This component
		is also used to estimate the water content in the riparian
		zone:
		
		This components computes the following variables:
		
		AET_dt:	Actual evapotranspiration [mm]
		THT_dt:	Soil water content [-]
		PCL_dt:	Percolation [mm]
		layer:	up to 2 layer, default 1
		"""
		# create variables for python objects
		self.dt = dt
		
		self.two_layer = 0
		# activate second layer for soil moisture
		#if layer:
		#	self.two_layer = 1
		#else:
		#	self.two_layer = 0
			
		#if self.two_layer == 1:
		#	# call the one-layer model
		#	self.L_0l = np.array(Duz)*self.tht_dt
		#	self.thtl_dt = np.array(tht_t0)
		pass
		
		
	def run_soil_aquifer_one_step(self, surface, head, Droot,
					theta_fc, theta_wp, Duz0, theta):
		"""	Update depth of the unsaturated soil depending on the
		water table elevation.

		Parameters
		----------
		tht_dt:	Soil water content at time t [-]
		z:		Topograhic elevation
		h:		water table
		fs:		Saturated water content
		fc:		Field capacity
		Sy:		Specific yield
		dq:		water storage anomaly
		Droot:	Rooting depth [mm]

		Returns
		-------
		Duz:	Unsaturated zone depth
		tht:	Updated soil ater content		
		"""
		# update rooting depth
		Duz = variable_soil_depth(surface, head, Droot)
		#print(67,np.mean(theta))
		# update soil water content
		theta = np.where((Duz0-Duz) > 0.0,
				theta*Duz,
				(Duz0*theta-(Duz0-Duz)*theta_fc))
		#print(72,np.mean(theta))		
		theta[Duz > 0] = theta[Duz > 0]/Duz[Duz > 0]
		theta[Duz <= 0] = theta_wp[Duz <= 0]
		theta = np.maximum(theta_wp, theta)
		return Duz, theta
	
	#@profile
	def run_swbm_one_step(self, inf, pet, Kc, Ksat, theta_sat,
		    	theta_fc, theta_wp, c, Droot, theta):
		"""This component call the one-layer soil water balance model
		
		Parameters
		-------
			inf:		infiltration [mm]
			pet:		potential evapotranspiration [mm]
			Kc:			Crop factor [-]
			Ksat:		Saturated hydraulic conductivity of the soil [mm/dt]
			Droot:		rooting depth
			theta:		initial water content
			theta_fs:	Soil moisture at saturated conditions
			theta_fc:	Soil moisture at field capacity
			theta_wp:	Soil moisture at wilting point
		
		Returns
		------
		
		"""
		# find nodes with root depth greater than 0
		nodes = np.where(Droot > 0.0)[0]
		
		# create states arrays
		AET = np.zeros_like(theta, dtype=float)
		PCR = np.zeros_like(theta, dtype=float)
		THT = theta.copy()
		ROF = inf.copy()
		#print(np.mean(theta))
		if nodes.size > 0:

			L_0 = theta[nodes]*Droot[nodes]

			# run two-layer model
			if self.two_layer == 0:
				# call the one-layer model
				if self.dt >= 1440:				
					AET_dt, PCR_dt, L_dt, ROF_dt = SWBM(
										inf[nodes],
			    						pet[nodes],
										Kc[nodes],
										L_0, Droot[nodes],
										theta_sat[nodes],
										theta_fc[nodes],
										theta_wp[nodes]
										)
					
				else:				
					AET_dt, PCR_dt, L_dt, ROF_dt = SWBMh(
										inf[nodes],
			     						pet[nodes], 
										Kc[nodes],
										L_0, Droot[nodes],
										theta_sat[nodes], 
										theta_fc[nodes], 
										theta_wp[nodes],
										c[nodes],
										Ksat[nodes]
										)
			
			#else:					
			#	# water content of the lower soil layer
			#	L_0l = self.L_0l[act_nodes]
			#	
			#	# call two-layer model solver
			#	L, Ll, E, T, D, RO = FAO2L(inf, pet, Kc,
			#								L_0, L_0l,
			#								ds, ds,
			#								theta_sat, theta_fc, theta_wp,
			#								c, Ksat)
			#	
			#	self.L_0l[act_nodes] = np.array(Ll)
			#	self.thtl_dt[act_nodes] = np.array(Ll/ds)	
			#	AET = E + T
			
			AET[nodes] = AET_dt
			PCR[nodes] = PCR_dt
			THT[nodes] = L_dt/Droot[nodes]
			ROF[nodes] = ROF_dt
		# If the soil is fully saturated, unsaturated zone is zero,
		# (water table is close to the surface), all water return
		# as saturation excess, there is not percolation
		#print(inf, AET, theta, Droot, THT)
		#print(inf - AET - PCR - ROF - (THT - theta)*Droot)
		#print(226, np.mean(inf), np.mean(AET), np.mean(PCR), np.mean(ROF))
		#print(np.mean((THT - theta)*Droot), np.mean(theta), np.mean(THT))
		# test the mass balance
		try:
			MB = np.mean(inf - AET - PCR - ROF - (THT - theta)*Droot)
			assert np.allclose(MB, 0.0, rtol=1e-05, atol=1.5e-05)
		except:
			raise Exception(MB,
			    'Soil Water balance Error: '
		   		'Please check units and non-data values')

		return AET, PCR, THT, ROF
		
	
	def water_deficit(self, discharge, evaporation, soil_deficit):
		"""Calculate the amount of water required to saturated
		the riparian zone

		Parameters
		----------
		discharge:	numpy array
			groundwater discharge [mm]
		soil_deficit:	numpy array
			soil moisture deficit riparian zone [mm]
		evaporation:	numpy array
			potential evapotranpiration at riparian zone [mm]
			pet = (PET - AET_soil)
		
		Returns
		-------
		smd:	numpy array
			water deficit below the streambed [mm]
		qriv: numpy array
			runoff [mm]
		inf:	numpy array
			infiltration [mm]
		"""
		
		# water required to saturate riparian zone
		soil_deficit = np.array(soil_deficit, dtype=np.float64)
		
		# calculate the surplus of water
		qriv = discharge - soil_deficit		
		soil_deficit = np.where(qriv > 0, 0, soil_deficit-discharge)
		
		# update river baseflow to unsaturated state, basically
		# all water will be stored in the riparian area
		qriv[qriv < 0] = 0
		
		# water required to overcome potential ET
		smd_et = evaporation - qriv
		
		# check if river baseflow could supply also evaporation
		# if there is enough, reduce the river baseflow by pet
		qriv = np.where(smd_et > 0, 0, -smd_et)
		
		# check if riparian demand is being supplied
		smd_et[smd_et < 0] = 0
		
		# total deficit in the unsaturated zone
		smd = soil_deficit + smd_et
		
		# partition of river baseflow into riparian demand
		inf = discharge - qriv
		
		return smd, qriv, inf
	
# Soil water balance model for daily time steps - constant Kc
# This model assumes that percolation occurrs immediately after precipitation 
def SWBM(I, PET, Kc, L0, z_soil, fs, fc, wp):
	"""Soil water balance

	Parameters
	----------
		I:	Infiltration
		PET:	Potential evapotranspiration
		L0:	initial water content
		SMD_0:Initial soil moisture deficit
		z_soil:Soil depth variation
		fs:	Soil moisture at saturated conditions
		fc:	Soil moisture at field capacity
		wp:	Soil moisture at wilting point
		c:	Exponential recession term estimated as
		d:	Soil parameter par_swb for reducing time steps
		z:    Surface elevation
		h:    Water table elevation
		Droot:Soil rooting depth
		Lsat:	Water content at saturated condition

	Returns
	-------
		AET:	Actual evpotranspiration
		D:		Drainage
		L:		Water content
	"""
	# calculate reference evapotranspiration
	PET = Kc*PET
	Pc = 0.5

	# water content at saturation condition
	Lsat = z_soil*fs
	# water content at wilting point
	Lwp = z_soil*wp
	# water content at field capacity
	Lfc =  z_soil*fc
	
	# total available water
	TAW =  Lfc - Lwp

	# ready available water
	RAW = Pc * TAW
	
	# water content at ready available water
	L_RAW = Lfc - RAW

	# water content at total available water
	L_TAW = Lfc - TAW
	
	# calculate stress coeficient
	den = L_RAW-L_TAW	
	beta = (L0-L_TAW)
	beta = (beta/den)
	beta[beta > 1.0] = 1.0
	beta[beta < 0.0] = 0.0	
	
	# calcualte direct evaporation from infiltration
	I_AET = np.where(I > PET, PET, I)

	# caculate evaporation from water stored in the soil
	AET = I_AET*(1.0-beta) + beta*PET
	AET[AET < 0.0] = 0.0
	
	# water balance
	L = L0 + I - AET
	
	# check if soil moisture do not go below wilting point
	AET = np.where((L-Lwp) < 0.0, L0 + I-Lwp, AET)
	
	# calculate water balance
	L = L0 + I - AET
	
	# calculate drainage
	D = L - Lfc
	D[D < 0.0] = 0.0
	#D = np.where(L-Lfc > 0.0, L-Lfc, 0.0)
	
	# calculate water content after drainage
	L = L-D
	
	# calculate runoff excess
	RO = L-Lsat
	RO[RO < 0.0] = 0.0
	
	# calculate soil after infiltration excess
	L = L-RO
	
	return AET, D, L, RO

# Soil moisture water balance model for subhourly time steps - Variable Kc
def SWBMh(I, PET, Kc, L0, Droot, fs, fc, wp, c, Ksat):
	"""Soil water balance

	Parameters:
	-----------
		I:	Infiltration
		PET:	Potential evapotranspiration
		L0:	initial water content
		SMD_0:Initial soil moisture deficit
		z_soil:Soil depth variation
		fs:	Soil moisture at saturated conditions
		fc:	Soil moisture at field capacity
		wp:	Soil moisture at wilting point
		c:	Exponential recession term estimated as
		d:	Soil parameter par_swb for reducing time steps
		z:    Surface elevation
		h:    Water table elevation
		Droot:Soil rooting depth
		Lsat:	Water content at saturated condition	
	
	Returns
	-------
		AET:	Actual evpotranspiration
		D:		Drainage
		L:		Water content
	"""
	
	# reference potential evapotranspiration
	PET = Kc*PET
	Pc = 0.5
	
	# water content at different states
	Lsat = Droot*fs
	Lwp = Droot*wp
	Lfc = Droot*fc
	
	# total availble water
	TAW = Lfc - Lwp
	
	# stress limit available water
	RAW = Pc * TAW
	# calculater availble water at ready available	
	L_RAW = Lfc - RAW
	L_TAW = Lfc - TAW
	
	# Calculate stress coeficient
	den = L_RAW - L_TAW	
	beta = (L0 - L_TAW) / den

	# Clip beta to the [0, 1] range
	beta = np.clip(beta, 0.0, 1.0)
	
	# Calculate direct evaporation from precipitation/infiltration
	I_AET = np.where(I > PET, PET, I)
	
	# Calculate evaporation under stress conditions
	AET = I_AET*(1.0-beta) + beta*PET
	#AET[AET < 0.0] = 0.0
	
	# Update water content
	L_aux = L0 + I - AET - Lwp

	# Update evaporation under limited water content, this will
	# not allow the water content to be less than wilting_point
	AET[L_aux < 0.0] = (L0+I-Lwp)[L_aux < 0.0]
	
	# Update water content
	L_aux = L0 + I - AET
	
	# Calculate infiltration excess
	RO = np.where(L_aux > Lsat, L_aux-Lsat, 0.0)
	
	L_aux -= RO
	
	# calculate second term of drainage equation
	kd = (1.0 - c) * Ksat / (Droot*np.power(fs, c))
	
	# calculate the water content after drainage
	Lt_term = np.power(L_aux / Droot, 1.0 - c) - kd
	Lt_term = np.clip(Lt_term, 1e-9, None) # Clip to avoid log(negative)
	Lt = Droot * np.power(Lt_term, 1.0 / (1.0 - c))
	
	# calculate the variation of water content due to drainage
	# check if the change in water content do not fall below field
	# capacity due to drainage, drainage will start to ocurr only until
	# field capacity is reached
	D = np.where(Lt > Lfc, L_aux-Lt, L_aux-Lfc)
	
	# check if drainage is not reducing the soil storage below
	# field capacity, 
	D[D < 0.0] = 0.0
	# Update drainage under infiltration excess, the maximu
	# drainage rate is Ksat, therefore, drainge can not be
	# greater than Ksat. The potential drainage rate is 
	# (assumin that water flows continuously into the soil):
	
	# Calculate water content
	L = L_aux - D
	
	return AET, D, L, RO

# Variable soil depth
def variable_soil_depth(z, h, Droot):
	# Luz	: Soil depth variation
	# z     : Surface elevation
	# h     : Water table elevation
	# Droot	: Soil rooting depth
	# Lsat	: Water content at saturated condition
	Zs = z - Droot*0.001
	Duz = np.where((Zs - h) >= 0, Droot, (z - h)*1000.0)
	Duz[Duz < 0] = 0
	return Duz
	
# Schaake infiltration approach, Schaake et. al. (1996)
# Soil moisture water balance model for subhourly time steps
# Needs numerical integrator to work RK4Sh
def SWBSh(P, PET, L, depth, Ks, Lsat, Lfc, Lwp, Pc, c, ga_kdt):
	"""Sheeke infiltration rates	
	"""
	TAW =  Lfc - Lwp
	RAW = Pc * TAW
	L_RAW = Lfc-RAW
	L_TAW = Lfc-TAW
	D = Lsat-L
	
	I_aux = D*ga_kdt
	I = P*I_aux/(P+I_aux)
	I = np.where(P+I_aux == 0.0,0.0,I)
		
	beta = (L-L_TAW) / (L_RAW-L_TAW)
	beta[beta > 1] = 1
	
	I_AET = np.where(I > PET,PET,I)
	AET = I_AET*(1-beta)+beta*PET
	R = np.where(L-Lfc > 0.0,Ks*(L/Lsat)**c,0.0)
	dL = I-AET-R
	return dL, I, AET, R
	
# Runge Kutta apprach for solving soil moisture SWBSh
def RK4Sh(P, PET, L0, depth, Ks, Lsat, Lfc, Lwp, Pc, kdt, c, dt):
	k1, I, AET, R = SWBSh(P, PET, L0, depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	k2, I, AET, R = SWBSh(P, PET, L0+k1/3, depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	k3, I, AET, R = SWBSh(P, PET, L0+k2/3, depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	k4, I, AET, R = SWBSh(P, PET, L0+k3, depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	L = L0 + k1/6 + k2/3 + k3/3 + k4/6
	k, I, AET, R = SWBSh(P, PET, L, depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	return L,I,AET,R

# Soil water balance model for subdaily time steps
# Infiltration input
# Needs numerical integrator to work RK4Ph
def SWBPh(P, PET, L, depth, Ks, Lsat, Lfc, Lwp, Pc, c, ga_b):
	TAW =  Lfc - Lwp
	RAW = Pc * TAW
	L_RAW = Lfc-RAW
	L_TAW = Lfc-TAW
	D = Lsat-L

	I_aux = D#*ga_kdt
	I = P*I_aux/(P+I_aux)
	I = np.where(P+I_aux == 0.0,0.0,I)

	beta = (L-L_TAW) / (L_RAW-L_TAW)
	beta[beta > 1] = 1

	I_AET = np.where(I > PET,PET,I)
	AET = I_AET*(1-beta)+beta*PET
	R = np.where(L-Lfc > 0.0,Ks*(L/Lsat)**c,0.0)
	dL = I-AET-R
	return dL, I, AET, R

# Runge Kutta apprach for solving soil moisture SWBPh
def RK4Ph(P, PET, L0, depth, Ks, Lsat, Lfc, Lwp, Pc, kdt, c, dt):
	k1, I, AET, R = SWBPh(P, PET, L0, depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	k2, I, AET, R = SWBPh(P, PET, L0+k1/3,depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	k3, I, AET, R = SWBPh(P, PET, L0+k2/3,depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	k4, I, AET, R = SWBPh(P, PET, L0+k3, depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	L = L0 + k1/6 + k2/3 + k3/3 + k4/6
	k, I, AET, R  = SWBPh(P, PET, L, depth, Ks, Lsat, Lfc, Lwp, Pc, c, kdt)
	return L, I, AET, R
	
#def lateral_flow_river_cell(L_riv,L_soil,Ktheta,dx):
#	return (L_riv - L_soil)*np.exp(Ktheta/d_sr)+L_soil


# Two layer model using and numerical integrator
# The model considers firstevaporation from the upper layer
# If there is enough water in the 
def SWBM1L(I, PET, Kc, L0, z_soil, fs, fc, wp, c, Ksat):
	"""Soil water balance

	Parameters
	----------
		I:	Infiltration
		PET:	Potential evapotranspiration
		L0u:	initial water content upper layer
		L0l:	initial water content bottom layer
		SMD_0:	Initial soil moisture deficit
		D_u:	Soil depth upper layer
		D_l:	Soil depth lower layer
		fs:		Soil moisture at saturated conditions
		fc:		Soil moisture at field capacity
		wp:		Soil moisture at wilting point
		c:		Exponential recession term estimated as
		d:		Soil parameter par_swb for reducing time steps
		z:		Surface elevation
		h:		Water table elevation
		Droot:	Soil rooting depth
		Lsat:	Water content at saturated condition
	
	Retuns
	-------
		AET:	Actual evpotranspiration
		D:		Drainage
		L:		Water content
	"""
	
	# reference potential evapotranspiration
	PET = Kc*PET
	Pc = 0.5
	
	# water content at different states
	Lsat = z_soil*fs
	Lwp = z_soil*wp
	Lfc = z_soil*fc
	
	# total availble water
	TAW = Lfc - Lwp
	# stress limit available water
	RAW = Pc * TAW
		
	L_RAW = Lfc - RAW
	L_TAW = Lfc - TAW
	
	# Calculate stress coeficient
	den = L_RAW - L_TAW	
	beta = (L0 - L_TAW)
	beta = beta/den
	
	beta[beta > 1] = 1
	beta[beta < 0] = 0	
		
	I_AET = np.where(I > PET, PET, I)
	AET = I_AET*(1-beta) + beta*PET
	AET[AET < 0] = 0
	
	#L_aux = L0 + I - AET
	
	# This will not allow the soil misture to be less than wilting_point
	AET = np.where((L0 + I - AET - Lwp) < 0, L0+I-Lwp, AET)
	
	L_aux = L0 + I - AET
	
	RO = np.where(L_aux > Lsat, L_aux-Lsat, 0)
	
	#L_aux -= RO
	aux = L0 - Lfc
	aux[aux < 0] = 0
	#R = np.where(aux > 0,
	R =	Ksat*np.power((aux)/Lsat, c)#,#/z_soil,
		#0)
		
	#DL = np.where(DL < 0, L_aux-Lfc, 0.0)
	R = np.where(aux - R < 0, aux, R)
	DL = I - AET - R
	
	return DL, AET, R, RO


def SWBM2L(I, PET, Kc, L0u, L0l, z_soilu, z_soill, fs, fc, wp, c, Ksat):
	"""Mass balance of the two reservoirs
	"""
	# Potential evapotranspiration upper layer
	PETu = 2*PET*z_soilu*(0.5*z_soilu + z_soill)*np.power(z_soilu + z_soill,-2)	
	
	# Upper layer mass balance
	DLu, E, RO, Ru = SWBM1L(I, PETu, Kc, L0u, z_soilu, fs, fc, wp, c, Ksat)
	
	# Potential evapotranspiration lower layer
	PETl = PET - E	
	
	# Lower layer mass balance
	DLl, T, RO, R = SWBM1L(Ru, PETl, Kc, L0l, z_soill, fs, fc, wp, c, Ksat)
	
	return DLu, DLl, E, T, R, RO
	
	

def FAO2L(I, PET, Kc, L0u, L0l, z_soilu, z_soill, fs, fc, wp, c, Ksat):
	""" Runge Kutta apprach for solving soil moisture SWBPh
	
	Parameters
	----------
	Lu:			Water content upper layer
	Ll:			Water content lower layer
	z_soilu:	Soil upper layer thickness
	z_soill:	Soil lower layer thickness

	Returns
	-------
	
	"""
	
	ku1, kl1, E, T, R, RO = SWBM2L(I, PET, Kc, L0u, L0l, z_soilu, z_soill, fs, fc, wp, c, Ksat)
	ku2, kl2, E, T, R, RO = SWBM2L(I, PET, Kc, L0u+ku1/3, L0l+kl1/3, z_soilu, z_soill, fs, fc, wp, c, Ksat)
	ku3, kl3, E, T, R, RO = SWBM2L(I, PET, Kc, L0u+ku2/3, L0l+kl2/3, z_soilu, z_soill, fs, fc, wp, c, Ksat)
	ku4, kl4, E, T, R, RO = SWBM2L(I, PET, Kc, L0u+ku3, L0l+kl3, z_soilu, z_soill, fs, fc, wp, c, Ksat)
	Lu = L0u + ku1/6 + ku2/3 + ku3/3 + ku4/6
	Ll = L0l + kl1/6 + kl2/3 + kl3/3 + kl4/6
	
	DLu, DLl, E, T, R, RO  = SWBM2L(I, PET, Kc, Lu, Ll, z_soilu, z_soill, fs, fc, wp, c, Ksat)
	
	# Calculate soil moisture deficit for GW - SW interactions
	SMD_dt = z_soilu*fc - Lu
	SMD_dt[SMD_dt < 0] = 0
	
	return Lu, Ll, SMD_dt, E, T, R, RO
	

	
	
	
	
	
	
	
	