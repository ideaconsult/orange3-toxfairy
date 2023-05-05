from tox5_preprocessing.src.TOX5.calculations.basic_normalization import BasicNormalization
from tox5_preprocessing.src.TOX5.calculations.dna_damage_normalization import DNADamageNormalization


class OHGH2AXNormalization(DNADamageNormalization):

    @staticmethod
    @BasicNormalization.percent_of_media_control
    def median_control(row):
        return (row.div(row['median control'])) * 100

