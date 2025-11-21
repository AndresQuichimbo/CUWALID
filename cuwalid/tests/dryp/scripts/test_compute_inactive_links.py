import numpy as np
import pytest

from cuwalid.dryp.components.DRYP_io import _generate_rectangular_grid_data, _compute_inactive_links

def test__compute_inactive_links_all_active():
    # 3x3 grid, all nodes active
    N_x, N_y = 3, 3
    Dx = np.ones(N_x * N_y, dtype=float)
    Dy = np.ones(N_x * N_y, dtype=float)
    grid = _generate_rectangular_grid_data(N_x, N_y, Dx, Dy)

    domain = np.ones(grid['N_cells'], dtype=int)  # all active
    inactive_links, active_mask = _compute_inactive_links(grid, domain)

    # all links should be active
    assert active_mask.dtype == bool
    assert np.all(active_mask)
    assert inactive_links.size == 0

def test__compute_inactive_links_partial_active():
    # 3x3 grid, only a subset of nodes active
    N_x, N_y = 3, 3
    Dx = np.ones(N_x * N_y, dtype=float)
    Dy = np.ones(N_x * N_y, dtype=float)
    grid = _generate_rectangular_grid_data(N_x, N_y, Dx, Dy)

    # define domain: activate top-left 2x2 block only (indices 0,1,3,4)
    domain = np.zeros(grid['N_cells'], dtype=int)
    active_indices = np.array([0, 1, 3, 4], dtype=int)
    domain[active_indices] = 1

    inactive_links, active_mask = _compute_inactive_links(grid, domain)

    I = grid['I'].astype(int)
    J = grid['J'].astype(int)
    expected_active = np.logical_and(domain[I] > 0, domain[J] > 0)

    # compare boolean masks
    assert np.array_equal(active_mask, expected_active)

    # inactive links are indices where expected_active is False
    expected_inactive = np.where(~expected_active)[0]
    assert np.array_equal(inactive_links, expected_inactive)