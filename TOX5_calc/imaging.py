from abc import abstractmethod

from TOX5_calc.endpoint import Endpoint
import pandas as pd
import numpy as np
import os
import glob
import warnings
warnings.filterwarnings('ignore')


class Imaging(Endpoint):

    SHEET = 'Imaging raw'

    @staticmethod
    def correct_from_dapi(col):
        if col.iloc[0] == 0:
            col = col.shift(-2)
        return col

    @staticmethod
    def correct_all_dapi(col):
        median_dapi = col.median()
        if median_dapi > 50:
            col = col.replace(0, np.nan)
        return col

    def read_raw_data(self, endpoint):
        df = pd.read_excel(self.annot_data, sheet_name=Imaging.SHEET, index_col=1, header=None)
        df.drop(df.columns[[0]], axis=1, inplace=True)
        df = df.T
        df[['time', 'cell']] = df[['time', 'cell']].apply(lambda col: col.str.upper().str.strip())

        # TODO: separate function for clean df imaging
        for idx1, cell in enumerate(df['cell'].unique()):
            for idx2, time in enumerate(df['time'].unique()):
                tmp = df.groupby(['cell', 'time']).get_group((cell, time))
                dapi_idx = tmp[tmp['Description'] == 'Dapi'].index.values
                for i in dapi_idx:
                    a = tmp.loc[i:i + 2, 'A1':].apply(Imaging.correct_from_dapi)
                    self.df = self.df.append(a)
                tmp2 = tmp.loc[dapi_idx, 'A1':].apply(Imaging.correct_all_dapi)
                self.df.loc[tmp2.index, :] = tmp2[:]

        self.df = self.df.sort_index(ascending=True)
        self.df.insert(0, "replicate", df['rep'])
        self.df.insert(1, "time", df['time'])
        self.df.insert(2, "cells", df['cell'])
        self.df.insert(3, "description", df['Description'])

        self.df = self.df[self.df['description'] == endpoint].reset_index(drop=True).drop(['description'], axis=1)

        self.read_annotation_data()
        self.df = self.df.append(pd.Series(self.materials, index=self.df.columns, name='material')) \
            .append(pd.Series(self.concentration, index=self.df.columns, name='concentration')) \
            .append(pd.Series(self.code, index=self.df.columns, name='code'))

    @property
    @abstractmethod
    def percent_of_median_control(self):
        pass

    def normalize(self):
        self.remove_outliers()
        self.percent_of_median_control()

    def calc_imaging_stat(self):
        self.read_annotation_data()
        self.df['median'] = self.df[self.water_keys].median(axis=1)
        self.df['std'] = self.df[self.water_keys].std(axis=1)
        self.df['median 2sd'] = self.df['median'] + 2 * self.df['std']



