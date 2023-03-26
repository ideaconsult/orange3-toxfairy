from TOX5_calc.cell_viability import CellViability
from TOX5_calc.imaging import Imaging
from scipy import stats
import pandas as pd
import numpy as np
from sklearn import metrics
from statistics import median


class DoseResponse:
    def __init__(self, obj):
        self.obj = obj
        self.normalized = self.obj.get_normalized()
        self.median = self.obj.get_median()
        self.code = self.obj.code
        self.water_keys = self.obj.water_keys
        self.materials = self.obj.materials
        self.concentration = self.obj.concentration

        self.sd_dict = {}
        self.p_value_dict = {}
        self.data_for_auc = []

        self.auc = pd.DataFrame()
        self.fsc_2sd = pd.DataFrame()
        self.fsc_3sd = pd.DataFrame()
        self.max = pd.DataFrame()

        self.dose_response = pd.DataFrame()

    # def __repr__(self):
    #     return str(self.data_for_auc)

    def calc_p_values_and_sd(self):
        for num, cell in enumerate(self.normalized['cells'].unique()):
            for n, time in enumerate(self.normalized['time'].unique()):
                p_values = []

                new_row = self.normalized.groupby(['time', 'cells']).get_group((time, cell))

                new_water_subdf = new_row[self.water_keys].values.tolist()
                y = np.concatenate(new_water_subdf)
                y = y[~np.isnan(y)]
                stdev = np.std(y, ddof=1)
                median_m = np.median(y)

                key_dict = f'{cell}_{time}'
                self.sd_dict[key_dict] = {'sd2': median_m + 2 * stdev, 'sd3': median_m + 3 * stdev}

                for col_name, col_data in new_row.iloc[:, 3:-3].iteritems():
                    p = stats.ttest_ind(col_data.values, y).pvalue.round(60)
                    pv = p if pd.isna(p) is not True else 0
                    p_values.append(pv)
                    if key_dict not in self.p_value_dict:
                        self.p_value_dict[key_dict] = {col_name: pv}
                    else:
                        self.p_value_dict[key_dict][col_name] = pv

    def clean_data_for_auc(self):
        for _, cell in enumerate(self.normalized['cells'].unique()):
            for _, time in enumerate(self.normalized['time'].unique()):
                new_row = self.normalized.groupby(['time', 'cells']).get_group((time, cell))

                for rowIdx, row in new_row.loc[:, 'A1':'P24'].iterrows():
                    for colIdx, value in row.items():
                        key = f'{cell}_{time}'
                        new_row[colIdx] = np.where(self.median.loc[key, colIdx] < self.sd_dict[key]['sd2'], 0, new_row[colIdx])
                self.data_for_auc.append(new_row)

        self.data_for_auc = pd.concat(self.data_for_auc)
        self.data_for_auc.iloc[0:, 3:-4] = self.data_for_auc.iloc[0:, 3:-4].fillna(0)
        self.data_for_auc = self.data_for_auc.drop(['median control', 'median', 'std', 'median 2sd'], axis=1)

    def calc_auc(self):
        material_set = list(set(self.materials.values()))

        dict_auc = {}
        for num, cell in enumerate(self.normalized['cells'].unique()):
            for n, time in enumerate(self.normalized['time'].unique()):
                key = f'{cell}-{time}'
                new_df2 = self.normalized.groupby(['time', 'cells']).get_group((time, cell))

                new_df2 = new_df2.append(pd.Series(self.materials, index=self.normalized.columns, name='material'))\
                    .append(pd.Series(self.concentration, index=self.normalized.columns, name='concentration'))\
                    .append(pd.Series(self.code, index=self.normalized.columns, name='code'))

                # new_df2 = add_annot_data(new_df2, annot_file)
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

                    auc_median2 = median(auc_median)  # calculate stdev ?

                    if key not in dict_auc:
                        dict_auc[key] = {i: auc_median2}
                    else:
                        dict_auc[key][i] = auc_median2

        self.auc = pd.DataFrame.from_dict(dict_auc)
        self.auc.columns = [str(col) + '_AUC' for col in self.auc.columns]

    def _create_fsc_df(self, dict_sd):
        df_sd = pd.DataFrame.from_dict(dict_sd)
        df_sd['concentration'] = pd.Series(self.concentration)
        df_sd['material'] = pd.Series(self.materials)
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

        for rowIndex, row in self.median.iterrows():
            for columnIndex, value in row.items():
                tmp_2sd = 0 if value < self.sd_dict[rowIndex]['sd2'] else self.p_value_dict[rowIndex][columnIndex]
                tmp_3sd = 0 if value < self.sd_dict[rowIndex]['sd3'] else self.p_value_dict[rowIndex][columnIndex]
                tmp2 = 0 if tmp_2sd > 0.05 else tmp_2sd
                tmp3 = 0 if tmp_3sd > 0.05 else tmp_3sd
                if rowIndex not in new_dict_2sd:
                    new_dict_2sd[rowIndex] = {}
                new_dict_2sd[rowIndex][columnIndex] = self.concentration[columnIndex] if tmp2 > 0 else np.nan

                if rowIndex not in new_dict_3sd:
                    new_dict_3sd[rowIndex] = {}
                new_dict_3sd[rowIndex][columnIndex] = self.concentration[columnIndex] if tmp3 > 0 else np.nan

        self.fsc_2sd = self._create_fsc_df(new_dict_2sd)
        self.fsc_3sd = self._create_fsc_df(new_dict_3sd)
        self.fsc_2sd.columns = [str(col) + '_1st_2SD' for col in self.fsc_2sd.columns]
        self.fsc_3sd.columns = [str(col) + '_1st_3SD' for col in self.fsc_3sd.columns]

    def max_effect(self):
        dinv = {}
        for k, v in self.materials.items():
            if v in dinv:
                dinv[v].append(k)
            else:
                dinv[v] = [k]

        dict_max = {}
        for key in dinv:
            for num, cell in enumerate(self.normalized['cells'].unique()):
                for n, time in enumerate(self.normalized['time'].unique()):
                    new_row = self.normalized.groupby(['time', 'cells']).get_group((time, cell))
                    max_v = new_row[dinv[key]].max(axis=1).median()
                    k = f'{cell}_{time}'
                    if key not in dict_max:
                        dict_max[key] = {k: max_v}
                    else:
                        dict_max[key][k] = max_v

        self.max = pd.DataFrame.from_dict(dict_max).T
        self.max.columns = [str(col) + '_MAX' for col in self.max.columns]

    def concatenate_parameters(self):
        self.dose_response = pd.concat([self.auc, self.fsc_2sd, self.fsc_3sd, self.max], axis=1)
        self.dose_response.columns = [str(col) + '_' + self.obj.ENDPOINT for col in self.dose_response.columns]
        self.dose_response = self.dose_response.drop('Dispersant')

    def print_dose_response_df(self):
        return self.dose_response
