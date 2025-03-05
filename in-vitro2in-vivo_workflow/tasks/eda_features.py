# + tags=["parameters"]
upstream = ["data_concat"]
product = None
nan_treatement = None
power_transform = None
standardized = None
pca_variance_threshold = None
umap_n_components = None
# -

import pandas as pd
import numpy as np
import os.path
import umap
from sklearn.preprocessing import PowerTransformer, StandardScaler
from sklearn.decomposition import PCA
from summarytools import dfSummary
import missingno as msno


path = upstream["data_concat"]["data"]
df = pd.read_csv(os.path.join(path, "combined.csv"))
os.makedirs(product["data"], exist_ok=True)


# dfSummary(df, is_collapsible=True)

def custom_imputation_nan(df):
    df_copy = df.copy()
    columns_with_nan = df_copy.columns[df_copy.isna().any()].tolist()
    if columns_with_nan:
        # Logic to fill NaN values:
        # FSC NaN values will be fill with 9999 based on idea that high value mean low toxic effect
        # AUC NAN values will be fill with 0 based on idea that low value mean low overall effect
        columns_to_process = df_copy.columns[df_copy.columns.str.contains('1st') | df_copy.columns.str.contains('AUC')]
        df_copy[columns_to_process] = df_copy[columns_to_process].fillna(
            {col: 999 if '1st' in col else 0 for col in columns_to_process})

    df_copy = df_copy.dropna(axis=1)
    return df_copy


def handle_nan(df, method='drop_row'):
    df_copy = df.copy()

    if method == 'drop_row':
        return df_copy.dropna(axis=0)

    elif method == 'drop_col':
        return df_copy.dropna(axis=1)

    elif method in ['impute_mean', 'impute_median', 'impute_mode']:

        for col in df_copy.columns:
            if df_copy[col].isnull().any():
                if method == 'impute_mean':
                    df_copy[col].fillna(df_copy[col].mean(), inplace=True)
                elif method == 'impute_median':
                    df_copy[col].fillna(df_copy[col].median(), inplace=True)
                elif method == 'impute_mode':
                    mode_value = df_copy[col].mode().iloc[0] if not df_copy[col].mode().empty else np.nan
                    df_copy[col].fillna(mode_value, inplace=True)
        return df_copy

    else:
        raise ValueError("Invalid method. Use 'drop_row', 'drop_col', 'impute_mean', 'impute_median' or 'impute_mode'.")


def transform(df, method='yeo-johnson'):
    pt = PowerTransformer(method)
    df_power = pt.fit_transform(df)
    df_power_transformed = pd.DataFrame(df_power, columns=df.columns)

    return df_power_transformed


def standardize(df):
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df)
    df_standardized = pd.DataFrame(df_scaled, columns=df.columns)

    return df_standardized


def apply_pca_function(df, variance_threshold=0.80):
    """ Apply PCA and select components that explain at least the given variance threshold.
        The data need to be standardized before PCA.
     """

    pca = PCA(n_components=variance_threshold)
    df_pca = pca.fit_transform(df)
    explained_variance = sum(pca.explained_variance_ratio_) * 100
    print(f"PCA: Selected {pca.n_components_} components, explaining {explained_variance:.2f}% variance.")
    df_pca_transformed = pd.DataFrame(df_pca, columns=[f"PCA_{i + 1}" for i in range(pca.n_components_)])
    return df_pca_transformed


def apply_umap_function(df, n_components=2):
    """ Apply UMAP to reduce dimensions to n_components.
        The data need to be standardized before UMAP.
    """

    umap_model = umap.UMAP(n_components=n_components, n_neighbors=15, min_dist=0.1, random_state=42)
    df_umap = umap_model.fit_transform(df)
    print(f"UMAP: Reduced data to {n_components} dimensions.")
    df_umap_transformed = pd.DataFrame(df_umap, columns=[f"UMAP_{i + 1}" for i in range(n_components)])
    return df_umap_transformed


x = df.iloc[:, 6:]
df_x = x.copy()

if nan_treatement:
    if nan_treatement == 'custom_imputation':
        df_x = custom_imputation_nan(df_x)
    else:
        df_x = handle_nan(df_x, method=nan_treatement)

if power_transform:
    df_x = transform(df_x, method=power_transform)

if standardized:
    df_x = standardize(df_x)

if pca_variance_threshold and standardized:
    df_x = apply_pca_function(df_x, variance_threshold=pca_variance_threshold)

if umap_n_components and standardized:
    df_x = apply_umap_function(df_x, n_components=umap_n_components)

df_combined = pd.concat([df.iloc[:, :6], df_x], axis=1)

print(df_combined.head())
file_name = os.path.join(product["data"], "eda_features.csv")
df_combined.to_csv(file_name, index=False)

dfSummary(df_combined, is_collapsible=True)

df_sorted = df_combined[df_combined.isnull().sum().sort_values(ascending=False).index]
msno.bar(df_sorted)

# summary = dfSummary(df, is_collapsible=True)
# Save as HTML
# TODO: Save summary as HTML don't work now
# summary_file = os.path.join(product["data"], "df_summary.html")
# with open(summary_file, "w", encoding="utf-8") as f:
#     f.write(summary)
