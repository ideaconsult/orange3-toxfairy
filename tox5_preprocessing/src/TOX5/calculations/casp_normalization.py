from tox5_preprocessing.src.TOX5.calculations.basic_normalization import BasicNormalization
from tox5_preprocessing.src.TOX5.calculations.cell_viability_normalization import CellViabilityNormalization
import pandas as pd


class CaspNormalization(CellViabilityNormalization):
    def __init__(self, data, data_ctg, data_dapi):
        super().__init__(data)
        self.mean_ctg = data_ctg.mean_df
        self.mean_dapi = data_dapi.mean_df

    @staticmethod
    @CellViabilityNormalization.subtract_median_0h
    def subtract_blank(df, i, row_index):
        return 100 + (df.loc[i, 'A1':] - df.loc[row_index, 'A1':])

    @staticmethod
    @BasicNormalization.percent_of_media_control
    def median_control(row):
        return (row.div(row['median control'])) * 100

    def calc_paramc_casp(self):
        df = pd.concat([self.mean_ctg, self.mean_dapi])
        df_mean = df.groupby(df.index).mean()
        df_mean = df_mean.apply(lambda x: 1 - (x / 100))

        df_casp = pd.concat([self.data.normalized_df, df_mean])
        df_casp.insert(0, 'cell_index', df_casp['cells'] + '_' + df_casp['time'])

        df_ready = []
        for num, v in enumerate(df_casp['cell_index'].unique()):
            if not isinstance(v, str):
                break
            tmp = df_casp[df_casp.cell_index == v]
            row1 = df_casp.loc[v, 'A1':'P24']
            tmp.iloc[:, 4:-4] = tmp.iloc[:, 4:-4].apply(lambda row: row / row1, axis=1)
            df_ready.append(tmp)

        df_ready = pd.concat(df_ready)
        self.data.normalized_df = df_ready.iloc[:, 1:]
