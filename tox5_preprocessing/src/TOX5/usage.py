
from tox5_preprocessing.src.TOX5.factory.endpoint_factory import *
from tox5_preprocessing.src.TOX5.factory.normalize_factory import create_normalize_data
from tox_orange_demo.toxpi_data_prep import *

annot_file = 'D:/PhD/projects/ToxPi/tox_data/vesa_files/HARMLESS_screens_clean.xlsx'
files_path = 'D:/PhD/projects/ToxPi/tox_data/vesa_files/raw_data'


df_img = read_imaging_raw(annot_file, 'Imaging raw')
df_img_clean = clean_imaging_raw(df_img)
df_img_new = create_imaging_cleaned_df(df_img_clean, 'Dapi', annot_file)
df_img_outlayers = remove_outlayer(df_img_new)
df_img_s = percent_of_median_control(df_img_outlayers, 'Dapi')
df_img_5 = calc_imaging_stat(df_img_s, annot_file)
df_img_6_median, df_img_6_mean = calc_mean_median(df_img_5, annot_file)
# print(df_img_5)
# print(df_img_6_median)
# print(df_img_6_mean)

df_ctg = read_raw_data('CTG', annot_file, files_path)
df_ctg_2 = remove_outlayer(df_ctg)
df_ctg_3 = percent_of_median_control(df_ctg_2, 'CTG')
df_ctg_percent_0 = median_0_h(df_ctg_3)
df_ready = subtract_median_0_h(df_ctg_percent_0, 'CTG', annot_file)
df_median, df_mean = calc_mean_median(df_ready, annot_file)
# print(df_ready)
# print(df_median)
# print(df_mean)

df_casp = read_raw_data('Casp', annot_file, files_path)
df_casp_2 = remove_outlayer(df_casp)
df_casp_3 = percent_of_median_control(df_casp_2, 'Casp')
df_casp_percent_0 = median_0_h(df_casp_3)
df_ready_casp = subtract_median_0_h(df_casp_percent_0, 'Casp', annot_file)
median_df_casp, mean_df_casp, df_ready_casp_ = calc_paramc_casp(annot_file, df_mean, df_img_6_mean, df_ready_casp)
print(df_ready_casp_)
print(median_df_casp)
print(mean_df_casp)

print('*****************************************************************************************************************')


ctg_data = create_data('CTG', files_path, annot_file)
ctg_data.read_data()
ctg_normalized = create_normalize_data('CTG_normalize', ctg_data)
ctg_normalized.normalize_data()

dapi_data = create_data('Dapi', files_path, annot_file, 'Imaging raw')
dapi_data.read_data()
dapi_norm = create_normalize_data('Dapi_normalize', dapi_data)
dapi_norm.normalize_data()

casp_data = create_data('Casp', files_path, annot_file)
casp_data.read_data()
casp_norm = create_normalize_data('Casp_normalize', casp_data, ctg_data, dapi_data)
casp_norm.normalize_data()

print(casp_data.normalized_df)
print(casp_data.median_df)
print(casp_data.mean_df)
