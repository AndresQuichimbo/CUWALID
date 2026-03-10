from mpi4py import MPI
import numpy as np
import pandas as pd
import sys
#sys.path.append('/home/c1755103/gitremote/CUWALID')
from cuwalid.dryp.components.DRYP_io import create_grid_from_extent
#from cuwalid.dryp.components.DRYP_flow_accumf90 import runoff_routing
import time

# Part of this code has been developed using AI tools (ChatGPT)
# to assist with parallelization and data handling.
# We user is responsible for verifying the correctness and
# performance of the code, and for ensuring that it meets the
# needs of the project.

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_basin_ids(catchment_mask):
    """Extract unique basin IDs from catchment mask (excluding 0 = sea)"""
    unique_ids = np.unique(catchment_mask)
    basin_ids = unique_ids[unique_ids > 0]  # Exclude sea (0)
    return basin_ids.tolist()


def extract_basin_data(basin_id, catchment_mask, full_grid_data):
    """
    Extract data for a specific basin from the full grid.
    Returns a dictionary with basin-specific grid and data arrays.
    """
    # Create mask for this basin
    basin_mask = (catchment_mask == basin_id)
    
    # Get bounding box to reduce grid size
    rows, cols = np.where(basin_mask)
    row_min, row_max = rows.min(), rows.max()
    col_min, col_max = cols.min(), cols.max()
    
    # Extract basin region
    basin_region_mask = basin_mask[row_min:row_max+1, col_min:col_max+1]
    nrows_basin = row_max - row_min + 1
    ncols_basin = col_max - col_min + 1
    #print(f"Rank {rank}: Basin {basin_id} - bbox rows({row_min}:{row_max}), cols({col_min}:{col_max}), size ({nrows_basin}x{ncols_basin})")
    
    # Create grid for this basin
    grid_cellsize = full_grid_data['cellsize']
    grid = create_grid_from_extent(
        ncols_basin, nrows_basin,
        col_min * grid_cellsize, row_min * grid_cellsize,
        grid_cellsize, active_domain=basin_region_mask.flatten()
    )
    return {
        'basin_id': basin_id,
        'grid': grid,
        'grid_size': grid['N_cells'],
        'mask': basin_region_mask,
        'bbox': (row_min, row_max, col_min, col_max),
        'shape': (nrows_basin, ncols_basin)
    }

def extract_basin_forcing(basin_id, catchment_mask, world_forcing_arrays):
    """Extract forcing data for a specific basin"""
    row_min, row_max, col_min, col_max = get_basin_bbox(basin_id, catchment_mask)
    forcing_data = {}
    for key, array in world_forcing_arrays.items():
        # Handle both 2D and 1D arrays
        if array.ndim == 2:
            forcing_data[key] = array[row_min:row_max+1, col_min:col_max+1].flatten()
        elif array.ndim == 1:
            forcing_data[key] = array  # Keep 1D arrays as is
        else:
            raise ValueError(f"Unsupported array dimension for {key}: {array.ndim}D")
    return forcing_data

def extract_basin_parameters(basin_id, catchment_mask, world_parameter_arrays):
    """Extract parameter data for a specific basin"""
    row_min, row_max, col_min, col_max = get_basin_bbox(basin_id, catchment_mask)
    parameter_data = {}
    for key, array in world_parameter_arrays.items():
        # Handle both 2D and 1D arrays, and skip scalar values like 'cellsize'
        if isinstance(array, np.ndarray):
            if array.ndim == 2:
                parameter_data[key] = array[row_min:row_max+1, col_min:col_max+1].flatten()
            elif array.ndim == 1:
                parameter_data[key] = array  # Keep 1D arrays as is
            else:
                raise ValueError(f"Unsupported array dimension for {key}: {array.ndim}D")
        else:
            # Keep scalar values (like cellsize) as is
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


def get_basin_bbox(basin_id, catchment_mask):
    """Get bounding box for a specific basin"""
    basin_mask = (catchment_mask == basin_id)
    rows, cols = np.where(basin_mask)
    row_min, row_max = rows.min(), rows.max()
    col_min, col_max = cols.min(), cols.max()
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




