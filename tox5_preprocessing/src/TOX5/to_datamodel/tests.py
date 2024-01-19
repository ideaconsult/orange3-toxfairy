import pandas as pd
import re
from TOX5.calculations.casp_normalization import CaspNormalization
from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.calculations.dapi_normalization import DapiNormalization
from TOX5.calculations.dose_response import DoseResponse
from TOX5.calculations.tox5 import TOX5
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
from TOX5.misc.utils import generate_annotation_file, annotate_data

# print(pd.__version__)
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

directories = [
    'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\data\\Misvik high throughput screening data\\Screen1-4_CTG_Caspase_raw_data',
    'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\data\\Misvik high throughput screening data\\Screen1-4_imaging data']
template_test = 'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\TestDataRecordingForm_harmless_HTS_METADATA.xlsx'

## Create object as data container for CTG endpoint
ctg_data = HTS('ctg')
ctg_meta = MetaDataReaderTmp(template_test, ctg_data)
ctg_meta.read_meta_data()

# print(ctg_data.metadata)
ctg_data_reader = DataReaderTmp(template_test, directories[0], ctg_data)
ctg_data_reader.read_data()
# print(ctg_data.raw_data_df)

# ## Create object for specific CTG normalization
# ctg_normalizer = CTGNormalization(ctg_data)
# ctg_normalizer.remove_outliers_by_quantiles()
# ctg_normalizer.median_control(ctg_data.normalized_df)
# ctg_normalizer.subtract_blank(ctg_data.normalized_df)
# ctg_normalizer.calc_mean_median()
# ctg_dose = DoseResponse(ctg_data)
# ctg_dose.dose_response_parameters()

dapi_data = HTS('dapi')
dapi_meta = MetaDataReaderTmp(template_test, dapi_data)
dapi_meta.read_meta_data()
dapi_data_reader = DataReaderTmp(template_test, directories[1], dapi_data)
dapi_data_reader.read_data()
# print(dapi_data.raw_data_df)
#
# dapi_normalizer = DapiNormalization(dapi_data)
# dapi_normalizer.clean_dna_raw()
# dapi_normalizer.remove_outliers_by_quantiles()
# dapi_normalizer.median_control(dapi_data.normalized_df)
# dapi_normalizer.calc_mean_median()
# dapi_dose = DoseResponse(dapi_data)
# dapi_dose.dose_response_parameters()
#
casp_data = HTS('casp')
casp_meta = MetaDataReaderTmp(template_test, casp_data)
casp_meta.read_meta_data()
casp_data_reader = DataReaderTmp(template_test, directories[0], casp_data)
casp_data_reader.read_data()

# casp_normalizer = CaspNormalization(casp_data, ctg_data.mean_df, dapi_data.mean_df)
# # casp_normalizer = CaspNormalization(casp_data)
# # casp_normalizer.ctg_mean_df = ctg_data.mean_df
# # casp_normalizer.dapi_mean_df = dapi_data.mean_df
# casp_normalizer.remove_outliers_by_quantiles()
# casp_normalizer.median_control(casp_data.normalized_df)
# casp_normalizer.subtract_blank(casp_data.normalized_df)
# ## additional normalization of CASP based on CTG and DAPI
# casp_normalizer.additional_normalization()
# casp_normalizer.calc_mean_median()
# casp_dose = DoseResponse(casp_data)
# casp_dose.dose_response_parameters()
#
# df = pd.concat([casp_data.dose_response_df,
#                 ctg_data.dose_response_df,
#                 dapi_data.dose_response_df], axis=1)
# df = df.reset_index().rename(columns={'index': 'material'})
# # print(df)
#

# tox5 = TOX5(df, ['A549', 'BEAS-2B'])

# user_selected_transform_functions = {
#     "1st": "log10x_6",
#     "auc": "sqrt_x",
#     "max": "yeo_johnson"
# }
# tox5.transform_data(user_selected_transform_functions)
#
# tox5.generate_auto_slices()
# tox5.calculate_tox5_scores()
# print(tox5.tox5_scores)
print('..................................... CTG RAW DATA ........................................')
print(ctg_data)

print('........................................ datamodel ............................................................')
from typing import List
import pprint
import json
from pynanomapper.datamodel.ambit import EffectRecord, EffectResult, EffectArray, ValueArray, Protocol, \
    EndpointCategory, ProtocolApplication, Study, SubstanceRecord, Substances
from typing import Dict, Optional, Union
import numpy as np


# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

# will be a function, but it's not ready
def create_effect_list(hts_object, data_type):
    unique_cells = hts_object.data_type['cells'].dropna().drop_duplicates().values  # unique
    unique_materials = set(item['material'] for item in hts_object.metadata.values())
    pass


unique_cells = ctg_data.raw_data_df['cells'].unique()
print(unique_cells)
unique_materials = set(item['material'] for item in ctg_data.metadata.values())
print(unique_materials)

dict_effect_list = {}
effect_list: List[Union[EffectRecord, EffectArray]] = []
protocol_app_list: List[ProtocolApplication] = []
papp_ctg = ProtocolApplication(
    protocol=Protocol(topcategory="TOX", category=EndpointCategory(code="cell viability"), endpoint='CTG'),
    effects=effect_list)

# for example for other endpoints
papp_dapi = ProtocolApplication(
    protocol=Protocol(topcategory="TOX", category=EndpointCategory(code="cell viability"), endpoint='DAPI'),
    effects=effect_list)

protocol_app_list.append(papp_ctg)
protocol_app_list.append(papp_dapi)


# only for raw data for CTG endpoint from object ctg_data
for cell in unique_cells:
    df = ctg_data.raw_data_df[ctg_data.raw_data_df['cells'] == cell]
    annotate_data(df, ctg_data.metadata)

    df1 = df.iloc[:, :3]
    for material in unique_materials:
        dict_effect_list[f"{cell}_{material}"] = SubstanceRecord(name=material)
        dict_effect_list[f"{cell}_{material}"].study = protocol_app_list
        # print(dict_effect_list[f"{i}_{n}"].study)

        fl = df.loc[:, df.loc['material'] == material]
        result = pd.concat([df1, fl], axis=1)
        # print('new cell and new material')
        # print(i)
        # print(n)

        df_processed = result.iloc[:-2, 3:]
        np_array = df_processed.values.ravel()

        concentrations = np.array(result.loc['concentration'].dropna().values)
        c = np.tile(concentrations, df_processed.shape[1])
        time = np.array(result['time'].dropna().values)
        time_values = [int(re.search(r'\d+', item).group()) for item in time]
        t = np.repeat(time_values, df_processed.shape[1])
        replicate = np.array(result['replicates'].dropna().values)
        replicate_values = [int(re.search(r'\d+', item).group()) for item in replicate]
        r = np.repeat(replicate_values, df_processed.shape[1])
        # print(np_array)
        # print(c)
        # print(time)
        # print(t)
        # print(r)

        data_dict: Dict[str, ValueArray] = {
            'concentration': ValueArray(values=c, unit='ug/ml'),
            'time': ValueArray(values=t, unit='h'),
            'replicate': ValueArray(values=r),
        }
        ea = EffectArray(endpoint="CTG", unit="count", endpointtype='RAW DATA',
                         signal=ValueArray(values=np_array, unit=''),
                         axes=data_dict
                         )
        # effect_list.append(ea)

        for pa in dict_effect_list[f"{cell}_{material}"].study:
            print('.............next protocol app...............')
            pa.parameters = {'E.cell_type': {'text': cell}}
            print(pa.parameters)
            if pa.protocol.endpoint == 'CTG':
                pa.effects.append(ea)
                print(pa.effects)


        # dict_effect_list[f"{cell}_{n}"] = ea

# for key, value in dict_effect_list.items():
#     print(f'............ new study for {key}...............')
#     print(value)
#     print('\n')
#     break
