import numpy as np

def update_soil(z, zroot_u, zroot_l, 
		theta_sat_u, theta_fc_u, theta_u,
		theta_sat_l, theta_fc_l, theta_l,
		deltaS, head, Sy):
	""" Function to calculate soil gorundwater interaction,
	this function update soil storage when the water table
	raise or decrease.

	Parameters
	----------
	z:	surface elevation
	zroot_u:	root elevation top layer
	zroot_l:	root elevation bottom layer
	theta_sat_u:	saturated water content, upper layer
	theta_fc_u:		water contentat field capacity, upper layer
	theta_u:		water water content, upper layer
	theta_sat_l:	saturated water content, lower layer
	theta_fc_l:		water contentat field capacity, lower layer
	theta_l:		water water content, lower layer
	delta:	change in storage
	head:	water table elevation
	Sy:		aquifer specific yield

	Returns
	--------
	h: water table elevation
	"""
	#head_out = np.zeros_like(head)
	#print(type(theta_sat_u))
	if theta_sat_u is not np.ndarray:		
		for i, ihead in enumerate(head): 
			head[i] = update_2layer_soil(z[i], zroot_u[i], zroot_l[i],
			theta_sat_u, theta_fc_u, theta_u,
			theta_sat_l[i], theta_fc_l[i], theta_l[i],
			deltaS[i], ihead, Sy[i])
	else:
		for i in enumerate(head): 
			head[i] = update_2layer_soil(z[i], zroot_u[i], zroot_l[i],
			theta_sat_u[i], theta_fc_u[i], theta_u[i],
			theta_sat_l[i], theta_fc_l[i], theta_l[i],
			deltaS[i], head[i], Sy[i])
	#print(head)
	return head
	
def update_2layer_soil(z, zroot_u, zroot_l,
	theta_sat_u, theta_fc_u, theta_u,
	theta_sat_l, theta_fc_l, theta_l,
	deltaS, head, Sy):
	""" Function to calculate soil gorundwater interaction,
	this function update soil storage when the water table
	raise or decrease.

	Parameters
	----------
	z:	surface elevation
	zroot_u:	root elevation top layer
	zroot_l:	root elevation bottom layer
	theta_sat_u:saturated water conten of the upper layer [m3/m3]	
	theta_fc_u: water content at field capacity of the upper layer [m3'm3]
	theta_u:	water content at the upper layer 
	theta_sat_l:saturated water conten of the lower layer [m3/m3]	
	theta_fc_l: water content at field capacity of the lower layer [m3'm3]
	theta_l:	water content at the lower layer [m3'm3]
	delta:	change in storage [m]
	head:	water table elevation [m]
	Sy:		aquifer specific yield [-]
	
	Returns
	--------
	h: water table elevation
	"""
	
	if deltaS < 0:
		
		# when water table decrease
		if head > zroot_u:
			# Calculate storage available at each soil layer
			# initial water table above the root zone of theupper layer
			deltaSu = (head-zroot_u)*(theta_sat_u-theta_fc_u)
			deltaSl = (zroot_u-zroot_l)*(theta_sat_l-theta_fc_l)
		else:
			# initail water table below the rooting depth
			deltaSu = 0
			deltaSl = (head-zroot_l)*(theta_sat_l-theta_fc_l)
			if head < zroot_l:
				deltaSl = 0
				
		deltaS = np.abs(deltaS)		
		deltaSp = deltaS - deltaSu
		#print(deltaSp, deltaSl, deltaSl)
		
		# update head elevation
		if deltaSu > 0:
			
			# initial water table located in the upper soil layer
			if deltaSp < 0:
				# volume of water availible at the top soil is enough to satify
				# groundwater lateral flow
				# water table always within the upper soil layer
				head = head - deltaS/(theta_sat_u-theta_fc_u)
			else:
				# Volume of water in the top soil is not enough to satisfy gw
				# lateral flow, therefore, it has to be taken also from the bottom soil
				deltaSpp = deltaS - deltaSu - deltaSl
				if deltaSpp < 0:
					# volume of water from top and bottom soil layer is enough to
					# satisfy the gw lateral flow
					# water table falls to lower soil layer
					head = zroot_u - (deltaS-deltaSu)/(theta_sat_u-theta_fc_u)
				else:
					# volume of water availble at top and bottm soil layer is not
					# enough to satisfy the the gw lateral flow, therfore, wwater
					# is taken from the aquifer
					# water table fails below the lower soil layer
					head = zroot_l - deltaSpp/(Sy)
		else:
			# no water availble at the upper soil layer
			# water table located below the upper soil layer
			deltaSp = deltaS - deltaSl
			if deltaSl > 0:
				# water availble at the unsaturated zone for lateral gw flow
				# water table always located below the upper soil layer
				if deltaSp < 0:
					# volume of water availble at the bottom soil layer is enough
					# to satisfy the gw lateral flow
					# water table always within the lower soil layer
					head = head - (deltaS)/(theta_sat_l-theta_fc_l)
					#print(head, deltaS, deltaSp, deltaSl)
				else:
					# not enough water avalinle at the lower soil layer
					#water table falls below the lower layer
					head = zroot_l - (deltaS-deltaSl)/Sy
					#print(head, deltaS, deltaSp, deltaSl)
					#print(c)
			else:
				# no water available at the unsaturated zone
				# water table allways in the aquifer
				head = head - deltaS/Sy

	else:#--------------------------------------------------------------------------
		#! when water table increases, the avilable volume of water required to fill
		#! the total starage is estimated
		#! calulate the storage availble at each layer:
		#! deltaSu:	storage available at the upper layer
		#! deltaSl:	storage available at the lower layer
		#! deltaSa:	storage available at the aquifer layer
		if head > zroot_u:
			#! no storage availbe at all layers, therefore, waterwill be released
			#! from the subsurface to the surface
			#! Water table located between the first layer
			#! the aquifer and the lower layer is full
			deltaSl = 0
			deltaSa = 0
		else:
			if head > zroot_l:
				#! water table located between the lower layer
				#! the aquifer layer is full however, both the lower and upper layers,
				#! have some storage available
				#! have space to store water
				deltaSa = 0
				deltaSl = (zroot_u-head)*(theta_sat_l-theta_l)
				#deltaSu = (z-zroot_u)*(theta_sat_u-theta_fc_u)
			else:
				#! water table located in the saturated zone (aquifer)
				#! below the lower soil layer
				deltaSl = (zroot_u-zroot_l)*(theta_sat_l-theta_l)
				deltaSa = (zroot_l-head)*Sy
		
		# update water table
		deltaSp = deltaS - deltaSa
		
		if deltaSa > 0:
			# storage available at the aquifer layer
			# initial water table in the aquifer
			if deltaSp < 0:
				# available aquifer storage is not filled with lateral gw flow
				# water table always below the lower soil layer
				head = head + deltaS/Sy
			else:
				# available aquifer storage is not enough to store gw lateral flow
				# water table always above the aquifer
				# bottom soil layers remains unsaturated
				# calculate avaliable storage in the bottom soil layer
				deltaSpp = deltaSp - deltaSl
				if deltaSpp < 0:
					# enough storage available at the bottom soil layer
					# water table rises above the lower layer
					head = zroot_l + (deltaSp)/(theta_sat_l-theta_l)
				else:
					# not enough space available at the bnttom soil layer
					# soil layer becomes fully saturated
					# water table rises above the aquifer
					head = zroot_u + deltaSpp/(theta_sat_u-theta_u)
		else:
			# initial water table above the aquifer
			# 
			if deltaSl > 0:
				# storage availble at the bottom soil layer
				# calulate the volume of water needed at the upper layer
				deltaSpp = deltaS - deltaSl
				if deltaSpp < 0:
					# available storage in the bottom soil layer is enough to
					# store lateral gw flow
					# bottom soil layer remains unsaturated
					# water table within the lower layer
					head = head + deltaS/(theta_sat_l-theta_l)
					#print(head, deltaS, deltaSp, deltaSl)
				else:
					# available storage is not enough for storing lateral gw flow
					# bottom soil layer becomes saturated
					# water table rises to upper layer
					head = zroot_u + deltaSpp/(theta_sat_u-theta_u)
					#print(head, deltaS, deltaSp, deltaSl)
			else:
				# bottom soil layer is saturated
				# water table always in the upper layer
				head = head + deltaS/(theta_sat_u-theta_u)
				
	return head