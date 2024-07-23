#import netCDF4
import geopandas as gpd
import xarray as xr
import rioxarray
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.ndimage import gaussian_filter
from rasterio.enums import Resampling

def plot_probabilistic_tercile_forecast(data,
		title="Probabilistic Forecasting", reproject=False,
		fshapefile=None, fmask=None):
	"""This function create a tercile plot
	
	Parameters
	----------
	
	data : dataset
		tercile forecasting datset
	title : str
		specify title for the figure
	
	Return
	------
	
	"""
	# apply mask
	#if fmask is not None:
	#	mask = np.flip(get_mask(fmask), 0)#*np.flip(get_mask(friver), 0)
	#	data = data*mask
	
	# reproject dataset
	if reproject is True:
		data = reproject_dataset(data, oldPP=None, newPP=None)
		
	data = data.where(data > 0.3333, np.nan)
	
	#data[data < 0.3333] = np.nan
	
	tercile = ["AN", "NN", "BN"]
	barloc = [0.0, 0.5, 1.75]
	cmap = ["Blues", "Greens", "Oranges"]
	
	
	fig, ax=plt.subplots(figsize=(7, 8))
	plt.subplots_adjust(#wspace=0.40, hspace=0.40,
						#left=0.075, right=0.97,
						top=0.92, bottom=0.20
						)
						
	#bounds = [40,45,50,55,60,65,70,75,80]
	bounds = [40, 50, 60, 70, 80]
	nbounds = [40,45,50]
	isigma = 0.5
	#for itercile, ibarloc, icmap in zip(var, barloc, cmap):
	#g1 = smooth_dataarray(data[tercile[0]], sigma=isigma).plot(
	g1 = data[tercile[0]].plot(
			x="lon", y="lat",
			vmin=0.30, vmax=0.80,
			cmap=plt.get_cmap(cmap[0], 5),
			ax=ax, add_colorbar=False,
			
			)
	
	#g2 = smooth_dataarray(data[tercile[1]], sigma=isigma).plot(
	g2 = data[tercile[1]].plot(
			x="lon", y="lat",
			vmin=0.35, vmax=0.55,
			cmap=plt.get_cmap(cmap[1], 4),
			ax=ax, add_colorbar=False
			)
	
	#g3 = smooth_dataarray(data[tercile[2]], sigma=isigma).plot(
	g3 = data[tercile[2]].plot(
			x="lon", y="lat",
			vmin=0.30, vmax=0.80,
			cmap=plt.get_cmap(cmap[2], 5),
			ax=ax, add_colorbar=False
			)
	
	if fshapefile is not None:
		boundaries = gpd.read_file(fshapefile)
		
		boundaries.plot(ax=ax,
				facecolor='none',
				#edgecolor=line_colors["Administrative Boundary"],
				#linewidth=line_width["Administrative Boundary"],
				#ls=line_ls["Administrative Boundary"],
				# legend=True, label='Boundaries',
				alpha=1.0
				)
	
	
	axins1_bottom = inset_axes(ax, width="35%", height="5%", loc='lower left',
		bbox_to_anchor=(0, -0.15, 1, 1), bbox_transform=ax.transAxes, borderpad=0.1)
	axins2_bottom = inset_axes(ax, width="20%", height="5%", loc='lower center',
		bbox_to_anchor=(0, -0.15, 1, 1), bbox_transform=ax.transAxes, borderpad=0.1)
	axins3_bottom = inset_axes(ax, width="35%", height="5%", loc='lower right',
		bbox_to_anchor=(0, -0.15, 1, 1), bbox_transform=ax.transAxes, borderpad=0.1)
	
	cbar_fbr = fig.colorbar(g1, ax=ax, cax=axins3_bottom, orientation='horizontal')
	cbar_fbr.set_label('Above-Normal (%)')
	cbar_fbr.set_ticks([i/100.0 for i in bounds])
	cbar_fbr.set_ticklabels(bounds)
	
	
	cbar_fbc = fig.colorbar(g2, ax=ax, cax=axins2_bottom, orientation='horizontal')
	cbar_fbc.set_label('Near-Normal (%)')
	cbar_fbc.set_ticks([i/100.0 for i in nbounds])
	cbar_fbc.set_ticklabels(nbounds)
	
	cbar_fbl = fig.colorbar(g3, ax=ax, cax=axins1_bottom, orientation='horizontal')
	cbar_fbl.set_label('Below-Normal (%)')
	cbar_fbl.set_ticks([i/100.0 for i in bounds])
	cbar_fbl.set_ticklabels(bounds)
	
	ax.set_title(title)
	ax.set_ylabel("Latitude")
	ax.set_xlabel("Longitude")

def plot_deterministic_forecast(data,
		title="Deterministic Forecasting", reproject=False,
		fshapefile=None, fmask=None, plot_anomaly=False):
	"""This function create a tercile plot
	
	Parameters
	----------
	
	data : dataset
		tercile forecasting datset
	title : str
		specify title for the figure
	
	Return
	------
	
	"""
	# apply mask
	if fmask is not None:
		mask = np.flip(get_mask(fmask), 0)#*np.flip(get_mask(friver), 0)
		data = data*mask
	
	# reproject dataset
	if reproject is True:
		data = reproject_dataset(data, oldPP=None, newPP=None)
	
	data = data.where(data < 1.0e100, np.nan)
	
	fig, ax=plt.subplots(1, 2, figsize=(12, 7))
	plt.subplots_adjust(#wspace=0.40, hspace=0.40,
						#left=0.075, right=0.97,
						top=0.92, bottom=0.25
						)
	
	idplot = int(plot_anomaly)
	
	fields = ["average", "anomaly", "Variability"]
	cmap = ["GnBu", "BrBG", "GnBu"]
	
	g1 = data[fields[idplot]].plot(
			x="lon", y="lat",
			#vmin=0.35, vmax=0.55,
			cmap=plt.get_cmap(cmap[idplot], 8),
			ax=ax[0], add_colorbar=False
			)
	
	g2 = data[fields[2]].plot(
			x="lon", y="lat",
			#vmin=0.35, vmax=0.55,
			cmap=plt.get_cmap(cmap[2], 8),
			ax=ax[1], add_colorbar=False
			)
	
	if fshapefile is not None:
		boundaries = gpd.read_file(fshapefile)
		
		boundaries.plot(ax=ax[0],
				facecolor='none',
				#edgecolor=line_colors["Administrative Boundary"],
				#linewidth=line_width["Administrative Boundary"],
				#ls=line_ls["Administrative Boundary"],
				# legend=True, label='Boundaries',
				alpha=1.0
				)
		
		boundaries.plot(ax=ax[1],
				facecolor='none',
				#edgecolor=line_colors["Administrative Boundary"],
				#linewidth=line_width["Administrative Boundary"],
				#ls=line_ls["Administrative Boundary"],
				# legend=True, label='Boundaries',
				alpha=1.0
				)
	
	# Add color bars
	axins1_bottom = inset_axes(ax[0], width="80%", height="5%", loc='lower center',
		bbox_to_anchor=(0, -0.15, 1, 1), bbox_transform=ax[0].transAxes, borderpad=0.1)
		
	axins2_bottom = inset_axes(ax[1], width="80%", height="5%", loc='lower center',
		bbox_to_anchor=(0, -0.15, 1, 1), bbox_transform=ax[1].transAxes, borderpad=0.1)
		
	cbar_fbc = fig.colorbar(g1, ax=ax[0], cax=axins1_bottom, orientation='horizontal')
	cbar_fbc.set_label(fields[idplot])
	#cbar_fbc.set_ticks([i/100.0 for i in nbounds])
	#cbar_fbc.set_ticklabels(nbounds)
	
	cbar_fbc = fig.colorbar(g2, ax=ax[0], cax=axins2_bottom, orientation='horizontal')
	cbar_fbc.set_label('Standard Deviation')
	#cbar_fbc.set_ticks([i/100.0 for i in nbounds])
	#cbar_fbc.set_ticklabels(nbounds)
	
	# add titles and axis lables
	ax[0].set_title(title+"\n"+fields[idplot])
	ax[0].set_ylabel("Latitude")
	ax[0].set_xlabel("Longitude")
	
	ax[1].set_title(title+"\n"+"Standard Deviation")
	ax[1].set_ylabel("Latitude")
	ax[1].set_xlabel("Longitude")
	
	
# Function to smooth a 2D xarray DataArray
def smooth_dataarray(dataarray, sigma=2):
    """
    Smooth a 2D xarray DataArray using a Gaussian filter.
    
    Parameters:
    - dataarray: xarray.DataArray, the input 2D data array
    - sigma: float, standard deviation for Gaussian kernel
    
    Returns:
    - smoothed_data: xarray.DataArray, the smoothed 2D data array
    """
    smoothed_data = gaussian_filter(dataarray, sigma=sigma)
    return xr.DataArray(smoothed_data, dims=dataarray.dims,
			coords=dataarray.coords)

	
def reproject_dataset(data, oldPP=None, newPP=None):
	"""Transform projection system
	oldPP and newPP have to be defined first
	
	Parameters
	----------
	Data:	Dataset
	
	Returns
	-------
	Data:	Dataset
	"""
	
	if oldPP is None:
		#oldfPP = (#rasterio.crs.CRS.from_string(
		oldPP = "+proj=laea +lat_0=5 +lon_0=20 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
		#)
		
	# define current projection (input)
	if newPP is None:
		newPP = 'EPSG:4326'
	
	
	# check if projection is in ERSG format
	if len(oldPP) > 11:
		oldPP = rasterio.crs.CRS.from_string(oldPP)
	
	# reprojec dataset
	data = data.rename({'lon': 'x', 'lat': 'y'})  # new method
	data = data.rio.write_crs(oldPP) # write crs
	data = data.rio.reproject(newPP,
				#resampling=Resampling.nearest
				) # reproject the file
	data = data.rename({'x': 'lon', 'y': 'lat'})  # new method
	
	return data

def get_label_variable(var):
	field_labels = {
		"pre" : 'Precipitation [mm/month]',
		"pet" : 'Potential ET. [mm/month]',
		"aet" : 'Actual ET. [mm/month]',
		"tht" : 'Soil moisture [--]',
		"inf" : 'Infiltration [mm/month]',
		"run" : 'Overland Flow [mm/month]',
		"tls" : 'Trans. Losses [mm/month]',
		"fch" : 'Focused Rch. [mm/month]',
		"rch" : 'Diffuse Rch. [mm/month]',
		"ghd" : 'GW Discharge [mm/month]',
		"dis" : 'Flow channel [m3/month]',
		"twsc": "Total Water storage \n Anomalies [mm/month]",
		"wrsi": "Water Requirement Satisfaction \n Index [-]",
		
		}
	return field_labels[var]
	
def get_mask(fmask):
	# output an array
	# get a mask
	mask = rasterio.open(fmask).read(1)
	# mask values for visualisation
	mask = np.array(mask, dtype=float)
	mask[mask <= 0] = np.nan
	mask[mask > 0] = 1.0
	return mask