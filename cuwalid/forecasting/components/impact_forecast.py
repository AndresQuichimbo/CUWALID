# Import libraries from local repository
import os
import geopy
from geopy.geocoders import Nominatim
from matplotlib import pyplot as plt
import osmnx as ox
import geopandas as gpd
import xarray as xr
import rioxarray
import rasterio
import numpy as np
import pandas as pd
from cmcrameri import cm
from matplotlib.colors import ListedColormap
import sys
import matplotlib.patches as mpatches
from matplotlib_scalebar.scalebar import ScaleBar
from geopy.distance import geodesic
from shapely.geometry import box
from matplotlib.patches import Rectangle
import matplotlib.patheffects as path_effects
#sys.path.append('C:/Users/Edisson/Documents/GitHub/DRYPv2.0.1')
#sys.path.append("/user/home/km19051/DRYPv2.0.1")
from cuwalid.forecasting.components.helper_functions import add_label_features, bounding_box, get_mask, get_season_dataset, read_dataset, resample_dataset
from cuwalid.forecasting.components.map_properties import *
from cuwalid.forecasting.components.default_parameter_dataset import *
from cuwalid.forecasting.components.read_paths import *

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
"""
This is an example plot, the generated map does not
represent the definitive value

TO INSTALL PACKAGES UES THE FOLLOWING CODE
In the anaconda prompt/environment (console)
pip install <package>

example: pip install osmnx

"""

def plot_map(plot_scale="Zoom",
			region="region",
			country_name="Kenya",
			place_name="Burat",
			place_code=29,
			iseason="OND",
			iwater_status="Groundwater",
			iyear=2010,
			ilanguage="English",
			output_dir=None,
			netcdf_path=None,
			threshold_path=None,
			mask_path=None,
			river_path=None,
			fname_output=None,
			place_code_field=False,
			shape_path=None):
	"""Plot maps
	
	Parameters:
	-----------
	plot_scale : string
		default Zoom
	region="region",
	country_name="Kenya",
	place_name="Burat",
	place_code=29,
	iseason="OND",
	iwater_status="Groundwater",
	iyear=2010,
	ilanguage="English",
	output_dir=None,
	netcdf_path=None,
	threshold_path=None,
	mask_path=None,
	river_path=None,
	fname_output=None,
	place_code_field : bool
		Name of shapefile attribute to use as poligon, default is False,
		it will use the place name,
	shape_path
	
	Returns:
	--------
	
	
	"""
	# use this function to cleam some variables and names in the code
	paths_all = read_dataset(plot_scale)

	if shape_path == None:
		shapefile_country = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', shapefile_country_dic[region]))
		shapefile_county = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', shapefile_county_dic[country_name.lower()]))
		# TODO: rewrite
		if plot_scale == "Wards":
			shapefile_wards = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', shapefile_wards_dic[country_name.lower()]))
	else:
		if plot_scale == "County":
			shapefile_county = shape_path
		elif plot_scale == "Wards":
			shapefile_wards = shape_path


	rivers_shapefile = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', rivers_shape_path))


	# load dataset of model outputs
	#netcdf_path = "forecasting_dataset/HAD/output/HAD_IMERGba_sim0_"+ str(iyear)+"_grid.nc"
	#netcdf_path = 'forecasting_dataset/HAD/output/HAD_IMERG_sim_ini_grid.nc'
	if netcdf_path == None:
		netcdf_path = default_netcdf.replace("YYYY", str(iyear))
	else:
		if "YYYY" in netcdf_path:
			netcdf_path = netcdf_path.replace("YYYY", str(iyear))
		else:
			print("The netcdf_path requires text 'YYYY' to replace with the the year being processed")
			sys.exit(1)

	if iwater_status == "Groundwater":
		var = "twsc"
		# If netcdf path is None use the default
		if netcdf_path == None:
			print("Using default netcdf path")
			netcdf_path = "forecasting_dataset/HAD/output/HAD_IMERGba_sim0_"+ str(iyear)+ "_grid_" + var + ".nc"
		else:
			netcdf_path.replace("YYYY", str(iyear))

	# load dataset for thresholds
	#nc_path_threshold = "forecasting_dataset/HAD/postpp/HAD_IMERGb_D2E_sim_" + iseason + "_quantiles.nc"
	if threshold_path == None:
		print("Using default threshold path")
		nc_path_threshold = "forecasting_dataset/HAD/postpp/HAD_IMERGb_D2E_sim_SSS".replace("SSS", iseason)
	else:
		if "SSS" in threshold_path:
			nc_path_threshold = threshold_path.replace("SSS", iseason)

		else:
			print("The threshold_path requires text 'SSS' to replace with the the year being processed")
			sys.exit(1)

	if (iwater_status == "Surface") or (iwater_status == "Flood"):
		nc_path_threshold = nc_path_threshold + "_flow_quantiles.nc"
	else:
		nc_path_threshold = nc_path_threshold + "_quantiles.nc"

	if mask_path == None:
		print("Using default mask path")
		fmask = "forecasting_dataset\HAD\input_model\HAD_mask_utm_m.asc"
	else:
		fmask = mask_path
	
	if river_path == None:
		print("Using default river path")
		friver =  "forecasting_dataset\HAD\input_model\HAD_riv_length_utm.asc"
	else:
		friver = river_path

	# Changing the country name depending on the country plotting. e.g. "kenya": "county"
	name_field_shp["County"] = name_field_county_shp[country_name.lower()]
	
	# =========================================================
	# DO NOT CHANGE FROM THIS LINE
	# =========================================================
	# SPECIFY projection
	# define new projection (output) #!with.PYPROJ.library
	netcdfPP = rasterio.crs.CRS.from_string(
	"+proj=laea +lat_0=5 +lon_0=20 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
	)
	# define current projection (input)
	mapPP = 'EPSG:4326'
	# ===========================================================
	# READ DATA FROM REGIONAL DATASET FROM LOCAL REPO
	# ----------------------------------------------------------
	# load shapefiles
	# name field for shapefile

	#name_field_name = {
	#	"Zoom" : name_field_county_shp,
	#	"County" : name_county_shp,
	#	#"Country" : name_field_county_shp,
	#	}
	#
	#name_field_code = {
	#	"Zoom" : name_field_county_shp,
	#	"County" : code_county_shp,
	#	#"Country" : name_field_county_shp,
	#	}
	
	## select the field to use as polygon attribute
	#if place_code_field is False:
	#	iname_field_shp = name_field_name[plot_scale]
	#else:		
	#	iname_field_shp = name_field_code[plot_scale]

	## additional files to plot as well as boundaries)
	## Select the ward that is requiested to plot
	#if (plot_scale == "Zoom") or (plot_scale == "Ward"):
	#	wards = gpd.read_file(shapefile_wards)
	#	#wards = wards[(wards["IEBC_WARDS"] == place_name)]
	#elif plot_scale == "County":
	#	wards = gpd.read_file(shapefile_county)
	#	#wards = wards[(wards["county"] == place_name)]
	#elif plot_scale == "Country":
	#	wards = gpd.read_file(shapefile_county)
	#	#wards = wards[(wards["NAME"] == place_name)]

	wards = gpd.read_file(paths_all.fname_place)

	if place_code_field is False:
		wards = wards[(wards[paths_all.iname_field_shp[country_name.lower()]] == place_name)]
	else:
		wards = wards[(wards[paths_all.iname_field_shp] == place_code)]

	# select polygon to use as mask
	polygon = wards["geometry"].iloc[0]

	# Get the street network graph for walking
	# Load data from shapefiles
	rivers = gpd.read_file(rivers_shapefile)
	#settlements = gpd.read_file(settlements_shapefile)
	#facilities = gpd.read_file(facilities_shapefile)

	# Clip rivers and settlements to the Burat boundary
	# Ensure the CRS of both the shapefile and NetCDF file match
	rivers = gpd.clip(rivers, polygon)

	#settlements = gpd.clip(settlements, polygon)


	# ----------------------------------------------------------
	# GET DATA FROM OPEN STREET MAP (osm) =====================
	# ----------------------------------------------------------
	# Get OSM data from point location and area extend
	if plot_scale == "Zoom":
		bbox = bounding_box(wards_data[place_name], distance=10) # in km
		bbox = box(bbox[0], bbox[1], bbox[2], bbox[3])
		# Create a GeoDataFrame
		extend = gpd.GeoDataFrame({'id': [1]},
			geometry=[bbox], crs="EPSG:4326")["geometry"]
		polygon = extend.iloc[0]

	# get roads and street from OSM
	if plot_obj_id[plot_scale]["Main Roads"] is True:
		try:
			# Query amenities using the latest OSMnx version (0.18.1 as of 2024-02-21)
			highway = ox.features.features_from_polygon(polygon, tags={'highway': True})
			highway.crs = mapPP
			highway = highway.to_crs(netcdfPP)#ds.rio.crs)
		except:
			print("error with highway")

	# read point locations
	read_oms = False
	for ipoint in points:
		if plot_obj_id[plot_scale][ipoint] is True:
			read_oms = True

	if read_oms is True:
		amenities = ox.features.features_from_polygon(polygon, tags={'amenity': True})
		amenities = amenities.loc["node"]
		amenities.crs = mapPP
		amenities = amenities.to_crs(netcdfPP)

	# read point locations
	read_oms = False
	for ipoint in aeroway_obj:
		if plot_obj_id[plot_scale][ipoint] is True:
			read_oms = True

	if read_oms is True:
		try:
			aeroway = ox.features.features_from_polygon(polygon, tags={'aeroway': True})
			aeroway = aeroway[aeroway["name"].notnull()]
			#aeroway = aeroway.loc["node"]
			aeroway.crs = mapPP
			aeroway = aeroway.to_crs(netcdfPP)
			aeroway = aeroway.centroid
		except:
			print("no airports found")
			aeroway = []

	# read waterways
	read_oms = False	
	for iwater in water_objects:
		if plot_obj_id[plot_scale][iwater] is True:
			read_oms = True

	if read_oms is True:
		try:
			water = ox.features.features_from_polygon(polygon, tags={'waterway': True})
			water.crs = mapPP
			water = water.to_crs(netcdfPP)
		except:
			print("error with waterway")

	# read natural reserves
	read_oms = False	
	for iwater in water_objects:
		if plot_obj_id[plot_scale][iwater] is True:
			read_oms = True

	if read_oms is True:
		try:
			leisure = ox.features.features_from_polygon(polygon, tags={'leisure': True})
			leisure.crs = mapPP
			leisure = leisure.to_crs(netcdfPP)

		except:
			print("error with leisure")

	# read urban centres
	read_oms = False	
	for iplaces in places_obj:
		if plot_obj_id[plot_scale][iplaces] is True:
			read_oms = True

	if read_oms is True:
		bbox = wards.total_bounds
		bbox = box(bbox[0], bbox[1], bbox[2], bbox[3])
		polygon_bnd = gpd.GeoDataFrame({'id': [1]},
			geometry=[bbox], crs="EPSG:4326")["geometry"].iloc[0]

		places = ox.features.features_from_polygon(polygon_bnd, tags={'place': True})
		#places = ox.features.features_from_polygon(polygon, tags={'place': True})
		places = places.loc['node']
		places.crs = mapPP
		places = gpd.clip(places, polygon_bnd)
		places = places.to_crs(netcdfPP)
	
	#places.plot()
	
	# admininstrative borders
	if plot_obj_id[plot_scale]["Administrative Boundary"] is True:
		bbox = wards.total_bounds
		bbox = box(bbox[0], bbox[1], bbox[2], bbox[3])
		polygon_bnd = gpd.GeoDataFrame({'id': [1]},
			geometry=[bbox], crs="EPSG:4326")["geometry"].iloc[0]

		bnd_admin = ox.features.features_from_polygon(polygon_bnd, tags={'boundary': True})
		bnd_admin = gpd.clip(bnd_admin, polygon_bnd)
		bnd_admin = bnd_admin.loc['relation']
		bnd_admin.crs = mapPP
		bnd_admin = bnd_admin.to_crs(netcdfPP)

	# Assign the CRS to the GeoPandas DataFrame
	wards.crs = mapPP
	wards = wards.to_crs(netcdfPP)#ds.rio.crs)
	rivers.crs = mapPP
	rivers = rivers.to_crs(netcdfPP)

	# get map extend
	if plot_scale == "Zoom":
		extend.crs = mapPP
		extend = extend.to_crs(netcdfPP)
		extend = extend.total_bounds
	else:
		extend = wards.total_bounds
	#print(wards.info())
	# =========================================================
	# READ MODEL DATASETS AND THRSHOLDS
	# =========================================================
	# especify water variable to read and plot
	var = water_var[iwater_status]

	# READ THRESHOLDS DATASET ---------------------------------
	# Open dataset of thrsholds
	ds_thrshold = read_dataset(nc_path_threshold, var_name=var)
	ds_thrshold = ds_thrshold.rio.write_crs(netcdfPP)

	# READ MODEL OUTPUTS ---------------------------------------
	# Open dataset of model outputs
	ds = read_dataset(netcdf_path, var_name=var)

	# Apply mask to datasets
	if var == "dis":
		mask = np.flip(get_mask(fmask), 0)*np.flip(get_mask(friver), 0)
		#ds = ds*mask	

	# Write projection on dataset
	ds = ds.rio.write_crs(netcdfPP)
	# reprojec dataset
	#ds = reproject_dataset(ds, oldPP, newPP)

	# get season average
	if var == 'dis':
		ds = get_season_dataset(ds, iseason)
		if iwater_status == "Surface":
			ds = xr.where(ds < ds_thrshold.time[1], 1, 0)
			ds = ds.resample(time="Y").sum()*mask
		else:
			ds = ds.resample(time="Y").max()*mask
	else:
		ds = resample_dataset(
			get_season_dataset(ds, iseason),
			)

	# convert mask into xarray dataset
	#mask = reproject_dataset(mask, oldPP, newPP)

	# reprojec dataset
	ds = ds.rename({'lon': 'x', 'lat': 'y'})
	ds_thrshold = ds_thrshold.rename({'lon': 'x', 'lat': 'y'})
	#ds_thrshold = reproject_dataset(ds_thrshold, oldPP, newPP)

	# ==========================================================
	# FORECASTING ANALYSIS
	# ==========================================================
	# FILTER DATA BETWEEN THRSHOLDS ----------------------------
	# THIS SECTION WILL BE UPDATED WHEN FORECASTING WILL BE
	# AVAILABLE

	if (plot_scale == "County") or (plot_scale == "Country"):
		# Clip the data model
		ds = ds.rio.clip(wards.geometry.values, wards.crs,
					  drop=False
					  )

		# Clip data thresholds
		ds_threshold = ds_thrshold.rio.clip(
					wards.geometry.values, wards.crs,
					drop=False)

		# Clip the mask
		#mask1 = mask.rio.clip(wards.geometry.values, wards.crs,
		#		drop=False)

	# create mask
	mask = ds.values[0]
	mask[mask>0] = 1

		## Calculate 1st and 3rd quantiles along the time dimension
		#q1 = ds_clipped_threshold.time[0]#(0.25, dim='time')
		#q3 = ds_clipped_threshold.time[2]#(0.75, dim='time')

		##ds_clipped_threshold.plot(x="lon", y="lat", col="time")#, col_wrap=12)
		##plt.show()
		#
		## FILTER DATA BETWEEN THRSHOLDS ---------------------------
		## Reassign values based on quantile thresholds
		##rescaled = xr.where(ds_clipped < q1, -1,
		##	xr.where(ds_clipped > q3, 1, ds_clipped*0)
		##	)
		#if iwater_status == "Surface":
		#	rescaled = xr.where(ds_clipped < 3, 0.0, -1.5)*mask
		#elif iwater_status == "Flood":
		#	rescaled = xr.where(ds_clipped < q3, -1.5, ds_clipped*0.0)#*mask
		#else:
		#	rescaled = xr.where(ds_clipped < q1, -1.5, ds_clipped*0.0)

	#else: # for zoomed values
	q1 = ds_thrshold.time[0]
	q3 = ds_thrshold.time[2]

	# Reassign values based on quantile thresholds
	if iwater_status == "Surface":
		rescaled = xr.where(ds < 3, 0.0, -1.5)*mask
	elif iwater_status == "Flood":
		rescaled = xr.where(ds < q3, -1.5, ds*0.0)*mask
	else:
		rescaled = xr.where(ds < q1, -1.5, ds*0.0)#*mask

	# =========================================================
	# =========================================================
	# CREATE FIGURE - MAP
	# =========================================================
	# calulate ration of figure heigth/width
	ratio_bw = np.abs((extend[1]-extend[3])/(extend[0]-extend[2]))
	if ratio_bw <= 1.5:
		ratio_bw = ratio_bw*1.2
	
	# figure size
	figure_width = 5.0*plot_scale_id[plot_scale]
	figure_height = 7.0*ratio_bw*plot_scale_id[plot_scale]
	
	# Create the base map
	fig, ax = plt.subplots()
	fig.set_size_inches(figure_width, figure_height)
						#7.0*ratio_bw*plot_scale_id[plot_scale])

	# mask values outside the map extend
	time_plot = 0
	#mask = rescaled.isel(time=time_plot).values
	#mean_value = rescaled.isel(time=time_plot).mean()

	# aggregate data within the polygon (ward)
	#rescaled.loc[rescaled.time[time_plot]] = mean_value.values*mask

	# select colors 
	cmap = ListedColormap(var_colour[iwater_status])

	# Example: plot the first time step
	im = rescaled.isel(time=time_plot).plot(ax=ax,
				levels=[-2.0, -1.0, 1.0],#, 2.0],
				cmap=cmap, alpha=0.8,
				add_colorbar=False
				)

	# Add river layers from other datasets
	#rivers.plot(ax=ax, color='#0099ff', label='Rivers')

	# plot water bodies and rivers
	# plot only when discharge is ploted
	if var != "dis":
		for iwater in water_objects:
			if plot_obj_id[plot_scale][iwater] is True:
				water_filter = water[water['waterway'].isin(water_body[iwater])]
				water_filter.plot(ax=ax,
					#marker=point_marker[ipoint],
					#color=water_color[iwater],
					edgecolor=water_color[iwater],
					linewidths=water_lw[iwater],
					facecolor='none',#water_color[iwater],
					#markersize=0.0*marker_size[ipoint],
					label=iwater+ "\n" + language_labels["Swahili"][iwater],
					path_effects=[path_effects.withStroke(
							linewidth=water_lw[iwater]*1.5, foreground='w')]
					)

	# plot natural reserves
	for ileisure in leisure_objects:
		if plot_obj_id[plot_scale][ileisure] is True:
			try:
				leisure_filter = leisure[leisure['leisure'].isin(leisure_body[ileisure])]
			
				leisure_filter.plot(ax=ax,
					#color=water_color[iwater],
					#marker=point_marker[ipoint],
					edgecolor=leisure_color[ileisure],
					linewidths=0.1,
					facecolor='none',#leisure_color[ileisure],
					#markersize=0.0*leisure_size[ipoint],
					label=ileisure+ "\n" + language_labels["Swahili"][ileisure],
					alpha=0.5,
					)
			

				# add labels
				# Filter edges to reduce the number of labels (optional)
				leisure_filter = leisure_filter[leisure_filter["name"].notnull()]#.sample(n=50)

				# Annotate the plot with street names
				add_label_features(leisure_filter, boundbox=extend,
					#language=language_map[ilanguage],
					)
			except:
				print("error with leisure filter")

	# plot layers from Open Street Map
	if plot_obj_id[plot_scale]["Small Roads"] is True:		
		try:
			highway.plot(ax=ax,
						linewidth=line_width["Small Roads"],
						edgecolor=line_colors["Small Roads"],
						facecolor='none',
						label='Small Roads',
						alpha=0.2)
		except:
			print("error with highway")

	# plot main roads			
	if plot_obj_id[plot_scale]["Main Roads"] is True:
		try:
			highway[highway['highway'].isin(highway_filter)].plot(ax=ax,
						linewidth=line_width["Main Roads"],
						edgecolor=line_colors["Main Roads"],
						facecolor='none',
						label='Main Roads'+ "\n" + language_labels["Swahili"]["Main Roads"],
						alpha=1.0,
						)
		except:
			print("error with highway")

	# print label of admin boundaries
	if plot_obj_id[plot_scale]["Administrative Boundary"] is True:
		#boundary_filter = bnd_admin[bnd_admin['admin_level'].notnull()]
		boundary_filter = bnd_admin[bnd_admin['admin_level'].isin(["4"])]
		# add labels
		add_label_features(boundary_filter, boundbox=extend, #, offset=1000)
			fontsize=12.5, fontstyle="italic", halignament="center", alpha=0.7,
			language=language_map[ilanguage], #color="gray"
			)
	#print(boundary_filter)
	#print(boundary_filter.info())	
	# Plot the original polygon (boundaries)
	wards.plot(ax=ax, facecolor='none',
			edgecolor=line_colors["Administrative Boundary"],
			linewidth=line_width["Administrative Boundary"],
			ls=line_ls["Administrative Boundary"],
			# legend=True, label='Boundaries',
			alpha=1.0
			)

	# Add point attributes
	#if plot_scale != "Country":
	for ipoint in points:
		if plot_obj_id[plot_scale][ipoint] is True:
			points_filter = amenities[amenities['amenity'].isin(points_ids[ipoint])]

			if len(points_filter) > 10:
				points_filter = points_filter.sample(n=10)

			points_filter.plot(ax=ax,
				color=point_color[ipoint],
				marker=point_marker[ipoint],
				edgecolor='none',
				#linewidths=0.1,
				facecolor=point_color[ipoint],
				markersize=marker_size[ipoint],
				label=ipoint+ "\n" + language_labels["Swahili"][ipoint],
				)
	# Add point attributes
	#if plot_scale != "Country":
	for ipoint in aeroway_obj:
		if plot_obj_id[plot_scale][ipoint] is True:
			if len(aeroway) > 0:
				aeroway.plot(ax=ax,
					color=aeroway_color[ipoint],
					marker=aeroway_marker[ipoint],
					edgecolor="none",#aeroway_color[ipoint],
					linewidths=0.1,
					facecolor=aeroway_color[ipoint],
					markersize=aeroway_size[ipoint],
					label=ipoint + "\n" + language_labels["Swahili"][ipoint],
					)

	# Add point attributes
	#if plot_scale != "Country":
	for iplaces in places_obj:
		if plot_obj_id[plot_scale][iplaces] is True:
			place_filter = places[places['place'].isin(place_ids[iplaces])]

			if len(place_filter) > 10:
				place_filter = place_filter.sample(n=10)

			place_filter.plot(ax=ax,
				color=place_color[iplaces],
				marker=place_marker[iplaces],
				edgecolor="none",
				linewidths=0.1,
				facecolor=place_color[iplaces],
				markersize=place_size[iplaces],
				label=iplaces + "\n" + language_labels["Swahili"][iplaces],
				)

			try:
				add_label_features(place_filter, boundbox=extend, #, offset=1000)
					fontsize=8, fontstyle="italic", offset=1000,
					halignament="left", #alpha=0.7,
					language=language_map[ilanguage], #color="gray"
					)
			except:
				print("error with add_label_features")

	# MAP TITLE ----------------------------------------
	# Configure and display the map
	plt.title(#"Map of "+ place_name + "" + ", Kenya\n"+
		# English
		#variable[iwater_status]+ '\n OND - YYYY' #+
		variable[iwater_status] + " in " + place_name +"\n"+
		season_name[iseason] + " - " + "YYYY" + "\n"+
		# Swahili
		language_labels["Swahili"][iwater_status] + "-" +
		place_name +"\n"+
		language_labels["Swahili"][iseason] + " \n " + "YYYY"
		#str(pd.to_datetime(rescaled.time.values[time_plot]).year)
		)

	# MAP LEGEND ----------------------------------------------
	# Prepare additional legend entry
	boundary_line, = plt.plot([], [], # Invisible in plot, visible in legend
				color=line_colors["Administrative Boundary"],
				ls=line_ls["Administrative Boundary"],
				label='Boundary\nMpaka',
				)  

	#rectangle_patch = mpatches.Patch(color='green', alpha=0.5, label='Rectangle patch')

	## Update legend
	#legend.remove()  # Remove the old legend
	ncol_legend = 2
	if ratio_bw > 1.5:
		ncol_legend = 1
	first_legend = ax.legend(#all_lines, labels,
			bbox_to_anchor=(0.0, 0),
			loc=2,
			frameon=False,
			title="Geography\nVipengele vya kijiografia",
			ncols=ncol_legend
			)

	# Add the legend manually to the Axes.
	ax.add_artist(first_legend)

	# ADD SECOND LEGEND
	# Add a patch to the plot
	# Step 2: Create a patch for the legend
	rect_patches = []
	for icolor in var_colour[iwater_status]:
		rect_patches.append(mpatches.Patch(color=icolor))
	#for id_object in leisure_objects:
	#	rect_patches.append(mpatches.Patch(color=leisure_color[id_object]))

	label_patches = status[iwater_status]# + leisure_objects

	# add legend
	ax.legend(handles=rect_patches, labels=label_patches,
			bbox_to_anchor=(1.0, 0),
			loc=1, borderaxespad=0.,
			title=variable[iwater_status]+ "\n" +
						language_labels["Swahili"][iwater_status],
			frameon=False)


	#add_scale_bar(ax, 0.1, location=(0.95, 0.95), linewidth=5, text='10 km')
	scalebar = ScaleBar(1, length_fraction=0.0254) # 1 pixel = 0.2 meter
	plt.gca().add_artist(scalebar)

	# add label to axis
	#plt.xlabel("Longitude")
	#plt.ylabel("Latitude")

	# switch off axis		
	if (plot_scale == "Zoom") or (plot_scale == "Ward"):
		ax.set(yticklabels=[])
		ax.tick_params(left=False)  # remove the ticks
		ax.set(xticklabels=[])
		ax.tick_params(bottom=False)  # remove the ticks
	else:
		plt.axis('off')


	plt.xlim([extend[0], extend[2]])
	plt.ylim([extend[1], extend[3]])

	plt.ylabel("")
	plt.xlabel("")
	plt.tight_layout()
	
	# ADD LOCATION PLOT ===========================================
	ax2 = fig.add_axes([0.80, 0.70, #location: x, y
		0.4*0.5,# axes width,
		0.4*0.7*ratio_bw # axes height
		]
		)
	ax2.set_title("Location")
	country = gpd.read_file(shapefile_country)
	country.crs = mapPP
	country = country.to_crs(netcdfPP)#ds.rio.crs)
	
	country.plot(ax=ax2, facecolor="none",
			edgecolor="k",
			linewidth=0.5,#line_width["Administrative Boundary"],
			#ls=line_ls["Administrative Boundary"],
			# legend=True, label='Boundaries',
			alpha=1.0
			)
	wards.plot(ax=ax2, facecolor='k',
			edgecolor=None,
			#linewidth=line_width["Administrative Boundary"],
			#ls=line_ls["Administrative Boundary"],
			# legend=True, label='Boundaries',
			alpha=1.0
			)
	#ax2.set_ylabel("")
	#ax2.set_xlabel("")
	ax2.axis('off')
	
	# Save figure as png
	if output_dir is not None:	
		# Check if path exist
		if not os.path.exists(output_dir):
			os.makedirs(output_dir)
		if fname_output is not None:
			fname_fig = os.path.join(output_dir, fname_output)
		else:
			#fname_fig = os.path.join(output_dir, 'HAD_forecasting_map_m_' + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png')
			fname_fig = os.path.join(output_dir, str(place_code) + "_" + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png')
	else:
		if fname_output is not None:
			fname_fig = fname_output
		else:
			fname_fig = str(place_code) + "_" + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png'

	plt.savefig(fname_fig, dpi=300)
	print("**************")
	print(fname_fig)
	print("**************")
	print(ratio_bw)

if __name__ == '__main__':
	#call_plot_maps()#sys.argv[1])
	plot_map()
