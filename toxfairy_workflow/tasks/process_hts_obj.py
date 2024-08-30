# + tags=["parameters"]
upstream = ["ambit_data2HTS_obj", "local_data2HTS_obj"]
product = None
folder_output = None
config_file = None
config_key = None
# -
from toxfairy.src.toxfairy.calculations.cell_viability_normalization import CellViabilityNormalization
from toxfairy.src.toxfairy.calculations.dna_damage_normalization import DNADamageNormalization
from toxfairy.src.toxfairy.endpoints.hts_data_container import HTS
from toxfairy.src.toxfairy.calculations.dose_response import DoseResponse
from toxfairy.src.toxfairy.calculations.basic_normalization import BasicNormalization
import pandas as pd
import os.path
import pickle
import json

# Read CTG data, extracted from calibrate database and save as a pickle object, other imaging endpoint read from local files
# Treat data with and without serum as a separate data
# Normalize and calculate dose-response parameters

path_db = upstream["ambit_data2HTS_obj"]["data_obj"]
path_local = upstream["local_data2HTS_obj"]["data"]

directories = [path_db, path_local]
combined_dict = {"w": {}, "wo": {}}


# Function to process a single directory
def process_directory(directory):
    if not os.listdir(directory):
        print(f"The directory {directory} is empty.")
        return

    for filename in os.listdir(directory):
        if filename.endswith(".pkl"):
            # Split the filename to categorize it
            parts = filename.split('_')
            if len(parts) >= 3:
                category_key = parts[2].split('.')[0]  # Extract the part after the second underscore
                nested_key = parts[0]  # Extract the first part before the first underscore
                print(f"Category Key: {category_key}, Nested Key: {nested_key}")

                # Read the .pkl file
                with open(os.path.join(directory, filename), 'rb') as file:
                    obj = pickle.load(file)

                if category_key not in combined_dict:
                    combined_dict[category_key] = {}

                combined_dict[category_key][nested_key] = obj


for directory in directories:
    process_directory(directory)


def normalize_data(_data, endpoint='ctg', assay_type="viability", ctg_data_mean=None, dapi_data_mean=None):
    if assay_type == "viability":
        normalizer = CellViabilityNormalization(_data)
        normalizer.remove_outliers_by_quantiles()

        if endpoint.lower() == 'ctg':
            normalizer.percentage_effect_from_median_control(_data.normalized_df)
            normalizer.subtract_blank(_data.normalized_df)
        if endpoint.lower() == 'casp':
            normalizer.percentage_of_median_control(_data.normalized_df)
            normalizer.subtract_blank_as_percent(_data.normalized_df)
            normalizer.normalize_data_to_cell_count(ctg_data_mean, dapi_data_mean)
        normalizer.calc_mean_median()

    elif assay_type == "imaging":
        normalizer = DNADamageNormalization(_data)
        normalizer.clean_dna_raw()
        normalizer.remove_outliers_by_quantiles()
        if "dapi" in endpoint.lower():
            normalizer.percentage_effect_from_median_control(_data.normalized_df)
        if endpoint.lower() == 'h2ax' or endpoint.lower() == '8ohg':
            normalizer.percentage_of_median_control(_data.normalized_df)
        if endpoint.lower() == 'casp':
            normalizer.percentage_effect_from_median_control(_data.normalized_df)
        normalizer.calc_mean_median()


def combine_hts_objects(hts_obj1: HTS, hts_obj2: HTS, endpoint_name: str) -> HTS:
    combined_df = pd.concat(
        [hts_obj1.normalized_df.groupby(['replicates', 'time', 'cells']).mean(),
         hts_obj2.normalized_df.groupby(['replicates', 'time', 'cells']).mean()]
    )

    average_df = combined_df.groupby(['replicates', 'time', 'cells']).mean()
    average_df.reset_index(inplace=True)

    hts_obj1.normalized_df = average_df
    hts_obj1.endpoint = endpoint_name
    normalizer = BasicNormalization(hts_obj1)
    normalizer.calc_mean_median()

    return hts_obj1


def process_all_hts_obj(hts_obj_dict, processing_order, tech_replicates_endpoints,
                        filtrate_by_materials=None, filtrate_by_cells=None):

    # tech_replicates_endpoints=['tech_repl0', 'tech_repl1', "combined_endpoint_name"]
    # for dapi data the two technical replicates (a+b) are first averaged, then median of the four biological replicates is counted

    if filtrate_by_materials or filtrate_by_cells:
        for obj_key, obj in hts_obj_dict.items():
            obj.filtrate_data(obj.raw_data_df, filtrate_by_materials, filtrate_by_cells)

    tech_repl_1 = None
    tech_repl_2 = None
    new_combined_endpoint = None
    if tech_replicates_endpoints:
        tech_repl_1 = tech_replicates_endpoints[0]
        tech_repl_2 = tech_replicates_endpoints[1]
        new_combined_endpoint = tech_replicates_endpoints[2]

    # for endpoint, obj in hts_obj_dict.items():
    for endpoint in processing_order:
        obj = hts_obj_dict[endpoint]

        if endpoint == tech_repl_2 and hts_obj_dict[tech_repl_1].normalized_df is not None:
            normalize_data(obj, obj.endpoint, obj.assay_type)
            hts_obj_dict[new_combined_endpoint] = combine_hts_objects(hts_obj_dict[tech_repl_1],
                                                                      hts_obj_dict[tech_repl_2], new_combined_endpoint)
            hts_obj_dict[new_combined_endpoint].endpoint = new_combined_endpoint

        elif endpoint == 'CASP' and obj.assay_type == 'viability':
            if hts_obj_dict['DAPI'].mean_df is not None and hts_obj_dict['CTG'].mean_df is not None:
                normalize_data(obj, obj.endpoint, obj.assay_type,
                               ctg_data_mean=hts_obj_dict['DAPI'].mean_df,
                               dapi_data_mean=hts_obj_dict['CTG'].mean_df)
        else:
            normalize_data(obj, obj.endpoint, obj.assay_type)
        dose_response = DoseResponse(obj)
        dose_response.dose_response_parameters()

    if tech_replicates_endpoints:
        del hts_obj_dict[tech_repl_1]
        del hts_obj_dict[tech_repl_2]


def pkl_hts_obj(hts_obj):
    for key, obj in hts_obj.items():
        if obj.serum_used:
            file_name = f'{obj.endpoint}_data_w.pkl'
        else:
            file_name = f'{obj.endpoint}_data_wo.pkl'

        with open(os.path.join(product['data'], file_name), 'wb') as f:
            pickle.dump(obj, f)


def loadconfig(config_file, config_key, subkey="extract"):
    with open(config_file) as f:
        cfg = json.load(f)
    return cfg[config_key][subkey]


extract_config = loadconfig(config_file, config_key, "processing")
filtrate_materials = extract_config["filtrate_materials"]
filtrate_cells = extract_config["filtrate_cells"]
print(extract_config["tech_replicates_endpoints"])
print(filtrate_materials)
print(filtrate_cells)

os.makedirs(product["data"], exist_ok=True)
if os.path.exists(product["data"]):
    files = os.listdir(product["data"])
    for file in files:
        os.remove(os.path.join(product["data"], file))

for key, objs in combined_dict.items():
    if objs:
        process_all_hts_obj(objs, extract_config["endpoint_order"], extract_config["tech_replicates_endpoints"],
                            filtrate_materials, filtrate_cells)
        pkl_hts_obj(objs)
