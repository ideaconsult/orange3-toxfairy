from pymcdm.methods import TOPSIS
from pymcdm.helpers import rrankdata, rankdata
from pymcdm.helpers import normalize_matrix
import numpy as np


def topsis_scoring(df):
    data = df
    data.set_index('material', inplace=True)
    # check for NaN values
    columns_with_nan = data.columns[data.isna().any()].tolist()
    if columns_with_nan:
        # Logic to fill NaN values:
        # 1st NaN values will be fill with 9999 based on idea that high value mean low toxic effect
        # AUC NAN values will be fill with 0 based on idea that low value mean low overall effect
        columns_to_process = data.columns[data.columns.str.contains('1st') | df.columns.str.contains('AUC')]
        data[columns_to_process] = data[columns_to_process].fillna(
            {col: 9999 if '1st' in col else 0 for col in columns_to_process})

    matrix = data.values
    # Set rule based criteria
    # Maximization (1): A higher value is better (indicating lower toxicity or a less harmful effect).
    # Minimization (-1): A lower value is better (indicating higher toxicity or a more harmful effect).
    criteria = []
    for col in data.columns:
        if '1st' in col:
            criteria.append(1)
        elif 'AUC' in col or 'MAX' in col:
            criteria.append(-1)

    if len(criteria) != matrix.shape[1]:
        raise ValueError(
            f"The number of criteria ({len(criteria)}) does not match the number of columns ({matrix.shape[1]})")

    criteria = np.array(criteria)
    # weights = np.ones(len(criteria)) / len(criteria)
    # Set weights
    weights = np.ones(len(criteria))  # Initialize with 1 for all criteria
    for i, col in enumerate(data.columns):
        if '1st_3SD' in col:
            weights[i] = 3  # Set weight to 3 for columns containing '1st_3SD'

    # Normalize weights to sum to 1
    # With normalization, each criterion’s weight represents its proportionate importance.
    weights = weights / weights.sum()

    # Create TOPSIS object
    topsis = TOPSIS()
    preferences = topsis(matrix, weights, criteria)

    # ranking = rrankdata(preferences)
    ranking = rankdata(preferences)

    data['Preference'] = preferences
    data['Ranking'] = ranking
    ranked = data[['Preference', 'Ranking']]
    sorted_df = ranked.sort_values(by='Ranking', ascending=True)

    return sorted_df
