# -*- coding: utf-8 -*-
"""This script runs the test model "Tilted-V"
The model is published in the original paper
of the model release.
"""
from context import dryp
from cuwalid.dryp.main_DRYP import run_DRYP
import numpy as np
import pandas as pd


def aggregate_slice_csv(fname, agg_step='M', mean=True,
			date_start='2000-01-01', date_end='2001-01-01'):
	df = pd.read_csv(fname)
	df["Date"] = pd.to_datetime(df['Date'])
	df = df[df['Date'].between(date_start, date_end)]
	df.index = pd.DatetimeIndex(df['Date'])
	if mean is True:
		df = df.resample(agg_step).mean()#.reset_index()
	else:
		df = df.resample(agg_step).sum()#.reset_index()
	return df

def test_dryp():
	# run model test input file
	run_DRYP('tilted_v/input_test.dmp')
	
	# compare model results
	ans = aggregate_slice_csv('tilted_v/output/test_p_dis.csv',
			   agg_step='D')['dis_0']
	
	out = aggregate_slice_csv('tilted_v/output_test/test_p_dis.csv',
			   agg_step='D')['dis_0']
	
	assert np.allclose(out, ans)

	print('Tilted-V catchment model: Test runs successfully')

if __name__ == '__main__':
	test_dryp()