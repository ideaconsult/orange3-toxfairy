# + tags=["parameters"]

upstream = None
product = None
folder_input: None
files_input: None
metadata_template: None

# -

import pandas as pd
import re
from TOX5.calculations.casp_normalization import CaspNormalization
from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.calculations.dapi_normalization import DapiNormalization
from TOX5.calculations.ohg_h2ax_normalization import OHGH2AXNormalization
from TOX5.calculations.dose_response import DoseResponse
from TOX5.calculations.tox5 import TOX5
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
from TOX5.misc.utils import generate_annotation_file, annotate_data
import os.path
import uuid
import pickle
import numpy as np

os.makedirs(product["data"], exist_ok=True)

template_test = metadata_template
directories = [os.path.join(folder_input, file) for file in files_input.split(",")]
print(directories)

def convert_to_native_types(obj):
    if isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def create_datacontainer(endpoint, directory):
    _data = HTS(endpoint)
    _meta = MetaDataReaderTmp(template_test, _data)
    _meta.read_meta_data()
    data_reader = DataReaderTmp(template_test, directory, _data)
    data_reader.read_data()

    return _data


def normalize_data(_data, endpoint='ctg', ctg_data_mean=None, dapi_data_mean=None):
    if endpoint.lower() == 'ctg':
        ctg_normalizer = CTGNormalization(_data)
        ctg_normalizer.remove_outliers_by_quantiles()
        ctg_normalizer.median_control(_data.normalized_df)
        ctg_normalizer.subtract_blank(_data.normalized_df)
        ctg_normalizer.calc_mean_median()
    elif endpoint.lower() == 'dapi':
        dapi_normalizer = DapiNormalization(_data)
        dapi_normalizer.clean_dna_raw()
        dapi_normalizer.remove_outliers_by_quantiles()
        dapi_normalizer.median_control(_data.normalized_df)
        dapi_normalizer.calc_mean_median()
    elif endpoint.lower() == 'casp':
        casp_normalizer = CaspNormalization(_data, ctg_data_mean, dapi_data_mean)
        casp_normalizer.remove_outliers_by_quantiles()
        casp_normalizer.median_control(_data.normalized_df)
        casp_normalizer.subtract_blank(_data.normalized_df)
        casp_normalizer.additional_normalization()
        casp_normalizer.calc_mean_median()
    elif endpoint.lower() == 'h2ax' or endpoint.lower() == '8ohg':
        h2ax_normalizer = OHGH2AXNormalization(_data)
        h2ax_normalizer.clean_dna_raw()
        h2ax_normalizer.remove_outliers_by_quantiles()
        h2ax_normalizer.median_control(_data.normalized_df)
        h2ax_normalizer.calc_mean_median()

    _dose_params = DoseResponse(_data)
    _dose_params.dose_response_parameters()
    return _data


_config = {"ctg": {"dir": directories[0]}, "dapi": {"dir": directories[1]}, "casp": {"dir": directories[0]},
           "h2ax": {"dir": directories[1]}, "8ohg": {"dir": directories[1]}}

_data = {}
_mode = "w"

# loop to create datacontainer for each endpoint and normalize data
for endpoint in _config:
    _data[endpoint] = create_datacontainer(endpoint, _config[endpoint]["dir"])
    if _data[endpoint].endpoint == 'CASP':
        _data[endpoint] = normalize_data(_data[endpoint], _data[endpoint].endpoint, _data['ctg'].mean_df,
                                         _data['dapi'].mean_df)
    else:
        _data[endpoint] = normalize_data(_data[endpoint], _data[endpoint].endpoint)

    _config[endpoint]["metadata"] = _data[endpoint].metadata

    # save data in separate files
    for df_name, df in zip(["raw_data", "normalized_data", "median_data", "dose-response_data"],
                           [_data[endpoint].raw_data_df, _data[endpoint].normalized_df,
                            _data[endpoint].median_df, _data[endpoint].dose_response_df]):
        file_name = os.path.join(product["data"], "{}_{}.txt".format(endpoint, df_name))
        _config[endpoint][df_name] = file_name
        df.to_csv(file_name, sep="\t")

    _mode = 'a'

with open(os.path.join(product["data"], "metadata.pkl"), 'wb') as pickle_file:
    pickle.dump(_config, pickle_file)


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


def get_metric_value(split_list):
    if len(split_list) == 4:
        return split_list[2]
    elif len(split_list) == 5:
        return f"{split_list[2]}_{split_list[3]}"


# function to melted df, based on result type
def hts2df(raw_data_df, metadata, endpoint='ctg', result_type='raw_data'):
    result_df = pd.DataFrame()
    if result_type == 'raw_data' or result_type == 'normalized_data':
        id_vars = ['cells', 'replicates', 'time']
        value_vars = raw_data_df.columns[3:]  # A1 to P24
        melted_df = pd.melt(raw_data_df, id_vars=id_vars, value_vars=value_vars, var_name='row', value_name='values')
        df = pd.DataFrame(metadata.values(), index=metadata.keys())  # materials
        result_df = pd.merge(df, melted_df, left_index=True, right_on='row')
        result_df["endpoint"] = endpoint
        result_df['time_unit'] = result_df['time'].str.extract(r'([a-zA-Z]+)')
        result_df['time'] = result_df['time'].str.extract(r'(\d+)').astype(int)
        result_df['replicates'] = result_df['replicates'].str.extract(r'(\d+)').astype(int)

    elif result_type == 'median_data':
        melted_df = pd.melt(raw_data_df.reset_index(), id_vars=['index'], value_vars=raw_data_df, var_name='row',
                            value_name='values')
        df = pd.DataFrame(metadata.values(), index=metadata.keys())
        result_df = pd.merge(df, melted_df, left_index=True, right_on='row')
        result_df["endpoint"] = endpoint
        result_df['cells'] = result_df['index'].str.split('_').str[0]
        result_df['time_'] = result_df['index'].str.split('_').str[1]
        result_df['time'] = result_df['time_'].str.extract(r'(\d+)').astype(int)
        result_df['time_unit'] = result_df['time_'].str.extract(r'([a-zA-Z]+)')

        result_df['time'] = result_df['time'].astype(int)
        result_df = result_df.drop('index', axis=1)
        result_df = result_df.drop('time_', axis=1)

    elif result_type == 'dose_response_data':
        melted_df = pd.melt(raw_data_df.reset_index(), id_vars=['index'], value_vars=raw_data_df, var_name='row',
                            value_name='values')
        result_df = melted_df.rename(columns={'index': 'material'})

        split_data = result_df['row'].str.split('_')
        result_df['endpoint'] = split_data.str[-1]
        result_df['cells'] = split_data.str[0]
        result_df['time'] = split_data.str[1]
        result_df['time_unit'] = result_df['time'].str.extract(r'([a-zA-Z]+)')
        result_df['time'] = result_df['time'].str.extract(r'(\d+)').astype(int)
        result_df['metric'] = split_data.apply(get_metric_value)
        result_df = result_df.drop('row', axis=1)

    return result_df


# melted all resulting df's and save them in file's
for endpoint in _config:
    print(endpoint)
    res_raw_data = hts2df(_data[endpoint].raw_data_df, _data[endpoint].metadata, endpoint, 'raw_data')
    res_norm_data = hts2df(_data[endpoint].normalized_df, _data[endpoint].metadata, endpoint, 'normalized_data')
    res_median_data = hts2df(_data[endpoint].median_df, _data[endpoint].metadata, endpoint, 'median_data')
    res_dose_response_data = hts2df(_data[endpoint].dose_response_df, _data[endpoint].metadata, endpoint,
                                    'dose_response_data')

    for df_name, df in zip(["raw_data", "normalized_data", "median_data", "dose-response_data"],
                           [res_raw_data, res_norm_data, res_median_data, res_dose_response_data]):
        file_name = os.path.join(product["data"], "{}_{}_melted.txt".format(endpoint, df_name))
        _config[endpoint][df_name] = file_name
        df.to_csv(file_name, sep="\t")
