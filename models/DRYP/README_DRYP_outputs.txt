ReadMe

This file describes the output data from DRYP model
There are three main files that DRYP produce:
gridded dataset: netcdf files with all model variables
raster files: for initial conditions, and are the
soil moiture and the water table elevation.
text files (comma delimited): these are for point and
    average model results.

Model outputs are the results of the calibration,
therefore, a calibration factor must be applied when
changing water content to water depth, as well as
when changing aquifer thickness to total water storage
of the aquifer. Those factors are specific for the
simulation so they can not be used in other simulations
dataset. Factors are provided for each variable.

NetCDF file contain the following variables:
CODE: variable name
pre: precipitation [mm]
pet: potential evapotranspiration [mm]
aet: actual evapotranspiration [mm]
inf: infiltration [mm]
tls: transmission losses [mm]
fch: focused recharge [mm]
dch: diffuse recharge [mm]
wte: water table elevation [m]
run: runoff [m3]
gdh: groundwater discharge [m3]
tht: water contet [m3/m3]

The catchment values are not mask, so an additional
file must be used to select the catchment.
For Kenyan basin the following file can be used:
"EW_1k_mask_m.asc"

To change water content [m3/m3] to water depth [mm],
the water content (tht) should be multiplied by the
soil depth.
For the Kenya basin, the following file can be used:
"EW_1k_depth_m.asc"
The factor 1.2607 must be applied to the soil depth

To change aquifer saturated thickness to depth (storage
depth), the aquifer saturated thickenss must be
multiplied by the aquifer specific yield.

For the Kenya basin, the following file can be used:
"EW_1k_Sy_aq.txt"
The factor 0.11163 must be applied to the specific yield

Change in Total water storage can be estimated directly
using the precipitation (pre), the actual evcpotranspiration
(aet), and runoff (run) (the last need to be changed to
water depth.

Change in Total groundwater water storage (dTGWS) is not
estimated by the model, however, it can be estimated by
applying the folowing equation:
dTGWS = (h_t - h_t0)*Sy*factor
where:
h_t: is the water table at time t,
h_t0: is the water table at time t0, 
Sy: is the aquifer specific yield, and
factor: calibration factor especified above

