# + tags=["parameters"]
upstream = ["process_hts_obj"]
product = None
# -

import pandas as pd
import os.path
import pickle
from matplotlib import pyplot as plt
from TOX5.calculations.tox5 import TOX5
from TOX5.misc.utils import plot_tox_rank_pie


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


path = upstream["process_hts_obj"]["data"]
pickle_hts_data = load_pickles_from_directory(path)
# print(pickle_hts_data.keys())
# ['8OHG_w', '8OHG_wo', 'CASP_w', 'CASP_wo', 'CTG_w', 'CTG_wo', 'DAPI_w', 'DAPI_wo', 'H2AX_w', 'H2AX_wo']

os.makedirs(product["data"], exist_ok=True)


def generate_tox5_scores(pickle_hts_data, keys, user_selected_transform_functions):
    df = pd.concat([pickle_hts_data[key].dose_response_df for key in keys], axis=1)
    df = df.reset_index().rename(columns={'index': 'material'})

    tox5 = TOX5(df, ['BEAS-2B'])
    tox5.add_weight(3, '1st_3SD')
    tox5.transform_data(user_selected_transform_functions)
    tox5.generate_auto_slices()
    tox5.calculate_tox5_scores()

    return tox5.tox5_scores


user_selected_transform_functions = {
    "1st": "log10x_6",
    "auc": "sqrt_x",
    "max": "log10x_6"
}

scores_w = generate_tox5_scores(pickle_hts_data, ['8OHG_w', 'CASP_w', 'CTG_w', 'DAPI_w', 'H2AX_w'],
                                user_selected_transform_functions)
scores_wo = generate_tox5_scores(pickle_hts_data, ['8OHG_wo', 'CASP_wo', 'CTG_wo', 'DAPI_wo', 'H2AX_wo'],
                                 user_selected_transform_functions)


# save scores in excel for comparing
file_name = os.path.join(product["data"], "calibrate_ranked.xlsx")
with pd.ExcelWriter(file_name) as writer:
    scores_w.to_excel(writer, sheet_name='with_serum')
    scores_wo.to_excel(writer, sheet_name='without_serum')

materials = ['Gemcitabine', 'Mitomycin C ', 'Non-porous Silica 300nm-Me',
             'Sodiumhexametaphosphate', 'TiO2', 'A1 Silver nanoparticles']
figure, legend = plot_tox_rank_pie(scores_w, materials)
## show all materials
# figure, legend = plot_tox_rank_pie(tox5.tox5_scores)

plt.show()
legend.show()
