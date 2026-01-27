import numpy as np

from cuwalid.dryp.components.DRYP_io import find_location_of_nearest_node, get_idnode_from_grid

def test_find_location_of_nearest_node():
    """
    Test the find_location_of_nearest_node function.
    """
    # Create coordinate arrays for a 3x3 grid
    x_array = np.array([0.0, 1.0, 2.0])  # x coordinates of columns
    y_array = np.array([0.0, 1.0, 2.0])  # y coordinates of rows
    
    # Test single point at center
    xpoint = np.array([1.0])
    ypoint = np.array([1.0])
    result = find_location_of_nearest_node(x_array, y_array, xpoint, ypoint)
    expected = np.array([1, 1])  # (column index, row index)
    assert np.array_equal(result, expected), f"Expected {expected}, got {result}"
    
    # Test point at (0.5, 0.5) - closest x is 0 (0.0), closest y is 0 (0.0)
    xpoint = np.array([0.5])
    ypoint = np.array([0.5])
    result = find_location_of_nearest_node(x_array, y_array, xpoint, ypoint)
    expected = np.array([0, 0]) # (column index, row index)
    assert np.array_equal(result, expected), f"Expected {expected}, got {result}"

def test_get_idnode_from_grid():
    """
    Test the get_idnode_from_grid function.
    """
    # Create a mock grid dict for a 3x3 grid
    N_x = 3
    N_y = 3
    N_cells = 9
    x = np.array([0.0, 1.0, 2.0])  # x coordinates
    y = np.array([0.0, 1.0, 2.0])  # y coordinates
    core_nodes = np.arange(N_cells)  # all nodes active
    
    grid = {
        'N_x': N_x,
        'N_y': N_y,
        'N_cells': N_cells,
        'x': x,
        'y': y,
        'core_nodes': core_nodes
    }
    
    # Test single point at center
    xpoint = np.array([1.0])
    ypoint = np.array([1.0])
    result = get_idnode_from_grid(grid, xpoint, ypoint)
    expected = [4]  # node id for (1,1) in 3x3 grid, row-major: 0 1 2 / 3 4 5 / 6 7 8
    assert result == expected, f"Expected {expected}, got {result}"
    
    # Test point at (0.5, 0.5) - closest to (0,0)
    xpoint = np.array([0.5])
    ypoint = np.array([0.5])
    result = get_idnode_from_grid(grid, xpoint, ypoint)
    expected = [0]
    assert result == expected, f"Expected {expected}, got {result}"
    
if __name__ == "__main__":
    test_find_location_of_nearest_node()
    test_get_idnode_from_grid()
    print("All tests passed!")