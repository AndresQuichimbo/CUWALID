from dryp.main_DRYP import run_DRYP
import time 

startTime = time.time()
#run_DRYP('../DynaVeg/DV_input.dmp')
#run_DRYP('../multiaq/MA_input.dmp')
#run_DRYP("../channel/CH_input.dmp")
#run_DRYP("../Somalia/OD_input.dmp")
#run_DRYP("../Lake/LA_input.dmp")
#run_DRYP("../Lake/LA_input_riv.dmp")
#run_DRYP('../OneCell/LA_input.dmp')
#run_DRYP('../HAD/HAD_input_long.dmp')
#run_DRYP('../HAD/HAD_input_long_v2.dmp')
#run_DRYP('../Kenya/EW_D2E_sim_0_input_3hv2.dmp')
#run_DRYP('../Kenya/EW_D2E_sim_1_input_3hv2.dmp')
#run_DRYP('../Kenya/EW_D2E_sim_2_input_3hv2.dmp')
#run_DRYP('../Kenya/EW_D2E_sim_3_input_3hv2.dmp')
#run_DRYP('../Kenya/EW_D2E_sim_4_input_3hv2.dmp')
#run_DRYP('../Kenya/EW_D2E_sim_5_input_3hv2.dmp')

for i in range (2000, 2023):
    ifname = "/home/c1755103/HAD/HAD_IMERG_input_sim_"+str(i)+".dmp"
    run_DRYP(ifname)





print ('time=', time.time() - startTime)