# -*- coding: utf-8 -*-
import numpy as np

class ponds():
	def __init__(self, Amax, hmax):
		"""This component calulate the water balance at ponds. Ponds
		are water bodies that store water from precipitation and loss
		water as potential evapotranspiration and human abstractions
		
		Parameters
		----------
		Amax: numpy array
			maximum surface area [m2]
		hmax : numpy array
			maximum pond depth [m]
		
		"""
		# specify max colume
		# calculate pond parameters: shape factor and Vmax
		#self.a = (1/2)*np.log(Amax)/np.log(hmax)
		self.a = 2.0
		self.b = (Amax/np.pi)*np.power(hmax, -2.*self.a)
		self.Vmax = (np.pi*self.b/(2*self.a+1))*hmax**(2*self.a+1)
		#print(Amax,hmax)
		# calculate denominator for reduce calculations
		self.denominator = 2.0*self.a+1 # this could be moved to only perform once		
		#print(self.denominator)
		pass
	

	def run_ponds_one_step(self, Vo, P, PET, cell_area, Aoz=None):
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
		cell_area:	numpy array
			grid cell area [m2]
			
		Returns
		-------
		V :	numpy array
			volume of water available at the end of time step [m3]
		et :	numpy array
			evaporation from pounds [m3]
		Aoz :	numpy array
			Total abstraction [m3]
		"""
		#print(Vo, P, PET, cell_area)
		# contribution of precipitation to pond total volume
		# transform all units to m
		P = P*cell_area*0.001
		Vo = P + Vo

		# check if there is excess water, pond is filled
		P = Vo - self.Vmax
		P[P < 0] = 0.0

		# update initial volume of water with excess water
		Vo = Vo - P

		# It is assumed that abstractions can quickly deplet water from
		# ponds
		if Aoz is None:
			Aoz = np.zeros(len(Vo))

		V = Vo - Aoz
		
		# Water abstraction are limited to the water availability
		Aoz[V < 0] = Vo[V < 0]
		
		# Update initial volume of water with abstractions
		V[V < 0] = 0
				
		# update initial conditions
		Vo = V
		
		# Calculate the volume of water available after evaporation
		V = (np.power(Vo, 1/self.denominator)-(np.pi*self.b*PET*0.001/self.denominator)*
		    np.power(self.denominator/(np.pi*self.b), 2*self.a/self.denominator))
		
		# Remove all zeros
		V[V < 0] = 0.0

		V = np.power(V, self.denominator)

		# caluclate evaporation
		et = Vo - V
		
		# check mass balance
		#try:
		#	MB = P + Aoz + et
		#	assert np.allclose(MB, 0.0)
		#except:
		#	raise Exception('Ponds Water balance Error: '
		#   		'Please check units and non-data values')
		# Calulate precipitation over the cell
		# change units to mm
		P = P*1000.0/cell_area
	
		return V, et, Aoz, P
		
		
