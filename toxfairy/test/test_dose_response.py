from unittest import TestCase, main
import pandas as pd
from pandas.testing import assert_frame_equal
from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.endpoints.hts_data_container import HTS
from TOX5.calculations.dose_response import DoseResponse
from TOX5.endpoints.reader import DataReader, MetaDataReader
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp


class DoseResponseTest(TestCase):

    def setUp(self) -> None:
        template_test = './test_data/TestDataRecordingForm_harmless_HTS_METADATA_tests.xlsx'
        directory_test = ['./test_data/raw_data', './test_data/raw_data_imaging']

        self.ctg_data = HTS('ctg')
        self.ctg_meta = MetaDataReaderTmp(template_test, self.ctg_data)
        self.ctg_meta.read_meta_data()
        self.ctg_data_reader = DataReaderTmp(template_test, directory_test[0], self.ctg_data)
        self.ctg_data_reader.read_data()
        self.ctg_normalize = CTGNormalization(self.ctg_data)
        self.ctg_dose_response = DoseResponse(self.ctg_data)

    def assert_dicts_almost_equal(self, dict1, dict2, places=7):
        self.assertEqual(set(dict1.keys()), set(dict2.keys()))

        for key in dict1:
            self.assertIn(key, dict2)
            value1 = dict1[key]
            value2 = dict2[key]
            if isinstance(value1, dict) and isinstance(value2, dict):
                self.assert_dicts_almost_equal(value1, value2, places=places)
            elif isinstance(value1, (float, int, complex)) and isinstance(value2, (float, int, complex)):
                self.assertAlmostEqual(value1, value2, places=places)
            else:
                self.assertEqual(value1, value2)

    def test_calc_p_values_and_sd(self):
        normalized = {
            'replicates': ['S1', 'S1', 'S2', 'S2'],
            'time': ['6H', '6H', '24H', '24H'],
            'cells': ['A549', 'A549', 'BEAS-2B', 'BEAS-2B'],
            'A1': [22.155, -6.903, 4.266, 0.182],
            'A2': [-2.543, -11.027, -0.519, 4.110],
            'B2': [7.668, 8.409, 11.454, 5.932]
        }
        self.ctg_data.normalized_df = pd.DataFrame(normalized)
        self.ctg_data.water_keys = ['A2', 'B2']
        dose_response = DoseResponse(self.ctg_data)
        dose_response.calc_p_values()
        expected_p_value_dict = {'A549_6H': {'A1': 0.568, 'A2': 0.373, 'B2': 0.345},
                                 'BEAS-2B_24H': {'A1': 0.484, 'A2': 0.435, 'B2': 0.446}}
        self.assert_dicts_almost_equal(expected_p_value_dict, dose_response.p_value_dict, 3)

        dose_response.calc_2_3_sd_of_blanks()
        expected_sd_dict = {'A549_6H': {'sd2': 21.038, 'sd3': 30.276},
                            'BEAS-2B_24H': {'sd2': 14.922, 'sd3': 19.873}}
        self.assert_dicts_almost_equal(expected_sd_dict, dose_response.sd_dict, 2)

    def test_auc_calculation(self):
        normalized = {
            'replicates': ['S1', 'S1'],
            'time': ['6H', '6H'],
            'cells': ['BEAS-2B', 'BEAS-2B'],
            'A1': [-2.1339, 16.4096],
            'B1': [-0.2855, 12.3860],
            'C1': [10.6548, 13.1618],
            'D1': [15.4558, 6.4151],
            'E1': [30.4205, 41.8357],
            'F1': [75.0069, 74.6985],
            'G1': [62.0135, 64.8124],
            'H1': [41.2396, 42.9896]
        }
        self.ctg_data.normalized_df = pd.DataFrame(normalized)

        median_df = {'A1': [7.1378],
                     'B1': [6.0502],
                     'C1': [11.9083],
                     'D1': [10.9355],
                     'E1': [36.1281],
                     'F1': [74.8527],
                     'G1': [63.4130],
                     'H1': [42.1149]
                     }
        self.ctg_data.median_df = pd.DataFrame(median_df)
        self.ctg_data.median_df.rename(index={0: 'BEAS-2B_6H'}, inplace=True)
        self.ctg_data.metadata = {'A1': {'material': 'NANOFIL 9', 'concentration': 0.1170553},
                                  'B1': {'material': 'NANOFIL 9', 'concentration': 0.3511660},
                                  'C1': {'material': 'NANOFIL 9', 'concentration': 1.0534979},
                                  'D1': {'material': 'NANOFIL 9', 'concentration': 3.1604938},
                                  'E1': {'material': 'NANOFIL 9', 'concentration': 9.4814815},
                                  'F1': {'material': 'NANOFIL 9', 'concentration': 28.4444444},
                                  'G1': {'material': 'NANOFIL 9', 'concentration': 85.3333333},
                                  'H1': {'material': 'NANOFIL 9', 'concentration': 256}}

        dose_response = DoseResponse(self.ctg_data)
        dose_response.sd_dict = {'BEAS-2B_6H': {'sd2': 21.18876, 'sd3': 30.74008}}
        dose_response.clean_data_for_auc()
        dose_response.calc_auc()
        expected_auc = pd.DataFrame({'BEAS-2B_6H_AUC': [93.25385]}, index=['NANOFIL 9'])
        assert_frame_equal(expected_auc, dose_response.auc, check_index_type=False, check_dtype=False)

    def test_fsc_calculation(self):
        median_df = {'A1': [7.1378],
                     'B1': [6.0502],
                     'C1': [11.9083],
                     'D1': [10.9355],
                     'E1': [36.1281],
                     'F1': [74.8527],
                     'G1': [63.4130],
                     'H1': [42.1149]
                     }
        self.ctg_data.median_df = pd.DataFrame(median_df)
        self.ctg_data.median_df.rename(index={0: 'BEAS-2B_6H'}, inplace=True)
        dose_response = DoseResponse(self.ctg_data)

        dose_response.p_value_dict = {'BEAS-2B_6H': {'A1': 0.549882794, 'B1': 0.639482502, 'C1': 0.200774229,
                                                     'D1': 0.25596591, 'E1': 0.000232718, 'F1': 1.56452E-08,
                                                     'G1': 1.70415E-07, 'H1': 3.36427E-05}}
        dose_response.sd_dict = {'BEAS-2B_6H': {'sd2': 21.18876, 'sd3': 30.74008}}
        dose_response.first_significant()
        expected_fsc_2sd = pd.DataFrame({'BEAS-2B_6H_1st_2SD': [9.481481]}, index=['NANOFIL 9'])
        expected_fsc_2sd.index.name = 'material'
        expected_fsc_3sd = pd.DataFrame({'BEAS-2B_6H_1st_3SD': [9.481481]}, index=['NANOFIL 9'])
        expected_fsc_3sd.index.name = 'material'

        assert_frame_equal(expected_fsc_2sd, dose_response.fsc_2sd, check_index_type=False, check_dtype=False)
        assert_frame_equal(expected_fsc_3sd, dose_response.fsc_3sd, check_index_type=False, check_dtype=False)

    def test_dose_response_parameters(self):
        self.ctg_normalize.remove_outliers_by_quantiles()
        self.ctg_normalize.median_control(self.ctg_data.normalized_df)
        self.ctg_normalize.subtract_blank(self.ctg_data.normalized_df)
        self.ctg_normalize.calc_mean_median()
        self.ctg_dose_response.dose_response_parameters()

        expected = pd.read_csv('./test_data/expected_dose_response.csv', index_col=0)
        assert_frame_equal(expected, self.ctg_data.dose_response_df, check_index_type=False,
                           check_dtype=False, check_like=True)


if __name__ == "__main__":
    main()
