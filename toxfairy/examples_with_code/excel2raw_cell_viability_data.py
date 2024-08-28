import pandas as pd
import re
import os

file = 'D:\\PhD\\projects\\ToxPi\\tox_data\\calibrate\\from_patrols\\nanodata-patrols\\misvik\\Patrols_HepG2_A549_Beas2b_HTS_data_Misvik.xlsx'

sheet_name = 'Apoptosis data'
# sheet_name = 'Cell viability data '

raw_data_df = pd.read_excel(file, skiprows=2, usecols="A, D:AM", engine='openpyxl', sheet_name=sheet_name)
print(raw_data_df)

raw_data_df['row'] = raw_data_df['well'].apply(lambda x: re.match(r"([A-Za-z]+)([0-9]+)", x).groups()[0])
raw_data_df['column'] = raw_data_df['well'].apply(lambda x: re.match(r"([A-Za-z]+)([0-9]+)", x).groups()[1])
save_dir = 'D:\\PhD\\projects\\ToxPi\\tox_data\\patrols\\cell_viability_custom'
for col in raw_data_df.columns[1:-2]:
    matrix_df = raw_data_df.pivot(index='row', columns='column', values=col)
    file_path = os.path.join(save_dir, f'{col}.csv')
    matrix_df.to_csv(file_path)
