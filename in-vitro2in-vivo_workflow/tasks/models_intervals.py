import pandas as pd
import numpy as np
import os.path
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, ConstantKernel as C
from sklearn.metrics import (mean_squared_error, root_mean_squared_error, 
                             r2_score, mean_absolute_error, 
                             mean_absolute_percentage_error)
from sklearn.model_selection import LeaveOneOut, KFold, train_test_split


# + tags=["parameters"]
upstream = ["data_concat_*", "eda_features_*", "models_*"]
product = None
in_vivo_cell = None
in_vivo_time = None
# -


path = upstream["eda_features_*"][f"eda_features_{in_vivo_cell}_{in_vivo_time}"]["data"]
df = pd.read_csv(os.path.join(path, "eda_features.csv"))
df = df[df['BMD_SD1'] <= 60]

# Selected important features from RandomForest
features_path = upstream["models_*"][f"models_{in_vivo_cell}_{in_vivo_time}"]["data"]
features = pd.read_csv(os.path.join(features_path, "feature_importance.csv"))
feature_list = features.iloc[:, 0].tolist()
feature_list

# Original feature values used to plot Log(x) vs Log(Y)
path2raw = upstream["data_concat_*"][f"data_concat_{in_vivo_cell}_{in_vivo_time}"]["data"]
df_raw = pd.read_csv(os.path.join(path2raw, "combined.csv"))
# df_raw = df_raw[df_raw['BMD_SD1'] <= 60]

y_err_lower = df['BMD_SD1'] - df['BMDL_SD1']
y_err_upper = df['BMDU_SD1'] - df['BMD_SD1']

plt.figure(figsize=(8, 8))
plt.errorbar(df['BMD_SD1'], df['ParticleID'], xerr=[y_err_lower, y_err_upper], fmt='o',
             ecolor='red', capsize=5, label='BMD')
plt.xlabel('BMD Value')
plt.ylabel('Materials')
plt.title('BMD')
plt.legend()
plt.show()

log_bmd = np.log(df['BMD_SD1'] + 1)
log_y_err_lower = np.log(y_err_lower + 1)
log_y_err_upper = np.log(y_err_upper + 1)

plt.figure(figsize=(8, 8))
plt.errorbar(log_bmd, df['ParticleID'], xerr=[log_y_err_lower, log_y_err_upper], fmt='o',
             ecolor='red', capsize=5, label='Log of BMD')
plt.xlabel('Log of BMD Value')
plt.ylabel('Materials')
plt.title('BMD (Natural Logarithmic Scale)')
plt.legend()
plt.show()

print(df)


def evaluate_model(y_true, y_pred, y_std):
    Z_low, Z_high = -1.645, 1.645
    y_lower = y_pred + Z_low * y_std
    y_upper = y_pred + Z_high * y_std

    metrics = {
        "R² Score": r2_score(y_true, y_pred),
        "MAE": mean_absolute_error(y_true, y_pred),
        "MSE": mean_squared_error(y_true, y_pred),
        "RMSE": root_mean_squared_error(y_true, y_pred),
        "Quantile Loss (5%)": quantile_loss(y_true, y_lower, 0.05),
        "Quantile Loss (95%)": quantile_loss(y_true, y_upper, 0.95),
    }

    return metrics


def quantile_loss(y_true, y_pred, quantile):
    errors = y_true - y_pred
    return np.mean(np.maximum(quantile * errors, (quantile - 1) * errors))


def GPR_model(x, Y_means, Y_vars, x_test=None, kernel="RBF"):
    if x_test is None or (isinstance(x_test, np.ndarray) and x_test.size == 0):
        x_test = x

    if kernel == "RBF":
        kernel = C(1.0) * RBF(length_scale=1.0)
    elif kernel == "Matern":
        kernel = C(1.0) * Matern(length_scale=1.0, nu=1.5)

    gp = GaussianProcessRegressor(kernel=kernel,
                                  alpha=Y_vars + 0.1,  # Adding 0.1 to increase noise tolerance
                                  n_restarts_optimizer=10)
    gp.fit(x, Y_means)
    Y_pred, Y_std = gp.predict(x_test, return_std=True)

    return Y_pred, Y_std


def plot_results(y_actual, y_pred, y_std, y_vars, title="Gaussian Process Regression"):
    plt.figure(figsize=(10, 6))
    plt.scatter(y_actual, y_pred, label='Predicted vs Actual', color='red', edgecolors='black', linewidth=0.5)
    plt.errorbar(y_actual, y_pred, yerr=1.96 * y_std, fmt='o', alpha=0.5, label='95% CI', color='blue', markersize=2)
    plt.errorbar(y_actual, y_pred, yerr=y_vars, fmt='o', alpha=0.5, label='BMD_U/L Error (95% CI)', color='green',
                 markersize=0.2)
    plt.plot([y_actual.min(), y_actual.max()], [y_actual.min(), y_actual.max()], 'r--', label='Prediction')
    plt.xlabel('Actual BMD')
    plt.ylabel('Predicted BMD')
    plt.title(title)
    plt.legend()
    plt.show()


def cross_validate2(x, Y_means, Y_vars, method="LOO", n_splits=3, test_size=0.2, plot=True):
    y_preds, y_stds, y_actuals = [], [], []

    if method == "LOO":
        cv = LeaveOneOut()
    elif method == "KFold":
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    elif method == "TrainTest":
        X_train, X_test, Y_train, Y_test, y_vars_train, y_vars_test = train_test_split(
            x, Y_means, Y_vars, test_size=test_size, random_state=42)

        y_pred, y_std = GPR_model(X_train, Y_train, y_vars_train, X_test)
        results = evaluate_model(Y_test, y_pred, y_std)

        if plot:
            plot_results(Y_test, y_pred, y_std, y_vars_test, title=f'GPR with {method} Split')
        return results

    # Perform cross-validation
    for train_index, test_index in cv.split(x):
        x_train, x_test = x[train_index], x[test_index]
        y_train, y_test = Y_means[train_index], Y_means[test_index]
        y_train_vars, y_test_var = Y_vars[train_index], Y_vars[test_index]

        y_pred, y_std = GPR_model(x_train, y_train, y_train_vars, x_test)

        y_preds.append(y_pred[0])
        y_stds.append(y_std[0])
        y_actuals.append(y_test[0])

    y_preds = np.array(y_preds)
    y_stds = np.array(y_stds)
    y_actuals = np.array(y_actuals)

    results = evaluate_model(y_actuals, y_preds, y_stds)

    if plot:
        plot_results(y_actuals, y_preds, y_stds, y_test_var, title=f'GPR with {method}')

    return results


def extract_x_y(df, log=False):
    df_copy = df.copy()

    if log:
        cols_to_log = ['BMD_SD1', 'BMDL_SD1', 'BMDU_SD1', 'BMD_SD2', 'BMDL_SD2']
        df_copy[cols_to_log] = np.log(df[cols_to_log] + 1)

    df_copy['y_vars'] = (df_copy['BMDU_SD1'] - df_copy['BMDL_SD1']) / 3.92
    x = df_copy.iloc[:, 6:-1].values
    y_vars = df_copy['y_vars'].values
    y_means = df_copy['BMD_SD1'].values

    return df_copy, x, y_means, y_vars


df_copy, x, Y_means, Y_vars = extract_x_y(df, log=True)

#  ////////////////////////////////////// Train model //////////////////////////////////////////////////////////////////////
Y_pred, Y_std = GPR_model(x, Y_means, Y_vars)
results = evaluate_model(Y_means, Y_pred, Y_std)
print(f"Metrics for GaussianProcessRegressor: ")
for metric, value in results.items():
    print(f"{metric}: {value: .2f}")
print("-" * 30)

plt.figure(figsize=(10, 6))
plt.scatter(Y_means, Y_pred, label='Predicted vs Actual', color='red', edgecolors='black', linewidth=0.5)
plt.errorbar(Y_means, Y_pred, yerr=1.96 * Y_std, fmt='o', alpha=0.5, label='GP Error (95% CI)', color='blue',
             markersize=0.2)
plt.errorbar(Y_means, Y_pred, yerr=Y_vars, fmt='o', alpha=0.5, label='BMD_U/L Error (95% CI)', color='green',
             markersize=0.2)
# plt.fill_between(Y_means, Y_pred - 1.96 * Y_std, Y_pred + 1.96 * Y_std, color='blue', alpha=0.2)
# plt.fill_between(Y_means, Y_pred - Y_vars, Y_pred + Y_vars, color='green', alpha=0.2)
plt.plot([Y_means.min(), Y_means.max()], [Y_means.min(), Y_means.max()], 'r--', label='Perfect Prediction')
plt.xlabel('Actual BMD_SD1')
plt.ylabel('Predicted BMD_SD1')
plt.title('Gaussian Process Regression with Two Error Bars')
plt.legend()
plt.show()

# /////////////////////////////////////// Cross Validation ////////////////////////////////////////////////////////
cv_methods = ["LOO", "TrainTest"]

for method in cv_methods:
    results = cross_validate2(x, Y_means, Y_vars, method=method, n_splits=3, plot=True)
    print(f"Metrics for GaussianProcessRegressor with {method}:")
    for metric, value in results.items():
        print(f"{metric}: {value:.2f}")
    print("-" * 30)


# Plot BMD vs each original x feature
x_raw = df_raw.iloc[:, 7:]
flag = set(feature_list).issubset(x_raw.columns)

for column in feature_list:
    df_plot = pd.DataFrame({
        column: x_raw[column] if flag else x[:, feature_list.index(column)],
        'Y_pred': Y_pred,
        'Y_means': Y_means,
        'Y_std': Y_std,
        'Y_vars': Y_vars,
    })

    df_plot = df_plot.sort_values(by=column)
    plt.figure(figsize=(10, 5))
    plt.scatter(df_plot[column], Y_means, color='red', label="Observed Mean (log)", s=40)
    plt.errorbar(df_plot[column], Y_means, yerr=Y_vars, fmt='o', alpha=0.5,
                 label='BMD_U/L interval (log)', color='green', markersize=0.2)
    plt.plot(df_plot[column], Y_pred, 'b-', label="Predicted Mean (log)")
    plt.fill_between(df_plot[column],
                     Y_pred - 1.96 * Y_std,
                     Y_pred + 1.96 * Y_std,
                     color='b', alpha=0.2,
                     label="Predicted Distribution (95% CI)")
    plt.title(f"Gaussian Process for {column}")
    plt.xlabel(column)
    plt.ylabel("Log BMD_SD1 (μg/mouse)")
    plt.legend(loc='lower right')
    plt.show()