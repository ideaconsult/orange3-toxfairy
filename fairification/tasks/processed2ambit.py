# + tags=["parameters"]
upstream = ["hts2ambit"]
product = None

# -

import os.path
import pandas as pd
import nexusformat.nexus.tree as nx
from pynanomapper.datamodel.ambit import  EffectArray, ValueArray, Protocol, \
    EndpointCategory, ProtocolApplication,  SubstanceRecord , Substances
from pynanomapper.datamodel.nexus_writer import to_nexus
from pynanomapper.datamodel.ambit import configure_papp
from typing import Dict
import numpy as np
import uuid

print(upstream["hts2ambit"])

_config = {"ctg" : {},"dapi" : {},"casp": {}}


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

            time_unit_values = np.sort(slice['time_unit'].unique())
            #Reshaping the values into a 3D array
            result_array = np.zeros((len(concentration_values), len(time_values)))
            for index, row in slice.iterrows():
                conc_idx = np.where(concentration_values == row['concentration'])[0][0]
                time_idx = np.where(time_values == row['time'])[0][0]
                result_array[conc_idx, time_idx] = row['median']


                #tmp_cell_time = tmp_cell.loc[tmp_cell["time"]==time].sort_values(by=["concentration"], ascending=True)
            data_dict: Dict[str, ValueArray] = {
                    'CONCENTRATION': ValueArray(values=concentration_values, unit='ug/ml')
                    ,'E.EXPOSURE_TIME': ValueArray(values=time_values, unit=time_unit_values[0].lower())
                    #,"well" :  ValueArray(values=np.array(['' if (x is None ) else x.encode('ascii', errors='ignore') for x in tmp_cell_time["row"].values]))
                }
            ea = EffectArray(endpoint=endpoint.upper(), unit="", endpointtype='MEDIAN',
                                signal=ValueArray(values=result_array, unit=''),
                                axes=data_dict
                                )                   
            papp.effects.append(ea)
            substance.i5uuid  = "{}-{}".format("TOX5",uuid.uuid5(uuid.NAMESPACE_OID,material))                
            substance.study.append(papp)
        substance_records.append(substance) 

    return substance_records  

#this is a test to write into existing nexus file    
path = upstream["hts2ambit"]["data"]
for endpoint in _config:
    result_df = pd.read_csv(os.path.join(path,"{}_melted.txt".format(endpoint)),sep="\t")
    groupby_columns = [col for col in result_df.columns if col not in  ['replicates', 'values']]
    result_df = result_df.groupby(groupby_columns)['values'].agg(['mean', 'median', 'std']).reset_index()
    print(result_df.columns)
    result_df.to_csv(os.path.join(path,"{}_median.txt".format(endpoint)),sep="\t",index=False)
    
    with nx.load(os.path.join(path,"{}.nxs".format(endpoint)),mode="a") as nxroot:
        substance_records = []
        substance_records = htsdf2ambit(result_df,endpoint,substance_owner="HARMLESS",dataprovider="Misvik",substance_records=substance_records)

        substances = Substances(substance=substance_records)    
        substances.to_nexus(nx_root=nxroot)
    #nxroot.save(os.path.join(path,"{}.nxs".format(endpoint)))

#os.path.join(product["data"],"{}.nxs".format(endpoint)),mode="w")