import numpy as np
import pandas as pd
from tox5_preprocessing.src.TOX5.calculations.basic_normalization import BasicNormalization
from tox5_preprocessing.src.TOX5.misc.utils import *


class DNADamageNormalization(BasicNormalization):

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

    def clean_dna_raw(self):
        new_df = pd.DataFrame()

        for idx1, cell in enumerate(self.data.raw_data_df['cells'].unique()):
            for idx2, time in enumerate(self.data.raw_data_df['time'].unique()):
                tmp = self.data.raw_data_df.groupby(['cells', 'time']).get_group((cell, time))
                dapi_idx = tmp[tmp['Description'] == 'DAPI'].index.values
                for i in dapi_idx:
                    a = tmp.loc[i:i + 2, tmp.columns[4]:].apply(DNADamageNormalization.correct_from_dapi)
                    new_df = pd.concat([new_df, a])
                tmp2 = tmp.loc[dapi_idx, tmp.columns[4]:].apply(DNADamageNormalization.correct_all_dapi)
                new_df.loc[tmp2.index, :] = tmp2[:]
        new_df = new_df.sort_index(ascending=True)
        add_endpoint_parameters(new_df, self.data.raw_data_df['replicates'],
                                self.data.raw_data_df['time'],
                                self.data.raw_data_df['cells'])
        new_df.insert(3, "description", self.data.raw_data_df['Description'])

        self.data.raw_data_df = new_df
        self.data.raw_data_df = self.data.raw_data_df[self.data.raw_data_df['description'] == self.data.endpoint] \
            .reset_index(drop=True).drop(['description'], axis=1)

