"""DRYP_default_parameters"""

model_name = "DRYP_model_sim"
path_input = None

TERRAIN = {
"path_dem": None, # topography (required)
"path_fdl": None, # flow direction
"path_mask": None, # Model domain
}

RIVER = {
"path_riv_decay": None, # river velocity
"path_riv_len": None, # river length
"path_riv_width": None,# river width
"path_riv_elev": None, # river streambed elevation
"path_riv_Qini": None, # river initial volume
"path_riv_ksat": None, # river hydraulic conductivity
}

WATER_BODIES = {
"path_lake_depth": None, # Lake depth (bathymetry)
"path_pnds_Hmax": None, # pond maximum depth
"path_pnds_Amax": None, # pond maximum area
"path_pnds_Vini": None, # pond initial condition
}

VEGETATION = {
   "path_veg_kc": None,
   "path_veg_lulc": None,
#   "path_veg_nn": None
}

INTERCEPTION = {
"path_veg_rp_tap_depth": None, # plant tap groundwater depth
"path_veg_rp_final_depth": None, # plant extinsion depth
}

RIPARIAN = {
"path_uz_theta_sat": None,
"path_uz_theta_res": None,
"path_uz_theta_awc": None,
"path_uz_theta_wp": None,
"path_uz_root": None,
"path_uz_lambda": None,
"path_uz_psi": None,
"path_uz_ksat": None,
"path_uz_sigmaksat": None,
"path_uz_theta": None,
"path_rp_width": None # riparian corridor width
}

UNSATURATED = {
   "path_uz_theta_sat": None,
   "path_uz_theta_res": None,
   "path_uz_theta_awc": None,
   "path_uz_theta_wp": None,
   "path_uz_root": None,
   "path_uz_lambda": None,
   "path_uz_psi": None,
   "path_uz_ksat": None,
   "path_uz_sigmaksat": None,
   "path_uz_theta": None,
}


SATURATED = {
   "path_sz_mask": None,
   "path_sz_ksat": None,
   "path_sz_sy": None,
   "path_sz_wte": None,
   "path_sz_bc_flux": None,
   "path_sz_bc_head": None,
   "path_sz_bottom": None,
   "path_gw_type": None,
   "path_gw_depth": None,
   "path_gw_bdd": None,
}

METEO = {
   "path_pre": None,
   "path_pet": None,
   "path_aof": None,
#   "Other": None
}

OUTPUT = {
   "path_out_sz": None,
   "path_out_uz": None,
   "path_out_oz": None,
   "path_output": None,
}

SETTINGS_FILES = {
"path_setting": None,
"path_gw_settings": None,
"path_vg_settings": None,
"path_rp_settings": None,
"path_of_settings": None,
"path_projection": None
}
