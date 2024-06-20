MODULE uz_sz_interaction
IMPLICIT NONE
CONTAINS
SUBROUTINE update_soil(z, zroot_u, zroot_l, theta_sat_u, theta_fc_u,&
theta_u, theta_sat_l, theta_fc_l, theta_l, deltaS, Sy, head)
!!""" Function to calculate soil gorundwater interaction,
!!this function update soil storage when the water table
!!raise or decrease.
!!INPUTS:
!!-------
!!z:	    surface elevation (maximum elevation of the water level)
!!zroot_u:	root elevation top layer
!!zroot_l:	root elevation bottom layer
!!theta_sat_u:  Saturted water content of the upper layer	
!!theta_fc_u:   Water content at field capacity of upper layer
!!theta_u:      water content of the upper layer
!!theta_sat_l:  Saturted water content of the lower layer	
!!theta_fc_l:   Water content at field capacity of lower layer
!!theta_l:      water content of the lower layer
!!delta:	change in storage
!!head:	    water table elevation
!!Sy:		aquifer specific yield
!!OUTPUTS:
!!--------
!!h: water table elevation
!!"""
REAL, INTENT(IN) :: z(:)
REAL, INTENT(IN) :: zroot_u(:)
REAL, INTENT(IN) :: zroot_l(:)
REAL, INTENT(IN) :: theta_sat_u(:)
REAL, INTENT(IN) :: theta_fc_u(:)
REAL, INTENT(IN) :: theta_u(:)
REAL, INTENT(IN) :: theta_sat_l(:)
REAL, INTENT(IN) :: theta_fc_l(:)
REAL, INTENT(IN) :: theta_l(:)
REAL, INTENT(IN) :: deltaS(:)
REAL, INTENT(IN) :: Sy(:)

REAL, INTENT(INOUT) :: head(:)
INTEGER :: i, npoint, npointtp
REAL :: ihead

npoint = SIZE(z)
npointtp = SIZE(theta_sat_u)

! Check if saturated water content of the upper layer is provided
IF (npointtp .ne. 1) THEN
DO i = 1, npoint, 1
CALL UPDATE_2LAYER_SOIL(zroot_u(i), zroot_l(i), theta_sat_u(i),&
theta_fc_u(i), theta_u(i), theta_sat_l(i), theta_fc_l(i), theta_l(i),&
deltaS(i), Sy(i), head(i))
END DO
!ELSE
!!! Check if saturated water content of the upper layer is provided
!DO i = 1, npoint, 1
!CALL UPDATE_2LAYER_SOIL(zroot_u(i), zroot_l(i), theta_sat_u,&
!theta_fc_u, theta_u, theta_sat_l(i), theta_fc_l(i), theta_l(i),&
!deltaS(i), Sy(i), ihead)
!END DO
End IF
END SUBROUTINE

!!======================================================================
!! SUBROUTINE for layered soil parameters
!!======================================================================	
!
SUBROUTINE UPDATE_2LAYER_SOIL(zroot_u, zroot_l, theta_sat_u,&
theta_fc_u, theta_u, theta_sat_l, theta_fc_l, theta_l, deltaSin, Sy, head)
!!""" Function to calculate soil gorundwater interaction,
!!this function update soil storage when the water table
!!raise or decrease.
!!INPUTS:
!!-------
!!z:	surface elevation
!!zroot_u:	root elevation top layer
!!zroot_l:	root elevation bottom layer
!!theta_sat_u:	
!!theta_fc_u:
!!theta_u:
!!theta_sat_l:
!!theta_fc_l:
!!theta_l:
!!delta:	change in storage
!!head:	water table elevation
!!Sy:		aquifer specific yield
!!OUTPUTS:
!!--------
!!h: water table elevation
!!"""
REAL, INTENT(IN) :: zroot_u, zroot_l
REAL, INTENT(IN) :: theta_sat_u, theta_fc_u, theta_u
REAL, INTENT(IN) :: theta_sat_l, theta_fc_l, theta_l, Sy
REAL, INTENT(IN) :: deltaSin

REAL, INTENT(INOUT) :: head

REAL :: deltaS, deltaSa, deltaSu, deltaSl, deltaSpp, deltaSp

!PRINT *, 'Hello, World!'

deltaS = deltaSin
! ---------------------------------------------------------------
IF (deltaS .lt. 0) THEN
!when water table decreases -----------------------------
IF (head .gt. zroot_u) THEN
! Calculate storage available at each soil layer
! initial water table above the root zone of theupper layer
deltaSu = (head-zroot_u)*(theta_sat_u-theta_fc_u)
deltaSl = (zroot_u-zroot_l)*(theta_sat_l-theta_fc_l)
ELSE
! initail water table below the rooting depth
! therefore the storage in the upper layer is zero
deltaSu = 0
deltaSl = (head-zroot_l)*(theta_sat_l-theta_fc_l)
IF (head .lt. zroot_l) THEN
deltaSl = 0
END IF
END IF

deltaS = ABS(deltaSin)
deltaSp = deltaS - deltaSu
!print(deltaSp, deltaSl, deltaSl)
! update head elevation
IF (deltaSu .gt. 0) THEN
! initial water table located in the upper soil layer
IF (deltaSp .lt. 0) THEN
! volume of water availible at the top soil is enough to satify
! groundwater lateral flow
! water table always within the upper soil layer
head = head - deltaS/(theta_sat_u-theta_fc_u)
ELSE
! Volume of water in the top soil is not enough to satisfy gw
! lateral flow, therefore, it has to be taken also from the bottom soil
deltaSpp = deltaS - deltaSu - deltaSl
IF (deltaSpp .lt. 0) THEN
! volume of water from top and bottom soil layer is enough to
! satisfy the gw lateral flow
! water table falls to lower soil layer
head = zroot_u - (deltaS-deltaSu)/(theta_sat_u-theta_fc_u)
ELSE
! volume of water availble at top and bottm soil layer is not
! enough to satisfy the the gw lateral flow, therfore, wwater
! is taken from the aquifer
! water table fails below the lower soil layer
head = zroot_l - deltaSpp/(Sy)
!PRINT "(f12.4)", head, deltaS, deltaSp, deltaSl
END IF
END IF
ELSE
! no water availble at the upper soil layer
! water table located below the upper soil layer
deltaSp = deltaS - deltaSl
IF (deltaSl .gt. 0) THEN
! water availble at the unsaturated zone for lateral gw flow
! water table always located below the upper soil layer
IF (deltaSp .lt. 0) THEN
! volume of water availble at the bottom soil layer is enough
! to satisfy the gw lateral flow
! water table always within the lower soil layer
head = head - (deltaS)/(theta_sat_l-theta_fc_l)
ELSE
! not enough water available at the lower soil layer
! water table falls below the lower layer
head = zroot_l - (deltaS-deltaSl)/Sy
END IF
ELSE
! no water available at the unsaturated zone
! water table allways in the aquifer
head = head - deltaS/Sy
!PRINT "(f12.4)", head, deltaS, deltaSp, deltaSl
END IF
!print(head)
END IF
ELSE
! ---------------------------------------------------
! when water table increases, the avilable volume of water required to fill
! the total starage is estimated
! calulate the storage availble at each layer:
! deltaSu:	storage available at the upper layer
! deltaSl:	storage available at the lower layer
! deltaSa:	storage available at the aquifer layer
! when water table increases
IF (head .gt. zroot_u) THEN
! no storage availbe at all layers, therefore, waterwill be released
! from the subsurface to the surface
! Water table located between the first layer
! the aquifer and the lower layer is full
deltaSl = 0
deltaSa = 0
ELSE
IF (head .gt. zroot_l) THEN
! water table located between the lower layer
! the aquifer layer is full however, both the lower and upper layers,
! have some storage available
! have space to store water
deltaSa = 0
deltaSl = (zroot_u-head)*(theta_sat_l-theta_l)
ELSE
! water table located in the saturated zone (aquifer)
! below the lower soil layer
deltaSl = (zroot_u-zroot_l)*(theta_sat_l-theta_l)
deltaSa = (zroot_l-head)*Sy
END IF
END IF
! update water table
deltaSp = deltaS - deltaSa
!PRINT "(f12.4)", head, deltaS, deltaSp, deltaSl
IF (deltaSa .gt. 0) THEN
! storage available at the aquifer layer
! initial water table in the aquifer
IF (deltaSp .lt. 0) THEN
! available aquifer storage is not filled with lateral gw flow
! water table always below the lower soil layer
head = head + deltaS/Sy
!PRINT "(f12.4)", head, deltaS, deltaSp, deltaSl
ELSE
! available aquifer storage is not enough to store gw lateral flow
! water table always above the aquifer
! bottom soil layers remains unsaturated
! calculate avaliable storage in the bottom soil layer
deltaSpp = deltaSp - deltaSl
IF (deltaSpp .lt. 0) THEN
! enough storage available at the bottom soil layer
! water table rises above the lower layer
head = zroot_l + (deltaSp)/(theta_sat_l-theta_l)
ELSE
! not enough space available at the bnttom soil layer
! soil layer becomes fully saturated
! water table rises above the aquifer
head = zroot_u + deltaSpp/(theta_sat_u-theta_u)
END IF
END IF
ELSE
! initial water table above the aquifer
IF (deltaSl .gt. 0) THEN
! storage availble at the bottom soil layer
! calulate the volume of water needed at the upper layer
deltaSpp = deltaS - deltaSl
IF (deltaSpp .lt. 0) THEN
! available storage in the bottom soil layer is enough to
! store lateral gw flow
! bottom soil layer remains unsaturated
! water table within the lower layer
head = head + deltaS/(theta_sat_l-theta_l)
!PRINT "(f12.4, 1x, f12.4, 1x, f12.4, 1x, f12.4)", head, deltaS, deltaSp, deltaSl
ELSE
! available storage is not enough for storing lateral gw flow
! bottom soil layer becomes saturated
! water table rises to upper layer
head = zroot_u + deltaSpp/(theta_sat_u-theta_u)
!PRINT "(f12.4)", head, deltaS, deltaSp, deltaSl
END IF
ELSE
! bottom soil layer is saturated
! water table always in the upper layer
head = head + deltaS/(theta_sat_u-theta_u)
END IF
END IF
END IF
END SUBROUTINE
END MODULE