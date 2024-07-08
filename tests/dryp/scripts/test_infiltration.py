"""Test Infiltration model
"""
from context import dryp
import numpy as np
from dryp.components.DRYP_infiltration import infiltration

def test_infiltration():
	# define grid size
	grid_size = 1
	
	# select Philips infiltration approach
	method = 1
	
	# specify soil hydraulic parameters
	# saturated hydraulic conductivity
	Ksat = np.array([0.275]) #
	# sorptivity
	PSI = np.array([11.01]) # mm
	# rooting depth
	Droot = np.array([1000]) # mm
	# water content
	theta_sat = np.array([0.612]) # mm theta_sat = 0.6
	
	# initial water content
	theta = np.array([0.20])
	
	# initial conditions
	Ft0 = None
	SORP0 = None
	t_0 = None
	dry_day = None
	
	# define precipitation
	rain = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.4, 0.6, 0.6]
	
	# initialising the infiltration model
	inf = infiltration(1)
	
	# expected solution
	answer = [0.3, 0.4, 0.5, 0.6, 0.6999815, 0.64082618, 0.4, 0.52407334, 0.4846126]
	
	out = []
	
	for irain in rain:
		# run one step of infiltration
		INF, EXS, Ft0, SORP0, t_0, dry_day = inf.run_infiltration_one_step(
			Ksat, theta_sat, PSI, Droot, theta,
			np.array([irain]),
			Ft0, SORP0, t_0, dry_day,
			)
		out.append(INF[0])
	
	assert np.allclose(out, answer)

	print('Infiltration: Test runs successfully')

if __name__ == '__main__':
	test_infiltration()