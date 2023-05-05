from unittest import TestCase, main
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from TOX5.endpoints.hts_data import HTSData
from TOX5.endpoints.hts_data_reader import HTSDataReader


class HTSDataReaderTest(TestCase):
    def setUp(self) -> None:
        self.ctg_data = HTSData('endpoint', './test_data/annotation.xlsx')
        self.ctg_reader = HTSDataReader('./test_data', './test_data/annotation.xlsx', self.ctg_data)

    def test_csv_reader(self):
        expected = {
                        'replicate': ['R1', 'R2', np.NAN, np.NAN, np.NAN],
                        'time': ['1H', '1H', np.NAN, np.NAN, np.NAN],
                        'cells': ['C1', 'C1', np.NAN, np.NAN, np.NAN],
                        'A1': [100, 100, 'Dispersant', 0.0, 'water'],
                        'B1': [110, 200, 'NM1', 10.0, 1],
                        'A2': [200, 110, 'NM2', 20.0, 2],
                        'B2': [210, 210, 'Dispersant', 0.0, 'water']
                    }
        expected_df = pd.DataFrame(data=expected, index=[0, 1, 'material', 'concentration', 'code'])
        self.ctg_reader.read_data_csv()
        assert_frame_equal(expected_df, self.ctg_data.raw_data_df)

    def test_excel_reader(self):
        pass


if __name__ == "__main__":
    main()
