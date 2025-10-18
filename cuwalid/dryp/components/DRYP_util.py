import numpy as np

def collapse_mean(a, b):
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

    # Precompute group start indices (avoids repeated array concat)
    idx = np.empty_like(b, dtype=int)
    np.cumsum(b[:-1], out=idx[1:])
    idx[0] = 0

    # Fast mean computation using reduceat
    return np.add.reduceat(a, idx) / b
