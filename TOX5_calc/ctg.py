from TOX5_calc.cell_viability import CellViability
import pandas as pd
import numpy as np


class CTG(CellViability):

    ENDPOINT = 'CTG'

    def percent_of_median_control(self):
        self.df = self.df.fillna(value=np.nan)
        new_df = pd.DataFrame()
        for i, j in self.df.iloc[0:, 3:].iterrows():
            j = j.apply(
                lambda x: (1 - (x / j['median control'])) * 100)
            new_df = new_df.append(pd.Series(j))

        new_df.insert(0, "replicate", self.df['replicate'])
        new_df.insert(1, "time", self.df['time'])
        new_df.insert(2, "cells", self.df['cells'])
        self.df = new_df

    def subtract_median_0_h(self):
        self.df = self.df[self.df.time != '0H']
        new_df = []
        for num, v in enumerate(self.df['cells'].unique()):
            tmp = self.df[self.df.cells == v]
            for i, j in tmp.iterrows():
                row_index = 'median_' + v
                tmp.loc[i, 'A1':] = self.df.loc[i, 'A1':] - self.df.loc[row_index, 'A1':]
            new_df.append(tmp)
        new_df = pd.concat(new_df)

        self.read_annotation_data()
        new_df['median'] = new_df[self.water_keys].median(axis=1)
        new_df['std'] = new_df[self.water_keys].std(axis=1)
        new_df['median 2sd'] = new_df['median'] + 2 * new_df['std']
        self.df = new_df

    # def __repr__(self):
    #     return str(self.materials)

