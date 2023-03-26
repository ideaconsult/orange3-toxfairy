from TOX5_calc.cell_viability import CellViability
import pandas as pd
import numpy as np


class CASP(CellViability):

    ENDPOINT = 'Casp'

    def subtract_median_0_h(self):
        self.df = self.df[self.df.time != '0H']
        new_df = []
        for num, v in enumerate(self.df['cells'].unique()):
            tmp = self.df[self.df.cells == v]
            for i, j in tmp.iterrows():
                row_index = 'median_' + v
                tmp.loc[i, 'A1':] = 100 + (self.df.loc[i, 'A1':] - self.df.loc[row_index, 'A1':])
            new_df.append(tmp)
        new_df = pd.concat(new_df)

        self.read_annotation_data()
        new_df['median'] = new_df[self.water_keys].median(axis=1)
        new_df['std'] = new_df[self.water_keys].std(axis=1)
        new_df['median 2sd'] = new_df['median'] + 2 * new_df['std']
        self.df = new_df

    def percent_of_median_control(self):
        self.df = self.df.fillna(value=np.nan)
        new_df = pd.DataFrame()

        for i, j in self.df.iloc[0:, 3:].iterrows():
            j = j.apply(
                lambda x: (x / j['median control']) * 100)
            new_df = new_df.append(pd.Series(j))

        new_df.insert(0, "replicate", self.df['replicate'])
        new_df.insert(1, "time", self.df['time'])
        new_df.insert(2, "cells", self.df['cells'])
        self.df = new_df

    def calc_param_casp(self, mean_CTG, mean_DAPI):
        df = pd.concat([mean_CTG, mean_DAPI])
        df_mean = df.groupby(df.index).mean()
        df_mean = df_mean.apply(lambda x: 1 - (x / 100))

        df_casp = pd.concat([self.df, df_mean])
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

        self.df = df_ready.iloc[:, 1:]

    # def get_dataframe(self):
    #     return self.median_df, self.mean_df, self.df

