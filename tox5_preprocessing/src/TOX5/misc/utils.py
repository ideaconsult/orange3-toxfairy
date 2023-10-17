import pandas as pd
import os
import glob
from openpyxl import load_workbook


def add_annot_data(df, material, concentration, code):
    return df.append(pd.Series(material, index=df.columns, name='material')) \
        .append(pd.Series(concentration, index=df.columns, name='concentration')) \
        .append(pd.Series(code, index=df.columns, name='code'))


def insert_columns(df, column_names, *arrays):
    for i, column in enumerate(column_names):
        df.insert(loc=i, column=column, value=arrays[i])


def add_endpoint_parameters(df, replicates, times, cells):
    df.insert(loc=0, column='replicate', value=replicates)
    df.insert(loc=1, column='time', value=times)
    df.insert(loc=2, column='cells', value=cells)


def annotate_data(df, nested_dict):
    df.loc['material'] = pd.Series({
        col: nested_dict[col]['material'] if col in nested_dict else None for col in df.columns})
    df.loc['concentration'] = pd.Series(
        {col: nested_dict[col]['concentration'] if col in nested_dict else None for col in df.columns})


def _extract_info_from_filename(file_name):
    file_name_without_extension = os.path.splitext(file_name)[0]
    parts = file_name_without_extension.split('_')
    meta_data = {}
    for i, part in enumerate(parts):
        meta_data[f'Part_{i + 1}'] = part
    meta_data['Full Name'] = file_name
    return meta_data


def generate_annotation_file(directories, template_path):
    data_list = []
    for directory in directories:
        all_files = glob.glob(os.path.join(directory, "*.*"))

        for file_dir in all_files:
            _, file_name = os.path.split(file_dir)
            data = _extract_info_from_filename(file_name)
            if data:
                data_list.append(data)

    df = pd.DataFrame(data_list)

    book = load_workbook(template_path)
    writer = pd.ExcelWriter(template_path, engine='openpyxl')
    writer.book = book
    df.to_excel(writer, sheet_name='Files', index=False, header=False, startrow=1)
    writer.save()

