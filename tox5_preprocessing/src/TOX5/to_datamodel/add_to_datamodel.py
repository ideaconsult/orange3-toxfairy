import pandas as pd

from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.misc.utils import annotate_data

directories = [
    'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\data\\Misvik high throughput screening data\\Screen1-4_CTG_Caspase_raw_data',
    'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\data\\Misvik high throughput screening data\\Screen1-4_imaging data']
template_test = 'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\TestDataRecordingForm_harmless_HTS_METADATA.xlsx'

# generate_annotation_file(directory_test, template_test)

## Create object as data container for CTG endpoint
ctg_data = HTS('ctg')
print('.............................. CTG endpoint metadata and raw data ............................................ ')
print(ctg_data.endpoint)
## Create object for metadata reader
ctg_meta = MetaDataReaderTmp(template_test, ctg_data)
ctg_meta.read_meta_data()

## recalculate doses
# ctg_meta.recalculate_dose_from_cell_growth(50, 0.079495092) # args: volume in ul, plate growth area
## SBET values are taken from template in sheet Materials and are connected with material name
# ctg_meta.recalculate_dose_from_sbet(50, 0.079495092)

print(ctg_data.metadata)
## Create object for data reader from template
ctg_data_reader = DataReaderTmp(template_test, directories[0], ctg_data)
ctg_data_reader.read_data()
annotate_data(ctg_data.raw_data_df, ctg_data.metadata)
print(ctg_data.raw_data_df)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Data model >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import sys
import os
# project_pynanomapper = os.path.abspath("D:\\PhD\\projects\\ToxPi\\pynanomapper")
# sys.path.append(project_pynanomapper)
import pynanomapper
import requests
import h5py
from pynanomapper.clients.h5converter import AmbitParser
import os.path
from pynanomapper.aa import GraviteeAuth
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
# # import pynanomapper.datamodel.ambit as m2n
# # import pprint
# # import json
# # protocol_app = m2n.ProtocolApplication(
# #     uuid="123",
# #     interpretationResult="result",
# #     effects=[
# #         m2n.EffectRecord(endpoint="CTG", unit="numbered", loValue=5.0), # effectarray
# #         m2n.EffectRecord(endpoint="CASP", unit="Unit 2", loValue=11.0),
# #         m2n.EffectRecord(endpoint="DAPI", unit="unit3", loValue=10.0),
# #         m2n.EffectRecord(endpoint="H2AX", unit="unit4", loValue=10.0),
# #         m2n.EffectRecord(endpoint="ohg", unit="unit5", loValue=10.0),
# #     ],
# #     owner= m2n.SampleLink(substance=m2n.Sample(uuid="sample-uuid")),
# #     parameters={"cell": {"textValue" : "a549"}, 'test': {"loValue" : 25, "unit" : "C" }},
# # )
# #
# # #json_string = protocol_app.to_json()
# # #print(json_string)
# # pp = pprint.PrettyPrinter(indent=4)
# # pp.pprint(protocol_app.__dict__)
# # print(m2n.SampleLink(substance=m2n.Sample(uuid="sample-uuid")).to_json())
# # protocol_app.to_json()
# # print('protocol app')
# # print(protocol_app)
#
#
# # EffectRecord = create_model('EffectRecord', __base__=EffectRecord)
#
#
#
#
from typing import List
import pprint
import json
from pynanomapper.datamodel.ambit import EffectRecord, EffectResult, EffectArray, ValueArray, Protocol, \
    EndpointCategory, ProtocolApplication, Study, SubstanceRecord, Substances
from typing import Dict, Optional, Union
import numpy as np

# Creating an instance of Dict[str, ValueArray]
data_dict: Dict[str, ValueArray] = {
    'concentration': ValueArray(values=np.array([0.1, 2.5, 3, 4, 5]), unit='ug/ml'),
    'time': ValueArray(values=np.array([6, 24, 72])),
    'replicate': ValueArray(values=np.array([1, 2, 3])),
}
endpointtype = 'RAW_DATA'
y = np.array([111, 222, 333, 444, 555, 666, 777, 888, 999])

effect_list: List[Union[EffectRecord, EffectArray]] = []
# effect_list.append(EffectRecord(endpoint="Endpoint 1", unit="Unit 1", result = EffectResult(loValue=5.0)))
ea = EffectArray(endpoint="CTG", unit="count", endpointtype=endpointtype,
                 signal=ValueArray(values=y),
                 axes=data_dict
                 # conditions={"time": {"loValue" : "24", 'unit': 'C'}}
                 )

ea2 = EffectArray(endpoint="CTG", unit="count", endpointtype='Normalized',
                  signal=ValueArray(values=y),
                  axes=data_dict
                  # conditions={"time": {"loValue" : "24", 'unit': 'C'}}
                  )
print('///////////////////////// effect array /////////////////////////////////////////////')
# print(ea)
effect_list.append(ea)
effect_list.append(ea2)
ea3 = EffectArray(endpoint="CTG", unit="count", endpointtype='dose_response',
                  signal=ValueArray(values=y),
                  axes=data_dict
                  # conditions={"time": {"loValue" : "24", 'unit': 'C'}}
                  )

effect_list.append(ea3)
# effect_list.append(EffectRecord(endpoint="Endpoint 2", unit="Unit 2", loValue=10.0))

protocol_app_list: List[ProtocolApplication] = []
papp = ProtocolApplication(
    protocol=Protocol(topcategory="TOX", category=EndpointCategory(code="cell viability"), endpoint='CTG'),
    effects=effect_list,
    parameters={'E.cell_type': {'unit': "a549"}})

papp2 = ProtocolApplication(
    protocol=Protocol(topcategory="TOX", category=EndpointCategory(code="dna damage"), endpoint='DAPI'),
    effects=effect_list,
    parameters={'E.cell_type': {'text': "a549"}})

print('........................... effect array to json ......................................')
# print(ea.to_json())
# print(papp)
# for e in papp.effects:
#     #rint(e.result)
#     print('from loop')
#     print(e.to_json())
#     #json.dumps(e)


protocol_app_list.append(papp)
protocol_app_list.append(papp2)
nm1 = SubstanceRecord(name='nm1', study=protocol_app_list)
nm2 = SubstanceRecord(name='nm2', study=protocol_app_list)
nm1_cell1 = SubstanceRecord(name='nm1', study=protocol_app_list)

substances = Substances(substance=[nm1, nm2, nm1_cell1])
# print(substances.to_json())


# for protocol_app in nm1.study:
#     print(protocol_app.to_json())
# print('//////////////////////////////////////////////// substances //////////////////////////////////////////////////')
#
# for substance in substances.substance:
#     papps = substance.study
#     for papp in papps:
#         print(papp.protocol.to_json())
#         print(papp.parameters)
#         for e in papp.effects:
#             print(e.to_json())


# filtrate by nm and cell
# Get unique values in the 'cells' column
# ctg_data which is container with all data

unique_cells = ctg_data.raw_data_df['cells'].dropna().drop_duplicates().values
print(unique_cells)
#
# # Get unique values in the 'material' row
unique_materials = ctg_data.raw_data_df.loc['material'].dropna().drop_duplicates().values
print(unique_materials)
# filtered_columns = ctg_data.raw_data_df.loc['material', ctg_data.raw_data_df.loc['material'] == 'Bleom']
# fl = ctg_data.raw_data_df.loc[:,ctg_data.raw_data_df.loc['material'] == 'Bleom']
# print(fl)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def create_effect_list():
    pass

dict_effect_list = {}
effect_list: List[Union[EffectRecord, EffectArray]] = []

for i in unique_cells:
    df = ctg_data.raw_data_df[ctg_data.raw_data_df['cells'] == i]
    annotate_data(df, ctg_data.metadata)
    df1 = df.iloc[:, :3]
    for n in unique_materials:

        fl = df.loc[:, df.loc['material'] == n]
        result = pd.concat([df1, fl], axis=1)
        print('new cell and new material')
        print(i)
        print(n)

        df_processed = result.iloc[:-2, 3:]
        np_array = df_processed.values.ravel()

        concentrations = np.array(result.loc['concentration'].dropna().values)
        c = np.tile(concentrations, df_processed.shape[1])
        time = np.array(result['time'].dropna().values)
        t = np.repeat(time, df_processed.shape[1])
        replicate = np.array(result['replicates'].dropna().values)
        r = np.repeat(replicate, df_processed.shape[1])
        #
        # print(np_array)
        #
        # print(c)
        # print(t)
        # print(r)

        data_dict2: Dict[str, ValueArray] = {
            'concentration': ValueArray(values=c, unit='ug/ml'),
            'time': ValueArray(values=t),
            'replicate': ValueArray(values=r),
        }
        ea = EffectArray(endpoint="CTG", unit="count", endpointtype='RAW DATA',
                         signal=ValueArray(values=np_array, unit=''),
                         axes=data_dict2
                         )
        effect_list.append(ea)
        dict_effect_list[f"{i}_{n}"] = ea


print(dict_effect_list)
