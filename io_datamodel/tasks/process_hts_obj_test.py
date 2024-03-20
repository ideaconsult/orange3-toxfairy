# + tags=["parameters"]
upstream = ["ambit2hts"]
product = None
folder_output = None
folder_input = None
files_input = None
metadata_templates = None
# -
from TOX5.calculations.dapi_normalization import DapiNormalization
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.calculations.casp_normalization import CaspNormalization
from TOX5.calculations.ohg_h2ax_normalization import OHGH2AXNormalization
from TOX5.calculations.dose_response import DoseResponse
from TOX5.calculations.tox5 import TOX5
from TOX5.misc.utils import plot_tox_rank_pie
import matplotlib.pyplot as plt
import pandas as pd
import os.path
import pickle

#Preprocess calibrate data with serum for methods: CTG, DAPI, CASP and calculate tox5 scores based on endpoint-timepoint grouping

# Read CTG data, extracted from calibrate database and save as a pickle object
# Normalize and calculate dose-response parameters

path = upstream["ambit2hts"]["data"]
with open(os.path.join(path, "ctg_data_w.pkl"), 'rb') as f:
    data_w = pickle.load(f)

ctg_normalizer = CTGNormalization(data_w)
ctg_normalizer.remove_outliers_by_quantiles()
ctg_normalizer.median_control(data_w.normalized_df)
ctg_normalizer.subtract_blank(data_w.normalized_df)
ctg_normalizer.calc_mean_median()

dose_params = DoseResponse(data_w)
dose_params.dose_response_parameters()

print(data_w.raw_data_df)
print(data_w.endpoint)
print(data_w.serum_used)
print(data_w.normalized_df)
print(data_w.mean_df)
print(data_w.median_df)
print(data_w.dose_response_df)

# Read imaging data from local files

template_test = [os.path.join(folder_input, file) for file in metadata_templates.split(",")]
directories = [os.path.join(folder_input, file) for file in files_input.split(",")]

# process technical replicate a and b (a= dapi, H2AX+8OHG plate, b = dapi + apoptosis plate) and serum used
dapi_data_A = HTS('dapiA')
dapi_data_A.serum_used = True
dapi_meta = MetaDataReaderTmp(template_test[0], dapi_data_A)
dapi_meta.read_meta_data()
dapi_data_reader = DataReaderTmp(template_test[0], directories[0], dapi_data_A)
dapi_data_reader.read_data()
dapi_data_A.raw_data_df = dapi_data_A.raw_data_df[dapi_data_A.raw_data_df['Description'] != '_']
dapi_data_A.raw_data_df = dapi_data_A.raw_data_df[dapi_data_A.raw_data_df['Description'] == dapi_data_A.endpoint] \
    .reset_index(drop=True).drop(['Description'], axis=1)
dapi_normalizerA = DapiNormalization(dapi_data_A)
dapi_normalizerA.remove_outliers_by_quantiles()
dapi_normalizerA.median_control(dapi_data_A.normalized_df)

dapi_data_B = HTS('dapiB')
dapi_data_B.serum_used = True
dapi_meta = MetaDataReaderTmp(template_test[0], dapi_data_B)
dapi_meta.read_meta_data()
dapi_data_reader = DataReaderTmp(template_test[0], directories[0], dapi_data_B)
dapi_data_reader.read_data()
dapi_data_B.raw_data_df = dapi_data_B.raw_data_df[dapi_data_B.raw_data_df['Description'] != '_']
dapi_data_B.raw_data_df = dapi_data_B.raw_data_df[dapi_data_B.raw_data_df['Description'] == dapi_data_B.endpoint] \
    .reset_index(drop=True).drop(['Description'], axis=1)
dapi_normalizer = DapiNormalization(dapi_data_B)
dapi_normalizer.remove_outliers_by_quantiles()
dapi_normalizer.median_control(dapi_data_B.normalized_df)

# for dapi data the two technical replicates (a+b) are first averaged, then median of the four biological replicates is counted
combined_df = pd.concat([dapi_data_B.normalized_df.groupby(['replicates', 'time', 'cells']).mean(),
                         dapi_data_A.normalized_df.groupby(['replicates', 'time', 'cells']).mean()])
average_df = combined_df.groupby(['replicates', 'time', 'cells']).mean()
average_df.reset_index(inplace=True)
dapi_data_A.normalized_df = average_df
dapi_normalizerA.calc_mean_median()


dapi_dose = DoseResponse(dapi_data_A)
dapi_dose.dose_response_parameters()
dapi_data_A.endpoint = 'dapi'

print(dapi_data_A.endpoint)
print(dapi_data_A.metadata)
print(dapi_data_A.serum_used)
print(dapi_data_A.raw_data_df)
print(dapi_data_A.dose_response_df)

# Process caspace

casp_data = HTS('casp')
casp_data.serum_used = True
casp_meta = MetaDataReaderTmp(template_test[0], casp_data)
casp_meta.read_meta_data()
casp_data_reader = DataReaderTmp(template_test[0], directories[0], casp_data)
casp_data_reader.read_data()
casp_data.raw_data_df = casp_data.raw_data_df[casp_data.raw_data_df['Description'] != '_']
casp_data.raw_data_df = casp_data.raw_data_df[casp_data.raw_data_df['Description'] == casp_data.endpoint] \
    .reset_index(drop=True).drop(['Description'], axis=1)

new_column_names = dapi_data_A.mean_df.columns
print(new_column_names)
data_w.mean_df.columns = new_column_names
print(data_w.mean_df.head())
casp_normalizer = CaspNormalization(casp_data, data_w.mean_df, dapi_data_A.mean_df)
casp_normalizer.remove_outliers_by_quantiles()
casp_normalizer.median_control(casp_data.normalized_df)
casp_normalizer.calc_mean_median()
casp_dose = DoseResponse(casp_data)
casp_dose.dose_response_parameters()

print(casp_data.endpoint)
print(casp_data.raw_data_df)
print(casp_data.normalized_df)
print(casp_data.median_df)

# TOX5 grouping only for dapi, ctg and casp with serum treated
df = pd.concat([casp_data.dose_response_df,
                data_w.dose_response_df,
                dapi_data_A.dose_response_df], axis=1)
df = df.reset_index().rename(columns={'index': 'material'})

tox5 = TOX5(df, ['BEAS-2B'])
user_selected_transform_functions = {
    "1st": "log10x_6",
    "auc": "sqrt_x",
    "max": "log10x_6"
}
tox5.transform_data(user_selected_transform_functions)
tox5.generate_auto_slices()
tox5.calculate_tox5_scores()
print(tox5.tox5_scores)

materials = ['Gemcitabine', 'Mitomycin C ', 'Non-porous Silica 300nm-Me', 'Sodiumhexametaphosphate', 'TiO2', 'A1 Silver nanoparticles']
figure, legend = plot_tox_rank_pie(tox5.tox5_scores, materials)
## show all materials
# figure, legend = plot_tox_rank_pie(tox5.tox5_scores)

plt.show()
legend.show()
