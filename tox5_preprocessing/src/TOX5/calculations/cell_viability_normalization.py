import pandas as pd
from TOX5.calculations.normalize import Normalize


class CellViabilityNormalization(Normalize):
    @classmethod
    def subtract_median_0h(cls, func):
        def wrapper(df):
            for i, j in enumerate(df['cells'].unique()):
                median = df.groupby(['time', 'cells']).get_group(('0H', j)).median()
                df = df.append(pd.Series(median, index=df.columns, name=f"median_{j}"))
            df = df[df.time != '0H']
            new_df = []
            for num, v in enumerate(df['cells'].unique()):
                tmp = df[df.cells == v]
                for i, j in tmp.iterrows():
                    row_index = 'median_' + v
                    tmp.loc[i, 'A1':] = func(df, i, row_index)
                new_df.append(tmp)
            new_df = pd.concat(new_df)
            return new_df
        return wrapper

