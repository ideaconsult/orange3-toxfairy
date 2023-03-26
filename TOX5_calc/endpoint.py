from abc import ABC, abstractmethod
import pandas as pd
import numpy as np


class Endpoint(ABC):
    def __init__(self, annot_data, raw_data_path):
        self.annot_data = annot_data
        self.raw_data_path = raw_data_path

        self.water_keys = []
        self.code = {}
        self.materials = {}
        self.concentration = {}

        self.df = pd.DataFrame()
        self.mean_df = pd.DataFrame()
        self.median_df = pd.DataFrame()

    def read_annotation_data(self):
        df_names = pd.read_excel(self.annot_data, sheet_name='Annotation', index_col=0, usecols='B:E')

        for k, v in df_names.iterrows():
            self.code[k] = v[0]
            self.materials[k] = v[1]
            self.concentration[k] = v[2]

        self.water_keys = [k for k, v in self.code.items() if v == 'water']

    @abstractmethod
    def read_raw_data(self, endpoint):
        pass

    def remove_outliers(self):
        blank_filter = (self.df == 'water').any()
        sub_df = self.df.loc[:, blank_filter].iloc[:-3].astype(float)

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
        self.df = self.df.iloc[0:-3, :]
        self.df[columns] = sub_df[columns]

    def calc_mean_median(self):
        self.read_annotation_data()

        for num, cell in enumerate(self.df['cells'].unique()):
            for n, time in enumerate(self.df['time'].unique()):
                new_row = self.df.groupby(['time', 'cells']).get_group((time, cell))
                median_row = new_row.median()
                avg = new_row.mean()
                self.median_df = self.median_df.append(pd.Series(median_row, index=list(self.code.keys()), name=f'{cell}_{time}'))
                self.mean_df = self.mean_df.append(pd.Series(avg, index=list(self.code.keys()), name=f'{cell}_{time}'))

    def get_median(self):
        return self.median_df

    def get_mean(self):
        return self.mean_df

    def get_normalized(self):
        return self.df









