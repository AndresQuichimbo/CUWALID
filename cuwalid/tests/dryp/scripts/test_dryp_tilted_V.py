# -*- coding: utf-8 -*-
"""This script runs the test model "Tilted-V"
The model is published in the original paper
of the model release.
"""
import os
from cuwalid.dryp.main_DRYP import run_DRYP
import numpy as np
import pandas as pd
import pytest


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

	input_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tilted_v', 'input_test.json'))

	# run model test input file
	run_DRYP(input_file)
	
	# compare model results
	ans = aggregate_slice_csv('tilted_v/output/test_p_dis.csv',
			   agg_step='D')['dis_0']
	
	out = aggregate_slice_csv('tilted_v/output_test/test_p_dis.csv',
			   agg_step='D')['dis_0']
	
	assert np.allclose(out, ans)

	print('Tilted-V catchment model: Test completed successfully')

def test_dryp_zones():

	input_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tilted_v', 'input_test_zones.json'))
	
	# run model test input file
	run_DRYP(input_file)
	
	# compare model results
	ans = aggregate_slice_csv('tilted_v/output/test_p_dis.csv',
			   agg_step='D')['dis_0']
	
	out = aggregate_slice_csv('tilted_v/output_test/test_p_dis.csv',
			   agg_step='D')['dis_0']
	
	assert np.allclose(out, ans)

	print('Tilted-V catchment model: Test completed successfully')

if __name__ == '__main__':
	test_dryp()
	test_dryp_zones()