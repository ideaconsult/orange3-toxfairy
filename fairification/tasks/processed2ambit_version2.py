# + tags=["parameters"]
upstream = ["hts2ambit_norm"]
product = None

# -

import os.path
import pandas as pd
import nexusformat.nexus.tree as nx
from pynanomapper.datamodel.ambit import EffectArray, ValueArray, Protocol, \
    EndpointCategory, ProtocolApplication, SubstanceRecord, Substances
from pynanomapper.datamodel.nexus_writer import to_nexus
from pynanomapper.datamodel.ambit import configure_papp
from typing import Dict
import numpy as np
import uuid

# print(upstream["hts2ambit"])

_config = {"ctg": {}, "dapi": {}, "casp": {}, 'h2ax': {}, '8ohg': {}}


def htsdf2ambit(result_df, endpoint, substance_owner="HARMLESS", dataprovider="Misvik", substance_records=[],
                endpoint_type='RAW',
                plot=False):
    for material in result_df["material"].unique():
        substance = SubstanceRecord(name=material, ownerName=substance_owner)
        substance.study = []
        tmp = result_df.loc[result_df["material"] == material]
        for cell in tmp["cells"].unique():
            slice = tmp.loc[tmp["cells"] == cell]
            # one ProtocolApplication per endpoint.
            # instead we can one protocol app per all 5 endpoints
            # and use NeXus SUBENTRY for endpoint: (optional) NXsubentry Group of multiple application definitions for “multi-modal” (e.g. SAXS/WAXS) measurements.
            # but ambit data model does not support it (yet)
            # m/b structure NeXus hierarchy as investigation, not endpoint category?
            papp = ProtocolApplication(
                protocol=Protocol(topcategory="TOX", category=EndpointCategory(code="ENM_0000068_SECTION"),
                                  endpoint=endpoint),
                effects=[])
            configure_papp(papp,
                           provider=dataprovider,
                           sample=material,
                           sample_provider=substance_owner,
                           investigation="WP3",
                           year=2023,
                           prefix="TOX5",
                           meta={'E.cell_type': cell , "E.method" : endpoint.upper() }
                           )
            if endpoint_type == 'MEDIAN':

                concentration_values = np.sort(slice['concentration'].unique())
                time_values = np.sort(slice['time'].unique())
                time_unit_values = np.sort(slice['time_unit'].unique())
                result_array = np.zeros((len(concentration_values), len(time_values)))
                for index, row in slice.iterrows():
                    conc_idx = np.where(concentration_values == row['concentration'])[0][0]
                    time_idx = np.where(time_values == row['time'])[0][0]
                    result_array[conc_idx, time_idx] = row['values']
                data_dict: Dict[str, ValueArray] = {
                    'CONCENTRATION': ValueArray(values=concentration_values, unit='ug/ml')
                    , 'E.EXPOSURE_TIME': ValueArray(values=time_values, unit=time_unit_values[0].lower())
                }
                ea = EffectArray(endpoint=endpoint.upper(), unit="", endpointtype=endpoint_type,
                                 signal=ValueArray(values=result_array, unit=''),
                                 axes=data_dict)

                papp.effects.append(ea)

            elif endpoint_type == "RAW" or endpoint_type == "NORMALIZED":
                concentration_values = np.sort(slice['concentration'].unique())
                time_values = np.sort(slice['time'].unique())
                time_unit_values = np.sort(slice['time_unit'].unique())
                replicates = np.sort(slice['replicates'].unique())
                result_array = np.zeros((len(concentration_values), len(time_values), len(replicates)))
                for index, row in slice.iterrows():
                    conc_idx = np.where(concentration_values == row['concentration'])[0][0]
                    time_idx = np.where(time_values == row['time'])[0][0]
                    rep_idx = np.where(replicates == row['replicates'])[0][0]
                    result_array[conc_idx, time_idx, rep_idx] = row['values']

                data_dict: Dict[str, ValueArray] = {
                    'CONCENTRATION': ValueArray(values=concentration_values, unit='ug/ml'),
                    'E.EXPOSURE_TIME': ValueArray(values=time_values, unit=time_unit_values[0].lower()),
                    'REPLICATE': ValueArray(values=replicates),
                }
                ea = EffectArray(endpoint=endpoint.upper(), unit="", endpointtype=endpoint_type,
                                 signal=ValueArray(values=result_array, unit=''),
                                 axes=data_dict)

                papp.effects.append(ea)

            elif endpoint_type == 'DOSE-RESPONSE':
                time_values = np.sort(slice['time'].unique())
                time_unit_values = np.sort(slice['time_unit'].unique())
                data_dict: Dict[str, ValueArray] = {
                    'E.EXPOSURE_TIME': ValueArray(values=time_values, unit=time_unit_values[0].lower()),
                }

                result_array_dict = {}
                for metric_u in slice['metric'].unique():
                    result_array_tmp = np.zeros((len(time_values),))
                    for index, row in slice.iterrows():
                        time_idx = np.where(time_values == row['time'])[0][0]
                        result_array_tmp[time_idx] = row['values']
                    result_array_dict[metric_u] = result_array_tmp

                ea_max = EffectArray(endpoint=endpoint.upper(), unit="", endpointtype='MAX_EFFECT',
                                     signal=ValueArray(values=result_array_dict['MAX'], unit=''),
                                     axes=data_dict)
                ea_auc = EffectArray(endpoint=endpoint.upper(), unit="", endpointtype='AUC',
                                     signal=ValueArray(values=result_array_dict['AUC'], unit=''),
                                     axes=data_dict)
                ea_frst_2sd = EffectArray(endpoint=endpoint.upper(), unit="", endpointtype='FIRST_DOSE_2SD',
                                          signal=ValueArray(values=result_array_dict['1st_2SD'], unit=''),
                                          axes=data_dict)
                ea_frst_3sd = EffectArray(endpoint=endpoint.upper(), unit="", endpointtype='FIRST_DOSE_3SD',
                                          signal=ValueArray(values=result_array_dict['1st_3SD'], unit=''),
                                          axes=data_dict)

                papp.effects.append(ea_max)
                papp.effects.append(ea_auc)
                papp.effects.append(ea_frst_2sd)
                papp.effects.append(ea_frst_3sd)

            substance.i5uuid = "{}-{}".format("TOX5", uuid.uuid5(uuid.NAMESPACE_OID, material))
            substance.study.append(papp)
        substance_records.append(substance)

    return substance_records


path = upstream["hts2ambit_norm"]["data"]

#if we don't remove, mode="a" will add to the file from previous run
if os.path.exists(product["data"]):
    os.remove(product["data"])

def add_to_nxs(_config, *endpoint_types):
    with nx.load(product["data"], mode="a") as nxroot:
        for endpoint_type in endpoint_types:
            for endpoint in _config:
                result_df = pd.read_csv(os.path.join(path, f"{endpoint}_{endpoint_type}_data_melted.txt"), sep="\t")
                result_df = result_df.loc[:, ~result_df.columns.str.contains('^Unnamed')]

            # with nx.load(os.path.join(path, "{}.nxs".format(endpoint)), mode="a") as nxroot:
                substance_records = []
                substance_records = htsdf2ambit(result_df, endpoint, substance_owner="HARMLESS",
                                                dataprovider="Misvik",
                                                substance_records=substance_records,
                                                endpoint_type=endpoint_type.upper())

                substances = Substances(substance=substance_records)
                substances.to_nexus(nx_root=nxroot)


add_to_nxs(_config, 'raw', 'median', 'normalized', 'dose-response')
