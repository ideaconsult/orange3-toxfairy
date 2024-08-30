# + tags=["parameters"]
upstream = None
product = None
folder_output = None
config_file = None
config_key = None
# -

from toxfairy.src.toxfairy.endpoints.hts_data_container import HTS
from toxfairy.src.toxfairy.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
import os.path
import pickle
import json
import sys


def loadconfig(config_file, config_key, subkey="extract"):
    with open(config_file) as f:
        cfg = json.load(f)
    return cfg[config_key][subkey]


def run_task(config_for_local):
    if not config_for_local:
        sys.exit(0)


extract_config = loadconfig(config_file, config_key, "extract_from_local")
run_task(extract_config)


def create_data_container(endpoint, assay_type, directory=None, tmp=None, serum=False, dose_recalc=None):
    _data = None

    _data = HTS(endpoint)
    _meta = MetaDataReaderTmp(tmp, _data)
    _meta.read_meta_data()
    if dose_recalc:
        _meta.recalculate_dose_from_sbet(dose_recalc["well_volume"], dose_recalc["cell_growth_area"])

    data_reader = DataReaderTmp(tmp, directory, _data)
    data_reader.read_data()
    if _data.assay_type == "imaging":
        _data.raw_data_df = _data.raw_data_df[_data.raw_data_df['Description'] != '_']

    _data.serum_used = serum
    _data.assay_type = assay_type

    return _data


def pkl_hts_obj(hts_obj):
    for obj in hts_obj:
        if obj.serum_used:
            file_name = f'{obj.endpoint}_data_w.pkl'
        else:
            file_name = f'{obj.endpoint}_data_wo.pkl'

        with open(os.path.join(product['data'], file_name), 'wb') as f:
            pickle.dump(obj, f)


obj_list = []
folder_data_input = extract_config["folder_data_input"]
folder_tmp_input = extract_config["folder_tmp_input"]
config = extract_config["config"]
dose_recalculation = extract_config["dose_recalculation"]
# print(config)

for key, config_item in config.items():
    directory = os.path.join(folder_data_input, config_item.get("dir", ""))
    tmp = os.path.join(folder_tmp_input, config_item.get("tmp", ""))
    serum = config_item.get("serum", None)
    assay_type = config_item.get("assay_type", None)
    endpoints = config_item.get("endpoints", [])

    for endpoint in endpoints:
        tmp_obj = create_data_container(endpoint, assay_type=assay_type, directory=directory, tmp=tmp, serum=serum,
                                        dose_recalc=dose_recalculation)
        obj_list.append(tmp_obj)

# # Example to print the resulting list of objects
# for obj in obj_list:
#     print(obj)

os.makedirs(product["data"], exist_ok=True)

if os.path.exists(product["data"]):
    files = os.listdir(product["data"])
    for file in files:
        os.remove(os.path.join(product["data"], file))

pkl_hts_obj(obj_list)

# print(len(obj_list))
# print(obj_list[0])
