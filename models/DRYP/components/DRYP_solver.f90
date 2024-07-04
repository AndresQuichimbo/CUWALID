MODULE solver
IMPLICIT NONE
CONTAINS
SUBROUTINE gauss_seidel_iteration(head, surface, conductivity,&
fluxes, nodes, links_at_node, node_link_head, node_link_tail, w)
!!"""Routine to solve the bussinesq equation through gaus seidel
!!method this function does not solve the bussinesq equation, it
!!only iterates through the different nodes
!!PYTHON INDEXES CAN NOT BE PASSED DIRECTLY TO THIS FUNCTION
!!THEREFORE, CHANGES SHOULD BE MADE IN ORDER TO CONSIDER INDEXES
!!GREATHER THAN 0
!!INPUT:
!!-----
!!nodes:		nodes to perform the calculation
!!surface:      surface elevation (n)
!!head:			array of head elevations (n)
!!conductivity:	array of conductivity values at links [L2 T-1] (m)
!!fluxes:		array of fluxes (e.g. recharge) [L3 T-1] (n)
!!links_at_node:  array of link at each node, size n x 4
!!node_link_head: array of link head nodes at each link (m)
!!node_link_tail: array of link tail nodes at each link (m)
!!w:				relaxation factor (1)
!!				w > 0 is over relaxation, w < 1 under relaxation
!!OUTPUT:
!!------
!!head:			array of updated nodes
!!"""
REAL, INTENT(IN) :: conductivity(:)
REAL, INTENT(IN) :: fluxes(:)
REAL, INTENT(IN) :: surface(:)
INTEGER, INTENT(IN) :: links_at_node(:,:)
INTEGER, INTENT(IN) :: nodes(:)
INTEGER, INTENT(IN) :: node_link_head(:)
INTEGER, INTENT(IN) :: node_link_tail(:)
REAL, INTENT(INOUT) :: head(:)
INTEGER :: i, k, link(4), nnodes, inode, delta(4), klink
REAL :: ihead, iconductivity, w

!# loop through each node across the model domain
delta = [1, 1, 0, 0]

!# find number of nodes
nnodes = SIZE(nodes)
!# loop through all nodes
DO i = 1, nnodes, 1
inode = nodes(i)
!# check if node is active
! active nodes have values greated than zero
IF (inode .ne. 0) THEN
ihead = 0
iconductivity = 0
!# select nodes at link
link = links_at_node(inode,:)
!# loop thrugh each link conected to the node
DO k = 1, 4, 1
!# skip calculation if link is inactive
klink = link(k)
IF (klink .ne. 0) THEN
!# calulate right had side of mass balance equatioh
ihead = ihead + conductivity(klink) &
* (delta(k)*head(node_link_head(klink)) &
+ (1-delta(k))*head(node_link_tail(klink)))
!# accumulate conductivity
iconductivity = iconductivity + conductivity(klink)
END IF
END DO
END IF
! update node value by gauss method
! do not update if the conductivity is 0 (it will return an
! error
IF (iconductivity .gt. 0) THEN
head(inode) = (1-w)*head(inode) + w*(ihead + fluxes(inode))&
/iconductivity
END IF
!do not allow the water table to rise above the surface
IF (head(inode) .gt. surface(inode)) THEN
head(inode) = surface(inode)
END IF
END DO
END SUBROUTINE
END MODULE
