# -*- coding: utf-8 -*-
import numpy as np

class ponds():
	def __init__(self, a):
		"""This component calulate the water balance at ponds. Ponds
		are water bodies that store water from precipitation and loss
		water as potential evapotranspiration and human abstractions
		
		"""
		# specify max colume
		#self.Vmax = Vmax
		# calculate denominator for reduce calculations
		self.denominator = 2*a+1 # this could be moved to only perform once		

		pass
	

	def run_ponds_one_step(self, Vo, P, PET, Aoz, a, Vmax, cell_area):
		"""This funciton calcu;ate one step of the water balance at
		ponds.  at the begining f the time step
		
		Parameters
		----------
		Vo: numpy array
			initial volume of water [m3]
		P : numpy array
			precipitation [mm/h]
		PET:numpy array
			potential evapotranspiration [mm/h]
		Aoz : numpy array
			Water abstractions in [m3]
		a:	numpy array
			pond shape factor [-]
			
		Returns
		-------
		V :	numpy array
			volume of water available at the end of time step [m3]
		et :	numpy array
			evaporation from pounds [m3]
		Aoz :	numpy array
			Total abstraction [m3]
		"""
		
		# contribution of precipitation to pond total volume
		P = P*cell_area
		Vo = P + Vo

		# check if there is excess water, pond is filled
		P = Vo - Vmax
		P[P < 0] = 0.0

		# update initial volume of water with excess water
		Vo = Vo - P

		# It is assumed that abstractions can quickly deplet water from
		# ponds
		V = Vo - Aoz
		
		# Water abstraction are limited to the water availability
		Aoz[V < 0] = Vo[V < 0]
		
		# Update initial volume of water with abstractions
		V[V < 0] = 0
				
		# update initial conditions
		Vo = V
		
		# Calculate the volume of water available after evaporation
		V = (np.power(Vo, 1/self.denominator)-(np.pi*PET/self.denominator)*
		    np.power(self.denominator/np.pi, 2*a/self.denominator))
		
		# Remove all zeros
		V[V < 0] = 0.0

		V = np.power(V, self.denominator)

		# caluclate evaporation
		et = V - Vo

		# Calulate precipitation over the cell
		P = P/cell_area
	
		return V, et, Aoz, P
		
		
