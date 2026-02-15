from cuwalid.dryp.components.DRYP_json_reader import get_model_settings
from cuwalid.dryp.components.DRYP_io import (
    grid_environment,
    zone_parameters,
	surface_parameters,
	soil_parameters,
	groundwater_parameters,
	interception_parameters,
	water_body_parameters,
    read_parameter_set_file,
)
from cuwalid.dryp.components.DRYP_dams import water_management		

def read_model_parameters(data_in):
    """Reads and prepares all model parameters and settings."""

    # create grid environment
    domain = grid_environment(data_in.fname_surface)

    print("====== > Reading surface and river network parameters")
    topo = surface_parameters(data_in.fname_surface)

    print("====== > Reading hillslope soil hydraulic parameters")
    soil = soil_parameters(domain.grid_size, data_in.fname_soil)
    # read calibration zones if provided and apply ksat factor
    factor_ksat = read_parameter_set_file(data_in.fname_cal_sets.fname_cal_uz_set)
    ksat_zones = zone_parameters(data_in.fname_cal_sets.fname_cal_uz_zone)
    factor_ksat = ksat_zones.get_scale_factor_zones(factor_ksat)
    soil.apply_factor_ksat(kKsat_soil=factor_ksat)
    soil.apply_factor_Droot(kDroot=None)
    
    print("====== > Reading riparian soil hydraulic parameters")
    rsoil = soil_parameters(domain.grid_size, data_in.fname_riparian)
    # read calibration zones if provided and apply ksat factor
    rsoil.apply_factor_ksat(kKsat_soil=None)
    rsoil.apply_factor_Droot(kDroot=None)

    print("====== > Reading groundwater aquifer hydraulic parameters")
    aquifer = groundwater_parameters(domain.grid_size, data_in.fname_aquifer)
    factor_ksat = read_parameter_set_file(data_in.fname_cal_sets.fname_cal_sz_set) # read calibration factor for zones if provided
    ksat_zones = zone_parameters(data_in.fname_cal_sets.fname_cal_sz_zone) # read calibration zones if provided and apply ksat factor
    factor_ksat = ksat_zones.get_scale_factor_zones(factor_ksat)
    aquifer.apply_factor_ksat(kKsat_aquifer=factor_ksat)
    
    print("====== > Reading interception parameters")
    vegetation = interception_parameters(
        domain.grid_size, data_in.fname_interception_hillslope)

    print("====== > Reading water body parameters")
    water_bodies = water_body_parameters(
        domain.grid_size, data_in.fname_water_bodies)

    print("====== > Reading water body management")
    water_bodies_management = water_management()

    # setting location and model results
    # env_state.set_output_dir(data_in)
    # env_state.points_output(data_in)

    return domain, topo, soil, rsoil, aquifer, vegetation, water_bodies, water_bodies_management
