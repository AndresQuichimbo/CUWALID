# python
import numpy as np
import pytest

from cuwalid.dryp.components.DRYP_io import zone_parameters
import rasterio

class DummyRaster:
    def __init__(self, arr):
        self._arr = arr
    def read(self, _):
        return self._arr

def test_zone_parameters_no_mask():
    zp = zone_parameters(None)
    assert zp.zone_mask is None
    assert zp.get_scale_factor_zones(np.array([1.0, 2.0])) is None
    assert zp.extract_zone_info() == (None, None)
    assert zp.get_zone_info_from_core_nodes(np.array([0, 1])) == (None, None)

def test_zone_parameters_with_mask_and_scale_and_core_nodes(monkeypatch):
    # prepare a 2x3 mask with two zones: shape (2,3)
    arr = np.array([
        [1, 2, 0],
        [1, 2, 0]
    ], dtype=int)

    # monkeypatch rasterio.open to return the dummy raster
    def fake_open(path):
        return DummyRaster(arr)
    
    # Make sure DRYP_io sees our fake open
    monkeypatch.setattr(rasterio, "open", fake_open)
    # Skip os.path.exists check
    monkeypatch.setattr("os.path.exists", lambda _: True)

    zp = zone_parameters("dummy_path.tif")

    # After __init__, zone_mask is np.flip(arr,0).astype(int).flatten()
    flipped = np.flip(arr, 0).astype(int).flatten()
    # expected flattened indices > 0
    expected_ids = list(np.where(flipped > 0)[0])
    # expected sizes per zone: zone1 has two cells, zone2 has two cells
    expected_sizes = [2, 2]

    # Test get_scale_factor_zones
    factors = np.array([10.0, 100.0])
    #print('zone_mask:', zp.zone_mask)
    param = zp.get_scale_factor_zones(factors)
    #assert param is not None
    # zone 1 cells should be multiplied by 10, zone 2 by 100, zeros remain 1
    for idx, val in enumerate(flipped):
        if val == 1:
            assert pytest.approx(param[idx]) == 10.0
        elif val == 2:
            assert pytest.approx(param[idx]) == 100.0
        else:
            assert pytest.approx(param[idx]) == 1.0

    # Test extract_zone_info (no core_nodes)
    ids_zone, size_zone = zp.extract_zone_info()
    assert isinstance(ids_zone, list) or isinstance(ids_zone, np.ndarray)
    # ids_zone should equal flattened indices > 0
    assert list(ids_zone) == expected_ids
    assert size_zone == expected_sizes

    # Test get_zone_info_from_core_nodes: choose core_nodes that include all active indices
    core_nodes = np.array(expected_ids, dtype=int)
    ids_core, sizes_core = zp.get_zone_info_from_core_nodes(core_nodes)
    # mask_core = zone_mask[core_nodes] will become [1,2,1,2] -> ids [0,1,2,3], sizes [2,2]
    assert list(ids_core) == [0,1,2,3]
    assert sizes_core == [2,2]

