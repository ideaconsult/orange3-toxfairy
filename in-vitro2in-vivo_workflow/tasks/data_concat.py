# + tags=["parameters"]
upstream = ["preprocessing"]
product = None
in_vivo_folder = None
in_vitro_cell = None
in_vitro_time = None
in_vivo_cell = None
in_vivo_time = None
missingvals = None
# -

import pandas as pd
import os.path
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

os.makedirs(product["data"], exist_ok=True)

# ///////////////////////////////////////// IN-VITRO /////////////////////////////////////////////////////////////////
in_vitro_df = pd.read_excel(upstream["preprocessing"]["x"])
# no explicit drop
# in_vitro_df = in_vitro_df.iloc[:-7]
in_vitro_df.columns


df_filtered_cells = in_vitro_df

# ///////////////////////////////////////// IN-VIVO /////////////////////////////////////////////////////////////////

in_vivo_df = pd.read_excel(in_vivo_folder)
columns_to_keep = ['ParticleID', 'Day', 'CellType', 'Doses', 'BMD_SD1', 'BMDL_SD1', 'BMDU_SD1', 'BMD_SD2',
                   'BMDL_SD2', 'BMDU_SD2']
filtered_df = in_vivo_df[columns_to_keep]

# IN VIVO CELLS: Neutrophil, Macrophage, Lymphocyte, Epithelial, Eosinophil
# IN VIVO TIME (DAY): 1, 28, 3, 90

# in_vivo_cell = "Neutrophil"
# in_vivo_time = 1
filtered_df2 = filtered_df[filtered_df['CellType'] == in_vivo_cell]
filtered_df3 = filtered_df2[filtered_df['Day'] == in_vivo_time]

filtered_df3.head()

# /////////////////////////////////////// combine by matched materials ///////////////////////////////////////////////
df_filtered_cells['material_lower'] = df_filtered_cells['material'].astype(str) 
df_filtered_cells['material_lower'] = df_filtered_cells['material_lower'].str.lower()
df_filtered_cells.shape

filtered_df3['material_lower'] = filtered_df3['ParticleID'].astype(str) 
filtered_df3['material_lower'] = filtered_df3['material_lower'].str.lower()
filtered_df3.shape


filtered = filtered_df3[filtered_df3['material_lower'].isin(df_filtered_cells['material_lower'])]

filtered.reset_index(drop=True)
dfinal = filtered.merge(df_filtered_cells, on="material_lower")
dfinal = dfinal.drop([
    # 'ParticleID',
    'Day', 'CellType', 'Doses'
    ], axis=1)

dfinal.head()

dfinal.columns

file_name = os.path.join(product["data"], "combined.csv")
dfinal.to_csv(file_name, index=False)

print('new data feature matrix')


def extract_col_info(col_name):
    parts = col_name.split("_")
    cell = parts[0]
    time = parts[1]
    assay = parts[-1]
    param = "_".join(parts[2:-1])
    return cell, time, param, assay

dfinal.columns

selected_cols = dfinal.columns[7:-16]
selected_cols

col_info = [extract_col_info(col) for col in selected_cols]
columns_df = pd.DataFrame(col_info, columns=["cell", "time", "param", "assay"], index=selected_cols)
melted_df = dfinal.melt(id_vars=["ParticleID"], value_vars=selected_cols, var_name="original_col", value_name="value")
melted_df = melted_df.merge(columns_df, left_on="original_col", right_index=True)
melted_df["value"] = pd.to_numeric(melted_df["value"], errors="coerce")
final_df = melted_df.pivot_table(index=["ParticleID", "cell", "time", "assay"],
                                 columns="param", values="value").reset_index()
final_df.columns.name = None
non_transformed_cols = [col for col in dfinal.columns if col not in selected_cols]
final_df = dfinal[non_transformed_cols].merge(final_df, on="ParticleID", how="left")
print(final_df)
final_df["time"] = final_df["time"].astype(str).str.replace("H", "", regex=False).astype(float)  # or .astype(int)

# x features encoding
columns_to_encode = ['cell', 'assay']

# encoder = OneHotEncoder(sparse_output=False, drop='first')  # remove first from each category to prevent multicollinearity
encoder = OneHotEncoder(sparse_output=False)

encoded_array = encoder.fit_transform(final_df[columns_to_encode])
encoded_df = pd.DataFrame(encoded_array, columns=encoder.get_feature_names_out(columns_to_encode))
final_df = pd.concat([final_df.drop(columns=columns_to_encode), encoded_df], axis=1)

# label_encoders = {}
# for col in columns_to_encode:
#     le = LabelEncoder()
#     final_df[col] = le.fit_transform(final_df[col])
#     label_encoders[col] = le

final_df

file_name2 = os.path.join(product["data"], "combined2.csv")
final_df.to_csv(file_name2, index=False)
