import pandas as pd
import os
import glob
import warnings
import numpy as np
from matplotlib import cm, patches
import matplotlib.pyplot as plt
import math

# TODO: to be removed
from matplotlib.colors import ListedColormap


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
    if isinstance(directories, str):
        directories = [directories]

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


def _create_color_map(labels, colored_by='endpoint'):
    """
    Parameters:
    - colored_by (string): the strings could be "endpoint", "cells", "time" and pies will be separately
    colored by chosen parameter.

    """
    cmap_galery = ['Purples', 'Greens', 'Blues', 'Oranges', 'Reds', 'Greys',
                   'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                   'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']

    cells_set = set()
    times_set = set()
    endpoints_set = set()
    for label in labels:
        cell, time, endpoint = label.split('_')
        cells_set.add(cell)
        times_set.add(time)
        endpoints_set.add(endpoint)

    color_palette_dict = {}
    if colored_by == 'cells':
        selected_set = cells_set
    elif colored_by == 'time':
        selected_set = times_set
    elif colored_by == 'endpoint':
        selected_set = endpoints_set
    else:
        raise ValueError("Invalid value for colored_by. Choose from 'endpoint', 'cells', 'time'.")

    for idx, param in enumerate(selected_set):
        num_occurrences = sum(param in label for label in labels)
        colors_pallete = plt.colormaps[cmap_galery[idx]](np.linspace(0.2, 1, num_occurrences)).tolist()
        for i, label in enumerate(labels):
            if param in label:
                color = colors_pallete.pop(0)
                color_palette_dict[label] = color
            else:
                continue

    colors = [color_palette_dict[label] for label in labels]
    return colors


def plot_tox_rank_pie(df, materials=None, figure=None, colored_param='cells', transparency_bars=0.6, linewidth=0.2,
                      conf_intervals=None, ci_low_color="#ff5c33", ci_high_color="#ff5c33", pies_per_col=2):
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
    - conf_intervals (dict or None, optional): Dictionary containing confidence intervals for each slice.
      Keys are the slice labels, values are tuples (CI_lower, CI_upper).

    Returns:
    - tuple of matplotlib.figure.Figure: The main figure with pie view of each material and a separate figure for the legend.
    """
    if figure is None:
        figure = plt.figure(tight_layout=True)

    figure.clear()
    plt.subplots_adjust(hspace=0.2)
    plt.suptitle("Toxpi Ranked materials", fontsize=10, y=0.95)

    if 'low_ci' in df.columns:
        df = df.drop(columns=['low_ci'])

    if 'high_ci' in df.columns:
        df = df.drop(columns=['high_ci'])

    if materials is None:
        materials = df['Material'].unique().tolist()

    columns = math.ceil(len(materials) / pies_per_col)  # /5
    rows = len(materials) // columns + (len(materials) % columns > 0)

    labels = df.columns[3:].tolist()

    # Sort labels based on the chosen parameter
    labels_sorted = sorted(labels, key=lambda x: x.split('_')[{'cells': 0, 'time': 1, 'endpoint': 2}[colored_param]])

    # Create colormap
    colors = _create_color_map(labels_sorted, colored_by=colored_param)
    legend_handles = []

    for n, i in enumerate(materials):
        rank = (df[df['Material'] == i].iloc[:, 2]).values[0]
        data_tox = df[df['Material'] == i].iloc[:, 3:].values.flatten().tolist()

        # Sort data_tox based on the sorted labels
        data_tox_sorted = [data_tox[labels.index(label)] for label in labels_sorted]

        width = 2 * np.pi / len(labels_sorted)
        angle = np.linspace(0.0, 2 * np.pi, len(labels_sorted), endpoint=False)

        ax = plt.subplot(rows, columns, n + 1, projection='polar')
        bars = ax.bar(angle, data_tox_sorted, width=width, bottom=0.02, color=colors, alpha=transparency_bars,
                      edgecolor='grey', linewidth=linewidth)

        # Plot confidence intervals if provided
        if conf_intervals:
            for j, label in enumerate(labels_sorted):
                if label in conf_intervals[i]:
                    conf_interval = conf_intervals[i][label]
                    ax.fill_between([angle[j] - width / 2, angle[j] + width / 2], conf_interval[0], conf_interval[1],
                                    color='gray', alpha=0.1)

                    ax.plot([angle[j] - width / 2, angle[j] + width / 2], [conf_interval[0], conf_interval[0]],
                            color=ci_low_color, linestyle='-', linewidth=1)
                    ax.plot([angle[j] - width / 2, angle[j] + width / 2], [conf_interval[1], conf_interval[1]],
                            color=ci_high_color, linestyle='-', linewidth=1)

        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([0.2, 0.5, 1.0])
        # ax.grid(False)
        ax.spines['polar'].set_color('grey')
        plt.title(f"{i} {rank.round(2)}", fontsize=8)

        legend_handles.extend(bars)

    legend_figure = plt.figure()
    legend_handles = legend_handles[:len(labels_sorted)]

    plt.legend(legend_handles, labels_sorted, loc='center', fontsize='small', ncol=4, mode='expand')
    plt.axis('off')

    return figure, legend_figure


warnings.simplefilter("always", Warning)
