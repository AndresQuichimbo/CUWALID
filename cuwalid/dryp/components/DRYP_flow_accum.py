"""Flow accumulator DRYP
"""
import numpy as np
from landlab.components.flow_accum import flow_accum_bw#, make_ordered_node_array
from landlab.core.utils import as_id_array
#from landlab import RasterModelGrid
from landlab.components import FlowDirectorD8

#Kloss = None
class runoff_routing(object):
    """Function to discharge and transmission losses discharge.
    Running run_one_step() results in the following to occur:
        1. Flow directions are updated (unless update_flow_director is set
           as False).
        2. Intermediate steps that analyse the drainage network topology
           and create datastructures for efficient drainage area and discharge
           calculations.
        3. Calculation of discharge and transmission losses.
    """

    def __init__(self, grid, grid_size, surface, FlowDirection,
                 Ksat, decay, riv_width, riv_length):
        """initialization of flow routing component
        
        Parameters
        ----------
        grid : landlab model grid environment
        grid_size : int
            grid size, length of grid arrays
        conductivity : numpy array of float
            channel hydraulic conductivity (m2/dt) [L2 T-1]
        Q_ini : numpy array
            initial volume of water available at the channel [m3] [L3]
        cth_area : numpy array
            path_Qo, it reduces or increases the area
        decay : numpy array
            river decay parameter (1/dt)
        river_cell : numpy array
            river cells, 0 indicate no river in the cell
        area_cells : numpy array
            cell area?
        AOF_threshold : numpy array
            Maximum volume of water available for abstraction

        Returns
        -------
        python object

        """
        # Creates numpy arrays for passing model variables
        Create_parameter_WV(self, Ksat, decay, riv_width, riv_length)
        
        self.discharge = np.zeros(grid_size)
        self.Q_ini = np.zeros(grid_size)
        self.trans_losses = np.zeros(grid_size)
        self.stage = np.zeros(grid_size)
        
        self.carea = None
        
        surface_aux = np.array(surface, dtype=np.float64)
        # 1. Check if flow director is needed
        if FlowDirection is None:
            if 'aux_grid' not in grid.at_node:
                grid.add_field("aux_grid", surface_aux, at="node")#, dtype=np.float64)
            else:
                grid.at_node['aux_grid'][:] = surface_aux[:]
            fd = FlowDirectorD8(grid, 'aux_grid')
            fd.run_one_step()
            # 2. Creates drainage networks, flowpaths and id arrays
            # a value of 1 must be added to change from python to forttran
            self.r = as_id_array(grid["node"]["flow__receiver_node"])
        else:
            self.r = as_id_array(FlowDirection)
        #nd = as_id_array(flow_accum_bw._make_number_of_donors_array(self.r))
        #delta = as_id_array(flow_accum_bw._make_delta_array(nd))
        #D = as_id_array(flow_accum_bw._make_array_of_donors(self.r, delta))
        self.s = as_id_array(flow_accum_bw.make_ordered_node_array(self.r))
        #self.carea = find_drainage_area(self.s, self.r,
        #            area_cells,
        #            grid.boundary_nodes)
        
        
    def run_runoff_one_step(self, runoff, AOF, AOF_threshold, conductivity,
             decay, river_cell, area_cells, area_river, river_sat_deficit,
             boundary_nodes):
        """Function to make FlowAccumulator calculate drainage area and discharge.
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
        runoff:            runoff at each model cell, including base flow
                        at channel cells (m/dt) [L T-1]
        conductivity:    channel hydraulic conductivity (m2/dt) [L2 T-1]
        Q_ini:            inital volume of water available at the channel [m3] [L3]
        cth_area:        path_Qo, it reduces or increases the area
        decay:            river decay parameter (1/dt)
        river_cell:        river cells, 0 indicate not river in the cell
        area_cells:        cell area?
        AOF_threshold:    Maximum volume of water available for abstraction
        Parameters
        ------
        discharge:    volumetric flow at each cell (m3) [L3]
        Q_ini:        inital volume of water available at the channel [m3] [L3]
        Trans_losses: Transmission lossses at river cells [m3] [L3]
        aof:        River flow abstraction [mm] [L]
        """
        
        #env_state.grid.at_node['AOF'][:] = aof
        #act_nodes = env_state.act_nodes
        
        # Update runoff with all inputs:
        # Runoff in units [m]
        #env_state.grid.at_node['runoff'][act_nodes] = (
        #        exs[act_nodes]*0.001*env_state.cth_area[act_nodes]
        #        + (env_state.SZgrid.at_node['discharge'][act_nodes])
        #        )
        
        # create array with bolean values for running streamflow routing
        #check_dry_conditions = len(np.where(
        #        (env_state.grid.at_node['runoff'][act_nodes]
        #        + env_state.grid.at_node['Q_ini'][act_nodes]
        #        ) > 0.0)[0])
        
        check_dry_condition = len(np.where(runoff > 0)[0])

        if check_dry_condition > 0:
            # run this section for any runoff
            # this function return
            # discharge, QTL, Q_ini, Q_aof
            self.discharge, self.trans_losses, self.Q_ini, Qaof = (
                find_discharge_and_losses(
                self.s, self.r,
                runoff,#Qw
                conductivity, #Criv
                decay, #Kt
                self.Q_ini, #Q_ini
                river_cell, #riv
                AOF, #Qaof
                AOF_threshold, #Qaoft
                river_sat_deficit, #riv_std
                self.par_3, #P3
                self.par_4, #P4
                area_cells,
                boundary_nodes
                ))
                
            # Update landlab grids of environmental states/fluxes
            #env_state.grid.at_node["surface_water__discharge"][:] = discharge
            #env_state.grid.at_node['Transmission_losses'][:] = QTL
            #env_state.grid.at_node['Q_ini'][:] = Q_ini
            #env_state.grid.at_node['AOF'][:] = Qaof
            
            #env_state.grid.at_node['AOF'][:] = aux[3] #aof
            #print(discharge[23], QTL[23], Q_ini[23])
            #self.dis_dt[act_nodes] = np.array(
            #        env_state.grid.at_node["surface_water__discharge"][act_nodes])
            
            self.discharge[self.discharge < 0] = 0.0
            
        else:
            # no runoff over the entire cells
            self.trans_losses[:] = 0.0
            self.discharge[:] = 0                
            noflow = 0
        
        # save runoff for mass balance
        #self.run_dt = np.zeros(grid_size)
        #self.run_dt[act_nodes] = np.array(
        #        env_state.grid.at_node['runoff'][act_nodes])
        
        # get transmission losses in [mm]
        #self.tls_dt = np.array(
        #        env_state.grid.at_node['Transmission_losses']
        #        *1000.0/env_state.area_cells)
        
        # get transmission losses in [m3]
        #self.tls_flow_dt = np.array(
        #        env_state.grid.at_node['Transmission_losses'])
        
        # get channel storage in [mm]
        #self.qfl_dt[act_nodes] = np.array(
        #        env_state.grid.at_node['Q_ini'][act_nodes]
        #        *1000.0/env_state.area_cells[act_nodes])
        #print(self.tls_dt[act_nodes])

        self.stage[area_river > 0] = (self.discharge[area_river > 0]
                /area_river[area_river > 0])
        self.stage = self.stage*river_cell
        #        env_state.grid.at_node['runoff'][act_nodes])


class watershed(object):
    """Function to delineate basins. This function needs to be initialized
    
    by providing a landlab grid, a surface elevation, and/or a flow
    direction map. When a flow direction is provided, the surface elevation
    is not required.

    This funtion will output a numpy 1D array.

    Running get_watershed(outlet) results in the following to occur:
        1. Flow directions are updated (unless update_flow_director is
        provided).
        2. Intermediate steps that analyse the drainage network topology
        only if flow direrection is not provided. This function will 
        create datastructures for efficient drainage area calculations.
        3. Basin delineation based on find watershed algorithm.
    """

    def __init__(self, grid, surface, FlowDirection=None):
        """initialization of flow routing component
        
        Parameters
        ----------
        grid :    landlab model grid environment
            model grid
        grid_size : int
            grid size, leng of grid arrays

        Returns
        -------

        """
        surface_aux = np.array(surface, dtype=np.float64)
        # 1. Check if flow director is needed
        if FlowDirection is None:
            if 'aux_grid' not in grid.at_node:
                grid.add_field("aux_grid", surface_aux, at="node")#, dtype=np.float64)
            else:
                grid.at_node['aux_grid'][:] = surface_aux[:]
            fd = FlowDirectorD8(grid, 'aux_grid')
            fd.run_one_step()
            # 2. Creates drainage networks, flowpaths and id arrays
            # a value of 1 must be added to change from python to forttran
            self.r = as_id_array(grid["node"]["flow__receiver_node"])
        else:
            self.r = as_id_array(FlowDirection)
        #nd = as_id_array(flow_accum_bw._make_number_of_donors_array(self.r))
        #delta = as_id_array(flow_accum_bw._make_delta_array(nd))
        #D = as_id_array(flow_accum_bw._make_array_of_donors(self.r, delta))
        self.s = as_id_array(flow_accum_bw.make_ordered_node_array(self.r))
        
    def get_watersheds(self, outlet):
        """Function call find_watershed to perforn the basin delineation.
        
        Parameters
        ----------
        outlet:    numpy array
            raster with cell specifiying the basin outlet
        
        Returns
        -------
        basin :    numpy array of int
            numpy array containg outlet values as basin (1D array)
        """
        return find_watersheds(self.s, self.r, outlet, boundary_nodes=None)

def Create_parameter_WV(self, Ksat, decay, riv_width, riv_length):#, kKloss):
    """additional parameters to save computational time

    Parameters
    ----------
    Ksat_ch: numpy array
        saturated hydraulic conductivity [m/dt]
    decay_flow: numpy array
        exponential factor -> residence time
    SS_loss: numpy array
        transmission losses at steady state
    river_width: numpy array
        channel width

    Returns
    -------
    par_3: numpy array
        grid variable tp estimate time
    par_4: numpy array
        grid variable to estimate transmission losses
    """
    # Calculate parameter p4 for transmission losses estimation
    self.par_4 = 2.0*Ksat/(decay*riv_width)
    
    # Calculate parameter p3 for estimating time to get dry
    # conditions in the channel
    self.par_3 = Ksat*riv_width*riv_length/(riv_width-2*Ksat)
    
    return


def find_drainage_area(s, r, node_cell_area=1.0, boundary_nodes=None):

    """Calculate the drainage area and water discharge at each node, permitting
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

    tuple of ndarray: drainage area and discharge

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

def find_watersheds(s, r, outlet, boundary_nodes=None):

    """Calculate the drainage area and water discharge at each node, permitting
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
    outlet: raster with the location of basin outlet
    
    Returns
    -------
    tuple of ndarray: drainage area and discharge

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
    basin = np.zeros(npoint, dtype=int) + outlet
    #discharge = np.zeros(npoint, dtype=int) + node_cell_area
    # note no loss occurs at a node until the water actually moves along a link
    
    # Optionally zero out drainage area and discharge at boundary nodes
    if boundary_nodes is not None:
        basin[boundary_nodes] = 0
    
    # Iterate forward through the list, which means we work from downstream
    # to upstream
    for i in range(npoint - 1):
        donor = s[i]
        recvr = r[donor]

        if donor != recvr:
            if basin[recvr] > 0:
                basin[donor] = basin[recvr]
                
    return basin

def find_discharge_and_losses(s, r, runoff, Criv, Kt,
                              Q_ini, riv, Q_aof, Q_aoft, riv_std, P3, P4,
                              node_cell_area, boundary_nodes):
    # node_cell_area=1.0, boundary_nodes=None):

    """Calculate the drainage area and water discharge at each node, permitting
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

    l : ndarray of int
        Link to receiver node IDs for each node

    loss_function : Python function(Qw, nodeID, linkID, grid)
        Function dictating how to modify the discharge as it leaves each node.
        nodeID is the current node; linkID is the downstream link, grid is a
        ModelGrid. Returns a float.

    grid : Landlab ModelGrid (or None)
        A grid to enable spatially variable parameters to be used in the loss
        function. If no spatially resolved parameters are needed, this can be
        a dummy variable, e.g., None.

    node_cell_area : float or ndarray
        Cell surface areas for each node. If it's an array, must have same
        length as s (that is, the number of nodes).

    runoff : float or ndarray
        Local runoff rate at each cell (in water depth per time). If it's an
        array, must have same length as s (that is, the number of nodes).

    boundary_nodes: list, optional
        Array of boundary nodes to have discharge and drainage area set to zero.
        Default value is None.

    Returns
    -------
    tuple of ndarray
        drainage area and discharge

    Notes
    -----
    - If node_cell_area not given, the output drainage area is equivalent
      to the number of nodes/cells draining through each point, including
      the local node itself.

    - Give node_cell_area as a scalar when using a regular raster grid.

    - If runoff is not given, the discharge returned will be the same as
      drainage area (i.e., drainage area times unit runoff rate).

    - If using an unstructured Landlab grid, make sure that the input
      argument for node_cell_area is the cell area at each NODE rather than
      just at each CELL. This means you need to include entries for the
      perimeter nodes too. They can be zeros.

    - Loss cannot go negative.

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
    
    QTL = np.zeros_like(runoff)

    # Initialize the drainage_area and discharge arrays. Drainage area starts
    # out as the area of the cell in question, then (unless the cell has no
    # donors) grows from there. Discharge starts out as the cell's local runoff
    # rate times the cell's surface area.
    #drainage_area = np.zeros(npoint, dtype=int) + node_cell_area
    discharge = node_cell_area * runoff
    # note no loss occurs at a node until the water actually moves along a link
    
    # Optionally zero out drainage area and discharge at boundary nodes
    if boundary_nodes is not None:
        discharge[boundary_nodes] = 0
    
    # Iterate backward through the list, which means we work from upstream to
    # downstream.
    for i in range(npoint - 1, -1, -1):
        donor = s[i]
        recvr = r[donor]
        if donor != recvr:
            #print('a',discharge[donor])    
            # this function calculate:
            # discharge_remaining, Q_TLp, Q_inip, Q_aofp    
            aux = TransLossWV(
                    discharge[donor],
                    Criv[donor],
                    Kt[donor],
                    #QTL[donor],
                    Q_ini[donor],
                    riv[donor],
                    Q_aof[donor],
                    Q_aoft[donor],
                    riv_std[donor],
                    P3[donor], P4[donor]
                    )
                
            discharge[recvr] += aux[0]#discharge_remaining
            QTL[donor] = aux[1]#Q_TLp
            Q_ini[donor] = aux[2]#Q_inip
            Q_aof[donor] = aux[3]#Q_aofp
            #print(aux)
    return discharge, QTL, Q_ini, Q_aof
    #return np.array([discharge, QTL, Q_ini, Q_aof])

#@jit(nopython=True)
def TransLossWV(Qw, Criv, Kt, Q_ini,
                riv, Qaof, Qaoft, riv_std, P3, P4):
    """Transmission losses function
    
    Parameters
    ----------
    Qw :        flow entering the cell
    Kloss :        Transmission losses factor
    Criv :        Conductivity
    Kt :        Decay parameter
    QTL :        Transimission losses
    Q_ini :        Initial flow
    riv :        river cell id
    Qaof :        Abstraction flux
    Qaoft :        Threshold abstraction
    riv_std :    River saturation deficit
    P3 :        Parameter
    P4 :        Parameter
    
    Returns
    -------
    Qout :        flow leaving the cell
    QTL :        Transimission losses
    Q_ini :        Initial flow
    Qaof :        Abstraction flux
    """
    Qout = Qw    
    if riv != 0:        
        Qin = (Qw+Q_ini)
        # abstractions, it can be modified
        if Qin <= Qaof:
            Qaof = Qaoft*Qin
        #Qin += -Qaof
            
        Q_ini = 0
        QTL = 0
        
        if Qin > 0.0:        
            if riv_std <= 0.0:        
                aux = exp_decay_wp(Qin, Kt)
                Qout = aux[0]
                Qo = aux[1]
                TL = 0                
            else:
                #Con = np.array(Criv)
                aux_l = exp_decay_loss_wp(Criv, Qin, Kt, P3, P4)
                
                #print(aux_l)
                Qout = aux_l[0]
                TL = aux_l[1]
                Qo = aux_l[2]
                                
                if TL > riv_std:                    
                    Qo += TL-riv_std
                    TL = riv_std
            
            Q_ini = Qo            
            QTL = TL
        
    else:
        Q_ini = 0.0
        QTL = 0.0
    return np.array([Qout, QTL, Q_ini, Qaof])
    #return Qout, QTL, Q_ini, Qaof

def exp_decay_loss_wp(TL, Qin, k, P3, P4):
    """Calculate transmission losses, flow leaving the cell, and
    channel storage
    
    Parameters
    ----------
    TL:        steady-state transmission losses [m2/dt]
    Qin:    Total amount of water entering the cell [m3]
    k:        decay factor - time residence [1/dt]
    par_3:    grid variable tp estimate time
    par_4:    grid variable to estimate transmission losses
    
    Returns
    -------
    Qout:    flow leaving the cells [m3/dt]
    Qtl:    transmission losses [m3/dt]
    Sch:    storage [m3]
    """
    Qout, Qo = 0, 0
    
    # Calcualte the time to reach dry condition on
    # the stream
    t = -(1/k)*np.log(P3/(Qin*k))
    
    # test if channel dry-up during the time step
    if t > 0:    
        if t > 1:        
            # Dry conditions are not developed
            t = 1
        
        # potential amount of water leaving the cell
        Q1 = Qin*(1-np.exp(-k*t))        
        
        # transmission losses
        Qtl = Qin*k*P4*(1-np.exp(-k*t))+TL*t    
        
        # water leaving the cell
        Qout = Q1 - Qtl
    
    # test     
    if t >= 1:
        # water stored in the channel
        Sch = Qin-Q1
    else:
        # channel get dry, no storage
        Sch = 0.0        
        Qtl = Qin - Qout
        
    return np.array([Qout, Qtl, Sch])

#@jit(nopython=True)
def exp_decay_wp(Qin, k):
    """Calculate flow leaving the cell and channel storage
    
    Parameters
    ----------
    Qin:    Total amount of water entering the cell [m3]
    k:        decay factor - time residence [1/dt]
        
    Returns
    -------
    Qout:    flow leaving the cells [m3/dt]
    Sch:    storage [m3]
    """
    Qout = Qin*(1-np.exp(-k))
    Sch = Qin-Qout
    
    return np.array([Qout, Sch])