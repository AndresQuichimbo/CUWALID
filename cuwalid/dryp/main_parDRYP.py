# -*- coding: utf-8 -*-
"""
DRYP - Dryland WAter Partitioning Model
__date__ = '20230801'
__version__ = '2.0.1'
__author__ = 'Andres Quichimbo (andresquichimbo@gmail.com)'
__library__ = 'dryp'

General command line:
	python run_drp_input.py filename_input.json
		
Parameters:
	-input_file : string
		path to input json as described in documentation which can be found at https://cuwalid.github.io/model-info/dryp-model
Version(s):
20191130 (1.0.0) --> Development of application for version 2.0.0 of Cuwalid models
"""

import argparse
import importlib
import json
import numpy as np
from cuwalid.dryp.components.DRYP_io import (
    zone_parameters,
	parallel_parameters
)
from cuwalid.dryp.components.DRYP_json_reader import get_model_settings
from cuwalid.dryp.components.DRYP_groundwater_EFD import storage_uz_sz
from cuwalid.dryp.components.assemble_model_components import (
    initialize_core_hydrology_components,
    set_flux_boundary_conditions,
    initialize_simulation_state_variables,
    initialize_output_arrays,
	setup_monitoring_nodes
	)
from cuwalid.dryp.components.read_model_parameters import read_model_parameters
from cuwalid.dryp.components.read_temporal_datasets import read_temporal_datasets
from cuwalid.dryp.components.save_model_output import save_model_outputs										
import cuwalid.dryp.components.DRYP_util as utils

import cuwalid.dryp.components.DRYP_parallel_tools as partools
import time

import matplotlib.pyplot as plt


if importlib.util.find_spec("tqdm") is not None:
	tqdm = importlib.import_module("tqdm").tqdm
else:
	class _NoOpTqdm:
		def update(self, n=1):
			return None

		def close(self):
			return None

	def tqdm(*args, **kwargs):
		return _NoOpTqdm()

if importlib.util.find_spec("mpi4py") is not None:
	from mpi4py import MPI
	#MPI = importlib.import_module("mpi4py").MPI
else:
	MPI = None
# ---------------------------------------------------------------------
# Version and algorithm information
project_name = 'DRYP'
alg_version = '2.0.1'
alg_type = 'Model'
alg_name = 'RUN_DRYP'
alg_release = '2023-08-01'
# ---------------------------------------------------------------------

import cProfile

def profile(filename=None, comm=MPI.COMM_WORLD):
  def prof_decorator(f):
    def wrap_f(*args, **kwargs):
      pr = cProfile.Profile()
      pr.enable()
      result = f(*args, **kwargs)
      pr.disable()

      if filename is None:
        pr.print_stats()
      else:
        filename_r = filename + ".{}".format(comm.rank)
        pr.dump_stats(filename_r)

      return result
    return wrap_f
  return prof_decorator

def _log_root(rank, *args, **kwargs):
	if rank == 0:
		print(*args, **kwargs)


def exchange_halos(comm, field, halo_info):
    """
    Exchange halo values for a local field (1D array aligned with region_domain).

    field: local array (including halo cells)
    halo_info: dict with recv_local and send_local per neighbor
    """

    reqs = []
    recv_buffers = {}

    # Post receives first
    for neighbor_rank, info in halo_info.items():
        recv_idx = info["recv_local"]
        recv_buffers[neighbor_rank] = np.empty(len(recv_idx), dtype=field.dtype)

        req = comm.Irecv(recv_buffers[neighbor_rank], source=int(neighbor_rank))
        reqs.append(req)

    # Post sends
    for neighbor_rank, info in halo_info.items():
        send_idx = info["send_local"]
        send_data = field[send_idx].copy()

        req = comm.Isend(send_data, dest=int(neighbor_rank))
        reqs.append(req)

    # Wait for all comms
    MPI.Request.Waitall(reqs)

    # Fill received values into halo
    for neighbor_rank, info in halo_info.items():
        recv_idx = info["recv_local"]
        field[recv_idx] = recv_buffers[neighbor_rank]

    return field

def _load_parallel_config(filename_input):
	try:
		with open(filename_input, 'r') as f:
			config = json.load(f)
	except Exception:
		return {}

	parallel_cfg = config.get('PARALLEL', {})
	if isinstance(parallel_cfg, dict):
		return parallel_cfg
	return {}

def _extract_subdomain_spec(parallel_cfg, component):
	if component == 'ro':
		keys = ('ro_subdomains', 'runoff_subdomains', 'oz_subdomains', 'subdomains_ro', 'path_oz_subdomains')
	else:
		keys = ('gw_subdomains', 'groundwater_subdomains', 'sz_subdomains', 'subdomains_gw', 'path_sz_subdomains')

	for key in keys:
		value = parallel_cfg.get(key)
		if isinstance(value, list):
			return value
	return None

# replace this function with a more robust function that can handle different formats of subdomain specifications, such as:
def _normalize_subdomains(raw_spec, grid_size, active_nodes):
	active_nodes = np.array(active_nodes, dtype=int)
	if raw_spec is None:
		return [active_nodes.copy()]

	subdomains = []
	if isinstance(raw_spec, list) and len(raw_spec) > 0 and isinstance(raw_spec[0], (list, tuple)):
		for region in raw_spec:
			subdomains.append(np.array(region, dtype=int).ravel())
	else:
		arr = np.array(raw_spec)
		if arr.ndim == 1 and arr.size in (grid_size, active_nodes.size):
			labels = arr.astype(int)
			for label in np.unique(labels):
				if label <= 0:
					continue
				if labels.size == grid_size:
					idx = np.where(labels == label)[0]
				else:
					idx = active_nodes[np.where(labels == label)[0]]
				subdomains.append(idx.astype(int))
		elif arr.ndim == 1:
			subdomains.append(arr.astype(int).ravel())

	clean_subdomains = []
	assigned = np.zeros(grid_size, dtype=bool)
	active_mask = np.zeros(grid_size, dtype=bool)
	active_mask[active_nodes] = True

	for region in subdomains:
		if region.size == 0:
			continue
		region = region[(region >= 0) & (region < grid_size)]
		if region.size == 0:
			continue
		region = np.unique(region)
		region = region[active_mask[region]]
		region = region[~assigned[region]]
		if region.size == 0:
			continue
		assigned[region] = True
		clean_subdomains.append(region)

	remaining = active_nodes[~assigned[active_nodes]]
	if remaining.size > 0:
		clean_subdomains.append(remaining)

	if len(clean_subdomains) == 0:
		clean_subdomains.append(active_nodes.copy())

	return clean_subdomains

def _owned_nodes_for_rank(subdomains, rank, size):
	if size <= 1:
		return np.unique(np.concatenate(subdomains)).astype(int)

	owned = [subdomains[i] for i in range(len(subdomains)) if i % size == rank]
	if len(owned) == 0:
		return np.array([], dtype=int)
	return np.unique(np.concatenate(owned)).astype(int)

def _allreduce_sum(comm, local_array):
	if comm is None:
		return local_array
	global_array = np.zeros_like(local_array)
	comm.Allreduce(local_array, global_array, op=MPI.SUM)
	return global_array



def add_send_info(halo_info, region_domain, global_node_owner, rank):
    global_nodes = region_domain['global_nodes']
    core_mask = region_domain['core_mask'].flatten()

    # build lookup: global_id → local core index
    global_to_local_core = {
        global_nodes[i]: i
        for i in range(len(global_nodes))
        if core_mask[i]
    }

    # initialize send lists
    for neighbor_rank in halo_info:
        halo_info[neighbor_rank]["send_local"] = []

    # iterate over my core nodes
    for local_idx, is_core in enumerate(core_mask):
        if not is_core:
            continue

        global_id = global_nodes[local_idx]

        # check if any neighbor wants this global node
        for neighbor_rank, info in halo_info.items():
            # neighbor's recv_local is in my local array — convert to global_ids
            neighbor_recv_global_ids = [global_nodes[idx] for idx in info["recv_local"]]

            if global_id in neighbor_recv_global_ids:
                halo_info[neighbor_rank]["send_local"].append(local_idx)

    return halo_info

import numpy as np

# def build_halo_send_recv(region_domain, global_node_owner, rank):
#     """
#     Build both recv_local and send_local for a given rank.
    
#     Args:
#         region_domain: dict with keys
#             - 'global_nodes': 1D array mapping local index → global node ID
#             - 'core_mask': bool array indicating core nodes
#             - 'mask': bool array indicating all nodes in the subdomain
#         global_node_owner: array mapping global node ID → owner rank
#         rank: current rank
    
#     Returns:
#         halo_info: dict keyed by neighbor rank
#             - 'recv_local': list of local indices to receive from that neighbor
#             - 'send_local': list of local indices to send to that neighbor
#     """
#     global_nodes = region_domain['global_nodes']
#     core_mask = region_domain['core_mask'].flatten()
#     mask = region_domain['mask'].flatten()
    
#     # halo nodes = in mask but not core
#     halo_mask = mask & (~core_mask)
    
#     halo_info = {}

#     # ----------------------------
#     # 1️⃣ Build recv_local
#     # ----------------------------
#     for local_idx, is_halo in enumerate(halo_mask):
#         if not is_halo:
#             continue

#         global_id = global_nodes[local_idx]
#         owner = global_node_owner[global_id]

#         if owner == rank:
#             continue  # I own it → not a recv from neighbor

#         if owner not in halo_info:
#             halo_info[owner] = {"recv_local": [], "send_local": []}

#         halo_info[owner]["recv_local"].append(local_idx)

#     # ----------------------------
#     # 2️⃣ Build send_local
#     # ----------------------------
#     # Build lookup: global_id → local core index
#     global_to_local_core = {
#         global_nodes[i]: i
#         for i, is_core in enumerate(core_mask)
#         if is_core
#     }

#     # Iterate over all my core nodes
#     for local_idx, is_core in enumerate(core_mask):
#         if not is_core:
#             continue

#         global_id = global_nodes[local_idx]

#         # Check which neighbors want this node
#         for neighbor_rank, info in halo_info.items():
#             # If neighbor owns a halo cell whose global ID equals this core node
#             neighbor_recv_global_ids = [
#                 global_nodes[idx] for idx in info["recv_local"]
#             ]
#             if global_id in neighbor_recv_global_ids:
#                 info["send_local"].append(local_idx)

#     return halo_info

# def build_halo_send_recv(region_domain, global_node_owner, rank):
#     """
#     Build recv_local and send_local for a rank based on global ownership.

#     Args:
#         region_domain: dict with
#             - 'global_nodes': 1D array mapping local index → global node ID
#             - 'core_mask': bool array indicating core nodes
#             - 'mask': bool array indicating all nodes in the subdomain
#         global_node_owner: array mapping global node ID → owner rank
#         rank: current rank

#     Returns:
#         halo_info: dict keyed by neighbor rank
#             - 'recv_local': list of local indices to receive from that neighbor
#             - 'send_local': list of local indices to send to that neighbor
#     """
#     global_nodes = region_domain['global_nodes']
#     core_mask = region_domain['core_mask'].flatten()
#     mask = region_domain['mask'].flatten()

#     # halo = in mask but not core
#     halo_mask = mask & (~core_mask)

#     halo_info = {}

#     # ----------------------------
#     # 1️⃣ Build recv_local: halo nodes owned by neighbors
#     # ----------------------------
#     for local_idx, is_halo in enumerate(halo_mask):
#         if not is_halo:
#             continue

#         global_id = global_nodes[local_idx]
#         owner = global_node_owner[global_id]

#         if owner == rank:
#             continue  # I own it → not received

#         if owner not in halo_info:
#             halo_info[owner] = {"recv_local": [], "send_local": []}

#         halo_info[owner]["recv_local"].append(local_idx)

#     # ----------------------------
#     # 2️⃣ Build send_local: my core nodes needed by neighbors
#     # ----------------------------
#     # build lookup: global_id → local core index
#     global_to_local_core = {
#         global_nodes[i]: i
#         for i, is_core in enumerate(core_mask) if is_core
#     }

#     # iterate over all halo nodes to see which neighbor wants which global_id
#     for neighbor_rank, info in halo_info.items():
#         send_list = []

#         for recv_local_idx in info["recv_local"]:
#             global_id = global_nodes[recv_local_idx]

#             # if I own this global_id → neighbor wants it
#             if global_node_owner[global_id] == rank:
#                 # map to my local core index
#                 send_list.append(global_to_local_core[global_id])

#         info["send_local"] = send_list

#     # ----------------------------
#     # 3️⃣ Check for frontier nodes I own that are requested by neighbors
#     # Optional: for ranks not already in halo_info
#     # ----------------------------
#     # This step ensures neighbors that have no halo nodes in my domain
#     # but might request frontier nodes still appear
#     return halo_info

# def add_send_info(halo_info, region_domain, global_node_owner, rank):
#     global_nodes = region_domain['global_nodes']
#     core_mask = region_domain['core_mask'].flatten()

#     # build reverse lookup: global_id → local core index
#     global_to_local_core = {
#         global_nodes[i]: i
#         for i in range(len(global_nodes))
#         if core_mask[i]
#     }

#     for neighbor_rank, info in halo_info.items():
#         send_list = []

#         for local_idx in info["recv_local"]:
#             global_id = global_nodes[local_idx]

#             # if I own this node → I must send it
#             if global_node_owner[global_id] == rank:
#                 if global_id in global_to_local_core:
#                     send_list.append(global_to_local_core[global_id])

#         info["send_local"] = send_list

#     return halo_info

# def add_send_info(halo_info, region_domain, global_node_owner, rank):
#     global_nodes = region_domain['global_nodes']
#     core_mask = region_domain['core_mask'].flatten()

#     for neighbor_rank, info in halo_info.items():
#         send_list = []

#         # Get global IDs that neighbor needs (from recv)
#         recv_globals = global_nodes[info["recv_local"]]

#         for local_idx, is_core in enumerate(core_mask):
#             if not is_core:
#                 continue

#             global_id = global_nodes[local_idx]

#             # ONLY send if neighbor needs it
#             if global_id in recv_globals:
#                 send_list.append(local_idx)

#         info["send_local"] = send_list

#     return halo_info

# def add_send_info(halo_info, region_domain, global_node_owner, rank):
#     global_nodes = region_domain['global_nodes']
#     core_mask = region_domain['core_mask'].flatten()

#     for neighbor_rank, info in halo_info.items():
#         send_list = []

#         for local_idx, is_core in enumerate(core_mask):
#             if not is_core:
#                 continue

#             global_id = global_nodes[local_idx]

#             # check if neighbor needs this node
#             if global_node_owner[global_id] == rank:
#                 send_list.append(local_idx)

#         info["send_local"] = send_list

#     return halo_info

# Structure and model components --------------------------------------
# data_in:	Input variables 
# env_state:Model state and fluxes
# rf:		Precipitation
# cnp:		canopy interception
# abc:		Anthropic boundary conditions
# inf:		Infiltration 
# swbm:		Soil water balance
# ro:		Routing - Flow accumulator
# gw:		Groundwater flow

# parallel version of the model, with parallel execution of model components
# parallelization: parallel execution of model components
#@profile

@profile(filename="profile_out")
def run_parDRYP(filename_input):
	"""This function integrates all components of the model, with
	all model parameters and component settings being specified in
	the -filename_input- file.
	
	"""
	
	comm = MPI.COMM_WORLD if MPI is not None else None
	rank = comm.Get_rank() if comm is not None else 0
	size = comm.Get_size() if comm is not None else 1
	is_root = rank == 0
	print(f"[MAIN] Rank: {rank}, Size: {size}")
	# print(C)
	# time.sleep(10)

	# read model paramters and model setting file
	data_in = get_model_settings(filename_input)

	_log_root(rank, "***************************** READING MODEL PARAMETERS *****************************")

	domain, topo, soil, rsoil, aquifer, vegetation, water_bodies, water_bodies_management = \
		read_model_parameters(data_in)
	
    # ***
    # components that needs to be parallelized
	# aquifer
	# It needs to be divided into subdomains, and each subdomain is assigned to a different process.
    # The subdomains are specified in the input file, and they can be defined based on the spatial
    # distribution of geographic features.
	
	# create model grid
	grid = domain.create_projected_grid(topo.mask, geographic=data_in.geographic)
	
    # ***
    # maybe here is a good place to split the grid into subdomains for parallel execution of the
    # groundwater component, but it can be done later in the groundwater component. The grid is
    # an object that contains the grid information such links connectivity and nodes.
	
	# READING FORCING DATASET -------------------------------------------
	# Read precipitation
	_log_root(rank, "***************************** READING TEMPORAL DATASETS ****************************")

	PRE, ET0, SAVI, LAI, Kc, av, SAVImin, SAVImax, fluxOF, fluxUZ, fluxSZ, fluxWB, Qusz = \
		read_temporal_datasets(data_in, topo)

	# MODEL COMPONENTS ------------------------------------------------------
	_log_root(rank, "*************************** ASSEMBLING MODEL COMPONENTS ****************************")

	abc, inf, cnp, swb, swb_rip, ro, gw, lks, pnds = initialize_core_hydrology_components(
		data_in, grid, topo, aquifer, water_bodies
		)
	
    # ***
    # the line above create the model components (gw-Jose), but it does not run them. The components are run
    # in the main loop below, where the model state is updated at each time step. The components
    # are run in a specific order, which is defined by the model structure and the dependencies
    # between components.
    # Here is the place where the parallel execution of the components can be implemented by creating
    # multiple sub components for each model component, depending on the number of subdomains.
    # The sub components can be run in parallel, and the results can be combined to update the model state.

	(idFluxOF, idFluxOF_act, idFluxUZ, idFluxUZ_act,
	idFluxSZ, idFluxSZ_act, idFluxWB, idFluxWB_act,
	idFluxWBout, idFluxWBout_act) = set_flux_boundary_conditions(
		data_in, grid, fluxOF, fluxUZ, fluxSZ, fluxWB
	)

	# Initialise time step variables
	t = t_eto = t_pre = t_savi = t_kc = t_av = t_abs= 0

	(gws_mb, etg_agg, rch_agg, dt_GW, act_nodes, riv_nodes, act_riv_nodes,
	id_lakes, head, theta, river_sat_deficit, save_rz_var, rtheta,
	Duz0, z_extintion, Ft0, SORP0, t_0, dry_day,
	runoff, recharge, baseflow, AOF_threshold) = initialize_simulation_state_variables(
		data_in, topo, grid, aquifer, soil, vegetation, ro
	)

	# read model domains for parallel execution of model components, and assign nodes to each subdomain
	parallel_domains = parallel_parameters(data_in)

	domains_ro = parallel_domains.ro
	domains_gw = parallel_domains.gw
	# print("domains_gw: ",domains_gw)
	runoff_grid_shape = domain.grid_metadata['shape']
	basin_ids = partools.get_basin_ids(domains_ro)
	runoff_parallel = size > 1 and len(basin_ids) > 0
	local_basin_ids = partools.assign_basins_to_rank(basin_ids, rank, size) if runoff_parallel else []
	
	basis_ro = {}
	basis_runtime_parameters = {}

	gw_region_ids = partools.get_basin_ids(domains_gw)
	gw_parallel = data_in.run_GW > 0 and size > 1 and len(gw_region_ids) > 0
	local_gw_region_ids = partools.assign_basins_to_rank(gw_region_ids, rank, size) if gw_parallel else []
	# print("local_gw_region_ids: ",local_gw_region_ids)
	region_gw = {}
	region_runtime_parameters_gw = {}
	gw_split_lakes_detected = False

	_log_root(
		rank,
		f"Parallel setup -> MPI ranks: {size}",
	)

	for basin_id in local_basin_ids:
		basin_domain = partools.extract_basin_data(
			basin_id, domains_ro, domain.grid_metadata, grid=True)
		
		
		basin_parameters = partools.extract_basin_parameters(
			basin_id,
			domains_ro,
			{
				'surface': topo.surface,
				'flowdird8': topo.FlowDir,
				'Ksat': topo.Ksat,
				'decay': topo.decay,
				'riv_width': topo.riv_width,
				'riv_length': topo.riv_length,
				'conductivity': topo.conductivity,
				'river_cells': topo.river_cells,
				'AOF_threshold': AOF_threshold,
				'area_cells': topo.area_cells,
				'area_river': topo.area_river,
			},
		)
		
		basis_ro[basin_id] = partools.initialize_basin_component(
			basin_domain, basin_parameters)
		basis_runtime_parameters[basin_id] = {
			'conductivity': basin_parameters['conductivity'],
			'decay': basin_parameters['decay'],
			'river_cells': basin_parameters['river_cells'],
			'AOF_threshold': basin_parameters['AOF_threshold'],
			'area_cells': basin_parameters['area_cells'],
			'area_river': basin_parameters['area_river'],
		}
	################################################################################################
	global_head = head.copy()
	global_baseflow = np.zeros_like(head)
	global_owner = np.zeros(topo.grid_size, dtype=np.int32)
	global_node_owner = np.full(topo.grid_size, -1, dtype=np.int32)
	# print("local_gw_region_ids: ",local_gw_region_ids)

	for region_id in local_gw_region_ids:
		region_domain = partools.extract_basin_data_with_halo2(
			region_id, domains_gw, domain.grid_metadata, rank, halo = 0, grid=True)
		
		core_mask_flat = region_domain['core_mask'].flatten()  # only real basin cells
		halo_mask_flat = region_domain['mask'].flatten() & ~core_mask_flat # halo=region domain without core cells
		# region_domain['local_to_global'] = region_domain['global_nodes']
		
		# print("Total halo cells:", np.sum(halo_mask_flat))
		# print("Halo cell indices:", np.where(halo_mask_flat)[0])
		################################################################################
		core_mask = region_domain['core_mask'].flatten()
		global_nodes = region_domain['global_nodes']

		owned_nodes = global_nodes[core_mask]
		global_node_owner[owned_nodes] = rank
		filename = f"/shared/home1/c.c23086054/CUWALID/cuwalid/global_node_owner_rank_{rank}.csv"
		np.savetxt(filename, global_node_owner, delimiter=",", fmt="%d")

		################################################################################
		
		region_parameters = partools.extract_basin_parameters_halo(
			region_id,
			domains_gw,
			{
				'surface': topo.surface,
				'bottom': aquifer.bottom,
				'thickness': aquifer.thickness,
				'bathymetry': topo.bathymetry,
				'riv_elevation': topo.riv_elevation,
				'Ksat': aquifer.Ksat,
				'Sy': aquifer.Sy,
				'Droot': soil.Droot*0.001,
				'conductivity': topo.conductivity,
				'inodetype': aquifer.gwtype,
				'theta_sat': soil.theta_sat,
				'theta_fc': soil.theta_fc,
				'area_river': topo.area_river,
				'bc_head': aquifer.CHB,
			},
			halo = 0,
			mask_inactive=True,
		)
		
		
		region_mask = region_domain['mask'].flatten()
		region_parameters['bc_head'][~region_mask] = -9999
		
		region_parameters['riv_nodes'] = partools.map_global_nodes_to_local(
			region_domain, riv_nodes)
		
		(ids_lks_local,
		 size_lks_local,
		 ids_max_depth_lks_local,
		 split_lakes_local) = partools.extract_complete_lake_data(
			region_domain,
			water_bodies.ids_lks,
			water_bodies.size_lks,
			water_bodies.ids_max_depth_lks,
		)
		
		gw_split_lakes_detected = gw_split_lakes_detected or split_lakes_local
		region_parameters['ids_lks'] = ids_lks_local
		region_parameters['size_lks'] = size_lks_local
		region_parameters['ids_max_depth_lks'] = ids_max_depth_lks_local

		# print('region_domain[mask]: bef gw ', region_domain['mask'])

		

		region_gw[region_id] = partools.initialize_gwflow_component(
			region_domain, region_parameters)
		
		region_runtime_parameters_gw[region_id] = {
			'grid': region_domain['grid'],
			'surface': region_parameters['surface'],
			'bottom': region_parameters['bottom'],
			'thickness': region_parameters['thickness'],
			'bathymetry': region_parameters['bathymetry'],
			'riv_elevation': region_parameters['riv_elevation'],
			'riv_nodes': region_parameters['riv_nodes'],
			'Ksat': region_parameters['Ksat'],
			'Sy': region_parameters['Sy'],
			'Droot': region_parameters['Droot'],
			'conductivity': region_parameters['conductivity'],
			'inodetype': region_parameters['inodetype'],
			'theta_sat': region_parameters['theta_sat'],
			'theta_fc': region_parameters['theta_fc'],
			'area_river': region_parameters['area_river'],
			'ids_lks': region_parameters['ids_lks'],
			'size_lks': region_parameters['size_lks'],
			'ids_max_depth_lks': region_parameters['ids_max_depth_lks'],
			'active_count': int(np.count_nonzero(region_mask)),
		}
	
	# print(C)

	

	if gw_parallel and comm is not None:
		gw_split_lakes_detected = comm.allreduce(gw_split_lakes_detected, op=MPI.LOR)

	


	#parallel_cfg = _load_parallel_config(filename_input)
	##ro_subdomains = _normalize_subdomains(
	##	_extract_subdomain_spec(parallel_cfg, 'ro'), topo.grid_size, act_nodes)
	#gw_subdomains = _normalize_subdomains(
	#	_extract_subdomain_spec(parallel_cfg, 'gw'), topo.grid_size, act_nodes)
#
	##local_ro_nodes = _owned_nodes_for_rank(ro_subdomains, rank, size)
	#local_gw_nodes = _owned_nodes_for_rank(gw_subdomains, rank, size)
#
	##local_ro_mask = np.zeros(topo.grid_size, dtype=bool)
	##local_ro_mask[local_ro_nodes] = True
#
	#local_gw_mask = np.zeros(topo.grid_size, dtype=bool)
	#local_gw_mask[local_gw_nodes] = True
#
	##ro_ssz_global = ro.SSZ.copy()
	#
	#if size > 1 and data_in.run_GW > 0:
	#	gw_global_mask = gw.act_nodes.copy()
	#	gw.act_nodes[:] = 0
	#	gw.act_nodes[local_gw_nodes] = gw_global_mask[local_gw_nodes]

	_log_root(
		rank,
		f"Parallel setup -> MPI ranks: {size}, runoff subdomains: {len(basin_ids) if basin_ids else 1}, groundwater subdomains: {len(gw_region_ids) if gw_region_ids else 1}",
	)
	
	if gw_parallel and gw_split_lakes_detected:
		_log_root(
			rank,
			"Warning: some lakes span multiple groundwater domains; lake coupling is only applied to lakes fully contained within a single groundwater domain.",
		)

	
    # ***
	# the line above initialize the model state variables, which are updated at each time step
    # in the main loop below. The model state variables are stored in a dictionary, and they
    # are updated by the model components at each time step. The model state variables are
    # also used to calculate the model outputs, which are saved at the end of the simulation.
	# It could be a good place to initialize sub state variables for each subdomain, which
    # can be updated in parallel by the model components.
	
	# INITIALISE OUTPUT AND MONITORING --------------------------------
	#print("************************ READING SETTINGS FOR MODEL OUPUTS *************************")
	_log_root(rank, "Setting up outputs and monitoring nodes")
	idOF, idUZ, idGW, idzone_info = setup_monitoring_nodes(grid, data_in)
	#print("Monitoring nodes OF:", idGW)
	#print("Monitoring nodes IDs:", idzone_info[2])
	(#idOF, idOF_act, idUZ, idUZ_act, idGW, idGW_act,
	point_var, grid_var, grid_rmax, grid_vmax, total_var,
	grid_rpvar, total_rpvar, grid_pndvar, total_pndvar, grid_veg,
	grid_lks, zone_var) = initialize_output_arrays(data_in)#, grid, riv_nodes, water_bodies
	
	
	# Initialise the progress bar
	_log_root(rank, "****************************** SIMULATION IN PROGRESS ******************************")
	_log_root(rank, "Simulation period: from", data_in.ini_date, "to", data_in.end_date, "number of days:", data_in.ndays)
	progress_bar = tqdm(total=data_in.ndays, unit='days') if is_root else None

	# print(C)
	start = time.time()

	while t < data_in.ndays:

		for UZ_ti in range(data_in.dt_hourly):
			
			for dt_pre_sub in range(data_in.dt_sub_hourly):

				# get rainfall
				rain = PRE.get_one_step_dataset(t_pre, data_in.fname_TSPre, 'pre')
				
				# get potential evapotranspiration
				PET = ET0.get_one_step_dataset(t_eto, data_in.fname_TSMeteo, 'pet')
				
				# ABSTRCTIONS/IRRIGATION ------------------------------
				# read flux boundary conditions for all components
				# add data abstractions/sink/source points
				# select row from dataframe and add to the excess component
				if fluxUZ.data_set is not None:					
					rain[idFluxUZ] += fluxUZ.get_point_dataset_one_step(t_abs)
				
				# not in used, NOT DELETE
				# estimate abstractions
				AOF, AUZ, ASZ = abc.run_ABM_one_step(
					rain, Duz0, theta,
					soil.theta_fc,
					soil.theta_wp,
					head,
					)				
				


				# check if interception is activated
				#if vegetation.av is None:
				#	SAVIdt = None
				#	SAVIdt_min = None
				#	SAVIdt_max = None
				#	LAIdt = None
				#	Kcdt = None
				#else:
				SAVIdt = SAVI.get_one_step_dataset(t_savi, data_in.fname_TSsavi, 'savi')
				SAVIdt_min = SAVImin.get_one_step_dataset(t_savi, data_in.fname_savi_min, 'savi')
				SAVIdt_max = SAVImax.get_one_step_dataset(t_savi, data_in.fname_savi_max, 'savi')
				LAIdt = LAI.get_one_step_dataset(t_savi, data_in.fname_TSlai, 'LAI')
				Kcdt = Kc.get_one_step_dataset(t_savi, data_in.fname_TSkc, 'kc')
				avdt = av.get_one_step_dataset(t_av, data_in.fname_TSav, 'VegetationFraction')

				

				if Kcdt is not None:
					# remove the folowing line
					#Kcdt = np.flip(Kcdt.reshape((topo.grid_ncols, topo.grid_nrows)),0).flatten()
					Kcdt = Kcdt[act_nodes]
					Kcdt[Kcdt <= 0] = 1.0
				if LAIdt is not None:
					# remove the folowing line
					#LAIdt = np.flip(LAIdt.reshape((topo.grid_ncols, topo.grid_nrows)),0).flatten()
					LAIdt = LAIdt[act_nodes]
					LAIdt[LAIdt <= 0] = 0.0
				if SAVIdt is not None:
					# remove the folowing line
					#SAVIdt = np.flip(SAVIdt.reshape((topo.grid_ncols, topo.grid_nrows)),0).flatten()
					SAVIdt = SAVIdt[act_nodes]
				
				#print(vegetation.av, SAVIdt, SAVIdt_max, SAVIdt_max, LAIdt, Kcdt)
				# PONDS: Add ponds here ------------------------------------------
				# first check if ponds is active
				if water_bodies.id_nodes is not None:
					water_bodies.pnds_Vo, et_pnds, aoz_pnds, Ppnds = pnds.run_ponds_one_step(
				 							water_bodies.pnds_Vo,
											rain[water_bodies.id_nodes],
											PET[water_bodies.id_nodes], #aoz,
											topo.area_cells,
											)
					# transfer data to the entire model domain
					rain[water_bodies.id_nodes] = Ppnds
				
				## calculate AV
				#av = None
				if avdt is None:
					if vegetation.av is not None:
						#av = (SAVIdt - SAVIdt_min)/(SAVIdt_max - SAVIdt_min)
						vegetation.av = vegetation.av[act_nodes]
				else:
					vegetation.av = avdt[act_nodes]

				
				
				# add interception component - UZ zone
				Pth, Eca, PETh, LAIdt, Kcdt, vegetation.Sc0_cn[act_nodes] = cnp.run_interception_one_step(
						rain[act_nodes], PET[act_nodes], vegetation.av,
						SAVIdt, SAVIdt_max, SAVIdt_min,
						LAIdt,
						vegetation.lai_a,
						vegetation.lai_b,
						vegetation.fcw_cn[act_nodes],
						vegetation.Sc0_cn[act_nodes],
						Kcdt)

				
				
				## Estimate Kc for the riparian area
				#Pthr, Ecar, PETr, LAIr, Kcr, Sc0_cnrp = cnp.run_interception_one_step(
				#		rain, PET, vegetation.av,
				#		SAVIdt, SAVIdt_max, SAVIdt_min,
				#		None,
				#		vegetation.lai_a,
				#		vegetation.lai_b,
				#		vegetation.fcw_cn,
				#		vegetation.Sc0_cnrp,
				#		Kcdt)
						
				##### NOT IN USE, NOT DELETE
				##### estimate precipitation over the soil
				##### it combines the interception from the hillslopes
				##### and the riparian zone
				####Pth = (Pth*(1-topo.rip_to_cell_area_factor)
				####	+ Pthr*(topo.rip_to_cell_area_factor))
							
				#### NOT IN USE, NOT DELETE												
				#### add irrigation as rain, still under development
				####Pth = Pth[:] + abc.auz[:]
								
				# INFILTRATION: estimate infiltration --------------------
				#inf.run_infiltration_one_step(Pth, env_state, data_in)

				

				INF, EXS, Ft0, SORP0, t_0, dry_day = inf.run_infiltration_one_step(
						soil.Ksat[act_nodes],
						soil.theta_sat[act_nodes],
						soil.PSI[act_nodes],
						soil.Droot[act_nodes],
						theta[act_nodes],
						#rain[act_nodes],
						Pth,
						Ft0, SORP0, t_0, dry_day,
						)

				
				
				# subsurface storage [mm]
				#if data_in.run_GW > 0:
				tws = storage_uz_sz(
						topo.surface[act_nodes],
						topo.bathymetry[act_nodes],
						aquifer.bottom[act_nodes],
						soil.Droot[act_nodes]*0.001,
						soil.theta_sat[act_nodes],
						aquifer.Sy[act_nodes],
						head[act_nodes],
						theta[act_nodes]
						)
				
				

				# GROUNDWATER ABSTRACTIONS ------------------------------
				# calculate maximum water available to extract from water bodies
				# select row from dataframe and add to the excess component
				# units of abstractions should be given in flux/volume units (e.g. m3)
				if fluxWB.data_set is not None:
					# read datasets				
					maximum_flux_wb = np.abs(fluxWB.get_point_dataset_one_step(t_abs))
					
					# change units from m3 to m
					maximum_flux_wb = maximum_flux_wb/topo.area_cells

					# calculate storage of water bodies (meters)
					# storage can not be negative
					storage_wb = head[idFluxWB] - topo.bathymetry[idFluxWB]
					storage_wb[storage_wb < 0] = 0

					# calculate maximum abstractions
					maximum_flux_wb = water_bodies_management.get_abstractions(
						storage_wb, maximum_flux_wb)
					#print(maximum_flux_wb)
				

				# ratio of Etp, units of procesing are in meters
				ratio_etp = head[act_nodes] - z_extintion
				ratio_etp[ratio_etp < 0] = 0
				ratio_etp[vegetation.extintion_depth[act_nodes] > 0] = (
						ratio_etp[vegetation.extintion_depth[act_nodes] > 0]
						/(vegetation.extintion_depth[act_nodes])[
						vegetation.extintion_depth[act_nodes] > 0]
						)
				
				# calculate ratio of potential evapotranspiration from
				# groundwater
				ratio_etp[ratio_etp > 1] = 1

				
				
				# potention evapotranspiration ONLY over model domain
				if Kcdt is not None:
					PETh = Kcdt*PETh#[act_nodes]
					#PETh = Kcdt[act_nodes]*PETh#[act_nodes]
				# potential evapotranspiration for saturated zone
				#PETsz = PETh*ratio_etp
				# potential evapotranspiration for unsaturated zone
				#PETuz = PETh - PETsz
				PETuz = PETh.copy()# - PETsz
				#print(INF)
				# SOIL WATER BALANCE: Mestimate soil water balance-------
				# Units for fluxes are in mm, units of soil moisture [--]
				AET, PCR, theta[act_nodes], ROF= swb.run_swbm_one_step(
						INF,
						PETuz,
						np.ones_like(act_nodes),#Kc[act_nodes],
						soil.Ksat[act_nodes],
						soil.theta_sat[act_nodes],
						soil.theta_fc[act_nodes],
						soil.theta_wp[act_nodes],
						soil.c_SOIL[act_nodes],
						Duz0,
						theta[act_nodes]
						)
				
				# if rivers available, run the water balance in the riparaian
				# zone, otherwise skip code
				if riv_nodes.size > 0:
					# RIPARIAN WATER BALANCE -------------------------------------
					# all values and rates are ONLY valid for the riparian area
					# calculate riparial pet
					rpet_dt = PETuz[act_riv_nodes] - AET[act_riv_nodes]					
					
					# calculate riparian water deficit [mm]
					rsmd = (soil.theta_fc[riv_nodes] - rtheta)*rsoil.Droot[riv_nodes]
					rsmd[rsmd < 0] = 0

					# estimate available storage at riparian zone
					# change gw discharge from m to mm per unit rip. area
					rsmd, qriv, inf_rip_dt = swb_rip.water_deficit(
						baseflow[riv_nodes]*1000.0*topo.cell_to_rip_area_factor[riv_nodes],
						rpet_dt, rsmd)
					
					# change river saturated deficit units from mm to m3
					# also update saturatin deficit with saturated zone
					river_sat_deficit[riv_nodes] += (rsmd*0.001*
									  topo.area_bank_cells[riv_nodes])
					
					# THIS VALUES IS TRANFERED TO THE CELL AREA
					# update groundwater discharge at river cells
					# change units from mm to m
					baseflow[riv_nodes] = (qriv*
							topo.rip_to_cell_area_factor[riv_nodes]*0.001)
				

				

				# update infiltration excess to considers lakes
				# precipitation over lakes is directly added to the total storage
				# as recharge
				# find lakes
				#id_lakes = bathymetry 
				# add excess to recharge
				aux_rch = np.zeros_like(EXS[:])
				if id_lakes.size > 0:
					aux_rch[id_lakes] = EXS[id_lakes]
					# update infiltration excess
					EXS[id_lakes] = 0
				
				# Update infiltration excess
				#exs_dt = EXS+ROF#[env_state.act_nodes]
								
				# Add runoff from all sources - change all units to mm 
				runoff[act_nodes] = EXS + ROF + baseflow[act_nodes]*1000.0
				
				# ABSTRACTIONS SURFACEWATER ------------------------------
				# add data abstractions/sink/source points
				# all abstractions units should be in m3 (cubic meters)
				# positive values indicate flow in the river/pond
				# negative values indicate flow out of the river/ponds
				if fluxOF.data_set is not None:					
					# select row from dataframe and add to the excess component
					# change units of flow rate to depth (m3 to m)
					runoff[idFluxOF] += fluxOF.get_point_dataset_one_step(t_abs)*1000.00/topo.area_cells
				
				# add flux (abstractions) from water bodies to streams	
				if fluxWB.data_set is not None:					
					# select row from dataframe and add to the excess component
					# units should be in m
					runoff[idFluxWBout] += maximum_flux_wb
					#print(maximum_flux_wb)
					
				# RUNOFF: estimate runoff---------------------------------------
				
                # ***
                # This component needs to be run in parallel for each subdomain, and
                # the results need to be combined to update the model state. The runoff
                # component is a flow accumulation component, which means that it needs
                # to be run in a specific order, starting from the upstream cells and
                # moving downstream. The parallel execution can be implemented by creating
                # multiple sub components for each subdomain, and running them in parallel.
                # The results can be combined by summing the runoff from each sub component,
                # and updating the model state accordingly.
				# print(C)

				# all variables with containing length must be changed to meters [m]
				
				if runoff_parallel:
					# if rank == 0:
					# print("runoff_parallel")
					time1 = time.time()
					local_discharge = np.zeros_like(ro.discharge)
					# print("time1: ",time.time()-time1)
					local_trans_losses = np.zeros_like(ro.trans_losses)
					local_stage = np.zeros_like(ro.stage)
					local_ssz = np.zeros_like(ro.SSZ)

					for basin_id in local_basin_ids:
						basin_forcing = partools.extract_basin_forcing(
							basin_id,
							domains_ro,
							{
								'runoff': runoff,
								'riv_sat_deficit': river_sat_deficit,
								'AOF': AOF,
							},
						)
						basin_parameters = basis_runtime_parameters[basin_id]
						basin_component = basis_ro[basin_id]

						basin_component.run_runoff_one_step(
							basin_forcing['runoff']*0.001,
							basin_forcing['AOF'],
							basin_parameters['AOF_threshold'],
							basin_parameters['conductivity'],
							basin_parameters['decay'],
							basin_parameters['river_cells'],
							basin_parameters['area_cells'],
							basin_parameters['area_river'],
							basin_forcing['riv_sat_deficit'],
							None,
						)
						
						local_discharge = partools.combine_basin_results_into_world(
							basin_id,
							domains_ro,
							basin_component.discharge,
							world_data=local_discharge,
							world_grid_shape=runoff_grid_shape,
							flatten=True,
						)
						local_trans_losses = partools.combine_basin_results_into_world(
							basin_id,
							domains_ro,
							basin_component.trans_losses,
							world_data=local_trans_losses,
							world_grid_shape=runoff_grid_shape,
							flatten=True,
						)
						local_stage = partools.combine_basin_results_into_world(
							basin_id,
							domains_ro,
							basin_component.stage,
							world_data=local_stage,
							world_grid_shape=runoff_grid_shape,
							flatten=True,
						)
						local_ssz = partools.combine_basin_results_into_world(
							basin_id,
							domains_ro,
							basin_component.SSZ,
							world_data=local_ssz,
							world_grid_shape=runoff_grid_shape,
							flatten=True,
						)

					ro.discharge[:] = _allreduce_sum(comm, local_discharge)
					ro.trans_losses[:] = _allreduce_sum(comm, local_trans_losses)
					ro.stage[:] = _allreduce_sum(comm, local_stage)
					ro.SSZ[:] = _allreduce_sum(comm, local_ssz)
					#ro_ssz_global[:] = ro.SSZ
					# print("before C in runoff parallel")
					# print(C)
				else:
					ro.run_runoff_one_step(
						runoff*0.001,
						AOF, AOF_threshold,
						topo.conductivity,
						topo.decay,
						topo.river_cells,
						topo.area_cells,
						topo.area_river,
						river_sat_deficit,
						None)
					# print("before C in else runoff parallel")
					
					#ro_ssz_global[:] = ro.SSZ
				
				if riv_nodes.size > 0:
					# change transmission losses rate to riparian area, all units
					# must be in mm/dt
					
					# change units of volumetric rate flow to depth rate flow
					# change units from m to mm per unit rip. area
					tls_aux = ro.trans_losses[riv_nodes]*topo.volume_to_depth_factor_rip[riv_nodes]

					if lks is not None:
						# Move Transmission losses to reservoirs or lakes
						tls2lake = lks.compute_lakes_tributary_volume(tls_aux[water_bodies.ids_slks])

						# calculate water balance in lakes
						et_lks = lks.get_lakes_evaporation_volume(PET[water_bodies.ids_slks])

						# update lake storage
						lks.add_volume_to_lakes(et_lks.keys, tls2lake.values-et_lks.values)

					# aggregate all inputs to riparian unsaturated zone [mm]
					riv_infiltration = tls_aux + inf_rip_dt

					# estimate riparian water balance,
					# use Ksas of the channel in [mm/dt]
					rAET, rPCR, rtheta, rROF = swb_rip.run_swbm_one_step(
							riv_infiltration,#[riv_nodes],
							rpet_dt,
							np.ones_like(riv_nodes),#Kc[act_nodes],
							rsoil.Ksat[riv_nodes],
							rsoil.theta_sat[riv_nodes],
							rsoil.theta_fc[riv_nodes],
							rsoil.theta_wp[riv_nodes],
							rsoil.c_SOIL[riv_nodes],
							rsoil.Droot[riv_nodes],
							rtheta
							)
					
					# update focused recharge
					rPCR += rROF

					# transfer fluxes from riparian zone to model cells
					# lenght units are keept in mm
					rAET *= topo.rip_to_cell_area_factor[riv_nodes]
					rPCR *= topo.rip_to_cell_area_factor[riv_nodes]

					# update total recharge, umits [mm/dt]
					recharge[riv_nodes] += rPCR

					# update recharge with abstractions for water bodies
					# add flux (abstractions) from water bodies to streams	
					if fluxWB.data_set is not None:					
						# select row from dataframe and add to the excess component
						recharge[idFluxWB] += -maximum_flux_wb
				
				# correct hill slop fluxes to grid cells
				#swb.pcl_dt *= env_state.hill_factor
				#swb.aet_dt *= env_state.hill_factor
				
				
				# estimate total groundwater recharge, units in [mm/dt]
				recharge[act_nodes] += PCR + aux_rch# - abc.asz# [mm/dt]
				
				

				#### apply dumping to groundwater recharge
				###rech = Qusz.run_recharge_routing(soil, rech, Dusz)
				# this is an update for increasing evapranspiration in humid areas
				PETsz = (PETh - AET)# + rAET))*ratio_etp #this is to increase evapotranspiraiton rates
				

				if riv_nodes.size > 0:
					PETsz[act_riv_nodes] = (PETsz[act_riv_nodes] - rAET)# + rAET))*ratio_etp #this is to increase evapotranspiraiton rates
				
				PETsz = PETsz*ratio_etp																						  
				
				# temporal aggregation of fluxes for groundwater
				# this will allow to run the groundwater component
				# at different time steps
				etg_agg[act_nodes] += PETsz[:] # [mm/h]
				rch_agg += recharge[:] # [mm/dt]
				
				# save total catchment fluxes for water balance
				# Save soil interception variables
				#if env_state.av is not None:
				#	eca_mb.append(np.mean(Eca[env_state.act_nodes]))
				#	lai_mb.append(np.mean(LAI[env_state.act_nodes]))
				#	kc_mb.append(np.mean(Kc[env_state.act_nodes]))
				#	
				#	kcrip_mb.append(np.mean(Kcr[env_state.act_nodes]))
				#	ecar_mb.append(np.mean(Ecar[env_state.act_nodes]))
				#else:
				#	eca_mb.append(0)
				#	lai_mb.append(0)
				#	kc_mb.append(0)
				#	kcrip_mb.append(0)
				
				# add data abstractions/sink/source points
				# units should be in m3 (cubic meters)
				if fluxSZ.data_set is not None:					
					# select row from dataframe and add to the excess component
					# cange units from flow (m3) to depth in mm
					rch_agg[idFluxSZ] += fluxSZ.get_point_dataset_one_step(t_abs)*1000.0/topo.area_cells
				

				
				# GROUNDWATER --------------------------------------------------(Jose)
				# activate groundwater component (gw)
				if data_in.run_GW > 0:
					if dt_GW == data_in.dtSZ:
						# estimate and change recharge units
						# from mm/h --> m/h
						#print("Aquifer Start Head", head[idGW[0]])
						# run groundwater component
						#if data_in.run_GW > 1:
							# under development
							#gw.run_one_step_gw_2Layer(env_state, data_in.dtSZ/60,
							#	swb.tht_dt,	env_state.Droot*0.001)
						#else:
						
                        # ***
						# heads[isubdomain] from head for each subdomain,
                        # and baseflow[isubdomain] from baseflow for each subdomain

						# This component needs to be run in parallel for each subdomain, and
                        # the results need to be combined to update the model state.
						# [heads[isubdomain]] = > [heads_0, heads_1, heads_2, ...]
						# [baseflow[isubdomain]] = > [baseflow_0, baseflow_1, baseflow_2, ...]
						
                        # run in parallel for each subdomain, and combine results to update head and baseflow for the entire model domain
						gw_recharge = (rch_agg - etg_agg)*0.001
						# print("before gw_parallel")
						
						if gw_parallel:
							# print("gw_parallel")
							local_head = np.zeros_like(head)
							local_baseflow = np.zeros_like(baseflow)
							local_owner = np.zeros(topo.grid_size, dtype=np.int32)
							local_flux_chb = 0.0
							local_count = 0.0

							# head = exchange_halos(comm, head, region_halo_info, tag=0)
							# theta = exchange_halos(comm, theta, region_halo_info, tag=1)
							# ro.stage = exchange_halos(comm, ro.stage, region_halo_info, tag=2)

								
							# print("local_gw_region_idsxxx: ", local_gw_region_ids)
							for region_id in local_gw_region_ids:
								
								region_parameters = region_runtime_parameters_gw[region_id]
								# start1 = time.time()
								region_forcing = partools.extract_basin_forcing_halo(
									region_id,
									domains_gw,
									{
										'head': head,
										'theta': theta,
										'recharge': gw_recharge,
										'stage': ro.stage,
									},
									halo = 0
								)
								#print("time1: ", time.time()-start1)
								
								# head = exchange_halos(comm, head, region_halo_info[region_id])
								# theta = exchange_halos(comm, theta, region_halo_info[region_id])
								# stage = exchange_halos(comm, ro.stage, region_halo_info[region_id])

								# region_forcing = partools.extract_basin_forcing_with_halo(
								# 	region_domain,
								# 	{
								# 		'head': head,
								# 		'theta': theta,
								# 		'recharge': gw_recharge,
								# 		'stage': ro.stage,
								# 	},
								# )

								# print("region_id: ", region_id)
								# print(region_parameters['surface'].shape)
								# print(region_forcing['head'].shape)
								# print("run_one_step_gw")
								start2 = time.time()
								head_local, baseflow_local = region_gw[region_id].run_one_step_gw(
									region_parameters['grid'],
									region_parameters['surface'],
									region_parameters['bottom'],
									region_parameters['thickness'],
									region_parameters['bathymetry'],
									region_parameters['riv_elevation'],
									region_parameters['riv_nodes'],
									region_parameters['Sy'],
									region_parameters['Droot'],
									region_parameters['conductivity'],
									region_parameters['inodetype'],
									region_parameters['theta_sat'],
									region_parameters['theta_fc'],
									region_forcing['theta'],
									region_forcing['head'],
									region_forcing['recharge'],
									region_forcing['stage'],
									data_in.dtSZ/60,
									ids_lks=region_parameters['ids_lks'],
									sizes_lks=region_parameters['size_lks'],
									ids_max_depth_lks=region_parameters['ids_max_depth_lks'],
								)
								# print("time2: ", time.time()-start2)
								# start3= time.time()
								local_head = partools.combine_basin_results_into_world_halo(
									region_id,
									domains_gw,
									head_local,
									halo = 0,
									world_data=local_head,
									world_grid_shape=runoff_grid_shape,
									flatten=True,
								)
								#print("time3: ", time.time()-start3)
								# start4= time.time()
								local_baseflow = partools.combine_basin_results_into_world_halo(
									region_id,
									domains_gw,
									baseflow_local,
									halo = 0,
									world_data=local_baseflow,
									world_grid_shape=runoff_grid_shape,
									flatten=True,
								)
								#print("time4: ", time.time()-start4)
								# start5= time.time()
								local_owner = partools.combine_basin_results_into_world_halo(
									region_id,
									domains_gw,
									np.ones_like(head_local, dtype=np.int32),
									halo = 0,
									world_data=local_owner,
									world_grid_shape=runoff_grid_shape,
									flatten=True,
								)
								#print("time5: ", time.time()-start5)

								#################################################################################################
								
								# local_head = partools.combine_basin_results_into_world_with_halo(
								# 	basin_domain=region_domain,
								# 	basin_result=head_local,
								# 	global_array=global_head
								# ) #it's actually global head
								# local_baseflow = partools.combine_basin_results_into_world_with_halo(
								# 	basin_domain=region_domain,
								# 	basin_result=baseflow_local,
								# 	global_array=global_baseflow
								# )
								# local_owner = partools.combine_basin_results_into_world_with_halo(
								# 	basin_domain=region_domain,
								# 	basin_result=np.ones_like(head_local, dtype=np.int32),
								# 	global_array=global_owner
								# )
								
								
								local_flux_chb += region_gw[region_id].flux_at_CHB*region_parameters['active_count']
								local_count += float(region_parameters['active_count'])
								# print(C)
								# print(local_head)

							# print("global_head")
							start6 = time.time()
							global_head = _allreduce_sum(comm, local_head)
							# print("time6: ", time.time()-start6)
							# print(C)
							# print('gl',global_head)
							# print(C)
							# start7 = time.time()
							global_baseflow = _allreduce_sum(comm, local_baseflow)
							#print("time7: ", time.time()-start7)
							# start8 = time.time()
							global_owner = _allreduce_sum(comm, local_owner)
							#print("time8: ", time.time()-start8)
							
							head[global_owner > 0] = global_head[global_owner > 0]
							baseflow[global_owner > 0] = global_baseflow[global_owner > 0]
							
							# start9 = time.time()
							total_count = comm.allreduce(local_count, op=MPI.SUM)
							#print("time9: ", time.time()-start9)
							# start10 = time.time()
							flux_weighted = comm.allreduce(local_flux_chb, op=MPI.SUM)
							#print("time10: ", time.time()-start10)
							gw.flux_at_CHB = flux_weighted/total_count if total_count > 0 else 0.0
							
						else:
							head, baseflow = gw.run_one_step_gw(grid,
									topo.surface[:],
									aquifer.bottom,
									aquifer.thickness,
									topo.bathymetry,
									topo.riv_elevation,
									riv_nodes,
									aquifer.Sy,
									soil.Droot*0.001,
									topo.conductivity,
									aquifer.gwtype,
									soil.theta_sat,
									soil.theta_fc,
									theta,
									head,
									gw_recharge,
									ro.stage,
									data_in.dtSZ/60,
									ids_lks=water_bodies.ids_lks,
									sizes_lks=water_bodies.size_lks,
									ids_max_depth_lks=water_bodies.ids_max_depth_lks,
								)
							#gw.run_one_step_gw(env_state.grid, data_in.dtSZ/60,
							#	swb.tht_dt,	env_state.Droot*0.001)
						
                        # transfer subdomain results to the entire model domain
						# appends (heads[i] for i in subdomains) in head
						rch_agg = np.zeros(topo.grid_size)
						etg_agg = np.zeros(topo.grid_size)
						dt_GW = 0
					
					# time accumulator for gw	
					dt_GW += int(data_in.dt)
				
				# update soil moisture
				if data_in.run_GW > 0:

					Duz0, theta[act_nodes] = swb.run_soil_aquifer_one_step(
						topo.surface[act_nodes],
						head[act_nodes],#aquifer.head[act_nodes],
						soil.Droot[act_nodes],
						soil.theta_fc[act_nodes],
						soil.theta_wp[act_nodes],
						Duz0, theta[act_nodes]
						)
				
				# estimate groundwater storage change for delta t
				twsc = np.zeros_like(rain)
				twsc[act_nodes] = storage_uz_sz(
						topo.surface[act_nodes],
						topo.bathymetry[act_nodes],
						aquifer.bottom[act_nodes],
						soil.Droot[act_nodes]*0.001,
						soil.theta_sat[act_nodes],
						aquifer.Sy[act_nodes],
						head[act_nodes],
						theta[act_nodes]) - tws


                #  Store model outputs -----------------------------------------------
                # results should be stored at each time step for continental simulation.
                # Each process can be sent to different processors so there is not need
                # to wait or keep them in memory.
                
                # get all state and flux variables to grid storage
				if rank == 0:
					# print("data_in.save_netcdf: ", data_in.save_netcdf)
					if data_in.save_netcdf is True:
						grid_var.store_variables(PRE.date_sim_dt, t_pre,
							{"pre": rain[act_nodes], "pet": PET[act_nodes],
							"dis": ro.discharge[act_nodes],
							"aet": AET, "inf": INF, "run": runoff[act_nodes],
							"tht": theta[act_nodes],
							"rch": recharge[act_nodes], "egw": PETsz,
							"wte": head[act_nodes],
							"gdh": baseflow[act_nodes], "twsc": twsc[act_nodes],
							})

					# print(" vegetation.av: ",  vegetation.av)
					
					# store vegetation variables
					if vegetation.av is not None:
						grid_veg.store_variables(PRE.date_sim_dt, t_pre,
							{'pth': Pth, 'eca': Eca, 'scz': vegetation.Sc0_cn[act_nodes],
							#'lai': LAIdt, 'kc': Kcdt, 'av': vegetation.av
							})

					# print("grid_vmax.store_max: ",  grid_vmax.store_max)
					# store maximum values
					if grid_vmax.store_max is True:
						grid_vmax.store_variables(PRE.date_sim_dt, t_pre,
								{"pre": rain[act_nodes], "pet": PET[act_nodes],
								"aet": AET, "inf": INF, "run": runoff[act_nodes],
								"rch": recharge[act_nodes], "egw": PETsz,
								"gdh": baseflow[act_nodes],
								}
								)
					# print("grid_rmax.store_max: ",  grid_rmax.store_max)
					# store maximum values at streams locations
					if grid_rmax.store_max is True:
						if riv_nodes.size > 0:
							grid_rmax.store_variables(PRE.date_sim_dt, t_pre,
								{"dis": ro.discharge[riv_nodes]}
								)
					# print("water_bodies.ids_slks: ",  water_bodies.ids_slks)
					# store lake levels
					if water_bodies.ids_slks is not None:
						grid_lks.store_variables(PRE.date_sim_dt, t_pre,
								{"slks": lks.get_lakes_volumetric_states_list()
								}
								)
						
					#print("Aquifer SHead", head[idGW[0]])
					# get all fluxes and states at sampling points
					point_var.store_variables(PRE.date_sim_dt, t_pre,
						{"aet": AET[idOF[1]], "inf": INF[idOF[1]],
						"dis": ro.discharge[idOF[0]], "tht": theta[idUZ[0]],
						"rch": recharge[idGW[0]], "wte": head[idGW[0]],
						"gdh": baseflow[idGW[0]], "ssz": ro.SSZ[idOF[0]],
						"twsc": twsc[idGW[0]], "tls": ro.trans_losses[idOF[0]],
						}
						)
					
					# get mean total values for each flux and state
					total_var.store_variables(PRE.date_sim_dt, t_pre,
						{"pre":[np.mean(rain[act_nodes])],
						"pet":[np.mean(PET[act_nodes])],
						"run":[np.mean(runoff[act_nodes])],
						"aet":[np.mean(AET)],
						"inf":[np.mean(INF)],
						"tht":[np.mean(theta[act_nodes])],
						"rch":[np.mean(recharge[act_nodes])],
						"egw":[np.mean(PETsz)],
						"wte":[np.mean(head[act_nodes])],
						"gdh":[np.mean(baseflow[act_nodes])],
						"twsc":[np.mean(twsc[act_nodes])],
						"chb":[gw.flux_at_CHB],
						"tls":[np.mean(ro.trans_losses[act_nodes])],
						'eca': [np.mean(Eca)] if Eca is not None else [0],
						'scz': [np.mean(vegetation.Sc0_cn[act_nodes])] if vegetation.Sc0_cn[act_nodes] is not None else [0],
						'pth': [np.mean(Pth)] if Pth is not None else [0],
						'lai': [np.mean(LAIdt)] if LAIdt is not None else [0],
						'kc': [np.mean(Kcdt)] if Kcdt is not None else [1],
						'av': [np.mean(vegetation.av)] if vegetation.av is not None else [0],
						})
					
					# get mean total values for each flux and state of the riparian zone
					# print("riv_nodes.size: ", riv_nodes.size)
					if riv_nodes.size > 0:
						total_rpvar.store_variables(PRE.date_sim_dt, t_pre,
							{"etrp": [np.mean(rAET)],
							"fch": [np.mean(rPCR)],
							"tls": [np.mean(ro.trans_losses[riv_nodes])],
							"thtrp": [np.mean(rtheta)],
							"ssz": [np.mean(ro.SSZ[riv_nodes])]}
							)
						
						grid_rpvar.store_variables(PRE.date_sim_dt, t_pre,
							{"etrp": rAET, "fch": rPCR,
							"tls": ro.trans_losses[riv_nodes],
							"thtrp": rtheta,
							"ssz": ro.SSZ[riv_nodes]}
							)

					# get mean total values for each flux and state of water bodies
					# print("water_bodies.id_nodes: ", water_bodies.id_nodes)
					if water_bodies.id_nodes is not None:
						total_pndvar.store_variables(PRE.date_sim_dt, t_pre,
							{"epd": [np.mean(et_pnds)],
							"vpd": [np.mean(water_bodies.pnds_Vo)],
							"apd": [np.mean(aoz_pnds)],
							}
							)
						
						grid_pndvar.store_variables(PRE.date_sim_dt, t_pre,
							{"epd": et_pnds,
							"vpd": water_bodies.pnds_Vo,
							"apd": aoz_pnds,
							}
							)
					# print("idzone_info[2]: ", idzone_info[2])
					if idzone_info[2] is not None:
						zone_var.store_variables(PRE.date_sim_dt, t_pre,
							{"pre":utils.collapse_mean(rain[idzone_info[0]], idzone_info[2]),
							"pet":utils.collapse_mean(PET[idzone_info[0]], idzone_info[2]),
							"run":utils.collapse_mean(runoff[idzone_info[0]], idzone_info[2]),
							"aet":utils.collapse_mean(AET[idzone_info[1]], idzone_info[2]),
							"inf":utils.collapse_mean(INF[idzone_info[1]], idzone_info[2]),
							"tht":utils.collapse_mean(theta[idzone_info[0]], idzone_info[2]),
							"rch":utils.collapse_mean(recharge[idzone_info[0]], idzone_info[2]),
							"egw":utils.collapse_mean(PETsz[idzone_info[1]], idzone_info[2]),
							"wte":utils.collapse_mean(head[idzone_info[0]], idzone_info[2]),
							"gdh":utils.collapse_mean(baseflow[idzone_info[0]], idzone_info[2]),
							"twsc":utils.collapse_mean(twsc[idzone_info[0]], idzone_info[2]),
							#"chb":[gw.flux_at_CHB],
							"tls":utils.collapse_mean(ro.trans_losses[idzone_info[0]], idzone_info[2]),
							#'eca': [np.mean(Eca)] if Eca is not None else [0],
							#'scz': [np.mean(vegetation.Sc0_cn[act_nodes])] if vegetation.Sc0_cn[act_nodes] is not None else [0],
							#'pth': [np.mean(Pth)] if Pth is not None else [0],
							#'lai': [np.mean(LAIdt)] if LAIdt is not None else [0],
							#'kc': [np.mean(Kcdt)] if Kcdt is not None else [1],
							#'av': [np.mean(vegetation.av)] if vegetation.av is not None else [0],
							})

				# reinitiate recharge variable
				recharge[act_nodes] = 0.0

				# reinitiate river saturation deficit (m3)
				# activate only when groundwater is active
				if data_in.run_GW > 0:
					# apply only when river exist
					if riv_nodes.size > 0:
						river_sat_deficit[riv_nodes] = ((
							topo.riv_elevation[riv_nodes] - head[riv_nodes])*
							np.power(topo.grid_size, 2)*
							aquifer.Sy[riv_nodes])

						river_sat_deficit[river_sat_deficit < 0] = 0.0

				
				# update time steps indices
				t_pre += 1
				t_savi += 1
				t_kc += 1
				t_abs += 1
				
			t_eto += 1		
		

		
		# update progress bar
		# if progress_bar is not None:
		# 	progress_bar.update(1)
	
		t += 1
		# print(C)

	end = time.time()
	# print("start: ",start)
	# print("end: ",end)
	# print("elapsed time: ", end - start)
		
	# Close the progress bar
	if progress_bar is not None:
		progress_bar.close()

	if comm is not None:
		comm.Barrier()

	# print('is_root: ',is_root)
	# print(f"Rank: {rank}, Size: {comm.Get_size()}")
	if is_root:
		print("********************************** SAVING RESULTS **********************************")
		# if rank == 0:
		print(rank)
		save_model_outputs(data_in, total_var, point_var, zone_var, total_rpvar, total_pndvar,
						grid_var, grid_rmax, grid_vmax, grid_rpvar, grid_pndvar, grid_veg, grid_lks,
						grid, head, theta, ro.SSZ, rtheta, topo, water_bodies.pnds_Vo,
						act_nodes, riv_nodes, water_bodies.ids_slks, water_bodies.id_nodes,
						projection=data_in.PROJECTION )
		print("======================= ALL PROCESSES COMPLETED SUCCESSFULLY =======================")
# ---------------------------------------------------------------------
# Call script from external library	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run DRYP with JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	run_parDRYP(args.config_file)
# ---------------------------------------------------------------------