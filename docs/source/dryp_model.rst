.. _dryp_model:

======================================
DRYP: Dryland Water Partitioning model
======================================

Model description and structure
--------------------------------

The parsimounius water partitioning model is a process-based distributed hydrological model.

.. image:: ../fig/Model_Structure_conceptual_GMD.png


Model Hydrological Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The model uses as input parameter files spatially distributed maps in raster format. If parameter file is not provided, the model will use spatially uniform default values.

A list of parameters required for each component is presented below:

For the **surface component**:

* Digital elevation model (DEM), required (essential).
* River network length (in meters) (values greater than zero are specified as rivers), if not available all cells are considered rivers. Default values is the size of model grids.
* Flow direction in landlab format (ID of receiving node following landlab indexing), if no available, Landlab will automatically find the direction of flow based on the digital elevation model (DEM).
* Model domain, a raster file that can indicating the basin. Default value is 1.0. If not provided, the entire grid will be assumed as the model domain.
* Channel witdth (in meters), default value is 10m.

In case of proving a flow direction file, it should follow Landlab conventions. A comprehensive description of landlab flow direction convention can be found `here <https://landlab.readthedocs.io/en/master/reference/components/flow_director.html>`_. Noted that Landlab grids are labelled from 0 to n, where n is the number of cells (see `here <https://landlab.readthedocs.io/en/master/user_guide/grid.html>`_ and example below).

.. parsed-literal::
    ncols        5
    nrows        4
    xllcorner    574361
    yllcorner    3502989
    cellsize     1000
    NODATA_value  -9999
    15 16 17 18 19
    10 11 12 13 14
    5 6 7 8 9
    0 1 2 3 4

Flow direction raster files must have as values the number of the next downstream cell. If a cell value of the flow direction file has the same value of index, it means that it is a sink point.

For the **subsurface component** the following parameters can be provided, if not availble default values will be used:

* Rooting depth in mm, default value 1000mm
* Wilting Point (wp), default value 0.1
* total available water wilting point (AWC), default value 0.10
* Porosity (n_e), default value 0.40
* Standard deviation of the saturated hydraulic conductivity, $\sigma$
* Infiltration at saturated conditions, ($K_{sat}$) in mm/h, default value 1.0 mm/h
* Water content at residual capacity, $\theta_r$
* Exponent of the water retention function (soil particle distribution), $b$ default value 10.5.
* Suction head, $\psi$, default value 300mm

For the **groundwater component**

* Aquifer saturated hydraulic conductivity, $Ks_{GW}$, default value 1 [m/h]
* Aquifer specific yield, $Ks_{GW}$, default value 0.01 [-]
* Groundwater model domain, optional, in case that groundwater catchment is different than surface catchment.
* Initial water table, default value is specified at 1 meter below the rooting depth.
* Head boundary conditions (optional)
* Flux boundary conditions (optional)
* Streambed elevation, default value is 5m below the surface elevation.

Forcing datasets
^^^^^^^^^^^^^^^^^

DRYP requires time series as model forcing datasets. Precipitation and potential evpotranspiration must be provided
in order to run the model, otherwise it will throw an error. Dataset can be spatially variable data
as netCDF files, or uniform values over the whole model domain by providing a csv file.

Model outputs
^^^^^^^^^^^^^^

Output variables for each model component are summarised below, the name of the variable is in brackets.
Units of time depends on model settings, for example months.


**Surface component**:

* Runoff (run), in mm/month
* Infiltration rate (inf, in mm/month)
* Transmission losses (tls), m3/month
* Streamflow (dis), m3/month
* surface water storage, it includes rivers (ssz), m3/month

**Subsurface and riparian component**:


* Soil and riparian Water content (tht), m3/m3
* Actual evapotranspiration from hillslope and riparian area (aet), mm/month
* Groundwater diffuse (drh) and focused (fch) recharge, mm/month

**Groundwater component**:

* Water table elevation (wte), m.
* groundwater discharge (gdh), m3/month
* capillary evapotranspiration (egw), mm/month
* total water storage deviation (twsc), m/month

.. _dryp_parameters:

Model parameters and setting files
-----------------------------------

Model input files are json, which can be created by using a text editor like notepad or code editor like Visual Studio Code.



Input parameter file
^^^^^^^^^^^^^^^^^^^^^

All filename's parameters must be listed in model parameters file, which is further explained below, However,
if a parameter filename is not provided, the default values will be used as model parameters.

The model is under development therefore some components are still not available (e.g. abstractions and 
irrigation are not yet available).

Meteorological data required as forcing dataset must be provided. Information can be provided in netCDF format
in order to take into account the spatial variability, or it can be a ".csv" file which in turn will assume a uniform rate
over the entire model domain (not common). Filenames of the forcing datasets should follow the format specified
in the paramter setting file (see next section), and it will depend on the numbers of files provided. If there
is only one file, the name of the file can be written directly on the files, but if there are multiple files it
will depend on the frequency. Yearly files must have the month and the year specified as numbers
(e.g. IMERG_2000-02.nc), whereas
yearly files must have only the year specified in numbers (e.g. IMERG-2000.nc). In the input parameter
file, the filename field must contain *YYYY* and/or *MM* for monthly or yearly datas, as it is shon in the
the following examples:

* *forcing/YYYY/MM/IMERG-YYYY-MM.nc* for monthly files,
* *forcing/IMERG-YYYY_final.nc for* yearly files



For the groundwater component, boundary conditions can be specified as head and flux boundary conditions. 
A raster file of head/flux must be provided if boundary conditions are
considered in the model. The raster file will consider a boundary condition any value different that -9999.
If boundary files are not provided, zero flux boundary conditions will be assumed.

To print results at specified locations a file listing the x and y coordinates of the each point must be
provided as input file. This file must have at least one point listed and it must be located inside the
model domain, otherwise an exception error will be raised. More details about the format and specifications
about output files is provided in section \ref{Coutput}

Result at different locations of each model component can be obtained by providing a file containing a
list of coordinates. This should be specified in a comma separated format (e.g. .csv) with column heads
specified as *North* and *East* for the y and x, respectively. If a coordinate is not located
inside the model domain, the simulation will stop.  Note that at least one point coordinate should be
specified, otherwise, an error will be produced.

Coordinate files can be specified under the 'RESULTS AND OUTPUT DIRECTORIES' in the main configuration file:

Point result file are named with the model name followed by aletter p and the name of the variable at the end.

Model variable name's and codes stored for point result files, for filename see table

Surface component

* dis,    Discharge
* tls,      Transmission losses
* inf,     infiltration excess


Unsaturated zone

* tht,      soil moisture
* aet,    actual evapotranspiration
* rch,    recharge, diffuse and foccused recharge

Saturated zone

* wte, water table elevation

Point result files are time series with the first column specified as time with head 'Date'. The number
of columns of result files depend on the number of points specified in the coordinate files defined above.
Columns are label depending on the component and variable (see \ref{tab:point_files}) followed by number
starting by zero (e.g. for discharge, the file model_name_p_dis.csv will contain the following columns,
Date' for time and 'dis_0', 'dis_1', .. etc. for discharge values) 


DRYP automatically save spatially averaged fluxes and water content of model compartments. The name of
the this result file has the suffix \texttt{avg} and the end. Results are saved at time steps specified
for the surface component.

Average results are saved in a comma separated file that can be opened in microsoft excel or any text
editor. The document contains the following information which is specified by codes for each variable
in the first line:

* pre,     precipitation,
* pet, potentiial evapotranspiration
* rch,     recharge,
* dis,     discharge,
* aet,     actual evapotranspiration,
* tht,     soil water content,
* twsc,     groundwater storage,
* egw, capillary evaporation
* bc, flux at boundary condition
* tls, transmission losses

Discharge stored in the 'avg' file corresponds to the first row of the coordinate file. Therefore, in
order to close the mass balance of the catchment, the first row of the coordinate file must be the
coordinate of the catchment output.

Finally, an example of input parameter file is shown bellow, user can copy this template to
create a nuew model.

.. literalinclude:: ../txt/example_input.json
	:language: json
	:linenos:

Simulation settings file
^^^^^^^^^^^^^^^^^^^^^^^^^

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

1. csv file (only one file, that will be applied to the whole model domain)
2. netCDF file, only when one file is provided for the entire simulation period.
3. netCDF files, when yearly files are provided
4. netCDF fiels, when monthly fiels are provided

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

    {
        "READING OPTIONS: PRE-PET-ABS-Kc-SAVI-FLUX": {
            "Read datasets: 0-csv 1-One-netCDF 2-Multi-netCDF": "0 0 0 0 0 0 0 0",
            "Dataset time step (minutes)": "60 60 60 60 60 60 60 60",
            "Reproject datasets: 0- disable 1- enable": "0 0 0 0 0 0 0 0",
            "Interpolate datasets: 0- disable 1- enable": "0 0 0 0 0 0 0 0"
        }
    }


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

To save model results as netCDF files change the boolean (true/false) under 'OUTPUT OPTIONS'.
Line "Temporal aggregation results (eg. 3M Y H)" is used to specify the aggregation
frequency. Frequency should be specified as integer and a string character. Accepted character are D for
days, M for months and Y for years, an example is specified below:

.. parsed-literal::
    "Save state results in netcf files": true,
    "Temporal aggregation results (eg. 3M Y H)": "1H",


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


.. literalinclude:: ../txt/example_par_setting.json
	:language: json
	:linenos:

Riparian zone parameter files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../txt/example_riparian_inputs.txt
	:language: none
	:linenos:

Groudwater parameter file
^^^^^^^^^^^^^^^^^^^^^^^^^^

The groundwater parameter file should be specified when the model uses
multi-aquifer and a transmisivity function. If lakes is considered in
the model, a file, indicating the bathymetry should be provided. An example
of groundwater paramter file is provided below:


.. literalinclude:: ../txt/example_GW_parameters.txt
	:language: none
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
