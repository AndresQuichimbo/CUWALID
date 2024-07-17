=============================================================================
Installation with GitHub
=============================================================================

This package has been tested on Windows, WSL on Windows and Linux

Cloning the GitHub repository to use CUWALID allows greater control with the code, this installation installs python and all dependencies with conda.

Using the :ref:`PyPi package installation <pypi_installation>` may be more simple if you just plan to run the model as it is.

Follow the steps below to get the model:

1. Clone the GitHub repository and navigate to the main directory (CUWALID) in the terminal:

   .. code-block:: bash

      git clone https://github.com/CornishLeo/CUWALID.git
      cd CUWALID

2. Set up the conda environment:

    Enter into the installers directory and run the cwld_wos.bat file:

    .. code-block:: bash

        cd installers
        # For windows
        cwld_wos.bat

        # For Linux and WSL
        sh cwld_linux.sh

    Wait for the installation to complete and then activate your environment using:

    .. code-block:: bash

        conda activate cwld 

    Exit the installers directory back into the main directory:

    .. code-block:: bash

        cd ..

3. Now you need to run a command to downlaod some of the files that are too large to be stored on github, follow the stops below from the root of the project:

    .. code-block:: bash

        cd cuwalid/tools/
        python download_data.py


4. Test everything has installed properly (Currently only for DRYP model)
   
    First ensure you have your environment activated with the command:

    Then enter the test directory and run the tests using these commands:

    .. code-block:: bash

        cd tests/dryp/
        python run_tests.py

    Once all the tests have completed, the last bit of output should look similair to this:

    .. code-block:: bash

        ************************************************************
        Infiltration approach: Philips
        Run Interception component
        100%|███████████████████████████████████████████████████████████████████████████████| 733/733 [00:21<00:00, 34.04days/s]
        *** SAVING RESULTS ***
        Traceback (most recent call last):
        File "/home/<username>/CUWALID/tests/test_dryp.py", line 24, in <module>
            test_dryp()
        File "/home/<username>/CUWALID/tests/test_dryp.py", line 19, in test_dryp
            assert np.allclose(out, ans)
        AssertionError
        Basin delineation: Test runs successfully

5. Learn how to run the model with an example at `this CUWALID Example <https://github.com/CornishLeo/CUWALID-Example>`_ github repository, or here :ref:`here <tutorial>`.

