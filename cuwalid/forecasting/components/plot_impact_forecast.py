# Import libraries from local repository
import os
import pickle
import geopy
from geopy.geocoders import Nominatim
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
import osmnx as ox
import geopandas as gpd
import xarray as xr
import rioxarray
import rasterio
import numpy as np
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches
from matplotlib_scalebar.scalebar import ScaleBar
from shapely.geometry import box
import matplotlib.patheffects as path_effects
from cuwalid.forecasting.components.helper_functions import add_label_features, bounding_box, get_mask, get_season_dataset, read_dataset, resample_dataset
from cuwalid.forecasting.components.map_properties import *
from cuwalid.forecasting.components.read_paths import *
import cuwalid.tools.CUWALID_view_tool as cuwalidplt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
#import arabic_reshaper
#from bidi import algorithm as bidialg

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
			language=["English","Swahili", "Amharic", "Oromo", "Somali"],
			output_dir=None,
			netcdf_path=None,
			threshold_path=None,
			mask_path=None,
			river_path=None,
			fname_output=None,
			place_code_field=False,
			shape_path_list=None):
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

	# make sure that kanguage is a list
	if isinstance(language, str):
		language = [language]
	
	# add loop for languages to avoid duplicate downloads
	for ilanguage in language:

		font_path = font_paths[ilanguage.lower()]

		if font_path:
			language_font = FontProperties(fname=font_path)
		else:
			language_font = FontProperties()

		# Save figure as png ========================================================
		if output_dir is not None:	
			# Check if path exist
			if not os.path.exists(output_dir):
				os.makedirs(output_dir, exist_ok=True)
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

		# add language initial at maps names.
		fname_fig = os.path.splitext(fname_fig)[0] + "_" + language_short_name[ilanguage] + ".png"

		if os.path.exists(fname_fig):
			#print("File already exist, delete it before you run it if you want to create a new file")
			print(f"The map {fname_fig} already exists, skipping to next")
		else:


			# use this function to cleam some variables and names in the code
			paths = get_paths(plot_scale, region, country_name,
						   	iwater_status, iyear, iseason,
							shape_path_list=shape_path_list,
							place_code_field=place_code_field,
							netcdf_path=netcdf_path,
							threshold_path=threshold_path,
							mask_path=mask_path,
							river_path=river_path
							)

			osm_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "osm_data")
			
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
			wards = gpd.read_file(paths.fname_place)

			if place_code_field is False:
				wards = wards[(wards[paths.iname_field_shp[country_name.lower()]] == place_name)]
			else:
				wards = wards[(wards[paths.iname_field_shp] == place_code)]

			# select polygon to use as mask
			polygon = wards["geometry"].iloc[0]

			# Get the street network graph for walking
			# Load data from shapefiles
			rivers = gpd.read_file(paths.rivers_shapefile)
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


			# get roads and streets from OSM
			if plot_obj_id[plot_scale]["Main Roads"] is True:
				cache_file = os.path.join(osm_data_dir, f'{place_name}_roads.pkl')
				try:
					if os.path.exists(cache_file):
						print("Reading road data from cached file")
						with open(cache_file, 'rb') as f:
							highway = pickle.load(f)
					else:
						print("Getting road data from OSM server")
						highway = ox.features.features_from_polygon(polygon, tags={'highway': True})
						with open(cache_file, 'wb') as f:
							pickle.dump(highway, f)

					# Clip the OSM data to the polygon
					highway = gpd.clip(highway, polygon)
					highway.crs = mapPP
					highway = highway.to_crs(netcdfPP)  # ds.rio.crs
				except:
					print("Error with highway")

			# read point locations
			read_oms = False
			for ipoint in points:
				if plot_obj_id[plot_scale][ipoint] is True:
					read_oms = True

			if read_oms is True:
				cache_file = os.path.join(osm_data_dir, f'{place_name}_amenity.pkl')
				try:
					if os.path.exists(cache_file):
						print("Getting amenity data from file")
						with open(cache_file, 'rb') as f:
							amenities = pickle.load(f)
					else:
						print("Getting amenity data from OSM server")
						amenities = ox.features.features_from_polygon(polygon, tags={'amenity': True})
						amenities = amenities[amenities.intersects(polygon)]
						with open(cache_file, 'wb') as f:
							pickle.dump(amenities, f)
				except:
					print("No amenities found")
					amenities = []

				amenities = amenities.loc["node"]
				amenities.crs = mapPP
				amenities = amenities.to_crs(netcdfPP)

			# read point locations for aeroways
			read_oms = False
			for ipoint in aeroway_obj:
				if plot_obj_id[plot_scale][ipoint] is True:
					read_oms = True

			if read_oms is True:
				cache_file = os.path.join(osm_data_dir, f'{place_name}_aeroway.pkl')
				try:
					if os.path.exists(cache_file):
						print("Getting aeroway data from file")
						with open(cache_file, 'rb') as f:
							aeroway = pickle.load(f)
					else:
						print("Getting aeroway data from OSM server")
						aeroway = ox.features.features_from_polygon(polygon, tags={'aeroway': True})
						aeroway = aeroway[aeroway["name"].notnull()]
						aeroway = gpd.clip(aeroway, polygon)
						aeroway.crs = mapPP
						aeroway = aeroway.to_crs(netcdfPP)
						aeroway = aeroway.centroid
						with open(cache_file, 'wb') as f:
							pickle.dump(aeroway, f)
				except:
					print("No airports found")
					aeroway = []

			# read waterways
			read_oms = False
			for iwater in water_objects:
				if plot_obj_id[plot_scale][iwater] is True:
					read_oms = True

			if read_oms is True:
				cache_file = os.path.join(osm_data_dir, f'{place_name}_waterway.pkl')
				try:
					if os.path.exists(cache_file):
						print("Getting waterway data from file")
						with open(cache_file, 'rb') as f:
							water = pickle.load(f)
					else:
						print("Getting waterway data from OSM server")
						water = ox.features.features_from_polygon(polygon, tags={'waterway': True})
						water = gpd.clip(water, polygon)
						water.crs = mapPP
						water = water.to_crs(netcdfPP)
						with open(cache_file, 'wb') as f:
							pickle.dump(water, f)
				except:
					print("Error with waterway")
					water = None

			# read natural reserves
			read_oms = False
			for iwater in water_objects:
				if plot_obj_id[plot_scale][iwater] is True:
					read_oms = True

			if read_oms is True:
				cache_file = os.path.join(osm_data_dir, f'{place_name}_leisure.pkl')
				try:
					if os.path.exists(cache_file):
						print("Getting leisure data from file")
						with open(cache_file, 'rb') as f:
							leisure = pickle.load(f)
					else:
						print("Getting leisure data from OSM server")
						leisure = ox.features.features_from_polygon(polygon, tags={'leisure': True})
						leisure = gpd.clip(leisure, polygon)
						leisure.crs = mapPP
						leisure = leisure.to_crs(netcdfPP)
						with open(cache_file, 'wb') as f:
							pickle.dump(leisure, f)
				except:
					print("Error with leisure")

			# read urban centres
			read_oms = False
			for iplaces in places_obj:
				if plot_obj_id[plot_scale][iplaces] is True:
					read_oms = True

			if read_oms is True:
				cache_file = os.path.join(osm_data_dir, f'{place_name}_place.pkl')
				if os.path.exists(cache_file):
					print("Getting place data from file")
					with open(cache_file, 'rb') as f:
						places = pickle.load(f)
				else:
					try:
						print("Getting place data from OSM server")
						places = ox.features.features_from_polygon(polygon, tags={'place': True})
						places = places.loc['node']
						places.crs = mapPP
						places = gpd.clip(places, polygon)
						places = places.to_crs(netcdfPP)
						with open(cache_file, 'wb') as f:
							pickle.dump(places, f)
					except:
						print("Error getting place names")

			# administrative borders
			if plot_obj_id[plot_scale]["Administrative Boundary"] is True:
				cache_file = os.path.join(osm_data_dir, f'{place_name}_boundary.pkl')
				if os.path.exists(cache_file):
					print("Getting boundary data from file")
					with open(cache_file, 'rb') as f:
						bnd_admin = pickle.load(f)
				else:
					try:
						print("Getting boundary data from OSM server")
						bnd_admin = ox.features.features_from_polygon(polygon, tags={'boundary': True})
						bnd_admin = gpd.clip(bnd_admin, polygon)
						bnd_admin = bnd_admin.loc['relation']
						bnd_admin.crs = mapPP
						bnd_admin = bnd_admin.to_crs(netcdfPP)
						with open(cache_file, 'wb') as f:
							pickle.dump(bnd_admin, f)
					except:
						print("Error getting boundry's")



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

			# =========================================================
			# READ MODEL DATASETS AND THRSHOLDS
			# =========================================================
			# especify water variable to read and plot
			var = water_var[iwater_status]

			# READ MODEL OUTPUTS ---------------------------------------
			# Open dataset of model outputs
			ds = xr.open_dataset(paths.netcdf_path)

			# Apply mask to datasets
			if paths.mask_path is not None:
				#print(paths.mask_path)
				mask = np.flip(get_mask(paths.mask_path), 0)
				ds = ds*mask	

			# Write projection on dataset
			ds = ds.rio.write_crs(netcdfPP)

			# convert mask into xarray dataset
			#mask = reproject_dataset(mask, oldPP, newPP)

			# reprojec dataset
			ds = ds.rename({'lon': 'x', 'lat': 'y'})
			#ds = reproject_dataset(ds, netcdfPP, mapPP)
			#ds_thrshold = ds_thrshold.rename({'lon': 'x', 'lat': 'y'})
			#ds_thrshold = reproject_dataset(ds_thrshold, netcdfPP, mapPP)

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

			# clip raster
			level_2_region = None
			if paths.shapefile_level_2 is not None:
				level_2_region = gpd.read_file(paths.shapefile_level_2)
				level_2_region = gpd.clip(level_2_region, polygon)

			# =========================================================
			# =========================================================
			# CREATE FIGURE - MAP
			# =========================================================
			# calulate ration of figure heigth/width
			ratio_bw = np.abs((extend[1]-extend[3])/(extend[0]-extend[2]))
			if ratio_bw <= 0.5:
				ratio_bw = ratio_bw*1.2

	## make sure that kanguage is a list
	#if isinstance(language, str):
	#	language = [language]
	#
	## add loop for languages to avoid duplicate downloads
	#for ilanguage in language:
#
	#	font_path = font_paths[ilanguage.lower()]
#
	#	if font_path:
	#		language_font = FontProperties(fname=font_path)
	#	else:
	#		language_font = FontProperties()
#
	#	# Save figure as png ========================================================
	#	if output_dir is not None:	
	#		# Check if path exist
	#		if not os.path.exists(output_dir):
	#			os.makedirs(output_dir, exist_ok=True)
	#		if fname_output is not None:
	#			fname_fig = os.path.join(output_dir, fname_output)
	#		else:
	#			#fname_fig = os.path.join(output_dir, 'HAD_forecasting_map_m_' + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png')
	#			fname_fig = os.path.join(output_dir, str(place_code) + "_" + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png')
	#	else:
	#		if fname_output is not None:
	#			fname_fig = fname_output
	#		else:
	#			fname_fig = str(place_code) + "_" + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png'
#
	#	# add language initial at maps names.
	#	fname_fig = os.path.splitext(fname_fig)[0] + "_" + language_short_name[ilanguage] + ".png"
#
	#	if os.path.exists(fname_fig):
	#		print("File already exist, delete it before you run it if you want to create a new file")
	#		print(fname_fig)
	#	else:
	
			# figure size
			map_width = 5.0*plot_scale_id[plot_scale]
			map_height = 5.2*ratio_bw*plot_scale_id[plot_scale]

			#axis for location
			ax_loc_width = map_width*0.25
			ax_loc_height = map_width*0.25

			figure_height = map_height + ax_loc_height

			# Create the base map
			fig, ax = plt.subplots()
			fig.set_size_inches(map_width, figure_height,
						  )

			plt.subplots_adjust(top=0.96, bottom=ax_loc_height/figure_height,
						  left=0.025, right=0.975)

			# Add figure
			cuwalidplt.plot_impact_tercile_forecast(ds,
				title="Impact based Forecast", reproject=False,
				fshapefile=None, fmask=None, ax=ax,
				color=var_colour[iwater_status])

			# Add sublevels for padmin boudaries
			if level_2_region is not None:
				level_2_region.plot(ax=ax, color="lightgray", label='Admin Boundaries')

			# Add river layers from other datasets
			#rivers.plot(ax=ax, color='#0099ff', label='Rivers')


			# plot water bodies and rivers
			# plot only when discharge is ploted
			if var != "dis":
				for iwater in water_objects:
					if plot_obj_id[plot_scale][iwater] is True:
						if water is not None:
							try:
								water_filter = water[water['waterway'].isin(water_body[iwater])]
								water_filter.plot(ax=ax,
									#marker=point_marker[ipoint],
									#color=water_color[iwater],
									edgecolor=water_color[iwater],
									linewidths=water_lw[iwater],
									facecolor='none',#water_color[iwater],
									#markersize=0.0*marker_size[ipoint],
									#label=iwater+ "\n" + language_labels["Swahili"][iwater],
									label=get_labels_by_lenguage(language_labels, ilanguage, iwater),
									path_effects=[path_effects.withStroke(
											linewidth=water_lw[iwater]*1.5, foreground='w')],
									)
							except:
								print("Error plotting waterway")

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
								#label='Main Roads'+ "\n" + language_labels["Swahili"]["Main Roads"],
								label=get_labels_by_lenguage(language_labels, ilanguage,"Main Roads"),
								alpha=1.0,
								)
				except:
					print("error with highway")

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
							#label=ileisure+ "\n" + language_labels["Swahili"][ileisure],
							label=get_labels_by_lenguage(language_labels, ilanguage, ileisure),
							alpha=0.5,
							)


						# add labels
						# Filter edges to reduce the number of labels (optional)
						leisure_filter = leisure_filter[leisure_filter["name"].notnull()]#.sample(n=50)

						# Annotate the plot with street names
						add_label_features(leisure_filter, language_font, boundbox=extend,
							#language=language_map[ilanguage],
							)
					except:
						print("error with leisure filter")

			# print label of admin boundaries
			if plot_obj_id[plot_scale]["Administrative Boundary"] is True:
				#boundary_filter = bnd_admin[bnd_admin['admin_level'].notnull()]
				boundary_filter = bnd_admin[bnd_admin['admin_level'].isin(["4"])]
				# add labels
				try:
					add_label_features(boundary_filter, language_font, boundbox=extend, #, offset=1000)
						fontsize=12.5, fontstyle="italic", halignament="center", alpha=0.7,
						language=language_map[ilanguage], #color="gray"
						)
				except:
					print("Error when adding admin boundry label features")

			# Plot the original polygon (boundaries)
			wards.plot(ax=ax, facecolor='none',
					edgecolor=line_colors["Administrative Boundary"],
					linewidth=line_width["Administrative Boundary"],
					ls=line_ls["Administrative Boundary"],
					# legend=True, label='Boundaries',
					alpha=1.0
					)

			# Add point attributes
			# if plot_scale != "Country":
			for ipoint in points:
				if plot_obj_id[plot_scale][ipoint] is True:
					try:
						points_filter = amenities[amenities['amenity'].isin(points_ids[ipoint])]

						if len(points_filter) > 10:
							points_filter = points_filter.sample(n=10, random_state=1)

						points_filter.plot(ax=ax,
							color=point_color[ipoint],
							marker=point_marker[ipoint],
							edgecolor='none',
							#linewidths=0.1,
							facecolor=point_color[ipoint],
							markersize=marker_size[ipoint],
							#label=ipoint+ "\n" + language_labels["Swahili"][ipoint],
							label=get_labels_by_lenguage(language_labels, ilanguage, ipoint),
							)
					except:
						print("Error plotting amenities")

			# Add point attributes -----------------------------------------------------------------------
			#if plot_scale != "Country":
			for ipoint in aeroway_obj:
				if plot_obj_id[plot_scale][ipoint] is True:
					if len(aeroway) > 0:
						try:
							aeroway = aeroway.centroid
						except:
							print("Centroid is not being calculated")
						
						aeroway.plot(ax=ax,
							color=aeroway_color[ipoint],
							marker=aeroway_marker[ipoint],
							edgecolor="none",#aeroway_color[ipoint],
							linewidths=0.1,
							facecolor=aeroway_color[ipoint],
							markersize=aeroway_size[ipoint],
							#label=ipoint + "\n" + language_labels["Swahili"][ipoint],
							label=get_labels_by_lenguage(language_labels, ilanguage, ipoint),
							#label=get_labels_by_lenguage(language_labels, ilanguage,"Main Roads"),
							)

			# Prepare additional legend entry
			boundary_line, = plt.plot([], [], # Invisible in plot, visible in legend
						color=line_colors["Administrative Boundary"],
						ls=line_ls["Administrative Boundary"],
						label=get_labels_by_lenguage(language_labels, ilanguage,'Boundary')
						)  
			plt.legend(handles=[boundary_line], prop=language_font)



			# Add point attributes ----------------------------------------------------------------------
			#if plot_scale != "Country":
			for iplaces in places_obj:
				if plot_obj_id[plot_scale][iplaces] is True:
					
					place_filter = places[places['place'].isin(place_ids[iplaces])]

					if len(place_filter) > 10:
						place_filter = place_filter.sample(n=10, random_state=1)


					add_label_features(place_filter, language_font, boundbox=extend, #, offset=1000)
						fontsize=8, fontstyle="italic", offset=1000,
						halignament="left", #alpha=0.7,
						language=language_map[ilanguage], #color="gray"
						)


					
					place_filter.plot(ax=ax,
						color=place_color[iplaces],
						marker=place_marker[iplaces],
						edgecolor=place_edgecolor[iplaces],
						#markeredgecolor=place_edgecolor[iplaces],
						linewidths=1.5,
						facecolor=place_color[iplaces],
						markersize=place_size[iplaces],
						#label=iplaces + "\n" + language_labels["Swahili"][iplaces],
						label=get_labels_by_lenguage(language_labels, ilanguage, iplaces),
						)


			# MAP TITLE ============================================================================
			plt.title(#"Map of "+ place_name + "" + ", Kenya\n"+
				# English
				get_labels_by_lenguage(language_labels, ilanguage, iwater_status) +
				" - " + place_name +#"\n"+
				get_labels_by_lenguage(language_labels, ilanguage, iseason) + " " + str(iyear),
	#			str(iyear)
				#str(pd.to_datetime(rescaled.time.values[time_plot]).year)
				fontweight="bold",
				fontproperties=language_font)


			# MAP LEGEND ============================================================================
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
					#title=get_labels_by_lenguage(language_labels, ilanguage,"Geography"),
					ncols=ncol_legend,
					prop= language_font
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

			label_patches = status_labels[ilanguage][iwater_status]

			# add legend
			ax.legend(handles=rect_patches, labels=label_patches,
					bbox_to_anchor=(1.0, 0),
					loc=1, borderaxespad=0.,
					#title=variable[iwater_status]+ "\n" +
					#			language_labels["Swahili"][iwater_status],
					title=get_labels_by_lenguage(language_labels, ilanguage, iwater_status),
					frameon=False,
					title_fontproperties=language_font,
					prop=language_font
					)

			# ADD SCALE BAR TO FIGURE ======================================================
			scalebar = ScaleBar(1, length_fraction=0.0254, location="lower right") # 1 pixel = 0.2 meter
			plt.gca().add_artist(scalebar)

			# add label to axis
			#plt.xlabel("Longitude")
			#plt.ylabel("Latitude")

			# MODFIDY AXES AND MARGINS
			# switch off axis ------------------------------------------------------		
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
			#plt.tight_layout()

			# ADD LOCATION PLOT ===========================================
			ax2 = fig.add_axes([0.5, 0, 
						  ax_loc_width/map_width,
						  ax_loc_height/figure_height])

			# read map location
			country = gpd.read_file(paths.fname_place)
			country.crs = mapPP
			country = country.to_crs(netcdfPP)

			#ax2.set_title("Location")

			country.plot(ax=ax2, facecolor="none",
					edgecolor="silver",
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
			# hide axes
			ax2.axis('off')

			# Add logo ==================================================================
			# Get the current script's directory
			current_dir = os.path.dirname(os.path.abspath(__file__))

			# Navigate two levels up
			two_levels_up = os.path.abspath(os.path.join(current_dir, '..', '..','..'))
			fname = os.path.join(two_levels_up,"docs","fig","CUWALID_Logo_LS_Tag.png")
			logo = plt.imread(fname, format="png")

			# Create an OffsetImage object
			imagebox = OffsetImage(logo, zoom=0.025)  # Adjust zoom as needed

			# Create an AnnotationBbox to place the image
			ab = AnnotationBbox(imagebox, (0.0, 0.0),
						  xycoords='axes fraction',
						  box_alignment=(0,0.0),
						  frameon=False)

			# Add the annotation to the plot
			ax.add_artist(ab)

			##### Save figure as png ========================================================
			####if output_dir is not None:	
			####	# Check if path exist
			####	if not os.path.exists(output_dir):
			####		os.makedirs(output_dir, exist_ok=True)
			####	if fname_output is not None:
			####		fname_fig = os.path.join(output_dir, fname_output)
			####	else:
			####		#fname_fig = os.path.join(output_dir, 'HAD_forecasting_map_m_' + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png')
			####		fname_fig = os.path.join(output_dir, str(place_code) + "_" + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png')
			####else:
			####	if fname_output is not None:
			####		fname_fig = fname_output
			####	else:
			####		fname_fig = str(place_code) + "_" + place_name + "_" + iwater_status + "_" + plot_scale + "_" + iseason + '.png'
			##### add language initial at maps names.
			####fname_fig = os.path.splitext(fname_fig)[0] + "_" + language_short_name[ilanguage] + ".png"

			plt.savefig(fname_fig, dpi=300)
			print("**************")
			print(fname_fig)
			print("**************")
			print(ratio_bw)
			plt.close()
def get_labels_by_lenguage(dictionary, language, iterm):
	"""Funciton to create labels with different languages
	
	Parameters:
	-----------
	dictionary: dictionary
		dictionary containing all terms in different languages
	language: list
		list of languages to print
	iterm : str
		name of the word/term to include in the label

	Returns
	--------
	label : str
		string containing all labels to pinclude in the map
	"""
	if isinstance(language, str):
		language = [language]
		#print("var1 is a string")
	#print(type(language))
	#print(language)

	label = None
	for ilanguage in language:
		if label is None:
			label = dictionary[ilanguage][iterm]
		label = ("\n" + dictionary[ilanguage][iterm])
	return label

if __name__ == '__main__':
	#call_plot_maps()#sys.argv[1])
	plot_map()