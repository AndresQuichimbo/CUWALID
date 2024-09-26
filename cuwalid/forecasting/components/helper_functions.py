import geopy
from geopy.distance import geodesic
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import rasterio
import xarray as xr


"""
A file containing helper functions to assist with the forecasting element

"""

def read_dataset(fname, var_name='tht'):
	# Open the first netCDF file
	# output dataset
	data = xr.open_dataset(fname)
	data = data[var_name]
	return data
	
def resample_dataset(data, mean=True, delt='Y'):
	# calculate climatological mean
	# output an array
	if mean is True:
		data = data.resample(time=delt).mean()
	else:
		data = data.resample(time=delt).sum()	
	return data

def season_name_to_number(season):
	"""This function read a string representing seasons and return a
	list of numbers indicating months
	
	Parameters
	----------
	season : str
		season represented by three capital letters (e.g. "OND")

	Returns
	-------
	list
		list of months
	"""

	if season == "MAM":
		season = [3,4,5]
	elif season == "OND":
		season = [10,11,12]

	return season

def get_season_dataset(data, season):
	# get seasson
	return data.where(data.time.dt.month.isin(season_name_to_number(season)))

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

def get_mask(fmask):
	# output an array
	# get a mask
	mask = rasterio.open(fmask).read(1)
	# mask values for visualisation
	mask = np.array(mask, dtype=float)
	mask[mask <= 0] = np.nan
	mask[mask > 0] = 1.0
	return mask

def bounding_box(center, distance=10):
	lat, lon = center[0], center[1]
	# sw, ne
	bearings = [225, 45]
	origin = geopy.Point(lat, lon)
	bbox = []

	for bearing in bearings:
		destination = geodesic(kilometers=np.sqrt(2)*distance).destination(origin, bearing)
		coords = destination.longitude, destination.latitude
		bbox.extend(coords)
	# xmin, ymin, xmax, ymax
	return bbox
	
def add_scale_bar(ax, length, location=(0.05, 0.05), linewidth=3, text='1 km'):
	"""
	Add a scale bar to a Matplotlib Axes object.
	
	Parameters:
	- ax: The Matplotlib Axes object to add the scale bar to.
	- length: Length of the scale bar in Axes coordinates (0 to 1).
	- location: Tuple indicating the location of the scale bar in Axes coordinates.
	- linewidth: The thickness of the scale bar line.
	- text: A string with the text label for the scale bar.
	"""
	# Transform from Axes coordinates (0-1) to figure coordinates
	trans = ax.transAxes + ax.figure.transFigure.inverted()
	x, y = trans.transform(location)
	
	# Draw the scale bar
	bar = mpatches.Rectangle((x, y), length*100, linewidth/100,
			#transform=ax.figure.transFigure,
			color='black')
	ax.figure.patches.extend([bar])
	
	# Add text annotation for the scale bar
	ax.text(x + length/2, y - linewidth/100 * 2,
		text, ha='center', va='top',
		transform=ax.figure.transFigure
		)

def add_label_features(geodata, fontsize=6, boundbox=None, offset=0,
	fontstyle="normal", halignament="center", alpha=1.0, color="k",
	language="name"):
	
	if len(geodata) > 10:
		geodata = geodata.sample(n=10)
	#print(geodata.columns)
	#print(c)
	for idx, row in geodata.iterrows():
		x_mid, y_mid = row.geometry.centroid.coords[0]

		iname = row[language].split(' ')

		if len(iname) > 2:
			iname = "\n".join(iname)
		else:
			iname = row[language]
		#print(x_mid, y_mid, boundbox, iname)
		if boundbox is not None:
			if (boundbox[0] > x_mid) or (x_mid > boundbox[2]):
				x_mid = None
				iname = None
			if (boundbox[1] > y_mid) or (y_mid > boundbox[3]):
				y_mid = None
				iname = None
		#print(x_mid, y_mid, boundbox)
		#if boundbox is not None:
		#	x_mid = np.max([boundbox[0]+offset, x_mid])
		#	y_mid = np.max([boundbox[1]+offset, y_mid])
		#	x_mid = np.min([boundbox[2]-offset, x_mid])
		#	y_mid = np.min([boundbox[3]-offset, y_mid])
		#print(x_mid, y_mid, boundbox)
		#print(iname)
		if iname is not None:
			plt.text(x_mid+offset, y_mid+offset, s=iname,
				fontsize=fontsize, fontstyle=fontstyle,
				horizontalalignment=halignament, alpha=alpha,
				color=color)