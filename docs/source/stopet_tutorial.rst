======================
StoPET Tutorial
======================

Running the model
=================

To run the StoPET model you can use the code below:

.. code-block:: python

    from cuwalid.stopet.main_stopet import run_stoPET

    run_stoPET("input.json")

Or run from the terminal using this command:

.. code-block:: bash

    # replace "input.json" with the path to your input json
    python -m cuwalid.stopet.main_stopet input.json


Once this script runs it will produce all the required folders in the root_outputpath
With new folders being created as result_R<trial> (e.g. result_R0, result_R1, …).
Within each folder, there will be other folders containing the netcdf files. These are the files required to do the forecasting.

Next, we run the forecast generation. This will also use the same json input you just used to get the required variables, navigate through the folders created before, and do the forecasting. The final netcdf files will be stored in a folder called ensemble_forecast, which will be created in the root_outputpath.

To run the forecast in your code you can use the code below:

.. code-block:: python

    from cuwalid.stopet.forecast_generation_v2 import run_pet_forecast

    run_pet_forecast("input.json")

Or from the command line using this command

.. code-block:: bash

    # replace "input.json" with the path to your input json
    python -m cuwalid.stopet.forecast_generation_v2 input.json

.. _stopet_parameters:

Input Parameters
================

The input JSON shown above will look something like this:

.. literalinclude:: ../txt/stopet_input.json
    :language: json
    :linenos:

Here is an explanation of what each parameter does:

- **execution_type**: `"hpc"`

  Can be set to "dryp" or "hpc". The standard choice is "dryp" and it will complete the trials in a loop. "hpc" can be used if you would like the trials to completed one at a time, good for a batch job submission.

- **outputpath**: `"stopet_output"`
  
  The directory where the output of the model will be placed.

- **runtype**: `"regional"`
  
  This is a string input with two options. 'regional' or 'single'. It will tell the model whether the PET is generated for a single point or an area of a specified region (or rectangle).

- **startyear**: `2024`
  
  The year from which the user wants to start the PET time series to start.

- **endyear**: `2024`
  
  The last year requested by the user for the PET time series.

- **seasonswitch**: `1`

  this is the seasonal julian dates required as a start date and end date

- **startdate**: `274`

  this is the seasonal julian dates required as a start date and end date

- **enddate**: `365`

  this is the seasonal julian dates required as a start date and end date

- **seasonName**: `"OND"`

  this is the seasonal julian dates required as a start date and end date
  
- **latval**: `3.8`
  
  The latitude of the single point where the user wants the PET.

- **lonval**: `36.6`
  
  The longitude of the single point where the user wants the PET.

- **latval_min**: `-5.5`
  
  This is for running stoPET on an area.
  The minimum latitude of the region.

- **latval_max**: `-4.5`
  
  The maximum latitude of the region. 

- **lonval_min**: `33.0`
  
  The minimum longitude of the region.

- **lonval_max**: `34.5`
  
  The maximum longitude of the region. 

- **locname**: `"HAD"`
  
  Any name to be given as a string which will be used in the file name of the final PET outcome of the location.

- **number_ensm**: `3`
  
  This is the number of ensembles the user wishes to run with each realization. It is kept 1 by default but if the user wants to have multiple runs the number should be given by this variable. HERE THE NUMBER SHOULD BE DIVISIBLE BY 3

- **tempAdj**: `3`
  
  This is an integer number with values 1, 2, or 3. Each of these numbers represents what method to use for the model to account for temperature adjustment on future PET.
  
  Method 1 = 1, Method 2 = 2, Method 3 = 3 
  Refer to the paper for the description of each method.

- **deltat**: `1.5`
  
  This variable represents the user-defined temperature increase expected in the area of interest. The value will only be used if Method 2 (tempAdj = 2) is selected as the temperature adjustment technique. Otherwise, this value will be ignored by the model.

- **udpi_pet**: `5`
  
  This variable is the user-defined percentage increase of PET. The value should be from 0 to 100. This will be used to adjust the estimated PET by the user-provided percentage if Method 1 (tempAdj = 1). Otherwise, this value will be ignored by the model.

- **slice_only**: `6`

  This is a variable that telss wheather to run a 
  full yearly PET and slice the given season or 
  just slice the season since you already run the yearly PET extimate
  slice_only = 0 (run all the PET yearly first and then slice the season)
  slice_only = 1 (run the slicing only)
  
- **tercile_forecast_file**: `"ICPAC_TempF_OND2022_HAD.nc"`

  This is the file containing the ICPAC seasonal tercile temperature forecast. provide the full path where it is located.