"""Test Infiltration model
"""

import numpy as np
from cuwalid.dryp.components.DRYP_soil_layer import swbm

def test_soil_layer():
			
	# specify soil hydraulic parameters
	# saturated hydraulic conductivity
	Ksat = np.array([10.545]) #
	
	# sorptivity
	PSI = np.array([11.01]) # mm
	
	# rooting depth
	Droot = np.array([1000]) # mm
	
	# crop factor
	Kc = np.array([1.0])
	
	# soil particle distribution parameter
	b = 10.5
	c = np.array([2/b + 3])
	
	theta_sat =np.array([0.40])
	theta_fc = np.array([0.30])
	theta_wp = np.array([0.20])
						
	Lsat = np.array(theta_sat[0]*Droot[0]) # mm theta_sat = 0.6
	
	# initail water content
	theta = np.array([0.212])
	
	# forcing variables
	# infiltration
	inf = [30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
	inf = np.append(inf, np.zeros(100))
	
	# potential evapotranspiraiton
	pet = np.full(len(inf), 2.0)
	
	# create a zero array to represent the mass balance
	answer = np.zeros_like(inf)
	swb = swbm(60)
	
	out = []
	# only to check the results
	#thetaarray = []
	#PCRarray = []
	#AETarray = []

	for inf_dt, pet_dt in zip(inf, pet):
	
		storage0 = Droot[0]*theta[0]
		
		AET, PCR, theta, ROF =swb.run_swbm_one_step(
							np.array([inf_dt]),
							np.array([pet_dt]),
							Kc, Ksat*0.6,
							theta_sat, theta_fc, theta_wp,
							c, Droot, theta
							)
		
		#thetaarray.append(theta)
		#PCRarray.append(PCR)
		#AETarray.append(AET)
		#print(PCR)
		mass_balance = inf_dt-AET[0]-PCR[0]-ROF[0] - (theta[0]*Droot[0] - storage0)
		
		out.append(mass_balance)
	
	# only to check the results
	#import matplotlib.pyplot as plt
	#fig, ax = plt.subplots()
	#ax.plot(inf)
	#ax.plot(PCRarray, label="PCR")
	#ax.plot(AETarray, label="AET")
	#ax.legend(loc=5)
	#ax2 = ax.twinx()
	#ax2.plot(thetaarray, "r.", label="tht")
	#ax2.legend()
	#plt.show()
	
	assert np.allclose(out, answer)
	print('Soil Layer Drainage: Test runs successfully')

if __name__ == '__main__':
	test_soil_layer()