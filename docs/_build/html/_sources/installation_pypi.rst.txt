.. _pypi_installation:

==========================
Installation with PyPi
==========================

These steps assume you already have python installed, we recommended python a version between 3.9-3.11. 

If you don't have python yet then you can find the install `here <https://www.python.org/downloads/release/python-3119/>`_, just make sure to tick the box to "Add to path" during your installation to make things easier.

These steps should work correctly even if installing through PyPi within a conda environment, however please note there is a higher change of conflicting dependencies with this method.

1. Open the directory you want to work in and ensure that python is working there by typing the following in you terminal.

    .. code-block:: bash
       
       python --version

    It should print out your python version if everything is working correctly

    Now create a virtual environment (This step is recommended but not technically necessary) by running the following command:

    .. code-block:: bash

        python -m venv test_env
        source test_env/bin/activate  # On Windows use `test_env\Scripts\activate`

    Now your environment is created and is activated

2. Now you can install the package with the command as follows. This should download the latest version of the package.

    Run the command:

    .. code-block:: bash
        
        pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple CUWALID    

    This will install all other dependencies along with the CUWALID package.

3. You can now choose to run some tests first or go on to the next step and just try running the model, to run the test scripts you can use this command:

    .. code-block:: bash
        
        python -m cuwalid.tests.dryp.run_tests

3. Now you can run the model, here is a simple example of what your python file might look like to run the DRYP model.

    .. code-block:: python

        from cuwalid.dryp.main_DRYP import run_DRYP

        run_DRYP("input/input_test.dmp")

    This will use the input files specified at the file path given. Look :ref:`here <dryp_parameters>` to learn more about the input files.