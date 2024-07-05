"""Flow accumulator DRYP
"""
import warnings
warnings.filterwarnings('ignore', message="divide by zero*")#\
warnings.filterwarnings('ignore', message="invalid value encountered in divide")

import numpy as np
#from landlab import RasterModelGrid
#import faccumf90 as floss
import models.dryp.components.faccumf90 as floss
from landlab.components.flow_accum import flow_accum_bw#, make_ordered_node_array
from landlab.core.utils import as_id_array
from landlab.components import FlowDirectorD8

class runoff_routing(object):
	"""Function to discharge and transmission losses discharge.
		Running run_one_step() results in the following to occur:
		1. Flow directions are updated (unless update_flow_director is set
		as False).
		2. Intermediate steps that analyse the drainage network topology
		and create datastructures for efficient drainage area and discharge
		calculations.
		3. Calculation of discharge and transmission losses.

	Attributes
	----------

	"""
	def __init__(self, grid, grid_size, surface, FlowDirection, Ksat,
	    	decay, riv_width, riv_length):
		"""initialization of flow routing component
		
		Parameters
		----------
		grid:	landlab grid
			model grid environment
		grid_size:	int
			grid size, leng of grid arrays
		conductivity: numpy array
			channel hydraulic conductivity (m2/dt) [L2 T-1]
		Q_ini: numpy array
			inital volume of water available at the channel [m3] [L3]
		cth_area:	numpy array
			Cell factor area, it reduces or increases the area
		decay: numpy array
			river decay parameter (1/dt)
		river_cell:	array of ints
			river cells, 0 indicate not river in the cell
		area_cells:		cell area?
		AOF_threshold:	Maximum volume of water available for abstraction

		Returns
		-------

		"""
		# Creates numpy arrays for passing model variables
		#env_state.grid.add_zeros('node', "surface_water__discharge")#, dtype=float32)
		Create_parameter_WV(self, Ksat, decay, riv_width, riv_length)
		#Create_parameter_WV(env_state.grid)#, data_in.Kloss)
		self.discharge = np.zeros(grid_size)
		self.SSZ = np.zeros(grid_size)
		self.trans_losses = np.zeros(grid_size)
		self.stage = np.zeros(grid_size)
		#self.flow_tls_dt = np.zeros(grid_size)
		self.carea = None
		
		# 1. Check if flow director is needed
		if FlowDirection is None:
			if 'aux_grid' not in grid.at_node:
				grid.add_field("aux_grid", surface, at="node")
			else:
				grid.at_node['aux_grid'][:] = FlowDirection

			fd = FlowDirectorD8(grid, 'aux_grid')
			fd.run_one_step()
		
			# 2. Creates drainage networks, flowpaths and id arrays
			# a value of 1 must be added to change from python to forttran
			self.r = as_id_array(grid["node"]["flow__receiver_node"])
		else:
			#self.r = as_id_array(range(grid_size))
			#self.r[grid.core_nodes] = FlowDirection[grid.core_nodes]
			self.r = as_id_array(FlowDirection)
			
		#nd = as_id_array(flow_accum_bw._make_number_of_donors_array(self.r))
		#delta = as_id_array(flow_accum_bw._make_delta_array(nd))
		#D = as_id_array(flow_accum_bw._make_array_of_donors(self.r, delta))
		self.s = as_id_array(flow_accum_bw.make_ordered_node_array(self.r))
		#self.carea = find_drainage_area(self.s, self.r,
		#			env_state.area_cells,
		#			env_state.grid.boundary_nodes)		

	#@profile
	def run_runoff_one_step(self, runoff, AOF, AOF_threshold, conductivity,
			 decay, river_cell, area_cells, area_river, river_sat_deficit,
			 boundary_nodes):
		"""Function to make FlowAccumulator calculate drainage area and
		discharge.
		Running run_one_step() results in the following to occur:
			1. Flow directions are updated (unless update_flow_director is set
			as False).
			2. Intermediate steps that analyse the drainage network topology
			and create datastructures for efficient drainage area and discharge
			calculations.
			3. Calculation of drainage area and discharge.
			4. Depression finding and mapping, which updates drainage area and
			discharge.

		Parameters
		----------
		runoff : numpy array
			runoff at each model cell, including base flow at channel
			cells (m/dt) [L T-1]
		conductivity : numpy array
			channel hydraulic conductivity (m2/dt) [L2 T-1]
		SSZ: numpy array
			inital volume of water available at the channel [m3] [L3]
		cth_area :	numpy array
			Cell factor area, it reduces or increases the area
		decay : mumpy array
			river decay parameter (1/dt)
		river_cell : numpy array
			river cells, 0 indicate not river in the cell
		area_cells : numpy array
			cell area
		AOF_threshold : numpy array
			Maximum volume of water available for abstraction
		river_sat_deficit : numpy array
			maximum volume of water allowed in in the riparian zone
			and below the riparian zone (m3)
		
		Attributes
		----------
		discharge : numpy array
			volumetric flow at each cell (m3) [L3]
		Q_ini : numpy array
			inital volume of water available at the channel [m3] [L3]
		Trans_losses : numpy array
			Transmission lossses at river cells [m3] [L3]
		aof : numpy array
			River flow abstraction [mm] [L]
		"""
		# if there is no flow skip flow accumulator
		check_dry_condition = len(np.where(runoff + self.SSZ > 0)[0])

		if check_dry_condition > 0:
			# all valye format type should be float32 to pass to Fortran
			# run this section for any runoff
			# this function return: discharge, QTL, Q_ini, Q_aof
			# calculate volume at each cell
			runoff = np.array(runoff*area_cells, np.float32)
			trans_losses = np.zeros_like(runoff)
			Q_ini = np.array(self.SSZ, np.float32) #Q_ini
			Qaof = np.array(AOF, np.float32) #Qaof
			
			# Call FORTRAN function for flow routing
			floss.ftransloss.find_discharge_and_losses(
				self.s+1, self.r+1,
				np.array(conductivity, np.float32), #Criv
				np.array(decay, np.float32), #Kt
				np.array(river_cell, np.int32), #riv
				np.array(AOF_threshold, np.float32), #Qaoft
				np.array(river_sat_deficit, np.float32), #riv_std
				np.array(self.par_3, np.float32), #P3
				np.array(self.par_4, np.float32), #P4
				runoff, trans_losses, Q_ini, Qaof)
			
			# update overland flow attributes
			self.discharge[:] = runoff[:]		
			self.discharge[self.discharge < 0] = 0
			self.trans_losses[:] = trans_losses[:]

			# save initial conditions for next iteration
			self.SSZ[:] = Q_ini
			
			
		else:
			# no runoff over the entire cells
			self.trans_losses[:] = 0.0
			self.discharge[:] = 0				
			noflow = 0
		
		# Update overland flow attributes
		self.stage[area_river > 0] = (self.discharge[area_river > 0]
				/area_river[area_river > 0])
		
		self.stage[:] = self.stage*river_cell
		

def Create_parameter_WV(self, Ksat, decay, riv_width, riv_length):#, kKloss):
	"""additional parameters to save computational time
	
	Parameters
	----------
	Ksat_ch: numpy array
		saturated hydraulic conductivity [m/dt]
	decay_flow : numpy array
		exponential factor -> residence time
	SS_loss : numpy array
		transmission losses at steady state
	river_width : numpy array
		channel width [m]
	Returns
	-------
	par_3 :	numpy array
		grid variable tp estimate time
	par_4 :	numpy array
		grid variable to estimate transmission losses
	"""
	# Calculate parameter p4 for transmission losses estimation
	self.par_4 = 2.0*Ksat/(decay*riv_width)
	
	# Calculate parameter p3 for estimating time to get dry
	# conditions in the channel
	self.par_3 = Ksat*riv_width*riv_length/(riv_width-2*Ksat)
	
	return		
		


def find_drainage_area(s, r, node_cell_area=1.0, boundary_nodes=None):
	"""THIS COMPONENT IS A MODIFIED VERSION OF FLOW ACCUMULATOR OF LANDLAB
	
	Calculate the drainage area and water discharge at each node, permitting
	discharge to fall (or gain) as it moves downstream according to some
	function. Note that only transmission creates loss, so water sourced
	locally within a cell is always retained. The loss on each link is recorded
	in the 'surface_water__discharge_loss' link field on the grid; ensure this
	exists before running the function.


	Parameters
	----------
	s : ndarray of int
		Ordered (downstream to upstream) array of node IDs
	r : ndarray of int
		Receiver node IDs for each node
	boundary_nodes: list, optional
		Array of boundary nodes to have discharge and drainage area set to zero.
		Default value is None.
	
	Returns
	-------
	tuple of ndarray
		drainage area and discharge
	Notes
	-----
	-  If node_cell_area not given, the output drainage area is equivalent
	to the number of nodes/cells draining through each point, including
	the local node itself.
	-  Give node_cell_area as a scalar when using a regular raster grid.
	-  If runoff is not given, the discharge returned will be the same as
	drainage area (i.e., drainage area times unit runoff rate).
	-  If using an unstructured Landlab grid, make sure that the input
	argument for node_cell_area is the cell area at each NODE rather than
	just at each CELL. This means you need to include entries for the
	perimeter nodes too. They can be zeros.
	
	Examples
	--------
	>>> import numpy as np
	>>> from landlab import RasterModelGrid
	>>> from landlab.components.flow_accum import (
	...     find_drainage_area_and_discharge)
	>>> r = np.array([2, 5, 2, 7, 5, 5, 6, 5, 7, 8])-1
	>>> s = np.array([4, 1, 0, 2, 5, 6, 3, 8, 7, 9])
	>>> l = np.ones(10, dtype=int)  # dummy
	>>> nodes_wo_outlet = np.array([0, 1, 2, 3, 5, 6, 7, 8, 9])
	
	"""
	# Number of points
	npoint = len(s)
	
	# Initialize the drainage_area and discharge arrays. Drainage area starts
	# out as the area of the cell in question, then (unless the cell has no
	# donors) grows from there. Discharge starts out as the cell's local runoff
	# rate times the cell's surface area.
	drainage_area = np.zeros(npoint, dtype=int) + node_cell_area
	#discharge = np.zeros(npoint, dtype=int) + node_cell_area
	# note no loss occurs at a node until the water actually moves along a link
	
	# Optionally zero out drainage area and discharge at boundary nodes
	if boundary_nodes is not None:
		drainage_area[boundary_nodes] = 0
	
	# Iterate backward through the list, which means we work from upstream to
	# downstream.
	for i in range(npoint - 1, -1, -1):
		donor = s[i]
		recvr = r[donor]
		if donor != recvr:
			drainage_area[recvr] += drainage_area[donor]
			
	return drainage_area		
