import os
import time
from cuwalid.stopet.main_stopet import run_stoPET

if __name__ == '__main__':
    start = time.time()

    # Get the directory where this script is located
    script_dir = os.path.dirname(__file__)
    # Construct the path to the JSON file
    input_file_path = os.path.join(script_dir, 'test_input.json')

    # Run the stoPET function with the input file path
    run_stoPET(input_file_path)
    
    end = time.time()
    print("Test run successfully")
    print('Time of run: %s' % (end - start))
