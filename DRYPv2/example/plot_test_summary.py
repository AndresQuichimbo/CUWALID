"""This fuction plot average results of the
tilted-V catchment model test
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# create figure of model inputs and outputs
fig, ax = plt.subplots(6, 1, sharex=True)
fig.set_size_inches(9, 6)

# plot soil moisture
fname = "output/test_avg.csv"
fname_dis = "output/test_p_dis.csv"

df =  pd.read_csv(fname)
df["Date"] = pd.to_datetime(df['Date'])
dfdis = pd.read_csv(fname_dis)

# plot forcing dataset
ax[0].plot(df['pre_0'], color='black')
ax[0].plot(df['pet_0'])
ax[0].set_ylabel('Rain/Evap.\n [mn/h]')

# plot model results
ax[1].plot(df['tht_0'])
ax[2].plot(df['aet_0'])
ax[3].plot(df['rch_0'])
ax[4].plot(dfdis['dis_0'])
ax[5].plot(df['wte_0'])

# add axis labels
ax[1].set_ylabel('Wat. Cont\n [%]')
ax[2].set_ylabel('Actual ET.\n [%]')
ax[3].set_ylabel('Recharge\n [mm/h]')
ax[4].set_ylabel('Discharge\n [mm/h]')
ax[5].set_xlabel('time [hours]')
ax[5].set_ylabel('Water table\n elev [m]')

ax[5].set_xlim([13500, 14000])
# save model results
plt.tight_layout()
fname_out = 'output/test_avg.png'
plt.savefig(fname_out, dpi=300)
#plt.show()
