import os
import sys
from urllib.request import urlretrieve
from tqdm import tqdm
from pyrosm import OSM, get_data
import geopandas as gpd


def get_data_osm(place, path=None,
            tags=["boundary", "place", "highway", "amenity", "leisure", "waterways", "aeroway"]):
    # Get test data 
    path_osm = get_data(place, directory=path)

    # Initialize the reader
    osm = OSM(path_osm)
    # Read POIs with custom filter A
    for itag in tags:
        path_out = os.path.join(os.path.split(path_osm)[0], itag + "_" + place + ".json")
        try:
            if not os.path.exists(path_out):
		
                # filter data
                my_filter = {itag: True}
                filtered_data = osm.get_pois(custom_filter=my_filter)
                # save data
                
                filtered_data.to_file(path_out, driver='GeoJSON')
        except:
            print("error with " + itag)