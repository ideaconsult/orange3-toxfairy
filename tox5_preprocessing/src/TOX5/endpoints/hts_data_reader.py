import os
import glob
from tox5_preprocessing.src.TOX5.misc.utils import *


class HTSDataReader:
    def __init__(self, raw_data_path, raw_data_file, data, sheet=None):
        self.raw_data = raw_data_path
        self.raw_data_ = raw_data_file
        self.sheet = sheet

        self.data = data
        self.data.meta_data.read_meta_data()

    def read_data_csv(self):
        all_files = glob.glob(os.path.join(self.raw_data, "*.csv"))
        replicates = []
        times = []
        cells = []

        for file_dir in all_files:
            if self.data.endpoint in file_dir:
                filepath, file_name = os.path.split(file_dir)
                (replicate, time, _endpoint, cell, date) = file_name.split('_')
                replicates.append(replicate)
                times.append(time)
                cells.append(cell)
                df = pd.read_csv(file_dir, engine='python',  sep='[;,]', header=None, on_bad_lines='skip')\
                    .dropna(subset=[0])
                start_row = df[df.iloc[:, 0] == 'A'].index[0]
                end_row = df[df.iloc[:, 0].str.match(r'^[A-Z](?![A-Z])$')].index[-1]
                df = df.iloc[start_row - 1:end_row, :]

                df = df.set_index(0).T.stack().astype('int')
                df.index = df.index.map('{0[1]}{0[0]}'.format)
                self.data.raw_data_df = self.data.raw_data_df.append(df, ignore_index=True)

        # add_endpoint_parameters(self.data.raw_data_df, replicates, times, cells)
        insert_columns(self.data.raw_data_df, ['replicates', 'time', 'cells'],  replicates, times, cells)
        self.data.raw_data_df[['time', 'cells']] = self.data.raw_data_df[['time', 'cells']].apply(lambda col: col.str.upper().str.strip())
        self.data.raw_data_df = add_annot_data(self.data.raw_data_df,
                                               self.data.meta_data.materials,
                                               self.data.meta_data.concentration,
                                               self.data.meta_data.code)

    def read_data_excel(self):
        self.data.raw_data_df = pd.read_excel(self.raw_data_, sheet_name=self.sheet, index_col=1, header=None)
        self.data.raw_data_df.drop(self.data.raw_data_df.columns[[0]], axis=1, inplace=True)
        self.data.raw_data_df = self.data.raw_data_df.T
        self.data.raw_data_df[['time', 'cells']] = self.data.raw_data_df[['time', 'cells']].apply(lambda col: col.str.upper().str.strip())
        self.data.raw_data_df = self.data.raw_data_df.rename_axis(None, axis=1).reset_index(drop=True)
        self.data.raw_data_df = add_annot_data(self.data.raw_data_df,
                                               self.data.meta_data.materials,
                                               self.data.meta_data.concentration,
                                               self.data.meta_data.code)

    def read_data_txt(self):
        dfs = []
        all_files = glob.glob(os.path.join(self.raw_data, "*.txt"))
        replicates = []
        times = []
        cells = []
        endpoints = []

        for file_dir in all_files:
            filepath, file_name = os.path.split(file_dir)
            (replicate, time, cell, endpoint) = os.path.splitext(file_name)[0].split('_')
            replicates.append(replicate)
            times.append(time)
            cells.append(cell)
            endpoints.append(endpoint)
            df = pd.read_csv(file_dir, sep='\t', skiprows=1, usecols=[1, 2], header=None)
            df = df.set_index(1).T.astype('int')
            dfs.append(df)

        self.data.raw_data_df = pd.concat(dfs, ignore_index=True)
        self.data.raw_data_df = self.data.raw_data_df.reset_index(drop=True)
        self.data.raw_data_df.index = self.data.raw_data_df.index + 2
        insert_columns(self.data.raw_data_df, ['cells', 'replicates', 'time', 'descriptions'], cells, replicates, times,
                       endpoints)
        self.data.raw_data_df = add_annot_data(self.data.raw_data_df,
                                               self.data.meta_data.materials,
                                               self.data.meta_data.concentration,
                                               self.data.meta_data.code)
