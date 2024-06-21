import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.DRYP.dryp.main_DRYP import run_DRYP
import time
startTime = time.time()

run_DRYP("input/DRYP_Input/input_test.dmp")

print ('time=', time.time() - startTime)