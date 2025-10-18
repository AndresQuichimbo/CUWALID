from cuwalid.dryp.components.DRYP_json_reader import get_model_settings
from cuwalid.dryp.components.DRYP_io import (
    grid_environment,
	surface_parameters,
	soil_parameters,
	groundwater_parameters,
	interception_parameters,
	water_body_parameters,
)
from cuwalid.dryp.components.DRYP_dams import water_management		

def read_model_parameters(data_in):
    """Reads and prepares all model parameters and settings."""

    # create grid environment
    domain = grid_environment(data_in.fname_surface)

    print("====== > Reading surface and river network parameters")
    topo = surface_parameters(data_in.fname_surface)

    print("====== > Reading hillslope soil hydraulic parameters")
    soil = soil_parameters(topo.grid_size, data_in.fname_soil)

    print("====== > Reading riparian soil hydraulic parameters")
    rsoil = soil_parameters(topo.grid_size, data_in.fname_riparian)

    print("====== > Reading groundwater aquifer hydraulic parameters")
    aquifer = groundwater_parameters(topo.grid_size, data_in.fname_aquifer)

    print("====== > Reading interception parameters")
    vegetation = interception_parameters(
        topo.grid_size, data_in.fname_interception_hillslope)

    print("====== > Reading water body parameters")
    water_bodies = water_body_parameters(
        topo.grid_size, data_in.fname_water_bodies)

    print("====== > Reading water body management")
    water_bodies_management = water_management()

    # setting location and model results
    # env_state.set_output_dir(data_in)
    # env_state.points_output(data_in)

    return domain, topo, soil, rsoil, aquifer, vegetation, water_bodies, water_bodies_management
