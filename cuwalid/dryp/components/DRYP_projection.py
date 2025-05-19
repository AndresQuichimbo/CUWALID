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
    """
    Transform projection system.
    oldPP and newPP have to be defined first.

    Parameters
    ----------
    data : xarray.Dataset
        The input dataset with coordinate variables.
    oldPP : str or CRS
        The original projection (EPSG code or CRS object).
    newPP : str or CRS
        The new projection to transform to (EPSG code or CRS object).

    Returns
    -------
    data : xarray.Dataset
        Reprojected dataset.
    """
    # Check if projection is in ERSG format
    if isinstance(newPP, str) and len(newPP) > 11:
        newPP = rasterio.crs.CRS.from_string(newPP)

    # Rename coordinates based on known patterns
    if 'lat' in list(data.coords):
        data = data.rename({'lat': 'y', 'lon': 'x'})
        revert = {'x': 'lon', 'y': 'lat'}
    elif 'LAT' in list(data.coords):
        data = data.rename({'LAT': 'y', 'LON': 'x'})
        revert = {'x': 'LON', 'y': 'LAT'}
    elif 'latitude' in list(data.coords):
        data = data.rename({'latitude': 'y', 'longitude': 'x'})
        revert = {'x': 'longitude', 'y': 'latitude'}
    elif 'Y' in list(data.coords):
        data = data.rename({'Y': 'y', 'X': 'x'})
        revert = {'x': 'X', 'y': 'Y'}
    elif 'x' in list(data.coords) and 'y' in list(data.coords):
        revert = {'x': 'x', 'y': 'y'}  # already in correct format
    else:
        raise ValueError("❌ ERROR: coordinate names not recognized. Please rename them to use standard forms like 'lon/lat' or 'x/y'.")

    # Apply projection
    data = data.rio.write_crs(oldPP)
    data = data.rio.reproject(newPP)

    # Rename back to original names
    data = data.rename(revert)

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


