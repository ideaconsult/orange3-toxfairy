import pandas as pd 
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from pathlib import Path


# + tags=["parameters"]
upstream = ["preprocessing"]
product = None
dataset = None
label = None
# -


Path(product["numeric_file"]).parent.mkdir(parents=True, exist_ok=True)


def create_pipeline(X, categorical_cols = ['cell', 'assay', 'CellType']):
    numerical_cols = X.columns.difference(categorical_cols)  # Other numeric features
    return ColumnTransformer([
        ('cat', OrdinalEncoder(), categorical_cols),
        #('num', StandardScaler(), numerical_cols)  # Scale numerical features
    ],  remainder='passthrough')

categorical_cols = ['cell', 'assay', 'CellType']
df = pd.read_excel(upstream["preprocessing"][dataset])
df['text'] = df[categorical_cols].fillna("").astype(str).agg(' '.join, axis=1)
df['text'].to_csv(product["text_file"], index=False)
df[label].to_csv(product["labels_file"], index=False)

df.head()
X_num = df.drop(columns=['material', 'BMD_SD1', 'BMDL_SD1', 'BMDU_SD1','text','cell', 'assay', 'CellType'])
X_num.to_csv(product["numeric_file"], index=False)

pipeline = create_pipeline(df[categorical_cols], categorical_cols)
X_transformed = pipeline.fit_transform(df[categorical_cols])

X_transformed_df = pd.DataFrame(X_transformed, columns=categorical_cols)
X_transformed_df.to_csv(product["categorical_file"], index=False)