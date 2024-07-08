#import pyproj as pp
import numpy as np
import rasterio
""" component to reproject dataset from the native format to
Landlab reference system when dataset have different reference
systems
WARING: Do not activat this component if the reference system
is the new defined
"""
#lat = rg.node_y.reshape(rg.shape)
#lon = rg.node_x.reshape(rg.shape)
#grid_shape = np.array(rg.shape)
#xaxis = rg.node_x[:grid_shape[1]]
#yaxis = np.linspace(np.min(rg.node_y), np.max(rg.node_y),num=grid_shape[0])

# change projection
# define new projection (output) #!with.PYPROJ.library
newPP = rasterio.crs.CRS.from_string(
"+proj=laea +lat_0=5 +lon_0=20 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)

# define current projection (input)
oldPP = 'EPSG:4326'

# transform from old CRS to new CRS
#old_new_pp = pp.Transformer.from_proj(oldPP, newPP)

def reproject_dataset(data, oldPP, newPP):
	"""Transform projection system
	oldPP and newPP have to be defined first
	
	Parameters
	----------
	Data:	Dataset
	
	Returns
	-------
	Data:	Dataset
	"""
	# check if projection is in ERSG format
	if len(newPP) > 11:
		newPP = rasterio.crs.CRS.from_string(newPP)
	
	# reprojec dataset
	data = data.rename({'lon': 'x', 'lat': 'y'})  # new method
	data = data.rio.write_crs(oldPP) # write crs
	data = data.rio.reproject(newPP) # reproject the file
	data = data.rename({'x': 'lon', 'y': 'lat'})  # new method
	
	return data

def reproject_dataset_old(data, keys):
	""" reproject netcdf files to a new reference system
	the new reference sysitem has to be defined obove

	Parameters
	----------
	data:	netcdf file read as xarray
	keys:	label of variables coordinata "longitude" and "latitude"

	Returns
	-------
	data:	dataset with reprojected coordinates
	"""
	# create raster grid of current projection
	x_old, y_old = np.meshgrid(data[keys[0]].values, data[keys[1]].values)
	
	# reproject data
	x_new, y_new = old_new_pp.transform(x_old, y_old, radians=False)
	
	# change to latitude longitude arrays
	data[keys[0]] = x_new[0][:]
	data[keys[1]] = y_new[:,0]

	return data


