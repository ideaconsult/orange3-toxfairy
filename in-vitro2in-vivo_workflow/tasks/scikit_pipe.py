from IPython.display import display, HTML
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler, PowerTransformer, QuantileTransformer
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
from tasks.utils import plot_results, plot_results_materials
from sklearn.model_selection import RandomizedSearchCV
import joblib
from summarytools import dfSummary


# + tags=["parameters"]
upstream = ["preprocessing", "compare_clusters"]
product = None
in_vivo_cell = None
in_vivo_time = None
in_vitro_assay = None
in_vitro_cell = None
cluster_label = None
model = None
cv_LOGO = None
cv_KFOLD = None
cv_MATERIAL = None
dataset = None
clean_products = None
log_transform = None
predict_all = None
param_search = None
# -


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
    #return RandomForestRegressor(n_estimators=200, random_state=42, min_samples_split= 2, min_samples_leaf= 3, max_features= 'log2', max_depth= 5, oob_score=True)
#Best Parameters: {'model__n_estimators': 200, 'model__min_samples_split': 2, 'model__min_samples_leaf': 3, 'model__max_features': 'sqrt', 'model__max_depth': 5}
#Best Parameters: {'model__n_estimators': 200, 'model__min_samples_split': 2, 'model__min_samples_leaf': 3, 'model__max_features': 'log2', 'model__max_depth': 5}



def create_pipeline(X, y_vars_train=None, model="XGB", log_transform=False):
    categorical_cols = ['cell', 'assay', 'CellType']
    numerical_cols = X.columns.difference(categorical_cols)  # Other numeric features
    preprocessor = ColumnTransformer([
        ('cat', OneHotEncoder(sparse_output=False), categorical_cols),
        ('num', PowerTransformer(), numerical_cols)  # Standardize numeric features
        #('num', QuantileTransformer(), numerical_cols)  # Standardize numeric features
    ])

    _models = {
        "GPR": gpr_model(y_vars_train.values),
        "XGB": xgb_model(),
        "RF": rf_model()
    }

    regressor = _models[model]

    if log_transform:
        regressor = TransformedTargetRegressor(
            regressor=regressor,
            func=np.log1p,  # Apply log transformation (log(1 + y))
            #inverse_func=lambda x: x 
            inverse_func=np.expm1  # Reverse transformation (exp(y) - 1)
        )

    # Use TransformedTargetRegressor to apply log transformation to y
    # regressor = TransformedTargetRegressor(regressor=gpr,
    #                                       func=np.log1p,  # Log-transform y
    #                                       inverse_func=np.expm1)  # Reverse log transform

    # Define the full pipeline
    return Pipeline([
        ('preprocessor', preprocessor),
        ('model', regressor)  # Use transformed target regressor
    ])


Path(product["data"]).parent.mkdir(parents=True, exist_ok=True)

if dataset is None:
    dataset = "xy"
if predict_all is None:
    predict_all = False

df = pd.read_excel(upstream["preprocessing"][dataset])
df.head()

clusters = pd.read_excel(upstream["compare_clusters"]["data"])[["material", "cluster_label"]]
clusters.head()

print("Unique cluster values:", clusters["cluster_label"].unique())

if in_vivo_cell != "ALL":
    print("Unique CellType values:", df["CellType"].unique())
    df = df.loc[df["CellType"] == in_vivo_cell]
    display(df.head())
if in_vivo_time != "ALL":
    print("Unique time values:", df["Day"].unique())
    df = df.loc[df["Day"] == in_vivo_time]
    display(df.head())
if in_vitro_assay != "ALL":
    print("Unique in vitro assay values:", df["assay"].unique())
    df = df.loc[df["assay"] == in_vitro_assay]
    display(df.head())
if in_vitro_cell != "ALL":
    print("Unique in vitro cell values:", df["cell"].unique())
    df = df.loc[df["cell"] == in_vitro_cell]
    display(df.head())

print("Filtering for:", in_vivo_cell, in_vivo_time, in_vitro_assay, cluster_label)
df.head()

df = df.dropna(how="any")
display(df.head())

if clean_products:
    try:
        os.remove(product["data"])
    except:
        pass
    try:
        os.remove(product["metrics"])
    except:
        pass

if df.empty:
    _metrics = pd.DataFrame(columns=[
        "Metric", "Value", "cv_method", "method", "cell", "time",
        "invitro_assay", "invitro_cell", "cluster_label", "materials"
    ])
    _metrics.to_excel(product["metrics"], index=False)
    df.to_excel(product["data"], index=False)
    plt.figure()
    plt.savefig(product["plot"])
elif not Path(product["metrics"]).exists():

    df = pd.merge(df, clusters, on="material", how="left")
    if cluster_label != "ALL":
        df = df.loc[df["cluster_label"] == cluster_label]
    df.to_excel(product["data"], index=False)

    X = df.drop(columns=['material', 'BMD_SD1', 'BMDL_SD1', 'BMDU_SD1', 'cluster_label'])
    y = df['BMD_SD1']
    groups = df['cluster_label']
    materials = df['material']
    Y_lower = df['BMDL_SD1']
    Y_upper = df['BMDU_SD1']


    #if log_transform:
    #    Y_lower = np.log1p(df['BMDL_SD1'])
    #    Y_upper = np.log1p(df['BMDU_SD1'])
    # handling log variance is more tricky , good that we don't use it in xgb/rf
    y_vars = (Y_upper - Y_lower) / 3.92

    # X.columns

    # Split the data into training and testing sets
    try:
        X_train, X_test, y_train, y_test, y_vars_train, y_vars_test, m_train, m_test, y_lower_train, y_lower_test, y_upper_train, y_upper_test, = train_test_split(
            X, y, y_vars, materials, Y_lower, Y_upper, test_size=0.3, random_state=42, stratify=groups)
        cv_method = "Test"
    except Exception as err:
        X_train, X_test, y_train, y_test, y_vars_train, y_vars_test, m_train, m_test, y_lower_train, y_lower_test, y_upper_train, y_upper_test, = train_test_split(
            X, y, y_vars, materials, Y_lower, Y_upper, test_size=0.3, random_state=42)
        cv_method = "Test*"


    #if log_transform:
    #    y_test = np.log1p(y_test)

    pipeline = create_pipeline(X, y_vars_train, model, log_transform)

    param_grid = {
        'model__n_estimators': [100, 200, 300],
        'model__max_depth': [1,2,3,4,5, 10, 15],
        'model__min_samples_split': [2, 5, 10, 20],
        'model__min_samples_leaf': [1, 3, 5, 10],
        'model__max_features': ['sqrt', 'log2']
    }
   
    if model == "RF" and param_search: 
        logo = LeaveOneGroupOut()
        random_search = RandomizedSearchCV(
            pipeline, param_grid, n_iter=20, cv=logo, scoring='r2', n_jobs=-1, verbose=1
        )
        random_search.fit(X, y, groups=materials)
        #random_search.fit(X_train, y_train, groups=m_train)
        print("Best Parameters:", random_search.best_params_)
        pipeline = random_search.best_estimator_
        if "model" in product:
            joblib.dump(pipeline, product["model"])
        #pipeline.fit(X_train, y_train)
    else:
        # Fit the pipeline on the training data
        pipeline.fit(X_train, y_train)
        if "model" in product:
            joblib.dump(pipeline, product["model"])

    X_test_transformed = pipeline.named_steps['preprocessor'].transform(X_test)
    if model == "GPR":
        y_pred, y_pred_std = pipeline.named_steps['model'].predict(X_test_transformed, return_std=True)
    else:
        y_pred = pipeline.named_steps['model'].predict(X_test_transformed)
        y_pred_std = None
    #if log_transform:
    #    y_pred = np.log1p(y_pred)

    results = evaluate_model(y_test, y_pred, y_pred_std)
    _metrics = pd.DataFrame(list(results.items()), columns=["Metric", "Value"])
    _metrics["cv_method"] = cv_method
    _metrics["method"] = model
    _metrics["cell"] = in_vivo_cell
    _metrics["time"] = in_vivo_time
    _metrics["invitro_assay"] = in_vitro_assay
    _metrics["invitro_cell"] = in_vitro_cell
    _metrics["cluster_label"] = cluster_label
    _metrics["materials"] = len(m_test.unique())  # ", ".join(map(str, m_test.unique()))

    # metrics = pd.concat([metrics, _metrics], ignore_index=True)
    metrics = _metrics
    metrics.to_excel(product["metrics"], index=False)

    # metrics

    # method = "Train"
    # plot_results(y_train, y_pred0, y_pred_std0, y_lower_train, y_upper_train,
    # title=f'{model} with {method} Split for {in_vitro_assay} - {in_vitro_cell} vs {in_vivo_cell} - {in_vivo_time} day.')

    method = "Test"
    plot_obj = plot_results(y_test, y_pred, y_pred_std, y_lower_test, y_upper_test,
                            title=f'{model} with {method} Split for in-vitro {in_vitro_assay} assay - {in_vitro_cell} cell vs in-vivo {in_vivo_cell} - {in_vivo_time} day.',
                            log=log_transform)
    plot_obj.savefig(product["plot"])
    plot_obj_materials = plot_results_materials(y_test, y_pred, y_pred_std, y_lower_test, y_upper_test,m_test,
                            title=f'{model} with {method} Split for in-vitro {in_vitro_assay} assay - {in_vitro_cell} cell vs in-vivo {in_vivo_cell} - {in_vivo_time} day.',
                            log=log_transform)
    plot_obj_materials.savefig(product["plot_m"])

    #bag_ids = X_test_instances['bag_id']
    #bag_preds = [np.mean(instance_preds[bag_ids == bag]) for bag in np.unique(bag_ids)]

    split_tag = []
    splits = []
    if cv_MATERIAL > 0:
        logo = LeaveOneGroupOut()
        splits.append(logo.split(X, y, groups=materials))
        split_tag.append("MATERIAL")
             
    if cv_LOGO > 0:
        try:
            if cluster_label == "ALL":
                logo = LeaveOneGroupOut()
                splits.append(logo.split(X, y, groups=groups))
                split_tag.append("LOGO")
            else:
                # logo = LeaveOneOut()
                logo = LeaveOneGroupOut()
                splits.append(logo.split(X, y, groups=materials))
                split_tag.append("LOO")
        except Exception as err:
            print(err)
    if cv_KFOLD > 0:
        if cluster_label == "ALL":
            try:
                skf = StratifiedKFold(n_splits=cv_KFOLD, shuffle=True, random_state=42)
                splits.append(skf.split(X, y=groups if cluster_label == "ALL" else y))
                split_tag.append("SKFOLD")
            except Exception as err:
                print(err)
        else:
            try:
                skf = KFold(n_splits=cv_KFOLD, shuffle=True, random_state=42)
                splits.append(skf.split(X, y))
                split_tag.append("KFOLD")
            except Exception as err:
                print(err)

    print(split_tag)
    for tag, split in zip(split_tag, splits):
        print(tag)
        y_test_loo, y_pred_loo, y_std_loo = [], [], []
        try:
            for i, (train_idx, test_idx) in enumerate(split):

                X_train = X.iloc[train_idx]
                y_train = y.iloc[train_idx]
                y_vars_train = y_vars.iloc[train_idx]

                pipeline = create_pipeline(X, y_vars_train, model, log_transform)
                if tag == "MATERIAL" and param_search and model=="RF":
                    random_search = RandomizedSearchCV(
                        pipeline, param_grid, n_iter=20, cv=3, scoring='r2', n_jobs=-1, verbose=1
                    )
                    random_search.fit(X_train, y_train)
                    print("Best Parameters:", random_search.best_params_)
                    pipeline = random_search.best_estimator_
                else:                    
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
                
                #if log_transform:
                #    y_pred = np.log1p(y_pred)

                if tag != "LOO":
                    results = evaluate_model(y_test, y_pred, y_pred_std)
                    _metrics = pd.DataFrame(list(results.items()), columns=["Metric", "Value"])
                    if tag == "MATERIAL":
                        _metrics["cv_method"] = f"{tag}"
                    else:
                        _metrics["cv_method"] = f"{tag} {i}"
                    _metrics["method"] = model
                    _metrics["cell"] = in_vivo_cell
                    _metrics["time"] = in_vivo_time
                    _metrics["cluster_label"] = cluster_label
                    _metrics["clusters"] = "Cluster " + ", ".join(map(str, clusters))
                    _metrics["materials"] = len(_materials)
                    _metrics["invitro_assay"] = in_vitro_assay
                    _metrics["invitro_cell"] = in_vitro_cell
                    metrics = pd.concat([metrics, _metrics], ignore_index=True)
                    if predict_all:
                        X_transformed = pipeline.named_steps['preprocessor'].transform(X)
                        y_pred_all = pipeline.named_steps['model'].predict(X_transformed)
                        df[f"{tag}_{i}_model"] = y_pred_all
                    
                else:
                    y_test_loo.extend(y_test.values)
                    y_pred_loo.extend(y_pred)
                    if y_pred_std is not None:
                        y_std_loo.extend(y_pred_std)
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
                _metrics["invitro_cell"] = in_vitro_cell
                metrics = pd.concat([metrics, _metrics], ignore_index=True)
        except Exception as err:
            print(err)

    with pd.ExcelWriter(product["metrics"], engine='xlsxwriter') as writer:
        sheet = "metrics"
        metrics.to_excel(writer, sheet_name=sheet, index=False)
        worksheet = writer.sheets[sheet]
        (max_row, max_col) = metrics.shape
        column_settings = [{'header': column} for column in metrics.columns]
        worksheet.add_table(0, 0, max_row, max_col - 1,
                            {'columns': column_settings, 'style': 'Table Style Light 1'})

if predict_all:
    df.to_excel(product["data"], index=False)
    dfSummary(df, is_collapsible=True)