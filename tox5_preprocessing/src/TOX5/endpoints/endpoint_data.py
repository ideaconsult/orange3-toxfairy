from abc import ABC, abstractmethod
import pandas as pd
from tox5_preprocessing.src.TOX5.misc.validator import Validator


class EndpointData(ABC):

    def __init__(self, endpoint, raw_data, meta_data):
        self.endpoint = endpoint
        self.raw_data = raw_data
        self.meta_data = meta_data

        self.water_keys = []
        self.code = {}
        self.materials = {}
        self.concentration = {}

    @property
    def endpoint(self):
        return self.__endpoint

    @endpoint.setter
    def endpoint(self, value):
        Validator.raise_error_for_empty_str(value, "Can't be empty string or white space")
        Validator.raise_error_for_uncorrect_endpoint(value, "This endpoint don't exist, use one of following: "
                                                            "'CTG', 'Casp', 'Dapi', 'H2AH', '8OHG'")
        self.__endpoint = value

    def read_annotation_data(self):
        df_names = pd.read_excel(self.meta_data, sheet_name='Annotation', index_col=0, usecols='B:E')

        for k, v in df_names.iterrows():
            self.code[k] = v[0]
            self.materials[k] = v[1]
            self.concentration[k] = v[2]
        self.water_keys = [k for k, v in self.code.items() if v == 'water']

    @abstractmethod
    def read_data(self):
        pass
