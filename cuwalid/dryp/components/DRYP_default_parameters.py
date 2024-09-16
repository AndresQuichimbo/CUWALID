"""DRYP_default_parameters"""


default_input = {

   "model_name": "DRYP_model_sim",
   "path_input": "",

   "TERRAIN": {
      "path_dem": "required",
      "path_Qo": None,
      "path_fdl": None,
      "path_riv_decay": None,
      "path_mask": None,
      "path_riv_len": None,
      "path_riv_width": None,
      "path_riv_elev": None
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
      "path_uz_root": None,
      "path_uz_lambda": None,
      "path_uz_psi": None,
      "path_uz_ksat": None,
      "path_uz_sigmaksat": None,
      "path_uz_theta": None,
      "path_riv_ksat": None,
      "path_uz_bottomksat": None
   },

   "SATURATED": {
      "path_sz_mask": None,
      "path_sz_ksat": None,
      "path_sz_sy": None,
      "path_sz_wte": None,
      "path_sz_bc_flux": None,
      "path_sz_bc_head": None,
      "path_sz_bottom": None
   },

   "METEO": {
      "path_pre": None,
      "path_pet": None,
      "path_aof": None,
      #"other": None
   },

   "OUTPUT": {
      "path_out_sz": None,
      "path_out_uz": None,
      "path_out_oz": None,
      "path_output": None,
      "Other": None,
      "path_setting": None,
      "path_projection": None
   },

   "RIPARIAN": {
      "path_rp_theta_sat": None,
      "path_rp_theta_res": None,
      "path_rp_theta_awc": None,
      "path_rp_theta_wp": None,
      "path_rp_rootdepth": None,
      "path_rp_lambdas": None,
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
      "path_veg_rp_par_a": None,
      "path_veg_rp_par_b": None,
      "path_veg_rp_savi_min": None,
      "path_veg_rp_savi_max": None,
      "path_veg_rp_lai": None,
      "path_veg_rp_tap_depth": None,
      "path_veg_rp_final_depth": None,
      "path_veg_rp_fcw": None,
      "path_veg_rp_sca": None
   },

   "GROUNDWATER": {
      "path_gw_depth": None,
      "path_gw_bdd": None,
      "path_gw_2l_bottom": None,
      "path_gw_2l_ksat": None,
      "path_gw_2l_sy": None,
      "path_gw_2l_ss": None,
      "path_gw_2l_wte": None,
      "path_gw_type": None,
      "path_gw_lake_elev": None,
      "path_pnds_vmax": None,
      "path_pnds_shape_par": None
   }
}
