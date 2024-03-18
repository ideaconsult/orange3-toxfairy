# + tags=["parameters"]
upstream = ["ambit2hts"]
product = None
folder_output = None
# -

from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.calculations.dose_response import DoseResponse
import os.path
import pickle

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
