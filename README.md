# CUWALID
Repository containing the models of CUWALID under the Down2Earth project

## TESTING

You can test if your environment is working correctly with the model by using the 'run_all_test.sh' script in your linux terminal or WSL terminal (THIS TEST CURRENTLY ONLY TESTS THE DRYP MODEL)

### Steps:

1. Navigate to the current directory (CUWALID)
2. Activate your environment
```
conda activate cwld
```
2. type the command
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


## Running the model

Currently only the DRYP model is correctly working, the python file 'run_DRYP.py' should run an example by using the example file 'input_test.dmp' in the DRYP_Input/ folder and uses other test files found in the directory at DRYPv2/example/input/


# TO DO LIST

- Create a streamlined input for using the DRYP model where someone using the project can quickly get up and running
- Add the script to help make the environments and import all the neccesary libraries and dependencies
- Possibly create a package out of each model to easily access its funtionality
- Create clear documentation on using this project
- Create a file to run the STORM model with a users input files
- Add stoPET model to the project and integrate it in a similair way
