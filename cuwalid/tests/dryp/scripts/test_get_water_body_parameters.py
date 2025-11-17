import numpy as np
import numpy.testing as npt

from cuwalid.dryp.components.DRYP_io import get_water_body_parameters

def test_get_water_body_parameters_simple():
    # Construct a small depth grid with three separate water bodies:
    # cluster 1: positions (0,1),(0,2),(1,1) -> flat indices [1,2,4] (size 3)
    # cluster 2: position (2,0) -> flat index 6 (size 1)
    # cluster 3: position (2,2) -> flat index 8 (size 1)
    depth = np.array([
        [0, 1, 4],
        [0, 2, 0],
        [3, 0, 1]
    ])

    name_lks, ids_lks, size_lks, ids_max_depth_lks, depths = get_water_body_parameters(depth)

    expected_ids = [1, 2, 4, 6, 8]
    expected_sizes = [3, 1, 1]
    expected_max_indices = [2, 6, 8]
    expected_depths = depth.flatten()[expected_ids]

    # Basic checks
    assert ids_lks == expected_ids
    assert size_lks == expected_sizes
    assert ids_max_depth_lks == expected_max_indices
    npt.assert_array_equal(depths, expected_depths)

    # name_lks should contain the zone labels for the returned ids and include 1..3
    unique_labels = np.unique(name_lks)
    npt.assert_array_equal(unique_labels, np.array([1, 2, 3]))