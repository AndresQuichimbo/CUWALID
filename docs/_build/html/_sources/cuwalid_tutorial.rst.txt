
======================
CUWALID Tutorial
======================

Preparing your system for running CUWALID
=========================================

IMPORTANT: GDAL is needed to be able to run the storm, this cannot be added to the package because it does not work with the windows operating system,
you will need to install this yourself, it is recommended if you are using a conda environment you can run this:

.. code-block:: bash

    conda install gdal

IMPORTANT: For running stoPET you need to download some pararmeter files, the system will give you a warning if you try to run it without the files,
The command for downloading these files if using cuwalid as a package is:

.. code-block:: bash

    python -m cuwalid.tools.download_data

or if using cuwalid with downloading from github, you can use this command in the root of the directory:

.. code-block:: bash

    python cuwalid/tools/download_data.py


Running the models
==================

To run the models in CUWALID you can use the code below:

.. code-block:: python

    from cuwalid.main_cuwalid import run_cuwalid

    run_cuwalid("cuwalid_input.json")

Or run from the terminal using this command:

.. code-block:: bash

    # replace "input.json" with the path to your input json
    python -m cuwalid.main_cuwalid cuwalid_input.json

Input for CUWALID
=================

The input of CUWALID is a combined version of all the json files used for the models (e.g. dryp, stopet, storm)
For finding the meaning of each parameter, I would look at the tutorials for each of the models for an example and description.

It will look something like this:

.. literalinclude:: ../txt/cuwalid_input.json
    :language: json
    :linenos:



