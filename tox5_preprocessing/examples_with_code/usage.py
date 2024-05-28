import pandas as pd
from TOX5.calculations.cell_viability_normalization import CellViabilityNormalization
from TOX5.calculations.dna_damage_normalization import DNADamageNormalization
from TOX5.calculations.dose_response import DoseResponse
from TOX5.calculations.tox5 import TOX5
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp

# print(pd.__version__)
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
from TOX5.misc.utils import plot_tox_rank_pie, generate_annotation_file

directories = [
    'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\data\\Misvik high throughput screening data\\Screen1-4_CTG_Caspase_raw_data',
    'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\data\\Misvik high throughput screening data\\Screen1-4_imaging data']
template_test = 'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\TestDataRecordingForm_harmless_HTS_METADATA.xlsx'

# directories = [
#     'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\data\\Misvik high throughput screening data\\Screens5-8 CTG Casp_raw_data',
#     'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\data\\Misvik high throughput screening data\\Screen5-8_imaging data']
# template_test = 'D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\TestDataRecordingForm_harmless_HTS_METADATA_QD_screens_5_8.xlsx'

# generate_annotation_file(directories, template_test)



# Create object as data container for CTG endpoint
ctg_data = HTS('ctg')
print('.............................. CTG endpoint metadata and raw data ............................................ ')
# print(ctg_data.endpoint)
## Create object for metadata reader
ctg_meta = MetaDataReaderTmp(template_test, ctg_data)
ctg_meta.read_meta_data()
#
# ## recalculate doses
# # ctg_meta.recalculate_dose_from_cell_growth(50, 0.079495092) # args: volume in ul, plate growth area
# ## SBET values are taken from template in sheet Materials and are connected with material name
# # ctg_meta.recalculate_dose_from_sbet(50, 0.079495092)
#
# print(ctg_data.metadata)
# print(ctg_data.water_keys)
## Create object for data reader from template
ctg_data_reader = DataReaderTmp(template_test, directories[0], ctg_data)
ctg_data_reader.read_data()
# print(ctg_data.raw_data_df)
# print('////////////////////////////////////// filtration //////////////////////////////////////////////')
# ctg_data.filtrate_data(ctg_data.raw_data_df, materials=['PL-QD-CF  (no disp)', 'PL-QD-OA (poor disp)'])
# print(ctg_data.metadata)
# print(ctg_data.raw_data_df)
#
## Create object for specific CTG normalization
ctg_normalizer = CellViabilityNormalization(ctg_data)
ctg_normalizer.remove_outliers_by_quantiles()
print(ctg_data.normalized_df)

print('................................ Normalized data after removing blank outliers ................................')
# print(ctg_data.normalized_df)
print('................................ Normalized data after percentage of median control ...........................')
ctg_normalizer.percentage_effect_from_median_control(ctg_data.normalized_df)
print(ctg_data.normalized_df)
print('................................ Normalized data after subtract median of blank controls ......................')
ctg_normalizer.subtract_blank(ctg_data.normalized_df)
print(ctg_data.normalized_df)
ctg_normalizer.calc_mean_median()
print('................................ Mean and Median dataframes....................................................')
# print(ctg_data.mean_df)
# print(ctg_data.median_df)
ctg_dose = DoseResponse(ctg_data)
# ctg_dose.calc_p_values()
# ctg_dose.calc_2_3_sd_of_blanks()
# ctg_dose.calc_auc()
# ctg_dose.first_significant()
# ctg_dose.max_effect()
# ctg_dose.concatenate_parameters()
ctg_dose.dose_response_parameters()
# print('................................ Dose-response parameters .....................................................')
print(ctg_data.dose_response_df)
# print('////////////////////////////////////// filtration //////////////////////////////////////////////')
# ctg_data.filtrate_data(ctg_data.dose_response_df, ['JRCNM04003a', 'NRCWE-055'], ['A549', 'HEPG2'])
# print(ctg_data.dose_response_df)
# #
dapi_data = HTS('dapi')
dapi_meta = MetaDataReaderTmp(template_test, dapi_data)
dapi_meta.read_meta_data()
dapi_data_reader = DataReaderTmp(template_test, directories[1], dapi_data)
dapi_data_reader.read_data()
# print(dapi_data.raw_data_df)
# dapi_data.filtrate_data(dapi_data.raw_data_df, materials=['PL-QD-CF  (no disp)', 'PL-QD-OA (poor disp)'])

dapi_normalizer = DNADamageNormalization(dapi_data)
## Clean imaging data
## method to remove potentially failed  imaging based on DAPI results.
dapi_normalizer.clean_dna_raw()
print('................................ Raw DAPI data after cleaning .................................................')
# print(dapi_data.raw_data_df)
dapi_normalizer.remove_outliers_by_quantiles()
dapi_normalizer.percentage_effect_from_median_control(dapi_data.normalized_df)
dapi_normalizer.calc_mean_median()
dapi_dose = DoseResponse(dapi_data)
dapi_dose.dose_response_parameters()
print(dapi_data.dose_response_df)

casp_data = HTS('casp')
casp_meta = MetaDataReaderTmp(template_test, casp_data)
casp_meta.read_meta_data()
casp_data_reader = DataReaderTmp(template_test, directories[0], casp_data)
casp_data_reader.read_data()
# casp_data.filtrate_data(casp_data.raw_data_df, materials=['PL-QD-CF  (no disp)', 'PL-QD-OA (poor disp)'])
casp_normalizer = CellViabilityNormalization(casp_data)
casp_normalizer.remove_outliers_by_quantiles()
casp_normalizer.percentage_of_median_control(casp_data.normalized_df)
casp_normalizer.subtract_blank_as_percent(casp_data.normalized_df)
print(casp_data.normalized_df)
casp_normalizer.normalize_data_to_cell_count(ctg_data.mean_df, dapi_data.mean_df)
casp_normalizer.calc_mean_median()
casp_dose = DoseResponse(casp_data)
casp_dose.dose_response_parameters()
print(casp_data.dose_response_df)
#
ohg_data = HTS('8ohg')
ohg_meta = MetaDataReaderTmp(template_test, ohg_data)
ohg_meta.read_meta_data()
ohg_data_reader = DataReaderTmp(template_test, directories[1], ohg_data)
ohg_data_reader.read_data()
print(ohg_data.raw_data_df)
# ohg_data.filtrate_data(ohg_data.raw_data_df, materials=['PL-QD-CF  (no disp)', 'PL-QD-OA (poor disp)'])

ohg_normalizer = DNADamageNormalization(ohg_data)
## Clean imaging data
## method to remove potentially failed  imaging based on DAPI results.
ohg_normalizer.clean_dna_raw()
print(ohg_data.raw_data_df)
ohg_normalizer.remove_outliers_by_quantiles()
ohg_normalizer.percentage_of_median_control(ohg_data.normalized_df)
ohg_normalizer.calc_mean_median()
ohg_dose = DoseResponse(ohg_data)
ohg_dose.dose_response_parameters()

#
h2ax_data = HTS('h2ax')
h2ax_meta = MetaDataReaderTmp(template_test, h2ax_data)
h2ax_meta.read_meta_data()
h2ax_data_reader = DataReaderTmp(template_test, directories[1], h2ax_data)
h2ax_data_reader.read_data()
print(h2ax_data.raw_data_df)
# h2ax_data.filtrate_data(h2ax_data.raw_data_df, materials=['PL-QD-CF  (no disp)', 'PL-QD-OA (poor disp)'])

h2ax_normalizer = DNADamageNormalization(h2ax_data)
## Clean imaging data
## method to remove potentially failed  imaging based on DAPI results.
h2ax_normalizer.clean_dna_raw()
print(h2ax_data.raw_data_df)
h2ax_normalizer.remove_outliers_by_quantiles()
h2ax_normalizer.percentage_of_median_control(h2ax_data.normalized_df)
h2ax_normalizer.calc_mean_median()
h2ax_dose = DoseResponse(h2ax_data)
h2ax_dose.dose_response_parameters()
# h2ax_data.dose_response_df.to_csv("D:\\PhD\\projects\\ToxPi\\tox_data\\harmless_screeen1-4_dose_response\\h2ax_dose_response.csv")


df = pd.concat([
    casp_data.dose_response_df,
    ctg_data.dose_response_df,
    dapi_data.dose_response_df,
    ohg_data.dose_response_df,
    h2ax_data.dose_response_df
], axis=1)
df = df.reset_index().rename(columns={'index': 'material'})

## TODO: TOX5 attr df -> list with HTS objects and concat them as previous few rows with concat
## Create TOX5 object with concat dataframes from all endpoints dose-response params., and filter it for choosen cell lines
## This part integrate ToxpiR library
tox5 = TOX5(df, ['A549', 'BEAS-2B', 'THP-1', 'HepG2'])
# tox5.add_weight(3, '1st_3SD')

print('//////////////////////// WEIGHT /////////////////////////////////////')

## available transforming functions are: "log10x_6", "sqrt_x", "yeo_johnson"
user_selected_transform_functions = {
    "1st": "log10x_6",
    "auc": "sqrt_x",
    "max": "log10x_6"
}
## Transform data based on dict "user_selected_transform_functions"
tox5.transform_data(user_selected_transform_functions)
print('................................ Transformed data .............................................................')

## Create slices automatically: by_endpoint, by_time_endpoint, or mannualy
tox5.generate_auto_slices()
tox5.calculate_tox5_scores()
# tox5.calculate_tox5_scores()## default by_time_endpoint
# print('..... TOX5 scores for CTG, CASP and DAPI, for cell lines A549, BEAS-2B and slices by endpoint .................')

print('////////////////////////////////////////// bootstrap confidential intervals by slices   ////////////////////')
dict_ci = tox5.ci_slices()

print('////////////////////////////////////////// bootstrap confidential intervals by scores   ////////////////////')
dict_ci_scores, df = tox5.ci_scores()

_, _ = tox5.ci_scores()

#
#
# tox5.tox5_scores.to_csv('D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\scored_data_original.csv')
# scored_df = pd.read_csv('D:\\PhD\\projects\\ToxPi\\tox_data\\vesa_files\\scored_data_original.csv')
# print(scored_df)

# from TOX5.misc.utils import plot_tox_rank_pie
import matplotlib.pyplot as plt

#
# materials = ['4NQO', 'MMC', 'NANOFIL 9', 'NRCWE-058']
materials = ['4NQO', 'NANOFIL 9', 'NRCWE-058']
# figure, legend = plot_tox_rank_pie(tox5.tox5_scores, materials=materials)
figure, legend = plot_tox_rank_pie(tox5.tox5_scores, materials=materials, colored_param='time',
                                   transparency_bars=0.8, linewidth=0.5, conf_intervals=dict_ci, pies_per_col=3)
# # # figure, legend = plot_tox(tox5.tox5_scores, dict_ci)
# #
# # ## show all materials
# # # # figure, legend = plot_tox_rank_pie(tox5.tox5_scores)
# # #
plt.show()
legend.show()
