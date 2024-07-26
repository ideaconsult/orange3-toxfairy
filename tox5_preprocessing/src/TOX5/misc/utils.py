import pandas as pd
import os
import glob
import warnings
import numpy as np
import matplotlib.pyplot as plt
import math
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.express as px
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.cluster import KMeans
import itertools


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

    def rgba_to_hex(rgba):
        """
        Convert an RGBA list to a HEX color string.
        """
        r, g, b, a = [int(c * 255) for c in rgba[:4]]
        return f'#{r:02x}{g:02x}{b:02x}'

    cmap_galery = ['Purples', 'Greens', 'Blues', 'Oranges', 'Greys', 'Reds',
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

    for label, rgba in color_palette_dict.items():
        color_palette_dict[label] = rgba_to_hex(rgba)

    colors_hex = [color_palette_dict[label] for label in labels]

    return colors, colors_hex


def plot_tox_rank_pie(df, materials=None, figure=None, colored_param='cells', transparency_bars=0.6, linewidth=0.2,
                      conf_intervals=None, ci_low_color="#ff5c33", ci_high_color="#ff5c33", pies_per_col=5,
                      legend_cols=2):
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

    # if 'low_ci' in df.columns:
    #     df = df.drop(columns=['low_ci'])
    #
    # if 'high_ci' in df.columns:
    #     df = df.drop(columns=['high_ci'])

    if not materials:
        materials = df['Material'].unique().tolist()

    columns = math.ceil(len(materials) / pies_per_col)  # /5
    rows = len(materials) // columns + (len(materials) % columns > 0)

    labels = df.columns[3:].tolist()

    # Sort labels based on the chosen parameter
    labels_sorted = sorted(labels, key=lambda x: x.split('_')[{'cells': 0, 'time': 1, 'endpoint': 2}[colored_param]])

    # Create colormap
    colors, _ = _create_color_map(labels_sorted, colored_by=colored_param)
    legend_handles = []

    for n, i in enumerate(materials):
        rank = (df[df['Material'] == i].iloc[:, 2]).values[0]
        score = (df[df['Material'] == i].iloc[:, 1]).values[0]
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
        plt.title(f"{i} {score.round(2)}", fontsize=8)

        legend_handles.extend(bars)

    legend_figure = plt.figure()
    legend_handles = legend_handles[:len(labels_sorted)]

    plt.legend(legend_handles, labels_sorted, loc='center', fontsize='small', ncol=legend_cols, mode='expand')
    plt.axis('off')

    return figure, legend_figure


def plot_tox_rank_pie_interactive(df, materials=None, output_directory=None, pies_per_col=4, pie_size=800,
                                  colored_param='cells',
                                  conf_intervals=None, transparency_bars=0.8, linewidth=1,
                                  ci_low_color='blue', ci_high_color='red', file_name='tox_pie_interactive'):
    if not materials:
        materials = df['Material'].unique().tolist()

    columns = math.ceil(len(materials) / pies_per_col)
    rows = len(materials) // columns + (len(materials) % columns > 0)

    figure = make_subplots(
        rows=rows,
        cols=columns,
        specs=[[{'type': 'polar'} for _ in range(columns)] for _ in range(rows)],
        subplot_titles=[f"{i}" for i in materials]
    )

    labels = df.columns[3:].tolist()
    labels_sorted = sorted(labels, key=lambda x: x.split('_')[{'cells': 0, 'time': 1, 'endpoint': 2}[colored_param]])
    colors, colors_hex = _create_color_map(labels_sorted, colored_by=colored_param)
    legend_handles = []

    for n, i in enumerate(materials):
        row = (n // columns) + 1
        col = (n % columns) + 1

        rank = (df[df['Material'] == i].iloc[:, 2]).values[0]
        score = (df[df['Material'] == i].iloc[:, 1]).values[0]
        data_tox = df[df['Material'] == i].iloc[:, 3:].values.flatten().tolist()
        data_tox_sorted = [data_tox[labels.index(label)] for label in labels_sorted]

        angle = np.linspace(0.0, 360.0, len(labels_sorted), endpoint=False)
        width = 360.0 / len(labels_sorted)

        customdata = np.stack([labels_sorted, [score] * len(labels_sorted)], axis=-1)
        figure.add_trace(go.Barpolar(
            r=data_tox_sorted,
            theta=angle,
            width=width,
            marker_color=colors_hex,
            opacity=transparency_bars,
            marker_line_color='grey',
            marker_line_width=linewidth,
            customdata=customdata,
            hovertemplate='<b>Label:</b> %{customdata[0]}<br>' +
                          '<i>Score:</i> %{r:.2f}<br>',
            # name=f"{i} - {score}",
            showlegend=False
        ), row, col)

        if conf_intervals:
            conf_r = [conf_intervals[i][label][1] - conf_intervals[i][label][0] for label in labels_sorted]
            conf_base = [conf_intervals[i][label][0] for label in labels_sorted]

            figure.add_trace(go.Barpolar(
                r=conf_r,
                theta=angle,
                width=width,
                base=conf_base,
                marker_color='grey',
                opacity=0.3,
                hoverinfo='none',
                showlegend=False
            ), row=row, col=col)

            for j, label in enumerate(labels_sorted):
                if label in conf_intervals[i]:
                    conf_interval = conf_intervals[i][label]
                    figure.add_trace(go.Scatterpolar(
                        r=[conf_interval[0], conf_interval[0]],
                        theta=[angle[j] - width / 2, angle[j] + width / 2],
                        mode='lines',
                        line=dict(color=ci_low_color, width=2),
                        hoverinfo="r",
                        showlegend=False
                    ), row=row, col=col)
                    figure.add_trace(go.Scatterpolar(
                        r=[conf_interval[1], conf_interval[1]],
                        theta=[angle[j] - width / 2, angle[j] + width / 2],
                        mode='lines',
                        line=dict(color=ci_high_color, width=2),
                        hoverinfo='r',
                        showlegend=False
                    ), row=row, col=col)

        for n, i in enumerate(materials):
            score = (df[df['Material'] == i].iloc[:, 1]).values[0]
            figure.layout.annotations[n].update(text=f"{i} ({score:.2f})")

        figure.update_polars(radialaxis=dict(range=[0, 1], tickvals=[0.2, 0.5, 1.0]))
        figure.update_layout(title=f"Toxpi Ranked materials", font=dict(size=10))
        legend_handles.append(labels_sorted)

    figure.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[0, 1],
                tickvals=[0.2, 0.5, 1.0]
            )
        ),
        title="Toxpi Ranked materials",
        height=rows * pie_size,
        width=columns * pie_size,
        # legend=dict(
        #     traceorder='normal',
        #     x=-0.2,  # Position to the left outside the plotting area
        #     y=0.5,
        #     xanchor='right',
        #     yanchor='middle',
        #     orientation='v',  # Vertical orientation
        #     itemsizing='trace'
        # ),
        margin=dict(l=200, r=50, t=100, b=100)  # Adjust margins to avoid overlap
    )

    figure.update_polars(
        angularaxis=dict(
            tickmode='array',
            tickvals=angle,
            ticktext=[''] * len(angle)  # Empty tick labels
        )
    )

    for label, color in zip(labels_sorted, colors_hex):
        figure.add_trace(go.Scatterpolar(
            r=[None],
            theta=[None],
            mode='markers',
            marker=dict(color=color),
            showlegend=True,
            name=label
        ))

    figure.update_layout(dragmode='pan')
    if output_directory:
        figure_html_file = os.path.join(output_directory, f'{file_name}.html')
        pio.write_html(figure, figure_html_file, auto_open=False)

    return figure


def _generate_colors(num_colors):
    color_palette = [
        '#FFA500',  # Orange
        '#FF00FF',  # Pink
        '#00FFFF',  # Cyan
        '#FFFF00',  # Yellow
        '#800080',  # Purple
        '#FFD700',  # Gold
        '#FF1493',  # Deep Pink
        '#4B0082',  # Indigo
        '#8B0000',  # Dark Red (but distinct from pure red)
        '#8A2BE2',  # Blue Violet
        '#FF4500',  # Orange Red
        '#DA70D6',  # Orchid
        '#EEE8AA',  # Pale Goldenrod
        '#DDA0DD',  # Plum
        '#BC8F8F',  # Rosy Brown
        '#4682B4',  # Steel Blue
        '#D8BFD8',  # Thistle
        '#FF6347',  # Tomato
        '#40E0D0',  # Turquoise
    ]

    color_palette_iter = itertools.cycle(color_palette)
    hex_colors = [next(color_palette_iter) for _ in range(num_colors)]

    return hex_colors


def plot_ranked_material(df, x_name, y_name, materials,
                         negative_controls=None, positive_controls=None, substance_types=None,
                         x_ci_dict=None, y_ci_dict=None,
                         marker_resize=0.8,
                         output_directory=None, file_name='tox_ranking'):
    category_colors = {'Material': 'blue', 'Negative Control': 'green', 'Positive Control': 'red'}
    default_color = 'blue'
    unique_materials = list(set(df[materials]))
    legend_labels = {material: 'Material' for material in unique_materials}
    legend_colors = {'Material': default_color}

    if positive_controls or negative_controls or substance_types:
        num_groups = len(substance_types) if substance_types else 0
        color_palette = _generate_colors(num_groups)
        color_palette_iter = itertools.cycle(color_palette)

        if substance_types:
            for group in substance_types.keys():
                if group not in category_colors:
                    category_colors[group] = next(color_palette_iter)

        for material in unique_materials:
            if negative_controls and material in negative_controls:
                legend_labels[material] = 'Negative Control'
            elif positive_controls and material in positive_controls:
                legend_labels[material] = 'Positive Control'
            elif substance_types:
                for group in substance_types:
                    if material in substance_types[group]:
                        legend_labels[material] = group
                        break

        legend_colors.update({value: category_colors[value] for value in set(legend_labels.values())})

    fig = go.Figure()
    unique_groups = set(legend_labels.values())
    for group in unique_groups:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            marker=dict(size=marker_resize, color=legend_colors[group]),
            legendgroup=group,
            showlegend=True,
            name=group
        ))

    if y_name == 'Material':
        sorted_materials = df.sort_values(by=x_name)[materials].unique()
        y_mapping = {material: i for i, material in enumerate(sorted_materials)}
        df['y_mapped'] = df[materials].map(y_mapping)
        y_values = df['y_mapped']
        y_tickvals = list(y_mapping.values())
        y_ticktext = list(y_mapping.keys())
    else:
        y_values = df[y_name]
        y_tickvals = df[y_name].unique()
        y_ticktext = df[y_name].unique()

    for material in unique_materials:
        material_df = df[df[materials] == material]

        error_x, error_x_minus = None, None
        error_y, error_y_minus = None, None

        if x_ci_dict:
            error_x = material_df[x_ci_dict[0]] - material_df[x_name]
            error_x_minus = material_df[x_name] - material_df[x_ci_dict[1]]
        if y_ci_dict:
            error_y = material_df[y_ci_dict[0]] - material_df[y_name]
            error_y_minus = material_df[y_name] - material_df[y_ci_dict[1]]

        fig.add_trace(go.Scatter(
            x=material_df[x_name],
            # y=material_df[y_name],
            y=y_values[material_df.index],
            mode='markers',
            name=legend_labels[material],
            marker=dict(size=marker_resize, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')),
            error_x=dict(type='data', array=error_x, arrayminus=error_x_minus, visible=True,
                         thickness=1.5, width=1.5, color='gray'),
            error_y=dict(type='data', array=error_y, arrayminus=error_y_minus, visible=True,
                         thickness=1.5, width=1.5, color='gray'),
            hovertext=material_df[materials],
            hovertemplate=f'{materials}: {material}<br>{x_name}: %{{x}}<br>{y_name}: %{{y}}<extra></extra>',
            marker_color=legend_colors[legend_labels[material]],
            showlegend=False
        ))

    x_axis = None
    y_axis = None

    if y_name == 'Material':
        if x_name == 'rnk':
            x_axis = dict(autorange=True)
            y_axis = dict(autorange='reversed', tickmode='array', tickvals=y_tickvals, ticktext=y_ticktext)
        elif x_name == 'toxpi_score':
            x_axis = dict(autorange='reversed')
            y_axis = dict(autorange=True, tickmode='array', tickvals=y_tickvals, ticktext=y_ticktext)

    elif y_name == 'rnk' and x_name == 'toxpi_score':
        x_axis = dict(autorange='reversed')
        y_axis = dict(autorange='reversed', tickmode='array', tickvals=y_tickvals, ticktext=y_ticktext)

    elif y_name == 'toxpi_score' and x_name == 'rnk':
        x_axis = dict(autorange=True)
        y_axis = dict(autorange=True, tickmode='array', tickvals=y_tickvals, ticktext=y_ticktext)

    else:
        x_axis = dict(autorange=True)
        y_axis = dict(autorange='reversed', tickmode='array', tickvals=y_tickvals, ticktext=y_ticktext)

    fig.update_layout(
        title='Material ranking',
        xaxis_title=x_name,
        yaxis_title=y_name,
        font=dict(size=12),
        yaxis=y_axis,
        xaxis=x_axis,
        template='plotly_white',
        width=1100, height=800
    )

    if output_directory:
        figure_html_file = os.path.join(output_directory, f'{file_name}.html')
        pio.write_html(fig, figure_html_file, auto_open=False)

    return fig


def _find_threshold_for_n_clusters(Z, num_clusters):
    distances = Z[:, 2]
    max_distance = distances.max()
    for threshold in np.linspace(0, max_distance, 1000):
        clusters = fcluster(Z, t=threshold, criterion='distance')
        if len(np.unique(clusters)) == num_clusters:
            return threshold
    return max_distance


def _clusters_by_elbow(features):
    cluster_range = range(2, 21)
    inertia_values = []
    for n_clusters in cluster_range:
        kmeans = KMeans(n_clusters=n_clusters, random_state=0)
        kmeans.fit(features)
        inertia_values.append(kmeans.inertia_)
    first_derivative = np.diff(inertia_values)
    second_derivative = np.diff(first_derivative)
    elbow_index = np.argmin(second_derivative)
    optimal_clusters = cluster_range[elbow_index]
    return optimal_clusters


def _clusters_by_silhouette(features):
    silhouette_scores = []
    cluster_range = range(2, 21)

    for n_clusters in cluster_range:
        agglomerative = AgglomerativeClustering(n_clusters=n_clusters)
        cluster_labels = agglomerative.fit_predict(features)

        silhouette_avg = silhouette_score(features, cluster_labels)
        silhouette_scores.append(silhouette_avg)
    max_index = np.argmax(silhouette_scores)

    optimal_clusters = cluster_range[max_index]
    return optimal_clusters


def h_clustering(features, labels, metric='euclidean', method='ward', clusters='elbow', output_directory=None,
                 file_name='dendogram'):
    """
    Perform hierarchical clustering on the provided features and labels.
    Metrics could be euclidean, cityblock, cosine, hamming, minkowski
    Methods could be ward, single, complete, average, centroid, median, weighted
    Clusters could be elbow, silhouette or int in range 1 to 20

    Metrics Explanation

    Silhouette Score: Range: [−1,1] Measures how similar an object is to its own cluster compared to other clusters.
    A score closer to 1 indicates well-separated clusters, a score close to 0 indicates overlapping clusters, and a
    score close to -1 indicates that the objects might be wrongly clustered. Higher is better.

    Davies-Bouldin Score: [0,∞) Measures the average similarity ratio of each cluster with its most similar cluster.
    Lower values indicate better clustering because the clusters are more distinct from each other. Lower is better.

    Calinski-Harabasz Score: [0,∞) Measures the ratio of the sum of between-cluster dispersion to within-cluster dispersion.
    Higher values indicate that clusters are well-separated and compact. Higher is better.
    """

    distance_matrix = pdist(features, metric=metric)
    linked = linkage(distance_matrix, method=method)
    if clusters == 'elbow':
        num_clusters = _clusters_by_elbow(features)
    elif clusters == 'silhouette':
        num_clusters = _clusters_by_silhouette(features)
    elif isinstance(clusters, int) and 2 <= clusters <= 20:
        num_clusters = clusters
    else:
        raise ValueError("Invalid value for 'clusters'. Must be 'elbow', 'silhouette', or an integer between 2 and 20.")

    # Obtain flat clusters
    cluster_labels = fcluster(linked, num_clusters, criterion='maxclust')

    silhouette_avg = silhouette_score(features, cluster_labels, metric=metric)
    davies_bouldin_avg = davies_bouldin_score(features, cluster_labels)
    calinski_harabasz_avg = calinski_harabasz_score(features, cluster_labels)

    threshold = _find_threshold_for_n_clusters(linked, num_clusters)

    fig, ax = plt.subplots(figsize=(10, 7))
    dendrogram(
        linked,
        labels=labels,
        color_threshold=threshold - 0.1,
        above_threshold_color='black',
        orientation='right',
        show_contracted=True,
        leaf_font_size=10,
        ax=ax
    )

    ax.set_title('Hierarchical Clustering Dendrogram')
    ax.set_xlabel('Distance')
    ax.set_ylabel('Material')
    ax.tick_params(axis='y', rotation=0, labelsize=8)
    plt.tight_layout()

    textstr = '\n'.join((
        f'Silhouette Score: {silhouette_avg:.4f}',
        f'Davies-Bouldin Score: {davies_bouldin_avg:.4f}',
        f'Calinski-Harabasz Score: {calinski_harabasz_avg:.4f}'
    ))

    plt.gca().text(
        0.95, 0.05, textstr, transform=plt.gca().transAxes,
        fontsize=12, verticalalignment='bottom',
        horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5)
    )

    if output_directory:
        full_path = os.path.join(output_directory, file_name)
        plt.savefig(full_path, bbox_inches='tight')
    return fig


warnings.simplefilter("always", Warning)
