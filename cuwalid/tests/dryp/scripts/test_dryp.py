import os
import numpy as np
import pandas as pd
from cuwalid.dryp.main_DRYP import run_DRYP

def test_dryp():
    
    """Run a test model file"""
    # Construct path to input file relative to package
    input_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tilted_v', 'input_test.dmp'))
    run_DRYP(input_file)
    
    # Construct paths to output files relative to package
    output_file1 = os.path.join(os.path.dirname(__file__), '..', 'tilted_v', 'output', 'test_p_dis.csv')
    output_file2 = os.path.join(os.path.dirname(__file__), '..', 'tilted_v', 'output_test', 'test_p_dis.csv')
    
    # Read and process the first output file
    df1 = pd.read_csv(output_file1)
    ans = np.array(df1['dis_0'])
    
    # Read and process the second output file
    df2 = pd.read_csv(output_file2)
    out = np.array(df2['dis_0'])
    
    # Perform assertion on the outputs
    assert np.allclose(out, ans)

    print('Test model: Test runs successfully')

if __name__ == '__main__':
    test_dryp()
