from dataclasses import dataclass, field
import pandas as pd
from typing import List, Optional


@dataclass()
class HTS:
    endpoint: Optional[str] = field(default=None)
    serum_used: bool = False
    assay_type: Optional[str] = field(default=None)
    _metadata: dict = field(default_factory=dict)
    _water_keys: List[str] = field(default_factory=list)
    raw_data_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    normalized_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    mean_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    median_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    dose_response_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        if self.endpoint is not None:
            self.endpoint = self.endpoint.upper()

        if self.assay_type is not None and self.assay_type not in {"imaging", "viability"}:
            raise ValueError(f"Invalid assay_type: {self.assay_type}. Allowed values are 'imaging' or 'viability'.")

    @property
    def metadata(self):
        self._update_metadata_and_water_keys()
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value
        # self._update_metadata_and_water_keys()

    @property
    def water_keys(self):
        self._update_metadata_and_water_keys()
        return self._water_keys

    @water_keys.setter
    def water_keys(self, value):
        self._water_keys = value
        # self._update_metadata_and_water_keys()

    def _update_metadata_and_water_keys(self):
        """Update metadata and water_keys based on raw_data_df columns."""
        if self.raw_data_df.empty or not self._metadata or not self._water_keys:
            return

        keys_to_keep = list(self.raw_data_df.columns)[3:]
        self._metadata = {key: value for key, value in self._metadata.items() if key in keys_to_keep}
        self._water_keys = [item for item in self._water_keys if item in keys_to_keep]

    def filtrate_data(self, df, materials: List[str] = None, cells: List[str] = None):
        if materials is None:
            materials = []
        if cells is None:
            cells = []

        self.metadata = {key: value for key, value in self.metadata.items()
                         if not materials or value.get('material') in materials or key in self.water_keys}

        if df is self.raw_data_df or df is self.normalized_df:
            if 'Description' in df.columns:
                columns_to_keep = ['cells', 'replicates', 'time', 'Description'] + list(self.metadata.keys())
            else:
                columns_to_keep = ['cells', 'replicates', 'time'] + list(self.metadata.keys())

            columns_to_keep = [col for col in columns_to_keep if col in df.columns]

            filtered_df = df[columns_to_keep]
            if cells:
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
            if cells:
                filtered_df = filtered_df[filtered_df.index.str.split('_').str[0].isin(cells)]
            if df is self.mean_df:
                self.mean_df = filtered_df
            else:
                self.median_df = filtered_df

        elif df is self.dose_response_df:
            mask_dose_resp_materials = df.index.isin(materials)
            filtered_df = df[mask_dose_resp_materials]
            if cells:
                mask_dose_resp_cells = filtered_df.columns.str.contains('|'.join(cells))
                filtered_df = filtered_df.loc[:, mask_dose_resp_cells]
            self.dose_response_df = filtered_df
