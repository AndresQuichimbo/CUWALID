import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

import cuwalid.tools.CUWALID_view_tool as cuwalidplt


def test_plot_probabilistic_tercile_forecast():
	data = xr.Dataset(
		{
			"AN": (("lat", "lon"), np.array([[0.45, 0.60], [0.50, 0.70]])),
			"NN": (("lat", "lon"), np.array([[0.36, 0.42], [0.40, 0.52]])),
			"BN": (("lat", "lon"), np.array([[0.35, 0.48], [0.55, 0.65]])),
		},
		coords={"lat": [0.0, 1.0], "lon": [35.0, 36.0]},
	)

	plt.close("all")
	cuwalidplt.plot_probabilistic_tercile_forecast(data, title="Test Forecast")

	fig = plt.gcf()
	main_ax = fig.axes[0]

	assert main_ax.get_title() == "Test Forecast"
	assert main_ax.get_xlabel() == "Longitude"
	assert main_ax.get_ylabel() == "Latitude"

	colorbar_labels = [ax.get_xlabel() for ax in fig.axes[1:]]
	assert "Above-Normal (%)" in colorbar_labels
	assert "Near-Normal (%)" in colorbar_labels
	assert "Below-Normal (%)" in colorbar_labels
	
	plt.show()

	#plt.close(fig)
