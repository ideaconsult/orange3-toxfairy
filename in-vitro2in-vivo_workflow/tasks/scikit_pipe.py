import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler, PowerTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import (mean_squared_error, root_mean_squared_error,
                             r2_score, mean_absolute_error,
                             mean_absolute_percentage_error)
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from pathlib import Path
import os.path 
import numpy as np
import matplotlib.pyplot as plt


# + tags=["parameters"]
upstream = ["preprocessing"]
product = None
in_vivo_cell = None
in_vivo_time = None
model = None
# -


def plot_results(y_actual, y_pred, y_std, y_vars, title="Gaussian Process Regression"):
    plt.figure(figsize=(10, 6))
    plt.scatter(y_actual, y_pred, label='Predicted vs Actual', color='red', edgecolors='black', linewidth=0.5)
    plt.errorbar(y_actual, y_pred, yerr=1.96 * y_std, fmt='o', alpha=0.5, label='95% CI', color='blue', markersize=2)
    plt.errorbar(y_actual, y_pred, yerr=y_vars, fmt='o', alpha=0.5, label='BMD_U/L Error (95% CI)', color='green',
                 markersize=0.2)
    plt.plot([y_actual.min(), y_actual.max()], [y_actual.min(), y_actual.max()], 'r--', label='Prediction')
    plt.xlabel('Actual ln(BMD)')
    plt.ylabel('Predicted ln(BMD)')
    plt.title(title)
    plt.legend()
    plt.show()


def quantile_loss(y_true, y_pred, quantile):
    errors = y_true - y_pred
    return np.mean(np.maximum(quantile * errors, (quantile - 1) * errors))


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
        "Quantile Loss (95%)": quantile_loss(y_true, y_upper, 0.95)
    }

    return metrics


def gpr_model(y_vars_train=None):
    kernel = ConstantKernel(1.0) * RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
    return GaussianProcessRegressor(kernel=kernel, alpha=y_vars_train.values, n_restarts_optimizer=10)    


Path(product["data"]).mkdir(parents=True, exist_ok=True)

df = pd.read_excel(upstream["preprocessing"]["xy"])
df.head()

print("Unique CellType values:", df["CellType"].unique())
print("Unique time values:", df["time"].unique())
print("Filtering for:", in_vivo_cell, in_vivo_time)

df = df.loc[(df["CellType"] == in_vivo_cell) & (df["Day"] == in_vivo_time)]
df.head()

df = df.dropna(how="any")
df.to_excel(os.path.join(product["data"], "data.xlsx"), index=False)

X = df.drop(columns=['material','BMD_SD1', 'BMDL_SD1', 'BMDU_SD1', 'CellType', 'Day'])
y = df['BMD_SD1']
y_vars = (df['BMDU_SD1'] - df['BMDL_SD1']) / 3.92

X.columns

# Define categorical columns to apply OneHotEncoder
categorical_cols = ['cell', 'assay']
numerical_cols = X.columns.difference(categorical_cols)  # Other numeric features

numerical_cols

# Define preprocessing pipeline
preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(sparse_output=False), categorical_cols),
    ('num', PowerTransformer(), numerical_cols)  # Standardize numeric features
])

# Split the data into training and testing sets
X_train, X_test, y_train, y_test, y_vars_train, y_vars_test = train_test_split(
            X, y, y_vars, test_size=0.3, random_state=42)


_models = {
    "GPR": gpr_model(y_vars_train.values)
}

regressor = _models[model]

# Use TransformedTargetRegressor to apply log transformation to y
#regressor = TransformedTargetRegressor(regressor=gpr, 
#                                       func=np.log1p,  # Log-transform y
#                                       inverse_func=np.expm1)  # Reverse log transform

# Define the full pipeline
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', regressor)  # Use transformed target regressor
])


# Fit the pipeline on the training data
pipeline.fit(X_train, y_train)

# Make predictions and get the variance (standard deviation)
#y_pred, y_pred_std = pipeline.predict(X_test, return_std=True)
# Transform X_test first using the pipeline's preprocessor
X_test_transformed = pipeline.named_steps['preprocessor'].transform(X_test)

# Now predict using the actual regressor inside the pipeline
#y_pred, y_pred_std = pipeline.named_steps['model'].regressor_.predict(X_test_transformed, return_std=True)
y_pred, y_pred_std = pipeline.named_steps['model'].predict(X_test_transformed, return_std=True)


# Print the predictions and variances (standard deviations)
#print("Predictions:", y_pred)
#print("Standard Deviations (Variances):", y_pred_std)

# Optionally, you can calculate the mean squared error (MSE) to evaluate the performance
mse = mean_squared_error(y_test, y_pred)

results = evaluate_model(y_test, y_pred, y_pred_std)
metrics = pd.DataFrame(list(results.items()), columns=["Metric", "Value"])
metrics["cv_method"] = "Test"
metrics["method"] = model
metrics["cell"] = in_vivo_cell
metrics["time"] = in_vivo_time

metrics.to_excel(os.path.join(product["data"], "metrics.xlsx"), index=False)

metrics

method = "Test"
plot_results(y_test, y_pred, y_pred_std, y_vars_test, title=f'{model} with {method} Split')