import time
import numpy as np


def original_river_flux_update(head, riv_elevation, stage, conductivity, riv_area, riv_sy, riv_kaq):
    hriv = np.minimum(head, riv_elevation + stage)

    head_diff = head - hriv
    head_diff[head_diff < 0] = 0

    aux = np.log(head_diff) - conductivity / (riv_area * riv_sy)
    head_diff = head_diff - np.where(aux > 0, np.exp(aux), 0)

    return -riv_kaq * (head_diff * riv_area * riv_sy)


def optimized_river_flux_update(head, riv_elevation, stage, conductivity, riv_area, riv_sy, riv_kaq):
    riv_storage = riv_area * riv_sy

    head_diff = head - (riv_elevation + stage)
    np.maximum(head_diff, 0.0, out=head_diff)

    with np.errstate(divide="ignore", invalid="ignore"):
        aux = np.log(head_diff) - conductivity / riv_storage
    head_diff -= np.where(aux > 0.0, np.exp(aux), 0.0)

    return -riv_kaq * (head_diff * riv_storage)


def run_benchmark(n_riv_nodes=200_000, n_iter=200, seed=42):
    rng = np.random.default_rng(seed)

    head = rng.uniform(100.0, 300.0, size=n_riv_nodes)
    riv_elevation = rng.uniform(90.0, 250.0, size=n_riv_nodes)
    stage = rng.uniform(0.0, 4.0, size=n_riv_nodes)
    conductivity = rng.uniform(0.01, 0.5, size=n_riv_nodes)
    riv_area = rng.uniform(100.0, 900.0, size=n_riv_nodes)
    riv_sy = rng.uniform(0.05, 0.25, size=n_riv_nodes)
    riv_kaq = rng.uniform(1e-4, 2e-3, size=n_riv_nodes)

    # Warm-up
    _ = original_river_flux_update(
        head.copy(), riv_elevation, stage, conductivity, riv_area, riv_sy, riv_kaq
    )
    _ = optimized_river_flux_update(
        head.copy(), riv_elevation, stage, conductivity, riv_area, riv_sy, riv_kaq
    )

    t0 = time.perf_counter()
    for _ in range(n_iter):
        out_old = original_river_flux_update(
            head.copy(), riv_elevation, stage, conductivity, riv_area, riv_sy, riv_kaq
        )
    old_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    for _ in range(n_iter):
        out_new = optimized_river_flux_update(
            head.copy(), riv_elevation, stage, conductivity, riv_area, riv_sy, riv_kaq
        )
    new_time = time.perf_counter() - t1

    max_abs_diff = np.max(np.abs(out_old - out_new))
    speedup = old_time / new_time if new_time > 0 else np.inf

    print(f"n_riv_nodes: {n_riv_nodes:,}")
    print(f"iterations: {n_iter}")
    print(f"original_time_s: {old_time:.6f}")
    print(f"optimized_time_s: {new_time:.6f}")
    print(f"speedup_x: {speedup:.3f}")
    print(f"max_abs_diff: {max_abs_diff:.6e}")


if __name__ == "__main__":
    run_benchmark()
