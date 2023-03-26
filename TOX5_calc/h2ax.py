from TOX5_calc.imaging import Imaging
import pandas as pd
import numpy as np


class H2AX(Imaging):

    ENDPOINT = 'H2AX'

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
