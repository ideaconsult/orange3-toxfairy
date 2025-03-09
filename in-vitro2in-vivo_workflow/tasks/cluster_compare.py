import pandas as pd
import os.path


# + tags=["parameters"]
upstream = ["cluster-*"]
product = None
# -

stats = None
for key in upstream["cluster-*"]:
    df = pd.read_excel(upstream["cluster-*"][key]["stats"])
    stats = df if stats is None else pd.concat([stats, df])

stats = stats.sort_values("silhouette_score", ascending=False)
stats.to_excel(product["stats"], index=None)
stats

stats = stats.loc[stats["nclusters"] > 2]

key = stats.iloc[0]["model"].split("-")[1]
option = stats.iloc[0]["method"]

data = pd.read_excel(os.path.join(upstream["cluster-*"][f"cluster-{key}"]["data"],f"x_{key}_{option}.xlsx"))

data.to_excel(product["data"], index=False)