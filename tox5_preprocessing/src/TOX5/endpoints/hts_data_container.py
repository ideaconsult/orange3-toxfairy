from dataclasses import dataclass, field
import pandas as pd
from typing import List, Optional


@dataclass()
class HTS:
    endpoint: Optional[str] = field(default=None)
    serum_used: bool = False
    metadata: dict = field(default_factory=dict)
    water_keys: List[str] = field(default_factory=list)
    raw_data_df: pd.DataFrame = pd.DataFrame()
    normalized_df: pd.DataFrame = pd.DataFrame()
    mean_df: pd.DataFrame = pd.DataFrame()
    median_df: pd.DataFrame = pd.DataFrame()
    dose_response_df: pd.DataFrame = pd.DataFrame()

    def __post_init__(self):
        if self.endpoint is not None:
            self.endpoint = self.endpoint.upper()

    def filtrate_data(self, df, materials: List[str] = None, cells: List[str] = None):
        self.metadata = {key: value for key, value in self.metadata.items()
                         if value.get('material') in materials or key in self.water_keys}

        if df is self.raw_data_df or df is self.normalized_df:
            if 'Description' in df.columns:
                columns_to_keep = ['cells', 'replicates', 'time', 'Description'] + list(self.metadata.keys())
            else:
                columns_to_keep = ['cells', 'replicates', 'time'] + list(self.metadata.keys())

            columns_to_keep = [col for col in columns_to_keep if col in df.columns]

            filtered_df = df[columns_to_keep]
            mask_data_cells = filtered_df['cells'].isin(cells)
            filtered_df = filtered_df[mask_data_cells]
            filtered_df.reset_index(drop=True, inplace=True)

            if df is self.raw_data_df:
                self.raw_data_df = filtered_df
            else:
                self.normalized_df = filtered_df
        elif df is self.mean_df or df is self.median_df:
            columns_to_keep = list(self.metadata.keys())
            columns_to_keep = [col for col in columns_to_keep if col in df.columns]
            filtered_df = df[columns_to_keep]
            filtered_df = filtered_df[filtered_df.index.str.split('_').str[0].isin(cells)]
            if df is self.mean_df:
                self.mean_df = filtered_df
            else:
                self.median_df = filtered_df

        elif df is self.dose_response_df:
            mask_dose_resp_materials = df.index.isin(materials)
            filtered_df = df[mask_dose_resp_materials]
            mask_dose_resp_cells = filtered_df.columns.str.contains('|'.join(cells))
            filtered_df = filtered_df.loc[:, mask_dose_resp_cells]
            self.dose_response_df = filtered_df
