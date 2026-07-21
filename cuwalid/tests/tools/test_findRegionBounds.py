import unittest
from cuwalid.tools.DRYP_rrtools import find_region_bounds
from cuwalid.tools.DRYP_rrtools import find_region_bounds
import numpy as np

class TestFindRegionBounds(unittest.TestCase):

    def test_empty_array(self):
        """Should return None if no pixels are greater than zero."""
        arr = np.zeros((10, 10))
        self.assertIsNone(find_region_bounds(arr))

    def test_single_pixel_no_frame(self):
        """Should isolate exactly one pixel when add_empty_frame=False."""
        arr = np.zeros((5, 5))
        arr[2, 3] = 10
        
        bounds = find_region_bounds(arr, add_empty_frame=False)
        self.assertEqual(bounds, (2, 3, 3, 4))
        
        # Test that slicing extracts exactly the region
        cropped = arr[bounds[0]:bounds[1], bounds[2]:bounds[3]]
        self.assertEqual(cropped.shape, (1, 1))
        self.assertEqual(cropped[0, 0], 10)

    def test_single_pixel_with_frame(self):
        """Should pad by 1 pixel safely within boundaries."""
        arr = np.zeros((5, 5))
        arr[2, 2] = 7
        
        bounds = find_region_bounds(arr, add_empty_frame=True)
        self.assertEqual(bounds, (1, 4, 1, 4))
        
        # Verify slice is a 3x3 window with the target in the center
        cropped = arr[bounds[0]:bounds[1], bounds[2]:bounds[3]]
        self.assertEqual(cropped.shape, (3, 3))
        self.assertEqual(cropped[1, 1], 7)

    def test_edge_clipping_with_frame(self):
        """Padding should not exceed matrix boundaries at row/col 0 or max."""
        arr = np.zeros((4, 6))
        arr[0, 5] = 1  # Top-left corner and bottom-right edge test
        
        bounds = find_region_bounds(arr, add_empty_frame=True)
        # min_row should stay 0, max_col should clamp to array width (6)
        self.assertEqual(bounds, (0, 2, 4, 6))

    def test_negative_values_ignored(self):
        """Negative values or zeros should not be recognized as the region."""
        arr = np.array([
            [0,  0,  0],
            [-5, 0,  0],
            [0,  0,  9]
        ])
        bounds = find_region_bounds(arr, add_empty_frame=False)
        # Should only target the bottom right pixel (9)
        self.assertEqual(bounds, (2, 3, 2, 3))

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    