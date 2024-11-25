import pandas as pd
import numpy as np
from .basic_normalization import BasicNormalization


class CellViabilityNormalization(BasicNormalization):
    @staticmethod
    def subtract_median_0h(func):
        def wrapper(df):
            for i, j in enumerate(df['cells'].unique()):
                tmp = df.groupby(['time', 'cells']).get_group(('0H', j))
                median = tmp.iloc[:, 3:].median()
                df.loc[f"median_{j}"] = median
            for num, v in enumerate(df['cells'].unique()):
                tmp = df[df.cells == v]
                for i, j in tmp.iterrows():
                    row_index = 'median_' + v
                    tmp.loc[i, df.columns[3]:] = func(df, i, row_index)
                df[df.cells == v] = tmp
            df.drop(df[df.time == '0H'].index, inplace=True)
            df.drop(df.filter(regex='^median_', axis=0).index, inplace=True)
            df.reset_index(drop=True, inplace=True)

        return wrapper

    @staticmethod
    @subtract_median_0h
    def subtract_blank_as_percent(df, i, row_index):
        res_of_median_control = df.loc[i, df.columns[3]:]
        median_0_h = df.loc[row_index, df.columns[3]:]
        result = 100 + (res_of_median_control.subtract(median_0_h, fill_value=np.nan))

        return result

    @staticmethod
    @subtract_median_0h
    def subtract_blank(df, i, row_index):
        res_of_median_control = df.loc[i, df.columns[3]:]
        median_0_h = df.loc[row_index, df.columns[3]:]
        result = res_of_median_control.subtract(median_0_h, fill_value=np.nan)
        return result

    def normalize_data_to_cell_count(self, *mean_dfs):
        """
            ..............

            Parameters:
            -

            Returns:
            -
            """

        if not mean_dfs:
            raise ValueError('To do additional normalization, at least one mean dataframe is required')

        for df in mean_dfs:
            if not isinstance(df, pd.DataFrame):
                raise TypeError('All provided arguments should be pandas DataFrames')
            if df.empty:
                raise ValueError('One or more of the provided data frames are empty')

            # Combine the provided dataframes by calculating the mean across them
        combined_mean_df = pd.concat(mean_dfs).groupby(level=0).mean()

        df_mean = combined_mean_df.apply(lambda x: 1 - (x / 100))


        df_casp = pd.concat([self.data.normalized_df, df_mean])
        df_casp.insert(0, 'cell_index', df_casp['cells'] + '_' + df_casp['time'])

        df_ready = []
        for num, v in enumerate(df_casp['cell_index'].unique()):
            if not isinstance(v, str):
                break
            tmp = df_casp[df_casp.cell_index == v]
            row1 = df_casp.loc[v, df_casp.columns[4]:]
            tmp.iloc[:, 4:] = tmp.iloc[:, 4:].apply(lambda row: row / row1, axis=1)
            df_ready.append(tmp)

        df_ready = pd.concat(df_ready)
        df_ready.reset_index(drop=True, inplace=True)
        self.data.normalized_df = df_ready.iloc[:, 1:]
