from scipy import stats
import pandas as pd
import numpy as np
from sklearn import metrics
from statistics import median
from tox5_preprocessing.src.TOX5.misc.utils import *


class DoseResponse:
    def __init__(self, data):
        self.data = data

        self.sd_dict = {}
        self.p_value_dict = {}
        self.data_for_auc = []

        self.auc = pd.DataFrame()
        self.fsc_2sd = pd.DataFrame()
        self.fsc_3sd = pd.DataFrame()
        self.max = pd.DataFrame()

    def calc_p_values(self):
        for num, cell in enumerate(self.data.normalized_df['cells'].unique()):
            for n, time in enumerate(self.data.normalized_df['time'].unique()):
                try:
                    new_row = self.data.normalized_df.groupby(['time', 'cells']).get_group((time, cell))
                except KeyError:
                    print(f'The group  between {time} and {cell}  does not exist')
                    continue
                new_water_subdf = new_row[self.data.meta_data.water_keys].values.tolist()
                y = np.concatenate(new_water_subdf)
                y = y[~np.isnan(y)]
                key_dict = f'{cell}_{time}'
                for col_name, col_data in new_row.iloc[:, 3:].iteritems():
                    p = stats.ttest_ind(col_data.values, y).pvalue.round(60)
                    pv = p if pd.isna(p) is not True else 0
                    if key_dict not in self.p_value_dict:
                        self.p_value_dict[key_dict] = {col_name: pv}
                    else:
                        self.p_value_dict[key_dict][col_name] = pv

    def calc_2_3_sd_of_blanks(self):
        for num, cell in enumerate(self.data.normalized_df['cells'].unique()):
            for n, time in enumerate(self.data.normalized_df['time'].unique()):
                try:
                    new_row = self.data.normalized_df.groupby(['time', 'cells']).get_group((time, cell))
                except KeyError:
                    print(f'The group  between {time} and {cell}  does not exist')
                    continue

                new_water_subdf = new_row[self.data.meta_data.water_keys].values.tolist()
                y = np.concatenate(new_water_subdf)
                # y = y[~np.isnan(y)]
                stdev = np.std(y, ddof=1)
                median_m = np.median(y)

                key_dict = f'{cell}_{time}'
                self.sd_dict[key_dict] = {'sd2': median_m + 2 * stdev, 'sd3': median_m + 3 * stdev}

    def clean_data_for_auc(self):
        self.data_for_auc = []
        for _, cell in enumerate(self.data.normalized_df['cells'].unique()):
            for _, time in enumerate(self.data.normalized_df['time'].unique()):
                new_row = self.data.normalized_df.groupby(['time', 'cells']).get_group((time, cell))

                for rowIdx, row in new_row.iloc[:, 3:].iterrows():
                    for colIdx, value in row.items():
                        key = f'{cell}_{time}'
                        new_row[colIdx] = np.where(self.data.median_df.loc[key, colIdx] < self.sd_dict[key]['sd2'],
                                                   0, new_row[colIdx])
                self.data_for_auc.append(new_row)

        self.data_for_auc = pd.concat(self.data_for_auc)
        self.data_for_auc.iloc[0:, 3:] = self.data_for_auc.iloc[0:, 3:].fillna(0)

    def calc_auc(self):
        self.clean_data_for_auc()

        material_set = list(set(self.data.meta_data.materials.values()))

        dict_auc = {}
        for num, cell in enumerate(self.data_for_auc['cells'].unique()):
            for n, time in enumerate(self.data_for_auc['time'].unique()):
                key = f'{cell}_{time}'
                new_df2 = self.data_for_auc.groupby(['time', 'cells']).get_group((time, cell))

                new_df2 = add_annot_data(new_df2,
                                         self.data.meta_data.materials,
                                         self.data.meta_data.concentration,
                                         self.data.meta_data.code)
                new_df2.loc['code', 'A1':] = new_df2.loc['code', 'A1':].apply(str)

                for i in material_set:
                    filter_material = (new_df2 == i).any()
                    sub_df = new_df2.loc[:, filter_material]
                    auc_median = []
                    conc = list(sub_df.loc['concentration'])
                    x = np.log10(conc)
                    for k, j in sub_df.iloc[:-3, :].iterrows():
                        y = list(j)
                        auc_calc = metrics.auc(x, y)
                        auc_median.append(auc_calc)
                    auc_median2 = median(auc_median)
                    if key not in dict_auc:
                        dict_auc[key] = {i: auc_median2}
                    else:
                        dict_auc[key][i] = auc_median2

        self.auc = pd.DataFrame.from_dict(dict_auc)
        self.auc.columns = [str(col) + '_AUC' for col in self.auc.columns]

    def _create_fsc_df(self, dict_sd):
        df_sd = pd.DataFrame.from_dict(dict_sd)
        df_sd['concentration'] = pd.Series(self.data.meta_data.concentration)
        df_sd['material'] = pd.Series(self.data.meta_data.materials)
        fsc_df = pd.DataFrame()

        for col in df_sd.columns:
            if col == 'concentration':
                break
            a = df_sd.groupby('material')[col].min()
            fsc_df = fsc_df.append(pd.Series(a))
        fsc_df = fsc_df.T

        return fsc_df

    def first_significant(self):
        new_dict_2sd = {}
        new_dict_3sd = {}

        for rowIndex, row in self.data.median_df.iterrows():
            for columnIndex, value in row.items():
                tmp_2sd = 0 if value < self.sd_dict[rowIndex]['sd2'] else self.p_value_dict[rowIndex][columnIndex]
                tmp_3sd = 0 if value < self.sd_dict[rowIndex]['sd3'] else self.p_value_dict[rowIndex][columnIndex]
                tmp2 = 0 if tmp_2sd > 0.05 else tmp_2sd
                tmp3 = 0 if tmp_3sd > 0.05 else tmp_3sd
                if rowIndex not in new_dict_2sd:
                    new_dict_2sd[rowIndex] = {}
                new_dict_2sd[rowIndex][columnIndex] = self.data.meta_data.concentration[
                    columnIndex] if tmp2 > 0 else np.nan

                if rowIndex not in new_dict_3sd:
                    new_dict_3sd[rowIndex] = {}
                new_dict_3sd[rowIndex][columnIndex] = self.data.meta_data.concentration[
                    columnIndex] if tmp3 > 0 else np.nan

        self.fsc_2sd = self._create_fsc_df(new_dict_2sd)
        self.fsc_3sd = self._create_fsc_df(new_dict_3sd)
        self.fsc_2sd.columns = [str(col) + '_1st_2SD' for col in self.fsc_2sd.columns]
        self.fsc_3sd.columns = [str(col) + '_1st_3SD' for col in self.fsc_3sd.columns]

    def max_effect(self):
        dinv = {}
        for k, v in self.data.meta_data.materials.items():
            if v in dinv:
                dinv[v].append(k)
            else:
                dinv[v] = [k]

        dict_max = {}
        for key in dinv:
            for num, cell in enumerate(self.data.normalized_df['cells'].unique()):
                for n, time in enumerate(self.data.normalized_df['time'].unique()):
                    new_row = self.data.normalized_df.groupby(['time', 'cells']).get_group((time, cell))
                    max_v = new_row[dinv[key]].max(axis=1).median()
                    k = f'{cell}_{time}'
                    if key not in dict_max:
                        dict_max[key] = {k: max_v}
                    else:
                        dict_max[key][k] = max_v

        self.max = pd.DataFrame.from_dict(dict_max).T
        self.max.columns = [str(col) + '_MAX' for col in self.max.columns]

    def concatenate_parameters(self):
        self.data.dose_response_df = pd.concat([self.auc, self.fsc_2sd, self.fsc_3sd, self.max], axis=1)
        self.data.dose_response_df.columns = [str(col) + '_' + self.data.endpoint for col in
                                              self.data.dose_response_df.columns]
        self.data.dose_response_df = self.data.dose_response_df.drop('Dispersant')

    def dose_response_parameters(self):
        self.calc_p_values()
        self.calc_2_3_sd_of_blanks()
        self.calc_auc()
        self.first_significant()
        self.max_effect()
        self.concatenate_parameters()
