import sys
sys.path.append("C:/Users/Edisson/Documents/GitHub/CUWALID")
import os
import numpy as np
import pandas as pd
import cuwalid.forecasting.main_impact_forecast as fcast

fconfig = "C:/Users/Edisson/Documents/GitHub/CUWALID-Example/input/impact_forecast_input.json"
fcast.plot_map_json(fconfig)