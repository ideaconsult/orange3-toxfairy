import pandas as pd
from pathlib import Path
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from summarytools import dfSummary
from tasks.utils import (
    get_material_id, get_scaler, drop_columns_by_missing_percentage)
from IPython.display import display, HTML


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


# Custom transformer to inverse the scaling after imputation
class InverseScaler(BaseEstimator, TransformerMixin):
    def __init__(self, scaler):
        self.scaler = scaler

    def fit(self, X, y=None):
        return self  # No fitting needed for inverse transform

    def transform(self, X):
        return self.scaler.inverse_transform(X)


def preprocess_lag(df):
    # Pivot the data to have time-series format for autoregression
    df_pivot = df.pivot_table(index=["material", "cell", "assay"], columns="time", values=["1st_2SD", "1st_3SD", "AUC", "MAX"])

    # Flatten MultiIndex column names
    df_pivot.columns = [f"{col[0]}_t{col[1]}" for col in df_pivot.columns]

    # Reset index for better manipulation
    df_pivot = df_pivot.reset_index()

    # Create lag features for autoregressive modeling
    timepoints = sorted(df["time"].unique())

    for time in timepoints:
        for metric in ["1st_2SD", "1st_3SD", "AUC", "MAX"]:
            col_name = f"{metric}_t{time}"
            if col_name in df_pivot.columns:
                df_pivot[f"{metric}_lag_t{time}"] = df_pivot[col_name].shift(1)  # 1-step lag

    # Fill missing values (can be forward fill, mean, or zero-fill)
    df_pivot.fillna(0, inplace=True)  # Modify based on need
    return df_pivot


def preprocess(df, scaler_type="standard", missingvals = None):

    # Calculate the percentage of missing values per column
    missing_percentage = df.isnull().mean()
    cols_to_drop = missing_percentage[missing_percentage > threshold].index
    df = drop_columns_by_missing_percentage(df, threshold)

    ids = df[get_material_id()]
    scaler = get_scaler(scaler_type)
    if missingvals == "impute":
        # Define the pipeline with scaling first, then imputation
        #scaler = StandardScaler()
        preprocessor = Pipeline([
            ("scaler", scaler),  # First scale the data
            ("imputer", KNNImputer(n_neighbors=5)),  # Then impute missing values
            ("inverse_scaler", InverseScaler(scaler))  # Apply inverse scaling to the imputed data
        ])
              
        # Step 2: Apply KNN Imputer
        df_no_id = df.drop(columns=[get_material_id()])
        df_processed = pd.DataFrame(
            preprocessor.fit_transform(df_no_id.values),
            columns=df_no_id.columns
        )
        df_processed.insert(0, get_material_id(), ids)
    elif missingvals == "drop":
        df = df.dropna(how='all')
        df_no_id = df.drop(columns=[get_material_id()])
        df_processed = pd.DataFrame(scaler.fit_transform(df_no_id), 
                                    columns=df_no_id.columns)
        df_processed.insert(0, get_material_id(), ids)
    else:
        df_processed = df
    return df_processed


Path(product["x"]).parent.mkdir(parents=True, exist_ok=True)

dfx = pd.read_excel(in_vitro_folder, index_col=None)
dfx = dfx.drop(["Unnamed: 0",'Chemical_composition', 'Morphology',
              'Crystalline_phase','Substance_group'], axis=1)
dfx.columns

dfx.describe()

dfx = preprocess(dfx, scaler_type=scaler_type_x, missingvals=missingvals)


dfx['material'] = dfx['material'].astype(str) 
dfx['material'] = dfx['material'].str.lower()

dfx.describe()


dfx = fix(dfx)
dfSummary(dfx, is_collapsible=True)

dfx.to_excel(product["x"], index=False)

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

cols = ['material','cell', 'assay','time','1st_2SD','1st_3SD','AUC','MAX']
# cols = ['material','cell', 'assay','time','AUC']

final_df = dfx[non_transformed_cols].merge(final_df[cols], on="material", how="left")
final_df["time"] = final_df["time"].astype(str).str.replace("H", "", regex=False).astype(float)  # or .astype(int)

final_df.to_excel(product["x_long"], index=False)


df_lag = preprocess_lag(final_df)
df_lag.to_excel(product["x_lag"], index=False)

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

df_merged = pd.merge(dfx, dfy, on="material", how="outer")
df_merged = df_merged.dropna(subset=['BMD_SD1'])
if missingvals != "keep":
    df_merged.dropna(how="any").to_excel(product["xy_wide"], index=False)
dfSummary(df_merged, is_collapsible=True)

df_merged = pd.merge(df_lag, dfy, on="material", how="outer")
df_merged = df_merged.dropna(subset=['BMD_SD1'])
df_merged.to_excel(product["xlag_y"], index=False)

