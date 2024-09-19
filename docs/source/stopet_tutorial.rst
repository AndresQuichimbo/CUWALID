======================
StoPET Tutorial
======================

Running the model
=================

To run the StoPET model you can run the command below:

.. code-block:: python

    from cuwalid.stopet.main_stoPET import run_stoPET

    run_stoPET("input.json")

Or run from the terminal using this command:

.. code-block:: bash

    # replace "input.json" with the path to your input json
    python -m cuwalid.stopet.main_stoPET input.json


Input Parameters
================

The input JSON shown above will look something like this:

.. literalinclude:: ../txt/stopet_input.json
    :language: json
    :linenos:

Here is an explanation of what each parameter does:

- **data_path**: `"stopet_parameters"`
  
  The path to the input data parameters.

- **output_path**: `"stopet_output"`
  
  The path where output data will be saved.

- **runtype**: `"regional"`
  
  The type of run for the model. Options might include regional or other types.

- **startyear**: `1994`
  
  The start year for the model simulation.

- **endyear**: `1996`
  
  The end year for the model simulation.

- **latval**: `3.8`
  
  Latitude value for the location of interest.

- **lonval**: `36.6`
  
  Longitude value for the location of interest.

- **latval_min**: `-5.5`
  
  Minimum latitude for the region of interest.

- **latval_max**: `-4.5`
  
  Maximum latitude for the region of interest.

- **lonval_min**: `33.0`
  
  Minimum longitude for the region of interest.

- **lonval_max**: `34.5`
  
  Maximum longitude for the region of interest.

- **locname**: `"Kenya"`
  
  Name of the location.

- **number_ensm**: `2`
  
  Number of ensemble members used in the simulation.

- **tempAdj**: `3`
  
  Temperature adjustment parameter.

- **deltat**: `1.5`
  
  Time step parameter.

- **udpi_pet**: `5`
  
  UDPI PET (Potential Evapotranspiration) parameter.
