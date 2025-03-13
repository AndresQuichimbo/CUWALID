import numpy as np

# read

class water_management(object):
	def __init__(self, ):	
		"""Initializa the water storage management component
		
		Parameters
		----------

		
		Attributes
		----------

		"""	
		pass
	    

	def get_abstractions(self, storage_water_bodies, abstractions):
		"""
		This component calculate the amount of water available for
		abstractions from reservoirs and dams
		"""
        # get dataset from
		abstractions = get_excess_storage(storage_water_bodies, abstractions)
		
		return abstractions

def get_excess_storage(storage, extraction):
    """
	Calculates the amount of storage available in the cell and update the
	extraction to match the current available dataset
	"""
    # calculate storage change
    storage_update = storage - extraction
	
	# update extraction, if water is not available, take only
	# the amount which is available
    extraction[storage_update < 0] = storage[storage_update <= 0]
	
    return extraction