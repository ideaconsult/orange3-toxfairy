from unittest import TestCase, main, TextTestRunner
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from TOX5.calculations.casp_normalization import CaspNormalization
from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.calculations.dapi_normalization import DapiNormalization
from TOX5.calculations.ohg_h2ax_normalization import OHGH2AXNormalization
from TOX5.endpoints.hts_data import HTSData
from TOX5.endpoints.hts_data_reader import HTSDataReader


class MainNormalizationsTest(TestCase):
    def setUp(self) -> None:
        self.ctg_data = HTSData('CTG', './test_data/annotation.xlsx')
        self.ctg_reader = HTSDataReader('./test_data/raw_data', './test_data/annotation.xlsx',
                                        self.ctg_data)
        self.ctg_reader.read_data_csv()
        self.ctg_normalize = CTGNormalization(self.ctg_data)

    def test_remove_outliers_by_quantiles(self):
        self.ctg_normalize.remove_outliers_by_quantiles()
        expected = pd.read_csv('./test_data/expected_outliers_removed.csv')
        assert_frame_equal(expected, self.ctg_data.normalized_df, check_index_type=False, check_dtype=False)

    def test_median_control(self):
        self.ctg_normalize.remove_outliers_by_quantiles()

        self.ctg_normalize.median_control(self.ctg_data.normalized_df)
        expected = pd.read_csv('./test_data/expected_median_control.csv')
        assert_frame_equal(expected, self.ctg_data.normalized_df, check_index_type=False, check_dtype=False)

    def test_subtract_blank(self):
        self.ctg_normalize.remove_outliers_by_quantiles()
        self.ctg_normalize.median_control(self.ctg_data.normalized_df)

        self.ctg_normalize.subtract_blank(self.ctg_data.normalized_df)
        expected = pd.read_csv('./test_data/expected_subtract_blank.csv')
        assert_frame_equal(expected, self.ctg_data.normalized_df.reset_index(drop=True), check_index_type=False,
                           check_dtype=False)

    def test_calc_blank_sd(self):
        self.ctg_normalize.remove_outliers_by_quantiles()
        self.ctg_normalize.median_control(self.ctg_data.normalized_df)
        self.ctg_normalize.subtract_blank(self.ctg_data.normalized_df)

        self.ctg_normalize.calc_blank_sd()
        expected = pd.read_csv('./test_data/expected_calc_blank_sd.csv')
        assert_frame_equal(expected, self.ctg_data.normalized_df.reset_index(drop=True), check_index_type=False,
                           check_dtype=False)

    def test_calc_mean_median(self):
        self.ctg_normalize.remove_outliers_by_quantiles()
        self.ctg_normalize.median_control(self.ctg_data.normalized_df)
        self.ctg_normalize.subtract_blank(self.ctg_data.normalized_df)

        self.ctg_normalize.calc_mean_median()
        expected_mean = pd.read_csv('./test_data/expected_mean.csv', index_col=0)
        assert_frame_equal(expected_mean, self.ctg_data.mean_df, check_index_type=False, check_dtype=False)
        expected_median = pd.read_csv('./test_data/expected_median.csv', index_col=0)
        assert_frame_equal(expected_median, self.ctg_data.median_df, check_index_type=False, check_dtype=False)

    def test_median_control_for_ctg_and_dapi(self):
        # (1-(result/median control))*100
        test_data = {
            'replicates': ['S1', 'S2', 'S3'],
            'time': ['0H', '6H', '24H'],
            'cells': ['C1', 'C1', 'C1'],
            'A': [10, 20, 30],
            'B': [5, 10, 15],
            'median control': [10, 10, 10]
        }
        df_ctg = pd.DataFrame(test_data)
        result_df_ctg = CTGNormalization(df_ctg)
        result_df_ctg.median_control(df_ctg)

        expected_data = {
            'replicates': ['S1', 'S2', 'S3'],
            'time': ['0H', '6H', '24H'],
            'cells': ['C1', 'C1', 'C1'],
            'A': [0, -100, -200],
            'B': [50, 0, -50]
        }

        df_dapi = pd.DataFrame(test_data)
        result_df_dapi = DapiNormalization(df_dapi)
        result_df_dapi.median_control(df_dapi)
        expected_df = pd.DataFrame(expected_data)
        assert_frame_equal(df_ctg, expected_df, check_dtype=False)
        assert_frame_equal(df_dapi, expected_df, check_dtype=False)

    def test_median_control_for_casp_ohg_h2ax(self):
        # (result/median control)*100
        test_data = {
            'replicates': ['S1', 'S2', 'S3'],
            'time': ['0H', '6H', '24H'],
            'cells': ['C1', 'C1', 'C1'],
            'A': [10, 20, 30],
            'B': [5, 10, 15],
            'median control': [10, 10, 10]
        }
        df_casp = pd.DataFrame(test_data)
        df_ohg_h2ax = pd.DataFrame(test_data)

        expected_data = {
            'replicates': ['S1', 'S2', 'S3'],
            'time': ['0H', '6H', '24H'],
            'cells': ['C1', 'C1', 'C1'],
            'A': [100, 200, 300],
            'B': [50, 100, 150]
        }

        result_df_casp = CaspNormalization(df_casp)
        result_df_casp.median_control(df_casp)

        result_df_ohg_h2ax = OHGH2AXNormalization(df_ohg_h2ax)
        result_df_ohg_h2ax.median_control(df_ohg_h2ax)

        expected_df = pd.DataFrame(expected_data)
        assert_frame_equal(df_casp, expected_df, check_dtype=False)
        assert_frame_equal(df_ohg_h2ax, expected_df, check_dtype=False)


class AddedNormalizationsTest(TestCase):
    def setUp(self) -> None:
        self.ctg_data = HTSData('CTG', './test_data/annotation.xlsx')
        self.ctg_reader = HTSDataReader('./test_data/raw_data', './test_data/annotation.xlsx',
                                        self.ctg_data)
        self.ctg_reader.read_data_csv()
        self.ctg_normalize = CTGNormalization(self.ctg_data)

        self.dapi_data = HTSData('Dapi', './test_data/annotation.xlsx')
        self.dapi_reader = HTSDataReader('./test_data/raw_data',
                                         './test_data/HARMLESS_for_tests.xlsx',
                                         self.dapi_data, 'Imaging raw')
        self.dapi_normalization = DapiNormalization(self.dapi_data)

    def test_clean_dna_raw(self):
        test = {'cells': ['A549', 'A549', 'A549', 'A549', 'A549', 'A549', 'A549', 'A549', 'A549', 'A549', 'A549', 'A549'],
                'replicate': ['S1', 'S1', 'S1', 'S2', 'S2', 'S2', 'S3', 'S3', 'S3', 'S4', 'S4', 'S4'],
                'time': ['6H', '6H', '6H', '6H', '6H', '6H', '6H', '6H', '6H', '6H', '6H', '6H'],
                'Description': ['Dapi', 'H2AX', '8OHG',  'Dapi', 'H2AX', '8OHG', 'Dapi', 'H2AX', '8OHG', 'Dapi', 'H2AX', '8OHG'],
                'A1': [0, 200, 100, 300, 200, 100, 300, 111, 100, 0, 200, 100],
                'B1': [0, 200, 100, 15, 200, 100, 10, 200, 100, 0, 200, 100]}

        self.dapi_data.raw_data_df = pd.DataFrame(test)
        for _ in range(3):
            self.dapi_data.raw_data_df.loc[len(self.dapi_data.raw_data_df)] = [None, None, None, None, None, None]

        self.dapi_normalization.clean_dna_raw()

        ohg_data = HTSData('8OHG', './test_data/HARMLESS_for_tests.xlsx')
        ohg_normalization = OHGH2AXNormalization(ohg_data)
        ohg_data.raw_data_df = pd.DataFrame(test)
        for _ in range(3):
            ohg_data.raw_data_df.loc[len(ohg_data.raw_data_df)] = [None, None, None, None, None, None]
        ohg_normalization.clean_dna_raw()

        self.assertTrue(np.isnan(self.dapi_data.raw_data_df.loc[0, 'A1']))
        self.assertTrue(np.isnan(self.dapi_data.raw_data_df.loc[3, 'A1']))
        self.assertTrue((self.dapi_data.raw_data_df.loc[0, 'B1']) == 0)
        self.assertTrue((self.dapi_data.raw_data_df.loc[3, 'B1']) == 0)

        self.assertTrue((ohg_data.raw_data_df.loc[0, 'A1']) is None)
        self.assertTrue((ohg_data.raw_data_df.loc[3, 'A1']) is None)
        self.assertTrue((ohg_data.raw_data_df.loc[0, 'B1']) is None)
        self.assertTrue((ohg_data.raw_data_df.loc[3, 'B1']) is None)

    def test_casp_additional_normalization(self):
        casp_data = HTSData('CASP',  './test_data/annotation.xlsx')
        casp_data.normalized_df = pd.read_csv('./test_data/casp_normalized_df.csv')
        dapi_mean_df = pd.read_csv('./test_data/mean_dapi.csv', index_col=0)
        ctd_mean_df = pd.read_csv('./test_data/expected_mean.csv', index_col=0)
        casp_normalization = CaspNormalization(casp_data, ctd_mean_df, dapi_mean_df)
        casp_normalization.additional_normalization()

        expected = pd.read_csv('./test_data/expected_casp_add_norm.csv')
        assert_frame_equal(expected, casp_data.normalized_df, check_index_type=False, check_dtype=False)


if __name__ == "__main__":
    main()
