# + tags=["parameters"]
upstream = ["ambit_data2HTS_obj"]
product = None
folder_output = None
config_file = None
config_key = None
# -

from pynanomapper.datamodel.nexus_writer import to_nexus
import os, os.path
import pynanomapper.datamodel.ambit as m2n
import nexusformat.nexus.tree as nx
import json
import uuid
import sys


def loadconfig(config_file, config_key, subkey="extract"):
    with open(config_file) as f:
        cfg = json.load(f)
    return cfg[config_key][subkey]


def run_task(config_for_db):
    if not config_for_db:
        sys.exit(0)


extract_config = loadconfig(config_file, config_key, "extract_from_db")
run_task(extract_config)
query = extract_config['query']

path = upstream["ambit_data2HTS_obj"]["data_json"]
json_path = os.path.join(path, "substances_obj.json")
with open(json_path, 'r') as json_file:
    pjson = json.load(json_file)

substances = m2n.Substances(substance=pjson)

nxroot = nx.NXroot()
substances.to_nexus(nxroot)
nxroot.save(os.path.join(folder_output, "substances_{}.nxs".format(uuid.uuid5(uuid.NAMESPACE_OID, query))), mode="w")
