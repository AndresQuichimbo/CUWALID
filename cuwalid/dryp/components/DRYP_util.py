import numpy as np

def collapse_mean_indices(group_sizes):
    group_sizes = np.asanyarray(group_sizes)

    if group_sizes.ndim != 1:
        raise ValueError("group_sizes must be one-dimensional")

    idx = np.empty_like(group_sizes, dtype=int)
    idx[0] = 0
    if group_sizes.size > 1:
        np.cumsum(group_sizes[:-1], out=idx[1:])
    return idx

def collapse_mean(a, b, idx=None):
    """Compute the mean of groups of values in an array.
    
    Parameters
    ----------
    a : array_like
        Array of values to be averaged.
    b : array_like of int
        Array with the number of values in each group.
        
    Returns
    -------
    c : ndarray
        Array with the mean of each group.
    """
    a = np.asanyarray(a)
    b = np.asanyarray(b)

    if b.ndim != 1:
        raise ValueError("b must be one-dimensional")
    if b.sum() != a.size:
        raise ValueError("Sum of b must equal the length of a")

    if idx is None:
        idx = collapse_mean_indices(b)

    # Fast mean computation using reduceat
    return np.add.reduceat(a, idx) / b

def print_grid_location_from_array(rows, cols, core_nodes, array, array_name):
    """Print the grid locations (row, col) of NaN values in a given array. 
    Parameters
    ----------
    rows : int
        Number of rows in the grid.
    cols : int
        Number of columns in the grid.
    core_nodes : array_like of int
        Array mapping the core nodes to the grid.
    array : array_like
        Array containing the values to check for NaNs.
    array_name : str
        Name of the array (for printing purposes).
    """
    # Map the indices to 2D coordinates (row, col) using core_nodes
    grid = np.zeros(rows * cols)#.reshape((rows, cols))
    grid[core_nodes[array]] = 1
    # reshape the grid to 2D
    grid = grid.reshape((rows, cols))
    nan_rows, nan_cols = np.where(grid == 1) #
    print(f"NaN in {array_name} found at the following grid locations (row, col):")
    for row, col in zip(nan_rows[:10], nan_cols[:10]):  # print only the first 10 locations
        print(f"Row: {row}, Column: {col}")
