import numpy as np

from tox5_preprocessing.src.TOX5.calculations.basic_normalization import BasicNormalization
from tox5_preprocessing.src.TOX5.calculations.cell_viability_normalization import CellViabilityNormalization


class CTGNormalization(CellViabilityNormalization):

    @staticmethod
    @BasicNormalization.percent_of_media_control
    def median_control(row):
        return (1 - row.div(row['median control'])) * 100

    @staticmethod
    @CellViabilityNormalization.subtract_median_0h
    def subtract_blank(df, i, row_index):
        res_of_median_control = df.loc[i, 'A1':]
        median_0_h = df.loc[row_index, 'A1':]
        result = res_of_median_control.subtract(median_0_h, fill_value=0)
        return result

