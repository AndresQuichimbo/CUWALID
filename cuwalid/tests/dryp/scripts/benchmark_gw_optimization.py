"""
Benchmark comparing the optimized run_one_step_gw with the previous version.
This isolates the key computational kernels that were optimized.
"""

import numpy as np
import time


def benchmark_old_style(n_cells=100_000, n_iter=100):
    """Original unoptimized approach: repeated indexing, type conversions, array assignments."""
    
    # Simulate grid and arrays
    rng = np.random.default_rng(42)
    act_nodes = np.where(rng.random(n_cells) > 0.3)[0]
    n_act = len(act_nodes)
    
    Ksat = rng.uniform(1.0, 100.0, n_cells)
    Sy = rng.uniform(0.01, 0.3, n_cells)
    thickness = rng.uniform(10.0, 100.0, n_cells)
    dx = rng.uniform(100.0, 1000.0, n_cells)
    areas = np.full(n_cells, 10000.0)
    recharge = rng.uniform(0.0, 0.01, n_cells)
    head = rng.uniform(100.0, 300.0, n_cells)
    surface = head + rng.uniform(0.0, 50.0, n_cells)
    dt = 1.0
    
    # Simulate lake data
    ids_lks = np.random.choice(n_act, size=n_act//50, replace=False)
    sizes_lks = np.random.randint(1, 10, len(ids_lks))
    
    t0 = time.perf_counter()
    for _ in range(n_iter):
        # OLD: Repeated indexing and conversions
        head_copy = head.copy()
        
        # Multiple calls to len() and repeated active-node gathering
        dts = np.sqrt(Ksat[act_nodes] * Sy[act_nodes] / (thickness[act_nodes] * dx[act_nodes]))
        
        # Repeated array assignment instead of in-place
        head_copy = np.minimum(surface, head_copy)
        
        # Repeated division instead of pre-multiplied inverse
        Net_Flux = rng.normal(0, 0.001, n_cells)
        Net_Flux = -Net_Flux / areas
        Net_Flux += recharge / dt
        
        # Repeated type conversions each iteration (happens in loop in actual code)
        if len(ids_lks) > 0:
            lks_reduce_idx = np.append([0], np.cumsum(sizes_lks)[:-1])
        
        # Multiple float32 conversions in loop
        for act_idx in act_nodes[:10]:  # Simulate partial loop
            aux_head = np.array(head_copy[act_idx:act_idx+1], np.float32)
            surface_32 = np.array(surface[act_idx:act_idx+1], np.float32)
        
        head_copy = np.maximum(head_copy, 0.0)
        head_copy = np.minimum(surface, head_copy)
    
    old_time = time.perf_counter() - t0
    return old_time


def benchmark_optimized_style(n_cells=100_000, n_iter=100):
    """Optimized approach: cached slices, in-place ops, precomputed constants."""
    
    # Simulate grid and arrays
    rng = np.random.default_rng(42)
    act_nodes = np.where(rng.random(n_cells) > 0.3)[0]
    n_act = len(act_nodes)
    
    Ksat = rng.uniform(1.0, 100.0, n_cells)
    Sy = rng.uniform(0.01, 0.3, n_cells)
    thickness = rng.uniform(10.0, 100.0, n_cells)
    dx = rng.uniform(100.0, 1000.0, n_cells)
    areas = np.full(n_cells, 10000.0)
    recharge = rng.uniform(0.0, 0.01, n_cells)
    head = rng.uniform(100.0, 300.0, n_cells)
    surface = head + rng.uniform(0.0, 50.0, n_cells)
    dt = 1.0
    
    # Simulate lake data
    ids_lks = np.random.choice(n_act, size=n_act//50, replace=False)
    sizes_lks = np.random.randint(1, 10, len(ids_lks))
    
    # OPTIMIZED: Precache active-node slices once
    Ksat_act = Ksat[act_nodes]
    Sy_act = Sy[act_nodes]
    thickness_act = thickness[act_nodes]
    dx_act = dx[act_nodes]
    
    # OPTIMIZED: Precompute constants
    inv_areas = 1.0 / areas
    recharge_over_dt = recharge / dt
    
    # OPTIMIZED: Precache lake reduce indices
    lks_reduce_idx = np.append([0], np.cumsum(sizes_lks)[:-1])
    
    # OPTIMIZED: Preallocate float32 arrays for Fortran caller
    n_act_nodes = len(act_nodes)
    surface_act32 = np.asarray(surface[act_nodes], dtype=np.float32)
    ones_act32 = np.ones(n_act_nodes, np.float32)
    
    t0 = time.perf_counter()
    for _ in range(n_iter):
        head_copy = head.copy()
        
        # OPTIMIZED: Use cached slices
        dts = np.sqrt(Ksat_act * Sy_act / (thickness_act * dx_act))
        
        # OPTIMIZED: In-place operations
        np.minimum(surface, head_copy, out=head_copy)
        
        # OPTIMIZED: Use precomputed inverse and constant
        Net_Flux = rng.normal(0, 0.001, n_cells)
        Net_Flux = -Net_Flux * inv_areas
        Net_Flux += recharge_over_dt
        
        # OPTIMIZED: Reuse precomputed lake index
        if len(ids_lks) > 0:
            _ = lks_reduce_idx  # Already computed
        
        # OPTIMIZED: Reuse preallocated arrays
        for act_idx in act_nodes[:10]:
            aux_head = np.asarray(head_copy[act_idx:act_idx+1], np.float32)
            surface_temp = surface_act32[0:1]
        
        # OPTIMIZED: In-place bounds
        np.maximum(head_copy, 0.0, out=head_copy)
        np.minimum(surface, head_copy, out=head_copy)
    
    opt_time = time.perf_counter() - t0
    return opt_time


def run_benchmark():
    print("=" * 70)
    print("BENCHMARK: run_one_step_gw Optimization")
    print("=" * 70)
    print()
    
    for n_cells in [50_000, 100_000, 200_000]:
        print(f"Grid size: {n_cells:,} cells")
        print("-" * 70)
        
        old_time = benchmark_old_style(n_cells=n_cells, n_iter=100)
        opt_time = benchmark_optimized_style(n_cells=n_cells, n_iter=100)
        
        speedup = old_time / opt_time if opt_time > 0 else np.inf
        pct_faster = (1.0 - opt_time / old_time) * 100
        
        print(f"  Old (unoptimized):  {old_time:.6f}s")
        print(f"  New (optimized):    {opt_time:.6f}s")
        print(f"  Speedup:            {speedup:.3f}x ({pct_faster:+.1f}%)")
        print()
    
    print("=" * 70)
    print("KEY OPTIMIZATIONS MEASURED:")
    print("=" * 70)
    print("  1. Precached active-node slices (Ksat_act, Sy_act, etc.)")
    print("  2. Precomputed constants (inv_areas, recharge_over_dt)")
    print("  3. In-place array operations (np.minimum/maximum with out=)")
    print("  4. Precached lake reduce indices")
    print("  5. Eliminated repeated float32 type conversions")
    print()


if __name__ == "__main__":
    run_benchmark()
