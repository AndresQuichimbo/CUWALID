import os
import sys
import traceback

package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, package_root)

from cuwalid.tests.dryp.scripts import (
    test_groundwater_multyaq_geo,
    test_precipitation,
    test_precipitation_csv,
    test_precipitation_step,
    test_infiltration,
    test_soil_layer,
    test_flow_accum_fortran,
    test_gw_sw_interaction,
    test_groundwater_multyaq_ss,
    test_groundwater_multyaq,
    test_groundwater_multyaq_geo,
    test_groundwater_ss_slopefactor,
    test_groundwater,
    test_save_necdf,
    test_save_necdf_maximum,
    test_save_csv,
    test_dryp_model,
    test_dryp_tilted_V,
    test_dryp,
    test_basin_delineation,
    test_ponds,
    test_water_bodies,
    test_find_location_of_nearest_node
)

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
dryp_dir = os.path.join(current_dir)
os.chdir(current_dir) 



test_functions = [
    test_ponds.test_ponds,
    test_precipitation.test_precipitation,
    test_precipitation_csv.test_precipitation,
    test_precipitation_step.test_precipitation,
    test_infiltration.test_infiltration,
    test_soil_layer.test_soil_layer,
    test_flow_accum_fortran.test_runoff,
    test_gw_sw_interaction.test_gw_sw_interaction,
    test_groundwater_multyaq_ss.run_DRYP_SS,
    test_groundwater_multyaq.test_groundwater_multiaq,
    test_groundwater_multyaq_geo.test_groundwater_multiaq,
    test_groundwater_ss_slopefactor.run_DRYP_SS,
    test_groundwater.test_groundwater,
    test_save_necdf.test_save_variables,
    test_save_necdf_maximum.test_save_maximum,
    test_save_csv.test_save_variables,
    test_dryp_model.test_dryp,
    test_dryp_tilted_V.test_dryp,
    test_dryp_tilted_V.test_dryp_zones,
    test_dryp.test_dryp,
    test_basin_delineation.test_basin_delineation,
    test_water_bodies,
    test_find_location_of_nearest_node.test_find_location_of_nearest_node
]

# Function to run tests
def run_tests():
    tests_run_successfully = True
    for test in test_functions:
        try:
            test()
        except Exception as e:
            tests_run_successfully = False
            print(f"Error running test from file: {test.__module__} - {str(e)}")
            traceback.print_exc()
    
    if tests_run_successfully:
        print("All tests completed successfully!")


if __name__ == "__main__":
    run_tests()
