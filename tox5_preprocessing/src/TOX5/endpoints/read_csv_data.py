from tox5_preprocessing.src.TOX5.misc.utils import *
from tox5_preprocessing.src.TOX5.endpoints.endpoint_data import EndpointData
from tox5_preprocessing.src.TOX5.endpoints.save_data import SaveData
import pandas as pd
import os
import glob
import warnings
warnings.filterwarnings('ignore')


class EndpointDataCSV(EndpointData, SaveData):
    def __init__(self, endpoint, raw_data, meta_data, sheet=None):
        EndpointData.__init__(self, endpoint, raw_data, meta_data)
        SaveData.__init__(self)
        self.sheet = sheet

    def read_data(self):
        all_files = glob.glob(os.path.join(self.raw_data, "*.csv"))
        replicates = []
        times = []
        cells = []

        for filename in all_files:
            if self.endpoint in filename:
                names = filename[len(self.raw_data) + 1:-13]  # TODO: use os lib, georgi recommend
                (replicate, time, _endpoint, cell) = names.split('_')
                replicates.append(replicate)
                times.append(time)
                cells.append(cell)
                df_test = pd.read_csv(filename, engine='python', sep='[;,]',
                                      skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
                                                37, 38])
                df_out = df_test.set_index('Unnamed: 0').T.stack()
                df_out.index = df_out.index.map('{0[1]}{0[0]}'.format)
                self.df = self.df.append(df_out, ignore_index=True)

        add_endpoint_parameters(self.df, replicates, times, cells)
        self.df[['time', 'cells']] = self.df[['time', 'cells']].apply(lambda col: col.str.upper().str.strip())
        self.read_annotation_data()
        self.df = add_annot_data(self.df, self.materials, self.concentration, self.code)
