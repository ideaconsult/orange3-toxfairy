import pandas as pd
import nexusformat.nexus.tree as nx
from pynanomapper.datamodel.ambit import EffectArray, ValueArray, Protocol, \
    EndpointCategory, ProtocolApplication, SubstanceRecord, Substances
from pynanomapper.datamodel.nexus_writer import to_nexus
from pynanomapper.datamodel.ambit import configure_papp
from typing import Dict
import numpy as np
import uuid


def get_metric_value(split_list):
    if len(split_list) == 4:
        return split_list[2]
    elif len(split_list) == 5:
        return f"{split_list[2]}_{split_list[3]}"


def hts2df(raw_data_df, metadata, endpoint='ctg', result_type='raw_data'):
    result_df = pd.DataFrame()
    if result_type == 'raw_data' or result_type == 'normalized_data':
        id_vars = ['cells', 'replicates', 'time']
        value_vars = raw_data_df.columns[3:]
        melted_df = pd.melt(raw_data_df, id_vars=id_vars, value_vars=value_vars, var_name='row', value_name='values')
        df = pd.DataFrame(metadata.values(), index=metadata.keys())
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


def htsdf2ambit(result_df, endpoint, substance_owner="HARMLESS", dataprovider="Misvik", substance_records=[],
                endpoint_type='RAW',
                serum_used=False):
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
            if serum_used:
                serum = 'LHC-9 Thermo-Fisher Scientific / Gibco #12680013 supplemented with 10% fetal bovine serum ' \
                        '(Biowest S181B-500) for duration of the nanomaterial exposure'
            else:
                serum = 'LHC-9 Thermo-Fisher Scientific / Gibco #12680013 supplemented'
            papp = ProtocolApplication(
                protocol=Protocol(topcategory="TOX", category=EndpointCategory(code="ENM_0000068_SECTION"),
                                  endpoint=endpoint), effects=[])
            configure_papp(papp,
                           provider=dataprovider,
                           sample=material,
                           sample_provider=substance_owner,
                           investigation="WP5",
                           year=2018,
                           prefix="TOX5",
                           meta={'E.cell_type': cell, "E.method": endpoint.upper(), "MEDIUM": serum}
                           )
            if endpoint_type == 'MEDIAN':
                # TODO:  add standard deviation
                # errQualifier: Optional[str] = None
                # errorValue: Optional[Union[NDArray, None]] = None

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
                                 signal=ValueArray(values=result_array, unit=''
                                                   # , errQualifier='sd',
                                                   #  errorValue= [[,]]
                                                   ),
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


def add_to_nxs(nxs_file, substance_owner, data_provider, melted_dfs_dict):
    with nx.load(nxs_file, mode="a") as nxroot:
        for endpoint_type, endpoints in melted_dfs_dict.items():
            for endpoint, df in endpoints.items():
                result_df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                substance_records = []
                substance_records = htsdf2ambit(result_df, endpoint, substance_owner=substance_owner,
                                                dataprovider=data_provider,
                                                substance_records=substance_records,
                                                endpoint_type=endpoint_type.upper())

                substances = Substances(substance=substance_records)
                substances.to_nexus(nx_root=nxroot)
