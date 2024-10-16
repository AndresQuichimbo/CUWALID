"""DRYP_default_settings"""

default_settings = {
    "SIMULATION_PERIOD": {
        "start_date": "2000 1 1",
        "end_date": "2002 1 3",
    },

    "PROJECTION" : None,

    "TIMESTEP_SETTINGS": {
        "dt_of": 60,
        "dt_uz": 60,
        "dt_gw": 60,
    },

    "READING": {
      
        "data_reading": {
            "pre": 0,
            "pet": 0,
            "abs": 0,
            "kc": 0,
            "flux": 0,
            "savi": 0,
            "savi_min": 0,
            "savi_max": 0,
            "lai": 0,
            },
        "data_step": {
            "pre": 60,
            "pet": 60,
            "abs": 60,
            "kc": 60,
            "flux": 60,
            "savi": 60,
            "savi_min": 60,
            "savi_max": 60,
            "lai": 60,
            },
        "data_reproject": {
            "pre": True,
            "pet": True,
            "abs": True,
            "kc": True,
            "flux": True,
            "savi": True,
            "savi_min": True,
            "savi_max": True,
            "lai": True,
            },
        "data_interp": {
            "pre": True,
            "pet": True,
            "abs": True,
            "kc": True,
            "flux": True,
            "savi": True,
            "savi_min": True,
            "savi_max": True,
            "lai": True,
            },
        "data_projection" : {
			"pre": "EPSG:4326",
			"pet": "EPSG:4326",
			"abs": "EPSG:4326",
			"kc": "EPSG:4326",
			"flux": "EPSG:4326",
			"savi":"EPSG:4326",
			"savi_min": "EPSG:4326",
            "savi_max": "EPSG:4326",
            "lai": "EPSG:4326",
            },
    },

    "COMPONENTS": {
        "method_inf": 1, # choose infiltration method
        "run_gw" : True, # activate groundwater component
        "method_gw": 0, # choose groundwater transimissivity approach
        #"not used 1": None,
        #"not used 2": None
    },

    "OUTPUT": {
        "output_csv": True, # activate save model outputs (only csv files)
        "output_grid": False, # activate save model outputs (grid files)
        "output_dt": "1M",
        #"not used 1": None,
        #"not used 2": None,
        #"not used 3": None
    },

    "GLOBAL_FACTORS": {
        "uz_kdt": 1.0,
        "uz_kdroot": 1.0,
        "uz_kawc": 1.0,
        "uz_kkast": 1.0,
        "uz_ksigma": 1.0,
        "riv_kksat": 1.0,
        "riv_kdecay": 1.0,
        "riv_kwidth": 1.0,
        "sz_kksat": 1.0,
        "sz_ksy": 1.0,
        "of_kflow": 1.0
    }
}

 