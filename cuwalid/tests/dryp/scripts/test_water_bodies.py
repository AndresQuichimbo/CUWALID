import numpy as np
from cuwalid.dryp.components.DRYP_water_bodies import MultiLakeModel


# Example (small) usage
def test_water_bodies():
    # synthetic domain with 1e5 cells and ~300 lakes to illustrate performance scaling
    rng = np.random.default_rng(42)
    Ncells = 1000
    # random assignment of 30 lakes + some non-lake cells (-1)
    lake_ids = rng.integers(-1, 30, size=Ncells)
    bottoms = 100.0 + rng.random(Ncells) * 5.0
    max_depths = 0.2 + rng.random(Ncells) * 3.0
    areas = 200.0 + rng.random(Ncells) * 800.0

    model = MultiLakeModel(bottoms, max_depths, areas, lake_ids)
    # add 1000 m3 to a handful of lakes
    some_lakes = model.lake_ids_list[:10]
    dVs = np.full_like(some_lakes, 1000.0, dtype=float)
    res = model.add_volume_to_lakes(some_lakes, dVs)
    print("Updated H for sample lakes:")
    for lid in some_lakes[:5]:
        print(lid, model.get_lake_state(int(lid)))
    # get per-cell depths
    depths = model.get_cell_water_depths()
    print("Depths stats:", depths.mean(), depths.max(), depths.sum())

    #print(model.get_lake_wet_cells())
    #print(model.get_lakes_evaporation_volume(np.full(Ncells, 0.5)))  # 0.5 mm evaporation from all cells

if __name__ == "__main__":
    test_water_bodies()