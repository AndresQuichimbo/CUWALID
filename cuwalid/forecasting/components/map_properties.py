"""forecasting_map_properties"""

# MAP PROPERTIES ===================================================
# Define filter for tertiary highways
import os


highway_filter = ["primary", "motorway", "tertiary", "trunk"]
# do not modify this
highways = {
'highway':["primary", "motorway", "tertiary"],
#"color" : "r",
#"label" : "Main Roads"
}
#boundaries = {
#'highway':["admin_level",],
#"color" : "r",
#"label" : "Main Roads"
#}

# LINE PROPERTIES -----------------
# specify colours of streets and roads
line_colors = {
"Small Roads": "#333333",
"Main Roads": "#000000",
"Administrative Boundary": "gray",
#"Administrative Boundary": "k",
}

# specify line widths of streets and roads
line_width = {
"Small Roads": 0.50,
"Main Roads": 2.0,
"Administrative Boundary": 2.5,
}

# specify lines styles
line_ls = {
"Small Roads": ":",
"Main Roads": ":",
"Administrative Boundary": "-",
#"Administrative Boundary": "dashed",
}

# dictionaries
aeroway_obj = ["Airport", ]

aeroway_ids = {
"Airport": ["aerodrome"],
}

# color of mark/symbols
aeroway_color = {
"Airport": 'k',
}

aeroway_marker = {
"Airport": '$\u2708$',
}

# marker size of reference points
aeroway_size = {
"Airport": 100,
}

# do not modify this
points = ["Church", "School", "Health centre"]#, "Gas"]

# do not modify this
points_ids = {
#"Airport": ["aerodrome"],
"Church": ["place_of_worship"],
"School": ["school", "college", "university"],
"Gas": ["fuel"],
"Health centre" : ["hospital", "clinic",],
}

# color of mark/symbols
point_color = {
#"Airport": 'k',
"Church": 'k',
"School": 'k',
"Gas": 'k',
"Health centre": "k",
}

# marker (symbol) of reference points
point_marker = {
#"Airport": '$\u2708$',
"Church": '$\u2628$',
"School": '$\u2302$',
"Gas": '$\u26FD$',
"Health centre": '$\u0048$',
}

# marker size of reference points
marker_size = {
"Airport": 35,
"Church": 40,
"School": 10,
"Gas": 20,
"Health centre": 45,
}

# PLACES, IMPORTANT URNAM CENTERS
places_obj = ["Town",]

place_ids = {
"Town": ["town",],
}

place_color = {
"Town": 'k',
}

place_edgecolor = {
"Town": 'gray',
}


place_marker = {
"Town": 'o',
}

place_size = {
"Town": 30,
}

# WATER BODIES
# do not change dthis
water_objects = ["River", "Stream"]
water_body = {
"River": ["river", "stream"],
"Stream": ["stream",],
}

# specify the colour of rivers
water_color = {
"River": '#56B4E9',
"Stream": '#56B4E9',
}

# this dictionary modify line widths of rivers
water_lw = {
"River": 1.2,
"Stream": 0.1,
}

# LEISURE OBJECTS
leisure_objects = ["Natural Reserve"]
leisure_body = {
"Natural Reserve": ["nature_reserve",],
}

leisure_color = {
"Natural Reserve": 'g',
}

# boundary OBJECTS
boundary_objects = ["Administrative Boundary"]

boundary_ids = {
"Administrative Boundary": ["admininstrative",],
}

boundary_color = {
"Administrative Boundary": 'gray',
}

admin_level_map = {
"Zoom": "4",
"Ward": "4",
"County": "4",
"Country": "2",
}

# MAP SCALE ---------------------------------------------------
# do not change this, paramters have been calibrated
plot_scale_id = {
"Zoom": 1.0,
"Ward": 1.0,
"County": 1.6,
"Country": 2.0,
}

## do not change this
#name_field_shp = {
#"Zoom": "IEBC_WARDS",
#"Ward": "IEBC_WARDS",
#"County": None,
#"Country": "NAME",	
#}
#
## Set the correct name field dependent on the country inputed
#name_field_county_shp = {
#	"kenya":'county',
#	"ethiopia":'NAME_2',
#	"somalia":'NAME',
#}

#name_field_shp["County"] = name_field_county_shp[country_name.lower()]

# change only if an element is not required
plot_obj_id = {
"Zoom": {"Administrative Boundary": True,
		"Natural Reserve": True,
		"River": True,
		"Stream": False,
		"Airport": True,
		"Church": False,
		"School": False,
		"Health centre": True,
		"Main Roads": True,
		"Small Roads": False,
		"Town": True,
		},
"Ward": {"Administrative Boundary": True,
		"Natural Reserve": True,
		"River": True,
		"Stream": False,
		"Airport": True,
		"Church": False,
		"Health centre": True,
		"School": False,
		"Main Roads": True,
		"Small Roads": False,
		"Town": True,
		},
"County": {"Administrative Boundary": True,
		"Natural Reserve": True,
		"River": True,
		"Stream": False,
		"Airport": True,
		"Church": False,
		"School": False,
		"Health centre": False,
		"Main Roads": True,
		"Small Roads": False,
		"Town": True,
		},
"Country": {"Administrative Boundary": True,
		"Natural Reserve": False,
		"River": False,
		"Stream": False,
		"Airport": False,
		"Church": False,
		"School": False,
		"Health centre": False,
		"Main Roads": False,
		"Small Roads": False,
		"Town": True,
		},
}
# do not change this
# https://www.loc.gov/standards/iso639-2/php/code_list.php
language_map = {
"English": "name",
"Swahili": "name:sw",
"Somali": "name:so",
"Amharic": "name:am",
"Oromo": "name:om",
}

language_short_name = {
"English": "EN",
"Swahili": "SW",
"Somali": "SO",
"Amharic": "AM",
"Oromo": "OM",
}

font_paths = {
    "English": None,
    "Swahili": None, 
    "Somali": None,
    "Amharic": os.path.join(os.path.dirname(__file__), "..", "forecasting", "fonts", "NotoSansEthiopic-VariableFont_wdth,wght.ttf"),
    "Oromo": None, 
}


language_labels = {
"English":{
    	"Administrative Boundary": "Boundary",
		"Natural Reserve": "Natural Reserve",
		"River": "River",
		"Stream": "Stream",
		"Airport": "Airport",
		"Church": "Church",
		"School": "School",
		"Health centre": "Health centre",
		"Main Roads": "Main Road",
		"Small Roads": "Small Road",
		"Town": "Town",
		#"OND": "Short rains (Oct-Dec)",
		#"MAM": "Long rains (MAR-MAY)",
		"OND": "(October-December)",
		"MAM": "(March-May)",
		"JJAS": "(June-September)",
		"JJA": "(June-August)",
		"Soil": "Soil Moisture Status",
		"Evaporation": "Evapotranspiration",
		"Groundwater": "Groundwater status",
		"Surface": "Surface Water Status",
		"Flood": "Flood Hazard",
		"in": "in",
        "Geography":"Geography",
        'Boundary':'Boundary',
        'Location': 'Location',
        "Crop": "Crop Status",
		"Pasture": "Pasture Status",
		},
"Swahili":{"Administrative Boundary": "Mpaka",
		"Natural Reserve": "Natural Reserve",
		"River": "River",
		"Stream": "Stream",
		"Airport": "Uwanja wa ndege",
		"Church": "",
		"School": "",
		"Health centre": "Kituo cha afya na matibabu",
		"Main Roads": "Barabara kuu",
		"Small Roads": "Small Roads",
		"Town": "Town",
		"OND": "Mvua kidogo wa mda mfupi (Oktoba-Desemba)",
		"MAM": "Mvua mingi wa masika (Machi - Mei)",
		"Soil": "Soil Moisture Status",
		"Evaporation": "Evapotranspiration",
		"Groundwater": "Hali ya maji ya chini ya ardhi",
		"Surface": "Hali ya maji ya juu ya ardhi",
		"Flood": "Uwezekano wa hadhari\nza Mafuriko",
		"in": "in",
		"Geography":"Vipengele vya kijiografia",
        'Boundary':'Mpaka',
        'Location': 'Location',
		"Crop": "Crop Status",
		"Pasture": "Pasture Status",
		},
"Somali":{"Administrative Boundary": "Mpaka",
		"Natural Reserve": "Natural Reserve",
		"River": "River",
		"Stream": "Stream",
		"Airport": "Uwanja wa ndege",
		"Church": "",
		"School": "",
		"Health centre": "Kituo cha afya na matibabu",
		"Main Roads": "Barabara kuu",
		"Small Roads": "Small Roads",
		"Town": "Town",
		"OND": "Mvua kidogo wa mda mfupi (Oktoba-Desemba)",
		"MAM": "Mvua mingi wa masika (Machi - Mei)",
		"Soil": "Soil Moisture Status",
		"Evaporation": "Evapotranspiration",
		"Groundwater": "Hali ya maji ya chini ya ardhi",
		"Surface": "Hali ya maji ya juu ya ardhi",
		"Flood": "Uwezekano wa hadhari\nza Mafuriko",
		"in": "in",
		"Geography":"Vipengele vya kijiografia",
        'Boundary':'Mpaka',
        'Location': 'Location',
		"Crop": "Crop Status",
		"Pasture": "Pasture Status",
		},
"Amharic":{"Administrative Boundary": "Mpaka",
		"Natural Reserve": "የተፈጥሮ ሀብት",
		"River": "River",
		"Stream": "Stream",
		"Airport": "Uwanja wa ndege",
		"Church": "",
		"School": "",
		"Health centre": "Kituo cha afya na matibabu",
		"Main Roads": "Barabara kuu",
		"Small Roads": "Small Roads",
		"Town": "Town",
		"OND": "Mvua kidogo wa mda mfupi (Oktoba-Desemba)",
		"MAM": "Mvua mingi wa masika (Machi - Mei)",
		"Soil": "Soil Moisture Status",
		"Evaporation": "Evapotranspiration",
		"Groundwater": "Hali ya maji ya chini ya ardhi",
		"Surface": "Hali ya maji ya juu ya ardhi",
		"Flood": "Uwezekano wa hadhari\nza Mafuriko",
		"in": "in",
		"Geography":"Vipengele vya kijiografia",
        'Boundary':'Mpaka',
        'Location': 'Location',
		"Crop": "Crop Status",
		"Pasture": "Pasture Status",
		},
"Oromo":{"Administrative Boundary": "Mpaka",
		"Natural Reserve": "Natural Reserve",
		"River": "River",
		"Stream": "Stream",
		"Airport": "Uwanja wa ndege",
		"Church": "",
		"School": "",
		"Health centre": "Kituo cha afya na matibabu",
		"Main Roads": "Barabara kuu",
		"Small Roads": "Small Roads",
		"Town": "Town",
		"OND": "Mvua kidogo wa mda mfupi (Oktoba-Desemba)",
		"MAM": "Mvua mingi wa masika (Machi - Mei)",
		"Soil": "Soil Moisture Status",
		"Evaporation": "Evapotranspiration",
		"Groundwater": "Hali ya maji ya chini ya ardhi",
		"Surface": "Hali ya maji ya juu ya ardhi",
		"Flood": "Uwezekano wa hadhari\nza Mafuriko",
		"in": "in",
		"Geography":"Vipengele vya kijiografia",
        'Boundary':'Mpaka',
        'Location': 'Location',
		"Crop": "Crop Status",
		"Pasture": "Pasture Status",
		}
        
}
# season labels
season_name = {
"OND": "Short rains (Oct-Dec)",
"MAM": "Long rains (MAR-MAY)",
}

# variable labels and colorbar labels -------------------------
water_var = {
"Flood": "flood",
"Groundwater": "twsc",
"Surface": "dis",
"Soil": "tht",
"Evaporation": "aet",
"Crop": "wrsi",
"Pasture": "wrsi",
}
variable = {
"Soil": "Soil Moisture Status",
"Evaporation": "Evapotranspiration",
"Groundwater": "Groundwater status",
"Surface": "Surface Water Status",
"Flood": "Flood Hazard Potential",
"Crop": "Potential crop health",
"Pasture": "Potential pasture/browse health",
}

status_labels = {
"English":{
    "Flood": ["High", "Normal", "Low"],
	"Groundwater": ["Above Normal","Normal", "Below Normal"],#"Bad", "Good"
	"Surface": ["Above Normal","Normal", "Below Normal"],
	"Soil": ["Above Normal","Normal", "Below Normal"],
	"Evaporation": ["Above Normal","Normal", "Below Normal"],
	"Crop": ["Above Normal","Normal", "Below Normal"],
	"Pasture": ["Above Normal","Normal", "Below Normal"],
},
"Swahili":{
    "Flood": ["High", "Normal", "Low"],
	"Groundwater": ["Above Normal","Normal", "Below Normal"],#"Bad", "Good"
	"Surface": ["Above Normal","Normal", "Below Normal"],
	"Soil": ["Above Normal","Normal", "Below Normal"],
	"Evaporation": ["Above Normal","Normal", "Below Normal"],
	"Crop": ["Above Normal","Normal", "Below Normal"],
	"Pasture": ["Above Normal","Normal", "Below Normal"],
},
"Somali":{
    "Flood": ["High", "Normal", "Low"],
	"Groundwater": ["Above Normal","Normal", "Below Normal"],#"Bad", "Good"
	"Surface": ["Above Normal","Normal", "Below Normal"],
	"Soil": ["Above Normal","Normal", "Below Normal"],
	"Evaporation": ["Above Normal","Normal", "Below Normal"],
	"Crop": ["Above Normal","Normal", "Below Normal"],
	"Pasture": ["Above Normal","Normal", "Below Normal"],
},
"Oromo":{
    "Flood": ["High", "Normal", "Low"],
	"Groundwater": ["Above Normal","Normal", "Below Normal"],#"Bad", "Good"
	"Surface": ["Above Normal","Normal", "Below Normal"],
	"Soil": ["Above Normal","Normal", "Below Normal"],
	"Evaporation": ["Above Normal","Normal", "Below Normal"],
	"Crop": ["Above Normal","Normal", "Below Normal"],
	"Pasture": ["Above Normal","Normal", "Below Normal"],
},
"Amharic":{
    "Flood": ["High", "Normal", "Low"],
	"Groundwater": ["Above Normal","Normal", "Below Normal"],#"Bad", "Good"
	"Surface": ["Above Normal","Normal", "Below Normal"],
	"Soil": ["Above Normal","Normal", "Below Normal"],
	"Evaporation": ["Above Normal","Normal", "Below Normal"],
	"Crop": ["Above Normal","Normal", "Below Normal"],
	"Pasture": ["Above Normal","Normal", "Below Normal"],
},
}

var_colour = {
"Groundwater": ["#648FFF", "#FFFF00", "#DB4325"],
"Surface": ["#648FFF", "#FFFF00", "#DB4325"],
"Soil": ["#648FFF", "##FFFF00", "#DB4325"],
"Evaporation": ["#FFFF00", "#EDA247", "#57C4AD"],
#"Crop": ["#57C4AD", "#EDA247", "#DB4325"],
#"Crop": ["#CC79A7", "#E69F00", "#D55E00"],
#"Crop": ["#CC79A7", "#E69F00", "#DB4325"],
"Crop": ["#648FFF", "#FFFF00", "#DB4325"],
"Pasture": ["#648FFF", "#FFFF00", "#DB4325"],
"Flood": ["#DB4325", "#FFFF00", "#648FFF"],
}

#status = {
#"Flood": ["Low\nSio sana", "High\nNi sana"],
#"Groundwater": ["Bad\nHali mbaya", "Good\nHali mzuri"],
#"Surface": ["Bad\nHali mbaya", "Good\nHali mzuri"],
#"Soil": ["Good\nHali mzuri", "Bad\nHali mbaya"],
#"Evaporation": ["Good\nHali mzuri", "Bad\nHali mbaya"],
#"Crop": ["Good\nHali mzuri", "Bad\nHali mbaya"],
#}

#aux_status_labels = {
#"English":{
#    "Flood": ["Low", "High"],
#	"Groundwater": ["Bad", "Good"],
#	"Surface": ["Bad", "Good"],
#	"Soil": ["Good", "Bad"],
#	"Evaporation": ["Good", "Bad"],
#	"Crop": ["Good", "Bad"],
#},
#"Swahili": {
#    "Flood": ["Low\nSio sana", "High\nNi sana"],
#	"Groundwater": ["Bad\nHali mbaya", "Good\nHali mzuri"],
#	"Surface": ["Bad\nHali mbaya", "Good\nHali mzuri"],
#	"Soil": ["Good\nHali mzuri", "Bad\nHali mbaya"],
#	"Evaporation": ["Good\nHali mzuri", "Bad\nHali mbaya"],
#	"Crop": ["Good\nHali mzuri", "Bad\nHali mbaya"],
#}
#}
#
#aux_var_colour = {
#"Groundwater": ["#E69F00", "#009E73"],
#"Surface": ["#E69F00", "#009E73"],
#"Soil": ["darkviolet", "seagreen"],
#"Evaporation": ["darkviolet", "seagreen"],
#"Flood": ["#009E73", "#E69F00"],
#"Crop": ["#E69F00", "#009E73"],
#}
#var_colour = {
##"Groundwater": ["#009E73", "#E69F00", "#E41A1C"],
##"Surface": ["#009E73", "#E69F00", "#E41A1C"],
##"Soil": ["#009E73", "#E69F00", "#E41A1C"],
##"Flood": ["#E41A1C", "#E69F00", "#009E73"],
#}


# ward name and center (lat, lon)
wards_data = {
"Burat": (0.3475694841724472, 37.493336034162525), #(0.353, 37.584),
"Kinna": (0.263515185704488, 38.240486302993496), #(0.31883, 38.20499),
}
