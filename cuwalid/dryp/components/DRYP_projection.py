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
    Transform projection system
    oldPP and newPP have to be defined first

    Parameters
    ----------
    data: xarray.Dataset
    oldPP: original CRS
    newPP: target CRS

    Returns
    -------
    data: xarray.Dataset with reprojected coordinates
    """

    # Check if projection is in ERSG format
    if isinstance(newPP, str) and len(newPP) > 11:
        newPP = rasterio.crs.CRS.from_string(newPP)

    # Handle different coordinate naming formats
    if 'lat' in list(data.coords):
        data = data.rename({'lat': 'y', 'lon': 'x'})
    elif 'LAT' in list(data.coords):
        data = data.rename({'LAT': 'y', 'LON': 'x'})
    elif 'latitude' in list(data.coords):
        data = data.rename({'latitude': 'y', 'longitude': 'x'})
    elif 'Y' in list(data.coords):
        data = data.rename({'Y': 'y', 'X': 'x'})
    elif 'projection_y_coordinate' in list(data.coords):
        data = data.rename({'projection_y_coordinate': 'y', 'projection_x_coordinate': 'x'})
    elif 'x' in list(data.coords):
        pass  # already correct
    else:
        raise ValueError("❌ Coordinate names not recognized. Please rename them to match x/y.")

    # Reproject
    data = data.rio.write_crs(oldPP)
    data = data.rio.reproject(newPP)

    # Rename back if needed (optional; depends on downstream expectations)
    data = data.rename({'x': 'lon', 'y': 'lat'})

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


