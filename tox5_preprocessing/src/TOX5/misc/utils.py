import pandas as pd


def add_annot_data(df, material, concentration, code):
    return df.append(pd.Series(material, index=df.columns, name='material')) \
        .append(pd.Series(concentration, index=df.columns, name='concentration')) \
        .append(pd.Series(code, index=df.columns, name='code'))


def insert_columns(df, column_names, *arrays):
    for i, column in enumerate(column_names):
        df.insert(loc=i, column=column, value=arrays[i])


def add_endpoint_parameters(df, replicates, times, cells):
    df.insert(loc=0, column='replicate', value=replicates)
    df.insert(loc=1, column='time', value=times)
    df.insert(loc=2, column='cells', value=cells)

