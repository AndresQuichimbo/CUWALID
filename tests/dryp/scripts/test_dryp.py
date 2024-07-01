from context import dryp
import numpy as np
import pandas as pd
from models.DRYP.dryp.main_DRYP import run_DRYP

def test_dryp():
	"""run a test model file
	"""
	run_DRYP('tilted_v/input_test.dmp')
	
	df = pd.read_csv('tilted_v/output/test_p_dis.csv')
	ans = np.array(df['dis_0'])
	#df = pd.read_csv('test/output/test_OF_Dis.csv')
	#ans = np.array(df['OF_0'])
	
	df = pd.read_csv('tilted_v/output_test/test_p_dis.csv')
	out = np.array(df['dis_0'])
	
	assert np.allclose(out, ans)

	print('Test model: Test runs successfully')

if __name__ == '__main__':
	test_dryp()