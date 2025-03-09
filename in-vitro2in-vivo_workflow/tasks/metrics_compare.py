import pandas as pd
import os.path 


# + tags=["parameters"]
upstream = ["scikit_*"]
product = None
# -

df = None
for key in upstream["scikit_*"]:
    _tmp = pd.read_excel(upstream["scikit_*"][key]["metrics"])
    df = _tmp if df is None else pd.concat([df, _tmp])

df.to_excel(product["data"], index=False)    
