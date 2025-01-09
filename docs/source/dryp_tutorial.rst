======================
DRYP Tutorial
======================

Runing the Tilted-V catchment model test
========================================

This folder contains files to run the tilted-V catchment model.

.. image:: ../fig/DRYP_GW_model_test.png

Model parameters and simulation settings
---------------------------------------------

The model requires a series of files that correspond to the parameter of the model. The parameters files have to be specified in the model input file:
input_test.dmp

The model also requires a setting file where all the model simulation parameters are specified:
setting_test.dmp

The example files are all provided in this directory for you to modify or replace, more information on the details of parameters and creating the DRYP inputs can be
:ref:`found here <dryp_parameters>`.


Running the simulation
--------------------------

Before you run the model, it is recommended to follow the steps for installation
:ref:`found here <installation_steps>` and activate the conda environments created for you in the instillation using this command:

.. code-block:: bash

    conda activate cwld 

Once all model and simulation parameters have been specified, the model can be run.

To run the test model, the test_dryp.py have to be used. This contains the path of the model input file, input_test.dmp.

If the model output matches the expected results provided in the /output_test/ folder, the test will result in no assertion errors.

The test can can also be run from the python command line or a python file with the following code:

.. code-block:: python

    from cuwalid.dryp.main_DRYP import run_DRYP

    run_DRYP("test_input/input_test.json")

The location of all file locations must be relative to the location you run the file from. This example has the input in a directory called 'test_input' in the main directory

Model outputs
-------------

The model outputs from the test function should be similar to the figure below:

The figure shows the main hydrological fluxes obtained as a result of the precipitation and potential evapotranspiration used as a forcing dataset.

.. image:: ../fig/test_avg.png

Model results show how average fluxes over the catchment vary in relation to the precipitation (first panel, backline). It is expected that precipitation increases the water content of the soil, but due to evapotranspiration losses, the amount of water available in the soil will be reduced at rates proportional to the available water content.

Rates of actual evapotranspiration vary depending on the availability of water, if there is enough water in the soil, water will be lost at potential rates (first panel blue line). if there is no water available the rate will be zero.

If the soil storage capacity of the soil is reached, water will percolate to the groundwater reservoir and produce recharge (fourth panel), this will in turn increase the water table elevation (bottom panel).


Running a regional model
========================

DRYP was designed to perform hydrological simulations at large or hyper resolution hydrological models, so a version a regional scale model
for the Horn of Africa Dryland region has been developed. This model is still on going further development, however, a first version of this
model is availble at .

Running the large scale model may need additional computation resources to speed up the running process. This model has been set up for HPC server, however,
a short version of the model can be prepared and executed using the DRYP pre-processing tools, assuming that all parameters maps are provided.



.. _dryp_parameters:

Creating a hydrological model from regional datasets
====================================================

Discharge stored in the 'avg' file corresponds to the first row of the coordinate file. Therefore, in
order to close the mass balance of the catchment, the first row of the coordinate file must be the
coordinate of the catchment output.

Finally, an example of input parameter file is shown bellow, user can copy this template to
create a nuew model.

Any values shown as null can be excluded from the json (defaults will be used), this example is just to present all the possible variables that could be used. In addition, variables labelled "required" must be given to run the DRYP model. Any other variables shown to have a value are showing the default parameters that will be used.

.. literalinclude:: ../txt/dryp_input.json
	:language: json
	:linenos:


Simulation parameter file
""""""""""""""""""""""""""

Information about simulation parameters such as period or time step must be provided in a json.
This file contains parameters that control the simulations such as simulation period, format of input
files as well as the activation of model components such as groundwater flow.

*Simulation period*
""""""""""""""""""""

Information related to simulation period should be specified as the initial and final date of the simulation. 
Date must be specified as integers separated by spaces (e.g. 2001 1 9),
zeros on the left side are not allowed (e.g 2001 01 19, will raise an error).

*Simulation time step*
""""""""""""""""""""""

Time has to be specified in minutes, with a maximum time step of one day (1440 min). 
Time step must be an integer, and values must be rational fraction of the hour 
(e.g 20 min is allowed but 25 will stop the simulation) when sub-hourly time step is set. 
In case of hourly time steps, it must be a rational fraction of the day (e.g. 180 min (3h) is
allowed but 300 min (5h) will result in errors). The time step of the groundwater components can not be less
than the surface component.

*Forcing data format*
""""""""""""""""""""""

The format of precipitation, evapotranspiration, vegetation, boundary conditions are shown below respectively:

0. csv file (only one file, that will be applied to the whole model domain)
1. netCDF file, only when one file is provided for the entire simulation period.
2. netCDF files, when yearly files are provided
3. netCDF files, when monthly fiels are provided
4. netCDF files, for DAILY netCDF files
5. netCDF files, for ensamble netCDF files (only for STORM)

The time frequency of the of model should be in minutes as time units. 
Note that it is not the time step of the model, it is only of the forcing dataset.

The model also accept datasets that are not in the model grid projection, or do not
have the same grid size. For those cases, we can specified if each dataset requires
a reprojection and/or interpolation. These options can be activated by changing the
value from 0 to 1 on each of the corresponding dataset values for
reprojection and interpolation, respectively. The order of the reading iptions parameters
is not allowed to change, it will result in errors or even stop the simulation.


The following is an example of the configuration of reading parameters
options.

.. parsed-literal::

    "READING": {
        "data_reading": {
            "pre": 0,
            "pet": 0,
            "abs": 0,
            "kc": 0,
            "flux": 0,
            "savi": 0,
            "savi_min": 0,
            "savi_max": 0
            },
        "data_step": {
            "pre": 60,
            "pet": 60,
            "abs": 60,
            "kc": 60,
            "flux": 60,
            "savi": 60,
            "savi_min": 60,
            "savi_max": 60
            },
        "data_reproject": {
            "pre": true,
            "pet": true,
            "abs": true,
            "kc": true,
            "flux": true,
            "savi": true,
            "savi_min": true,
            "savi_max": true
            },
        "data_interp": {
            "pre": true,
            "pet": true,
            "abs": true,
            "kc": true,
            "flux": true,
            "savi": true,
            "savi_min": true,
            "savi_max": true
            }
    },


Infiltration method selection
""""""""""""""""""""""""""""""""
DRYP has four types of infiltration methods implemented. 
The following codes can be chosen depending on the infiltration approach adopted:

1. Schaake model,
2. Philip's equation,
3. Upscaled Green and Ampt,
4. Modified Green and Ampt method.

Groundwater component selection
"""""""""""""""""""""""""""""""""

For the groundwater component, three different approaches for groundwater flow conditions are available:

0. Constant transmissivity,
1. Variable transmissivity with depth, fully unconfined conditions,
2. Transmissivity function,
3. Multi-aquifer settingd, it will enable the use of multiple aquifer types domains (a file must be provided).


The groundwater components can be activated or disabled, a value of 1 enable the groundwater
component whereas a value of 0 disables it. A value of 2 will activate a two layer groundwater component
(this component is still being tested).

The groundwater approach is specified along with the activation code of the groundwater component as
shown in the example below (not required for the two-layer model):  

.. parsed-literal::
    Run Groundwater - Type: 0-Cons 1-Unc 2-func 3-Multi
    1 1

In case that the approach is not specified, the "variable transmissivity", option 0, is used as default
approach.

Setting storage of model outputs
""""""""""""""""""""""""""""""""

To save model results as netCDF files change the boolean (true/false) under 'OUTPUT'.
Line "output_dt" is used to specify the aggregation
frequency. Frequency should be specified as integer and a string character. Accepted character are D for
days, M for months and Y for years, an example is specified below:

.. parsed-literal::
    "output_grid": true,
    "output_dt": "1H",


Calibration factors
""""""""""""""""""""

A set of parameters that globally modify the model parameters are also specified in the simulation settings
file. Values are scale factors of the following parameters, this values are unitless:


* kdt, for water partitioning of the Shaake infiltration approach,
* kDroot, for rooting depth,
* kAWC, for available water content,
* kKsat for the saturated hydraulic conductivity of the soil,
* kSigma, for the standard deviation of the saturated hydraulic conductivity of the Modified Green and Ampt approach,
* kKch, for infiltration rates in the channel,
* kT for decay parameter of discharge,
* kKaq for aquifer saturated hydraulic conductivity,
* kSy for aquifer specific yield factor,


.. literalinclude:: ../txt/dryp_settings.json
	:language: json
	:linenos:


Projection system file
^^^^^^^^^^^^^^^^^^^^^^^

When datasets are not in the same projection system thatn the model domain (UTM),
a projection settings file should ne provided. It should contain the projection
system of model, and the projection system of each dataset. An example is presented below:


.. literalinclude:: ../txt/example_projection.txt
	:language: none
	:linenos:

Vegetation parameters file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This component is still under development

.. literalinclude:: ../txt/example_vegetation_input.txt
	:language: none
	:linenos:

Overland flow boundary condition file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This component is still under development:

.. literalinclude:: ../txt/example_boundary_conditions.txt
	:language: none
	:linenos:

Store variables settings file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



.. literalinclude:: ../txt/example_store_variables.txt
	:language: none



Prepraring DRYP code
---------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Preprocessing datasets
-----------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Runing DRYP
------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Postprocessing podel outputs
-----------------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Quick mass balance calculation
-------------------------------
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   notebooks/DRYP_water_balance