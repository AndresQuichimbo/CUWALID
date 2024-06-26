# CUWALID
Repository containing the models of CUWALID under the Down2Earth project

## TESTING

You can test if your environment is working correctly with the model by using the 'run_all_test.sh' script in your linux terminal or on windows you can use the command prompt or WSL (THIS TEST CURRENTLY ONLY TESTS THE DRYP MODEL)

### Steps:

1. Navigate to the current directory (CUWALID) in terminal
2. Activate your environment
```
conda activate cwld
```
2. enter tests/dryp directory
```
cd tests/dryp/
```
3. run the tests script
```
sh run_all_test.sh
```
You should see the tests being run, some minor warnings may appear but should be safe to ignore,

The end of the output should look like this:
```
************************************************************
Infiltration approach: Philips
Run Interception component
100%|███████████████████████████████████████████████████████████████████████████████| 733/733 [00:21<00:00, 34.04days/s]
*** SAVING RESULTS ***
Traceback (most recent call last):
  File "/home/cornish_leo/CUWALID/CUWALID/CUWALID_Complete/tests/test_dryp.py", line 24, in <module>
    test_dryp()
  File "/home/cornish_leo/CUWALID/CUWALID/CUWALID_Complete/tests/test_dryp.py", line 19, in test_dryp
    assert np.allclose(out, ans)
AssertionError
Basin delineation: Test runs successfully
```

## Setting up the environments

Within the main directory there is a directory called installers, this contains some scripts to easily set up the environments you need to run the model

### Steps:
1. Enter your linux terminal or command prompt
2. Navigate to the main directory
3. cd into the installers directory
```
cd installers
```
4. Enter on of the commands below to install conda and create the environment
- If on Linux use this command:
```
sh cwld_linux.sh
```
- If using the windows command prompt use:
```
cwld_wos.bat
```
5. You should now see the instilation begin, please wait until complete,

After instilation you should be able to access the main environment by running the command:
```
conda activate cwld
```


## Running the model

Currently only the DRYP model is correctly working, the python file 'run_DRYP.py' should run an example by using the example file 'input_test.dmp' in the DRYP_Input/ folder and uses other test files found in the directory at DRYPv2/example/input/

### Steps:

1. Access your linux based terminal (WSL if on Windows)
2. Naviate to the project where this README.md file is found
3. Activate your environment by running:
```
conda activate cwld
```
4. Then enter the CUWALID folder by typing:
```
cd CUWALID
```
5. Finally run the file by typing:
```
python run_DRYP.py
```

The end of the output should look similar to the output of the testing output above, with a final line specifiying the time it took to run.


# TO DO LIST

- Create a streamlined input for using the DRYP model where someone using the project can quickly get up and running
- Possibly create a package out of each model to easily access its funtionality
- Create clear documentation on using this project
- Create a file to run the STORM model with a users input files
- Add stoPET model to the project and integrate it in a similair way
