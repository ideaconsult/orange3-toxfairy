import os
import glob

import numpy as np
import pandas as pd

# def convert_df_non_numeric_int_to_numeric(df, idx_to_numeric=True):
#     df = df.apply(pd.to_numeric, errors='coerce').fillna(df)
#     dropped_rows = df[df.isnull().any(axis=1)]
#     df_dropped_na = df.dropna(subset=['replicates'])
#     current_index = df_dropped_na.index
#     new_index = pd.to_numeric(current_index, errors='coerce')
#     df_with_numeric_index = df_dropped_na
#     df_with_numeric_index.index = new_index
#     df = pd.concat([df_with_numeric_index, dropped_rows])
#     return df
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader import DataReader, MetaDataReader
# from TOX5.misc.utils import annotate_data

print(pd.__version__)

from tox5_preprocessing.src.TOX5.calculations.casp_normalization import CaspNormalization
from tox5_preprocessing.src.TOX5.calculations.ctg_normalization import CTGNormalization
from tox5_preprocessing.src.TOX5.calculations.dapi_normalization import DapiNormalization
from tox5_preprocessing.src.TOX5.calculations.dose_response import DoseResponse
from tox5_preprocessing.src.TOX5.calculations.ohg_h2ax_normalization import OHGH2AXNormalization
from tox5_preprocessing.src.TOX5.calculations.tox5 import TOX5
from tox5_preprocessing.src.TOX5.endpoints.hts_data import HTSData
from tox5_preprocessing.src.TOX5.endpoints.hts_data_reader import HTSDataReader

annot_file = 'D:/PhD/projects/ToxPi/tox_data/vesa_files/HARMLESS_screens_clean.xlsx'
raw_data = 'D:/PhD/projects/ToxPi/tox_data/vesa_files/imaging_raw_data'
files_path = 'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\raw_data'
# ctg_data = HTSData('CTG', annot_file)
# ctg_reader = HTSDataReader(files_path, annot_file, ctg_data)
# ctg_reader.read_data_csv()
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

#
# ctg_normalize = CTGNormalization(ctg_data)
# ctg_normalize.remove_outliers_by_quantiles()
# ctg_normalize.median_control(ctg_data.normalized_df)
# # # # print(ctg_data.normalized_df)
# ctg_normalize.subtract_blank(ctg_data.normalized_df)
# # # # print(ctg_data.normalized_df)
# # # want to remove it ///////////////////////////////////////////////////////////////////////////////////////////////////////////
# # # ctg_normalize.calc_blank_sd()
# # # # print(ctg_data.normalized_df)
# ctg_normalize.calc_mean_median()
# # print(ctg_data.mean_df)
# # print(ctg_data.median_df)
# # print(ctg_data.mean_df)
# # print(ctg_data.median_df)
# # # print(ctg_data.normalized_df.columns)
# # # print('//////////////////////////////////////////')
# # # print(ctg_data.mean_df.columns)
# ctg_dose_response = DoseResponse(ctg_data)
# ctg_dose_response.calc_p_values()
# # print(ctg_dose_response.p_value_dict)
# ctg_dose_response.calc_2_3_sd_of_blanks()
# # print(ctg_dose_response.sd_dict)
# ctg_dose_response.calc_auc()
# # print(ctg_dose_response.auc)
# ctg_dose_response.first_significant()
# # print(ctg_dose_response.fsc_2sd)
# ctg_dose_response.max_effect()
# ctg_dose_response.concatenate_parameters()
# print(ctg_dose_response.max)
# ctg_dose_response.dose_response_parameters()
#
#
#
# # Standard dapi processing
# dapi_data = HTSData('Dapi', annot_file)
# dapi_reader = HTSDataReader(files_path, annot_file, dapi_data, 'Imaging raw')
# dapi_reader.read_data_excel()
# print(dapi_data.raw_data_df.head())
# dapi_normalize = DapiNormalization(dapi_data)
# dapi_normalize.clean_dna_raw()
# print(dapi_data.raw_data_df.head())
# # print(dapi_data.raw_data_df)
# dapi_normalize.remove_outliers_by_quantiles()
# dapi_normalize.median_control(dapi_data.normalized_df)
# # dapi_normalize.calc_blank_sd()
# dapi_normalize.calc_mean_median()
# print(dapi_data.normalized_df.head())
# dapi_dose_responce = DoseResponse(dapi_data)
# dapi_dose_responce.dose_response_parameters()

# #
# # # Standard h2ax processing
# h2ax_data = HTSData('H2AX', annot_file)
# h2ax_reader = HTSDataReader(files_path, annot_file, h2ax_data, 'Imaging raw')
# h2ax_reader.read_data_excel()
# h2ax_normalize = OHGH2AXNormalization(h2ax_data)
# h2ax_normalize.clean_dna_raw()
# h2ax_normalize.remove_outliers_by_quantiles()
# h2ax_normalize.median_control(h2ax_data.normalized_df)
# h2ax_normalize.calc_blank_sd()
# h2ax_normalize.calc_mean_median()
# h2ax_dose_responce = DoseResponse(h2ax_data)
# h2ax_dose_responce.dose_response_parameters()
# #
# # # Standard 8ohg processing
# ohg_data = HTSData('8OHG', annot_file)
# ohg_reader = HTSDataReader(files_path, annot_file, ohg_data, 'Imaging raw')
# ohg_reader.read_data_excel()
# ohg_normalize = OHGH2AXNormalization(ohg_data)
# ohg_normalize.clean_dna_raw()
# ohg_normalize.remove_outliers_by_quantiles()
# ohg_normalize.median_control(ohg_data.normalized_df)
# ohg_normalize.calc_blank_sd()
# ohg_normalize.calc_mean_median()
# ohg_dose_responce = DoseResponse(ohg_data)
# ohg_dose_responce.dose_response_parameters()
# #
# # Standard casp processing
# casp_data = HTSData('Casp', annot_file)
# casp_reader = HTSDataReader(files_path, annot_file, casp_data)
# casp_reader.read_data_csv()
# casp_normalize = CaspNormalization(casp_data, ctg_data.mean_df, dapi_data.mean_df)
# casp_normalize.remove_outliers_by_quantiles()
# casp_normalize.median_control(casp_data.normalized_df)
# casp_normalize.subtract_blank(casp_data.normalized_df)
#
# print(casp_data.normalized_df)
# print(type(ctg_data.mean_df))
# # casp_normalize.calc_blank_sd()
# casp_normalize.additional_normalization()
# print(casp_data.normalized_df)

# # print(casp_data.normalized_df)
# casp_normalize.calc_mean_median()
# casp_dose_responce = DoseResponse(casp_data)
# casp_dose_responce.dose_response_parameters()
# #
# df = pd.concat([casp_data.dose_response_df,
#                 ohg_data.dose_response_df,
#                 h2ax_data.dose_response_df,
#                 ctg_data.dose_response_df,
#                 dapi_data.dose_response_df], axis=1)
#
# print(df)
#
# df = ctg_data.dose_response_df
# df = df.reset_index().rename(columns={'index': 'material'})
# #
# #
# # # df_last = table_from_frame(df, force_nominal=True)
# #
# # #
# user_selected_transform_functions = {
#     "1st": "log10x_6",
#     "auc": "sqrt_x",
#     "max": "yeo_johnson"
# }
# tox5 = TOX5(df, ['A549', 'BEAS-2B'])
# tox5.transform_data(user_selected_transform_functions)
# # print(tox5.transformed_data.head())
# print(df.head())
# print(df.dtypes)
# tox5.calculate_tox5_scores()
# print(tox5.tox5_scores.head())


# print(tox5.first_tox5_df)
# print(tox5.slice_names_)
# print()
# print(tox5.cell)
# print()
# print(tox5.all_slice_names)
# print()
# tox5.calculate_second_tox5_by_endpoint()
# print('first')
# print(tox5.tox5_score['CTG'])
# tox5.calculate_slices_by_time_endpoint()
# print('second')
# print(tox5.tox5_scores)
# print('test')
# slices_names, slices = tox5.generate_auto_slices('by_time_endpoint')
# print(slices_names)
# print(slices)
# # tox5.test('by_time_endpoint')
# # print(tox5.tox5_scores)
#
# data = list(map(list, zip(*slices)))
# df = pd.DataFrame(data, columns=slices_names)
# pd.set_option('display.max_columns')
# pd.set_option('display.max_rows')
# print(df)

# test2 = tox5.tox5_score.equals(tox5.tox5_scores)
# print(f'the df are equals {test2}')

# print(tox5.tox5_score.columns)
# print(tox5.all_slice_names)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<TESTS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
# ctg_data2 = HTSData('CTG', 'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/annotation.xlsx')
# ctg_reader2 = HTSDataReader('D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/raw_data',
#                             'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/HARMLESS_for_tests.xlsx',
#                             ctg_data2)
# # #
# # pd.set_option('display.max_columns', None)
# # pd.set_option('display.max_rows', None)
# ctg_reader2.read_data_csv()
# # # print(ctg_data.raw_data_df)
# ctg_normalize2 = CTGNormalization(ctg_data2)
# ctg_normalize2.remove_outliers_by_quantiles()
# ctg_normalize2.median_control(ctg_data2.normalized_df)
# ctg_normalize2.subtract_blank(ctg_data2.normalized_df)
# ctg_normalize2.calc_mean_median()
#
# # # print(ctg_data.mean_df)
# # # print(ctg_data.median_df)
# ctg_dose_response2 = DoseResponse(ctg_data2)
# ctg_dose_response2.dose_response_parameters()
#
# df2 = ctg_data2.dose_response_df
# df2 = df2.reset_index().rename(columns={'index': 'material'})
# print(df2)
# print(df2.dtypes)



# user_selected_transform_functions = {
#     "1st": "sqrt_x",
#     "auc": "sqrt_x",
#     "max": "sqrt_x"
# }
# #
# tox52 = TOX5(df2, ['A549', 'BEAS-2B'])
# print(tox52.all_slice_names)
# tox52.transform_data(user_selected_transform_functions)
# # print(tox52.transformed_data)


#
# dapi_data = HTSData('Dapi',
#                     'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/annotation.xlsx')
# dapi_reader = HTSDataReader('D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/raw_data',
#                             'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/HARMLESS_for_tests.xlsx',
#                             dapi_data, 'Imaging raw')
# #
# dapi_reader.read_data_excel()
# print(dapi_data.raw_data_df)
# dapi_data.raw_data_df.to_csv('D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/expected_read_excel.csv')
# # print(dapi_data.raw_data_df)
# dapi_normalize = DapiNormalization(dapi_data)
# dapi_normalize.clean_dna_raw()
# dapi_normalize.remove_outliers_by_quantiles()
# dapi_normalize.median_control(dapi_data.normalized_df)
# dapi_normalize.calc_mean_median()
# dapi_data.mean_df.to_csv('D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/mean_dapi.csv')
#
#
#
# casp_data = HTSData('Casp', 'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/HARMLESS_screens_clean_for_code_test.xlsx')
# casp_reader = HTSDataReader('D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/raw_data',
#                             'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/HARMLESS_screens_clean_for_code_test.xlsx',
#                             casp_data)
# casp_reader.read_data_csv()
# casp_normalize = CaspNormalization(casp_data, ctg_data.mean_df, dapi_data.mean_df)
# casp_normalize.remove_outliers_by_quantiles()
# casp_normalize.median_control(casp_data.normalized_df)
# casp_normalize.subtract_blank(casp_data.normalized_df)
# casp_normalize.additional_normalization()
# print(casp_data.normalized_df)
#
#
#
#
#
# # ohg_data = HTSData('8OHG',
# #                     'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/HARMLESS_screens_clean_for_code_test.xlsx')
# # ohg_reader = HTSDataReader('D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/raw_data',
# #                             'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/HARMLESS_screens_clean_for_code_test.xlsx',
# #                             ohg_data, 'Imaging raw')
# # #
# # ohg_reader.read_data_excel()
# # # print(ohg_data.raw_data_df)
# # # print(dapi_data.raw_data_df)
# # ohg_normalize = OHGH2AXNormalization(ohg_data)
# # ohg_normalize.clean_dna_raw()
# # print(ohg_data.raw_data_df)
#
# # print(dapi_data.normalized_df)
# # dapi_data.normalized_df.to_csv('D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/expected_clean_dna_raw.csv', index=False)
# #
# # dapi_normalize.remove_outliers_by_quantiles()
# # dapi_normalize.median_control(dapi_data)
# # dapi_normalize.calc_mean_median

# df_for_tox5 = pd.read_csv(
#     'D:/PhD/projects/ToxPi/orange-tox5/tox5_preprocessing/test/test_data/expected_dose_response_for_tox5.csv',
#     index_col=0)
# df_for_tox5 = df_for_tox5.reset_index().rename(columns={'index': 'material'})
# # print('original df')
# # print(df_for_tox5)
#
# user_selected_transform_functions = {
#     "1st": "log10x_6",
#     "auc": "sqrt_x",
#     "max": "yeo_johnson"
# }
# #
# tox52 = TOX5(df_for_tox5, ['A549', 'BEAS-2B'])
# tox52.transform_data(user_selected_transform_functions)
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# slice_name, slices = tox52.generate_auto_slices()
# print(slice_name, slices)


# print('/////////////////////////////////////////////////////////////////////////////////////////////////////////////')
# print('/////////////////////////////////////////////////////////////////////////////////////////////////////////////')
# test_data = HTS('CTG')
# test_read = DataReader(files_path, annot_file, test_data)
# test_read.read_data_csv()
# print(test_data.raw_data_df)
# test_meta = MetaDataReader(annot_file, test_data)
# test_meta.read_meta_data()
# test_meta.recalculate_dose_from_cell_delivered_dose()
# test_meta.recalculate_dose_from_sbet(50, 0.079495092)
# test_read.read_data_excel()
# print(test_data.raw_data_df)
# print(test_data.metadata)
#
# annotate_data(test_data.raw_data_df,test_data.metadata)
# print(test_data.raw_data_df.tail())

# ctg_normalize = CTGNormalization(test_data)
# ctg_normalize.remove_outliers_by_quantiles()
# # # print(test_data.normalized_df)
# ctg_normalize.median_control(test_data.normalized_df)
# # # print('/////////////////////////////////////////////////////////////////////////////////////////////////////////////')
# #
# # # print(test_data.normalized_df)
# ctg_normalize.subtract_blank(test_data.normalized_df)
# # # print('/////////////////////////////////////////////////////////////////////////////////////////////////////////////')
# #
# # # print(test_data.normalized_df)
# ctg_normalize.calc_mean_median()
# # # print('/////////////////////////////////////////////////////////////////////////////////////////////////////////////')
# #
# # # print(test_data.mean_df)
# # # print(test_data.median_df)
# test_d = DoseResponse(test_data)
# # test_d.calc_p_values()
# # test_d.calc_2_3_sd_of_blanks()
# # test_d.calc_auc()
# # # print(test_d.auc)
# # test_d.first_significant()
# # # print(test_d.fsc_2sd)
# # # print(test_d.fsc_3sd)
# # test_d.max_effect()
# # print(test_d.max)
# # # print('/////////////////////////////////////////////////////////////////////////////////////////////////////////////')
# # #
# # # print(test_data.dose_response_df)
# test_d.dose_response_parameters()
# print(test_data.metadata)



# test_data = HTS('CTG')
# test_read = DataReader(files_path, test_data, 'Imaging raw')
# # test_read.read_data_txt()
#
# test_meta = MetaDataReader(annot_file, test_data)
# test_meta.read_meta_data()
# # test_meta.recalculate_dose_from_cell_delivered_dose()
# # test_meta.recalculate_dose_from_sbet(50, 0.079495092)
# test_read.read_data_csv()
# # test_read.read_data_excel()
#
# # print(test_data.raw_data_df)
# # annotate_data(test_data.raw_data_df, test_data.metadata)
# test_norm= CTGNormalization(test_data)
# # test_norm = DapiNormalization(test_data)
# test_norm.remove_outliers_by_quantiles()
# print(test_data.normalized_df)
# test_norm.median_control(test_data.normalized_df)
# print(test_data.normalized_df)
# test_norm.subtract_blank(test_data.normalized_df)
# print(test_data.normalized_df)
# test_norm.calc_mean_median()
# print(test_data.mean_df)


# print(test_data.raw_data_df)
# # test_norm.clean_dna_raw()
# print(test_data.raw_data_df)




# #
# import sys
# project_pynanomapper = os.path.abspath("D:\\PhD\\projects\\ToxPi\\pynanomapper")
# sys.path.append(project_pynanomapper)
# import pynanomapper
# import requests
# import h5py
# from pynanomapper.clients.h5converter import AmbitParser
# import os.path
# from pynanomapper.aa import GraviteeAuth
# #
# # url = "https://apps.ideaconsult.net/gracious/substance?media=application/json&max=10"
# # #url = "https://apps.ideaconsult.net/harmless /substance?type=substancetype&search=CHEBI_48730"
# #
# # response = requests.get(url)
# # if response.status_code ==200:
# #     pjson = response.json()
# #     print(pjson)
# # else:
# #     print(response.status_code)
#
# #
# # Example usage
# import pynanomapper.datamodel.ambit as m2n
# import pprint
# import json
# protocol_app = m2n.ProtocolApplication(
#     uuid="123",
#     interpretationResult="result",
#     effects=[
#         m2n.EffectRecord(endpoint="CTG", unit="numbered", loValue=5.0), # effectarray
#         m2n.EffectRecord(endpoint="CASP", unit="Unit 2", loValue=11.0),
#         m2n.EffectRecord(endpoint="DAPI", unit="unit3", loValue=10.0),
#         m2n.EffectRecord(endpoint="H2AX", unit="unit4", loValue=10.0),
#         m2n.EffectRecord(endpoint="ohg", unit="unit5", loValue=10.0),
#     ],
#     owner= m2n.SampleLink(substance=m2n.Sample(uuid="sample-uuid")),
#     parameters={"cell": {"textValue" : "a549"}, 'test': {"loValue" : 25, "unit" : "C" }},
# )
#
# #json_string = protocol_app.to_json()
# #print(json_string)
# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(protocol_app.__dict__)
# print(m2n.SampleLink(substance=m2n.Sample(uuid="sample-uuid")).to_json())
# protocol_app.to_json()
# print('protocol app')
# print(protocol_app)
#
#
# # EffectRecord = create_model('EffectRecord', __base__=EffectRecord)
#
#
#
#
# from typing import List
# import pprint
# import json
# from pynanomapper.datamodel.ambit import EffectRecord,EffectResult, EffectArray, ValueArray, Protocol, EndpointCategory, ProtocolApplication
# from typing import Dict, Optional, Union
# import numpy as np
#
# # Creating an instance of Dict[str, ValueArray]
# data_dict: Dict[str, ValueArray] = {
#     'array1': ValueArray(values = np.array([1, 2, 3, 4, 5])),
#     'array2': ValueArray(values = np.array([6, 7, 8, 9, 10])),
# }
#
# effect_list: List[Union[EffectRecord,EffectArray]] = []
# # effect_list.append(EffectRecord(endpoint="Endpoint 1", unit="Unit 1", result = EffectResult(loValue=5.0)))
# ea = EffectArray(endpoint="CTG", unit="Unit ctg",
#                                 signal = ValueArray(values = np.array([11, 22, 33, 44, 55])),
#                                 axes = data_dict, conditions={"time": {"loValue" : "24", 'unit': 'C'}})
# print('///////////////////////// effect array /////////////////////////////////////////////')
# print(ea)
# effect_list.append(ea)
# #effect_list.append(EffectRecord(endpoint="Endpoint 2", unit="Unit 2", loValue=10.0))
# papp = ProtocolApplication(protocol=Protocol(topcategory="TOX",category=EndpointCategory(code="cell viability")),
#                            effects=effect_list,
#                            parameters={"cell": {"textValue" : "a549"}, 'temperature': {"loValue" : 25, "unit" : "C" }})
# print('........................... effect array to json ......................................')
# print(ea.to_json())
# #print(papp)
# # for e in papp.effects:
# #     #rint(e.result)
# #     print('from loop')
# #     print(e.to_json())
# #     #json.dumps(e)
#
# print(papp.to_json())
