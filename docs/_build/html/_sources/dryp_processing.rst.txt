DRYP Pre- and post-processing tools
===================================

Preprocessing tools
-------------------

Preprocessing tools is a python library that contains a series of functions developed to prepare
raster dataset that are required for running DRYP.
These functions are limited to especific and simple raster (matrix) operations, 
so complex operation will require the use of specialised GIS software (Geographical Information
System), e.g: QGIS <https://qgis.org/en/site/>, ArcGIS <https://www.arcgis.com/index.html> or any
python library available for raster processing (e.g rasterio <https://rasterio.readthedocs.io/en/stable/>,
geopandas <https://geopandas.org/en/stable/index.html>, gdal <https://gdal.org/api/python_bindings.html>).
A list of function s available can be found at :doc: 'DRYP_pptools:DRYP-pptools'.


Pre-processing dataset
----------------------


To calculate the constributed areas (watersheds) at location specified in the outputs point files, the following the following code can be used:

.. parsed-literal::

	>>> from cuwalid.dryp.components.DRYP_watershed import get_area_watershed
	>>> filename = "test_input.txt"
	>>> get_area_watershed(filename)


To find the extend of the contributing area for a specific location the following code can be used:

.. parsed-literal::

	>>> outlet = np.zeros_like(dem, dtype=int)
	>>> outlet[ipoint] = 1

	>>> ibasin = watershed(dem, outlet, nrows, ncols, flowDir=flowDir, cellsize=cellsize)
	>>> ibasin = np.flip(ibasin.reshape(nrows, ncols), 0)
	>>> data, profile, transform = open_raster(fname)
	>>> fname_basin = "basin.asc"
	>>> save_raster(fname_basin, ibasin, profile, transform)

Generate soil parameters files required for DRYP.


Postprocessing tools
--------------------

Post processing tools are functions to create additionl varaibles from DRYP model outputs.