from unittest import TestCase, main
import pandas as pd
from pandas.testing import assert_frame_equal
from TOX5.endpoints.hts_data import HTSData
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.hts_data_reader import HTSDataReader
from TOX5.endpoints.reader import DataReader, MetaDataReader
from TOX5.misc.utils import annotate_data


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
        self.ctg_data = HTS('CTG')
        self.ctg_reader = DataReader('./test_data/raw_data', self.ctg_data)
        # self.ctg_reader.read_data_csv()
        self.ctg_meta_data = MetaDataReader('./test_data/annotation.xlsx', self.ctg_data)
        # self.ctg_meta_data.read_meta_data()

        self.dapi_data = HTS('Dapi')
        self.dapi_reader = DataReader('./test_data/raw_data',
                                      self.dapi_data, 'Imaging raw')
        self.dapi_meta_data = MetaDataReader('./test_data/annotation.xlsx', self.dapi_data)

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

    def test_meta_data(self):
        self.ctg_reader.read_data_csv()
        expected_metadata = {'A1': {'material': 'Nanofil9 (Nanoclay)', 'concentration': 0.1170553},
                             'B1': {'material': 'Nanofil9 (Nanoclay)', 'concentration': 0.3511660},
                             'C1': {'material': 'Nanofil9 (Nanoclay)', 'concentration': 1.0534979},
                             'D1': {'material': 'Nanofil9 (Nanoclay)', 'concentration': 3.1604938},
                             'E1': {'material': 'Nanofil9 (Nanoclay)', 'concentration': 9.4814815},
                             'F1': {'material': 'Nanofil9 (Nanoclay)', 'concentration': 28.4444444},
                             'G1': {'material': 'Nanofil9 (Nanoclay)', 'concentration': 85.3333333},
                             'H1': {'material': 'Nanofil9 (Nanoclay)', 'concentration': 256},
                             'A2': {'material': 'Dispersant', 'concentration': 0.0},
                             'B2': {'material': 'Dispersant', 'concentration': 0.0},
                             'C2': {'material': 'Dispersant', 'concentration': 0.0},
                             'D2': {'material': 'Dispersant', 'concentration': 0.0},
                             'E2': {'material': 'Dispersant', 'concentration': 0.0},
                             'F2': {'material': 'Dispersant', 'concentration': 0.0},
                             'G2': {'material': 'Dispersant', 'concentration': 0.0},
                             'H2': {'material': 'Dispersant', 'concentration': 0.0}
                             }
        expected_water_keys = ['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2']
        self.ctg_meta_data.read_meta_data()
        self.assert_dicts_almost_equal(self.ctg_data.metadata, expected_metadata)

        self.assertEqual(self.ctg_data.water_keys, expected_water_keys)

    def test_csv_reader(self):
        self.ctg_reader.read_data_csv()
        self.ctg_meta_data.read_meta_data()
        annotate_data(self.ctg_data.raw_data_df, self.ctg_data.metadata)
        expected = pd.read_csv('./test_data/expected_read_csv.csv', index_col=0)
        expected = convert_df_non_numeric_int_to_numeric(expected)
        assert_frame_equal(expected.iloc[:-1], self.ctg_data.raw_data_df, check_index_type=False, check_dtype=False)

    def test_excel_reader(self):
        self.dapi_reader.read_data_excel()
        self.dapi_meta_data.read_meta_data()
        annotate_data(self.dapi_data.raw_data_df, self.dapi_data.metadata)
        expected = pd.read_csv('./test_data/expected_read_excel.csv', index_col=0)

        expected = convert_df_non_numeric_int_to_numeric(expected)
        assert_frame_equal(expected.iloc[:-1], self.dapi_data.raw_data_df, check_index_type=False, check_dtype=False)

    def test_txt_reader(self):
        pass


if __name__ == "__main__":
    main()
