# + tags=["parameters"]
upstream = ["process_hts_obj"]
product = None
config_file = None
config_key = None
combine_data_with = None
combine_w_wo_serum = None
# -

import pandas as pd
import os.path
from pathlib import Path
import pickle
import json
from TOX5.calculations.tox5 import TOX5
from TOX5.misc.utils import plot_tox_rank_pie, plot_tox_rank_pie_interactive, plot_ranked_material, \
    h_clustering
from TOX5.calculations.topsis_ranking import topsis_scoring
from TOX5.misc.pvclust import PvClust


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


def generate_tox5_scores(hts_data, cells: [], transform_functions: dict, keys=None,
                         weight=(3, '1st_3SD'), auto_slices='by_time_endpoint',
                         manual_slices=False, manual_names=False,
                         bootstrap_cis=True
                         ):
    df = pd.DataFrame()
    if isinstance(hts_data, dict):
        df = pd.concat([hts_data[key].dose_response_df for key in keys], axis=1)
        df = df.reset_index().rename(columns={'index': 'material'})
    elif isinstance(hts_data, pd.DataFrame):
        df = hts_data

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


def rank_with_topsis(hts_data, keys):
    df = pd.concat([hts_data[key].dose_response_df for key in keys], axis=1)
    df = df.reset_index().rename(columns={'index': 'material'})
    sorted_df = topsis_scoring(df)
    return sorted_df


path = upstream["process_hts_obj"]["data"]
pickle_hts_data = load_pickles_from_directory(path)
os.makedirs(product["data"], exist_ok=True)

if combine_data_with:
    path2 = Path(path)
    two_dirs_up = path2.parents[1]
    new_path = two_dirs_up / combine_data_with / 'processed_hts_obj'
    pickle_hts_data_2 = load_pickles_from_directory(new_path)

    for key, obj in pickle_hts_data.items():
        df_combined = pd.concat([obj.dose_response_df, pickle_hts_data_2[key].dose_response_df])
        df_combined = df_combined.drop(['water'])
        obj.dose_response_df = df_combined

without_serum = []  # the basis
with_serum = []
for key in pickle_hts_data.keys():
    if key.endswith('wo'):
        without_serum.append(key)
    else:
        with_serum.append(key)

# ----------------------------------------------- Extract cofigurable parameters ---------------------------------------
extract_config = loadconfig(config_file, config_key, "scoring")
extract_config_plot = loadconfig(config_file, config_key, "plotting")

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

tox5_obj_file_names = {}
# for special task: combine calibrate +/- serum
if combine_w_wo_serum:
    df = pd.concat([pickle_hts_data[key].dose_response_df for key in without_serum], axis=1)
    df = df.reset_index().rename(columns={'index': 'material'})
    df_w = pd.concat([pickle_hts_data[key].dose_response_df for key in with_serum], axis=1)
    df_w = df_w.reset_index().rename(columns={'index': 'material'})
    df_w.columns = [col.replace('MAX', 'MAX_w')
                        .replace('AUC', 'AUC_w')
                        .replace('2SD', '2SD_w')
                        .replace('3SD', '3SD_w')
                    for col in df_w.columns]
    combined_df = pd.concat([df, df_w], axis=1)
    tox5 = generate_tox5_scores(combined_df, cells=cells, transform_functions=user_selected_transform_functions,
                                bootstrap_cis=bootstrap_ci)
    tox5_obj_file_names["tox5"] = [tox5, 'ranked.xlsx', 'ranked', 'ranked_rank_ci', 'ranked_score_ci',
                                   'tox_pie_interactive', 'dendograme', 'PV_clust']
else:
    if with_serum:
        tox5_w = generate_tox5_scores(pickle_hts_data, keys=with_serum, cells=cells,
                                      transform_functions=user_selected_transform_functions)
        tox5_obj_file_names["tox5_w"] = [tox5_w, 'ranked_w.xlsx', 'ranked_w', 'ranked_rank_ci_w', 'ranked_score_ci_w',
                                         'tox_pie_interactive_w', 'dendograme_w', 'PV_clust_w']
    if without_serum:
        tox5_wo = generate_tox5_scores(pickle_hts_data, keys=without_serum, cells=cells,
                                       transform_functions=user_selected_transform_functions)
        tox5_obj_file_names["tox5_wo"] = [tox5_wo, 'ranked_wo.xlsx', 'ranked_wo', 'ranked_rank_ci_wo',
                                          'ranked_score_ci_wo',
                                          'tox_pie_interactive_wo', 'dendograme_wo', 'PV_clust_wo']

for key, value in tox5_obj_file_names.items():
    tox5 = value[0]

    file_name = os.path.join(product["data"], value[1])
    with pd.ExcelWriter(file_name) as writer:
        tox5.tox5_scores.to_excel(writer, sheet_name='scores')
        tox5.results_ci_df.to_excel(writer, sheet_name='scores_cis')

    # plot ranked materials as a scatter plot
    fig_ranks = plot_ranked_material(tox5.results_ci_df, 'toxpi_score', 'rnk', 'Material',
                                     negative_controls=negative_controls,
                                     positive_controls=positive_controls,
                                     substance_types=substance_types,
                                     x_ci_dict=('score_ci_high', 'score_ci_low'),
                                     y_ci_dict=('rank_ci_high', 'rank_ci_low'),
                                     marker_resize=20, output_directory=product["data"], file_name=value[2])

    fig_ranks_ci = plot_ranked_material(tox5.results_ci_df, 'rnk', 'Material', 'Material',
                                        negative_controls=negative_controls,
                                        positive_controls=positive_controls,
                                        substance_types=substance_types,
                                        x_ci_dict=('rank_ci_high', 'rank_ci_low'),
                                        marker_resize=20, output_directory=product["data"],
                                        file_name=value[3])

    fig_scores_ci = plot_ranked_material(tox5.results_ci_df, 'toxpi_score', 'Material', 'Material',
                                         negative_controls=negative_controls,
                                         positive_controls=positive_controls,
                                         substance_types=substance_types,
                                         x_ci_dict=('score_ci_high', 'score_ci_low'),
                                         marker_resize=20, output_directory=product["data"],
                                         file_name=value[4])

    # plot interactive pies
    fig = plot_tox_rank_pie_interactive(tox5.tox5_scores, colored_param=colored_param,
                                        conf_intervals=tox5.ci_slices,
                                        output_directory=product["data"], materials=materials,
                                        file_name=value[5])

    # hierarchial clustering
    features = tox5.tox5_scores.iloc[:, 3:].values
    labels = tox5.tox5_scores['Material'] + ' rank:' + tox5.tox5_scores['rnk'].astype(str)
    labels = labels.values
    dendograme = h_clustering(features, labels, output_directory=product["data"],
                              file_name=value[6])

    # PV clust
    features = tox5.tox5_scores.iloc[:, 4:].values
    X = pd.DataFrame(features.T)
    pv = PvClust(X, method="ward", metric="euclidean", nboot=1000)
    pv.plot(labels=tox5.tox5_scores['Material'].values, output_directory=product["data"], file_name=value[7])



# =========================  Topsis model: test for quantum dots and patrols controls ==============================
#     sorted_df = rank_with_topsis(pickle_hts_data, without_serum)
#     file_name_topsis = os.path.join(product["data"], "ranked_topsis.xlsx")
#     with pd.ExcelWriter(file_name_topsis) as writer:
#         sorted_df.to_excel(writer)
#
#     fig_topsis = plot_ranked_material(sorted_df, 'Preference', 'Ranking', 'Material',
#                                       # controls for calibrate
#                                       negative_controls=['water'],
#                                       positive_controls=['Gemcitabine', 'Mitomycin C ', '5-Fluorouracil',
#                                                          '4-Nitroquinoline 1-oxide', 'Daunorubicin '],
#                                       # controls for quntum dots
#                                       # negative_controls=['NM-220', 'JRCNM50001a', 'NM-105'],
#                                       # positive_controls=['NM-110', 'JRCNM01005a'],
#                                       marker_resize=20, output_directory=product["data"], file_name='topsis_ranked_wo')
# ==================================================================================================================
