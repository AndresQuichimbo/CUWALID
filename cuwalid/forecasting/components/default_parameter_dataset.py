"""default_parameter_dataset

country codes from
https://wiki.openstreetmap.org/wiki/Nominatim/Country_Codes

"""

# Set the correct name field dependent on the country inputed
name_short_country = {
		"kenya":'KE',
		"ethiopia":'ET',
		"somalia":'SO',
	}


name_field_county_shp = {
		"kenya":'county',
		"ethiopia":'NAME_2',
		"somalia":'NAME',
	}

code_county_shp = {
		"kenya":'gid',
		"ethiopia":'OBJECTID',
		"somalia":'REGN_NO',
	}

name_county_shp = {
		"kenya":'county',
		"ethiopia":'NAME_2',
		"somalia":'NAME',
	}

# do not change this
name_field_shp = {
	"Zoom": "IEBC_WARDS",
	"Ward": "IEBC_WARDS",
	"County": None,
	"Country": "NAME",	
	}



shapefile_country_dic = {
	"region": "forecasting_dataset/HAD/gis/Horn_Africa/Horn_africa_contry.shp"
	}

shapefile_county_dic = {
		"kenya": 'forecasting_dataset/kenya/kenya-county/ke_county.shp',
		"ethiopia": 'forecasting_dataset/ethiopia/Export_admin2.shp',
		"somalia": 'forecasting_dataset/somalia/somalia_regions.shp',
	}

shapefile_wards_dic = {
	"kenya": 'forecasting_dataset/kenya/kenya_wards/Kenya wards.shp'
	}

fname_places_list_file = {
		"kenya": 'forecasting_dataset/KE_Kenya_county.csv',
		"ethiopia": 'forecasting_dataset/ET_Ethiopia_region.csv',
		"somalia": 'forecasting_dataset/SO_Somalia_region.csv',

}