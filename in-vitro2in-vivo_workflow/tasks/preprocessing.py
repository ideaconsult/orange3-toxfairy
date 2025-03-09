import pandas as pd
from pathlib import Path
from sklearn.impute import KNNImputer
from summarytools import dfSummary
from tasks.utils import (
    get_material_id, get_scaler, drop_columns_by_missing_percentage)


# + tags=["parameters"]
upstream = []
product = None
missingvals = None
n_neighbors = None
scaler_type_x = None
scaler_type_y = None
threshold = None
in_vitro_folder = None
in_vivo_folder = None
in_vivo_sheet = None
# -


def fix(df, column="material"):
    _fix = {
        "jrcnm04001a" : "nm-401",
        "jrcnm04003a" : "nm-403",
        "ncrwe-026": "nrcwe-026",
        "mitsui-7" : "nrcwe-006",
        "1, NM401" : "nm-401",
        "1, nm401" : "nm-401",
        "10, nrcwe-051" : "nrcwe-051"
    }
    for f in _fix:
        df.loc[df[column] == f, column] = _fix[f]
    return df


def extract_col_info(col_name):
    parts = col_name.split("_")
    cell = parts[0]
    time = parts[1]
    assay = parts[-1]
    param = "_".join(parts[2:-1])
    return cell, time, param, assay


def preprocess(df, scaler_type="standard"):

    # Calculate the percentage of missing values per column
    missing_percentage = df.isnull().mean()
    cols_to_drop = missing_percentage[missing_percentage > threshold].index
    df = drop_columns_by_missing_percentage(df, threshold)

    ids = df[get_material_id()]
    scaler = get_scaler(scaler_type)
    if missingvals == "impute":
        # Step 2: Apply KNN Imputer
        df_no_id = df.drop(columns=[get_material_id()])
        df_no_id = pd.DataFrame(scaler.fit_transform(df_no_id), 
                                columns=df_no_id.columns)
        knn_imputer = KNNImputer(n_neighbors=n_neighbors)
        df_processed = pd.DataFrame(
            knn_imputer.fit_transform(df_no_id.values),
            columns=df_no_id.columns
        )
        df_processed.insert(0, get_material_id(), ids)
    else:
        df = df.dropna(how='all')
        df_no_id = df.drop(columns=[get_material_id()])
        df_processed = pd.DataFrame(scaler.fit_transform(df_no_id), 
                                    columns=df_no_id.columns)
        df_processed.insert(0, get_material_id(), ids)
    return df_processed


Path(product["x"]).parent.mkdir(parents=True, exist_ok=True)

dfx = pd.read_excel(in_vitro_folder, index_col=None)
dfx = dfx.drop(["Unnamed: 0",'Chemical_composition', 'Morphology',
              'Crystalline_phase','Substance_group'], axis=1)
dfx.columns

dfx = preprocess(dfx, scaler_type=scaler_type_x)
dfx['material'] = dfx['material'].astype(str) 
dfx['material'] = dfx['material'].str.lower()

dfx.columns

dfx = fix(dfx)
dfSummary(dfx, is_collapsible=True)

dfx.to_excel(product["x"], index=False)
# onehot

# 4 dashes
selected_cols = [col for col in dfx.columns if col.count('_') >= 3]
selected_cols

col_info = [extract_col_info(col) for col in selected_cols]
columns_df = pd.DataFrame(col_info, columns=["cell", "time", "param", "assay"], index=selected_cols)
melted_df = dfx.melt(id_vars=["material"], value_vars=selected_cols, var_name="original_col", value_name="value")
melted_df = melted_df.merge(columns_df, left_on="original_col", right_index=True)
melted_df["value"] = pd.to_numeric(melted_df["value"], errors="coerce")
final_df = melted_df.pivot_table(index=["material", "cell", "time", "assay"],
                                 columns="param", values="value").reset_index()
final_df.head()

#final_df.columns.name = None
non_transformed_cols = [col for col in dfx.columns if col not in selected_cols]
non_transformed_cols

final_df = dfx[non_transformed_cols].merge(final_df[['material','cell', 'assay','time']], on="material", how="left")
final_df["time"] = final_df["time"].astype(str).str.replace("H", "", regex=False).astype(float)  # or .astype(int)

final_df.to_excel(product["x_long"], index=False)
# x features encoding
columns_to_encode = ['cell', 'assay']

# encoder = OneHotEncoder(sparse_output=False, drop='first')  # remove first from each category to prevent multicollinearity
#encoder = OneHotEncoder(sparse_output=False)

#encoded_array = encoder.fit_transform(final_df[columns_to_encode])
#encoded_df = pd.DataFrame(encoded_array, columns=encoder.get_feature_names_out(columns_to_encode))
#final_df = pd.concat([final_df.drop(columns=columns_to_encode), encoded_df], axis=1)




# in-vivo
dfy = pd.read_excel(in_vivo_folder, sheet_name=in_vivo_sheet, index_col=None)
dfy.columns

dfy['material'] = dfy['ParticleID'].astype(str) 
dfy['material'] = dfy['material'].str.lower()

columns_to_keep = ['material', 'Day', 'CellType', 'BMD_SD1',
                   'BMDL_SD1', 'BMDU_SD1']
dfy = dfy[columns_to_keep]
dfx = fix(dfx)
dfSummary(dfy, is_collapsible=True)

dfy.to_excel(product["y"], index=False)


df_merged = pd.merge(final_df, dfy, on="material", how="outer")
df_merged = df_merged.dropna(subset=['BMD_SD1'])
df_merged.to_excel(product["xy"], index=False)


