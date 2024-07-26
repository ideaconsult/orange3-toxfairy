# + tags=["parameters"]
upstream = ["process_hts_obj"]
product = None
config_file = None
config_key = None
# -

import pandas as pd
import os.path
import pickle
from matplotlib import pyplot as plt
import json
from TOX5.calculations.tox5 import TOX5
from TOX5.misc.utils import plot_tox_rank_pie, plot_tox_rank_pie_interactive, plot_ranked_material, \
    h_clustering
from TOX5.calculations.topsis_ranking import topsis_scoring


def load_pickles_from_directory(directory):
    pickle_hts_data = {}
    for filename in os.listdir(directory):
        if filename.endswith(".pkl"):
            key = filename.split('_')[0]
            key += "_" + filename.split('_')[2]
            key = key.split('.')[0]
            file_path = os.path.join(directory, filename)
            with open(file_path, 'rb') as f:
                pickle_hts_data[key] = pickle.load(f)
    return pickle_hts_data


def loadconfig(config_file, config_key, subkey="extract"):
    with open(config_file) as f:
        cfg = json.load(f)
    return cfg[config_key][subkey]


path = upstream["process_hts_obj"]["data"]
pickle_hts_data = load_pickles_from_directory(path)

# for combining data
# TODO: make combining data more generic

# pickle_hts_data_patrols = load_pickles_from_directory(
#     'D:\\PhD\\projects\\ToxPi\\orange-tox5\\io_datamodel\\products\\patrols\\processed_hts_obj')
# for key, obj in pickle_hts_data.items():
#     df_combined = pd.concat([obj.dose_response_df, pickle_hts_data_patrols[key].dose_response_df])
#     df_combined = df_combined.drop(['0.05% BSA water, 30ul EtOH', 'water'])
#     obj.dose_response_df = df_combined

without_serum = []
with_serum = []
for key in pickle_hts_data.keys():
    if key.endswith('wo'):
        without_serum.append(key)
    else:
        with_serum.append(key)
# print(pickle_hts_data.keys())
# ['8OHG_w', '8OHG_wo', 'CASP_w', 'CASP_wo', 'CTG_w', 'CTG_wo', 'DAPI_w', 'DAPI_wo', 'H2AX_w', 'H2AX_wo']

os.makedirs(product["data"], exist_ok=True)

extract_config = loadconfig(config_file, config_key, "scoring")
extract_config_plot = loadconfig(config_file, config_key, "plotting")
print(tuple(extract_config["add_weight"]))


def generate_tox5_scores(pickle_hts_data, keys, cells: [], transform_functions: dict,
                         weight=(3, '1st_3SD'), auto_slices='by_time_endpoint',
                         manual_slices=False, manual_names=False,
                         bootstrap_cis=True
                         ):
    df = pd.concat([pickle_hts_data[key].dose_response_df for key in keys], axis=1)
    df = df.reset_index().rename(columns={'index': 'material'})

    tox5 = TOX5(df, cells)
    if weight:
        tox5.add_weight(weight[0], weight[1])
    tox5.transform_data(transform_functions)
    if not manual_names and not manual_slices:
        tox5.generate_auto_slices(slicing_pattern=auto_slices)
        tox5.calculate_tox5_scores()
    else:
        tox5.manual_slices = manual_slices
        tox5.manual_names = manual_names
        tox5.calculate_tox5_scores(manual_slicing=True)

    if bootstrap_cis:
        tox5.calc_ci_slices()
        tox5.calc_ci()

    return tox5


def rank_with_topsis(pickle_hts_data, keys):
    df = pd.concat([pickle_hts_data[key].dose_response_df for key in keys], axis=1)
    df = df.reset_index().rename(columns={'index': 'material'})
    sorted_df = topsis_scoring(df)
    return sorted_df


cells = extract_config['cells']
user_selected_transform_functions = extract_config['transform_functions']
bootstrap_ci = extract_config['bootstrap_CIs']

# extract parameters for pies plot
materials = extract_config_plot['pies']['materials']
colored_param = extract_config_plot['pies']['colored_param']
ci_color_low = extract_config_plot['pies']['ci_low_color']
ci_color_up = extract_config_plot['pies']['ci_high_color']

# extract parameters for ranks plot
negative_controls = extract_config_plot['ranks']['negative_controls']
positive_controls = extract_config_plot['ranks']['positive_controls']
substance_types = extract_config_plot['ranks']['substance_types']

if with_serum:
    # Calculate tox5 scores with confidence intervals
    tox5_w = generate_tox5_scores(pickle_hts_data, with_serum, cells=cells,
                                  transform_functions=user_selected_transform_functions)
    file_name = os.path.join(product["data"], "ranked_w.xlsx")

    # Save results in excel
    with pd.ExcelWriter(file_name) as writer:
        tox5_w.tox5_scores.to_excel(writer, sheet_name='scores')
        tox5_w.results_ci_df.to_excel(writer, sheet_name='scores_cis')

    # plot ranked materials as a scatter plot
    fig_ranks = plot_ranked_material(tox5_w.results_ci_df, 'toxpi_score', 'rnk', 'Material',
                                     x_ci_dict=('score_ci_high', 'score_ci_low'),
                                     y_ci_dict=('rank_ci_high', 'rank_ci_low'),
                                     negative_controls=negative_controls,
                                     positive_controls=positive_controls,
                                     substance_types=substance_types,
                                     marker_resize=20,
                                     output_directory=product["data"], file_name='ranked_w')

    fig_ranks_ci = plot_ranked_material(tox5_w.results_ci_df, 'rnk', 'Material', 'Material',
                                        x_ci_dict=('rank_ci_high', 'rank_ci_low'),
                                        negative_controls=negative_controls,
                                        positive_controls=positive_controls,
                                        substance_types=substance_types,
                                        marker_resize=20,
                                        output_directory=product["data"], file_name='ranked_w_rank_ci')

    fig_scores_ci = plot_ranked_material(tox5_w.results_ci_df, 'toxpi_score', 'Material', 'Material',
                                         x_ci_dict=('score_ci_high', 'score_ci_low'),
                                         negative_controls=negative_controls,
                                         positive_controls=positive_controls,
                                         substance_types=substance_types,
                                         marker_resize=20,
                                         output_directory=product["data"], file_name='ranked_w_score_ci')

    # plot interactive pies
    fig = plot_tox_rank_pie_interactive(tox5_w.tox5_scores, colored_param=colored_param,
                                        conf_intervals=tox5_w.ci_slices,
                                        output_directory=product["data"], materials=materials,
                                        file_name='tox_pie_w_interactive')

    # hierarchial clustering
    features = tox5_w.tox5_scores.iloc[:, 3:].values
    labels = tox5_w.tox5_scores['Material'] + ' rank:' + tox5_w.tox5_scores['rnk'].astype(str)
    labels = labels.values
    dendogram = h_clustering(features, labels, output_directory=product["data"], file_name='dendograme_w')
    dendogram2 = h_clustering(features, labels, clusters='silhouette', output_directory=product["data"],
                              file_name='dendograme_w_silhouette')

    # figure, legend = plot_tox_rank_pie(scores_w, conf_intervals=ci_slices, colored_param=colored_param,
    #                                    materials=materials, ci_low_color=ci_color_low, ci_high_color=ci_color_up)
    # figure_file_name_pdf = os.path.join(product["data"], "tox_rank_pie_w.pdf")
    # figure.savefig(figure_file_name_pdf, format='pdf', bbox_inches='tight')
    # legend_file_name_pdf = os.path.join(product["data"], "tox_rank_pie_legend_w.pdf")
    # legend.savefig(legend_file_name_pdf, format='pdf', bbox_inches='tight')
    # plt.show()
    # legend.show()

if without_serum:
    # Calculate tox5 scores with confidence intervals
    tox5_wo = generate_tox5_scores(pickle_hts_data, without_serum, cells=cells,
                                   transform_functions=user_selected_transform_functions)
    file_name = os.path.join(product["data"], "ranked_wo.xlsx")
    # Save results in excel
    with pd.ExcelWriter(file_name) as writer:
        tox5_wo.tox5_scores.to_excel(writer, sheet_name='scores')
        tox5_wo.results_ci_df.to_excel(writer, sheet_name='scores_cis')

    # =========================  Topsis model: test for quantum dots and patrols controls ==============================
    sorted_df = rank_with_topsis(pickle_hts_data, without_serum)
    file_name_topsis = os.path.join(product["data"], "ranked_topsis.xlsx")
    with pd.ExcelWriter(file_name_topsis) as writer:
        sorted_df.to_excel(writer)

    fig_topsis = plot_ranked_material(sorted_df, 'Preference', 'Ranking', 'Material',
                                      # controls for calibrate
                                      negative_controls=['water'],
                                      positive_controls=['Gemcitabine', 'Mitomycin C ', '5-Fluorouracil',
                                                         '4-Nitroquinoline 1-oxide', 'Daunorubicin '],
                                      # controls for quntum dots
                                      # negative_controls=['NM-220', 'JRCNM50001a', 'NM-105'],
                                      # positive_controls=['NM-110', 'JRCNM01005a'],
                                      marker_resize=20, output_directory=product["data"], file_name='topsis_ranked_wo')
    # ==================================================================================================================

    # plot ranked materials as a scatter plot
    fig_ranks = plot_ranked_material(tox5_wo.results_ci_df, 'toxpi_score', 'rnk', 'Material',
                                     negative_controls=negative_controls,
                                     positive_controls=positive_controls,
                                     substance_types=substance_types,
                                     x_ci_dict=('score_ci_high', 'score_ci_low'),
                                     y_ci_dict=('rank_ci_high', 'rank_ci_low'),
                                     marker_resize=20, output_directory=product["data"], file_name='ranked_wo')

    fig_ranks_ci = plot_ranked_material(tox5_wo.results_ci_df, 'rnk', 'Material', 'Material',
                                        negative_controls=negative_controls,
                                        positive_controls=positive_controls,
                                        substance_types=substance_types,
                                        x_ci_dict=('rank_ci_high', 'rank_ci_low'),
                                        marker_resize=20, output_directory=product["data"],
                                        file_name='ranked_wo_rank_ci')

    fig_scores_ci = plot_ranked_material(tox5_wo.results_ci_df, 'toxpi_score', 'Material', 'Material',
                                         negative_controls=negative_controls,
                                         positive_controls=positive_controls,
                                         substance_types=substance_types,
                                         x_ci_dict=('score_ci_high', 'score_ci_low'),
                                         marker_resize=20, output_directory=product["data"],
                                         file_name='ranked_wo_score_ci')

    # plot interactive pies
    fig = plot_tox_rank_pie_interactive(tox5_wo.tox5_scores, colored_param=colored_param,
                                        conf_intervals=tox5_wo.ci_slices,
                                        output_directory=product["data"], materials=materials,
                                        file_name="tox_pie_wo_interactive")

    # hierarchial clustering
    features = tox5_wo.tox5_scores.iloc[:, 3:].values
    labels = tox5_wo.tox5_scores['Material'] + ' rank:' + tox5_wo.tox5_scores['rnk'].astype(str)
    labels = labels.values
    dendogram = h_clustering(features, labels, output_directory=product["data"], file_name='dendograme_wo')
    dendogram2 = h_clustering(features, labels, clusters='silhouette', output_directory=product["data"],
                              file_name='dendograme_wo_silhouette')

    # figure, legend = plot_tox_rank_pie(scores_wo, conf_intervals=ci_slices, colored_param=colored_param,
    #                                    materials=materials, ci_low_color=ci_color_low, ci_high_color=ci_color_up)
    # figure_file_name_pdf = os.path.join(product["data"], "tox_rank_pie_wo.pdf")
    # figure.savefig(figure_file_name_pdf, format='pdf', bbox_inches='tight')
    # legend_file_name_pdf = os.path.join(product["data"], "tox_rank_pie_legend_wo.pdf")
    # legend.savefig(legend_file_name_pdf, format='pdf', bbox_inches='tight')
    # plt.show()
    # legend.show()
