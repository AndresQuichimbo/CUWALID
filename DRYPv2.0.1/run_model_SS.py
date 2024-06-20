from dryp.main_DRYP_SS import run_DRYP_SS
import time 

startTime = time.time()
#run_DRYP_SS('../GW_1D_SS/GW_1D_input.dmp')
#run_DRYP_SS('../HAD/HAD_input.dmp')
run_DRYP_SS('../HAD/HAD_input_ss_wg.dmp')
#run_DRYP_SS('../HAD/HAD_input_ss.dmp')
#run_DRYP_SS('../HAD/HAD_input_ss_1.dmp')
#run_DRYP_SS('../HAD/HAD_input_ss_2.dmp')
#run_DRYP_SS('../HAD/HAD_input_ss_3.dmp')


print ('time=', time.time() - startTime)