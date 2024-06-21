"""Gauss seidel for solving steady state conditions of groundwater models
"""
import numpy as np
def gauss_seidel_iteration(z, head, conductivity, fluxes, nodes, links_at_node, node_link_head, node_link_tail, w):
	"""
	Routine to solve the bussinesq equation through gaus seidel method
	this function does not solve the bussinesq equation, it only iterates
	through the different nodes
	
	Parameters
	-----
	nodes:			nodes to perform the calculation
	head:			array of head elevations (n)
	conductivity:	array of conductivity values at links [L2 T-1] (m)
	fluxes:			array of fluxes (e.g. recharge) [L3 T-1] (n)
	links_at_node:  array of link at each node, size n x 4
	node_link_head: array of link head nodes at each link (m)
	node_link_tail: array of link tail nodes at each link (m)
	w:				relaxation factor (1)
					w > 0 is over relaxation, w < 1 under relaxation
					
	Returns
	------
	head:			array of updated nodes
	"""
	
	# loop through each node across the model domain
	delta = [1, 1, 0, 0]
	
	for inode in nodes:
		
		if inode is not -1:
			## to be deleted
			##-----------------------------------
			#k = 0
			#ihead = 0
			#iconductivity = 0
			#if inode == 1013583:
			#	print(inode, head[inode])
			## loop thrugh each link conected to the node
			#for klink in links_at_node[inode]:
			#	
			#	# skip calculation if link is inactive
			#	if klink is not -1:
			#		if inode == 1013583:
			#			print(klink, conductivity[klink],
			#				delta[k], head[node_link_head[klink]],
			#				head[node_link_tail[klink]]
			#				)
			#		
			#					
			#	k = k + 1
			##------------------------------------------------		
			
			k = 0
			ihead = 0
			iconductivity = 0
			
			# loop thrugh each link conected to the node
			for klink in links_at_node[inode]:
				# skip calculation if link is inactive
				if klink is not -1:
					
					# calulate right had side of mass balance equatioh
					ihead += conductivity[klink]*(
						delta[k]*head[node_link_head[klink]]
						+ (1-delta[k])*head[node_link_tail[klink]]
						)
					iconductivity += conductivity[klink]
								
				k = k + 1
			
			# update node value by gauss method
			if iconductivity > 0:
				head[inode] = (1-w)*head[inode] + w*(ihead + fluxes[inode])/iconductivity
			
			# do not allow the head to go above the surface
			if head[inode] > z[inode]:
				head[inode] = z[inode]
			
			#	raise Exception("Nan values generate, stop solver")	
	return head