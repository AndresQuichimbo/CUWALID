from cuwalid.dryp.components.DRYP_store_functions import save_map_to_rasterfile#, save_map_to_rastergrid


def save_model_outputs(data_in, total_var, point_var, zone_var, # csv variables
                       total_rpvar, total_pndvar, # csv variables
                       grid_var, grid_rmax, grid_vmax, # grid variables
                       grid_rpvar, grid_pndvar, grid_veg, grid_lks, # grid variables
                       grid, head, theta, ssz, rtheta, topo, pnd_Vo, # raster variables
                       act_nodes, riv_nodes, lks_nodes, pnd_nodes, # node indices
                       projection=None):
    """Saves model outputs to files (netCDF, CSV, raster)

    Parameters
    ----------
    data_in : DRYPInputData
        Input data object containing file names for saving outputs
    total_var : DRYPTimeSeriesStore
        Object storing average temporal variables for CSV output
    point_var : DRYPTimeSeriesStore
        Object storing point temporal variables for CSV output
    zone_var : DRYPTimeSeriesStore
        Object storing zone temporal variables for CSV output
    total_rpvar : DRYPTimeSeriesStore
        Object storing average riparian zone temporal variables for CSV output
    total_pndvar : DRYPTimeSeriesStore
        Object storing average pond temporal variables for CSV output
    grid_var : DRYPTimeSeriesStore
        Object storing gridded temporal variables for netCDF output
    grid_rmax : DRYPTimeSeriesStore
        Object storing gridded temporal maximum values at streams for netCDF output
    grid_vmax : DRYPTimeSeriesStore
        Object storing gridded temporal maximum values for netCDF output
    grid_rpvar : DRYPTimeSeriesStore
        Object storing riparian zone gridded temporal variables for netCDF output
    grid_pndvar : DRYPTimeSeriesStore
        Object storing pond gridded temporal variables for netCDF output
    grid_veg : DRYPTimeSeriesStore
        Object storing vegetation gridded temporal variables for netCDF output
    grid : DRYPGrid
        Model grid object
    head : numpy array
        Array of groundwater head values
    theta : numpy array
        Array of soil moisture values
    ssz : numpy array
        Array of channel flow values
    rtheta : numpy array
        Array of riparian zone soil moisture values
    topo : DRYPTopo
        Topography object containing latitude and longitude arrays
    pnd_Vo : numpy array
        Array of pond water volume values
    act_nodes : numpy array
        Array of active node indices
    riv_nodes : numpy array
        Array of river node indices
    lks_nodes : numpy array
        Array of lake node indices
    pnd_nodes : numpy array
        Array of pond node indices
    projection : osgeo.osr.SpatialReference, optional
        Projection information for geospatial outputs (default is None)

    """

    print("<==== saving model average temporal outputs")
    # SAVE AVERAGE VALUES OF VARIABLES: CSV-FILES
    # var_name = ['pre', 'pet', 'run', 'aet', 'inf', 'tht',
    #     'rch', 'egw', 'wte', 'gdh', 'twsc', 'chb', 'tls']
    # length_var = np.ones(len(var_name), dtype=int)
    total_var.save_csv_var(data_in.fnameTS_avg,  # var_name,
                           # length_var,
                           multi_files=False)

    print("<==== saving model point temporal outputs")

    # SAVE VARIABLES AT POINT LOCATION: CSV-FILES
    # name of variables to store
    # var_name = ['aet', 'inf', 'dis', 'tht', 'rch', 'wte', 'gdh', 'ssz']
    point_var.save_csv_var(data_in.fnameTS_point)  # , var_name, length_var)

    print("<==== saving model zone temporal outputs")

    # SAVE VARIABLES AT POINT LOCATION: CSV-FILES
    # name of variables to store
    # var_name = ['aet', 'inf', 'dis', 'tht', 'rch', 'wte', 'gdh', 'ssz']
    zone_var.save_csv_var(data_in.fnameTS_point+"zone_")  # , var_name, length_var)

    print("<==== saving model gridded temporal outputs")

    # SAVE VARIABLES AS GRIDS-NETCDF FILES
    # name of variables to store as grid
    # var_name = ['pre', 'pet', 'dis', 'aet', 'inf', 'run', 'tht',
    #     'rch', 'egw', 'wte', 'gdh', 'twsc']
    grid_var.save_netCDF_var(data_in.fnameTS_grid + '.nc',
                              topo.lat, topo.lon, act_nodes,
                              projection=projection
                              )  # , var_name

    # save grided model maximum values at streams - result datasets
    #if grid_rmax.store_max is True:
    print("<==== saving model gridded temporal maximum values at streams outputs")
    #if riv_nodes.size > 0:
    grid_rmax.save_netCDF_var(data_in.fnameTS_grid + 'rmax.nc',
                                      topo.lat, topo.lon, riv_nodes,
                                      projection=projection
                                      )  # , var_name

    # save grided model maximum values at streams - result datasets
    print("<==== saving model gridded temporal lake outputs")
    #if water_bodies.ids_slks.size > 0:
    grid_lks.save_netCDF_var(data_in.fnameTS_grid + 'lks.nc',
                                      topo.lat, topo.lon, lks_nodes,
                                      projection=projection
                                      )  # , var_name

    # save maximum grided model result datasets
    #if grid_vmax.store_max is True:
    print("<==== saving model gridded temporal maximum values outputs")
    grid_vmax.save_netCDF_var(data_in.fnameTS_grid + 'vmax.nc',
                                  topo.lat, topo.lon, act_nodes,
                                  projection=projection
                                  )  # , var_name

    # SAVE VARIABLES FROM THE RIPARIAN ZONE
    #if riv_nodes.size > 0:
    print("<==== saving riparian zone temporal outputs")
        # var_name = ['aet', 'fch', 'tls', 'tht', 'ssz']
        # save grided model result datasets
    grid_rpvar.save_netCDF_var(data_in.fnameTS_grid + 'rp.nc',
                                   topo.lat, topo.lon, riv_nodes,
                                   projection=projection
                                   )  # , var_name

        # save average riparian zone variables in a csv file
        # length_var = np.ones(len(var_name), dtype=int)
    total_rpvar.save_csv_var(data_in.fnameTS_avg + 'rp',  # var_name,
                                 # length_var,
                                 multi_files=False)
    
    # SAVE VARIABLES FROM VEGETATION
    print("<==== saving vegetation gridded temporal outputs")
    # var_name = ['pth', 'eca', 'scz']
    # save grided model result datasets
    grid_veg.save_netCDF_var(data_in.fnameTS_grid + 'veg.nc',
                                    topo.lat, topo.lon, act_nodes,
                                    projection=projection
                                    )  # , var_name

    # SAVE VARIABLES FROM PONDS
    print("<==== saving water bodies temporal outputs")
    #if water_bodies.id_nodes is not None:
        # var_name = ['aet', 'fch', 'tls', 'tht', 'ssz']
        # save grided model result datasets
    grid_pndvar.save_netCDF_var(data_in.fnameTS_grid + 'pnd.nc',
                                    topo.lat, topo.lon, pnd_nodes,
                                    projection=projection
                                    )  # , var_name

        # save average values in csv
        # length_var = np.ones(len(var_name), dtype=int)
    total_pndvar.save_csv_var(data_in.fnameTS_avg + 'pnd',  # var_name,
                                  # length_var,
                                  #multi_files=False
                                  )

    # SAVE RASTER FILES FOR INITIAL CONDITIONS
    print("<==== saving raster files for initial conditions")

    # Save water table for initial conditions
    save_map_to_rasterfile(grid, head,
                           data_in.fnameTS_avg + '_wte_ini.asc')

    # Save soil moisture for initial conditions
    save_map_to_rasterfile(grid, theta,
                           data_in.fnameTS_avg + '_tht_ini.asc')

    # Save channel flow initial conditions
    save_map_to_rasterfile(grid, ssz,
                           data_in.fnameTS_avg + '_Q_ini.asc')

    if riv_nodes.size > 0:
        # Save riparian soil moisture for initial conditions
        theta[riv_nodes] = rtheta
        save_map_to_rasterfile(grid, theta,
                               data_in.fnameTS_avg + '_tht_rp_ini.asc')

    if pnd_nodes is not None:
        # Save pond water volume for initial conditions
        theta[:] = -9999
        theta[pnd_nodes] = pnd_Vo
        save_map_to_rasterfile(grid, theta,
                               data_in.fnameTS_avg + '_V_pnd_ini.asc')

