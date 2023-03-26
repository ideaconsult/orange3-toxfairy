from TOX5_calc.casp import CASP
from TOX5_calc.ctg import CTG
from TOX5_calc.dapi import DAPI
from TOX5_calc.dose_responce_parameters import DoseResponse
# from tox_orange_demo.toxpi_data_prep import *

ctg = CTG('D:/PhD/projects/ToxPi/tox_data/vesa_files/HARMLESS_screens_clean.xlsx',
          'D:/PhD/projects/ToxPi/tox_data/vesa_files/raw_data')

ctg.read_raw_data(CTG.ENDPOINT)
ctg.normalize()
ctg.median_0_h()
ctg.subtract_median_0_h()
ctg.calc_mean_median()

ctg_dose_resp = DoseResponse(ctg)
ctg_dose_resp.calc_p_values_and_sd()
ctg_dose_resp.clean_data_for_auc()
ctg_dose_resp.calc_auc()
ctg_dose_resp.first_significant()
ctg_dose_resp.max_effect()
ctg_dose_resp.concatenate_parameters()
print(ctg_dose_resp.print_dose_response_df())

dapi = DAPI('D:/PhD/projects/ToxPi/tox_data/vesa_files/HARMLESS_screens_clean.xlsx',
            'D:/PhD/projects/ToxPi/tox_data/vesa_files/raw_data')

dapi.read_raw_data(DAPI.ENDPOINT)
dapi.normalize()
dapi.calc_imaging_stat()
dapi.calc_mean_median()

dapi_dose_resp = DoseResponse(dapi)
dapi_dose_resp.calc_p_values_and_sd()
dapi_dose_resp.clean_data_for_auc()
dapi_dose_resp.calc_auc()
dapi_dose_resp.first_significant()
dapi_dose_resp.max_effect()
dapi_dose_resp.concatenate_parameters()
print(dapi_dose_resp.print_dose_response_df())


casp = CASP('D:/PhD/projects/ToxPi/tox_data/vesa_files/HARMLESS_screens_clean.xlsx',
            'D:/PhD/projects/ToxPi/tox_data/vesa_files/raw_data')

casp.read_raw_data(CASP.ENDPOINT)
casp.normalize()
casp.median_0_h()
casp.subtract_median_0_h()
casp.calc_param_casp(ctg.get_mean(), dapi.get_mean())
casp.calc_mean_median()

casp_dose_resp = DoseResponse(casp)
casp_dose_resp.calc_p_values_and_sd()
casp_dose_resp.clean_data_for_auc()
casp_dose_resp.calc_auc()
casp_dose_resp.first_significant()
casp_dose_resp.max_effect()
casp_dose_resp.concatenate_parameters()
print(casp_dose_resp.print_dose_response_df())

# *********************************************************************************************************************

# annot_file = 'D:/PhD/projects/ToxPi/tox_data/vesa_files/HARMLESS_screens_clean.xlsx'
# files_path = 'D:/PhD/projects/ToxPi/tox_data/vesa_files/raw_data'

# df_img = read_imaging_raw(annot_file, 'Imaging raw')
# df_img_clean = clean_imaging_raw(df_img)
# df_img_new = create_imaging_cleaned_df(df_img_clean, 'Dapi', annot_file)
# df_img_outlayers = remove_outlayer(df_img_new)
# df_img_s = percent_of_median_control(df_img_outlayers, 'Dapi')
# df_img_5 = calc_imaging_stat(df_img_s, annot_file)
# df_img_6_median, df_img_6_mean = calc_mean_median(df_img_5, annot_file)





