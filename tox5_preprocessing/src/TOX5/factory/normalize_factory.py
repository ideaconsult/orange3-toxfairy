from TOX5.calculations.casp_normalization import CaspNormalization
from TOX5.calculations.dapi_normalization import DapiNormalization
from TOX5.calculations.ctg_normalization import CTGNormalization
from TOX5.calculations.ohg_h2ax_normalization import OhgH2axNormalization


def create_normalize_data(flag, *obj):
    normalization_types = {'CTG_normalize': CTGNormalization,
                           'Casp_normalize': CaspNormalization,
                           'Dapi_normalize': DapiNormalization,
                           '8OHG_normalize': OhgH2axNormalization,
                           'H2AX_normalize': OhgH2axNormalization}
    return normalization_types[flag](*obj)
