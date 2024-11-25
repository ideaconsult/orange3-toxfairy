import os
from pathlib import Path

import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QGridLayout, QFileDialog
import copy
from PyQt5.QtWidgets import QListWidget
from orangewidget.settings import Setting
from .data_view import DataViewHandler
from toxfairy.misc.hts2nexus import hts2df, add_to_nxs


class HTS2NXS(OWWidget):
    name = "Convert HTS processed data to Nexus file format"
    description = "Convert HTS processed data to Nexus file format"
    icon = "icons/print.svg"

    class Inputs:
        data_container = Input("Data dictionary", dict, auto_summary=False)

    substance_owner = Setting('', schema_only=True)
    data_provider = Setting('', schema_only=True)
    filename = Setting('', schema_only=True)

    def __init__(self):
        super().__init__()
        self.data_container = None
        self.data_container_copy = None
        self.melted_data = {
            'raw': {},
            'normalized': {},
            'median': {},
            'dose-response': {}
        }
        self.save_directory = ""

        box = gui.widgetBox(self.controlArea, self.name)
        self.substance_owner_label = gui.label(box, self, 'Enter substance owner:')
        self.substance_owner_line = gui.lineEdit(box, self, 'substance_owner')
        self.data_provider_label = gui.label(box, self, 'Enter data provider:')
        self.data_provider_line = gui.lineEdit(box, self, 'data_provider')
        # Directory selection button
        self.save_directory_button = gui.button(box, self, "Choose Save Directory", callback=self.select_save_directory)

        # Label to show selected directory
        self.save_directory_label = gui.label(box, self, 'Selected Directory: Not set')
        self.filename_label = gui.label(box, self, 'Enter filename:')
        self.filename_line_edit = gui.lineEdit(box, self, 'filename')

        self.convert2nxs_btn = gui.button(box, self, "Convert to Nexus file", callback=self.add2nexus)
        self.resulting_msg = gui.label(box, self, 'Resulting message: Not ready')

    @Inputs.data_container
    def set_data_container(self, data_container):
        if data_container:
            self.data_container = data_container
            self.data_container_copy = copy.deepcopy(self.data_container)
            # self.endpoints = list(self.data_container.keys())
            # self.data_container_copy = copy.deepcopy(self.data_container1)
        else:
            self.data_container = None

    def select_save_directory(self):
        """
        Opens a dialog to select a directory and stores the path.
        """
        # Open a directory chooser dialog
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")

        if directory:  # If a directory is selected
            self.save_directory = directory
            print(self.save_directory)
            self.save_directory_label.setText(f'Selected Directory: {directory}')
        else:
            self.save_directory_label.setText('Selected Directory: Not set')

    def create_melted_dfs(self):
        for key_endpoint, obj in self.data_container_copy.items():
            data_obj = obj[0]
            endpoint = data_obj.endpoint

            if data_obj.raw_data_df is not None:
                res_raw_data = hts2df(data_obj.raw_data_df, data_obj.metadata, endpoint, 'raw_data')
                self.melted_data['raw'][key_endpoint] = res_raw_data

            if data_obj.normalized_df is not None:
                res_norm_data = hts2df(data_obj.normalized_df, data_obj.metadata, endpoint, 'normalized_data')
                self.melted_data['normalized'][key_endpoint] = res_norm_data

            if data_obj.median_df is not None:
                res_median_data = hts2df(data_obj.median_df, data_obj.metadata, endpoint, 'median_data')
                self.melted_data['median'][key_endpoint] = res_median_data

            if data_obj.dose_response_df is not None:
                res_dose_response_data = hts2df(data_obj.dose_response_df, data_obj.metadata, endpoint,
                                                'dose_response_data')
                self.melted_data['dose-response'][key_endpoint] = res_dose_response_data

    def add2nexus(self):
        nexus_file = Path(self.save_directory) / f"{self.filename_line_edit.text()}.nxs"
        self.create_melted_dfs()
        add_to_nxs(nexus_file, self.substance_owner_line.text(), self.data_provider_line.text(), self.melted_data)
        self.resulting_msg.setText(f'Resulting message: Nexus file is saved in  {nexus_file}')


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(HTS2NXS).run()
