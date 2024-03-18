# + tags=["parameters"]
upstream = ["extract_data"]
product = None
folder_output = None
query = None
# -

from pynanomapper.datamodel.nexus_writer import to_nexus
import os, os.path
import pynanomapper.datamodel.ambit as m2n
import nexusformat.nexus.tree as nx
import json
import uuid

path = upstream["extract_data"]["data"]
json_path = os.path.join(path, "substances_obj.json")
with open(json_path, 'r') as json_file:
    pjson = json.load(json_file)

substances = m2n.Substances(substance=pjson)

nxroot = nx.NXroot()
substances.to_nexus(nxroot)
nxroot.save(os.path.join(folder_output, "substances_{}.nxs".format(uuid.uuid5(uuid.NAMESPACE_OID, query))), mode="w")
