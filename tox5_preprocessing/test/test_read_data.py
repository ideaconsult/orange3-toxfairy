from unittest import TestCase, main
import pandas as pd
from pandas.testing import assert_frame_equal
from TOX5.endpoints.hts_data import HTSData
from TOX5.endpoints.hts_data_reader import HTSDataReader


def convert_df_non_numeric_int_to_numeric(df):
    df = df.apply(pd.to_numeric, errors='coerce').fillna(df)
    dropped_rows = df[df.isnull().any(axis=1)]
    df_dropped_na = df.dropna(subset=['replicates'])
    current_index = df_dropped_na.index
    new_index = pd.to_numeric(current_index, errors='coerce')
    df_with_numeric_index = df_dropped_na
    df_with_numeric_index.index = new_index
    df = pd.concat([df_with_numeric_index, dropped_rows])
    return df


class HTSDataReaderTest(TestCase):
    def setUp(self) -> None:
        self.ctg_data = HTSData('CTG', './test_data/annotation.xlsx')
        self.ctg_reader = HTSDataReader('./test_data/raw_data', './test_data/annotation.xlsx',
                                        self.ctg_data)
        self.dapi_data = HTSData('DAPI', './test_data/annotation.xlsx')
        self.dapi_reader = HTSDataReader('./test_data/raw_data', './test_data/HARMLESS_for_tests.xlsx',
                                         self.dapi_data, 'Imaging raw')

    def assert_dicts_almost_equal(self, dict1, dict2, places=5):
        self.assertEqual(set(dict1.keys()), set(dict2.keys()))

        for key in dict1:
            self.assertIn(key, dict2)
            value1 = dict1[key]
            value2 = dict2[key]
            if isinstance(value1, (float, int)) and isinstance(value2, (float, int)):
                self.assertAlmostEqual(value1, value2, places=places)
            else:
                self.assertEqual(value1, value2)

    def test_meta_data(self):
        self.ctg_reader.read_data_csv()
        code = {'A1': 20, 'A2': 'water', 'B1': 20, 'B2': 'water', 'C1': 20, 'C2': 'water',
                'D1': 20, 'D2': 'water', 'E1': 20, 'E2': 'water', 'F1': 20, 'F2': 'water',
                'G1': 20, 'G2': 'water', 'H1': 20, 'H2': 'water'}
        materials = {'A1': 'Nanofil9 (Nanoclay)', 'A2': 'Dispersant', 'B1': 'Nanofil9 (Nanoclay)', 'B2': 'Dispersant',
                     'C1': 'Nanofil9 (Nanoclay)', 'C2': 'Dispersant', 'D1': 'Nanofil9 (Nanoclay)', 'D2': 'Dispersant',
                     'E1': 'Nanofil9 (Nanoclay)', 'E2': 'Dispersant', 'F1': 'Nanofil9 (Nanoclay)', 'F2': 'Dispersant',
                     'G1': 'Nanofil9 (Nanoclay)', 'G2': 'Dispersant', 'H1': 'Nanofil9 (Nanoclay)', 'H2': 'Dispersant'}
        concentration = {'A1': 0.1170553, 'A2': 0, 'B1': 0.3511660, 'B2': 0,
                         'C1': 1.0534979, 'C2': 0, 'D1': 3.1604938, 'D2': 0,
                         'E1': 9.4814815, 'E2': 0, 'F1': 28.4444444, 'F2': 0,
                         'G1': 85.3333333, 'G2': 0, 'H1': 256, 'H2': 0}
        water_keys = ['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2']

        self.assertDictEqual(self.ctg_data.meta_data.code, code)
        self.assertDictEqual(self.ctg_data.meta_data.materials, materials)
        self.assert_dicts_almost_equal(self.ctg_data.meta_data.concentration, concentration)
        self.assertEqual(self.ctg_data.meta_data.water_keys, water_keys)

    def test_csv_reader(self):
        self.ctg_reader.read_data_csv()
        expected = pd.read_csv('./test_data/expected_read_csv.csv', index_col=0)
        expected = convert_df_non_numeric_int_to_numeric(expected)
        assert_frame_equal(expected,self.ctg_data.raw_data_df, check_index_type=False, check_dtype=False)

    def test_excel_reader(self):
        self.dapi_reader.read_data_excel()
        expected = pd.read_csv('./test_data/expected_read_excel.csv', index_col=0)
        expected = convert_df_non_numeric_int_to_numeric(expected)
        assert_frame_equal(expected, self.dapi_data.raw_data_df, check_index_type=False, check_dtype=False)

    def test_txt_reader(self):
        pass


if __name__ == "__main__":
    main()
