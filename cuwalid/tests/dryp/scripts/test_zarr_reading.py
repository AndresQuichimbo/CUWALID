import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from cuwalid.dryp.components.DRYP_read_dataset import read_dataset, read_dataset_interp


def create_test_zarr_store(store_path, var_name='pre', dates=None, lat=None, lon=None):
	if dates is None:
		start_date = pd.Timestamp('2000-01-01 00:00:00')
		end_date = pd.Timestamp('2000-01-03 00:00:00')
		dates = pd.date_range(start=start_date, end=end_date, freq='h')[:-1]
	if lat is None:
		lat = np.array([0.0, 1.0])
	if lon is None:
		lon = np.array([10.0, 11.0, 12.0])
	data = np.arange(1, len(dates) * len(lat) * len(lon) + 1, dtype=float)
	data = data.reshape((len(dates), len(lat), len(lon)))

	da = xr.DataArray(
		data,
		coords=[dates, lat, lon],
		dims=['time', 'lat', 'lon'],
		name=var_name,
	)
	ds = xr.Dataset({var_name: da}).chunk({'time': 1, 'lat': len(lat), 'lon': len(lon)})
	ds.to_zarr(store_path, mode='w')
	return data, lat, lon


def run_test_zarr_read_dataset_interp_reads_chunked_store(tmp_path):
	store_path = Path(tmp_path) / 'forcing_pre.zarr'
	data, lat, lon = create_test_zarr_store(store_path)

	reader = read_dataset_interp(
		dt=60,
		dt_ds=60,
		ini_date=datetime(2000, 1, 1, 0, 0, 0),
		end_date=datetime(2000, 1, 3, 0, 0, 0),
		file_format=7,
		reproject=False,
		interpolate=False,
		grid_length=len(lat) * len(lon),
		lat=lat,
		lon=lon,
	)

	step0 = reader.get_one_step_dataset(0, str(store_path), 'pre')
	step5 = None
	for j_step in range(1, 6):
		step5 = reader.get_one_step_dataset(j_step, str(store_path), 'pre')

	assert np.array_equal(step0, data[0].flatten())
	assert np.array_equal(step5, data[5].flatten())
	assert reader.ds.chunksizes['time'] == (1,) * len(reader.ds.time)


def test_zarr_read_dataset_interp_reads_chunked_store(tmp_path):
	run_test_zarr_read_dataset_interp_reads_chunked_store(tmp_path)


def test_zarr_read_dataset_interp_forward_fills_missing_steps(tmp_path):
	store_path = Path(tmp_path) / 'forcing_missing_step.zarr'
	dates = pd.date_range('2000-01-01 00:00:00', '2000-01-01 05:00:00', freq='h')
	dates = dates.delete(2)
	data, lat, lon = create_test_zarr_store(store_path, dates=dates)

	reader = read_dataset_interp(
		dt=60,
		dt_ds=60,
		ini_date=datetime(2000, 1, 1, 0, 0, 0),
		end_date=datetime(2000, 1, 1, 5, 0, 0),
		file_format=7,
		reproject=False,
		interpolate=False,
		grid_length=len(lat) * len(lon),
		lat=lat,
		lon=lon,
		fill_missing_time=True,
	)

	step0 = reader.get_one_step_dataset(0, str(store_path), 'pre')
	step1 = reader.get_one_step_dataset(1, str(store_path), 'pre')
	step2 = reader.get_one_step_dataset(2, str(store_path), 'pre')

	assert np.array_equal(step0, data[0].flatten())
	assert np.array_equal(step1, data[1].flatten())
	assert np.array_equal(step2, data[1].flatten())


def test_zarr_read_dataset_interp_clips_to_model_domain_without_interpolation(tmp_path):
	store_path = Path(tmp_path) / 'forcing_clipped_domain.zarr'
	data, _, _ = create_test_zarr_store(store_path)

	reader = read_dataset_interp(
		dt=60,
		dt_ds=60,
		ini_date=datetime(2000, 1, 1, 0, 0, 0),
		end_date=datetime(2000, 1, 1, 2, 0, 0),
		file_format=7,
		reproject=False,
		interpolate=False,
		grid_length=2,
		lat=np.array([0.0]),
		lon=np.array([11.0, 12.0]),
	)

	step0 = reader.get_one_step_dataset(0, str(store_path), 'pre')

	assert np.array_equal(step0, data[0, 0:1, 1:3].flatten())


def test_zarr_read_dataset_interp_matches_model_lat_lon_size_without_interpolation(tmp_path):
	store_path = Path(tmp_path) / 'forcing_dense_domain.zarr'
	source_lat = np.array([0.0, 0.5, 1.0])
	source_lon = np.array([10.0, 10.5, 11.0, 11.5, 12.0])
	data, _, _ = create_test_zarr_store(store_path, lat=source_lat, lon=source_lon)

	reader = read_dataset_interp(
		dt=60,
		dt_ds=60,
		ini_date=datetime(2000, 1, 1, 0, 0, 0),
		end_date=datetime(2000, 1, 1, 2, 0, 0),
		file_format=7,
		reproject=False,
		interpolate=False,
		grid_length=6,
		lat=np.array([0.0, 1.0]),
		lon=np.array([10.0, 11.0, 12.0]),
	)

	step0 = reader.get_one_step_dataset(0, str(store_path), 'pre')

	assert step0.size == 6
	assert np.array_equal(step0, data[0][::2, ::2].flatten())


def run_test_zarr_read_dataset_reads_chunked_store(tmp_path):
	store_path = Path(tmp_path) / 'forcing_seq.zarr'
	data, _, _ = create_test_zarr_store(store_path, var_name='rain')

	reader = read_dataset(
		dt=60,
		dt_ds=60,
		ini_date=datetime(2000, 1, 1, 0, 0, 0),
		end_date=datetime(2000, 1, 3, 0, 0, 0),
		file_format=7,
		reproject=False,
		interpolate=False,
		grid_length=data.shape[1] * data.shape[2],
	)

	step0 = reader.get_one_step_dataset(0, str(store_path), 'pre')
	step1 = reader.get_one_step_dataset(1, str(store_path), 'pre')

	assert np.array_equal(step0, data[0].flatten())
	assert np.array_equal(step1, data[1].flatten())
	assert reader.fpre.chunksizes['time'] == (1,) * len(reader.fpre.time)


def test_zarr_read_dataset_reads_chunked_store(tmp_path):
	run_test_zarr_read_dataset_reads_chunked_store(tmp_path)


def test_zarr_read_dataset_forward_fills_missing_steps(tmp_path):
	store_path = Path(tmp_path) / 'forcing_seq_missing_step.zarr'
	dates = pd.date_range('2000-01-01 00:00:00', '2000-01-01 05:00:00', freq='h')
	dates = dates.delete(2)
	data, _, _ = create_test_zarr_store(store_path, var_name='rain', dates=dates)

	reader = read_dataset(
		dt=60,
		dt_ds=60,
		ini_date=datetime(2000, 1, 1, 0, 0, 0),
		end_date=datetime(2000, 1, 1, 5, 0, 0),
		file_format=7,
		reproject=False,
		interpolate=False,
		grid_length=data.shape[1] * data.shape[2],
		fill_missing_time=True,
	)

	step0 = reader.get_one_step_dataset(0, str(store_path), 'pre')
	step1 = reader.get_one_step_dataset(1, str(store_path), 'pre')
	step2 = reader.get_one_step_dataset(2, str(store_path), 'pre')

	assert np.array_equal(step0, data[0].flatten())
	assert np.array_equal(step1, data[1].flatten())
	assert np.array_equal(step2, data[1].flatten())


def test_dataset_reads_keep_float32_for_float_variables_and_int_for_integer_variables(tmp_path):
	store_path = Path(tmp_path) / 'forcing_dtype.zarr'
	dates = pd.date_range('2000-01-01 00:00:00', '2000-01-02 00:00:00', freq='h')[:-1]
	lat = np.array([0.0, 1.0])
	lon = np.array([10.0, 11.0])
	float_data = np.arange(len(dates) * len(lat) * len(lon), dtype=np.float64).reshape(len(dates), len(lat), len(lon))
	int_data = np.arange(len(dates) * len(lat) * len(lon), dtype=np.int32).reshape(len(dates), len(lat), len(lon))

	ds = xr.Dataset({
		'pre': xr.DataArray(float_data, coords=[dates, lat, lon], dims=['time', 'lat', 'lon']),
		'cell_id': xr.DataArray(int_data, coords=[dates, lat, lon], dims=['time', 'lat', 'lon'])
	})
	ds.to_zarr(store_path, mode='w')

	float_reader = read_dataset_interp(
		dt=60,
		dt_ds=60,
		ini_date=datetime(2000, 1, 1, 0, 0, 0),
		end_date=datetime(2000, 1, 2, 0, 0, 0),
		file_format=7,
		reproject=False,
		interpolate=False,
		grid_length=len(lat) * len(lon),
		lat=lat,
		lon=lon,
	)
	float_result = float_reader.get_one_step_dataset(0, str(store_path), 'pre')
	assert float_result.dtype == np.float32

	int_reader = read_dataset_interp(
		dt=60,
		dt_ds=60,
		ini_date=datetime(2000, 1, 1, 0, 0, 0),
		end_date=datetime(2000, 1, 2, 0, 0, 0),
		file_format=7,
		reproject=False,
		interpolate=False,
		grid_length=len(lat) * len(lon),
		lat=lat,
		lon=lon,
	)
	int_result = int_reader.get_one_step_dataset(0, str(store_path), 'cell_id')
	assert int_result.dtype == np.int32


if __name__ == '__main__':
	with TemporaryDirectory() as tmp_dir:
		run_test_zarr_read_dataset_interp_reads_chunked_store(tmp_dir)
		run_test_zarr_read_dataset_reads_chunked_store(tmp_dir)
	print('Zarr reading tests completed successfully')