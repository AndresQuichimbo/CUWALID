.. _pypi_installation:

==========================
Installation with PyPi
==========================

These steps assume you already have python installed, we recommended python a version between 3.9-3.11. 

If you don't have python yet then you can find the install `here <https://www.python.org/downloads/release/python-3119/>`_, just make sure to tick the box to "Add to path" during your installation to make things easier.

Or using Anaconda to create an environment with a specific python version also works (shown below).

These steps should work correctly even if installing through PyPi within a conda environment, however please note there is a higher change of conflicting dependencies with this method.

1. Open the directory you want to work in and ensure that python or anaconda is working there.

    Now it is recommended to create a virtual environment by running the following command (Using conda as shown will make this process easier):

    .. code-block:: bash

        # For creating a conda environment with the name "test_env":
        conda create --name test_env python=3.11 -y
        conda activate test_env


    Now your environment is created and is activated

2. Now you can install the package with the command as follows. This should download the latest version of the package.

    Run the command:

    .. code-block:: bash
        
        # This is currently only on the test version of PyPi, this will need to be changed when fully released
        pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple CUWALID    

    This will install all other dependencies along with the CUWALID package.

    If you need to update the package to the newest version of CUWALID, please use the command below:

    .. code-block:: bash
        
        # This is currently only on the test version of PyPi, this will need to be changed when fully released
        pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple CUWALID --upgrade

    For using storm you will need gdal installed, the easiest way to do this is by installing it using conda (not pip, however it can be done through pip if you follow some extra steps which you can find online)

    .. code-block:: bash
        
        conda install gdal "numpy<2.0" # It is important to include this numpy version for gdal to work correctly for storm


3. You can now choose to run some tests first (may take some time, but if they start running you can stop early as that means cuwalid has been installed correctly):

    To run the whole cuwalid system go see the tutorial :ref:`here <cuwalid_tutorial>` and use the example github repository `CUWALID Example <https://github.com/CornishLeo/CUWALID-Example>`_ to get some example inputs:

    .. code-block:: bash
        
        python -m cuwalid.tests.dryp.run_tests
        python -m cuwalid.tests.stopet.run_tests
_
