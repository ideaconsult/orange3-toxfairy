from dataclasses import dataclass, field
import pandas as pd
from typing import List


@dataclass()
class HTS:
    endpoint: str
    metadata: dict = field(default_factory=dict)
    water_keys: List[str] = field(default_factory=list)
    raw_data_df: pd.DataFrame = pd.DataFrame()
    normalized_df: pd.DataFrame = pd.DataFrame()
    mean_df: pd.DataFrame = pd.DataFrame()
    median_df: pd.DataFrame = pd.DataFrame()
    dose_response_df: pd.DataFrame = pd.DataFrame()
