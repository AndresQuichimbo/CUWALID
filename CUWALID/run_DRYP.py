from models.DRYP.dryp.main_DRYP import run_DRYP
import time
startTime = time.time()

run_DRYP("input/DRYP_Input/input_test.dmp")

print ('time=', time.time() - startTime)