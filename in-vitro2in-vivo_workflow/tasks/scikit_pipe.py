import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler, PowerTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor 
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import (mean_squared_error, root_mean_squared_error,
                             r2_score, mean_absolute_error,
                             mean_absolute_percentage_error)
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from xgboost import XGBRegressor
from pathlib import Path
import os.path 
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold, KFold, LeaveOneOut, LeaveOneGroupOut, LeavePGroupsOut


# + tags=["parameters"]
upstream = ["preprocessing", "compare_clusters"]
product = None
in_vivo_cell = None
in_vivo_time = None
in_vitro_assay = None
cluster_label = None
model = None
cv_LOGO = None
cv_KFOLD = None
# -


def plot_results(y_actual, y_pred, y_std, y_vars, title="Gaussian Process Regression"):
    plt.figure(figsize=(10, 6))
    plt.scatter(y_actual, y_pred, label='Predicted vs Actual', color='red', edgecolors='black', linewidth=0.5)
    if y_std is not None:
        plt.errorbar(y_actual, y_pred, yerr=1.96 * y_std, fmt='o', alpha=0.5, label='95% CI', color='blue', markersize=2)
    plt.errorbar(y_actual, y_pred, yerr=y_vars, fmt='o', alpha=0.5, label='BMD_U/L Error (95% CI)', color='green',
                 markersize=0.2)
    plt.plot([y_actual.min(), y_actual.max()], [y_actual.min(), y_actual.max()], 'r--', label='Prediction')
    plt.xlabel('Actual BMD')
    plt.ylabel('Predicted BMD')
    plt.title(title)
    plt.legend()
    plt.show()


def quantile_loss(y_true, y_pred, quantile):
    errors = y_true - y_pred
    return np.mean(np.maximum(quantile * errors, (quantile - 1) * errors))


def evaluate_model(y_true, y_pred, y_std=None):
    Z_low, Z_high = -1.645, 1.645

    metrics = {
        "R² Score": r2_score(y_true, y_pred),
        "MAE": mean_absolute_error(y_true, y_pred),
        "MSE": mean_squared_error(y_true, y_pred),
        "RMSE": root_mean_squared_error(y_true, y_pred),
    }
    if y_std is not None:
        y_lower = y_pred + Z_low * y_std
        y_upper = y_pred + Z_high * y_std
        metrics["Quantile Loss (5%)"] = quantile_loss(y_true, y_lower, 0.05),
        metrics["Quantile Loss (95%)"] = quantile_loss(y_true, y_upper, 0.95)

    return metrics


def gpr_model(y_vars_train=None, n_restarts_optimizer=3):
    kernel = ConstantKernel(1.0) * RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
    return GaussianProcessRegressor(kernel=kernel, alpha=y_vars_train, n_restarts_optimizer=n_restarts_optimizer)    


def xgb_model():
    return XGBRegressor(objective='reg:squarederror', n_estimators=100, seed=42)

def rf_model():
    return RandomForestRegressor(n_estimators=100, random_state=42, oob_score=True)



def create_pipeline(X, y_vars_train=None, model="XGB"):
    categorical_cols = ['cell', 'assay']
    numerical_cols = X.columns.difference(categorical_cols)  # Other numeric features
    preprocessor = ColumnTransformer([
        ('cat', OneHotEncoder(sparse_output=False), categorical_cols),
        ('num', PowerTransformer(), numerical_cols)  # Standardize numeric features
    ])

    _models = {
        "GPR": gpr_model(y_vars_train.values),
        "XGB": xgb_model(),
        "RF": rf_model()
    }

    regressor = _models[model]

    # Use TransformedTargetRegressor to apply log transformation to y
    #regressor = TransformedTargetRegressor(regressor=gpr, 
    #                                       func=np.log1p,  # Log-transform y
    #                                       inverse_func=np.expm1)  # Reverse log transform

    # Define the full pipeline
    return Pipeline([
        ('preprocessor', preprocessor),
        ('model', regressor)  # Use transformed target regressor
    ])


Path(product["data"]).parent.mkdir(parents=True, exist_ok=True)

in_vitro_assay

df = pd.read_excel(upstream["preprocessing"]["xy"])
df.head()

clusters = pd.read_excel(upstream["compare_clusters"]["data"])[["material", "cluster_label"]]
clusters.head()

print("Unique CellType values:", df["CellType"].unique())
print("Unique time values:", df["time"].unique())
print("Unique in vitro assay values:", df["assay"].unique())
print("Unique cluster values:", clusters["cluster_label"].unique())
print("Filtering for:", in_vivo_cell, in_vivo_time, in_vitro_assay, cluster_label)

df = df.loc[(df["CellType"] == in_vivo_cell) & (df["Day"] == in_vivo_time)]
if in_vitro_assay != "ALL":
    df = df.loc[df["assay"] == in_vitro_assay]

df.head()

df = df.dropna(how="any")
df = pd.merge(df, clusters, on="material", how="left")
if cluster_label != "ALL":
    df = df.loc[df["cluster_label"] == cluster_label]
df.to_excel(product["data"], index=False)

X = df.drop(columns=['material','BMD_SD1', 'BMDL_SD1', 'BMDU_SD1', 'CellType', 'Day','cluster_label'])
y = df['BMD_SD1']
y_vars = (df['BMDU_SD1'] - df['BMDL_SD1']) / 3.92
groups = df['cluster_label']
materials = df['material']

X.columns


# Split the data into training and testing sets
X_train, X_test, y_train, y_test, y_vars_train, y_vars_test, m_train, m_test = train_test_split(
    X, y, y_vars, materials, test_size=0.3, random_state=42, stratify=groups)

pipeline = create_pipeline(X, y_vars_train, model)

# Fit the pipeline on the training data
pipeline.fit(X_train, y_train)


X_test_transformed = pipeline.named_steps['preprocessor'].transform(X_test)
if model=="GPR":
    y_pred, y_pred_std = pipeline.named_steps['model'].predict(X_test_transformed, return_std=True)
else:
    y_pred = pipeline.named_steps['model'].predict(X_test_transformed)    
    y_pred_std = None

results = evaluate_model(y_test, y_pred, y_pred_std)
_metrics = pd.DataFrame(list(results.items()), columns=["Metric", "Value"])
_metrics["cv_method"] = "Test"
_metrics["method"] = model
_metrics["cell"] = in_vivo_cell
_metrics["time"] = in_vivo_time
_metrics["invitro_assay"] = in_vitro_assay
_metrics["cluster_label"] = cluster_label
_metrics["materials"] = len(m_test.unique()) # ", ".join(map(str, m_test.unique()))

#metrics = pd.concat([metrics, _metrics], ignore_index=True)
metrics = _metrics
metrics.to_excel(product["metrics"], index=False)

metrics

#method = "Train"
#plot_results(y_train, y_pred0, y_pred_std0, y_vars_train, title=f'{model} with {method} Split')

method = "Test"
plot_results(y_test, y_pred, y_pred_std, y_vars_test, title=f'{model} with {method} Split')

split_tag = []
splits = []
if cv_LOGO > 0:
    if cluster_label == "ALL":
        logo = LeaveOneGroupOut()
        splits.append(logo.split(X, y, groups=groups))
        split_tag.append("LOGO")
    else:
        #logo = LeaveOneOut()
        logo = LeaveOneGroupOut()
        splits.append(logo.split(X, y, groups=materials))
        split_tag.append("LOGO")
if cv_KFOLD > 0:
    if cluster_label == "ALL":
        skf = StratifiedKFold(n_splits=cv_KFOLD, shuffle=True, random_state=42)
        splits.append(skf.split(X, y=groups if cluster_label == "ALL" else y))
        split_tag.append("SKFOLD")
    else:
        skf = KFold(n_splits=cv_KFOLD, shuffle=True, random_state=42)
        splits.append(skf.split(X, y))
        split_tag.append("KFOLD")    

print(split_tag)
for tag, split in zip(split_tag, splits):
    print(tag)
    y_test_loo, y_pred_loo, y_std_loo = [], [], []
    for i, (train_idx, test_idx) in enumerate(split):
        print(i)
        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        y_vars_train = y_vars.iloc[train_idx]

        pipeline = create_pipeline(X, y_vars_train, model)
        pipeline.fit(X_train, y_train)
        
        X_test = X.iloc[test_idx]
        y_test = y.iloc[test_idx]
        y_vars_test = y_vars.iloc[test_idx]
        clusters = groups.iloc[test_idx].unique()
        _materials = materials.iloc[test_idx].unique()

        X_test_transformed = pipeline.named_steps['preprocessor'].transform(X_test)
        if model == "GPR":
            y_pred, y_pred_std = pipeline.named_steps['model'].predict(X_test_transformed, return_std=True)
        else:
            y_pred = pipeline.named_steps['model'].predict(X_test_transformed)    
            y_pred_std = None    

        if tag != "LOO":
            results = evaluate_model(y_test, y_pred, y_pred_std)
            _metrics = pd.DataFrame(list(results.items()), columns=["Metric", "Value"])
            _metrics["cv_method"] = f"{tag} {i}"
            _metrics["method"] = model
            _metrics["cell"] = in_vivo_cell
            _metrics["time"] = in_vivo_time
            _metrics["cluster_label"] = cluster_label
            _metrics["clusters"] = "Cluster " + ", ".join(map(str, clusters))
            _metrics["materials"] = len(_materials)
            _metrics["invitro_assay"] = in_vitro_assay
            metrics = pd.concat([metrics, _metrics], ignore_index=True)
        else:
            y_test_loo.append(y_test.values[0])
            y_pred_loo.append(y_pred[0])
            if y_pred_std is not None:
                y_std_loo.append(y_pred_std[0])

    if tag == "LOO":
        results = evaluate_model(y_test_loo, y_pred_loo)
        _metrics = pd.DataFrame(list(results.items()), columns=["Metric", "Value"])
        _metrics["cv_method"] = f"{tag}"
        _metrics["method"] = model
        _metrics["cell"] = in_vivo_cell
        _metrics["time"] = in_vivo_time
        _metrics["cluster_label"] = cluster_label
        _metrics["clusters"] = "Cluster " + ", ".join(map(str, clusters))
        _metrics["invitro_assay"] = in_vitro_assay
        metrics = pd.concat([metrics, _metrics], ignore_index=True)        

with pd.ExcelWriter(product["metrics"], engine='xlsxwriter') as writer:
    sheet = "metrics"
    metrics.to_excel(writer, sheet_name=sheet, index=False)
    worksheet = writer.sheets[sheet]    
    (max_row, max_col) = metrics.shape
    column_settings = [{'header': column} for column in metrics.columns]
    worksheet.add_table(0, 0, max_row, max_col - 1,
                {'columns': column_settings, 'style': 'Table Style Light 1'})    


