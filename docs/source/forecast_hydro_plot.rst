===========================
Forecast Hydrological Tutorial
===========================

Running the model
=================


Plotting hydrological forecast is done by running this command in the terminal:

.. code-block:: bash

    # replace "input.json" with the path to your input json
    python -m cuwalid.forecasting.main_hydro_forecast input.json

Or you can import the function into your code like this:

.. code-block:: python

    from cuwalid.forecasting.main_hydro_forecast import run_hydro_forecast

    # replace "input.json" with the path to your input json
    plot_maps_json("input.json")


If you would prefer to not use a json input you can use:

.. code-block:: python

    from cuwalid.forecasting.main_hydro_forecast import call_plot_maps

    # replace parameters with the necessary parameters
    call_plot_maps(parameters)


Input Parameters
================

The input JSON shown above will look something like this:

.. literalinclude:: ../txt/forecast_plot_input.json
    :language: json
    :linenos:

Any parameters shown within a list will be iterated over and create a map for each, for example with 'place_names' there are three locatations ["Samburu", "Laikipia", "Meru"], In the output you will find a different output for each place,


Here is an explanation of what each parameter does:

- **plot_scales**: A list that defines the geographical scale at which the plot will be made. Examples include "County" or "Zoom".
  
- **country**: Specifies the name of the country for which the forecast will be generated. In this example, it is set to "Kenya".

- **place_names**: A list of specific places (regions, counties, etc.) within the country where the forecast will focus. For example, ["Samburu", "Laikipia", "Meru"].

- **seasons**: Specifies the season for which the forecast is being generated. Common abbreviations like "OND" (October-November-December) or "MAM" (March-April-May) are used.

- **water_status**: Indicates the type of water-related event being forecasted. For instance, "Flood" in this example.

- **year**: The specific year for which the forecast is being created. In this case, the year is set to 2022.

- **language**: Defines the language of the output, such as "English". The output can be translated into other languages based on this parameter.

- **output_dir**: Specifies the directory where the output files (maps, data, etc.) will be saved. In this case, the folder is called "output".

- **netcdf_path**: The path to the NetCDF file that contains the forecasting dataset. This file stores large-scale gridded forecast data, typically in .nc format. Where the year is specified in your file name please replace it with 'YYYY', this will be replaced by the year you specified above. You can see how this is done in the example above.

- **threshold_path**: Specifies the path to the threshold data used for post-processing of the forecast. Thresholds are used to define critical values for forecasting events like floods. In your file name for this file, please replace your season with 'SSS', this will be replaced by the seasons you entered above. In addition please leave out the '_flow_quantiles.nc' and '_quantiles.nc', these will be added in the script. You can see an example of this in the examplea above.

- **mask_path**: The path to the mask file, which defines the areas where the forecast is applied. It typically filters or limits data to the region of interest.

- **river_path**: Path to the river network data file, which is used to model the river system within the forecast region. It helps in determining river lengths and other hydrological features.
