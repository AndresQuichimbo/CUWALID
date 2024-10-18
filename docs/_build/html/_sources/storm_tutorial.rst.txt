======================
Storm Tutorial
======================

Running the model
=================

IMPORTANT: GDAL is needed to be able to run storm, this cannot be added to the package because it does not work with the windows operating system,
you will need to install this yourself, it is recommended if you are using a conda environment you can run this:

.. code-block:: bash

    conda install gdal

To run the Storm model you can use the code below:

.. code-block:: python

    from cuwalid.storm.main_storm import run_storm

    run_storm("input.json")

Or run from the terminal using this command:

.. code-block:: bash

    # replace "input.json" with the path to your input json
    python -m cuwalid.storm.main_storm input.json


the files required to do the forecasting.

Input Parameters
================

The input JSON shown above will look something like this:

.. literalinclude:: ../txt/storm_input.json
    :language: json
    :linenos:

Here is an explanation of what each parameter does:

- **NUMSIMS**: `1`
  
  The number of simulation runs per season. Each simulation generates one NetCDF file.

- **NUMSIMYRS**: `2`
  
  The number of years to simulate for each run. This indicates how long the simulation will run.

- **PTOT_SC**: `[0.00]`
  
  A signed scalar specifying the step change in the observed wetness (total precipitation). Values must be between 0 and 1.

- **PTOT_SF**: `[0.0]`
  
  A signed scalar specifying the progressive trend in the observed wetness. This value also must be between 0 and 1.

- **STORMINESS_SC**: `[-0.0]`
  
  A signed scalar indicating the step change in observed storminess, with values between 0 and 1.

- **STORMINESS_SF**: `[0.0]`
  
  A signed scalar specifying the progressive trend in observed storminess. This value should be between 0 and 1.

- **PDF_FILE**: `"./model_input/ProbabilityDensityFunctions.csv"`
  
  The path to the Probability Density Functions CSV file, which contains the statistical parameters for the simulation.

- **SHP_FILE**: `"./model_input/HAD_basin.shp"`
  
  The path to the shapefile representing the catchment area. This file should be in WGS84 format.

- **DEM_FILE**: `"./model_input/HAD_wgs84.tif"`
  
  The path to the Digital Elevation Model (DEM) raster file. This is optional but required if running simulations at different altitudes.

- **ZON_FILE**: `"./model_input/regions.shp"`
  
  The path to the shapefile that defines the regions for the simulation.

- **OUT_PATH**: `"./storm_output"`
  
  The directory where the output files from the simulation will be saved.

- **RAIN_MAP**: `"./model_input/rainfall_OND.nc"`
  
  The path to the rainfall data file in NetCDF format. This file must have an interpretable coordinate reference system.

- **NREGIONS**: `4`
  
  The number of regions to split the catchment area into for the simulation. A value of 1 indicates no splitting.

- **Z_STAT**: `"mean"`
  
  The statistical method to retrieve from the DEM: 'mean', 'median', 'min', or 'max'.

- **Z_CUTS**: `[300, 600, 1200]`
  
  A list of altitude cuts in meters, defining the boundaries for different altitude bands.

- **TACTIC**: `1`
  
  The method by which the simulation must be run. A value of 1 indicates no copulas are used.

- **WKT_OGC**: 

  The Well-Known Text (WKT) representation of the projection system used for the simulation.

- **BUFFER**: `7000.0`

  The buffer distance in meters, extending the catchment boundary to delineate the area for generating storm centers.

- **X_RES**: `5000.0`

  The pixel resolution for the X-axis in meters for the 'regular/local' coordinate reference system.

- **Y_RES**: `5000.0`

  The pixel resolution for the Y-axis in meters for the 'regular/local' coordinate reference system.

- **T_RES**: `30`

  The temporal resolution of time slices in minutes.

- **NO_RAIN**: `0.01`

  The minimum measurable precipitation in millimeters for the area of interest.

- **MIN_DUR**: `20`

  The minimum duration of rain events in minutes.

- **MAX_DUR**: `5760`

  The maximum duration of rain events in minutes, equivalent to 4 days.

- **MAXD_RAIN**: `120`

  The designed maximum rainfall in millimeters for the specified temporal resolution.

- **DISPERSE_**: `0.2`

  The factor used to split the maximum rainfall into multiple events.

- **SEASON_TAG**: `"OND"`

  The tag identifying the seasonal period of the simulation.

- **SEED_YEAR**: `2024`

  The year in which the simulation will start.

- **TIME_ZONE**: `"Africa/Addis_Ababa"`

  The local time zone for the simulation.

- **DATE_ORIGIN**: `"1970-01-01"`

  The origin date used for storing dates as integers.

- **RAINFMT**: `"u2"`

  The format for storing the rainfall variable, with 'u' indicating unsigned integers.

- **PRECISION**: `0.002`

  The precision of the output values.

- **TIMEINT**: `"u4"`

  The format for integers in the time dimension, where 'u' indicates unsigned integers.

- **TIMEFIL**: `4294967295`

  The maximum value for the time dimension.

- **TIME_OUTNC**: `"minutes"`

  The units for the NetCDF time dimension.

- **TIME_DICT_**: 

  A dictionary mapping various time units to their corresponding values in seconds.

- **RAIN_NAME**: `"rain"`

  The name used to identify the rainfall variable in the output files.
