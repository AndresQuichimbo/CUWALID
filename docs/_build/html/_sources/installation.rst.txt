.. _installation_steps:

=============================================================================
Installation
=============================================================================

Installing on windows
-----------------------------------------------------------------------------

On windows there are two approaches to installing, the first is using the standard WOS (Windows Operating System) or with WSL (Windows Subsystem for Linux)

Currently the best way to install the CUWALID project is through cloning the GitHub repository.

Follow the steps below to get the model:

1. Clone the GitHub repository and navigate to the main directory (CUWALID) in the terminal:

   .. code-block:: bash

      git clone https://github.com/CornishLeo/CUWALID.git
      cd CUWALID

2. Set up the conda environment:

    Enter into the installers directory and run the cwld_wos.bat file:

    .. code-block:: bash

        cd installers
        cwld_wos.bat

    Wait for the installation to complete and then activate your environment using:

    .. code-block:: bash

        conda activate cwld 

    Exit the installers directory back into the main directory:

    .. code-block:: bash

        cd ..

3. Test everything has installed properly (Currently only for DRYP model)
   
    First ensure you have your environment activated with the command:

    .. code-block:: bash

        conda activate cwld 


    Then enter the test directory and run the tests using these commands:

    .. code-block:: bash

        cd tests/dryp/
        run_all_test.bat

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

4. Learn how to run the model :ref:`here <tutorial>`.



Installing on Linux or WSL
-----------------------------------------------------------------------------

WSL (Windows Subsystem for Linux)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Windows WSL (Windows Subsystem for Linux) is a way you can create a linux like environment on your windows machine.

Follow the instructions `here <https://docs.microsoft.com/en-us/windows/wsl/install>`_ to download WSL and get it setup if you do not already have it installed.

After it has been installed you should be able to run a Linux like terminal by accessing the WSL app on your windows device (it should appear if you type 'WSL' in your search bar below)

Keep in mind that the WSL environment runs seperately from your regular machine and has different locations for files.

Linux
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Clone the GitHub repository and navigate to the main directory (CUWALID) in the terminal:

   .. code-block:: bash

      git clone https://github.com/CornishLeo/CUWALID.git
      cd CUWALID

2. Set up the conda environment:

    Enter into the installers directory and run the cwld_wos.bat file:

    .. code-block:: bash

        cd installers
        sh cwld_linux.sh

    Wait for the installation to complete and then activate your environment using:

    .. code-block:: bash

        conda activate cwld 

    Exit the installers directory back into the main directory:

    .. code-block:: bash

        cd ..

3. Test everything has installed properly (Currently only for DRYP model)
   
    First ensure you have your environment activated with the command:

    .. code-block:: bash

        conda activate cwld 


    Then enter the test directory and run the tests using these commands:

    .. code-block:: bash

        cd tests/dryp/
        sh run_all_test.sh

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

6. Learn how to run the model :ref:`here <tutorial>`.

