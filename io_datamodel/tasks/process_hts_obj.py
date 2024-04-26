# + tags=["parameters"]
upstream = ["ambit2hts"]
product = None
folder_output = None
folder_input = None
files_input = None
metadata_templates = None
# -

from TOX5.calculations.dapi_normalization import DapiNormalization
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.calculations.ohg_h2ax_normalization import OHGH2AXNormalization
from TOX5.calculations.dose_response import DoseResponse
import pandas as pd
import os.path
import pickle

# Read CTG data, extracted from calibrate database and save as a pickle object, other imaging endpoint read from local files
# Treat data with and without serum as a separate data
# Normalize and calculate dose-response parameters

path = upstream["ambit2hts"]["data"]


def pickle_obj(pkl_file):
    with open(os.path.join(path, pkl_file), 'rb') as f:
        data = pickle.load(f)
    return data


def create_data_container(endpoint, directory=None, tmp=None, serum=False, pkl_file=None):
    _data = None
    if not pkl_file:
        _data = HTS(endpoint)
        _meta = MetaDataReaderTmp(tmp, _data)
        _meta.read_meta_data()
        data_reader = DataReaderTmp(tmp, directory, _data)
        data_reader.read_data()
        _data.raw_data_df = _data.raw_data_df[_data.raw_data_df['Description'] != '_']
    else:
        _data = pickle_obj(pkl_file)
    _data.serum_used = serum

    return _data


def normalize_data(_data, endpoint='ctg', ctg_data_mean=None, dapi_data_mean=None):
    if endpoint.lower() == 'ctg':
        ctg_normalizer = CTGNormalization(_data)
        ctg_normalizer.remove_outliers_by_quantiles()
        ctg_normalizer.median_control(_data.normalized_df)
        ctg_normalizer.subtract_blank(_data.normalized_df)
        ctg_normalizer.calc_mean_median()
    elif "dapi" in endpoint.lower():
        dapi_normalizer = DapiNormalization(_data)
        dapi_normalizer.clean_dna_raw()
        dapi_normalizer.remove_outliers_by_quantiles()
        dapi_normalizer.median_control(_data.normalized_df)
        # dapi_normalizer.calc_mean_median()
    elif endpoint.lower() == 'casp':
        casp_normalizer = DapiNormalization(_data)
        casp_normalizer.clean_dna_raw()
        casp_normalizer.remove_outliers_by_quantiles()
        casp_normalizer.median_control(_data.normalized_df)
        casp_normalizer.calc_mean_median()
    elif endpoint.lower() == 'h2ax' or endpoint.lower() == '8ohg':
        h2ax_normalizer = OHGH2AXNormalization(_data)
        h2ax_normalizer.clean_dna_raw()
        h2ax_normalizer.remove_outliers_by_quantiles()
        h2ax_normalizer.median_control(_data.normalized_df)
        h2ax_normalizer.calc_mean_median()


def process_all_hts_obj(hts_obj_dict):
    # for dapi data the two technical replicates (a+b) are first averaged, then median of the four biological replicates is counted

    for endpoint, obj in hts_obj_dict.items():
        if endpoint == "dapiB":
            normalize_data(obj, obj.endpoint)

            combined_df = pd.concat(
                [hts_obj_dict['dapiB'].normalized_df.groupby(['replicates', 'time', 'cells']).mean(),
                 hts_obj_dict['dapiA'].normalized_df.groupby(['replicates', 'time', 'cells']).mean()])
            average_df = combined_df.groupby(['replicates', 'time', 'cells']).mean()
            average_df.reset_index(inplace=True)
            hts_obj_dict['dapiA'].normalized_df = average_df
            norm = DapiNormalization(hts_obj_dict['dapiA'])
            norm.calc_mean_median()
            hts_obj_dict['dapiA'].endpoint = 'DAPI'
        else:
            normalize_data(obj, obj.endpoint)

    del hts_obj_dict['dapiB']


def pkl_hts_obj(hts_obj):
    for key, obj in hts_obj.items():
        if obj.serum_used:
            file_name = f'{obj.endpoint}_data_w.pkl'
        else:
            file_name = f'{obj.endpoint}_data_wo.pkl'

        with open(os.path.join(product['data'], file_name), 'wb') as f:
            pickle.dump(obj, f)


templates = [os.path.join(folder_input, file) for file in metadata_templates.split(",")]
directories = [os.path.join(folder_input, file) for file in files_input.split(",")]

_config_w = {"ctg": {"pkl_file": "ctg_data_w.pkl"},
             "dapiA": {"dir": directories[0], "tmp": templates[0]},
             "dapiB": {"dir": directories[0], "tmp": templates[0]},
             "casp": {"dir": directories[0], "tmp": templates[0]},
             "h2ax": {"dir": directories[0], "tmp": templates[0]},
             "8ohg": {"dir": directories[0], "tmp": templates[0]}}

_config_wo = {"ctg": {"pkl_file": "ctg_data_wo.pkl"},
              "dapiA": {"dir": directories[1], "tmp": templates[1]},
              "dapiB": {"dir": directories[1], "tmp": templates[1]},
              "casp": {"dir": directories[1], "tmp": templates[1]},
              "h2ax": {"dir": directories[1], "tmp": templates[1]},
              "8ohg": {"dir": directories[1], "tmp": templates[1]}}

_data_w = {}
for endpoint, config_data in _config_w.items():
    directory = config_data.get("dir", None)
    tmp = config_data.get("tmp", None)
    pkl_file = config_data.get("pkl_file", None)
    serum = config_data.get("serum", True)

    _data_w[endpoint] = create_data_container(endpoint, directory=directory, tmp=tmp, serum=serum, pkl_file=pkl_file)

_data_wo = {}
for endpoint, config_data in _config_wo.items():
    directory = config_data.get("dir", None)
    tmp = config_data.get("tmp", None)
    pkl_file = config_data.get("pkl_file", None)
    serum = config_data.get("serum", False)

    _data_wo[endpoint] = create_data_container(endpoint, directory=directory, tmp=tmp, serum=serum, pkl_file=pkl_file)

process_all_hts_obj(_data_w)
process_all_hts_obj(_data_wo)

for key, obj in _data_w.items():
    _dose_params = DoseResponse(obj)
    _dose_params.dose_response_parameters()

for key, obj in _data_wo.items():
    _dose_params = DoseResponse(obj)
    _dose_params.dose_response_parameters()

os.makedirs(product["data"], exist_ok=True)

pkl_hts_obj(_data_wo)
pkl_hts_obj(_data_w)
