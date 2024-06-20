# -*- coding: utf-8 -*-
"""This script run the model from the command
prompt. The input file needs to be specified
in the command prompt.
>>> run_model input_file.txt
"""
import sys
from dryp.main_DRYP import run_DRYP
import time 

startTime = time.time()

def run_model(path_model):
    """"Function to call run the model ffrom an input file

    Parameters
    ----------
    path_model: str
        path of model input file
    
    Examples
    --------
    >>> from main_DRYP import run_DRYP
    >>> run_DRYP(inputfile)
    """
    run_DRYP(path_model)

if __name__ == '__main__':
    run_model(sys.argv[1])

print ('time=', time.time() - startTime)