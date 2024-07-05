import sys
import os
import numpy as np
from models.dryp.components.DRYP_flow_accum import watershed
from models.dryp.components.DRYP_watershed import get_watershed_area
from landlab import RasterModelGrid
import rasterio



## run basin delineation
#fname = "D:/HAD/model/input/HAD_DEM_utm_mm.asc"
#fdir = "D:/HAD/model/input/HAD_flowdir_land_utm.asc"
#
## delineate basin
#
## get raster properties
#ncols, nrows, cellsize = get_raster_properties(fname)
#
#dem = read_raster(fname)
#flowDir = read_raster(fdir)
##print(len(dem))
#basinlabel = ['Juba', 'Shabelle', 'Tana']
#
#for ipoint, ibasinlabel in zip([2295740, 2765662, 1476629], basinlabel):
#	outlet = np.zeros_like(dem, dtype=int)
#	#outlet[1476629] = 1
#	outlet[ipoint] = 1


def calc_areas(path_model):
	"""Thiis function call the DRYP calculate areas function
	
	Parameters
	----------
	path_model : str
		filename of the model paramter file

	Examples
	--------
	>>> from DRYP_grid_calculate_area import calc_areas
	>>> filename = "test_input.txt"
	>>> calc_area(filename)
	"""
	get_area_watershed(path_model)

if __name__ == '__main__':
	calc_areas(sys.argv[1])