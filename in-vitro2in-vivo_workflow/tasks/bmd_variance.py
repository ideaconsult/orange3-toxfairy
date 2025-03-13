import pandas as pd
import os.path

# + tags=["parameters"]
upstream = []
product = None
in_vivo_folder = None
# -


def estimate_variance(bmd_upper, bmd_lower):
    std_dev = (bmd_upper - bmd_lower) / 3.92
    variance = std_dev ** 2
    return variance


os.makedirs(product["bmd_variance"], exist_ok=True)

in_vivo_df = pd.read_excel(in_vivo_folder)
columns_to_keep = ['ParticleID', 'Day', 'CellType', 'BMD_SD1', 'BMDL_SD1', 'BMDU_SD1', 'BMD_SD2',
                   'BMDL_SD2', 'BMDU_SD2']
filtered_df = in_vivo_df[columns_to_keep]
filtered_df['variance_BMD_SD1'] = estimate_variance(filtered_df['BMDU_SD1'], filtered_df['BMDL_SD1'])
filtered_df['variance_BMD_SD2'] = estimate_variance(filtered_df['BMDU_SD2'], filtered_df['BMDL_SD2'])
filtered_df = filtered_df.drop([
    # 'ParticleID',
    'BMD_SD1', 'BMDL_SD1', 'BMDU_SD1', 'BMD_SD2', 'BMDL_SD2', 'BMDU_SD2'
], axis=1)

df_clean_nan = filtered_df.dropna()

file_name = os.path.join(product["bmd_variance"], "bmd_variance.csv")
df_clean_nan.to_csv(file_name, index=False)
print()

