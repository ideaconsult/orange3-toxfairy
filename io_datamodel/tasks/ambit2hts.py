# + tags=["parameters"]
upstream = ["extract_data"]
product = None
folder_output = None
# -

# # for testing outside of pipeline
# enm_api_url = "https://api.ideaconsult.net/calibrate"
# db = "calibrate"
# query = "type=citationowner&search=MISVIK"

import os.path
import pandas as pd
import pynanomapper.datamodel.ambit as m2n
import json
import re
import pickle
from TOX5.endpoints.hts_data_container import HTS

# pjson_path = "D:\PhD\projects\ToxPi\orange-tox5\io_datamodel\products\substance_data\substances_obj.json"
# with open(pjson_path, 'r') as json_file:
#     pjson = json.load(json_file)

path = upstream["extract_data"]["data"]
json_path = os.path.join(path, "substances_obj.json")
with open(json_path, 'r') as json_file:
    pjson = json.load(json_file)

substances = m2n.Substances(substance=pjson)

_data_w = HTS('CTG')
_data_w.serum_used = True
_data_wo = HTS('CTG')

metadata = {}
df_data_w = []
df_data_wo = []

serum = False
for substance in substances.substance:
    papps = substance.study
    for papp in papps:
        if papp.protocol.topcategory == 'TOX' and papp.protocol.category.code == 'ENM_0000068_SECTION':
            method = papp.parameters.get('E.method')
            medium = papp.parameters.get('MEDIUM')
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

                    if serum:
                        df_data_w.append({
                            'cells': cell,
                            'replicate': replicate,
                            # 'time': time_value,
                            'time': (re.sub(r'\s+', '', time)).upper(),
                            'result': result,
                            'well': well
                        })
                    else:
                        df_data_wo.append({
                            'cells': cell,
                            'replicate': replicate,
                            # 'time': time_value,
                            'time': (re.sub(r'\s+', '', time)).upper(),
                            'result': result,
                            'well': well
                        })

                    if well not in metadata and well is not None:
                        metadata[well] = {'material': substance.name, 'concentration': conc_value}

df_w = pd.DataFrame(df_data_w)
df_wo = pd.DataFrame(df_data_wo)

pivot_df_w = df_w.pivot_table(index=['cells', 'replicate', 'time'],
                              columns='well',
                              values='result',
                              aggfunc='first')

pivot_df_w.reset_index(inplace=True)

pivot_df_wo = df_wo.pivot_table(index=['cells', 'replicate', 'time'],
                                columns='well',
                                values='result',
                                aggfunc='first')

pivot_df_wo.reset_index(inplace=True)

materials_to_check = ['water', 'Dispersant', 'dispersant', 'another_material']
water_keys = [key for key, value in metadata.items() if value['material'] in materials_to_check]

_data_w.raw_data_df = pivot_df_w
_data_w.water_keys = water_keys
_data_w.metadata = metadata

_data_wo.raw_data_df = pivot_df_wo
_data_wo.water_keys = water_keys
_data_wo.metadata = metadata

os.makedirs(product["data"], exist_ok=True)
with open(os.path.join(product["data"], 'ctg_data_w.pkl'), 'wb') as f:
    pickle.dump(_data_w, f)

with open(os.path.join(product["data"], 'ctg_data_wo.pkl'), 'wb') as f:
    pickle.dump(_data_wo, f)
