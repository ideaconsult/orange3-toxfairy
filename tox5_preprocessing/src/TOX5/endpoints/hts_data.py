import pandas as pd


class MetaData:
    def __init__(self, annot_data):
        self.annot_data = annot_data

        self.water_keys = []
        self.code = {}
        self.materials = {}
        self.concentration = {}

    def read_meta_data(self):
        df_names = pd.read_excel(self.annot_data, sheet_name='Annotation', index_col=0, usecols='B:E')

        for k, v in df_names.iterrows():
            self.code[k] = v[0]
            self.materials[k] = v[1]
            self.concentration[k] = v[2]
        self.water_keys = [k for k, v in self.code.items() if v == 'water']


class HTSData:
    def __init__(self, endpoint, annot_data_file):
        self.meta_data = MetaData(annot_data_file)
        self.endpoint = endpoint
        self.raw_data_df = pd.DataFrame()
        self.normalized_df = pd.DataFrame()
        self.mean_df = pd.DataFrame()
        self.median_df = pd.DataFrame()
        self.dose_response_df = pd.DataFrame()



