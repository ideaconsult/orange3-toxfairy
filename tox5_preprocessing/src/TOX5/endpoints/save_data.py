import pandas as pd


class SaveData:

    def __init__(self):
        self.df = pd.DataFrame()
        self.normalized_df = pd.DataFrame()
        self.mean_df = pd.DataFrame()
        self.median_df = pd.DataFrame()
        self.dose_response_df = pd.DataFrame()

