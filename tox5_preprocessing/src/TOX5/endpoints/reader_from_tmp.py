import os
import re
import pandas as pd
from tox5_preprocessing.src.TOX5.misc.utils import *


class MetaDataReaderTmp:
    def __init__(self, template, data_container):
        self.template = template
        self.data_container = data_container

    def read_meta_data(self):
        df_names = pd.read_excel(self.template, sheet_name='Front sheet', skiprows=4, index_col=0,
                                 usecols=lambda col: not col.startswith('Unnamed'))
        materials_to_check = ['water', 'Dispersant', 'dispersant', 'another_material']

        sbet = pd.read_excel(self.template, sheet_name='Materials', usecols=['ERM identifiers', 'BET surface in m²/g'])
        sbet.set_index('ERM identifiers', inplace=True)

        for k, v in df_names.iterrows():
            self.data_container.metadata[k] = {'material': v.iloc[0], 'concentration': v.iloc[2]}
            if v.iloc[0] in sbet.index:
                self.data_container.metadata[k]['SBET'] = pd.to_numeric(sbet.loc[v.iloc[0], 'BET surface in m²/g'])

        self.data_container.water_keys = [key for key, value in self.data_container.metadata.items()
                                          if value['material'] in materials_to_check]

    def recalculate_dose_from_cell_growth(self, well_volume, cell_growth_area):
        # Recalculate material dose (ug/ml), based on cell growth area in ug/cm2
        for key, value in self.data_container.metadata.items():
            if "concentration" in value:
                value['concentration'] = value['concentration'] * well_volume / cell_growth_area

    def recalculate_dose_from_sbet(self, well_volume, cell_growth_area):
        # Recalculate material dose (ug/ml), based on SBET in cm2/cm2
        for key, value in self.data_container.metadata.items():
            if "concentration" in value and 'SBET' in value:
                value['concentration'] = value['SBET'] / 100 * (
                            value['concentration'] / (1000 / well_volume)) / cell_growth_area


class DataReaderTmp:
    def __init__(self, template, directory, data_container):
        self.template = template
        self.directory = directory
        self.data = data_container

    @staticmethod
    def _read_data_csv(file):
        df = pd.read_csv(file, engine='python', sep='[;,]', header=None, on_bad_lines='skip').dropna(subset=[0])
        start_row = df[df.iloc[:, 0] == 'A'].index[0]
        end_row = df[df.iloc[:, 0].str.match(r'^[A-Z](?![A-Z])$')].index[-1]
        df = df.iloc[start_row - 1:end_row, :]

        df = df.set_index(0).T.stack().astype('int')
        df.index = df.index.map('{0[1]}{0[0]}'.format)
        return df

    @staticmethod
    def _read_data_txt(file):
        df = pd.read_csv(file, sep='\t', skiprows=1, usecols=[1, 2, 3, 4], header=None)
        df = df.set_index(1).T.astype('int')
        return df

    @staticmethod
    def _check_endpoint_existence(text, word):
        pattern = r'\b{}\b'.format(re.escape(word))
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    def _process_file(self, row):
        df_result = pd.DataFrame()
        filename = row['filename']
        full_file_path = os.path.join(self.directory, filename)
        file_extension = os.path.splitext(full_file_path)[1]

        if os.path.exists(full_file_path):
            if file_extension.lower() == '.csv':
                df_tmp = self._read_data_csv(full_file_path)
                new_values = pd.Series([row['Cell'], row['Replicate'], row['Time']],
                                       index=['cells', 'replicates', 'time'])
                df_concat = pd.concat([new_values, df_tmp])
                df_result = pd.DataFrame(df_concat).T

            elif file_extension.lower() == '.txt':
                df_tmp = self._read_data_txt(full_file_path)
                df_tmp.insert(0, 'cells', row['Cell'])
                df_tmp.insert(1, 'replicates', row['Replicate'])
                df_tmp.insert(2, 'time', row['Time'])
                endpoints = re.split(r'[,.]\s+', row['Endpoint'].upper())
                df_tmp.insert(3, 'Description', endpoints)
                df_tmp = df_tmp.rename_axis(None, axis=1)
                df_result = df_tmp
        else:
            raise FileNotFoundError(f"File '{full_file_path}' does not exist.")
        return df_result

    def read_data(self):
        df = pd.read_excel(self.template, sheet_name='Files')
        filtered_df = df[df['Endpoint'].apply(lambda x: self._check_endpoint_existence(x, self.data.endpoint))]

        tmp_results = []
        for index, row in filtered_df.iterrows():
            tmp_result = self._process_file(row)
            tmp_results.append(tmp_result)

        self.data.raw_data_df = pd.concat(tmp_results, ignore_index=True)
        self.data.raw_data_df[['time', 'cells', 'replicates']] = self.data.raw_data_df[['time', 'cells', 'replicates']]\
            .apply(lambda col: col.str.upper().str.strip())
