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


# CUWALID — Running `main_cuwalid.py` from the Tutorials Repo (ICPAC example)

This document explains how to run CUWALID using the **tutorial templates** from `AndresQuichimbo/CUWALID-tutorials`, while the `input/` folder lives in a server path such as:

- `/home/example/cuwalid_forecasting/input/`

It also explains the purpose of the key JSON configuration files:
- CUWALID master config (`cuwalid_input_ICPAC.json`)
- stoPET config (`stopet_input_ICPAC.json`)
- DRYP input template (`dryp_input.json`)
- DRYP settings (`dryp_settings_ICPAC.json`)
- Hydro forecasting (HyCast) config** (`forecast_input.json`)
- Impact forecasting (ImCast) config (`impact_forecast_input_ICPAC.json`)

> Important: `main_cuwalid.py` takes **one** command-line argument: the path to the CUWALID master config JSON.

---

## 2. Example folder layout on the server

Assume your server has:

- Your working directory (tutorials repo clone):
  - `/home/example/CUWALID-tutorials/`

- Your forecasting input files (on server home, outside the repo):
  - `/home/example/cuwalid_forecasting/input/`

A recommended layout is:

```text
/home/example/
  CUWALID/                      # (optional) CUWALID source repo, if not installed via pip/conda
  CUWALID-tutorials/
    input_template/
      cuwalid_input_ICPAC.json
      stopet_input_ICPAC.json
      dryp_input.json
      dryp_settings_ICPAC.json
      forecast_input.json
      impact_forecast_input_ICPAC.json
      ...
  cuwalid_forecasting/
    input/
      input_files/
        Ens_Prec_2monLead_MAM_Prob_LogitWVGEnsRegrCPT-avgRaw2025.nc
        Ens_Tref_2monLead_MAM_Raw_2025.nc
      storm_input_ICPAC.json
      stopet_input_ICPAC.json
      dryp_input.json
      dryp_settings_ICPAC.json
      forecast_input.json
      impact_forecast_input.json
      cuwalid_input_ICPAC.json
    output/
      ... (created by CUWALID)
```

Notes:
- CUWALID will create the output structure under `output_dir`.
- In this guide, we use:
  - `output_dir = /home/example/cuwalid_forecasting/output`

---

## 5. Prepare the CUWALID master config JSON (`cuwalid_input_ICPAC.json`)

The master config controls:
- which models run (`run_STORM`, `run_stoPET`, `run_DRYP`, `run_WaterCast`)
- ensemble size (`NSIM`, optional `NSIM_HYDRO`)
- season/year
- where outputs go (`output_dir`)
- where tercile forecast inputs are (`Tercile_Pre_path`, `Tercile_Tem_path`)
- where to find per-model templates under `MODELS`

### Key fields (must be correct)
- `output_dir` **must not be empty**
- `season` is a list, but CUWALID uses `season[0]` internally
- `year`, `NSIM` must be set
- if you want hydro ensemble size different from meteo ensemble size, set `NSIM_HYDRO`

### Example: master config adapted to `/home/example/cuwalid_forecasting`

Create a config file such as:

- `/home/example/cuwalid_forecasting/input/cuwalid_input_ICPAC.json`

Example content:

```json
{
  "run_STORM": true,
  "run_stoPET": true,
  "run_DRYP": true,
  "run_WaterCast": true,

  "sim_in_parallel": true,

  "output_dir": "/home/example/cuwalid_forecasting/output",

  "Tercile_Pre_path": "/home/example/cuwalid_forecasting/input/input_files/Ens_Prec_2monLead_MAM_Prob_LogitWVGEnsRegrCPT-avgRaw2025.nc",
  "Tercile_Tem_path": "/home/example/cuwalid_forecasting/input/input_files/Ens_Tref_2monLead_MAM_Raw_2025.nc",

  "season": ["MAM"],
  "year": 2022,

  "NSIM": 30,
  "NSIM_HYDRO": 30,

  "MODELS": {
    "DRYP": {
      "input": "/home/example/cuwalid_forecasting/input/dryp_input.json",
      "settings": "/home/example/cuwalid_forecasting/input/dryp_settings_ICPAC.json"
    },
    "STORM": {
      "input": "/home/example/cuwalid_forecasting/input/storm_input_ICPAC.json"
    },
    "stoPET": {
      "input": "/home/example/cuwalid_forecasting/input/stopet_input_ICPAC.json"
    },
    "WaterCast": {
      "HyCast": "/home/example/cuwalid_forecasting/input/forecast_input.json",
      "ImCast": "/home/example/cuwalid_forecasting/input/impact_forecast_input.json"
    }
  }
}
```

**Why absolute paths?**
- If you run from the tutorials repo or any other directory, absolute paths prevent “file not found” errors due to relative-path resolution.

---

## 6. What CUWALID overwrites inside the model templates

CUWALID reads the templates you point to and injects run-specific values.

### 6.1 stoPET (`stopet_input_ICPAC.json`)

CUWALID overwrites values such as:
- `outputpath` (to CUWALID PET output folder)
- `temp_path` (to `<output_dir>/temp`)
- `startyear`, `endyear` (to `year`)
- `startdate`, `enddate` (derived from `season` + `year`)
- `number_ensm` (to `NSIM`)
- `seasonName` (to `season[0]`)
- `tercile_forecast_file` (to `Tercile_Tem_path`)

You still need to provide the rest of the stoPET-required settings in the template, like:
- bounding box (`latval_min/max`, `lonval_min/max`)
- `locname`
- `tempAdj`, etc.

---

### 6.2 DRYP input template (`dryp_input.json`)

The DRYP input template is a skeleton containing paths for:
- terrain inputs
- vegetation inputs
- unsaturated/saturated parameters
- meteo forcing (`METEO.path_pre` / `METEO.path_pet`)
- output paths
- plus a pointer to DRYP settings under `OUTPUT.path_setting`

CUWALID will:
- set `dryp_input["OUTPUT"]["path_setting"]` to the path defined in `MODELS.DRYP.settings`
- generate **one DRYP run JSON per ensemble simulation** under:
  - `<output_dir>/<season>_<year>/model/`

and fill in, per simulation:
- `model_name`
- `METEO.path_pre` and `METEO.path_pet` (pointing to the STORM and stoPET forecast NetCDF files produced earlier)
- output paths for that realization
- season start/end dates

---

### 6.3 DRYP settings (`dryp_settings_ICPAC.json`)

The settings JSON controls:
- simulation period
- projection string
- timestep configuration
- reading/interpolation settings
- global calibration factors

Keep these consistent with your dataset and your intended model configuration.

---

## 7. WaterCast: Hydro forecasting (HyCast) and Impact forecasting (ImCast)

When `run_WaterCast` is `true`, `main_cuwalid.py` runs two stages:

1. **HyCast** (hydrological forecasting post-processing over DRYP results)
2. **ImCast** (impact-based products: maps/tables/datasets)

You provide both templates via:

```json
"MODELS": {
  "WaterCast": {
    "HyCast": ".../forecast_input.json",
    "ImCast": ".../impact_forecast_input.json"
  }
}
```

### 7.1 Hydro forecasting template (`forecast_input.json`)

This file controls what HyCast does and which variables it processes.

The tutorial example contains fields like: citeturn2tool0
- run toggles:
  - `run_historical`
  - `run_forecast`
  - `run_plotting`
- `multi_files` (e.g., `true`)
- `historical` block (paths + model name used if historical processing is enabled)
- `forecasting` block (paths + model name used for forecast processing)
- `threshold_path` (where thresholds/netcdfs live)
- `season`, `start_year`, `end_year`, `year`
- `variables` (booleans for which hydro variables to compute/export/plot)

#### What CUWALID overwrites in `forecast_input.json`
Before calling `run_hydro_forecast(...)`, CUWALID injects a new `forecasting` block built from the current run outputs (model name + output directories), and also sets:
- `season`
- `year`
- `nsim` (from `NSIM_HYDRO`)

So your HyCast template should mainly define:
- which operations to run (`run_forecast`, `run_plotting`, etc.)
- thresholds location (if needed)
- the variables list (what to compute/plot)

> Tip: If you want HyCast to actually run, ensure `run_forecast` and/or `run_plotting` are set to `true` in your `forecast_input.json`. The tutorial template has them set to `false` by default. citeturn2tool0

---

### 7.2 Impact forecasting template (`impact_forecast_input_ICPAC.json`)

This template controls impact products (ImCast), such as maps.

Your example includes: citeturn1tool3
- what to create:
  - `create_dataset`
  - `create_table`
  - `create_map`
- what to plot:
  - `plot_scales`
 


