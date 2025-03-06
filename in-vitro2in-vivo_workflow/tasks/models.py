import pandas as pd
import numpy as np
import os.path
from sklearn.model_selection import train_test_split, RandomizedSearchCV, LeaveOneOut
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from xgboost import XGBRegressor, plot_importance
from sklearn.metrics import (mean_squared_error, root_mean_squared_error,
                             r2_score, mean_absolute_error, 
                             mean_absolute_percentage_error)
from pathlib import Path


# + tags=["parameters"]
upstream = ["eda_features_*"]
product = None
in_vivo_cell = None
in_vivo_time = None
# -


path = upstream["eda_features_*"][f"eda_features_{in_vivo_cell}_{in_vivo_time}"]["data"]
Path(product["data"]).mkdir(parents=True, exist_ok=True)

df = pd.read_csv(os.path.join(path, "eda_features.csv"))
os.makedirs(product["data"], exist_ok=True)
print(df)


def evaluate_model(y_test, y_pred):
    metrics = {
        "MSE": mean_squared_error(y_test, y_pred),
        "RMSE": root_mean_squared_error(y_test, y_pred),
        "MAE": mean_absolute_error(y_test, y_pred),
        "MAPE": mean_absolute_percentage_error(y_test, y_pred),
        "R^2 Score": r2_score(y_test, y_pred),
    }

    return metrics


def optimize_model(model_name, model, X_train, y_train):
    print(f"\nOptimizing {model_name}...")

    if model_name not in param_grids:
        print(f"Skipping {model_name} (no hyperparameters to tune)")
        return model

    param_grid = param_grids[model_name]

    random_search = RandomizedSearchCV(
        model,
        param_distributions=param_grid,
        n_iter=50,
        cv=5,
        # scoring='neg_mean_squared_error',  # Optimize for MSE
        scoring={'neg_mean_squared_error': 'neg_mean_squared_error', 'r2': 'r2'},  # Multiple scoring metrics
        refit='r2',  # Select the best model based on R²
        verbose=1,
        n_jobs=-1,
        random_state=42
    )

    random_search.fit(X_train, y_train.ravel())  # .ravel() to remove DataConversionWarning

    print(f"Best parameters for {model_name}: {random_search.best_params_}")
    return random_search.best_estimator_


def cross_validate_loocv(model, X, y):
    loo = LeaveOneOut()
    y_true, y_pred = [], []

    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model.fit(X_train, y_train)
        pred = model.predict(X_test)

        y_true.append(y_test[0])
        y_pred.append(pred[0])

    return np.array(y_true), np.array(y_pred)


# Define hyperparameter grids for each model
param_grids = {
    "XGBoost": {
        "n_estimators": np.arange(100, 1000, 100),
        "learning_rate": np.linspace(0.01, 0.3, 10),
        "max_depth": np.arange(3, 10, 1),
        "min_child_weight": np.arange(1, 10, 1),
        "subsample": np.linspace(0.5, 1.0, 5),
        "colsample_bytree": np.linspace(0.5, 1.0, 5),
        "gamma": np.arange(0, 5, 1),
        "reg_alpha": np.arange(0, 10, 1),
        "reg_lambda": np.arange(0, 10, 1)
    },

    "RandomForest": {
        "n_estimators": np.arange(100, 1000, 100),
        "max_depth": [None, 10, 20, 30, 50],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4]
    },

    "HistGradientBoosting": {
        "max_iter": np.arange(100, 1000, 100),
        "learning_rate": np.linspace(0.01, 0.3, 10),
        "max_depth": np.arange(3, 10, 1),
        "l2_regularization": np.linspace(0, 1, 5)
    },

    "GradientBoosting": {
        "n_estimators": np.arange(100, 1000, 100),
        "learning_rate": np.linspace(0.01, 0.3, 10),
        "max_depth": np.arange(3, 10, 1),
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "subsample": np.linspace(0.5, 1.0, 5)
    },

    "SVR": {
        "C": np.logspace(-2, 2, 5),
        "gamma": ['scale', 'auto'],
        "kernel": ['linear', 'rbf', 'poly', 'sigmoid']
    },

    "KNeighbors": {
        "n_neighbors": np.arange(1, 20, 2),
        "weights": ['uniform', 'distance'],
        "metric": ['euclidean', 'manhattan', 'minkowski']
    }
}

models = {
    "XGBoost": XGBRegressor(objective='reg:squarederror', n_estimators=100, seed=42),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, oob_score=True),
    "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=100, random_state=42),
    "GradientBoosting": GradientBoostingRegressor(subsample=0.75, n_estimators=100, min_samples_split=5,
                                                  min_samples_leaf=4, max_depth=9, learning_rate=0.01),
    "SVR": SVR(),
    # # "LinearRegression": LinearRegression(), # very bad
    "KNeighbors": KNeighborsRegressor(n_neighbors=5)
}

X = df.iloc[:, 7:]
y = df['BMD_SD1'].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

optimized_models = {}
for name, model in models.items():
    print(f"\nTraining {name}...")
    if df.isnull().values.any():
        if name in ["GradientBoosting", "SVR", "KNeighbors"]:
            print(f"Skipping {name} due to NaN values in the dataset.")
            continue

    best_model = optimize_model(name, model, X_train, y_train)
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)

    results = evaluate_model(y_test, y_pred)
    optimized_models[name] = best_model

    print(f"\nMetrics for {name} after optimization: ")
    for metric, value in results.items():
        print(f"{metric}: {value: .4f}")
    print("-" * 30)

print(optimized_models)

feature_importances_RF = None
for name, model in optimized_models.items():
    print(f"\nTraining {name}...")
    if df.isnull().values.any():
        if name in ["GradientBoosting", "SVR", "KNeighbors"]:
            print(f"Skipping {name} due to NaN values in the dataset.")
            continue

    model.fit(X_train, y_train)
    # y_pred = model.predict(X_test)
    y_true, y_pred = cross_validate_loocv(model, X, y)
    results = evaluate_model(y_true, y_pred)

    print(f"Metrics for {name} and LOO CV: ")
    for metric, value in results.items():
        print(f"{metric}: {value: .4f}")
    print("-" * 30)

    if name == "RandomForest":
        print(f"OOB Score: {model.oob_score_:.4f}")
        # if hasattr(model, "feature_importances"):
        x = df.iloc[:, 7:]
        feature_importances = pd.Series(model.feature_importances_, index=x.columns)
        feature_importances = feature_importances.sort_values()
        print(feature_importances.iloc[-10:])
        feature_importances_RF = feature_importances.iloc[-10:]

        feature_importances.plot(kind="barh", figsize=(15, 40), color='Green')
        plt.title("Feature Importances")
        plt.xlabel("Importance Score")
        plt.ylabel("Features")
        plt.tight_layout()
        plt.show()

    if name == "XGBoost":
        plt.figure(figsize=(15, 8))
        plot_importance(model, importance_type='gain', max_num_features=20, color='blue')
        plt.title("XGBoost Feature Importance")
        plt.show()

    #     tree_to_plot = model.estimators_[0]
    #
    #     # Plot the decision tree
    #     plt.figure(figsize=(20, 10))
    #     plot_tree(tree_to_plot, feature_names=df.columns.tolist(), filled=True, rounded=True, fontsize=10)
    #     plt.title("Decision Tree from Random Forest")
    #     plt.show()

print(feature_importances_RF)
file_name = os.path.join(product["data"], "feature_importance.csv")
feature_importances_RF.to_csv(file_name, index=True)
# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

''' 

After filtering in-vitro data by cell and time, the model's statistical parameters got worse

'''
