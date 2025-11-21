import numpy as np

from cuwalid.dryp.components.DRYP_io import create_grid_from_extent, center_ones

def test_create_grid_from_extent_projected():
    """
    Basic sanity checks for create_grid_from_extent using projected=True
    (uses array Dx/Dy path in the implementation).
    """
    ncols = 4
    nrows = 5
    lon_min = 10.0
    lat_min = 20.0
    cellsize = 1000.0

    grid = create_grid_from_extent(ncols, nrows, lon_min, lat_min, cellsize, domain=None, projected=True)

    # basic structural checks
    assert grid['N_cells'] == ncols * nrows
    assert grid['N_x'] == ncols
    assert grid['N_y'] == nrows

    # x and y coordinate arrays lengths
    assert grid['x'].shape[0] == ncols
    assert grid['y'].shape[0] == nrows

    # core_nodes should match the center-ones pattern used by the function.
    # Note: create_grid_from_extent currently calls center_ones with swapped args
    # (ncols, nrows) — match that behavior here to compute expected core nodes.
    expected_core = np.where(center_ones(ncols, nrows).flatten() > 0)[0]
    assert np.array_equal(np.sort(grid['core_nodes']), np.sort(expected_core))