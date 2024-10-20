import warnings
warnings.filterwarnings('ignore', message="invalid value encountered in true_divide")
import os
import numpy as np
import scipy.special as spy

#from landlab import RasterModelGrid
#from landlab.io import read_esri_ascii


class infiltration(object):
	def __init__(self, method=0):	
		"""Initializa the infiltration component.
		An infiltration aproach has to bu provided, defauil approach is Philips
		
		Parameters
		----------
		method : str
			0- Shaake
			1- Philips
			2- Upscaled Green ampt method
			3- Modify Green Ampt method

		Attributes
		----------
		method : int
			flag indicating infiltration method

		"""	
		# create all initial states and model funtion variables
		print('************************************************************')
		if method == 1:
			print('Infiltration approach: Philips')			
		elif method == 2:
			print('Infiltration approach: Upscaled GA')			
		elif method == 3:
			print('Infiltration approach: Modified GA')			
		else:
			print('Infiltration approach: Schaake Method')			
		
		# pass method option to the run option
		self.method = method
				
	
	def run_infiltration_one_step(self, Ksat, theta_sat, PSI,
			    Droot, theta, rain, Ft0, SORP0, t_0, rain_day_before, *args):
		
		"""
		Parameters
		----------
		rainfall : numpy array 
			Rainfall
		act_nodes : list int
			Active nodes
		inf_method	: int
			0 - Shaake
			1 - Philips
			2 - Up-scaled GA
			3 - Modified GA
		PSI_f : numpy array
			Maximum potentiometric head (cm)
		Droot : numpy array
			Soil depth (mm)
		SORP0 : numpy array
			Initail sorptivity
		L_0	: numpy array
			Initial water content t = 0
		L : Water content at time t
		ds			: Soil depth

		t_i	: numpy array
			time from the start of the precipitation event

		Returns
		-------

		t_0	: numpy array
			initial t for accumulation	

		Ft : numpy array
			Cummulative infiltration rate [mm]

		SORP : numpy array
			Sorptivity

		inf_dt : numpy array
			infiltration [mm]

		excess_dt : numpy array
			infiltration excess [mm]

		rain_day_before : numpy array int
			flag to indicate if precipitation event have occurred before
		
		"""
		
		
		# L_0:	Initial soil water content [mm]
		# Lsat:	Saturated water content [mm]
		# Ft0:	Cummulative infiltration [mm]
		# t_0:	Initial time for infiltration rate [h]
		# SORP0:Sorptivity at the begining of the time step
		if t_0 is None:
			t_0 = np.zeros_like(Ksat)
		if Ft0 is None:
			Ft0 = np.zeros_like(Ksat)
		if SORP0 is None:
			SORP0 = np.zeros_like(Ksat)
		if rain_day_before is None:
			rain_day_before = 0
		
		Lsat = theta_sat*Droot
		L_0 = theta*Droot

		# run infiltration		
		Ft, SORP, infiltration, excess, t_0, rain_day_before = infiltration_model(
				rain,
				Ksat,
				PSI,
				Droot,
				SORP0,
				L_0,
				Lsat,
				t_0[:],
				Ft0,
				rain_day_before,
				self.method,
				args,#self.args
				)
		
		# test water balance of the model
		try:
			MB = rain - infiltration - excess
			assert np.allclose(MB, 0.0)
		except:
			raise Exception('Infiltration Water balance Error: '
		   		'Please check units and non-data values')

		return infiltration, excess, Ft, SORP, t_0, rain_day_before

def infiltration_model(rainfall, K_sat, PSI_f, Droot, SORP0, L_0, Lsat, t_0, Ft0, rain_day_before, inf_method, *args):
	"""Incorporate the variable saturated conditions make zero precipitation for cell with saturated
	and zero depth of UZ zone	
	
	Parameters
	----------
	rainfall : numpy array 
		Rainfall
	act_nodes : list int
		Active nodes
	inf_method	: int
		0 - Shaake
		1 - Philips
		2 - Up-scaled GA
		3 - Modified GA
	PSI_f : numpy array
		Maximum potentiometric head (cm)
	Droot : numpy array
		Soil depth (mm)
	SORP0 : numpy array
		Initail sorptivity
	L_0	: numpy array
		Initial water content t = 0
	L : Water content at time t
	ds			: Soil depth
	
	t_i	: numpy array
		time from the start of the precipitation event

	Returns
	-------
	
	t_0	: numpy array
		initial t for accumulation	
	
	Ft : numpy array
		Cummulative infiltration rate [mm]
	
	SORP : numpy array
		Sorptivity
			
	inf_dt : numpy array
		infiltration [mm]
	
	excess_dt : numpy array
		infiltration excess [mm]

	rain_day_before : numpy array int
		flag to indicate if precipitation event have occurred before

	"""
	sat_excess_dt = np.where((Lsat-L_0) <= 0.0, rainfall, 0.0)
	rainfall = np.where((Lsat-L_0) <= 0.0, 0.0, rainfall)
	sat_excess_dt = np.where(Droot <= 0.0, rainfall, sat_excess_dt)
	rainfall = np.where(Droot <= 0.0, 0.0, rainfall)
	inode_inf_aux = np.where(rainfall > 0.0)[0]

	if len(inode_inf_aux) > 0:
		t_i = np.zeros_like(rainfall)
		if inf_method == 0: # SCHAAKE METHOD
			ga_kdt = args[0]
			SORP = np.zeros_like(rainfall)
			Ft = np.zeros_like(rainfall)
			
			# Call SCHAAKE function
			inf_dt, excess_dt = SCHAAKE(rainfall, ga_kdt, Lsat, L_0)
			
		elif inf_method == 1: # PHILIPS EQUATION
			F = np.zeros_like(rainfall)
			
			# calulate sorptivity
			SORP = np.where(Droot == 0, 0,
					2*K_sat*PSI_f*((Lsat-L_0)/Droot)
					)
			
			#if len(np.argwhere(np.isnan(SORP))) > 0:
			#	raise(print('stop'))
			SORP[SORP > 0] =  np.sqrt(SORP[SORP > 0])
			
			if rain_day_before == 1:
				SORP[inode_inf_aux] = SORP0[inode_inf_aux]
				t_i[inode_inf_aux] = t_0[inode_inf_aux]
				F[inode_inf_aux] = Ft0[inode_inf_aux]
			
			# call Philips function
			Ft, inf_dt, excess_dt = Philip(rainfall, 
										0.5*K_sat,
										SORP, F,
										np.array(t_i))
										
		elif inf_method == 2: # UPSACALED GREEN & AMPT METHOD
			Ft = np.zeros_like(rainfall)
			mu_logks = args[0][0]
			sigma_ks = args[0][1]
			SORP = np.where(Droot == 0, 0, PSI_f*((Lsat-L_0)/Droot))
			if rain_day_before == 1:
				SORP[inode_inf_aux] = SORP0[inode_inf_aux]
				t_i[inode_inf_aux] = t_0[inode_inf_aux]
			
			# call upscaled GA function
			inf_dt, excess_dt = Upscaled_GA(rainfall,K_sat,SORP,
											np.array(t_i+1.0),
											mu_logks,
											sigma_ks)
											
		elif inf_method == 3: # MODIFIED GREEN AND AMPT EQUATION
			F = np.zeros_like(rainfall)
			SORP = np.where(Droot == 0, 0,
				np.sqrt(2*K_sat*PSI_f*((Lsat-L_0)/Droot)))
				
			if rain_day_before == 1:
				SORP[inode_inf_aux] = SORP0[inode_inf_aux]
				t_i[inode_inf_aux] = t_0[inode_inf_aux]
				F[inode_inf_aux] = Ft0[inode_inf_aux]
			
			# Call Mod_GA function
			Ft, inf_dt, excess_dt = Mod_GA(rainfall,
										K_sat,
										np.array(SORP),
										F,
										np.array(t_i), 1.)
		
		if inf_method > 1:
			inf_dt[SORP == 0] = 0
			excess_dt[SORP == 0] = rainfall[SORP == 0]
		
		t_0[inode_inf_aux] += 1
		rain_day_before = 1
	else:
		t_0 = np.zeros(len(rainfall), dtype=float)
		rain_day_before = 0
		inf_dt = np.zeros(len(rainfall), dtype=float)
		Ft = np.zeros(len(rainfall), dtype=float)
		SORP = np.zeros(len(rainfall), dtype=float)
		excess_dt = np.zeros(len(rainfall), dtype=float)
	excess_dt += sat_excess_dt
	return Ft, SORP, inf_dt, excess_dt, t_0, rain_day_before

 
def SCHAAKE(P, ga_kdt, Lsat, L):
	"""Schaake infiltration approach, Schaake et. al. (1996)

	Parameters
	-----------
	P:	Precipitation
	ks:	Sat. Hydraulic Conductivity
	Sp:	Sorptivity (keep the same sorptivity for one event)
	F:	Cummulative infiltration
	t:	Cummulative event time

	Returns
	--------
	I:		Infiltration over the time step
	RO:		Runoff
	"""
	# calculate water deficit
	D = Lsat-L
	I_aux = D*ga_kdt
	I = P*I_aux/(P+I_aux)
	I[P+I_aux == 0.0] = 0#np.where(P+I_aux == 0.0,0.0,I)
	RO = P-I
	return I, RO

def Philip(P, ks, Sp, F, t):
	"""Philips Infiltration function

	Parameters
	-----------
	P: numpy array
		Precipitation
	ks:	numpy array
		Sat. Hydraulic Conductivity
	Sp:	numpy array
		Sorptivity (keep the same sorptivity for one event)
	F: numpy array
		Cummulative infiltration
	t: numpy array
		Cummulative event time
	
	Returns
	--------
	Ft: numpy array
		Total Cumulative infiltration
	I: numpy array
		Infiltration over the time step
	RO:	numpy array
		Runoff
	"""
	dt = 1
		
	Fp = np.where(P > 0, 0.5*(Sp**2)*(P-0.5*ks)*((P-ks)**(-2)), 0)
	Fp_aux = Fp-F
	#print(np.where(np.isnan(F)), np.where(np.isnan(Fp)), np.where(np.isnan(P)))#, np.where(np.isnan(ks)), np.where(np.isnan(Sp)))	
	dtp = np.where(P > 0.0, Fp_aux/P, 0.0)
	
	ts = np.where(dtp > dt, t+dt, t+dtp)
	ts = np.where(dtp < 0, t, ts)
	
	Faux = np.where(dtp < 0, F, Fp)
	
	sp_aux = np.sqrt(Sp**2+4*ks*Faux) - Sp
	
	to_p = (1/4)*(sp_aux/ks)**2
	to = np.where(dtp < dt, ts-to_p, t+dt-ts)
	
	dtc = np.where(P == 0.0, 0.0, t+dt-to)
	
	Ft_aux = np.where(dtc == 0.0, 0, Sp*dtc**0.5+ks*dtc)
	Ft = np.where(F+P < Ft_aux, F+P, Ft_aux)
	I = Ft - F
	RO = P - I
	return Ft, I, RO

def Upscaled_GA(P, ks, Sp, t, mu_Y, sigma_Y):
	"""Upscaled Green & Ampt infiltration approach - Craig et. al. 2010
	Required Gauss2p, epsilon, and getX

	Parameters
	-----------
	P: numpy array
		Precipitation
	ks:	numpy array
		Sat. Hydraulic Conductivity
	Sp:	numpy array
		Sorptivity (keep the same sorptivity for one event)
	F:	numpy array
		Cummulative infiltration
	t:	numpy array
		Cummulative event time
	
	Returns
	--------
	I: numpy array
		Infiltration over the time step
	RO: numpy array
		Runoff
	"""
	X = getX(t, Sp, P)
	A = np.where(X == 0, 0, (np.log(P*X)-mu_Y)/(sigma_Y*np.sqrt(2)))
	A = np.where(sigma_Y == 0, 1e99, A)
	Aaux = np.exp(mu_Y+0.5*(sigma_Y**2))
	I = np.where(X == 0, 0, 0.5*P*spy.erfc(A)+(0.5/X)*Aaux*spy.erfc((sigma_Y/np.sqrt(2))-A))
	I += np.where(X == 0.0,0.0,Gauss2p(t,Sp,P,mu_Y,sigma_Y,ks))
	RO = P-I
	return I, RO

# 2-point Gauss-Legrenge integrator	
def Gauss2p(t, Sp, P, mu_Y, sigma_Y, ks):
	X = getX(t, Sp, P)
	dk = 0.5*(P*X-np.exp(mu_Y-3.0*sigma_Y))
	km = P*X-dk
	k1 = km-0.57735*dk
	k2 = km+0.57735*dk
	return dk*P*(epsilon_fks(k1,t,Sp,P,mu_Y,sigma_Y,ks)+epsilon_fks(k1,t,Sp,P,mu_Y,sigma_Y,ks))

# Epsilon funtion for upscaled GA infiltration	
def epsilon_fks(k,t,Sp,P,mu_Y,sigma_Y,ks):
	X = getX(t,Sp,P)
	kp = ks/(P*X)
	fks = np.where(k <= 0.0,0.0,(1.0/(k*sigma_Y*np.sqrt(2.0*np.pi)))*np.exp(-0.5*(np.power((np.log(k)-mu_Y)/sigma_Y,2))))
	epsilon = np.where(X == 0.0,0.0,0.36315*np.power(1-X,0.484)*np.power(1.0-kp,1.74)*np.power(kp,0.38))
	epsilon[kp >= 1.0] = 0
	epsilon[kp == 0.0] = 0
	return epsilon*fks

# Dimentionless time parameter	
def getX(t, Sp, P):
	X_aux = P*t/Sp
	return np.where(X_aux == 0.0,0.0,1/(1+1/X_aux))


def Mod_GA(P,ks,Sp,F,t,dt):
	"""Modified Green & Ampt infiltration approach
	Requires solver (Newthon_Rap_Mod_GA) and F (f_GA) and F' (dF_GA)
	
	Parameters
	-----------
	P:	Precipitation
	ks:	Sat. Hydraulic Conductivity
	Sp:	Sorptivity (keep the same sorptivity for one event)
	F:	Cummulative infiltration
	t:	Cummulative event time
	
	Returns
	--------
	Ft:		Total Cumulative infiltration
	I:		Infiltration over the time step
	RO:		Runoff
	"""
	tp = np.where(P > ks,Sp/(P-ks),0)
	aux_1 = tp-t
	aux_2 = t+1-tp
	aux = aux_1*aux_2
	id_error = np.where(aux >= 0)[0]
	if len(id_error) > 0: # ponding during time step
		to = Newthon_Rap_Mod_GA(P,ks,Sp,F,t,tp,0.1)
	else:
		to = t
	Faux = np.where(to == 0,0,ks*(t+dt-to)+Sp*np.log((t+dt)/to))

	F_tf = np.where(tp > t+1,F+P,Faux)
	F_tf = np.where(tp < to,F_tf+F,F_tf)
	F_tf = np.where(tp == 0,P+F,F_tf)

	I = F_tf - F
	RO = P-I
	return F_tf, I, RO
	
def Newthon_Rap_Mod_GA(P,ks,Sp,F,t,tp,to_0):
	error = np.zeros_like(F)
	aux_1 = tp-t
	aux_2 = t+1-tp
	aux = aux_1*aux_2
	id_error = np.where(aux > 0)[0]
	len_error = len(id_error)
	error[id_error] = 1
	to = t
	
	while len_error > 0:
		to = np.where(error < 0.001,t,to_0-f_GA(P,ks,Sp,F,t,tp,to_0)/dF_GA(ks,Sp,to_0))
		error = np.where(error <= 0.001,0.0,np.abs(to-to_0)/to)
		len_error = len(np.where(error >= 0.001)[0])
		to_0 = to	
	return to
	
# Implicit solution of Green and Ampt equation	
def f_GA(P,ks,Sp,F,t,tp,to):	
	return ks*(tp-to)+Sp*np.log(tp/to)-F-P*(tp-t)

# Derivative of the implicit GA equation
def dF_GA(ks,Sp,to):
	return -(ks+Sp/to)
	
## Modified Green & Ampt infiltration approach
#def Mod_GA_Sim(P,ks,Sp,t,dt):
#	# Approximation of Green and Ampt equation for small time steps
#	tp = np.where(P > ks,Sp/(P-ks),0)
#	tf = np.where(tp > t+dt,t+dt,tp)
#	I  = np.where(t == 0,0,ks*(t+dt-tp)+Sp*np.log((t+dt)/tp)-P*(t-tp))
#	RO = P-I
#	return F, I, RO
#	
#def to_modGA(P,ks,Sp,t,tp,to_0):
#	# Next step for 'to', it is done to avoid iteration for each cell
#	F = ks*(tp-to)+Sp*np.log(tp/to_0)-P*(t-tp)
#	dF = -ks-B/to_0
#	to = to_0-F/dF
#	return to