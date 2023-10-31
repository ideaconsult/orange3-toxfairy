from unittest import TestCase, main
import pandas as pd
from pandas.testing import assert_frame_equal
from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
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


class DataReaderTmpTest(TestCase):
    def setUp(self) -> None:
        template_test = './test_data/TestDataRecordingForm_harmless_HTS_METADATA_tests.xlsx'
        directory_test = ['./test_data/raw_data', './test_data/raw_data_imaging']

        self.ctg_data = HTS('ctg')
        self.ctg_meta = MetaDataReaderTmp(template_test, self.ctg_data)
        self.ctg_meta.read_meta_data()
        self.ctg_data_reader = DataReaderTmp(template_test, directory_test[0], self.ctg_data)
        self.ctg_data_reader.read_data()

    def test_read_data(self):
        # annotate_data(self.ctg_data.raw_data_df, self.ctg_data.metadata)
        expected = pd.read_csv('./test_data/expected_read_csv.csv', index_col=0)
        expected = convert_df_non_numeric_int_to_numeric(expected)
        assert_frame_equal(expected.iloc[:-2, :], self.ctg_data.raw_data_df, check_index_type=False, check_dtype=False)


if __name__ == "__main__":
    main()