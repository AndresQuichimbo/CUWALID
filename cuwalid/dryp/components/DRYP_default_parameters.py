"""DRYP_default_parameters"""


default_input = {

   "model_name": "DRYP_model_sim",
   "path_input": "",

   "TERRAIN": {
      "path_dem": "required", # Digital elevation model
      "path_Qo": None, # initial channel storage
      "path_fdl": None, # flow direction in landlab format
      "path_riv_decay": None, # river flow velocity
      "path_mask": None, # basin mask. model active domain
      "path_riv_len": None, # river lenght
      "path_riv_width": None, # river width
      "path_riv_elev": None, # tiver stream bottom elevation
      "path_of_bc_flux": None, # flux boundary condition overland flow
      
   },

   "VEGETATION": {
      "path_veg_kc": None,
      "path_veg_lulc": None,
      #"path_veg_nn": None
   },

   "UNSATURATED": {
      "path_uz_theta_sat": None,
      "path_uz_theta_res": None,
      "path_uz_theta_awc": None,
      "path_uz_theta_wp": None,
      "path_uz_rootdepth": None,
      "path_uz_lambda": None,
      "path_uz_psi": None,
      "path_uz_ksat": None,
      "path_uz_sigmaksat": None,
      "path_uz_theta": None, # initial conditions
      "path_riv_ksat": None,
      "path_uz_bottomksat": None,
      "path_uz_bc_flux": None,
   },

   "SATURATED": {
      "path_sz_mask": None,
      "path_sz_ksat": None,
      "path_sz_sy": None,
      "path_sz_wte": None,
      "path_sz_bc_flux": None,
      "path_sz_bc_head": None,
      "path_sz_bottom": None,
      "path_sz_depth": None,
      "path_sz_bdd": None,
      "path_sz_type": None, # aquifer type
   },

   "METEO": {
      "path_pre": None,
      "path_pet": None,
      "path_aof": None,
  		"path_lai": None,
		"path_savi": None,
		"path_kc": None,
   	"path_TSOF": None,
   	"path_TSUZ": None,
   	"path_TSSZ": None,
   	"path_TSav": None, # vegetation cover fraction
      "path_TSWB": None, # Variable flux for water bodies and dams
   },

   "OUTPUT": {
      "path_out_sz": None,
      "path_out_uz": None,
      "path_out_oz": None,
      "path_out_zones": None,
      "path_output": None,
      "path_setting": None,
      "path_store_settings": None
   },

   "RIPARIAN": {
      "path_rp_theta_sat": None,
      "path_rp_theta_res": None,
      "path_rp_theta_awc": None,
      "path_rp_theta_wp": None,
      "path_rp_rootdepth": None,
      "path_rp_lambda": None,
      "path_rp_psi": None,
      "path_rp_ksat": None,
      "path_rp_sigmaksat": None,
      "path_rp_theta": None,
      "path_rp_width": None
   },

   "INTERCEPTION": {
      "path_veg_lulc_frac": None,
      "path_veg_hs_savi": None,
      "path_veg_hs_par_a": None,
      "path_veg_hs_par_b": None,
      "path_veg_hs_savi_min": None,
      "path_veg_hs_savi_max": None,
      "path_veg_hs_lai": None,
      "path_veg_hs_tap_depth": None,
      "path_veg_hs_extinction_depth": None,
      "path_veg_hs_fcw": None,
      "path_veg_hs_sca": None,
      "path_veg_rp_par_a": None,
      "path_veg_rp_par_b": None,
      "path_veg_rp_savi_min": None,
      "path_veg_rp_savi_max": None,
      "path_veg_rp_lai": None,
      "path_veg_rp_tap_depth": None,
      "path_veg_rp_extinction_depth": None,
      "path_veg_rp_fcw": None,
      "path_veg_rp_sca": None
   },

   #"GROUNDWATER": {
   ##   "path_gw_depth": None,
   ##   "path_gw_bdd": None,
   #   "path_gw_2l_bottom": None,
   #   "path_gw_2l_ksat": None,
   #   "path_gw_2l_sy": None,
   #   "path_gw_2l_ss": None,
   #   "path_gw_2l_wte": None, 
   ##   "path_gw_type": None, # aquifer type
   ##   "path_gw_lake_elev": None, # lakes bathymetry
   ##   "path_pnds_hmax": None, # ponds max depth
   ##   "path_pnds_Amax": None, # ponds maximum extend
   #},

   "WATER_BODIES": {
      "path_lake_ids": None, # lakes labels as integers
      "path_lake_depth": None, # lakes bathymetry
      "path_pnd_hmax": None, # ponds max depth
      "path_pnd_Amax": None, # ponds maximum extend
      "path_pnd_Vo": None, # ponds volume of water
      "path_wb_bc_flux": None, # water bodies boundary conditions
      "path_slks_depth": None, # shallow lakes depth
      "path_slks_area": None, # shallow lakes area
   },

   "CALIBRATION": {
      "path_cal_of_zone": None,
      "path_cal_uz_zone": None,
      "path_cal_sz_zone": None,
      "path_cal_rp_zone": None,
      "path_cal_st_zone": None,
      "path_cal_of_set": None,
      "path_cal_uz_set": None,
      "path_cal_sz_set": None,
      "path_cal_rp_set": None,
      "path_cal_st_set": None,
   #   "path_cal_sz": None,
   #   "path_cal_uz": None,
   #   "path_cal_oz": None,
   #   "path_cal_gw": None,
   #   "path_cal_riv": None,
   #   "path_cal_wb": None,
   #   "path_cal_method": "Nash-Sutcliffe",
   #   "path_cal_start": None,
   #   "path_cal_end": None
   },

   "PARALLEL": {
      "path_subdomains_oz": None, # raster map with subdomains for parallel processing
      "path_subdomains_sz": None, # raster map with subdomains for parallel processing
      "path_subdomains_uz": None, # raster map with subdomains for parallel processing
      "path_basin_order": None, # raster map with basin order for parallel processing
   },

}
