import numpy as np
from cuwalid.dryp.components.DRYP_io import create_grid_from_extent
from cuwalid.dryp.components.DRYP_flow_accumf90 import runoff_routing
from cuwalid.dryp.components.DRYP_groundwater_EFD_geo import gwflow_EFD

# Part of this code has been developed using AI tools (ChatGPT)
# to assist with parallelization and data handling.
# We user is responsible for verifying the correctness and
# performance of the code, and for ensuring that it meets the
# needs of the project.

# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_basin_ids(catchment_mask):
    """Extract unique basin IDs from catchment mask (excluding 0 = sea)"""
    if catchment_mask is None:
        return []

    unique_ids = np.unique(catchment_mask)
    basin_ids = unique_ids[unique_ids > 0]  # Exclude sea (0)
    return basin_ids.tolist()


def assign_basins_to_rank(basin_ids, rank, size):
    """Assign basin IDs to MPI ranks in round-robin order."""
    if size <= 1:
        return list(basin_ids)

    return [basin_id for index, basin_id in enumerate(basin_ids) if index % size == rank]


_BASIN_REGION_CACHE = {}


def _get_basin_region(basin_id, catchment_mask):
    # called several times per step per basin; the mask is static, so cache by identity
    key = (id(catchment_mask), basin_id)
    cached = _BASIN_REGION_CACHE.get(key)
    if cached is not None and cached[0] is catchment_mask:
        return cached[1]

    basin_mask = (catchment_mask == basin_id)
    if not np.any(basin_mask):
        raise ValueError(f"Basin ID {basin_id} was not found in the catchment mask")

    rows, cols = np.where(basin_mask)
    row_min, row_max = rows.min(), rows.max()
    col_min, col_max = cols.min(), cols.max()
    basin_region_mask = basin_mask[row_min:row_max+1, col_min:col_max+1].copy()

    result = (basin_region_mask, row_min, row_max, col_min, col_max)
    _BASIN_REGION_CACHE[key] = (catchment_mask, result)
    return result


def _get_global_to_local_lookup(basin_input, active_only=True):
    mask = basin_input['mask'].flatten()
    global_nodes = basin_input['global_nodes']

    if active_only:
        return {
            int(global_id): local_id
            for local_id, global_id in enumerate(global_nodes)
            if mask[local_id]
        }

    return {
        int(global_id): local_id
        for local_id, global_id in enumerate(global_nodes)
    }


def _extract_basin_array(array, catchment_mask, row_min, row_max, col_min, col_max):
    data = np.asarray(array)
    if data.ndim == 2:
        return data[row_min:row_max+1, col_min:col_max+1].copy()
    if data.ndim == 1:
        if data.size != catchment_mask.size:
            raise ValueError(
                f"Expected array of size {catchment_mask.size}, received {data.size}")
        return data.reshape(catchment_mask.shape)[row_min:row_max+1, col_min:col_max+1].copy()

    raise ValueError(f"Unsupported array dimension: {data.ndim}D")


def extract_basin_data(basin_id, domains, grid_metadata, grid=True):
    """
    Extract data for a specific basin from the full grid.
    Returns a dictionary with basin-specific grid and data arrays.
    """
    basin_region_mask, row_min, row_max, col_min, col_max = _get_basin_region(
        basin_id, domains)
    nrows_basin = row_max - row_min + 1
    ncols_basin = col_max - col_min + 1

    # Create grid for this basin
    if grid:
        grid = create_grid_from_extent(
            ncols_basin, nrows_basin,
            grid_metadata['xllcorner'] + col_min * grid_metadata['cellsize'],
            grid_metadata['yllcorner'] + row_min * grid_metadata['cellsize'],
            grid_metadata['cellsize'],
            active_domain=basin_region_mask.flatten(),
        )
    else:
        grid = None

    global_nodes = np.arange(domains.size, dtype=int).reshape(domains.shape)[
        row_min:row_max+1, col_min:col_max+1
    ].flatten()

    return {
        'basin_id': basin_id,
        'grid': grid,
        'grid_size': nrows_basin*ncols_basin,
        'mask': basin_region_mask,
        'bbox': (row_min, row_max, col_min, col_max),
        'shape': (nrows_basin, ncols_basin),
        'global_nodes': global_nodes,
    }


def combine_basin_results_into_world_halo(basin_id, catchment_mask, basin_result, halo =1, world_data=None, world_grid_shape=None, flatten=False):
    """Combine results from one basin into a full world array"""
    if world_data is None:
        if world_grid_shape is None:
            world_grid_shape = catchment_mask.shape
        world_data = np.zeros(world_grid_shape, dtype=np.asarray(basin_result).dtype)

    if basin_result is None:
        return world_data

    if world_grid_shape is None:
        world_grid_shape = catchment_mask.shape

    needs_flatten = flatten or world_data.ndim == 1
    if world_data.ndim == 1:
        world_view = world_data.reshape(world_grid_shape)
    else:
        world_view = world_data

    basin_region_mask, row_min, row_max, col_min, col_max = _get_basin_region(
        basin_id, catchment_mask)
    row_min_h = max(0, row_min - halo)
    row_max_h = min(catchment_mask.shape[0]-1, row_max + halo)
    col_min_h = max(0, col_min - halo)
    col_max_h = min(catchment_mask.shape[1]-1, col_max + halo)
    bounds = np.array([[row_min, row_max, col_min, col_max]])
    nrows = row_max_h - row_min_h + 1
    ncols = col_max_h - col_min_h + 1
    
    extended_mask = np.ones((nrows, ncols), dtype=bool)
 
    # np.savetxt(
    #     f"/shared/home1/c.c23086054/CUWALID/cuwalid/dryp/bounds_combine_{basin_id}.csv",
    #     bounds,
    #     fmt="%d",
    #     delimiter=",",
    #     header="row_min,row_max,col_min,col_max",
    #     comments=""
    # )
    # basin_array = np.asarray(basin_result).reshape(basin_region_mask.shape)
    # print("-----------------------------------------------------------------------------------------------")
    # print("basin_region_mask.shape: ", basin_region_mask.shape)
    # print("extended_mask.shape: ", extended_mask.shape)
    # print("basin_result.shape: ", basin_result.shape)
    basin_array = np.asarray(basin_result).reshape(extended_mask.shape)
    # row_min>row_max?
    # print("row_min: ", row_min)
    # print("row_max: ", row_max)
    local_row_min = row_min - row_min_h
    local_row_max = row_max - row_min_h
    local_col_min = col_min - col_min_h
    local_col_max = col_max - col_min_h


    # basin_array = basin_array[row_min:row_max+1, col_min:col_max+1]
    basin_array = basin_array[
        local_row_min:local_row_max+1,
        local_col_min:local_col_max+1
    ]
    world_region = world_view[row_min:row_max+1, col_min:col_max+1]
    # print("basin_array.shape: ", basin_array.shape)
    # print("-----------------------------------------------------------------------------------------------")
    
    world_region[basin_region_mask] = basin_array[basin_region_mask]

    if needs_flatten:
        return world_view.ravel()

    return world_view

def extract_basin_forcing_halo(basin_id, catchment_mask, world_forcing_arrays, halo=1):
    """Extract forcing data for a specific basin"""
    basin_region_mask, row_min, row_max, col_min, col_max = _get_basin_region(
        basin_id, catchment_mask)
    forcing_data = {}
    row_min_h = max(0, row_min - halo)
    row_max_h = min(catchment_mask.shape[0]-1, row_max + halo)
    col_min_h = max(0, col_min - halo)
    col_max_h = min(catchment_mask.shape[1]-1, col_max + halo)
    nrows = row_max_h - row_min_h + 1
    ncols = col_max_h - col_min_h + 1

    # Extended mask: all cells in bounding box, regardless of basin
    extended_mask = np.ones((nrows, ncols), dtype=bool)

    for key, array in world_forcing_arrays.items():
        basin_array = _extract_basin_array(
            array, catchment_mask, row_min_h, row_max_h, col_min_h, col_max_h)
        # basin_array[~basin_region_mask] = 0print("basin_region_mask.shape: ", basin_region_mask.shape)
        basin_array[~extended_mask] = 0
        forcing_data[key] = basin_array.flatten()

    return forcing_data

def extract_basin_forcing(basin_id, catchment_mask, world_forcing_arrays):
    """Extract forcing data for a specific basin"""
    basin_region_mask, row_min, row_max, col_min, col_max = _get_basin_region(
        basin_id, catchment_mask)
    forcing_data = {}
    for key, array in world_forcing_arrays.items():
        basin_array = _extract_basin_array(
            array, catchment_mask, row_min, row_max, col_min, col_max)
        basin_array[~basin_region_mask] = 0
        forcing_data[key] = basin_array.flatten()

    return forcing_data

def extract_basin_forcing_with_halo(
    basin_domain,
    world_forcing_arrays,
    mask_inactive=True,
):
    """
    Extract forcing data for a basin INCLUDING halo cells.

    Parameters
    ----------
    basin_domain : dict
        Output from extract_basin_data_with_halo().
        Must contain:
            - 'global_nodes'
            - 'mask' (core + halo)
            - 'core_mask' (optional)
    world_forcing_arrays : dict
        Global arrays (flattened or 2D).
    mask_inactive : bool
        If True, inactive cells (outside mask) are zeroed.

    Returns
    -------
    forcing_data : dict
        Local (halo-aware) flattened arrays of size N_local_cells.
    """

    global_nodes = basin_domain['global_nodes']
    region_mask = basin_domain['mask'].flatten()

    forcing_data = {}

    for key, array in world_forcing_arrays.items():

        data = np.asarray(array)

        # --- Handle 2D arrays ---
        if data.ndim == 2:
            data = data.flatten()

        # --- Handle 1D arrays ---
        elif data.ndim == 1:
            pass

        else:
            raise ValueError(f"Unsupported array dimension: {data.ndim}D")

        # --- Extract halo-aware local array ---
        local_array = data[global_nodes].copy()

        # --- Mask inactive cells if requested ---
        if mask_inactive:
            local_array[~region_mask] = 0

        forcing_data[key] = local_array

    return forcing_data

def extract_basin_parameters(basin_id, catchment_mask, world_parameter_arrays, mask_inactive=False):
    """Extract parameter data for a specific basin"""
    basin_region_mask, row_min, row_max, col_min, col_max = _get_basin_region(
        basin_id, catchment_mask)
    parameter_data = {}
    for key, array in world_parameter_arrays.items():
        if isinstance(array, np.ndarray):
            basin_array = _extract_basin_array(
                array, catchment_mask, row_min, row_max, col_min, col_max)
            if mask_inactive:
                basin_array[~basin_region_mask] = 0
            parameter_data[key] = basin_array.flatten()
        else:
            parameter_data[key] = array

    return parameter_data

def extract_basin_parameters_with_halo(
    basin_domain,
    catchment_mask,
    world_parameter_arrays,
    mask_inactive=False
):
    """
    Extract parameters INCLUDING halo region.
    """

    row_min, row_max, col_min, col_max = basin_domain['bbox']
    extended_mask = basin_domain['mask']        # includes halo
    core_mask = basin_domain['core_mask']       # only real cells

    parameter_data = {}

    for key, array in world_parameter_arrays.items():
        if isinstance(array, np.ndarray):

            data = np.asarray(array)

            # extract using HALO bbox
            if data.ndim == 2:
                local = data[row_min:row_max+1, col_min:col_max+1].copy()

            elif data.ndim == 1:
                local = data.reshape(catchment_mask.shape)[
                    row_min:row_max+1, col_min:col_max+1
                ].copy()
            else:
                raise ValueError(f"Unsupported array dimension: {data.ndim}D")

            # flatten to match your solver
            local = local.flatten()

            if mask_inactive:
                # IMPORTANT: only mask OUTSIDE extended domain
                local[~extended_mask.flatten()] = 0

            parameter_data[key] = local

        else:
            parameter_data[key] = array

    return parameter_data

def combine_all_basin_results_into_world(all_basin_results, catchment_mask, world_grid_shape):
    """Combine results from all basins back into a full world array"""
    combined_discharge = np.zeros(world_grid_shape)
    if all_basin_results is None:
        return combined_discharge

    # gather() on root returns list-of-lists; flatten to list of basin dicts
    if len(all_basin_results) > 0 and isinstance(all_basin_results[0], list):
        flat_results = []
        for worker_results in all_basin_results:
            flat_results.extend(worker_results)
    else:
        flat_results = all_basin_results

    for result in flat_results:
        basin_id = result['basin_id']
        discharge = result['discharge']
        # Get bounding box for this basin
        basin_mask = (catchment_mask == basin_id)
        rows, cols = np.where(basin_mask)
        #print(rows, cols)
        #row_min, row_max, col_min, col_max = get_basin_bbox(basin_id, catchment_mask)
        
        # Reshape discharge to basin grid shape and place into combined array
        nrows_basin = rows.max() - rows.min() + 1
        ncols_basin = cols.max() - cols.min() + 1
        combined_discharge[rows.min():rows.max()+1, cols.min():cols.max()+1] = discharge.reshape(nrows_basin, ncols_basin)
    
    return combined_discharge
def combine_basin_results_into_world_with_halo(
    basin_domain,
    basin_result,
    global_array
):
    """
    Write back ONLY CORE values from a halo domain.
    """

    global_nodes = basin_domain['global_nodes']
    core_mask = basin_domain['core_mask'].flatten()

    basin_result = np.asarray(basin_result)

    # safety check
    assert len(basin_result) == len(global_nodes), \
        "Local result size mismatch with domain"

    # extract only core
    core_values = basin_result[core_mask]
    core_global_nodes = global_nodes[core_mask]

    # write back
    global_array[core_global_nodes] = core_values

    return global_array


def combine_basin_results_into_world(basin_id, catchment_mask, basin_result, world_data=None, world_grid_shape=None, flatten=False):
    """Combine results from one basin into a full world array"""
    if world_data is None:
        if world_grid_shape is None:
            world_grid_shape = catchment_mask.shape
        world_data = np.zeros(world_grid_shape, dtype=np.asarray(basin_result).dtype)

    if basin_result is None:
        return world_data

    if world_grid_shape is None:
        world_grid_shape = catchment_mask.shape

    needs_flatten = flatten or world_data.ndim == 1
    if world_data.ndim == 1:
        world_view = world_data.reshape(world_grid_shape)
    else:
        world_view = world_data

    basin_region_mask, row_min, row_max, col_min, col_max = _get_basin_region(
        basin_id, catchment_mask)
    basin_array = np.asarray(basin_result).reshape(basin_region_mask.shape)
    world_region = world_view[row_min:row_max+1, col_min:col_max+1]
    world_region[basin_region_mask] = basin_array[basin_region_mask]

    if needs_flatten:
        return world_view.ravel()

    return world_view

def get_basin_bbox(basin_id, catchment_mask):
    """Get bounding box for a specific basin"""
    _, row_min, row_max, col_min, col_max = _get_basin_region(
        basin_id, catchment_mask)
    return row_min, row_max, col_min, col_max

def setup_basin_model(basin_data):
    """
    Read and set all model parameters/arrays for a single basin.
    Returns a dictionary with everything needed to run the basin model.
    """
    grid = basin_data['grid']
    grid_size = basin_data['grid_size']
    basin_id = basin_data['basin_id']
    
    return {
        'basin_id': basin_id,
        'grid': grid,
        'grid_size': grid_size,
    }


def map_global_nodes_to_local(basin_input, global_node_ids):
    """Map global flattened node ids into a basin-local indexing scheme."""
    if global_node_ids is None:
        return np.array([], dtype=int)

    lookup = _get_global_to_local_lookup(basin_input)
    local_nodes = [
        lookup[int(global_id)]
        for global_id in np.asarray(global_node_ids, dtype=int).ravel()
        if int(global_id) in lookup
    ]
    return np.array(local_nodes, dtype=int)

def extract_basin_parameters_halo(basin_id, catchment_mask, world_parameter_arrays, halo=1, mask_inactive=False):
    """Extract parameter data for a specific basin"""
    #basin_1: 1,2,3,4
    # catchment_mask: 1,2,3,4 mask
    #     [[1. 1. 1. ... 3. 3. 3.]
    #  [1. 1. 1. ... 3. 3. 3.]
    #  [1. 1. 1. ... 3. 3. 3.]
    #  ...
    #  [2. 2. 2. ... 4. 4. 4.]
    #  [2. 2. 2. ... 4. 4. 4.]
    #  [2. 2. 2. ... 4. 4. 4.]]
    # print("Inside extract basin parameters halo: ", basin_id)
    # print("catchment_mask.shape: ", catchment_mask.shape)
    
    basin_region_mask, row_min, row_max, col_min, col_max = _get_basin_region(
        basin_id, catchment_mask)
    # np.savetxt("/shared/home1/c.c23086054/CUWALID/cuwalid/dryp/basin_region_mask_"+str(basin_id)+".csv", basin_region_mask, fmt="%s", delimiter=",")

    # Expand bounding box with halo, without going out of global matrix
    row_min_h = max(0, row_min - halo)
    row_max_h = min(catchment_mask.shape[0]-1, row_max + halo)
    col_min_h = max(0, col_min - halo)
    col_max_h = min(catchment_mask.shape[1]-1, col_max + halo)
    # print(str(row_min_h)+' '+str(row_max_h)+ ' '+str(col_min_h)+ ' '+str(col_max_h))
    nrows = row_max_h - row_min_h + 1
    ncols = col_max_h - col_min_h + 1
    # print("basin_forcing_halo nrows: ", nrows)
    # print("basin_forcing_halo ncols: ", ncols)
    
    # np.savetxt("/shared/home1/c.c23086054/CUWALID/cuwalid/dryp/basin_region_mask_"+str(basin_id)+".csv", basin_region_mask, fmt="%s", delimiter=",")
 
    # Extended mask: all cells in bounding box, regardless of basin
    extended_mask = np.ones((nrows, ncols), dtype=bool)
    # np.savetxt("/shared/home1/c.c23086054/CUWALID/cuwalid/dryp/extended_region_mask_"+str(basin_id)+".csv", extended_mask, fmt="%s", delimiter=",")


    bounds = np.array([[row_min, row_max, col_min, col_max, row_min_h, row_max_h, col_min_h, col_max_h, catchment_mask.shape[0], catchment_mask.shape[1]]])
 
    # np.savetxt(
    #     f"/shared/home1/c.c23086054/CUWALID/cuwalid/dryp/bounds_param_{basin_id}.csv",
    #     bounds,
    #     fmt="%d",
    #     delimiter=",",
    #     header="row_min,row_max,col_min,col_max,row_min_h,row_max_h,col_min_h,col_max_h,catchment_mask.shape[0],catchment_mask.shape[1]",
    #     comments=""
    # )


    parameter_data = {}
    for key, array in world_parameter_arrays.items():
        if isinstance(array, np.ndarray):
            # basin_array = _extract_basin_array(
            #     array, catchment_mask, row_min_h, row_max_h, col_min_h, col_max_h)
            basin_array = _extract_basin_array(array, catchment_mask, 
                            row_min_h, row_max_h, col_min_h, col_max_h)
            if mask_inactive:
                # basin_array[~basin_region_mask] = 0
                basin_array[~extended_mask] = 0
            parameter_data[key] = basin_array.flatten()
        else:
            parameter_data[key] = array

    return parameter_data

def extract_basin_data_with_halo2(basin_id, domains, grid_metadata, rank, halo=1, grid=True):
    """
    Extract subdomain data including halo (ghost cells) for MPI exchange.
    Halo includes neighboring cells even if they are outside the basin.
    """
 
    # Get the bounding box of the basin
    basin_mask, row_min, row_max, col_min, col_max = _get_basin_region(basin_id, domains)
    # print("basin_mask: ",basin_mask)
    # np.savetxt("/shared/home1/c.c23086054/CUWALID/cuwalid/dryp/basin_mask_"+str(rank)+".csv", basin_mask, fmt="%s", delimiter=",")
 
 
 
    # Expand bounding box with halo, without going out of global matrix
    row_min_h = max(0, row_min - halo)
    row_max_h = min(domains.shape[0]-1, row_max + halo)
    col_min_h = max(0, col_min - halo)
    col_max_h = min(domains.shape[1]-1, col_max + halo)
 
    # Save the 4 values as one row
    bounds = np.array([[row_min, row_max, col_min, col_max, row_min_h, row_max_h, col_min_h, col_max_h,
                        grid_metadata['xllcorner'], grid_metadata['yllcorner']]])
 
    # np.savetxt(
    #     f"/shared/home1/c.c23086054/CUWALID/cuwalid/dryp/bounds_{rank}.csv",
    #     bounds,
    #     fmt="%d",
    #     delimiter=",",
    #     header="row_min,row_max,col_min,col_max,row_min_h,row_max_h,col_min_h,col_max_h,xllcorner,yllcorner",
    #     comments=""
    # )
 
    nrows = row_max_h - row_min_h + 1
    ncols = col_max_h - col_min_h + 1
 
    # Extended mask: all cells in bounding box, regardless of basin
    extended_mask = np.ones((nrows, ncols), dtype=bool)

    # Core mask: only the real basin cells (True) vs halo/ghost cells
    # pulled in from neighboring regions (False). This MUST be the
    # actual basin-shaped mask, not the all-True extended_mask - with
    # halo=0 the two happen to coincide (since the box exactly equals
    # the basin's own extent), which is why this went unnoticed, but
    # with halo>0 (required for real inter-region connectivity) using
    # extended_mask here would treat neighboring regions' ghost cells
    # as this region's own core cells.
    core_mask = np.zeros_like(extended_mask, dtype=bool)
    core_mask[
        (row_min - row_min_h):(row_max - row_min_h + 1),
        (col_min - col_min_h):(col_max - col_min_h + 1)
    ] = basin_mask
    binary_init_core_mask = core_mask
    # print('core_mask: ',core_mask)
 
    # Grid (optional)
    if grid:
        grid = create_grid_from_extent(
            ncols, nrows,
            grid_metadata['xllcorner'] + col_min_h * grid_metadata['cellsize'],
            grid_metadata['yllcorner'] + row_min_h * grid_metadata['cellsize'],
            grid_metadata['cellsize'],
            active_domain=extended_mask.flatten(),
        )
    else:
        grid = None
 
    # Global node indices
    global_nodes = np.arange(domains.size, dtype=int).reshape(domains.shape)[
        row_min_h:row_max_h+1, col_min_h:col_max_h+1
    ].flatten()
 
    return {
        'basin_id': basin_id,
        'grid': grid,
        'grid_size': nrows * ncols,
        'mask': extended_mask,  # now includes all halo cells
        'core_mask': core_mask, # only subdomain real cells
        'binary_init_core_mask': binary_init_core_mask,
        'bbox': (row_min_h, row_max_h, col_min_h, col_max_h),
        'shape': (nrows, ncols),
        'global_nodes': global_nodes,
    }

# def extract_basin_data_with_halo2(basin_id, domains, grid_metadata, rank, halo=1, grid=True):
#     """
#     Extract subdomain data including halo (ghost cells) for MPI exchange.
#     Halo includes neighboring cells even if they are outside the basin.
#     """

#     # Get the bounding box of the basin
#     basin_mask, row_min, row_max, col_min, col_max = _get_basin_region(basin_id, domains)
#     # print("basin_mask: ",basin_mask)
#     np.savetxt("basin_mask.csv", basin_mask, fmt="%s", delimiter=",")


#     # Expand bounding box with halo, without going out of global matrix
#     row_min_h = max(0, row_min - halo)
#     row_max_h = min(domains.shape[0]-1, row_max + halo)
#     col_min_h = max(0, col_min - halo)
#     col_max_h = min(domains.shape[1]-1, col_max + halo)

#     nrows = row_max_h - row_min_h + 1
#     ncols = col_max_h - col_min_h + 1

#     # Extended mask: all cells in bounding box, regardless of basin 
#     extended_mask = np.ones((nrows, ncols), dtype=bool) 

#     # Core mask: only the real basin cells
#     core_mask = np.zeros_like(extended_mask, dtype=bool) 
#     core_mask[
#         (row_min - row_min_h):(row_max - row_min_h + 1),
#         (col_min - col_min_h):(col_max - col_min_h + 1)
#     ] = basin_mask
#     print('core_mask: ',core_mask)
#     np.savetxt("/shared/home1/c.c23086054/CUWALID/cuwalid/dryp/core_mask_"+str(rank)+".csv", core_mask, fmt="%s", delimiter=",")

#     # Grid (optional)
#     if grid:
#         grid = create_grid_from_extent(
#             ncols, nrows,
#             grid_metadata['xllcorner'] + col_min_h * grid_metadata['cellsize'],
#             grid_metadata['yllcorner'] + row_min_h * grid_metadata['cellsize'],
#             grid_metadata['cellsize'],
#             active_domain=extended_mask.flatten(),
#         )
#     else:
#         grid = None

#     # Global node indices
#     global_nodes = np.arange(domains.size, dtype=int).reshape(domains.shape)[
#         row_min_h:row_max_h+1, col_min_h:col_max_h+1
#     ].flatten()

#     return {
#         'basin_id': basin_id,
#         'grid': grid,
#         'grid_size': nrows * ncols,
#         'mask': extended_mask,  # now includes all halo cells
#         'core_mask': core_mask, # only subdomain real cells
#         'bbox': (row_min_h, row_max_h, col_min_h, col_max_h),
#         'shape': (nrows, ncols),
#         'global_nodes': global_nodes,
#     }

def extract_basin_data_with_halo(basin_id, domains, grid_metadata, halo=1, grid=True):
    """
    Extrae los datos de un subdominio incluyendo halo (celdas fantasma).
    """

    # obtener bounding box del subdominio
    basin_mask, row_min, row_max, col_min, col_max = _get_basin_region(basin_id, domains)

    # expandir con halo, sin salirse de la matriz global
    row_min_h = max(0, row_min - halo)
    row_max_h = min(domains.shape[0]-1, row_max + halo)
    col_min_h = max(0, col_min - halo)
    col_max_h = min(domains.shape[1]-1, col_max + halo)

    nrows = row_max_h - row_min_h + 1
    ncols = col_max_h - col_min_h + 1

    # máscara extendida: incluye halo
    extended_mask = domains[row_min_h:row_max_h+1, col_min_h:col_max_h+1] == basin_id

    # máscara core: solo el subdominio real
    core_mask = np.zeros_like(extended_mask, dtype=bool)
    core_mask[
        (row_min - row_min_h):(row_max - row_min_h + 1),
        (col_min - col_min_h):(col_max - col_min_h + 1)
    ] = basin_mask

    # grid extendido
    if grid:
        grid = create_grid_from_extent(
            ncols, nrows,
            grid_metadata['xllcorner'] + col_min_h * grid_metadata['cellsize'],
            grid_metadata['yllcorner'] + row_min_h * grid_metadata['cellsize'],
            grid_metadata['cellsize'],
            active_domain=extended_mask.flatten(),
        )
    else:
        grid = None

    global_nodes = np.arange(domains.size, dtype=int).reshape(domains.shape)[
        row_min_h:row_max_h+1, col_min_h:col_max_h+1
    ].flatten()

    return {
        'basin_id': basin_id,
        'grid': grid,
        'grid_size': nrows * ncols,
        'mask': extended_mask,  # incluye halo
        'core_mask': core_mask, # solo subdominio real
        'bbox': (row_min_h, row_max_h, col_min_h, col_max_h),
        'shape': (nrows, ncols),
        'global_nodes': global_nodes,
    }


def extract_complete_lake_data(basin_input, ids_lks, size_lks, ids_max_depth_lks):
    """Return lake metadata for lakes fully contained within a basin."""
    if ids_lks is None or size_lks is None or ids_max_depth_lks is None:
        return None, None, None, False

    lookup = _get_global_to_local_lookup(basin_input)
    local_ids_lks = []
    local_size_lks = []
    local_ids_max_depth_lks = []
    split_lakes_detected = False
    offset = 0

    for lake_size, max_depth_id in zip(size_lks, ids_max_depth_lks):
        lake_nodes = ids_lks[offset:offset + lake_size]
        offset += lake_size
        local_nodes = [lookup[int(node)] for node in lake_nodes if int(node) in lookup]

        if not local_nodes:
            continue

        if len(local_nodes) != lake_size or int(max_depth_id) not in lookup:
            split_lakes_detected = True
            continue

        local_ids_lks.extend(local_nodes)
        local_size_lks.append(lake_size)
        local_ids_max_depth_lks.append(lookup[int(max_depth_id)])

    if len(local_ids_lks) == 0:
        return None, None, None, split_lakes_detected

    return (
        np.array(local_ids_lks, dtype=int),
        np.array(local_size_lks, dtype=int),
        np.array(local_ids_max_depth_lks, dtype=int),
        split_lakes_detected,
    )


def build_basin_connectivity(connectivity_spec, grid_size):
    """
    Parse a basin-to-basin surface-water connectivity table.

    Each entry describes one connection: the outlet node of an upstream
    basin whose discharge should be added, at the following time step, as
    an inflow at the inlet node of a downstream basin. This is the piece
    that makes basins that are NOT truly endorheic (i.e. they drain into
    another, separately-simulated basin) actually receive their upstream
    water, since each basin's runoff_routing component otherwise only
    ever sees its own local runoff.

    Parameters
    ----------
    connectivity_spec : list of dict, or None
        Each dict needs the keys 'outlet_basin', 'outlet_node',
        'inlet_basin', 'inlet_node'. Node ids are GLOBAL (flattened,
        full-domain) node indices - the same indexing used everywhere
        else in this module (topo.surface, ro.discharge, domains_ro,
        etc). This is exactly the information the user needs to supply:
        for every basin that is not truly endorheic, identify its
        outlet cell (where flow leaves the basin, usually the lowest
        point on its boundary) and the corresponding inlet cell in the
        receiving basin (where that flow re-enters, usually the
        matching cell just downstream). None or [] means no basin is
        connected to any other (all endorheic) - the previous, implicit
        behaviour.
    grid_size : int
        Full domain grid size, used only for bounds-checking.

    Returns
    -------
    connections : list of dict
        Validated connections with plain python int node/basin ids.
    """
    connections = []
    if not connectivity_spec:
        return connections

    for entry in connectivity_spec:
        try:
            outlet_basin = int(entry['outlet_basin'])
            outlet_node = int(entry['outlet_node'])
            inlet_basin = int(entry['inlet_basin'])
            inlet_node = int(entry['inlet_node'])
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                f"Invalid basin connectivity entry: {entry}. Each entry "
                "must provide integer 'outlet_basin', 'outlet_node', "
                "'inlet_basin', 'inlet_node' (global node ids)."
            )
        if not (0 <= outlet_node < grid_size):
            raise ValueError(
                f"outlet_node {outlet_node} is out of range for a grid "
                f"of size {grid_size} (entry: {entry})")
        if not (0 <= inlet_node < grid_size):
            raise ValueError(
                f"inlet_node {inlet_node} is out of range for a grid "
                f"of size {grid_size} (entry: {entry})")
        connections.append({
            'outlet_basin': outlet_basin,
            'outlet_node': outlet_node,
            'inlet_basin': inlet_basin,
            'inlet_node': inlet_node,
        })
    return connections


def build_basin_execution_levels(basin_ids, basin_connections):
    """
    Compute a topological execution order for basins from their
    surface-water connectivity, so every basin's outlet discharge is
    available BEFORE its downstream basin is run - in the same time
    step, with no lag.

    Parameters
    ----------
    basin_ids : iterable of int
        All basin ids in the domain (across all ranks).
    basin_connections : list of dict
        As returned by build_basin_connectivity: each entry has
        'outlet_basin' and 'inlet_basin' (the inlet basin depends on
        the outlet basin having already been run this step).

    Returns
    -------
    levels : list of list of int
        levels[0] are basins with no upstream dependency (endorheic
        basins, or the head of a connected chain) - these can be run
        first, in any order / in parallel across ranks. levels[1] are
        basins whose only upstream dependencies are in levels[0], and
        so on. Every basin in `basin_ids` appears in exactly one level.
        Basins within the same level have no dependency on each other
        and can be run in parallel; levels themselves must be
        processed in order, with the outlet discharge of each level's
        basins made available to later levels before they run (see the
        main loop).

    Notes
    -----
    If the connectivity table contains a cycle (basins draining into
    each other in a loop - a configuration error), this breaks the
    cycle deterministically (by basin id) rather than looping forever,
    since a long-running continental-scale job hanging silently would
    be far worse than a warning.
    """
    basin_ids = list(basin_ids)
    remaining = set(basin_ids)
    downstream = {b: set() for b in basin_ids}
    indegree = {b: 0 for b in basin_ids}

    for connection in basin_connections:
        u = connection['outlet_basin']
        v = connection['inlet_basin']
        if u not in downstream or v not in indegree:
            # connection references a basin id not present in this
            # decomposition (e.g. sea / not modelled) - ignore
            # defensively rather than fail the whole setup.
            continue
        if v not in downstream[u]:
            downstream[u].add(v)
            indegree[v] += 1

    levels = []
    while remaining:
        current_level = sorted(b for b in remaining if indegree[b] == 0)
        if not current_level:
            # cycle detected - break it deterministically and move on;
            # the caller should be warned separately if this happens.
            current_level = [min(remaining)]
        for b in current_level:
            remaining.discard(b)
            for downstream_basin in downstream.get(b, ()):
                if downstream_basin in indegree:
                    indegree[downstream_basin] -= 1
        levels.append(current_level)
    return levels


def initialize_basin_component(basin_input, basin_model_parameters):
    """Start the runoff routing component (`ro`) for one basin."""
    local_flow_direction = None
    if basin_model_parameters.get('flowdird8') is not None:
        grid_size = basin_input['grid_size']
        basin_mask = basin_input['mask'].flatten()
        # flow_direction is already indexed locally (one entry per cell
        # in this basin's bounding box), but its VALUES are GLOBAL
        # receiver node ids (since topo.FlowDir stores global ids for
        # the whole domain and extracting a spatial subset doesn't
        # change the values, only which cells are included).
        flow_direction = np.asarray(basin_model_parameters['flowdird8'], dtype=int).ravel()
        global_nodes = np.asarray(basin_input['global_nodes'], dtype=int)

        # Build the global-id -> local-id lookup as a vectorized scatter
        # instead of a Python dict + per-cell loop. This turns what used
        # to be an O(n) pure-Python loop (with a dict lookup per cell -
        # a severe bottleneck for continental-scale basins with millions
        # of cells) into a couple of O(n) numpy operations.
        global_size = int(global_nodes.max()) + 1 if global_nodes.size > 0 else 0
        global_to_local_arr = np.full(global_size, -1, dtype=np.int64)
        global_to_local_arr[global_nodes] = np.arange(global_nodes.size)

        # Gather: for every local cell, look up the local id of its
        # (global-indexed) receiver. Values outside this basin's
        # bounding box (or invalid) come back as -1.
        valid_receiver = (flow_direction >= 0) & (flow_direction < global_size)
        receiver_local_id = np.full(grid_size, -1, dtype=np.int64)
        receiver_local_id[valid_receiver] = global_to_local_arr[flow_direction[valid_receiver]]

        local_ids = np.arange(grid_size, dtype=np.int64)
        # Fall back to routing to itself (a local sink) wherever the
        # receiver falls outside this basin's bounding box, or lands on
        # a halo/inactive cell that isn't part of the basin mask.
        not_found = receiver_local_id < 0
        receiver_local_id[not_found] = local_ids[not_found]
        clipped = np.clip(receiver_local_id, 0, grid_size - 1)
        outside_mask = ~basin_mask[clipped]
        receiver_local_id[outside_mask] = local_ids[outside_mask]

        local_flow_direction = local_ids.copy()
        local_flow_direction[basin_mask] = receiver_local_id[basin_mask]

    return runoff_routing(
        basin_input['grid'],
        basin_input['grid_size'],
        basin_model_parameters['surface'],
        local_flow_direction,
        basin_model_parameters['Ksat'],
        basin_model_parameters['decay'],
        basin_model_parameters['riv_width'],
        basin_model_parameters['riv_length'],
        parallel=False
    )

def initialize_gwflow_component(aquifer_input, aquifer_model_parameters):
    """Start the groundwater flow component (`gw`) for one basin."""

    return gwflow_EFD(
        aquifer_input['grid'],
        aquifer_model_parameters['Ksat'],
        aquifer_model_parameters['area_river'],
        aquifer_model_parameters['bc_head'],
        method=0   #, region_domain = aquifer_input
    )


def initiallize_gwflow_component(aquifer_input, aquifer_model_parameters):
    """Backward-compatible alias for the groundwater initializer."""
    return initialize_gwflow_component(aquifer_input, aquifer_model_parameters)
