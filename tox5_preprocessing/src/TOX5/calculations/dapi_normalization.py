from tox5_preprocessing.src.TOX5.calculations.basic_normalization import BasicNormalization
from tox5_preprocessing.src.TOX5.calculations.dna_damage_normalization import DNADamageNormalization


class DapiNormalization(DNADamageNormalization):

    @staticmethod
    @BasicNormalization.percent_of_media_control
    def median_control(row):
        return (1 - row.div(row['median control'])) * 100

