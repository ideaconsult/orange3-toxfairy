import os
import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QGridLayout, QFileDialog
import copy
from PyQt5.QtWidgets import QListWidget
from orangewidget.settings import Setting
from .data_view import DataViewHandler


class CombineHTSObj(OWWidget):
    name = "Combine HTS Objects"
    description = "Combine HTS Objects"
    icon = "icons/print.svg"

    class Inputs:
        data_container1 = Input("Data dictionary 1", dict, auto_summary=False)  # if used for combining +- serum, +serum
        data_container2 = Input("Data dictionary 2", dict, auto_summary=False)  # if used for combining +- serum, -serum

    class Outputs:
        data_container_output = Output("Data dictionary", dict, auto_summary=False)

    radioBtnSelection = Setting(0, schema_only=True)

    def __init__(self):
        super().__init__()
        self.data_container1 = None
        self.data_container2 = None
        self.data_container_copy = None
        self.endpoints1 = []
        self.endpoints2 = []

        box = gui.widgetBox(self.controlArea, self.name)
        gui.radioButtonsInBox(box, self, 'radioBtnSelection',
                              btnLabels=['Combine by different materials', 'Combine +/- serum used'],
                              tooltips=['Use this option for .....', 'Use this option for .....'],
                              callback=self.engine)

        # ---------------------------------------- Main area -----------------------------------------------------------
        self.mainBox = gui.widgetBox(self.mainArea, 'Data view')
        self.data_view_handler = DataViewHandler(self.mainBox)
        self.data_view_handler.dataframes_available_dict = {'Normalized': 'normalized_df',
                                                            'Mean': 'mean_df',
                                                            'Median': 'median_df',
                                                            'Dose-response': 'dose_response_df'}

    @Inputs.data_container1
    def set_data_container1(self, data_container):
        if data_container:
            self.data_container1 = data_container
            self.endpoints1 = list(self.data_container1.keys())
            # self.data_container_copy = copy.deepcopy(self.data_container1)
        else:
            self.data_container1 = None

    @Inputs.data_container2
    def set_data_container2(self, data_container):
        if data_container:
            self.data_container2 = data_container
            self.endpoints2 = list(self.data_container2.keys())
            # self.data_container_copy = copy.deepcopy(self.data_container1)
        else:
            self.data_container2 = None

    def engine(self):
        if self.radioBtnSelection == 0:
            self.combine_by_diff_marials()
        else:
            self.combine_by_serum_used()

    def combine_by_diff_marials(self):
        print('combine by diff materials')
        if self.data_container1 and self.data_container2:
            for key, obj in self.data_container1.items():
                df_combined = pd.concat([obj[0].dose_response_df, self.data_container2[key][0].dose_response_df])
                df_combined = df_combined.drop(['water'])
                obj[0].dose_response_df = df_combined
                self.Outputs.data_container_output.send(self.data_container1)

                self.view_data()
        else:
            print('No data')

    def combine_by_serum_used(self):
        print('combine by serum used')
        if self.data_container1 and self.data_container2:
            for key, obj in self.data_container1.items():
                obj[0].dose_response_df.columns = [col.replace('MAX', 'MAX_ws')
                                                       .replace('AUC', 'AUC_ws')
                                                       .replace('2SD', '2SD_ws')
                                                       .replace('3SD', '3SD_ws')
                                                   for col in obj[0].dose_response_df.columns]
                df_combined = pd.concat([obj[0].dose_response_df, self.data_container2[key][0].dose_response_df], axis=1)
                obj[0].dose_response_df = df_combined

            self.Outputs.data_container_output.send(self.data_container1)
            self.view_data()

    def view_data(self):
        self.data_view_handler.data = self.data_container1
        self.data_view_handler.setup_ui()
        self.view()

    def view(self):
        self.data_view_handler.view()

    def save_table(self):
        self.data_view_handler.save_table()


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(CombineHTSObj).run()
