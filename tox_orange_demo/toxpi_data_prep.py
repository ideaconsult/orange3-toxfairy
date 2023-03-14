import warnings
import pandas as pd
import numpy as np
import os
import glob
from scipy import stats
from sklearn import metrics
from statistics import median

warnings.filterwarnings('ignore')


def read_annotation_data(annot_file):
    code = {}
    material = {}
    concentration = {}
    water_keys = None

    df_names = pd.read_excel(annot_file, sheet_name='Annotation', usecols="B:E", index_col=0)

    for k, v in df_names.iterrows():
        code[k] = v[0]
        material[k] = v[1]
        concentration[k] = v[2]

    water_keys = [k for k, v in code.items() if v == 'water']

    return water_keys, code, material, concentration


def read_raw_data(endpoint, annot_file, path):
    all_files = glob.glob(os.path.join(path, "*.csv"))
    df = pd.DataFrame()

    replicates = []
    times = []
    cells = []

    for filename in all_files:
        if endpoint in filename:
            names = filename[len(path) + 1:-13]
            (replicate, time, endpoint, cell) = names.split('_')
            replicates.append(replicate)
            times.append(time)
            cells.append(cell)

            df_test = pd.read_csv(filename,
                                  sep='[;,]',
                                  skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
                                            38])
            df_test = df_test.set_index('Unnamed: 0')
            df_test = df_test.T
            df_out = df_test.stack()
            df_out.index = df_out.index.map('{0[1]}{0[0]}'.format)
            df = df.append(df_out, ignore_index=True)

    df.insert(0, 'replicate', replicates)
    df.insert(1, 'time', times)
    df.insert(2, 'cells', cells)
    df[['time', 'cells']] = df[['time', 'cells']].apply(lambda col: col.str.upper().str.strip())

    return add_annot_data(df, annot_file)


def read_imaging_raw(path, sheet):
    df = pd.read_excel(path, sheet_name=sheet, index_col=1, header=None)
    df.drop(df.columns[[0]], axis=1, inplace=True)
    df = df.T
    df[['time', 'cell']] = df[['time', 'cell']].apply(lambda col: col.str.upper().str.strip())

    return df


def correct_from_dapi(col):
    if col.iloc[0] == 0:
        col = col.shift(-2)

    return col


def correct_all_dapi(col):
    median_dapi = col.median()
    if median_dapi > 50:
        col = col.replace(0, np.nan)

    return col


def clean_imaging_raw(df):
    new_df = pd.DataFrame()

    for idx1, cell in enumerate(df['cell'].unique()):
        for idx2, time in enumerate(df['time'].unique()):
            tmp = df.groupby(['cell', 'time']).get_group((cell, time))
            dapi_idx = tmp[tmp['Description'] == 'Dapi'].index.values
            for i in dapi_idx:
                a = tmp.loc[i:i + 2, 'A1':].apply(correct_from_dapi)
                new_df = new_df.append(a)
            tmp2 = tmp.loc[dapi_idx, 'A1':].apply(correct_all_dapi)
            new_df.loc[tmp2.index, :] = tmp2[:]

    new_df = new_df.sort_index(ascending=True)
    new_df.insert(0, "replicate", df['rep'])
    new_df.insert(1, "time", df['time'])
    new_df.insert(2, "cells", df['cell'])
    new_df.insert(3, "description", df['Description'])

    return new_df


def create_imaging_cleaned_df(df, endpoint, annot_file):
    df_imaging = df[df['description'] == endpoint].reset_index(drop=True).drop(['description'], axis=1)

    return add_annot_data(df_imaging, annot_file)


def remove_outlayer(df):
    filter = ((df == 'water')).any()
    sub_df = df.loc[:, filter].iloc[:-3].astype(float)

    sub_df['lower Bound'] = sub_df.quantile(0.25, axis=1) - 1.5 * (
            sub_df.quantile(0.75, axis=1) - sub_df.quantile(0.25, axis=1))
    sub_df['upper Bound'] = sub_df.iloc[:, :-1].quantile(0.75, axis=1) + 1.5 * (
            sub_df.iloc[:, :-1].quantile(0.75, axis=1) - sub_df.iloc[:, :-1].quantile(0.25, axis=1))

    for i, j in sub_df.iterrows():
        sub_df.loc[i] = sub_df.loc[i].apply(
            lambda x: x if sub_df.loc[i]['upper Bound'] >= x >= sub_df.loc[i]['lower Bound'] else np.nan)

    sub_df['median control'] = sub_df.iloc[:, :-2].median(axis=1)

    columns = list(sub_df.iloc[:, :-3].keys())
    columns.append('median control')
    df = df.iloc[0:-3, :]
    df[columns] = sub_df[columns]

    return df


def percent_of_median_control(df, endpoint):
    df = df.fillna(value=np.nan)
    new_df = pd.DataFrame()

    for i, j in df.iloc[0:, 3:].iterrows():
        # if pd.isnull(x['Col1'])
        j = j.apply(
                lambda x: (1 - (x / j['median control'])) * 100 if endpoint == 'CTG' or endpoint == 'Dapi' else (x / j[
                    'median control']) * 100)

        new_df = new_df.append(pd.Series(j))

    new_df.insert(0, "replicate", df['replicate'])
    new_df.insert(1, "time", df['time'])
    new_df.insert(2, "cells", df['cells'])

    return new_df


def median_0_h(df):
    for i, j in enumerate(df['cells'].unique()):
        median = df.groupby(['time', 'cells']).get_group(('0H', j)).median()
        df = df.append(pd.Series(median, index=df.columns, name=f"median_{j}"))

    return df


def subtract_median_0_h(df, endpoint, annot_file):
    df = df[df.time != '0H']
    new_df = []
    for num, v in enumerate(df['cells'].unique()):
        tmp = df[df.cells == v]
        for i, j in tmp.iterrows():
            row_index = 'median_' + v
            tmp.loc[i, 'A1':] = df.loc[i, 'A1':] - df.loc[row_index, 'A1':] if endpoint == 'CTG' else 100 + (
                    df.loc[i, 'A1':] - df.loc[row_index, 'A1':])
        new_df.append(tmp)
    new_df = pd.concat(new_df)

    water_keys, _, _, _ = read_annotation_data(annot_file)
    new_df['median'] = new_df[water_keys].median(axis=1)
    new_df['std'] = new_df[water_keys].std(axis=1)
    new_df['median 2sd'] = new_df['median'] + 2 * new_df['std']

    return new_df


def calc_imaging_stat(df, annot_file):
    water_keys, _, _, _ = read_annotation_data(annot_file)
    df['median'] = df[water_keys].median(axis=1)
    df['std'] = df[water_keys].std(axis=1)
    df['median 2sd'] = df['median'] + 2 * df['std']

    return df


def calc_p_values_and_sd(df, annot_file):
    water_keys, code, _, _ = read_annotation_data(annot_file)

    sd_dict = {}
    pvalue_dict = {}

    for num, cell in enumerate(df['cells'].unique()):
        for n, time in enumerate(df['time'].unique()):
            p_values = []

            new_row = df.groupby(['time', 'cells']).get_group((time, cell))

            new_water_subdf = new_row[water_keys].values.tolist()
            y = np.concatenate(new_water_subdf)
            y = y[~np.isnan(y)]
            stdev = np.std(y, ddof=1)
            median_m = np.median(y)

            key_dict = f'{cell}_{time}'
            sd_dict[key_dict] = {'sd2': median_m + 2 * stdev, 'sd3': median_m + 3 * stdev}

            for col_name, col_data in new_row.iloc[:, 3:-3].iteritems():
                p = stats.ttest_ind(col_data.values, y).pvalue.round(60)
                pv = p if pd.isna(p) is not True else 0
                p_values.append(pv)

                if key_dict not in pvalue_dict:
                    pvalue_dict[key_dict] = {col_name: pv}
                else:
                    pvalue_dict[key_dict][col_name] = pv

    return sd_dict, pvalue_dict


def calc_mean_median(df, annot_file):
    water_keys, code, _, _ = read_annotation_data(annot_file)
    median_df = pd.DataFrame()
    avrg_df = pd.DataFrame()

    for num, cell in enumerate(df['cells'].unique()):
        for n, time in enumerate(df['time'].unique()):
            new_row = df.groupby(['time', 'cells']).get_group((time, cell))
            median_row = new_row.median()
            avrg = new_row.mean()
            median_df = median_df.append(pd.Series(median_row, index=list(code.keys()), name=f'{cell}_{time}'))
            avrg_df = avrg_df.append(pd.Series(avrg, index=list(code.keys()), name=f'{cell}_{time}'))

    return median_df, avrg_df


def calc_paramc_casp(annot_file, mean_CTG, mean_DAPI, df_ready_casp):
    df = pd.concat([mean_CTG, mean_DAPI])
    df_mean = df.groupby(df.index).mean()
    df_mean = df_mean.apply(lambda x: 1 - (x / 100))

    df_casp = pd.concat([df_ready_casp, df_mean])
    df_casp.insert(0, 'cell_index', df_casp['cells'] + '_' + df_casp['time'])

    df_ready = []
    for num, v in enumerate(df_casp['cell_index'].unique()):
        if not isinstance(v, str):
            break

        tmp = df_casp[df_casp.cell_index == v]
        row1 = df_casp.loc[v, 'A1':'P24']
        tmp.iloc[:, 4:-4] = tmp.iloc[:, 4:-4].apply(lambda row: row / row1, axis=1)

        df_ready.append(tmp)
    df_ready = pd.concat(df_ready)

    df_ready = df_ready.iloc[:, 1:]

    median_df, mean_df = calc_mean_median(df_ready, annot_file)

    return median_df, mean_df, df_ready


def create_fsc_df(dict_sd, annot_file):
    _, code, material, concentration = read_annotation_data(annot_file)
    df_sd = pd.DataFrame.from_dict(dict_sd)
    df_sd['concentration'] = pd.Series(concentration)
    df_sd['material'] = pd.Series(material)
    fsc_df = pd.DataFrame()

    for col in df_sd.columns:
        if col == 'concentration':
            break
        a = df_sd.groupby('material')[col].min()
        fsc_df = fsc_df.append(pd.Series(a))
    fsc_df = fsc_df.T

    return fsc_df


def first_significant_conc(df, median_df, annot_file):
    _, code, material, concentration = read_annotation_data(annot_file)
    sd_dict, pvalue_dict = calc_p_values_and_sd(df, annot_file)

    new_dict_2sd = {}
    new_dict_3sd = {}

    for rowIndex, row in median_df.iterrows():
        for columnIndex, value in row.items():
            tmp_2sd = 0 if value < sd_dict[rowIndex]['sd2'] else pvalue_dict[rowIndex][columnIndex]
            tmp_3sd = 0 if value < sd_dict[rowIndex]['sd3'] else pvalue_dict[rowIndex][columnIndex]
            tmp2 = 0 if tmp_2sd > 0.05 else tmp_2sd
            tmp3 = 0 if tmp_3sd > 0.05 else tmp_3sd
            if rowIndex not in new_dict_2sd:
                new_dict_2sd[rowIndex] = {}
            new_dict_2sd[rowIndex][columnIndex] = concentration[columnIndex] if tmp2 > 0 else np.nan

            if rowIndex not in new_dict_3sd:
                new_dict_3sd[rowIndex] = {}
            new_dict_3sd[rowIndex][columnIndex] = concentration[columnIndex] if tmp3 > 0 else np.nan

    fsc_2sd = create_fsc_df(new_dict_2sd, annot_file)
    fsc_3sd = create_fsc_df(new_dict_3sd, annot_file)
    fsc_2sd.columns = [str(col) + '_1st_2SD' for col in fsc_2sd.columns]
    fsc_3sd.columns = [str(col) + '_1st_3SD' for col in fsc_3sd.columns]

    return fsc_2sd, fsc_3sd


def max_effect(df, annot_file):
    _, code, material, concentration = read_annotation_data(annot_file)
    dinv = {}
    for k, v in material.items():
        if v in dinv:
            dinv[v].append(k)
        else:
            dinv[v] = [k]

    dict_max = {}
    for key in dinv:
        for num, cell in enumerate(df['cells'].unique()):
            for n, time in enumerate(df['time'].unique()):
                new_row = df.groupby(['time', 'cells']).get_group((time, cell))
                max_v = new_row[dinv[key]].max(axis=1).median()
                k = f'{cell}_{time}'
                if key not in dict_max:
                    dict_max[key] = {k: max_v}
                else:
                    dict_max[key][k] = max_v

    df_max = pd.DataFrame.from_dict(dict_max).T

    df_max.columns = [str(col) + '_MAX' for col in df_max.columns]

    return df_max


def clean_data_for_auc(df_ready, median_df, annot_file):
    sd_dict, pvalue_dict = calc_p_values_and_sd(df_ready, annot_file)

    new_df_auc = []
    for _, cell in enumerate(df_ready['cells'].unique()):
        for _, time in enumerate(df_ready['time'].unique()):
            new_row = df_ready.groupby(['time', 'cells']).get_group((time, cell))

            for rowIdx, row in new_row.loc[:, 'A1':'P24'].iterrows():
                for colIdx, value in row.items():
                    key = f'{cell}_{time}'
                    new_row[colIdx] = np.where(median_df.loc[key, colIdx] < sd_dict[key]['sd2'], 0, new_row[colIdx])
            new_df_auc.append(new_row)

    new_df_auc = pd.concat(new_df_auc)
    new_df_auc.iloc[0:, 3:-4] = new_df_auc.iloc[0:, 3:-4].fillna(0)
    new_df_auc = new_df_auc.drop(['median control', 'median', 'std', 'median 2sd'], axis=1)

    return new_df_auc


def calc_auc(annot_file, df):
    _, code, material, concentration = read_annotation_data(annot_file)
    material_set = list(set(material.values()))

    dict_auc = {}
    for num, cell in enumerate(df['cells'].unique()):
        for n, time in enumerate(df['time'].unique()):
            key = f'{cell}-{time}'
            new_df2 = df.groupby(['time', 'cells']).get_group((time, cell))
            new_df2 = add_annot_data(new_df2, annot_file)
            new_df2.loc['code', 'A1':] = new_df2.loc['code', 'A1':].apply(str)

            for i in material_set:
                filter_material = ((new_df2 == i)).any()
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

    df_auc = pd.DataFrame.from_dict(dict_auc)
    df_auc.columns = [str(col) + '_AUC' for col in df_auc.columns]
    return df_auc


def add_annot_data(df, annot_file):
    _, code, material, concentration = read_annotation_data(annot_file)

    return df.append(pd.Series(material, index=df.columns, name='material')) \
        .append(pd.Series(concentration, index=df.columns, name='concentration')) \
        .append(pd.Series(code, index=df.columns, name='code'))


def calc_params_ctg(endpoint, annot_file, files_path):
    df_ctg = read_raw_data(endpoint, annot_file, files_path)
    df_ctg_2 = remove_outlayer(df_ctg)
    df_ctg_percent = percent_of_median_control(df_ctg_2, endpoint)

    df_ctg_percent_0 = median_0_h(df_ctg_percent)
    df_ready = subtract_median_0_h(df_ctg_percent_0, endpoint, annot_file)

    median_df, mean_df = calc_mean_median(df_ready, annot_file)

    return median_df, mean_df, df_ready


def calc_params_imaging(endpoint, annot_file, files_path):
    df_img = read_imaging_raw(annot_file, 'Imaging raw')
    df_img_clean = clean_imaging_raw(df_img)
    df_img_new = create_imaging_cleaned_df(df_img_clean, endpoint, annot_file)
    df_img_outlayers = remove_outlayer(df_img_new)
    df_img_percent = percent_of_median_control(df_img_outlayers, endpoint)

    df_ready = calc_imaging_stat(df_img_percent, annot_file)

    median_df, mean_df = calc_mean_median(df_ready, annot_file)

    return median_df, mean_df, df_ready


def calc_final(df_ready_dapi, median_dapi, annot_file, endpoint):
    new_df_auc = clean_data_for_auc(df_ready_dapi, median_dapi, annot_file)

    auc_dapi = calc_auc(annot_file, new_df_auc)
    f_2sd_dapi, f_3sd_dapi = first_significant_conc(df_ready_dapi, median_dapi, annot_file)
    max_effect_dapi = max_effect(df_ready_dapi, annot_file)

    ready_dapi_df = pd.concat([auc_dapi, f_2sd_dapi, f_3sd_dapi, max_effect_dapi], axis=1)
    ready_dapi_df.columns = [str(col) + '_' + endpoint for col in ready_dapi_df.columns]

    return ready_dapi_df.drop('Dispersant')


def df_by_cells(df1, df2, df3, df4, df5):
    df = pd.concat([df1, df2, df3, df4, df5], axis=1)
    df.reset_index(inplace=True)
    df = df.rename(columns={'index': 'material'})

    return df
