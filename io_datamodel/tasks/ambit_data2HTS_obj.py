# + tags=["parameters"]
upstream = None
folder_output = None
product = None
config_file = None
config_key = None
# -

from pynanomapper import aa
import os, os.path
import pandas as pd
import requests
import pynanomapper.datamodel.ambit as m2n
import traceback
import json
import re
import pickle
from TOX5.endpoints.hts_data_container import HTS
import sys

os.makedirs(product["data_json"], exist_ok=True)


def loadconfig(config_file, config_key, subkey="extract"):
    with open(config_file) as f:
        cfg = json.load(f)
    return cfg[config_key][subkey]


def run_task(config_for_db):
    if not config_for_db:
        sys.exit(0)


extract_config = loadconfig(config_file, config_key, "extract_from_db")

run_task(extract_config)

enm_api_url = extract_config['enm_api_url']
db = extract_config['db']
query = extract_config['query']
serum_used = extract_config['serum_used']
assay_type = extract_config['assay_type']
endpoint = extract_config['endpoint']


def substances2json(url_db, auth, pjson):
    substances = m2n.Substances(**pjson)
    for substance in substances.substance:
        try:
            sjson = None
            url = "{}/substance/{}/study&media=application/json&max={}".format(url_db, substance.i5uuid, 10000)
            # url = "{}/study?media=application/json&max=10000".format(substance.URI)
            response = requests.get(url, auth=auth)
            if response.status_code == 200:
                sjson = response.json()
                substance.study = m2n.Study(**sjson).study
            else:
                print(response.status_code, url)
        except Exception as err:
            print("An exception occurred: %s", str(err))
            print("Exception traceback:\n%s", traceback.format_exc())
            print(substance.i5uuid)
            # Write JSON data to the file
            with open(os.path.join(product["data_json"], "{}.json".format(substance.i5uuid)), 'w') as json_file:
                json.dump(sjson, json_file, indent=4)
            break

    return substances


# Extract HTS data from Ambit as json
config, config_servers, config_security, auth_object, msg = aa.parseOpenAPI3()
if auth_object != None:
    auth_object.setKey('')

rows = 1000
url_db = "{}/enm/{}/substance?{}&media=application/json&max={}".format(enm_api_url, db, query, rows)

OK = False
response = requests.get(url_db, auth=auth_object)
if response.status_code == 200:
    pjson = response.json()
    with open(os.path.join(product["data_json"], "substances_parsed.json"), 'w') as json_file:
        json.dump(pjson, json_file, indent=4)

    OK = True
else:
    print(response.status_code)

substances = substances2json("{}/enm/{}".format(enm_api_url, db), auth_object, pjson)
substances_json = substances.to_json()

print(substances_json)
with open(os.path.join(product["data_json"], "substances_obj.json"), 'w') as json_file:
    json_file.write(substances_json)


# Create HTS objects from Ambit substances

def ambit_subs2hts_obj(ambit_substances, assay_type, endpoint, serum_used=False):
    metadata = {}
    df_data_w = []
    df_data_wo = []

    serum = False
    for substance in ambit_substances.substance:
        papps = substance.study
        for papp in papps:
            if papp.protocol.topcategory == 'TOX' and papp.protocol.category.code == 'ENM_0000068_SECTION':
                method = papp.parameters.get('E.method')
                medium = papp.parameters.get('MEDIUM')
                if serum_used:
                    if 'serum' in medium:
                        serum = True
                    else:
                        serum = False
                for e in papp.effects:
                    if e.endpoint == "CELL_VIABILITY" and e.endpointtype == "RAW DATA":

                        concentrations = e.conditions.get('CONCENTRATION')
                        if concentrations:
                            conc_value = concentrations.loValue
                        else:
                            conc_value = 0
                        well = e.conditions.get('WELL')

                        cell = papp.parameters.get("E.cell_type")
                        replicate = e.conditions.get('REPLICATE')
                        time = e.conditions.get('E.EXPOSURE_TIME')
                        time_value = re.search(r'\d+', time).group()
                        result = e.result.loValue
                        if serum_used:
                            if serum:
                                df_data_w.append({
                                    'cells': cell, 'replicates': replicate, 'time': (re.sub(r'\s+', '', time)).upper(),
                                    'result': result, 'well': well
                                })
                            else:
                                df_data_wo.append({
                                    'cells': cell, 'replicates': replicate, 'time': (re.sub(r'\s+', '', time)).upper(),
                                    'result': result, 'well': well
                                })
                        else:
                            df_data_wo.append({
                                'cells': cell, 'replicates': replicate, 'time': (re.sub(r'\s+', '', time)).upper(),
                                'result': result, 'well': well
                            })

                        if well not in metadata and well is not None:
                            metadata[well] = {'material': substance.name, 'concentration': conc_value}

    materials_to_check = ['water', 'Dispersant', 'dispersant', 'another_material']
    water_keys = [key for key, value in metadata.items() if value['material'] in materials_to_check]

    if serum_used:
        df_w = pd.DataFrame(df_data_w)
        pivot_df_w = df_w.pivot_table(index=['cells', 'replicates', 'time'],
                                      columns='well',
                                      values='result',
                                      aggfunc='first')
        pivot_df_w.reset_index(inplace=True)

        _data_w = HTS(endpoint)
        _data_w.serum_used = True
        _data_w.raw_data_df = pivot_df_w
        _data_w.water_keys = water_keys
        _data_w.metadata = metadata
        _data_w.assay_type = assay_type

    df_wo = pd.DataFrame(df_data_wo)
    pivot_df_wo = df_wo.pivot_table(index=['cells', 'replicates', 'time'],
                                    columns='well',
                                    values='result',
                                    aggfunc='first')
    pivot_df_wo.reset_index(inplace=True)
    _data_wo = HTS(endpoint)
    _data_wo.raw_data_df = pivot_df_wo
    _data_wo.water_keys = water_keys
    _data_wo.metadata = metadata
    _data_wo.assay_type = assay_type

    if serum_used:
        return _data_w, _data_wo
    else:
        return _data_wo


# Save HTS objects
os.makedirs(product["data_obj"], exist_ok=True)
if serum_used:
    _data_w, _data_wo = ambit_subs2hts_obj(substances, assay_type=assay_type, endpoint=endpoint, serum_used=True)
    print(_data_wo)
    print(_data_w)
    with open(os.path.join(product["data_obj"], f'{endpoint}_data_w.pkl'), 'wb') as f:
        pickle.dump(_data_w, f)

    with open(os.path.join(product["data_obj"], f'{endpoint}_data_wo.pkl'), 'wb') as f:
        pickle.dump(_data_wo, f)
else:
    _data_wo = ambit_subs2hts_obj(substances, assay_type=assay_type, serum_used=False)
    with open(os.path.join(product["data_obj"], f'{endpoint}_data_wo.pkl'), 'wb') as f:
        pickle.dump(_data_wo, f)
