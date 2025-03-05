# + tags=["parameters"]
upstream = []
product = None
in_vivo_folder = None
in_vitro_folder = None
in_vitro_cell = None
in_vitro_time = None
in_vivo_cell = None
in_vivo_time = None
# -

import pandas as pd
import os.path

os.makedirs(product["data"], exist_ok=True)

# ///////////////////////////////////////// IN-VITRO /////////////////////////////////////////////////////////////////
in_vitro_df = pd.read_excel(in_vitro_folder)
in_vitro_df = in_vitro_df.drop(in_vitro_df.columns[0], axis=1)
in_vitro_df = in_vitro_df.iloc[:-7]
# IN VITRO CELLS: A549, BEAS-2B, HEPG2, THP-1
# IN VITRO TIME: 6H, 24H, 72H

# in_vitro_cell = "A549"
# in_vitro_time = "24H"
df_filtered_cells = pd.DataFrame()
if in_vitro_time and in_vitro_cell:
    cols_to_keep = in_vitro_df.columns[1:-20][
        in_vitro_df.columns[1:-20].str.contains(in_vitro_cell, na=False) &
        in_vitro_df.columns[1:-20].str.contains(in_vitro_time, na=False)
        ]
    df_filtered_cells = in_vitro_df[[in_vitro_df.columns[0]] + cols_to_keep.tolist() + list(in_vitro_df.columns[-20:])]
else:
    df_filtered_cells = in_vitro_df

print(df_filtered_cells.columns)

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

print(filtered_df3)

# /////////////////////////////////////// combine by matched materials ///////////////////////////////////////////////
df_filtered_cells['material_lower'] = df_filtered_cells['material'].str.lower()
filtered_df3['material_lower'] = filtered_df3['ParticleID'].str.lower()

filtered = filtered_df3[filtered_df3['material_lower'].isin(df_filtered_cells['material_lower'])]

filtered.reset_index(drop=True)
dfinal = filtered.merge(df_filtered_cells, on="material_lower")
dfinal = dfinal.drop([
    # 'ParticleID',
    'Day', 'CellType', 'Doses', 'material_lower', 'material',
    'Chemical_composition', 'Morphology', 'Crystalline_phase',
    'Substance_group'], axis=1)

print(dfinal)
print(dfinal.columns)

file_name = os.path.join(product["data"], "combined.csv")
dfinal.to_csv(file_name, index=False)
