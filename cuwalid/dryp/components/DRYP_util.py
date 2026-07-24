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
