from tox5_preprocessing.src.TOX5.calculations.normalize import Normalize
from TOX5.calculations.cell_viability_normalization import CellViabilityNormalization
import pandas as pd


class CaspNormalization(CellViabilityNormalization):
    def __init__(self, obj, obj_ctg, obj_dapi):
        super().__init__(obj)
        self.mean_ctg = obj_ctg.mean_df
        self.mean_dapi = obj_dapi.mean_df

    @staticmethod
    @CellViabilityNormalization.subtract_median_0h
    def subtract_blank(df, i, row_index):
        return 100 + (df.loc[i, 'A1':] - df.loc[row_index, 'A1':])

    @staticmethod
    @Normalize.percent_of_media_control
    def median_control(row):
        return (row.div(row['median control'])) * 100

    def calc_paramc_casp(self):
        df = pd.concat([self.mean_ctg, self.mean_dapi])
        df_mean = df.groupby(df.index).mean()
        df_mean = df_mean.apply(lambda x: 1 - (x / 100))

        df_casp = pd.concat([self.obj.normalized_df, df_mean])
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
        self.obj.normalized_df = df_ready.iloc[:, 1:]

    def normalize_data(self):
        self.remove_outliers_by_quantiles()
        percent_of_media = self.median_control(self.obj.df)
        self.obj.normalized_df = self.subtract_blank(percent_of_media)
        self.calc_blank_sd()
        self.calc_paramc_casp()
        self.calc_mean_median()