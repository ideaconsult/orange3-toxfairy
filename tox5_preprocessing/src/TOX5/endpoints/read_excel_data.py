from tox5_preprocessing.src.TOX5.endpoints.endpoint_data import EndpointData
from tox5_preprocessing.src.TOX5.endpoints.save_data import SaveData
from tox5_preprocessing.src.TOX5.misc.utils import *
import pandas as pd
import numpy as np


class EndpointDataExcel(EndpointData, SaveData):
    def __init__(self, endpoint, raw_data, meta_data, sheet=None):
        EndpointData.__init__(self, endpoint, raw_data, meta_data)
        SaveData.__init__(self)
        self.sheet = sheet

    def read_data(self):
        self.df = pd.read_excel(self.meta_data, sheet_name=self.sheet, index_col=1, header=None)
        self.df.drop(self.df.columns[[0]], axis=1, inplace=True)
        self.df = self.df.T
        self.df[['time', 'cells']] = self.df[['time', 'cells']].apply(lambda col: col.str.upper().str.strip())

        self.read_annotation_data()
        self.df = add_annot_data(self.df, self.materials, self.concentration, self.code)
