import numpy as np
import pandas as pd
from toxfairy.src.toxfairy.calculations.basic_normalization import BasicNormalization
from toxfairy.src.toxfairy.misc.utils import *


class DNADamageNormalization(BasicNormalization):

    @staticmethod
    def correct_from_dapi(df):
        """Corrects values in columns where 'Description' contains 'DAPI'.
            if value for DAPI is zero, that's mean no cells, so no data (NaN) for
            other endpoints,  but keep dapi 0
        Args:
            df (DataFrame): Input DataFrame containing the data, sorts by cells, times and replicates
        Returns:
            None. The input DataFrame is modified in place.
        """
        dapi_idx = df['Description'].str.contains('DAPI')
        if dapi_idx.any():
            for col in df.columns[4:]:
                if (df.loc[dapi_idx, col] == 0).any():
                    df.loc[~dapi_idx, col] = np.nan

    @staticmethod
    def correct_dapi(df):
        """Remove DAPI if imaging has failed, which mean replicates have clearly more cells.
        Corrects 0 DAPI values in columns where median value for 'DAPI' samples is > 50.
        Args:
            df (DataFrame): Input DataFrame containing the data, sorts by cells and times.
        Returns:
            None. The input DataFrame is modified in place.
        """
        zero_cols = (df == 0).any()
        for col in zero_cols[zero_cols].index:
            dapi_median = df.loc[df['Description'].str.contains('DAPI'), col].median()

            if dapi_median > 50:
                df.loc[(df['Description'].str.contains('DAPI')) & (df[col] == 0), col] = np.nan

    def clean_dna_raw(self):
        """Clean DNA raw data.
        Sorts, corrects 'Description' containing 'DAPI', and corrects values based on 'DAPI' median.
        Returns:
            None. The input DataFrame is modified in place.
        """
        new_df = pd.DataFrame()

        for idx1, cell in enumerate(self.data.raw_data_df['cells'].unique()):
            for idx2, time in enumerate(self.data.raw_data_df['time'].unique()):
                tmp = self.data.raw_data_df.groupby(['cells', 'time']).get_group((cell, time))
                for idx3, repl in enumerate(tmp['replicates'].unique()):
                    tmp_replicate = tmp[tmp['replicates'] == repl]
                    DNADamageNormalization.correct_from_dapi(tmp_replicate)
                    new_df = pd.concat([new_df, tmp_replicate])
                DNADamageNormalization.correct_dapi(new_df)
        new_df = new_df.sort_index(ascending=True)
        self.data.raw_data_df = new_df
        self.data.raw_data_df = self.data.raw_data_df[self.data.raw_data_df['Description'] == self.data.endpoint] \
            .reset_index(drop=True).drop(['Description'], axis=1)
