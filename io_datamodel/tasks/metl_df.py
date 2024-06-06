# + tags=["parameters"]
upstream = ["process_hts_obj"]
product = None
# -

import pandas as pd
import os.path
import pickle


def load_pickles_from_directory(directory):
    pickle_hts_data = {}
    for filename in os.listdir(directory):
        if filename.endswith(".pkl"):
            key = filename.split('_')[0]
            key += "_" + filename.split('_')[2]
            key = key.split('.')[0]
            file_path = os.path.join(directory, filename)
            with open(file_path, 'rb') as f:
                pickle_hts_data[key] = pickle.load(f)
    return pickle_hts_data


path = upstream["process_hts_obj"]["data"]
pickle_hts_data = load_pickles_from_directory(path)
print(pickle_hts_data.keys())


def get_metric_value(split_list):
    if len(split_list) == 4:
        return split_list[2]
    elif len(split_list) == 5:
        return f"{split_list[2]}_{split_list[3]}"


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


os.makedirs(product["data"], exist_ok=True)
if os.path.exists(product["data"]):
    files = os.listdir(product["data"])
    for file in files:
        os.remove(os.path.join(product["data"], file))

for key_endpoint, obj in pickle_hts_data.items():
    endpoint = obj.endpoint
    res_raw_data = hts2df(obj.raw_data_df, obj.metadata, endpoint, 'raw_data')
    res_norm_data = hts2df(obj.normalized_df, obj.metadata, endpoint, 'normalized_data')
    res_median_data = hts2df(obj.median_df, obj.metadata, endpoint, 'median_data')
    res_dose_response_data = hts2df(obj.dose_response_df, obj.metadata, endpoint,
                                    'dose_response_data')

    for df_name, df in zip(["raw_data", "normalized_data", "median_data", "dose-response_data"],
                           [res_raw_data, res_norm_data, res_median_data, res_dose_response_data]):
        file_name = os.path.join(product["data"], "{}_{}_melted.txt".format(key_endpoint, df_name))
        # endpoint[df_name] = file_name
        df.to_csv(file_name, sep="\t")

