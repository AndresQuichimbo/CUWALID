.. _cuwalid_tutorial:

======================
CUWALID Tutorial
======================

Preparing your system for running CUWALID
=========================================

IMPORTANT: GDAL is needed to be able to run the storm, this cannot be added to the package because it does not work with the windows operating system,
you will need to install this yourself, it is recommended if you are using a conda environment you can run this:

.. code-block:: bash

    conda install gdal "numpy<2.0"

IMPORTANT: For running stoPET you need to download some pararmeter files, the system will give you a warning if you try to run it without the files,
The command for downloading these files if using cuwalid as a package is:

.. code-block:: bash

    # For using as a package (PyPi)
    python -m cuwalid.tools.download_data
    # For downloading the project from GitHub
    python cuwalid/tools/download_data.py

Running the models
==================

To run the models in CUWALID you can use the code below:

.. code-block:: python

    from cuwalid.main_cuwalid import run_cuwalid

    run_cuwalid("cuwalid_input.json")

Or run from the terminal using this command:

.. code-block:: bash

    # replace "cuwalid_input.json" with the path to your input json
    python -m cuwalid.main_cuwalid cuwalid_input.json

Input for CUWALID
=================

The input of CUWALID is a combined version of all the json files used for the models (e.g. dryp, stopet, storm)
For finding the meaning of each parameter, I would look at the tutorials for each of the models for an example and description.

It will look something like the file json file below:

.. literalinclude:: ../txt/cuwalid_input.json
    :language: json
    :linenos:

Parameters Descriptions
=======================

run_STORM
    *Type*: Boolean  
    Whether to run the STORM simulation. Set to `true` to enable.

run_stoPET
    *Type*: Boolean  
    Whether to run the stoPET simulation. Set to `true` to enable.

run_DRYP
    *Type*: Boolean  
    Whether to run the DRYP simulation. Set to `true` to enable.

run_WaterCast
    *Type*: Boolean  
    Whether to run the WaterCast simulation. Set to `true` to enable.

sim_in_parallel
    *Type*: Boolean  
    If set to `false` all processes will run sequentially, if set as `true` this will use 'nohup' to run simulations in the background to save time (only for the dryp model and impact map plotting), but some issues may occur with memory allocation based on your environment.

historical
----------

model_name
    *Type*: String  
    The name of the historical model used for the simulation.

main_path
    *Type*: String  
    Path to the main directory of the historical dataset.

model_path
    *Type*: String  
    Path to the directory containing the historical model outputs.

postpp_path
    *Type*: String  
    Path to the post-processing outputs of the historical simulation.


forecasting
-----------

forecasting_model_name
    *Type*: String  
    The name of the forecasting model used for the simulation.

Tercile_Pre_path
    *Type*: String  
    Path to the NetCDF file for the precipitation tercile data (For StoPET).

Tercile_Tem_path
    *Type*: String  
    Path to the NetCDF file for the temperature tercile data (For Storm). This is converted to a .shp file that is necessary for storm

threshold_path
    *Type*: String  
    Path to the threshold data files in NetCDF format.

season
    *Type*: List of Strings  
    The season(s) for which the simulation is run. Example: `["OND"]`.

start_year
    *Type*: Integer  
    The first year in the simulation period.

end_year
    *Type*: Integer  
    The last year in the simulation period.

year
    *Type*: Integer  
    The specific year for which the simulation is run.

NSIM
    *Type*: Integer  
    The number of simulation realisations to run.

MODELS
------

DRYP
~~~~

input
    *Type*: String  
    Path to the input JSON file for the DRYP model. Find the parameters :ref:`here <dryp_parameters>` 

settings
    *Type*: String  
    Path to the settings directory for the DRYP model. Find the parameters :ref:`here <dryp_settings_parameters>` 

STORM
~~~~~

input
    *Type*: String  
    Path to the input JSON file for the STORM model. Find the parameters :ref:`here <storm_parameters>` 

stoPET
~~~~~~

input
    *Type*: String  
    Path to the input JSON file for the stoPET model. Find the parameters :ref:`here <stopet_parameters>` 

WaterCast
~~~~~~~~~

HyCast
    *Type*: String  
    Path to the forecast input JSON file for the HyCast submodule of WaterCast.

ImCast
    *Type*: String  
    Path to the impact forecast input JSON file for the ImCast submodule of WaterCast.




