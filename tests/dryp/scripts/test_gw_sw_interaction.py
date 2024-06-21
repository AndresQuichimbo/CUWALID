# -*- coding: utf-8 -*-
"""This script test the groundwater-surface water
components. This component uses the function lakes
which is written in Fortran and needs to be
compiled during the model installation"""

from context import dryp
import numpy as np
import DRYPv2.dryp.components.lakesf90 as lakes

def test_gw_sw_interaction():
    # specify grid size
    grid = 3
    
    # surface, soil and lake elevation
    dem_elevation = np.full(grid, 100, dtype=float)
    lake_elevation = np.array([100, 95, 100], dtype=float)
    soil_elevation = np.array([99, 94, 99], dtype=float)

    # storage parameters of the aquifer and soil
    Sy_aquifer = np.full(grid, 0.10, dtype=float)
    theta_sat = np.full(grid, 0.30, dtype=float)
    theta_fc = np.full(grid, 0.10, dtype=float)
    
    # initial conditions
    theta = np.full(grid, 0.1, dtype=float)
    head = np.array([99.5, 98, 97.0], dtype=float)
    storage_change = np.full(grid, -0.01, dtype=float)
    
    # save initial head
    head0 = head.copy()
    # call fortran funtion for calculation
    for i in range(10):
        aux_head = np.array(head, np.float32)
        lakes.uz_sz_interaction.update_soil(
	    	np.array(dem_elevation, np.float32),
	    	np.array(lake_elevation, np.float32),
	    	np.array(soil_elevation, np.float32),
	    	np.ones(grid, np.float32),# specifiy yield upper layer (always 1 for lakes)
	    	np.zeros(grid, np.float32),# field capacity (always zero for lakes)
	    	np.zeros(grid, np.float32),# water content (alwas zero for lakes)
	    	np.array(theta_sat, np.float32),
	    	np.array(theta_fc, np.float32),
	    	np.array(theta, np.float32),
	    	np.array(storage_change, np.float32),#dS
	    	np.array(Sy_aquifer, np.float32),#Sy
            aux_head
	    	)
        
        head[:] = aux_head
    
    # calculate change in storage, exact solution
    storage = np.array([0.2, 1.0, 0.1], dtype=float)
    total_change = storage_change*10.0/storage
    answer = head0+total_change
    
    # evaluate the result
    assert np.allclose(head, answer)
    print('GW_SW interactions: Test runs successfully')

if __name__ == '__main__':
	test_gw_sw_interaction()				