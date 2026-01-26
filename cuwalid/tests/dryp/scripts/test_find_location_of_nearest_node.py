import numpy as np

from cuwalid.dryp.components.DRYP_io import find_location_of_nearest_node

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
    expected = [(1, 1)]  # (column index, row index)
    assert result == expected, f"Expected {expected}, got {result}"
    
    # Test point at (0.5, 0.5) - closest x is 0 (0.0), closest y is 0 (0.0)
    xpoint = np.array([0.5])
    ypoint = np.array([0.5])
    result = find_location_of_nearest_node(x_array, y_array, xpoint, ypoint)
    expected = [(0, 0)]
    assert result == expected, f"Expected {expected}, got {result}"
    
if __name__ == "__main__":
    test_find_location_of_nearest_node()
    print("All tests passed!")