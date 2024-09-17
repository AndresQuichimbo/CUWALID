"""Test ponds
"""
#from context import dryp
import numpy as np
from cuwalid.dryp.components.DRYP_ponds import ponds

def test_ponds():
    """run test functions
    Parameterization of ponds:
    Given the maximum extend and the maximum depth
    for hmax -> Amax -> Vmax
    Amax = pi*hmax^(2a)
    a = 1/2*(log{Amax/pi}/log{hmax})
    Vmax = hmax^{2a+1}*(pi/{2a+1})
    
    """

    # Initializae variables
    cell_area = 1000*1000

    Vo = np.array([450.0])
    pet = np.array([0.5])
    aoz = np.array([0])
    Amax = np.array([10*10.]) # units m2
    hmax = np.array([2.]) # units m

    # forcing dataset    
    P = 0.0
    #print(Vmax, a)
    # initailaize ponds functions
    pnds= ponds(Amax, hmax)

    # run loop for time step
    for i in range(20):
        V, et, aoz, P = pnds.run_ponds_one_step(Vo, P, pet, aoz, cell_area)
        #V, rt, aoz = pnds.run_ponds_one_step(Vo, pet, aoz, a)
        Vo = V

    # check if test runs ok
    answer = [0.0]
    #print(Vo)
    assert np.allclose(Vo, answer)
    print('ponds: Test runs successfully')

if __name__ == '__main__':
	test_ponds()