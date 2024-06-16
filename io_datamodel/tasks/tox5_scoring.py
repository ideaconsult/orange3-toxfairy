# + tags=["parameters"]
from TOX5.calculations.topsis_ranking import topsis_scoring

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
from TOX5.misc.utils import plot_tox_rank_pie, plot_tox_rank_pie_interactive, plot_topsis


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
pickle_hts_data_patrols = load_pickles_from_directory(
    'D:\\PhD\\projects\\ToxPi\\orange-tox5\\io_datamodel\\products\\patrols\\processed_hts_obj')
for key, obj in pickle_hts_data.items():
    df_combined = pd.concat([obj.dose_response_df, pickle_hts_data_patrols[key].dose_response_df])
    df_combined = df_combined.drop(['0.05% BSA water, 30ul EtOH', 'water'])
    obj.dose_response_df = df_combined

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
        tox5.calc_ci_scores()

    return tox5.tox5_scores, tox5.ci_slices, tox5.ci_scores, tox5.ci_scores_df


def rank_with_topsis(pickle_hts_data, keys):
    df = pd.concat([pickle_hts_data[key].dose_response_df for key in keys], axis=1)
    df = df.reset_index().rename(columns={'index': 'material'})
    sorted_df = topsis_scoring(df)
    return sorted_df



cells = extract_config['cells']
user_selected_transform_functions = extract_config['transform_functions']
bootstrap_ci = extract_config['bootstrap_CIs']
materials = extract_config_plot['materials']
colored_param = extract_config_plot['colored_param']
ci_color_low = extract_config_plot['ci_low_color']
ci_color_up = extract_config_plot['ci_high_color']

if with_serum:
    scores_w, ci_slices, _, df_ci = generate_tox5_scores(pickle_hts_data, with_serum, cells=cells,
                                                         transform_functions=user_selected_transform_functions)
    file_name = os.path.join(product["data"], "ranked_w.xlsx")
    with pd.ExcelWriter(file_name) as writer:
        scores_w.to_excel(writer, sheet_name='scores')
        df_ci.to_excel(writer, sheet_name='scores_cis')

    figure, legend = plot_tox_rank_pie(scores_w, conf_intervals=ci_slices, colored_param=colored_param,
                                       materials=materials, ci_low_color=ci_color_low, ci_high_color=ci_color_up)
    figure_file_name_pdf = os.path.join(product["data"], "tox_rank_pie_w.pdf")
    figure.savefig(figure_file_name_pdf, format='pdf', bbox_inches='tight')
    legend_file_name_pdf = os.path.join(product["data"], "tox_rank_pie_legend_w.pdf")
    legend.savefig(legend_file_name_pdf, format='pdf', bbox_inches='tight')

    plt.show()
    legend.show()

if without_serum:
    scores_wo, ci_slices, _, df_ci = generate_tox5_scores(pickle_hts_data, without_serum, cells=cells,
                                                          transform_functions=user_selected_transform_functions)
    file_name = os.path.join(product["data"], "ranked_wo.xlsx")
    with pd.ExcelWriter(file_name) as writer:
        scores_wo.to_excel(writer, sheet_name='scores')
        df_ci.to_excel(writer, sheet_name='scores_cis')

    # test with topsis
    sorted_df = rank_with_topsis(pickle_hts_data, without_serum)
    file_name_topsis = os.path.join(product["data"], "ranked_topsis.xlsx")
    with pd.ExcelWriter(file_name_topsis) as writer:
        sorted_df.to_excel(writer)

    # plot topsis
    fig_topsis = plot_topsis(sorted_df, marker_resize=7, output_directory=product["data"])


    figure, legend = plot_tox_rank_pie(scores_wo, conf_intervals=ci_slices, colored_param=colored_param,
                                       materials=materials, ci_low_color=ci_color_low, ci_high_color=ci_color_up)

    fig = plot_tox_rank_pie_interactive(scores_wo, colored_param=colored_param, conf_intervals=ci_slices,
                                        output_directory=product["data"], materials=materials)

    figure_file_name_pdf = os.path.join(product["data"], "tox_rank_pie_wo.pdf")
    figure.savefig(figure_file_name_pdf, format='pdf', bbox_inches='tight')
    legend_file_name_pdf = os.path.join(product["data"], "tox_rank_pie_legend_wo.pdf")
    legend.savefig(legend_file_name_pdf, format='pdf', bbox_inches='tight')

    plt.show()
    legend.show()
