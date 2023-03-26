from abc import abstractmethod

from TOX5_calc.endpoint import Endpoint
import pandas as pd
import os
import glob
import warnings

warnings.filterwarnings('ignore')


class CellViability(Endpoint):
    # def __init__(self, endpoint, annot_data, raw_data_path):
    #     super().__init__(annot_data, raw_data_path)
    #     self.endpoint = endpoint
    #     self.df = pd.DataFrame()

    def read_raw_data(self, endpoint):
        all_files = glob.glob(os.path.join(self.raw_data_path, "*.csv"))

        replicates = []
        times = []
        cells = []

        for filename in all_files:
            if endpoint in filename:
                names = filename[len(self.raw_data_path) + 1:-13]  # TODO: use os lib, georgi recommend
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

        self.df.insert(loc=0, column='replicate', value=replicates)
        self.df.insert(loc=1, column='time', value=times)
        self.df.insert(loc=2, column='cells', value=cells)
        self.df[['time', 'cells']] = self.df[['time', 'cells']].apply(lambda col: col.str.upper().str.strip())

        self.read_annotation_data()
        self.df = self.df.append(pd.Series(self.materials, index=self.df.columns, name='material'))\
            .append(pd.Series(self.concentration, index=self.df.columns, name='concentration'))\
            .append(pd.Series(self.code, index=self.df.columns, name='code'))

    def median_0_h(self):
        for i, j in enumerate(self.df['cells'].unique()):
            median = self.df.groupby(['time', 'cells']).get_group(('0H', j)).median()
            self.df = self.df.append(pd.Series(median, index=self.df.columns, name=f"median_{j}"))

    @property
    @abstractmethod
    def subtract_median_0_h(self):
        pass

    def normalize(self):
        self.remove_outliers()
        self.percent_of_median_control()

    @property
    @abstractmethod
    def percent_of_median_control(self):
        pass
