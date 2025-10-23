import numpy as np

from cuwalid.dryp.components.DRYP_ABM_connector import ABMconnector
from cuwalid.dryp.components.DRYP_flow_accumf90 import runoff_routing
from cuwalid.dryp.components.DRYP_groundwater_EFD import gwflow_EFD
from cuwalid.dryp.components.DRYP_infiltration import infiltration
from cuwalid.dryp.components.DRYP_interception import interception
from cuwalid.dryp.components.DRYP_io import (
    get_index_from_coord_file,
    set_initial_conditions,
    zone_parameters)
from cuwalid.dryp.components.DRYP_soil_layer import swbm
from cuwalid.dryp.components.DRYP_ponds import ponds
from cuwalid.dryp.components.DRYP_store_functions import GlobalGridVar
from cuwalid.dryp.components.DRYP_water_bodies import MultiLakeModel

def initialize_core_hydrology_components(data_in, grid, topo, aquifer, water_bodies):
    abc = ABMconnector()
    inf = infiltration(data_in.inf_method)
    cnp = interception()
    swb = swbm(data_in.dt) # soil layer
    swb_rip = swbm(data_in.dt) # riparian layer


    # lakes
    lake_bottom = None
    if water_bodies.depth_slks is not None:
        lake_bottom = topo.surface[water_bodies.ids_lks] - water_bodies.depth_slks
    
        lks = MultiLakeModel(
            lake_bottom,
            water_bodies.depth_slks,
            water_bodies.area_slks,
            water_bodies.name_slks
            )
    else:
        lks = None
        print("Lakes are not active")

    ro = runoff_routing(grid,
                        topo.grid_size,
                        topo.surface[:],
                        topo.FlowDir,
                        topo.Ksat,
                        topo.decay,
                        topo.riv_width,
                        topo.riv_length
                        )
    
    gw = gwflow_EFD(grid,
                    aquifer.Ksat,
                    topo.area_river,
                    aquifer.CHB,
                    data_in.gw_func
                    )
    
    pnds = None
    if water_bodies.id_nodes is not None:
        pnds = ponds(water_bodies.pnds_Amax, water_bodies.pnds_hmax) # ponds
    
    return abc, inf, cnp, swb, swb_rip, ro, gw, lks, pnds

def set_flux_boundary_conditions(data_in, grid, fluxOF, fluxUZ, fluxSZ, fluxWB):
    """Sets up boundary conditions for the model simulation.

    """
    
    idFluxOF, idFluxOF_act = None, None
    idFluxUZ, idFluxUZ_act = None, None
    idFluxSZ, idFluxSZ_act = None, None
    idFluxWB, idFluxWB_act = None, None
    idFluxWBout, idFluxWBout_act = None, None

    # read location of point boundary conditions
    if fluxOF.data_set is not None:
        if data_in.data_reading['fluxOF'] == 0:
            idFluxOF, idFluxOF_act = get_index_from_coord_file(
                grid, data_in.fname_surface.fname_of_bc_flux)

    if fluxUZ.data_set is not None:
        if data_in.data_reading['fluxUZ'] == 0:
            idFluxUZ, idFluxUZ_act = get_index_from_coord_file(
                grid, data_in.fname_soil.fname_uz_bc_flux)

    if fluxSZ.data_set is not None:
        #print(data_in.fname_aquifer.fname_sz_bc_flux)
        if data_in.data_reading['fluxSZ'] == 0:
            idFluxSZ, idFluxSZ_act = get_index_from_coord_file(
                grid, data_in.fname_aquifer.fname_sz_bc_flux)
        
        #elif data_in.data_reading['abs'] == 2:
        #   idFluxOF = extract_id_from_raster(
        #       env_state.grid,
        #       data_in.filename_OF_points
        #       )

    if fluxWB.data_set is not None:
        #print(data_in.fname_aquifer.fname_sz_bc_flux)
        if data_in.data_reading['fluxWB'] == 0:
            idFluxWB, idFluxWB_act = get_index_from_coord_file(
                grid, data_in.fname_water_bodies.fname_wb_bc_flux)
        if data_in.data_reading['fluxWB'] == 0:
            idFluxWBout, idFluxWBout_act = get_index_from_coord_file(
                grid, data_in.fname_water_bodies.fname_wb_bc_flux,
                xlabel="East_out", ylabel="North_out"
            )
            
    return (idFluxOF, idFluxOF_act, idFluxUZ, idFluxUZ_act,
            idFluxSZ, idFluxSZ_act, idFluxWB, idFluxWB_act,
            idFluxWBout, idFluxWBout_act)

def initialize_simulation_state_variables(data_in, topo, grid, aquifer, soil, vegetation, ro):

    gws_mb = []

    etg_agg = np.zeros(topo.grid_size)
    rch_agg = np.zeros(topo.grid_size)
    dt_GW = int(data_in.dt)

    # nodes to perform calculation
    act_nodes = grid.core_nodes[:]
    
    _riv_nodes_mask = np.zeros(topo.grid_size)
    _riv_nodes_mask[act_nodes] = 1
    topo.river_cells = _riv_nodes_mask * topo.river_cells
    
    riv_nodes = np.array(np.where(topo.river_cells > 0)[0], dtype=int)
    
    act_riv_nodes = None
    # nodes to transfer information from river grid
    # to core nodes grid (active nodes)
    if riv_nodes.size > 0:
        act_riv_nodes = np.where(topo.river_cells[act_nodes] > 0)[0]

    # find location of lakes
    id_lakes = topo.surface[act_nodes] - topo.bathymetry[act_nodes]
    #print(id_lakes)
    id_lakes = np.where(id_lakes > 0)[0]
    #print(id_lakes)

    # locations ponds
    #id_ponds = None

    # INITIAL CONDITIONS =========
    # surface water
    ro.SSZ = topo.Qo[:]

    # set initial conditions for soil and groundwater
    head = aquifer.head[:]
    theta = soil.theta[:]
    river_sat_deficit = np.zeros(topo.grid_size)

    save_rz_var = False
    rtheta = None
    if riv_nodes.size > 0:
        save_rz_var = True
        rtheta = soil.theta[riv_nodes]
        
    # update initial conditions
    head_act_nodes_updated, Duz0, z_extintion, river_sat_deficit_act_nodes_updated, Ft0, SORP0, t_0, dry_day = (
        set_initial_conditions(
            topo.grid_size, soil.Droot[act_nodes],
            head[act_nodes],
            topo.surface[act_nodes],
            topo.bathymetry[act_nodes],
            vegetation.extintion_depth[act_nodes],
            topo.grid_cellsize,
            data_in.run_GW
        )
    )
    head[act_nodes] = head_act_nodes_updated
    river_sat_deficit[act_nodes] = river_sat_deficit_act_nodes_updated
    
    #if riv_nodes.size > 0:
    #   river_sat_deficit = river_sat_deficit[act_riv_nodes]

    runoff = np.zeros(topo.grid_size)
    recharge = np.zeros(topo.grid_size)
    baseflow = np.zeros(topo.grid_size)
    AOF_threshold = np.ones(topo.grid_size)

    return (gws_mb, etg_agg, rch_agg, dt_GW, act_nodes, riv_nodes, act_riv_nodes,
            id_lakes, head, theta, river_sat_deficit, save_rz_var, rtheta,
            Duz0, z_extintion, Ft0, SORP0, t_0, dry_day,
            runoff, recharge, baseflow, AOF_threshold)

def initialize_output_arrays(data_in):#, riv_nodes, water_bodies):
    # initialize array to store model results
    point_var = GlobalGridVar(data_in.ini_date,
                              data_in.dt_results_csv, data_in.save_results,
                              data_in.store.var_point)
    zone_var = GlobalGridVar(data_in.ini_date,
                              data_in.dt_results_csv, data_in.save_results,
                              data_in.store.var_point)
    grid_var = GlobalGridVar(data_in.ini_date,
                             data_in.dt_results, data_in.save_netcdf,
                             data_in.store.var_grid)
    grid_veg = GlobalGridVar(data_in.ini_date,
                             data_in.dt_results, data_in.save_netcdf,
                             data_in.store.var_grid)
    grid_rmax = GlobalGridVar(data_in.ini_date,
                              data_in.dt_results, data_in.save_netcdf,
                              data_in.store.var_grid,
                              store_max=data_in.store_rmax, nstep_day=data_in.nstep_day)
    grid_vmax = GlobalGridVar(data_in.ini_date,
                              data_in.dt_results, data_in.save_netcdf,
                              data_in.store.var_grid,
                              store_max=data_in.store_vmax, nstep_day=data_in.nstep_day)
    total_var = GlobalGridVar(data_in.ini_date,
                              data_in.dt_results, data_in.save_results,
                              data_in.store.var_avg)

    #grid_rpvar, total_rpvar = None, None
    # create grid and average results from the riparian area
    #if riv_nodes.size > 0:
    grid_rpvar = GlobalGridVar(data_in.ini_date,
                                   data_in.dt_results, data_in.save_netcdf,
                                   data_in.store.var_grid_rp)
    total_rpvar = GlobalGridVar(data_in.ini_date,
                                    data_in.dt_results, data_in.save_results,
                                    data_in.store.var_grid_rp)

    #grid_pndvar, total_pndvar = None, None
    # create grid and average results from the water bodies (ponds)
    #if water_bodies.id_nodes is not None:
    grid_pndvar = GlobalGridVar(data_in.ini_date,
                                    data_in.dt_results, data_in.save_netcdf,
                                    data_in.store.var_grid_pnd)
    total_pndvar = GlobalGridVar(data_in.ini_date,
                                     data_in.dt_results, data_in.save_results,
                                     data_in.store.var_grid_pnd)
    #grid_lks = None
    # create grid and average results from the water bodies (lakes)        
    #if water_bodies.ids_slks is not None:
    grid_lks = GlobalGridVar(data_in.ini_date,
                                 data_in.dt_results, data_in.save_netcdf,
                                 data_in.store.var_grid_lks) # lakes
                                     
    return (#idOF, idOF_act, idUZ, idUZ_act, idGW, idGW_act,
            point_var, grid_var, grid_rmax, grid_vmax, total_var,
            grid_rpvar, total_rpvar, grid_pndvar, total_pndvar,
            grid_veg, grid_lks, zone_var)


def setup_monitoring_nodes(grid, data_in):
    """Sets up monitoring nodes for discharge, soil moisture, and groundwater.
    
    Parameters:
    grid : Landlab Grid
        The Landlab grid object.
        data_in : object
        Input data object containing file paths for monitoring points.
    
    Returns: tuple
    -------
    idOF : tuple
        numpy array of indices and core indices of discharge monitoring points.
    idUZ : tuple
        numpy array of indices and core indices of soil moisture monitoring points.
    idGW : tuple
        numpy array of Indices and core indices of groundwater monitoring points.
    """
    

    # Output variables and location
    idOF = get_index_from_coord_file(grid, data_in.fname_DISpoints)  # Discharge monitoring points
    idUZ = get_index_from_coord_file(grid, data_in.fname_SMDpoints)  # Soil moisture monitoring points
    idGW = get_index_from_coord_file(grid, data_in.fname_GWpoints) # groundwater monitoring points

    # add nodes and core nodes for zone ouptuts
    zones = zone_parameters(data_in.fname_zone_outputs)
    
    idzone, size_zone = zones.extract_zone_info(grid.core_nodes)
    idzone_core, _ = zones.get_zone_info_from_core_nodes(grid.core_nodes)
    idzone_info = (idzone, idzone_core, size_zone)
    
    return idOF, idUZ, idGW, idzone_info