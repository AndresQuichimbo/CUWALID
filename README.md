# CUWALID
Repository containing the models of CUWALID under the Down2Earth project

These instructions are not currently up to date whilst testing the package, for the most up to date installation instructions, please use the html webpages found in `docs/_build/html/index.html`.

## Installation with PyPi

These steps assume you already have Python installed; we recommend a version between 3.9-3.11. 

If you don't have Python yet, you can find the install [here](https://www.python.org/downloads/release/python-3119/), just make sure to tick the box to "Add to path" during your installation to make things easier.

Alternatively, using Anaconda to create an environment with a specific Python version also works.

These steps should work correctly even if installing through PyPi within a conda environment, however, please note there is a higher chance of conflicting dependencies with this method.

1. Open the directory you want to work in and ensure that Python is working there by typing the following in your terminal.

    ```bash
    python --version
    ```

    It should print out your Python version if everything is working correctly.

    Now create a virtual environment (This step is recommended but not technically necessary) by running the following command:

    ```bash
    python -m venv test_env
    source test_env/bin/activate  # On Windows use `test_env\Scripts\activate`
    ```

    Now your environment is created and is activated.

2. Now you can install the package with the command as follows. This should download the latest version of the package.

    Run the command:

    ```bash
    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple CUWALID    
    ```

    This will install all other dependencies along with the CUWALID package.

    Some of the parameter files for the StoPET model are too large to be installed with the package, so use the command below after installing the package if you want to use the StoPET model:

    ```bash
    python -m cuwalid.tools.download_data
    ```

3. You can now choose to run some tests first or go on to the next step and just try running the model. To run the test scripts, you can use this command:

    ```bash
    python -m cuwalid.tests.dryp.run_tests
    python -m cuwalid.tests.stopet.run_tests
    ```

4. Now you can run the model. Here is a link to a GitHub repository with an example of using the CUWALID models for you to use:

    [CUWALID Example](https://github.com/CornishLeo/CUWALID-Example)

    This will use the input files specified at the file path given. Look [here](#dryp_parameters) to learn more about the input files.
