from tox5_preprocessing.src.TOX5.calculations.basic_normalization import BasicNormalization
from tox5_preprocessing.src.TOX5.calculations.cell_viability_normalization import CellViabilityNormalization
import pandas as pd


class CaspNormalization(CellViabilityNormalization):
    def __init__(self, data, ctg_mean_df=None, dapi_mean_df=None):
        super().__init__(data)
        self.ctg_mean_df = ctg_mean_df
        self.dapi_mean_df = dapi_mean_df

    @staticmethod
    @CellViabilityNormalization.subtract_median_0h
    def subtract_blank(df, i, row_index):
        res_of_median_control = df.loc[i, 'A1':]
        median_0_h = df.loc[row_index, 'A1':]
        result = 100 + (res_of_median_control.subtract(median_0_h, fill_value=0))

        return result

    @staticmethod
    @BasicNormalization.percent_of_media_control
    def median_control(row):
        return (row.div(row['median control'])) * 100

    def additional_normalization(self):
        if self.ctg_mean_df is None and self.dapi_mean_df is None:
            raise ValueError('To do additional normalization of CASP, CTG and DAPI mean dataframes are required')
        if not isinstance(self.ctg_mean_df, pd.DataFrame) and not isinstance(self.dapi_mean_df, pd.DataFrame):
            raise TypeError('Attributes should be a pandas DataFrame')

        df = pd.concat([self.ctg_mean_df, self.dapi_mean_df])
        df_mean = df.groupby(df.index).mean()
        df_mean = df_mean.apply(lambda x: 1 - (x / 100))

        df_casp = pd.concat([self.data.normalized_df, df_mean])
        df_casp.insert(0, 'cell_index', df_casp['cells'] + '_' + df_casp['time'])

        df_ready = []
        for num, v in enumerate(df_casp['cell_index'].unique()):
            if not isinstance(v, str):
                break
            tmp = df_casp[df_casp.cell_index == v]
            row1 = df_casp.loc[v, 'A1':]
            tmp.iloc[:, 4:] = tmp.iloc[:, 4:].apply(lambda row: row / row1, axis=1)
            df_ready.append(tmp)

        df_ready = pd.concat(df_ready)
        df_ready.reset_index(drop=True, inplace=True)
        self.data.normalized_df = df_ready.iloc[:, 1:]
