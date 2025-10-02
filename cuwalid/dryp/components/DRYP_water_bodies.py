# -*- coding: utf-8 -*-
"""
Efficient multi-lake model for gridded domains.
- Supports multiple lakes (cells assigned a lake_id, -1 = no lake).
- Optimized per-lake precomputation: unique event elevations and segment areas.
- Batch operations supported to add/remove volume per lake.

Usage:
  - Instantiate with arrays for bottoms, max_depths, areas and lake_ids (ints).
  - Call add_volume_to_lakes(lake_ids, dV_array) or add_volume_to_lake(lake_id, dV).
  - Query per-cell depths with get_cell_water_depths().

Notes on performance for large domains:
  - Precomputation groups cells by lake and computes per-lake events and segment areas once.
  - Operations that change only lake volumes/elevations avoid touching other lakes' cells.
  - For extreme-scale problems, consider enabling numba on the hotspot loops or parallelizing lakes.

Copyright: snippets for research use.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class _LakeBucket:
    """Internal container: precomputed data for a single lake."""
    indices: np.ndarray                # indices of cells belonging to this lake
    bottoms: np.ndarray                # bottoms for these cells
    tops: np.ndarray                   # tops = bottoms + max_depths
    areas: np.ndarray                  # areas for these cells
    events: np.ndarray = field(default=None)      # sorted unique event elevations
    seg_areas: np.ndarray = field(default=None)   # area active in each segment
    seg_caps: np.ndarray = field(default=None)    # capacity per segment
    total_area: float = 0.0
    min_bottom: float = 0.0
    max_top: float = 0.0
    H: float = None                    # current lake surface elevation
    volume: float = 0.0                # current lake volume

    def precompute(self):
        # Compute supporting arrays for fast inversion
        self.tops = self.tops  # already passed in
        events = np.unique(np.concatenate([self.bottoms, self.tops]))
        self.events = events
        nseg = len(events) - 1
        seg_areas = np.zeros(nseg, dtype=float)
        seg_caps = np.zeros(nseg, dtype=float)
        # For each segment compute active area (vectorized over local arrays)
        # This loop runs per lake; for very large lakes this could be vectorized differently
        for i in range(nseg):
            low = events[i]
            high = events[i+1]
            mask = (self.tops > low) & (self.bottoms < high)
            A = float(self.areas[mask].sum())
            seg_areas[i] = A
            seg_caps[i] = A * (high - low)
        self.seg_areas = seg_areas
        self.seg_caps = seg_caps
        self.total_area = float(self.areas.sum())
        self.min_bottom = float(self.bottoms.min()) if self.bottoms.size else 0.0
        self.max_top = float(self.tops.max()) if self.tops.size else 0.0
        # Initialize H at min_bottom if not set, and volume accordingly
        if self.H is None:
            self.H = self.min_bottom
            self.volume = 0.0
        else:
            # ensure volume consistent
            self.volume = float(self.compute_volume_from_elevation(self.H))

    def compute_volume_from_elevation(self, H: float) -> float:
        # Local vectorized computation
        depths = np.clip(H - self.bottoms, 0.0, self.tops - self.bottoms)
        return float(np.sum(depths * self.areas))

    def elevation_from_volume(self, target_volume: float) -> float:
        # Piecewise analytic inversion using precomputed segments
        if target_volume <= 0:
            return self.min_bottom + target_volume / max(self.total_area, 1e-30)
        events = self.events
        cum = 0.0
        for i in range(len(self.seg_caps)):
            cap = self.seg_caps[i]
            if target_volume <= cum + cap + 1e-15:
                remaining = target_volume - cum
                area = self.seg_areas[i]
                if area <= 0:
                    return float(events[i])
                return float(events[i] + remaining / area)
            cum += cap
        # above all tops
        remaining = target_volume - cum
        return float(self.max_top + remaining / max(self.total_area, 1e-30))

class MultiLakeModel:
    """High-performance multi-lake model for large gridded domains.

    Parameters
    ----------
    bottoms : 1D ndarray (Ncells,)   bottom elevations (m)
    max_depths : 1D ndarray (Ncells,) maximum depth (m)
    areas : 1D ndarray (Ncells,)     horizontal area per cell (m2)
    lake_ids : 1D integer ndarray (Ncells,) lake identifier for each cell; use -1 for non-lake
    """

    def __init__(self, bottoms: np.ndarray, max_depths: np.ndarray, areas: np.ndarray, lake_ids: np.ndarray):
        bottoms = np.asarray(bottoms, dtype=float)
        max_depths = np.asarray(max_depths, dtype=float)
        areas = np.asarray(areas, dtype=float)
        lake_ids = np.asarray(lake_ids, dtype=int)
        if not (bottoms.shape == max_depths.shape == areas.shape == lake_ids.shape):
            raise ValueError("bottoms, max_depths, areas and lake_ids must have same shape")
        self.N = bottoms.size
        self.bottoms = bottoms
        self.max_depths = max_depths
        self.tops = bottoms + max_depths
        self.areas = areas
        self.lake_ids = lake_ids

        # Build buckets per lake id
        unique_ids = np.unique(lake_ids)
        unique_ids = unique_ids[unique_ids >= 0]  # drop -1 (no-lake)
        self.lake_ids_list = np.asarray(unique_ids, dtype=int)
        self.lakes: Dict[int, _LakeBucket] = {}
        # Precompute buckets: group indices by lake id
        for lid in self.lake_ids_list:
            idx = np.nonzero(lake_ids == lid)[0]
            b = bottoms[idx]
            t = self.tops[idx]
            a = areas[idx]
            bucket = _LakeBucket(indices=idx, bottoms=b, tops=t, areas=a)
            bucket.precompute()
            self.lakes[int(lid)] = bucket
        # For performance: map lake index array to bucket references for vectorized queries
        # Dict lookup is cheap compared to per-cell operations but we also keep a cell->lake map
        self.cell_to_lake = lake_ids

    def compute_volume_of_lake(self, lake_id: int) -> float:
        bucket = self.lakes[lake_id]
        return float(bucket.volume)

    def compute_volume_from_elevation(self, lake_id: int, H: float) -> float:
        bucket = self.lakes[lake_id]
        return bucket.compute_volume_from_elevation(H)

    def elevation_from_volume(self, lake_id: int, target_volume: float) -> float:
        bucket = self.lakes[lake_id]
        return bucket.elevation_from_volume(target_volume)

    def add_volume_to_lake(self, lake_id: int, dV: float) -> float:
        """Add (or remove) volume for a single lake. Returns new H."""
        bucket = self.lakes[lake_id]
        new_vol = bucket.volume + dV
        new_H = bucket.elevation_from_volume(new_vol)
        bucket.volume = float(new_vol)
        bucket.H = float(new_H)
        return float(new_H)

    def add_volume_to_lakes(self, lake_ids: np.ndarray, dV_array: np.ndarray) -> Dict[int, float]:
        """Batch add volumes. lake_ids and dV_array are same-length arrays. Returns dict lake_id->new H.
        This groups operations by lake_id so each lake performs one inversion per call.
        """
        lake_ids = np.asarray(lake_ids, dtype=int)
        dV_array = np.asarray(dV_array, dtype=float)
        if lake_ids.shape != dV_array.shape:
            raise ValueError("lake_ids and dV_array must have same shape")
        # aggregate dV per lake
        unique, inv_idx = np.unique(lake_ids, return_inverse=True)
        sums = np.zeros_like(unique, dtype=float)
        for i, dv in enumerate(dV_array):
            sums[inv_idx[i]] += dv
        result = {}
        for lid, dvsum in zip(unique, sums):
            if lid < 0:
                continue
            result[int(lid)] = self.add_volume_to_lake(int(lid), float(dvsum))
        return result

    def get_cell_water_depths(self) -> np.ndarray:
        """Return per-cell water depths from per-lake H values. Vectorized by bucket.
        For cells without a lake (lake_id < 0) depth = 0.
        """
        depths = np.zeros(self.N, dtype=float)
        for lid, bucket in self.lakes.items():
            H = bucket.H
            # compute depths for bucket cells
            local_depths = np.clip(H - bucket.bottoms, 0.0, bucket.tops - bucket.bottoms)
            depths[bucket.indices] = local_depths
        return depths

    def get_lake_state(self, lake_id: int) -> Dict:
        b = self.lakes[lake_id]
        return {"H": float(b.H), "volume": float(b.volume), "total_area": float(b.total_area)}
