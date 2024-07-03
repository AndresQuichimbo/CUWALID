.. _dryp_parameters:

DRYP Parameters
=============================================================================

A list of parameters required for each component is presented below:

**Surface component:**
 
- Digital elevation model (DEM), required
- River network (values greater than zero are considered as river), if not available all cells are considered rivers
- Flow direction in landlab format (ID of receiving node following landlab indexing), if not available, Landlab will automatically find the direction of flow based on the DEM.
- Drainage area, it can be specified as the model domain for the catchment. Default value is 1.0.

**Subsurface component:**

- Rooting depth in mm, default value 1000mm
- Wilting Point (θwp), default value 0.1
- Field capacity (θfc), default value 0.15
- Porosity, ne, default value 0.35
- Standard deviation of the saturated hydraulic conductivity, σ
- Infiltration at saturated conditions, (Ksat) in mm/h
- Water content at residual capacity, θr
- Exponent of the water retention function, b default value 2.
- Suction head, ψ, default value 300mm

**Groundwater component:**
 
- Aquifer saturated hydraulic conductivity, KsGW, default value 1 [m/h]
- Aquifer specific yield, KsGW, default value 0.01 [-]
- Groundwater model domain, optional, in case that groundwater catchment is different than surface catchment.
- Initial water table, default value is specified at 1 meter below the rooting depth.
- Head boundary conditions
- Flux boundary conditions
- Bottom stream bed elevation, default value: z - 5m


Parameters can be provided as numerical values or as maps. When maps are provided, they must be raster files. An example of the raster format for a 3 x 3 grid size map is shown below.

.. code-block:: text

   ncols 3
   nrows 3
   xllcorner 574361
   yllcorner 3502989
   cellsize 1000
   NODATA_value -99999
   3
   825.233 860.3439 864.650
   825.233 860.3439 864.650
   825.233 860.3439 -99999


Maps specifying boundary conditions must have as nodata values -9999, any other value will be assumed as boundary conditions.

Filenames of parameters required for the model must be included in the input file. If a filename is not provided, default values will be considered. The input file must be a plain text file. This file must start with ‘drylandmodel’ in the first line (see example below), omitting the first line will stop the simulation. 

Filenames provided in the input file must be written in each line specified in the example, changes will result in simulation errors or wrong variables being read (e.g. if the file ‘GW 1D dem m.asc’ is written in line 5, python will raise an exception error).

**input file**

.. code-block:: text

   1 drylandmodel
   2 Model name --------------------------------------(1):
   3 test
   4 ================ TERRAIN COMPONENTS =================
   5 Topography (DEM)---------------------------------(4):
   6 test/input/test_dem_m.asc
   7 Cell factor area --------------------------------(6):
   8 test/input/test_area_m.asc
   9 Flow Direction (fd)------------------------------(8):
   10 test/input/test_flowdir_m.asc
   11 Boundary conditions (check CHB) ----------------(10):
   12 test/input/test_chb.asc
   13 Basin Mask (catchment) -------------------------(12):
   14 test/input/test_mask_m.asc
   15 River length -----------------------------------(14):
   16 test/input/test_riv_m.asc
   17 River width ------------------------------------(16):
   18 none
   19 River bottom elevation -------------------------(18):
   20 none
   21 ================ SURFACE COMPONENTS =================
   22 Vegetation type Kc -----------------------------(21):
   23 none
   24 Soil land use ----------------------------------(23):
   25 none
   26 Other ------------------------------------------(25):
   27 none
   28 =========== SOIL AND SUBSURFACE PARAMETERS ==========
   29 Soil porosity: porosity ------------------------(28):
   30 test/input/test_rawls_ne.txt
   31 Theta residual ---------------------------------(30):
   32 test/input/test_rawls_theta_r.txt
   33 Available Water content (AWC) ------------------(32):
   34 test/input/test_rawls_awc.txt
   35 Wilting Point (wp) -----------------------------(34):
   36 test/input/test_rawls_wp.txt
   37 Soil Depth (D) ---------------------------------(36):
   38 test/input/test_depth_m.asc
   39 Soil particle distribution parameter (b) -------(38):
   40 test/input/test_rawls_n.txt
   41 Soil suction head ------------------------------(40):
   42 test/input/test_rawls_phi.txt
   43 Saturated hydraulic conductivity ---------------(42):
   44 test/input/test_rawls_ks.txt
   45 sigma_Ksat -------------------------------------(44):
   46 test/input/test_rawls_sigma_ks.txt
   47 Initial soil water content ---------------------(46):
   48 none
   49 Other ------------------------------------------(48):
   50 none
   51 === GROUNDWATER PARAMETER AND BOUNDARY CONDITIONS ===
   52 Groundwater Boundary condition (domain) --------(51):
   53 test/input/test_mask_m.asc
   54 Aquifer Sat. Hydraulic Conductivity (Ksat_aq) --(53):
   55 test/input/test_rawls_ks1.txt
   56 Specific Yield----------------------------------(55):
   57 none
   58 Initial Conditions Water table elevation -------(57):
   59 test/input/test_wte_ini.asc
   60 Flux Boundary Conditions -----------------------(59):
   61 None
   62 Head Boundary Conditions -----------------------(61):
   63 test/input/test_CHB1.asc
   64 Other-------------------------------------------(63):
   65 none
   66 ============== METEOROLOGICAL DATA ==================
   67 Precipitation ----------------------------------(66):
   68 test/input/Pre_60m_00_05_10_sin.csv
   69 Potential Evapotranspiration -------------------(68):
   70 test/input/Pre_60m_p00_e00.csv
   71 Water abstractions file ------------------------(70):
   72 none
   73 Other ------------------------------------------(72):
   74 none
   75 ======== RESULTS AND OUTPUT DIRECTORIES =============
   76 Discharge point results ------------------------(75):
   77 test/input/test_Flumes_points.csv
   78 Soil point results output ----------------------(77):
   79 test/input/test_SM_points.csv
   80 Groundwater point results ----------------------(79):
   81 test/input/test_well_point_m.csv
   82 Folder location results ------------------------(81):
   83 test/output
   84 Other ------------------------------------------(83):
   85 none
   86 Other ------------------------------------------(85):
   87 none
   88 MODEL PARAMETER SETTINGS FILE ------------------(87):
   89 test/setting_test.dmp

If information related anthropogenic interactions such as water abstractions and irrigation are available, it must be provided in line 72. Information can be provided in netCDF format in order to take into account the spatial variability, if a CSV file is provided a uniform rate will be applied over the entire model domain. Additionally, information must be specified with the following codes:

**Table 1: Code and Name of variables for input datasets of anthropogenic fluxes**

.. list-table::
   :header-rows: 1

   * - Code
     - Variable
   * - ASW
     - Surface component: River abstractions
   * - AUZ
     - Unsaturated component: Irrigation
   * - ASZ
     - Saturated component: Groundwater abstractions

For the groundwater component, boundary conditions have to be specified as head boundary and flux boundary conditions in lines 61 and 63, respectively. A raster file of head/flux must be provided if boundary conditions are considered in the model. The raster file must have as non boundary condition values of -9999, otherwise it will be assumed as head/flux condition. If no file is provided, zero flux boundary conditions will be assumed.

Additionally, a simulation settings file must also be provided. This file should contain parameters that control the simulations such as simulation period, format of input files as well as the activation of model components such as groundwater flow.

Simulation settings file is a plain text document file, which has to include in the first line the following text ‘DWAPM SET’, as it is shown in the example below, omitting the first line will stop the simulation. Lines with numerical values are allowed to change, but they can not be displaced by adding a new line. The change of position of lines will result in errors or will stop the simulation.

**simulation setting file**

.. code-block:: text

   1 DWAPM_SET
   2 ======== SIMULATION PERIOD AND TIME STEP ==========
   3 Initial date for simulation (YYYY MM DD) ........(2)
   4 2000 1 1
   5 Initial date for simulation (YYYY MM DD) ........(4)
   6 2004 1 3
   7 OF Time step - dt_Pre (min) - (1440 for daily)...(8)
   8 60
   9 UZ Time step - dt_Pre (min) - (1440 for daily)..(10)
   10 60
   11 SZ Time step - dt_Pre (min) - (1440 for daily)..(12)
   12 60
   13 ============ MODEL READING OPTIONS ================
   14 Read Precipitation from NETCF file..............(13)
   15 0 60
   16 Read Evapotranspiration from NETCF file.........(15)
   17 0 60
   18 Read Abstractions from NETCF file ..............(17)
   19 0
   20 ============== MODEL COMPONENTS ===================
   21 Inf.- 0: Scheeke 1: Philips 2: Up_GA 3: Mod_GA..(20)
   22 1
   23 Run surface routing ----------------------------(22)
   24 0
   25 Run Groundwater-Enable Type: 0-Unc 1-func 2-Con-(26)
   26 1 1
   27 Run OF linear reservoir: 1 active 0 disable.....(26)
   28 0
   29 Run UZ linear reservoir: 1 active 0 disable.....(28)
   30 0
   31 =============== OUTPUT OPTIONS ====================
   32 Show simulation times 1 active 0 disable .......(31)
   33 0
   34 Save state results in netcf files...............(33)
   35 1
   36 Temporal aggregation results (eg. 3M Y H).......(35)
   37 6M
   38 Plot maps at the end of the period.............(37)
   39 0
   40 Save maps as raster at the end of the period....(39)
   41 0
   42 Print daily maps................................(41)
   43 0
   44 Print simulation time...........................(43)
   45 0
   46 ============= MODEL PARAMETERS FACTORS ============
   47 Runoff partition parameter (kdt-Sheeke).........(46)
   48 1.0
   49 Soil Depth factor - kDroot (mm) ................(48)
   50 1.0
   51 Available Water Content factor - kAWC ..........(50)
   52 1.0
   53 Infiltration rate factor - kKsat ...............(52)
   54 0.004
   55 Heterogeneity factor - k_sigma - (Upscaled GA)..(54)
   56 1.0
   57 Transmission losses - Kch (m/h) ................(56)
   58 10.52967
   59 Decay discharge - T - (hours)...................(58)
   60 0.1512967
   61 Channel width parameter (pe-not activated)......(60)
   62 1
   63 Aquifer saturated hydraulic conductivity........(62)
   64 1.250
   65 Aquifer specific yield factor...................(64)
   66 1.00

Information related to simulation period should be specified as the initial and final date of the simulation and must be specified in lines 4 and 6. Date must be specified as integers separated by spaces (e.g. 2001 1 9), zero on the left side is not allowed and will stop the simulation (e.g 2001 01 19, will raise an error). 

Simulation time step of the surface component must be specified in line 10. Time has to be specified in minutes, with a maximum time step of one day. Time step must be an integer, and values must be a rational fraction of the hour (e.g 20 min is allowed but 25 will stop the simulation) when sub-hourly time step is set. In case of hourly time steps, it must be a rational fraction of the day (e.g. 180 min (3h) is allowed but 300 min (5h) will result in errors).

For groundwater component, the simulation time step must be specified on line 12. Time step has to be an integer value, and should be specified in hours.

The format of precipitation/evapotranspiration and water abstraction files must be specified in lines 15, 17 and 19, respectively, A value of 1 represent grids in netcdf format, whereas a value of zero represent comma-separated formats. Time frequency of model input files should be specified along with the file format parameter. Time frequency should be specified in minutes (see example below). If frequency is not provided, DRYP will assume a default value of 60 min.

.. code-block:: text

   13 ============ MODEL READING OPTIONS ================
   14 Read Precipitation from NETCF file..............(15)
   15 0 60
   16 Read Evapotranspiration from NETCF file.........(17)
   17 0 720
   18 Other...........................................(19)
   19 0 60

DRYP has four types of infiltration methods implemented which have to be specified in line 22. The following codes can be chosen depending on the infiltration approach adopted:

0. Schaake model
1. Philip’s equation
2. Upscaled Green and Ampt
3. Modified Green and Ampt method

For groundwater, three different approaches for running the groundwater component have been added to DRYP:

0. Variable transmissivity, fully unconfined conditions
1. Constant transmissivity
2. Transmissivity function

The groundwater components can be activated or disabled in line 26, a value of 1 enable the groundwater component whereas a value of 0 disables it. The groundwater approach is specified along with the activation code of the groundwater component as shown in the example below:

.. code-block:: text

   25 Run Groundwater-Enable Type: 0-Unc 1-func 2-Con-(26)
   26 1 1

In case that the approach is not specified, the ”variable transmissivity”, option 0, is used as default approach.

Line 27 is currently disabled.

To save model results as netCDF files, lines 33 and 35 needs to be modified. A value of 1 in line 33 will activate the option save, whereas line 35 is used to specify the aggregation frequency. Frequency should be specified as integer and a string character. Accepted characters are D for days, M for months and Y for years, an example is specified below:

.. code-block:: text

   32 Save state results in netcf files...............(33)
   33 1
   34 Temporal aggregation results (eg. 3M Y H).......(35)
   35 6M

A set of parameters that globally modify the model parameters are also specified in the simulation settings file. Values are scale factors of the following parameters:

- line 48: kdt, for water partitioning of the Shaake infiltration approach,
- line 50: kDroot, for rooting depth,
- line 52: kAWC, for available water content,
- line 54: kKsat for the saturated hydraulic conductivity of the soil,
- line 56: kSigma, for the standard deviation of the saturated hydraulic conductivity of the Modified Green and Ampt approach,
- line 58: kKch, for infiltration rates in the channel,
- line 60: kT for decay parameter of discharge,
- line 62: kKaq for aquifer saturated hydraulic conductivity,
- line 64: kSy for aquifer specific yield factor
