import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import matplotlib.pyplot as plt

# Import the required components from the cuwalid library
from cuwalid.dryp.components.DRYP_infiltration import infiltration
from cuwalid.dryp.components.read_model_parameters import read_model_parameters_and_settings
from cuwalid.dryp.components.read_temporal_datasets import read_temporal_datasets_and_grid


def _run_region(func, mask, input_arrays, region_args):
    """
    Run the given function for a specific spatial region defined by the mask.

    Parameters:
    - func: The function to run on region data.
    - mask: Binary mask selecting region indices.
    - input_arrays: Dictionary of input data arrays.
    - region_args: List of argument names that require region-specific slicing.

    Returns:
    - Tuple of indices selected by mask and function result for those indices.
    """
    idx = np.where(mask == 1)[0]

    # Prepare inputs for this region: slice only those arrays specified in region_args
    local_args = {}
    for name, arr in input_arrays.items():
        if name in region_args:
            local_args[name] = None if arr is None else arr[idx]
        else:
            local_args[name] = arr  # global inputs unchanged

    result = func(**local_args)
    return idx, result


def parallel_masked_runner(func, region_masks, input_arrays, region_args, output_shape):
    """
    Execute `func` in parallel over spatial regions defined by binary masks.

    Splits data and runs each region in a separate process to speed up computation.
    Stitches outputs back into arrays aligned with the original input shape.

    Returns:
    - Aggregated outputs stitched together across regions.
    - Total parallel execution time.
    """
    results = []
    print(f"Parallel runner: Processing {len(region_masks)} regions...")
    start_time = time.perf_counter()

    # Prepare inputs sliced per region to reduce data sent to workers
    region_inputs = []
    for mask in region_masks:
        idx = np.where(mask == 1)[0]
        local_inputs = {}
        for name, arr in input_arrays.items():
            local_inputs[name] = None if (name in region_args and arr is None) else (arr[idx] if name in region_args else arr)
        region_inputs.append((idx, local_inputs))

    # Submit jobs to worker pool
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(func, **inputs) for _, inputs in region_inputs]
        for (idx, _), future in zip(region_inputs, futures):
            results.append((idx, future.result()))

    parallel_time = time.perf_counter() - start_time
    print(f"Parallel execution time: {parallel_time:.4f} seconds")

    # Stitch results back into full output arrays, averaging overlaps
    sample_output = results[0][1]
    is_dict = isinstance(sample_output, dict)

    if is_dict:
        stitched = {k: np.zeros(output_shape, dtype=np.float64) for k in sample_output.keys()}
        counts = {k: np.zeros(output_shape, dtype=np.int32) for k in sample_output.keys()}
        for idx, output in results:
            for k in output:
                stitched[k].ravel()[idx] += output[k]
                counts[k].ravel()[idx] += 1
        # Average overlapping values
        final_outputs = {
            k: np.divide(stitched[k], counts[k], out=np.zeros_like(stitched[k]), where=counts[k] > 0)
            for k in stitched
        }
        return final_outputs, parallel_time
    else:
        n_outputs = len(sample_output)
        sums = [np.zeros(output_shape, dtype=np.float64) for _ in range(n_outputs)]
        counts = [np.zeros(output_shape, dtype=np.int32) for _ in range(n_outputs)]

        for idx, output in results:
            for i, arr in enumerate(output):
                sums[i].ravel()[idx] += arr
                counts[i].ravel()[idx] += 1

        final_outputs = tuple(
            np.divide(sums[i], counts[i], out=np.zeros_like(sums[i]), where=counts[i] > 0)
            for i in range(n_outputs)
        )
        return final_outputs, parallel_time



def normal_full_runner(func, input_arrays):
    """
    Run the function once on the full input arrays (no region splitting).

    Returns:
    - Function outputs.
    - Execution time.
    """
    print("Full-array runner: Processing entire input at once...")
    start_time = time.perf_counter()
    result = func(**input_arrays)
    exec_time = time.perf_counter() - start_time
    print(f"Execution time: {exec_time:.4f} seconds")
    return result, exec_time


def generate_region_masks(shape, n_regions=4):
    """
    Create binary masks dividing 1D or 2D arrays into `n_regions` spatial partitions.

    Returns a list of masks where each mask corresponds to one region.

    Parameters:
    - shape: int for 1D or tuple for 2D array shape.
    - n_regions: number of regions to split into.
    """
    masks = []

    if isinstance(shape, int):
        # 1D case: split array into contiguous chunks
        size = shape
        chunk_sizes = [size // n_regions] * n_regions
        for i in range(size % n_regions):
            chunk_sizes[i] += 1  # distribute remainder evenly

        starts = np.cumsum([0] + chunk_sizes[:-1])
        for start, chunk_size in zip(starts, chunk_sizes):
            mask = np.zeros(size, dtype=np.uint8)
            mask[start:start + chunk_size] = 1
            masks.append(mask)

    elif isinstance(shape, (tuple, list)) and len(shape) == 2:
        # 2D case: split array into a grid (rows x cols) covering n_regions
        nrows, ncols = shape
        rows = int(np.sqrt(n_regions))
        cols = int(np.ceil(n_regions / rows))

        row_edges = np.linspace(0, nrows, rows + 1, dtype=int)
        col_edges = np.linspace(0, ncols, cols + 1, dtype=int)

        for i in range(rows):
            for j in range(cols):
                if len(masks) >= n_regions:
                    break
                mask = np.zeros((nrows, ncols), dtype=np.uint8)
                mask[row_edges[i]:row_edges[i+1], col_edges[j]:col_edges[j+1]] = 1
                masks.append(mask)
    else:
        raise ValueError("Shape must be int (1D) or tuple (rows, cols) for 2D.")

    return masks


if __name__ == '__main__':
    data_array_size = 70
    n_masks = 8
    filename_input = 'inputs/dryp_input.json'

    # Instantiate infiltration class
    inf = infiltration(1)

    # Load model parameters and datasets
    data_in, topo, soil, rsoil, aquifer, vegetation, water_bodies, water_bodies_management = read_model_parameters_and_settings(filename_input)
    PRE, ET0, SAVI, LAI, Kc, av, SAVImin, SAVImax, fluxOF, fluxUZ, fluxSZ, fluxWB, Qusz, grid = read_temporal_datasets_and_grid(data_in, topo)

    rain = PRE.get_one_step_dataset(0, data_in.fname_TSPre, 'pre')

    data_array_size = rain.shape[0]

    region_masks = generate_region_masks(data_array_size, n_masks)

    # Define input arrays for infiltration function; must match data_array_size
    input_arrays = {
        'Ksat': np.random.rand(data_array_size).astype(np.float32),
        'theta_sat': np.random.rand(data_array_size).astype(np.float64),
        'PSI': np.random.rand(data_array_size).astype(np.float32),
        'Droot': np.random.rand(data_array_size).astype(np.float64),
        'theta': np.random.rand(data_array_size).astype(np.float32),
        'Ft0': np.random.rand(data_array_size).astype(np.float64),
        'SORP0': np.random.rand(data_array_size).astype(np.float64),
        't_0': None,
        'rain': rain.copy(),  # use real rain data from file
        'rain_day_before': 1
    }

    region_args = ['Ksat', 'theta_sat', 'PSI', 'Droot', 'theta', 'Ft0', 'SORP0', 't_0', 'rain']
    output_shape = region_masks[0].shape  # output shape aligned with single region mask

    print("--- Running Parallel Test ---")
    parallel_outputs, parallel_time = parallel_masked_runner(
        inf.run_infiltration_one_step, region_masks, input_arrays, region_args, output_shape)

    print("\n--- Running Sequential Test ---")
    sequential_outputs, sequential_time = normal_full_runner(inf.run_infiltration_one_step, input_arrays)

    # Verification: compare parallel and sequential outputs if both return tuples
    print("\n--- Verification ---")
    if isinstance(parallel_outputs, tuple) and isinstance(sequential_outputs, tuple):
        if len(parallel_outputs) == len(sequential_outputs):
            print("Number of output arrays match.")
            for i in range(len(parallel_outputs)):
                if np.allclose(parallel_outputs[i], sequential_outputs[i], equal_nan=True):
                    print(f"Output array {i} (shape {parallel_outputs[i].shape}): MATCHES (within tolerance)")
                else:
                    print(f"Output array {i} (shape {parallel_outputs[i].shape}): MISMATCHES")
        else:
            print("Number of output arrays DO NOT match!")
    else:
        print("Output types are not tuples; cannot perform direct array comparison.")

    # Plot execution time comparison
    print("\n--- Plotting Results ---")
    labels = ['Sequential', 'Parallel']
    times = [sequential_time, parallel_time]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, times, color=['skyblue', 'lightcoral'])
    plt.ylabel('Execution Time (seconds)')
    plt.title('Sequential vs. Parallel Execution Time')
    plt.show()
