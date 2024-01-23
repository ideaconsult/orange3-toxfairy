# + tags=["parameters"]
upstream = None
product = None
folder_input: None
files_input: None
metadata_template: None

# -

import pandas as pd
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
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


def create_datacontainer(endpoint,directory):
    ## Create object as data container for CTG endpoint
    _data = HTS(endpoint)
    _meta = MetaDataReaderTmp(template_test,_data )
    _meta.read_meta_data()

    #print(ctg_data.metadata)
    data_reader = DataReaderTmp(template_test, directory, _data)
    data_reader.read_data()
    return _data

_config = {"ctg" : {"dir" : directories[0]},"dapi" : {"dir" : directories[1]},"casp": {"dir" : directories[0]}}
_data = {}
_mode = "w"
for endpoint in _config:
    _data[endpoint] = create_datacontainer(endpoint,_config[endpoint]["dir"])
    _config[endpoint]["metadata"] = _data[endpoint].metadata
    _config[endpoint]["data"] = os.path.join(product["data"],"{}.txt".format(endpoint))
    _data[endpoint].raw_data_df.to_csv(_config[endpoint]["data"] ,sep="\t",index=None)
    #test 
    _data[endpoint].raw_data_df.to_hdf(os.path.join(product["data"],"hts.h5"), key=endpoint, mode=_mode)
    _mode = 'a'

#with open(os.path.join(product["data"],"hts.json"), 'w') as json_file:
#    json.dump(_config, json_file, indent=2) 
with open(os.path.join(product["data"],"metadata.pkl"), 'wb') as pickle_file:
    pickle.dump(_config, pickle_file)    


from pynanomapper.datamodel.ambit import  EffectArray, ValueArray, Protocol, \
    EndpointCategory, ProtocolApplication,  SubstanceRecord, Substances
from pynanomapper.datamodel.ambit import configure_papp
from typing import Dict


# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)


def hts2df(raw_data_df,metadata,endpoint='ctg'):
    id_vars = ['cells', 'replicates', 'time']
    value_vars = raw_data_df.columns[3:]  # A1 to P24
    # Use the melt function to transform the DataFrame
    melted_df = pd.melt(raw_data_df, id_vars=id_vars, value_vars=value_vars, var_name='row', value_name='values')
    df = pd.DataFrame(metadata.values(), index=metadata.keys()) #materials
    result_df = pd.merge(df, melted_df, left_index=True, right_on='row')
    result_df["endpoint"] = endpoint
    result_df['time_unit'] = result_df['time'].str.extract(r'([a-zA-Z]+)')
    result_df['time'] = result_df['time'].str.extract(r'(\d+)').astype(int)
    result_df['replicates'] = result_df['replicates'].str.extract(r'(\d+)').astype(int)    
    return result_df

import matplotlib.pyplot as plt
import plotly.express as px

def htsdf2ambit(result_df,endpoint,substance_owner="HARMLESS",dataprovider="Misvik",substance_records = [],plot = False):
    for material in result_df["material"].unique():
        substance = SubstanceRecord(name=material,ownerName=substance_owner)
        substance.study = []
        tmp = result_df.loc[result_df["material"]==material]
        for cell in tmp["cells"].unique():
            slice = tmp.loc[tmp["cells"]==cell]
            # one ProtocolApplication per endpoint. 
            # instead we can one protocol app per all 5 endpoints
            # and use NeXus SUBENTRY for endpoint: (optional) NXsubentry Group of multiple application definitions for “multi-modal” (e.g. SAXS/WAXS) measurements.
            # but ambit data model does not support it (yet)
            # m/b structure NeXus hierarchy as investigation, not endpoint category?
            papp = ProtocolApplication(
                    protocol=Protocol(topcategory="TOX", category=EndpointCategory(code="ENM_0000068_SECTION"), endpoint=endpoint),
                    effects=[])
            configure_papp(papp,
                provider=dataprovider,
                sample = material,
                sample_provider = substance_owner,
                investigation="WP3",
                year=2023,
                prefix="TOX5",
                meta =  {'E.cell_type': cell }
                )
            # Creating a 3D array
            concentration_values = np.sort(slice['concentration'].unique())
            time_values = np.sort(slice['time'].unique())
            replicates_values = np.sort(slice['replicates'].unique())

            time_unit_values = np.sort(slice['time_unit'].unique())
            #Reshaping the values into a 3D array
            result_array = np.zeros((len(concentration_values), len(time_values), len(replicates_values)))
            for index, row in slice.iterrows():
                conc_idx = np.where(concentration_values == row['concentration'])[0][0]
                time_idx = np.where(time_values == row['time'])[0][0]
                rep_idx = np.where(replicates_values == row['replicates'])[0][0]
                result_array[conc_idx, time_idx, rep_idx] = row['values']


                #tmp_cell_time = tmp_cell.loc[tmp_cell["time"]==time].sort_values(by=["concentration"], ascending=True)
            data_dict: Dict[str, ValueArray] = {
                    'CONCENTRATION': ValueArray(values=concentration_values, unit='ug/ml')
                    ,'E.EXPOSURE_TIME': ValueArray(values=time_values, unit=time_unit_values[0].lower())
                    ,'REPLICATE': ValueArray(values=replicates_values)
                    #,"well" :  ValueArray(values=np.array(['' if (x is None ) else x.encode('ascii', errors='ignore') for x in tmp_cell_time["row"].values]))
                }
            ea = EffectArray(endpoint=endpoint.upper(), unit="", endpointtype='RAW_DATA',
                                signal=ValueArray(values=result_array, unit=''),
                                axes=data_dict
                                )                   
            papp.effects.append(ea)
            substance.i5uuid  = "{}-{}".format("TOX5",uuid.uuid5(uuid.NAMESPACE_OID,material))                
            substance.study.append(papp)
        if plot:
            plt.figure()
            fig = px.scatter(tmp, x='concentration', y='values', color='material',
                facet_col='time', facet_row='cells', labels={'values': 'Values', 'concentration': 'Concentration'})

                # Update layout and show the plot
            fig.update_layout(title='Concentration vs Values Faceted Plot', height=800, width=800)
            fig.show()
        substance_records.append(substance) 

    return substance_records  


import nexusformat.nexus.tree as nx
import os 
from pynanomapper.datamodel.nexus_writer import to_nexus



for endpoint in _config:
    print(endpoint)
    substance_records = []
    result_df = hts2df(_data[endpoint].raw_data_df,_data[endpoint].metadata,endpoint)
    result_df["values"] = result_df["values"].astype(float) 
    result_df.to_csv(os.path.join(product["data"],"{}_melted.txt".format(endpoint)),sep="\t",index=False)
    #result_df = pd.read_csv(os.path.join(product["data"],"{}_melted.txt".format(endpoint)),sep="\t")
    #print(result_df.info())
    substance_records = htsdf2ambit(result_df,endpoint,substance_owner="HARMLESS",dataprovider="Misvik",substance_records=substance_records)

    substances = Substances(substance=substance_records)    
    nxroot = nx.NXroot()
    substances.to_nexus(nxroot)
    nxroot.save(os.path.join(product["data"],"{}.nxs".format(endpoint)),mode="w")
    

