=====================
Developer Maintenance
=====================

This documentation is **purely for the use of the CUWALID Team** to maintain this project and should be **ignored** by users.

-----------------------------
Maintaining the documentation
-----------------------------

The documentation for the code (e.g. the functions and classes) are automatically generated when using sphinx as shown below, other parts of the documentation such as the part you are reading are writting in .rst (reStructuredText) files, these can be found at docs/source.

Within the static folder there are also folders for 'txt' text files or json examples and things that you can include in your documentation. You can find out how to write .rst files `here <https://www.writethedocs.org/guide/writing/reStructuredText/>`_

If you have added code to the documentation you will first need to delete any of the .rst files found in docs/source that are related to the code you changed.

For example if there is a new module in the cuwalid.dryp.components module, you should delete the cuwalid.dryp.components.rst file, or just change the file to include the new module.

If this is not done, you may not see your new changed appear in the documentation, after deleting the necessary files you can run this command from the docs directory in your terminal:

.. code-block:: bash
       
    sphinx-apidoc -o source/ ../cuwalid

Now you can clean and rebuild the html. From the same docs directory, you can now run these 2 commands:

.. code-block:: bash
       
    make clean
    make html

You may see some errors that you should check to make sure they aren't related to the changes you made, but some of the errors won't have much affect on the documentation.

The easiest way to check you changes is to open the newly created html files in a browser (e.g. chrome). The html files are found in docs/_build/html

-------------------------------
Maintaining the package on PyPi
-------------------------------

Useful Tips
^^^^^^^^^^^

1. The setup.py file is for building the package, it contains information like the name of the package, authors, minimum python version, package dependencies and more.

2. The MANIFEST.in file contains files that PyPi might skip over when packaging if you don't specificy to keep it. For example it contains the compiled fortran code for the DRYP model and also data needed to run tests.

3. As you likely know, the README.md is standard for using in github repostitories. But the setup.py file will also use it to display the README.md on the PyPi page for the package.

Releasing a new version
^^^^^^^^^^^^^^^^^^^^^^^

To publish a new version to PyPi you should first check it works on all systems and the documentation on how to instal/use the package is all up to date.

1. First ensure there are no distrubution files already in your root folder. The directories you want to delete are called 'build', 'CUWALID.egg-info' and 'dist'. If this is the first time publishing a new version these files might not exist anyway.

2. Make sure you update the version number in the setup.py file. It will not let you publish to the name version number twice.

3. Now enter the root directory of the project in a terminal (where the README.md and setup.py files are) and activate your environment. You will then want to run these files in order:
    
    .. code-block:: bash
       
        # These command are just precautionary to make sure nothing cached in memory will mess with the changed
        python setup.py clean
        pip cache purge
        # This command packages the files up ready for sending to PyPi
        python setup.py sdist bdist_wheel
        # This command is used to publish to the test PyPi servers and should be changed when the package is released to the main servers.
        twine upload --repository-url https://test.pypi.org/legacy/ dist/* 

    You will be asked to enter your API token for PyPi, if you have not created one yet you will need to login to PyPi's website and create one. This Token should be kept private and shared with no one.

4. Now you should see it uploading the files and then you can check it has all worked correctly by installing the new version in one of your environments with the command:

    .. code-block:: bash

        # Upgrade an existing cuwalid package in the environment
        pip install --upgrade cuwalid
        # Install the package from scratch
        pip install cuwalid

----------------------------------
Creating/Issues with fortran files
----------------------------------

I often ran into issues with fortran files when testing the package, it seems they need to be compiled for each python version. To do this you can follow these steps.

1. First activate an environment with the python version you want to use or are having trouble with, you can create an environment with conda with a specific python version with this command:

    .. code-block:: bash
       
        # This example shows creating a conda environment with Python version 3.9 but you can choose any version.
        conda create -n py39 python=3.9
        # And activate the environment after
        conda activate py39

2. Now you need to navigate to the folder where the fortran files are found, for DRYP you can go to this path:

    .. code-block:: bash

        cd cuwald/dryp/components

3. Now you need to run these 3 commands, this is where it gets tricky because you will need a fortran compiler both installed on your device and found in your systems path. The one i personally got to work on a windows machine was MinGW-w64 version of gfortran. But it might be different on Linux. 

    if you now have a fortran compiler, check you have f2py working by using the command:

    .. code-block:: bash

        # Just check this doesn't give an error that f2py wasnt found
        f2py

    Now we can compile the fortran code using these commands. This example shows the fortran code found in DRYP.

    .. code-block:: bash

        f2py -c DRYP_uz_sz_interaction.f90 -m lakesf90 
        f2py -c TransLoss.f90 -m faccumf90
        f2py -c DRYP_solver.f90 -m gaussf90

4. This has compiled the code into new folders found in the components directories called lakesf90 etc. You will need to pull out the files found inside these folders into the main components directory for them to be found in the code.

Now your fortran code should be working for whatever python version you compiled it for.

-----------------
Package Structure
-----------------

The package structure looks similair to the diagram below:

.. code-block:: bash

    cuwalid/
    ├── dryp/
    │   ├── main_dryp.py
    │   │   └── def run_dryp(input_file):
    │   │       └── ...
    │   └── components/
    │       └── ... 
    ├── storm/
    │   ├── main_storm.py
    │   │   └── def run_storm(input_file):
    │   │       └── ...
    │   └── components/
    │       └── ... 
    ├── stopet/
    │   ├── main_stopet.py
    │   │   └── def run_stopet(input_file):
    │   │       └── ...
    │   └── components/
    │       └── ...
    ├── tools/
    │   └── ... 
    │
    ├── tests/
    │   ├── dryp
    │   │   └── run_tests.py:
    │   ├── storm
    │   │   └── run_tests.py:
    │   └── stopet
    │       └── run_tests.py:
    │
    └── forecasting/
        └── ...

Below is a brief explanation of the structure and how you should go about adding new modules.

* cuwalid:

    The Cuwalid directory is the root of the package, so anything you want users to be able to get from the package should be in there.

* dryp, storm and stopet:

    These directories are for the three main models of the Cuwalid project. They each have a 'main_<name>.py' module which holds a 'run_<name>(input_file)' which will run the model. The components directory holds any other python files necessary for using the model.

* tools:
  
    This directory holds useful python files and functions that are useful for more than one model, or related to the package as a whole.

* tests:

    This directory holds a directory for each model to test it. It can hold test example data as long as its specified in the MANIFEST.in file so it gets included in the package.

* forecasting:

    This directory is one that will hold python files to aid in using the outputs of the models to forecast useful information.
