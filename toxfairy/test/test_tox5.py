from unittest import TestCase, main
import pandas as pd
import numpy as np
from sklearn.preprocessing import PowerTransformer
from pandas.testing import assert_frame_equal, assert_series_equal
from TOX5.calculations.tox5 import TOX5


class Tox5Test(TestCase):
    def setUp(self) -> None:
        self.df = {'material': ['M1', 'M2', 'M3'],
                   'CELL1_24H_AUC_E1': [10, 20, 50],
                   'CELL1_24H_1st_2SD_E1': [10, 20, 50],
                   'CELL1_24H_1st_3SD_E1': [10, 10, 10],
                   'CELL1_24H_MAX_E1': [10, 20, 50]
                   }
        self.tox_df = pd.DataFrame(self.df)
        self.tox5 = TOX5(self.tox_df, ['CELL1'])

    def test_transforming(self):
        user_selected_transform_functions = {
            "1st": "log10x_6",
            "auc": "sqrt_x",
            "max": "yeo_johnson"
        }

        self.tox5.transform_data(user_selected_transform_functions)
        # sort by index because in toxpir datafarme is sorted by toxpi score
        self.tox5.transformed_data = self.tox5.transformed_data.sort_index()

        log_original = self.tox5.transformed_data['CELL1_24H_1st_2SD_E1']
        sqrt_original = self.tox5.transformed_data['CELL1_24H_AUC_E1']
        yeo_johnson_original = self.tox5.transformed_data['CELL1_24H_MAX_E1']

        # test sqrt
        sqrt_transform_expected = (np.sqrt(self.tox_df['CELL1_24H_AUC_E1']) - np.sqrt(min(self.tox_df['CELL1_24H_AUC_E1']))) / \
            (np.sqrt(max(self.tox_df['CELL1_24H_AUC_E1'])) - np.sqrt(min(self.tox_df['CELL1_24H_AUC_E1'])))
        assert_series_equal(sqrt_original, sqrt_transform_expected, check_index=False)

        # test log10x+6
        log_transform = -np.log10(self.tox_df['CELL1_24H_1st_2SD_E1']) + 6
        min_transformed = log_transform.min()
        max_transformed = log_transform.max()
        log_transform_expected = (log_transform - min_transformed) / (max_transformed - min_transformed)
        assert_series_equal(log_original, log_transform_expected, check_index=False)

        # test yeo_johnson
        pt = PowerTransformer(method='yeo-johnson')
        pt_data = self.tox_df['CELL1_24H_MAX_E1'].values.reshape(-1, 1)
        yj_transform = pt.fit_transform(pt_data)
        data_scaled = (yj_transform - (yj_transform.min())) / (yj_transform.max() - (yj_transform.min()))
        yeo_transform_expected = pd.Series(data_scaled.flatten(), name='CELL1_24H_MAX_E1')
        assert_series_equal(yeo_johnson_original, yeo_transform_expected, check_index=False)

    def test_generate_auto_slices(self):
        pass


if __name__ == "__main__":
    main()
