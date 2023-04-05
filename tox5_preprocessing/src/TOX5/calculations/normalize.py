from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from tox5_preprocessing.src.TOX5.misc.utils import add_endpoint_parameters


class Normalize:
    def __init__(self, obj):
        self.obj = obj

    def remove_outliers_by_quantiles(self):
        filter_water = (self.obj.df == 'water').any()
        sub_df = self.obj.df.loc[:, filter_water].iloc[:-3].astype(float)

        sub_df['lower Bound'] = sub_df.quantile(0.25, axis=1) - 1.5 * (
                sub_df.quantile(0.75, axis=1) - sub_df.quantile(0.25, axis=1))
        sub_df['upper Bound'] = sub_df.iloc[:, :-1].quantile(0.75, axis=1) + 1.5 * (
                sub_df.iloc[:, :-1].quantile(0.75, axis=1) - sub_df.iloc[:, :-1].quantile(0.25, axis=1))
        for i, j in sub_df.iterrows():
            sub_df.loc[i] = sub_df.loc[i].apply(
                lambda x: x if sub_df.loc[i]['upper Bound'] >= x >= sub_df.loc[i]['lower Bound'] else np.nan)

        sub_df['median control'] = sub_df.iloc[:, :-2].median(axis=1)
        columns = list(sub_df.iloc[:, :-3].keys())
        columns.append('median control')
        self.obj.df = self.obj.df.iloc[0:-3, :]
        self.obj.df[columns] = sub_df[columns]

    @classmethod
    def percent_of_media_control(cls, func):
        def wrapper(df):
            df = df.fillna(value=np.nan)
            new_df = df.iloc[:, 3:].apply(lambda row: func(row), axis=1)
            add_endpoint_parameters(new_df, df['replicate'], df['time'], df['cells'])
            return new_df
        return wrapper

    def calc_blank_sd(self):
        self.obj.normalized_df['median'] = self.obj.normalized_df[self.obj.water_keys].median(axis=1)
        self.obj.normalized_df['std'] = self.obj.normalized_df[self.obj.water_keys].std(axis=1)
        self.obj.normalized_df['median 2sd'] = self.obj.normalized_df['median'] + 2 * self.obj.normalized_df['std']

    def calc_mean_median(self):
        for num, cell in enumerate(self.obj.normalized_df['cells'].unique()):
            for n, time in enumerate(self.obj.normalized_df['time'].unique()):
                new_row = self.obj.normalized_df.groupby(['time', 'cells']).get_group((time, cell))
                median_row = new_row.median()
                avrg = new_row.mean()
                self.obj.median_df = self.obj.median_df.append(pd.Series(median_row,
                                                                         index=list(self.obj.code.keys()),
                                                                         name=f'{cell}_{time}'))
                self.obj.mean_df = self.obj.mean_df.append(pd.Series(avrg,
                                                                     index=list(self.obj.code.keys()),
                                                                     name=f'{cell}_{time}'))

