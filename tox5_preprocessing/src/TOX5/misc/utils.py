import pandas as pd


def add_annot_data(df, material, concentration, code):
    material_df = pd.Series(material, index=df.columns).to_frame().T.rename(index={0: 'material'})
    concentration_df = pd.Series(concentration, index=df.columns).to_frame().T.rename(index={0: 'concentration'})
    code_df = pd.Series(code, index=df.columns).to_frame().T.rename(index={0: 'code'})

    df = pd.concat([df, material_df, concentration_df, code_df])
    return df


def insert_columns(df, column_names, *arrays):
    for i, column in enumerate(column_names):
        df.insert(loc=i, column=column, value=arrays[i])


def add_endpoint_parameters(df, replicates, times, cells):
    df.insert(loc=0, column='replicate', value=replicates)
    df.insert(loc=1, column='time', value=times)
    df.insert(loc=2, column='cells', value=cells)

