"""default_parameter_dataset

country codes from
https://wiki.openstreetmap.org/wiki/Nominatim/Country_Codes

"""

import os

# Base path: resolve to the parent directory of this file (where forecasting_dataset is located)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
def get_full_path(path): return os.path.join(BASE_DIR, path)


shapefile_country_dic = {
    "region": get_full_path("forecasting_dataset/HAD/gis/Horn_Africa/Horn_africa_contry.shp")
}

shapefile_level_1_dic = {
    "kenya": get_full_path('forecasting_dataset/kenya/kenya-county/ke_county.shp'),
    "ethiopia": get_full_path('forecasting_dataset/ethiopia/Export_admin2.shp'),
    "somalia": get_full_path('forecasting_dataset/somalia/somalia_regions.shp'),
}

shapefile_level_2_dic = {
    "kenya": get_full_path('forecasting_dataset/kenya/kenya-county/ke_county.shp'),
    "ethiopia": get_full_path('forecasting_dataset/ethiopia/Export_admin2.shp'),
    "somalia": get_full_path('forecasting_dataset/somalia/somalia_regions.shp'),
}

shapefile_wards_dic = {
    "kenya": get_full_path('forecasting_dataset/kenya/kenya_wards/Kenya wards.shp')
}

fname_places_list_file = {
    "kenya": get_full_path('forecasting_dataset/kenya/kenya-county/KE_Kenya_county.csv'),
    "ethiopia": get_full_path('forecasting_dataset/ethiopia/ET_Ethiopia_region.csv'),
    "somalia": get_full_path('forecasting_dataset/somalia/SO_Somalia_region.csv'),
}

rivers_shape_path = get_full_path('forecasting_dataset/NaturalEarth/ne_10m_rivers_lake_centerlines.shp')

default_netcdf = get_full_path("forecasting_dataset/HAD/output/HAD_IMERGba_sim0_YYYY_grid.nc")
