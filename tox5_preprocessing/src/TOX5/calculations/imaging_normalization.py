import numpy as np
import pandas as pd

from TOX5.calculations.normalize import Normalize
from tox5_preprocessing.src.TOX5.misc.utils import *


class ImageNormalization(Normalize):

    @classmethod
    def correct_from_dapi(cls, col):
        if col.iloc[0] == 0:
            col = col.shift(-2)
        return col

    @classmethod
    def correct_all_dapi(cls, col):
        median_dapi = col.median()
        if median_dapi > 50:
            col = col.replace(0, np.nan)
        return col

    def clean_imaging_raw(self):
        new_df = pd.DataFrame()
        self.obj.df.drop(index=self.obj.df.index[-3:], inplace=True)

        for idx1, cell in enumerate(self.obj.df['cells'].unique()):
            for idx2, time in enumerate(self.obj.df['time'].unique()):
                tmp = self.obj.df.groupby(['cells', 'time']).get_group((cell, time))
                dapi_idx = tmp[tmp['Description'] == 'Dapi'].index.values
                for i in dapi_idx:
                    a = tmp.loc[i:i + 2, 'A1':].apply(ImageNormalization.correct_from_dapi)
                    new_df = new_df.append(a)
                tmp2 = tmp.loc[dapi_idx, 'A1':].apply(ImageNormalization.correct_all_dapi)
                new_df.loc[tmp2.index, :] = tmp2[:]

        new_df = new_df.sort_index(ascending=True)
        add_endpoint_parameters(new_df, self.obj.df['replicate'], self.obj.df['time'], self.obj.df['cells'])
        new_df.insert(3, "description", self.obj.df['Description'])

        self.obj.df = new_df
        self.obj.df = self.obj.df[self.obj.df['description'] == self.obj.endpoint]\
            .reset_index(drop=True)\
            .drop(['description'], axis=1)
        self.obj.df = add_annot_data(self.obj.df, self.obj.materials, self.obj.concentration, self.obj.code)
