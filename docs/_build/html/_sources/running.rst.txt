.. _running:

Running the model
=============================================================================

Currently only the DRYP model is available for use

Running DRYP Model
-----------------------------------------------------------------------------

A file called run_dryp.py is included in the GitHub repository which can provide a file to quickly get up and running with the model

Before you run the model, it is recommended to follow the steps for installation
:ref:`found here <installation_steps>` and activate the conda environments created for you in the instillation using this command:

.. code-block:: bash

    conda activate cwld 

Within the run_dryp.py file found in the main directory contains a small amound of code showing how the DRYP model can be imported and ran. The code is as follows below:

.. code-block:: python

    from models.DRYP.dryp.main_DRYP import run_DRYP

    run_DRYP("test_input/input_test.dmp")

In this code it shows the input_test.dmp file is found with in the test_input directory. 
The example files are all provided in this directory for you to modify or replace, more information on the details of parameters and creating the DRYP inputs can be
:ref:`found here <dryp_parameters>`.