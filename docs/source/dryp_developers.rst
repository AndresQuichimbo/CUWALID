.. _dryp_developers:

======================================
CUWALID: Workflow for contributions
======================================



DRYP: Model Hydrological Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adding new model components
----------------------------
Entries for the model components are in the DRYP_default_parameters.py
Create new entries in the DRYP_default_settings.py
Add the corresponding new entries into the DRYP_json_reader.py
Create the new model component in the components folder

Add model component into the assemble_model_components.py. 
This will include initializing the component within the initialize_core_hydrology_components function
Create new python objects to the grid environment DRYP_io.py
Add new component to the model main_DRYP
Add new component to the model test_main_DRYP.py
Add new component to the model example_main_DRYP.py
Add new component to the model documentation
Add new component to the model tutorial if applicable


Adding new temporal datasets
----------------------------

Create new entries in the DRYP_default_parameters.py
Create new entries in the DRYP_default_settings.py
Add new entries to the DRYP_json_reader.py
Add new python objects to the grid environment DRYP_io.py
verify which function is the most appropiate to read the datasets
Add new dataset to the model main_DRYP


Adding new raster datasets
--------------------------

Create new entries in the DRYP_default_parameters.py
Add new entries to the DRYP_json_reader.py
Add new python objects to the grid environment DRYP_io.py
Add new dataset to the model main_DRYP

Additing new calibration parameters
------------------------------------

Running test units
^^^^^^^^^^^^^^^^^^^^^^
Test unit functions for reading calibration parameters in
cuwalid/tests/dryp/scripts/test_zone_parameters.py

move to the cuwalid/tests/dryp/
cd cuwalid/tests/dryp/scripts/
and run:
python -m pytest -vv scripts/test_dryp_tilted_V.py