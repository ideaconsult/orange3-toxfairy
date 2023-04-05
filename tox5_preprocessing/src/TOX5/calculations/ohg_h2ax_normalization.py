from TOX5.calculations.imaging_normalization import ImageNormalization
from TOX5.calculations.normalize import Normalize


class OhgH2axNormalization(ImageNormalization):

    @staticmethod
    @Normalize.percent_of_media_control
    def median_control(row):
        return (row.div(row['median control'])) * 100

    def normalize_data(self):
        self.clean_imaging_raw()
        self.remove_outliers_by_quantiles()
        self.obj.normalized_df = self.median_control(self.obj.df)
        self.calc_blank_sd()
        self.calc_mean_median()
