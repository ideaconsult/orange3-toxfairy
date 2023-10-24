import pandas as pd
import numpy as np


class BasicNormalization:
    def __init__(self, data):
        self.data = data

    def remove_outliers_by_quantiles(self):
        self.data.normalized_df = self.data.raw_data_df.copy()
        sub_df = self.data.normalized_df[self.data.water_keys].astype(float)
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
        self.data.normalized_df[columns] = sub_df[columns]

    @staticmethod
    def percent_of_media_control(func):
        def wrapper(df):
            df.fillna(value=np.nan, inplace=True)
            df.iloc[:, 3:] = df.iloc[:, 3:].apply(lambda row: func(row), axis=1)
            df.drop('median control', axis=1, inplace=True)
        return wrapper

    def calc_blank_sd(self):
        self.data.normalized_df['median'] = self.data.normalized_df[self.data.water_keys].median(axis=1)
        self.data.normalized_df['std'] = self.data.normalized_df[self.data.water_keys].std(axis=1)
        self.data.normalized_df['median 2sd'] = self.data.normalized_df['median'] + 2 * self.data.normalized_df['std']

    def calc_mean_median(self):
        median_tmp = []
        mean_tmp = []
        for num, cell in enumerate(self.data.normalized_df['cells'].unique()):
            for n, time in enumerate(self.data.normalized_df['time'].unique()):
                new_row = self.data.normalized_df.groupby(['time', 'cells']).get_group((time, cell))
                numeric_cols = new_row.iloc[:, 3:]

                median_row = numeric_cols.median()
                median_tmp.append(pd.Series(median_row,
                                            index=list(self.data.metadata.keys()),
                                            name=f'{cell}_{time}'))
                mean_row = numeric_cols.mean()
                mean_tmp.append(pd.Series(mean_row,
                                          index=list(self.data.metadata.keys()),
                                          name=f'{cell}_{time}'))

        self.data.median_df = pd.concat(median_tmp, axis=1).T
        self.data.mean_df = pd.concat(mean_tmp, axis=1).T
