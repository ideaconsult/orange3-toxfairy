import pandas as pd
import os.path 


# + tags=["parameters"]
upstream = ["intervalmodels_*"]
product = None
# -

df = None
for key in upstream["intervalmodels_*"]:
    _tmp = pd.read_excel(os.path.join(upstream["intervalmodels_*"][key]["data"], "metrics.xlsx"))
    df = _tmp if df is None else pd.concat([df, _tmp])

df.to_excel(product["data"], index=False)    
