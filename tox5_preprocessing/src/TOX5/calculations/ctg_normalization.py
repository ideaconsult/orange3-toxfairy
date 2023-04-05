from TOX5.calculations.cell_viability_normalization import CellViabilityNormalization
from TOX5.calculations.normalize import Normalize


class CTGNormalization(CellViabilityNormalization):

    @staticmethod
    @CellViabilityNormalization.subtract_median_0h
    def subtract_blank(df, i, row_index):
        return df.loc[i, 'A1':] - df.loc[row_index, 'A1':]

    @staticmethod
    @Normalize.percent_of_media_control
    def median_control(row):
        return (1 - row.div(row['median control'])) * 100

    def normalize_data(self):
        self.remove_outliers_by_quantiles()
        percent_of_media = self.median_control(self.obj.df)
        self.obj.normalized_df = self.subtract_blank(percent_of_media)
        self.calc_blank_sd()
        self.calc_mean_median()

