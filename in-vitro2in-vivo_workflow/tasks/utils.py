import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, QuantileTransformer, RobustScaler, PowerTransformer
)


def get_material_id():
    return "material"


def get_clusters_range(nsamples, min_clusters=3, min_cluster_size=10):
    return np.arange(min_clusters, round(nsamples / min_cluster_size), 1, dtype=int)


def preprocess(df, columns_weights=None, scaler="power"):
    X = df.drop(columns=[get_material_id()])
    _scaler = get_scaler(scaler)
    _scaler.fit(X)
    X_transformed = _scaler.transform(X)
    # Transform the data
    if columns_weights:
        for col, weight in columns_weights.items():
            if col in X.columns:  # Ensure the column exists
                col_idx = X.columns.get_loc(col)  # Get the column index
                X_transformed[:, col_idx] *= weight  # Apply the weight
    return X_transformed


def get_scaler(scaler="standard"):
    if scaler == "minmax":
        return MinMaxScaler()
    elif scaler == "quantile":
        return QuantileTransformer(output_distribution='normal')
    elif scaler == "robust":
        return RobustScaler()
    elif scaler == "standard":
        return StandardScaler()
    elif scaler == 'power':
        return PowerTransformer(method='yeo-johnson')
    else:
        return StandardScaler()


def drop_columns_by_missing_percentage(df, threshold):
    """
    Drops columns based on the percentage of missing values.

    Parameters:
    - df (pd.DataFrame): Input DataFrame.
    - threshold (float): Maximum percentage of missing values allowed (0 to 1).

    Returns:
    - pd.DataFrame: DataFrame with columns dropped.
    """
    # Calculate the percentage of missing values per column
    missing_percentage = df.isnull().mean()

    # Identify columns to drop
    cols_to_drop = missing_percentage[missing_percentage > threshold].index
    print(f"Columns dropped: {list(cols_to_drop)}")

    # Drop the columns
    df_cleaned = df.drop(columns=cols_to_drop)

    return df_cleaned


def plot_results(y_actual, y_pred, y_std, y_err_lower, y_err_upper, title="Gaussian Process Regression", log=False):
    xlabel = 'Actual BMD (μg/mouse)'
    ylabel = 'Predicted BMD (μg/mouse)'
    if log:
        xlabel = 'Actual log BMD (μg/mouse)'
        ylabel = 'Predicted log BMD (μg/mouse)'

    plt.figure(figsize=(10, 6))
    plt.scatter(y_actual, y_pred, label='Predicted vs Actual', color='red', edgecolors='black', linewidth=0.5)
    if y_std is not None:
        plt.errorbar(y_actual, y_pred, yerr=1.96 * y_std, fmt='o', alpha=0.5, label='95% CI', color='blue',
                     markersize=2)
    plt.errorbar(y_actual, y_pred, yerr=[y_err_lower, y_err_upper], fmt='o', alpha=0.5, label='BMD_U/L Error (95% CI)',
                 color='green',
                 markersize=0.2)
    plt.plot([y_actual.min(), y_actual.max()], [y_actual.min(), y_actual.max()], 'r--', label='Prediction')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()

    return plt
