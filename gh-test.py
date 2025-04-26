#%%
import pandas as pd
from iertools.read import read_epw

#%%
f = "data/MEX_MOR_Cuernavaca-Matamoros.Intl.AP.767260_TMYx.2004-2018.epw"
epw = read_epw(f, alias=True, year=2025)
epw

#%%
setpoint_heating = 20
setpoint_cooling = 20
epw["To_Cte"] = 20
epw["GHCal"] = (setpoint_heating - epw["To_Cte"]).clip(lower=0)
epw["GHEnf"] = (epw["To_Cte"] - setpoint_cooling).clip(lower=0)

# %%
epw["GHCal"].resample("ME").sum()
# %%
epw["GHCal"].resample("YE").sum()

# %%
epw["GHEnf"].resample("ME").sum()
# %%
epw["GHEnf"].resample("YE").sum()
