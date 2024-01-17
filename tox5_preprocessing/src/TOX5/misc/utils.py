import pandas as pd
import os
import glob
import warnings
import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
import math


# TODO: to be removed
def add_annot_data(df, material, concentration, code):
    return df.append(pd.Series(material, index=df.columns, name='material')) \
        .append(pd.Series(concentration, index=df.columns, name='concentration')) \
        .append(pd.Series(code, index=df.columns, name='code'))


def insert_columns(df, column_names, *arrays):
    for i, column in enumerate(column_names):
        df.insert(loc=i, column=column, value=arrays[i])


def add_endpoint_parameters(df, replicates, times, cells):
    df.insert(loc=0, column='replicates', value=replicates)
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
    error_message = None

    for directory in directories:
        no_extension_files = [file for file in os.listdir(directory) if
                              os.path.isfile(os.path.join(directory, file)) and '.' not in file]
        if no_extension_files:
            joined_files = '\n'.join(no_extension_files)
            error_message = 'Files without extensions.Please add extensions, or ' \
                            f'this files will be skipped.\n{joined_files}'

        all_files = glob.glob(os.path.join(directory, "*.*"))

        for file_dir in all_files:
            _, file_name = os.path.split(file_dir)
            data = _extract_info_from_filename(file_name)
            if data:
                data_list.append(data)

    df = pd.DataFrame(data_list)
    """
    Use pd.ExcelWriter but with openpyxl engine, which support append mode, without load_workbook instance.
    The pd.ExcelWriter will handle the creation and management of the workbook
    """
    with pd.ExcelWriter(template_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, sheet_name='Files', index=False, header=False, startrow=1)

    if error_message:
        warnings.warn(error_message, Warning)


def plot_tox_rank_pie(df, materials=None, figure=None):
    """
    Plot Tox5-score materials using a pie plot.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing Toxpi data. It should have the following columns:
      - 'index': indexes.
      - 'Material': The material names.
      - 'toxpi_score': Toxpi scores for the materials.
      - 'rnk': Ranks associated with the materials.
      - 'slices': Values for different slices of each material.
    - materials (list or None, optional): List of materials to plot. If None, all unique materials in the DataFrame are used.
    - figure (matplotlib.figure.Figure or None, optional): The Figure object to use for the plot. If None, a new Figure is created.
      Used in Orange canvas to plot.

    Returns:
    - tuple of matplotlib.figure.Figure: The main figure with pie view of each material and a separate figure for the legend.

    Example:
    ```
    # Plot Tox5-score materials with default options
    main_fig, legend_fig = plot_tox_rank_pie(df)

    # Optionally specify materials and existing Figure
    selected_materials = ['Material1', 'Material2']
    existing_figure = plt.figure()
    main_fig, legend_fig = plot_tox_rank_pie(df, materials=selected_materials, figure=existing_figure)
    ```
    """
    if figure is None:
        figure = plt.figure(tight_layout=True)

    figure.clear()
    plt.subplots_adjust(hspace=0.2)
    plt.suptitle("Toxpi Ranked materials", fontsize=10, y=0.95)

    if materials is None:
        materials = df['Material'].unique().tolist()

    columns = math.ceil(len(materials) / 5)

    rows = len(materials) // columns + (len(materials) % columns > 0)

    legend_handles = []
    labels = df.columns[4:].tolist()

    for n, i in enumerate(materials):
        rank = (df[df['Material'] == i].iloc[:, 2]).values[0]
        data_tox = df[df['Material'] == i].iloc[:, 4:].values.flatten().tolist()
        width = 2 * np.pi / len(labels)
        angle = np.linspace(0.0, 2 * np.pi, len(labels), endpoint=False)
        colors = cm.get_cmap('plasma', len(labels)).colors

        ax = plt.subplot(rows, columns, n + 1, projection='polar')
        bars = ax.bar(angle, data_tox, width=width, bottom=0.02, color=colors, alpha=0.6, edgecolor='grey')
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        ax.spines['polar'].set_color('grey')
        plt.title(f"{i} {rank.round(2)}", fontsize=8)

        legend_handles.extend(bars)

    legend_figure = plt.figure()
    legend_handles = legend_handles[len(labels):]

    plt.legend(legend_handles, labels, loc='center', fontsize='small', ncol=4, mode='expand')
    plt.axis('off')

    return figure, legend_figure


warnings.simplefilter("always", Warning)
