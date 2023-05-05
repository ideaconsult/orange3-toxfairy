import pandas as pd
from tox5_preprocessing.src.TOX5.calculations.basic_normalization import BasicNormalization


class CellViabilityNormalization(BasicNormalization):
    @staticmethod
    def subtract_median_0h(func):
        def wrapper(df):
            for i, j in enumerate(df['cells'].unique()):
                median = df.groupby(['time', 'cells']).get_group(('0H', j)).median()
                df.loc[f"median_{j}"] = median
            for num, v in enumerate(df['cells'].unique()):
                tmp = df[df.cells == v]
                for i, j in tmp.iterrows():
                    row_index = 'median_' + v
                    tmp.loc[i, 'A1':] = func(df, i, row_index)
                df[df.cells == v] = tmp
            df.drop(df[df.time == '0H'].index, inplace=True)
            df.drop(df.filter(regex='^median_', axis=0).index, inplace=True)
        return wrapper
