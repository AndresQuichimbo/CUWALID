import os
from modulefinder import ModuleFinder
import pandas as pd
f = ModuleFinder()
# Run the main script
f.run_script('run_DRYP.py')
# Get names of all the imported modules
names = list(f.modules.keys())
# Get a sorted list of the root modules imported
basemods = sorted(set([name.split('.')[0] for name in names]))
# Print it nicely
print ("\n".join(basemods))


def write_sim_file(filename_input, parameter):
	""" modify the parematers of the model input file and
		model setting file.
		WARNING: it will reeplace the original file, so
		make a copy of the original files

	Parameters
	----------
	filename_input:	str
		model inputfile name, including path
	parameter : list or numpy array
		1D array of model paramters
	"""
	
	# Check if input file exist
	if not os.path.exists(filename_input):
		raise ValueError("File not availble")
	
	# Read model input file
	f = pd.read_csv(filename_input)
	
	# Change model name by adding the simulation number
	f.drylandmodel[1] = f.drylandmodel[1] + str(int(parameter[0]))

	# change the name of the setting parameter file
	filename_simpar = f.drylandmodel[87]
	
	# Open setting parameter file
	fsimpar = pd.read_csv(filename_simpar)	
	
	# Change setting parameter file with new values
	fsimpar['DWAPM_SET'][46] = ('%.5f' % parameter[1]) # kdt
	fsimpar['DWAPM_SET'][48] = ('%.5f' % parameter[2]) # kDroot
	fsimpar['DWAPM_SET'][50] = ('%.2f' % parameter[3]) # kAWC
	fsimpar['DWAPM_SET'][52] = ('%.5f' % parameter[4]) # kKsat
	fsimpar['DWAPM_SET'][54] = ('%.5f' % parameter[5]) # kSigma
	fsimpar['DWAPM_SET'][56] = ('%.5f' % parameter[6]) # kKch
	fsimpar['DWAPM_SET'][58] = ('%.5f' % parameter[7]) # T
	fsimpar['DWAPM_SET'][60] = ('%.5f' % parameter[8]) # kW
	fsimpar['DWAPM_SET'][62] = ('%.5f' % parameter[9]) # kKaq
	fsimpar['DWAPM_SET'][64] = ('%.5f' % parameter[10])# kSy
	
	# Reeplace model input and parameters file
	os.remove(filename_input) if os.path.exists(filename_input) else None
	os.remove(filename_simpar) if os.path.exists(filename_simpar) else None
	
	# Write model parameter and input file
	f.to_csv(filename_input, index=False)
	fsimpar.to_csv(filename_simpar, index=False)