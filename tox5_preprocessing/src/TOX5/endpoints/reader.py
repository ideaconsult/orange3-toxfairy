import os
import glob
from tox5_preprocessing.src.TOX5.misc.utils import *


class MetaDataReader:
    def __init__(self, annot_data, data_container):
        self.annot_data = annot_data
        self.data_container = data_container

    def read_meta_data(self):
        df_names = pd.read_excel(self.annot_data, sheet_name='Annotation', index_col=0, usecols='B:E')
        materials_to_check = ['water', 'Dispersant', 'another_material']

        for k, v in df_names.iterrows():
            self.data_container.metadata[k] = {'material': v[1], 'concentration': v[2]}
        self.data_container.water_keys = [key for key, value in self.data_container.metadata.items()
                                          if value['material'] in materials_to_check]

    def recalculate_dose_from_cell_growth(self, well_volume, cell_growth_area):
        # Recalculate material dose (ug/ml), based on cell growth area in ug/cm2
        for key, value in self.data_container.metadata.items():
            if "concentration" in value:
                value['concentration'] = value['concentration'] * well_volume / cell_growth_area

    def recalculate_dose_from_sbet(self, well_volume, cell_growth_area):
        # Recalculate material dose (ug/ml), based on SBET in cm2/cm2
        # do reading more generic, sbet in m2/g
        sbet = pd.read_excel(self.annot_data, sheet_name='Annotation', usecols='J,K', na_values=[''])
        sbet.dropna(subset=['material', 'SBET'], inplace=True)
        sbet_dict = sbet.set_index('material')['SBET'].to_dict()

        for key, value in self.data_container.metadata.items():
            if "concentration" in value:
                value['concentration'] = value['concentration'] / (1000 / well_volume)

            material = value['material']
            if material in sbet_dict:
                value['concentration'] = sbet_dict[material] / 100 * value['concentration'] / cell_growth_area

    def recalculate_dose_from_cell_delivered_dose(self):
        # available only for THP-1 and Beas-2B
        df = pd.read_excel(self.annot_data, sheet_name='Annotation', usecols='L:R', na_values=[''], header=None)
        df = df.iloc[:43]
        print(df.head())
        materials = df.iloc[2, 2:].tolist()

        cells = df.iloc[3, 2:].tolist()
        times = df.iloc[1, 1:].tolist()
        print(times)
        result_dict = {}

        # Iterate through the rows starting from the fourth row (data rows)
        for row in df.iloc[2:].itertuples(index=False, name=None):

            material = row[0]
            if material not in result_dict:
                result_dict[material] = {}
            cell = row[1]
            print(cell)
            if cell not in result_dict[material]:
                result_dict[material][cell] = {}

            # for i, time in enumerate(times):
            #     dose = row[i + 2]  # Offset by 2 to match the column index
            #     result_dict[material][cell][time] = dose


class DataReader:
    def __init__(self, raw_data_path, data_container, sheet=None):
        self.raw_data = raw_data_path
        # TODO: remove attr sheet
        self.sheet = sheet

        self.data = data_container

    def read_data_csv(self):
        all_files = glob.glob(os.path.join(self.raw_data, "*.csv"))
        cell = ''
        replicate = ''
        time = ''

        for file_dir in all_files:
            if self.data.endpoint in file_dir.upper():
                filepath, file_name = os.path.split(file_dir)

                parts = file_name.split('_')
                if len(parts) >= 5:
                    (replicate, time, _endpoint, cell, _date) = parts[:5]
                else:
                    print(f"File '{file_name}' does not have enough parts.")

                # (replicate, time, _endpoint, cell, date) = file_name.split('_')
                df = pd.read_csv(file_dir, engine='python', sep='[;,]', header=None, on_bad_lines='skip') \
                    .dropna(subset=[0])
                start_row = df[df.iloc[:, 0] == 'A'].index[0]
                end_row = df[df.iloc[:, 0].str.match(r'^[A-Z](?![A-Z])$')].index[-1]
                df = df.iloc[start_row - 1:end_row, :]

                df = df.set_index(0).T.stack().astype('int')
                df.index = df.index.map('{0[1]}{0[0]}'.format)
                new_values = pd.Series([cell, replicate, time], index=['cells', 'replicates', 'time'])
                df = pd.concat([new_values, df])
                self.data.raw_data_df = self.data.raw_data_df.append(df, ignore_index=True)

        self.data.raw_data_df[['time', 'cells']] = self.data.raw_data_df[['time', 'cells']].apply(
            lambda col: col.str.upper().str.strip())

    def read_data_excel(self):
        self.data.raw_data_df = pd.read_excel(self.raw_data, sheet_name=self.sheet, index_col=1, header=None)
        self.data.raw_data_df.drop(self.data.raw_data_df.columns[[0]], axis=1, inplace=True)
        self.data.raw_data_df = self.data.raw_data_df.T
        self.data.raw_data_df[['time', 'cells', 'Description']] = self.data.raw_data_df[['time', 'cells', 'Description']].apply(
            lambda col: col.str.upper().str.strip())
        self.data.raw_data_df = self.data.raw_data_df.rename_axis(None, axis=1).reset_index(drop=True)

    def read_data_txt(self):
        dfs = []
        all_files = glob.glob(os.path.join(self.raw_data, "*.txt"))

        for file_dir in all_files:
            filepath, file_name = os.path.split(file_dir)
            (replicate, time, cell) = os.path.splitext(file_name)[0].split('_')

            df = pd.read_csv(file_dir, sep='\t', skiprows=1, usecols=[1, 2, 3, 4], header=None)
            df = df.set_index(1).T.astype('int')
            df.insert(0, 'cells', cell)
            df.insert(1, 'replicates', replicate)
            df.insert(2, 'time', time)
            df.insert(3, 'Description', ['DAPI', 'H2AX', '8OHG'])
            dfs.append(df)

        self.data.raw_data_df = pd.concat(dfs, ignore_index=True)
        self.data.raw_data_df = self.data.raw_data_df.rename_axis(None, axis=1)

    def read_data(self, value):
        if os.path.isfile(value) and value.lower().endswith(('.xls', '.xlsx')):
            self.read_data_excel()
        elif os.path.isdir(value):
            for root, _, files in os.walk(value):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    _, file_extension = os.path.splitext(file_path)
                    if file_extension.lower() == '.csv':
                        self.read_data_csv()
                    elif file_extension.lower() == '.txt':
                        self.read_data_txt()
