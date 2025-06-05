from cuwalid.dryp.components.DRYP_groundwater_EFD import recharge_routing
from cuwalid.dryp.components.DRYP_io import grid_environment
from cuwalid.dryp.components.DRYP_read_dataset import (
	read_temporal_dataset, read_dataset, read_dataset_interp)

def read_temporal_datasets_and_grid(data_in, topo):
    """Reads all temporal input datasets and sets up the simulation grid."""

    print("====== > Reading precipitation")
    PRE = read_dataset_interp(
        data_in.dt, data_in.data_step['pre'],
        data_in.ini_date, data_in.end_date,
        data_in.data_reading['pre'],
        data_in.data_reproject['pre'],
        data_in.data_interpolate['pre'],
        topo.grid_size,
        topo.lat,
        topo.lon,
        proj=data_in.data_projection['pre'],
        proj_model=data_in.PROJECTION
    )

    print("====== > Reading evapoptranspiration")
    ET0 = read_dataset_interp(
        data_in.dt, data_in.data_step['pet'],
        data_in.ini_date, data_in.end_date,
        data_in.data_reading['pet'],
        data_in.data_reproject['pet'],
        data_in.data_interpolate['pet'],
        topo.grid_size,
        topo.lat,
        topo.lon,
        proj=data_in.data_projection['pet'],
        proj_model=data_in.PROJECTION
    )

    print("====== > Reading vegetation SAVI")
    SAVI = read_dataset_interp(
        data_in.dt, data_in.data_step['savi'],
        data_in.ini_date, data_in.end_date,
        data_in.data_reading['savi'],
        data_in.data_reproject['savi'],
        data_in.data_interpolate['savi'],
        topo.grid_size,
        topo.lat,
        topo.lon,
        proj=data_in.data_projection['savi'],
        proj_model=data_in.PROJECTION,
        step_func=True,
        noskip=False
    )

    print("====== > Reading vegetation LAI")
    LAI = read_dataset_interp(
        data_in.dt, data_in.data_step['lai'],
        data_in.ini_date, data_in.end_date,
        data_in.data_reading['lai'],
        data_in.data_reproject['lai'],
        data_in.data_interpolate['lai'],
        topo.grid_size,
        topo.lat,
        topo.lon,
        proj=data_in.data_projection['lai'],
        proj_model=data_in.PROJECTION,
        step_func=True,
        noskip=False
    )

    print("====== > Reading vegetation Kc")
    Kc = read_dataset_interp(
        data_in.dt, data_in.data_step['kc'],
        data_in.ini_date, data_in.end_date,
        data_in.data_reading['kc'],
        data_in.data_reproject['kc'],
        data_in.data_interpolate['kc'],
        topo.grid_size,
        topo.lat,
        topo.lon,
        proj=data_in.data_projection['kc'],
        proj_model=data_in.PROJECTION,
        step_func=True,
        noskip=False
    )

    print("====== > Reading vegetation fraction")
    av = read_dataset_interp(
        data_in.dt, data_in.data_step['av'],
        data_in.ini_date, data_in.end_date,
        data_in.data_reading['av'],
        data_in.data_reproject['av'],
        data_in.data_interpolate['av'],
        topo.grid_size,
        topo.lat,
        topo.lon,
        proj=data_in.data_projection['av'],
        proj_model=data_in.PROJECTION,
        step_func=True,
        noskip=False
    )

    print("====== > Reading SAVI minimum value")
    SAVImin = read_dataset(
        data_in.dt, data_in.data_step['savi_min'],
        data_in.ini_date, data_in.end_date,
        data_in.data_reading['savi_min'],
        data_in.data_reproject['savi_min'],
        data_in.data_interpolate['savi_min'],
        topo.grid_size
    )

    print("====== > Reading SAVI maximum value")
    SAVImax = read_dataset(
        data_in.dt, data_in.data_step['savi_max'],
        data_in.ini_date, data_in.end_date,
        data_in.data_reading['savi_max'],
        data_in.data_reproject['savi_max'],
        data_in.data_interpolate['savi_max'],
        topo.grid_size
    )

    print("====== > Reading surface flux boundary conditions")
    fluxOF = read_temporal_dataset(
        data_in.fname_TSOF,
        data_in.data_reading['fluxOF'],
        data_in.dt,
        data_in.end_date,
        data_in.ini_date
    )

    print("====== > Reading unsaturated flux boundary conditions")
    fluxUZ = read_temporal_dataset(
        data_in.fname_TSUZ,
        data_in.data_reading['fluxUZ'],
        data_in.dt,
        data_in.end_date,
        data_in.ini_date
    )

    print("====== > Reading saturated flux boundary conditions")
    fluxSZ = read_temporal_dataset(
        data_in.fname_TSSZ,
        data_in.data_reading['fluxSZ'],
        data_in.dt,
        data_in.end_date,
        data_in.ini_date
    )

    print("====== > Reading reservoirs flux boundary conditions")
    fluxWB = read_temporal_dataset(
        data_in.fname_TSWB,
        data_in.data_reading['fluxWB'],
        data_in.dt,
        data_in.end_date,
        data_in.ini_date
    )

    # add variable saturated component
    Qusz = recharge_routing(topo.grid_size)

    # BUILD GRID DOMAIN -----------------------------------------------------
    grid = grid_environment().create_grid(
        topo.grid_ncols,
        topo.grid_nrows,
        topo.grid_xllcorner,
        topo.grid_yllcorner,
        topo.grid_cellsize,
        topo.mask
    )

    # setting model fluxes and state variables
    # env_state = model_environment_status(data_in)

    return PRE, ET0, SAVI, LAI, Kc, av, SAVImin, SAVImax, fluxOF, fluxUZ, fluxSZ, fluxWB, Qusz, grid
