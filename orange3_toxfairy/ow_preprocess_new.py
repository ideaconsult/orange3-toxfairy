import os
import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QGridLayout, QFileDialog
import copy
from PyQt5.QtWidgets import QListWidget
from orangewidget.settings import Setting
from .data_view import DataViewHandler
from toxfairy.calculations.cell_viability_normalization import CellViabilityNormalization
from toxfairy.calculations.dna_damage_normalization import DNADamageNormalization
from toxfairy.endpoints.hts_data_container import HTS
from toxfairy.calculations.dose_response import DoseResponse
from toxfairy.calculations.basic_normalization import BasicNormalization


class HTSPreprocess(OWWidget):
    name = "HTS preprocess"
    description = "HTS data preprocessing and calculation of dose-response parameters"
    icon = "icons/print.svg"

    class Inputs:
        data_container = Input("Data dictionary", dict, auto_summary=False)

    class Outputs:
        data_container_output = Output("Data dictionary", dict, auto_summary=False)

    endpoint = Setting([])
    endpoint_ = Setting(0)

    remove_out = Setting(True, schema_only=True)
    med_control = Setting(True, schema_only=True)
    eff_med_control = Setting(True, schema_only=True)
    sub_bl = Setting(True, schema_only=True)
    sub_bl_percent = Setting(True, schema_only=True)
    casp_clean_ = Setting(False, schema_only=True)
    mean_median = Setting(True, schema_only=True)
    clean_dna = Setting(True, schema_only=True)
    dose = Setting(True, schema_only=True)
    combine = Setting(False, schema_only=True)

    def __init__(self):
        super().__init__()
        self.data_container = None
        self.data_container_copy = None
        self.tech_replicate = ''
        self.tech_replicate_items = []

        # ---------------------------------- control area ------------------------------------------------------------
        self.layout = QGridLayout()
        gui.widgetBox(self.controlArea, 'Tox5', orientation=self.layout)

        self.radioBtnSelection = None
        self.endpoints = gui.listBox(None, self, 'endpoint_', callback=self.load_available_btns)
        self.layout.addWidget(self.endpoints, 0, 0, 4, 1)

        self.box2 = gui.widgetBox(None, 'Normalizations')

        self.clean_dna_ = gui.checkBox(self.box2, self, 'clean_dna', 'Remove failed images',
                                       callback=self.save_checked_btn,
                                       tooltip='for all 0 DAPI results: remove results for 8OHG + H2AX '
                                               'if DAPI is 0 and remove result for DAPI if imaging is failed '
                                               '(median for DAPI replicates are more than 50)')
        self.clean_dna_.setObjectName('clean_dna')

        self.remove_outliers = gui.checkBox(self.box2, self, 'remove_out', 'Remove outliers',
                                            callback=self.save_checked_btn,
                                            tooltip='removing  dispersant outliers based on first and '
                                                    'third quantiles and replacing the value with NaN')
        self.remove_outliers.setObjectName('remove')
        self.median_control = gui.checkBox(self.box2, self, 'med_control', 'Percent of control',
                                           callback=self.save_checked_btn)
        self.median_control.setObjectName('median_control')

        self.effect_median_control = gui.checkBox(self.box2, self, 'eff_med_control', 'Percent effect of control',
                                                  callback=self.save_checked_btn)
        self.effect_median_control.setObjectName('effect_median_control')

        self.subtract_blanks = gui.checkBox(self.box2, self, 'sub_bl', 'Baseline correction',
                                            callback=self.save_checked_btn)
        self.subtract_blanks.setObjectName('subtract')

        self.subtract_blanks_percent = gui.checkBox(self.box2, self, 'sub_bl_percent', 'Baseline correction as percent',
                                                    callback=self.save_checked_btn)
        self.subtract_blanks_percent.setObjectName('subtract_as_percent')

        self.casp_clean = gui.checkBox(self.box2, self, 'casp_clean_', 'Normalize Caspase to cell amount',
                                       callback=self.save_checked_btn,
                                       tooltip='based on CTG and DAPI normalization')
        self.casp_clean.setObjectName('casp_clean')

        self.calc_mean_median = gui.checkBox(self.box2, self, 'mean_median', 'Mean and Median of replicates',
                                             callback=self.save_checked_btn)
        self.calc_mean_median.setObjectName('mean_median')

        self.button_norm = gui.button(None, self, f'Normalize', autoDefault=False, callback=self.normalize)

        self.box3 = gui.widgetBox(None, 'Technical replicates')
        self.toggle_button = gui.checkBox(self.box3, self, "combine", "Combine technical replicates",
                                          callback=self.toggle_combine)
        self.combine_tr = gui.listBox(None, self, "tech_replicate",
                                      selectionMode=QListWidget.MultiSelection,
                                      callback=self.add_selected_multi_cell_lines)
        self.combine_tr.setFixedHeight(50)

        self.box4 = gui.widgetBox(None, 'Dose - response')
        self.dr_params = gui.checkBox(self.box4, self, 'dose', 'Dose - response')
        self.dr_params.setObjectName('dr_param')

        self.button = gui.button(None, self, f'Preprocess', autoDefault=False, callback=self.preprocess)

        self.remove_outliers.setVisible(False)
        self.subtract_blanks.setVisible(False)
        self.subtract_blanks_percent.setVisible(False)
        self.median_control.setVisible(False)
        self.effect_median_control.setVisible(False)
        self.calc_mean_median.setVisible(False)
        self.clean_dna_.setVisible(False)
        self.casp_clean.setVisible(False)

        self.layout.addWidget(self.box2, 0, 1)
        self.layout.addWidget(self.button_norm, 1, 1)
        self.layout.addWidget(self.box3, 2, 1)
        self.layout.addWidget(self.box4, 3, 1)
        self.layout.addWidget(self.button, 4, 0, 1, 2)

        self.rules = {'viability': [self.remove_outliers, self.median_control, self.effect_median_control,
                                    self.subtract_blanks, self.subtract_blanks_percent,
                                    self.calc_mean_median, self.casp_clean],
                      'imaging': [self.clean_dna_, self.remove_outliers, self.median_control,
                                  self.effect_median_control,
                                  self.calc_mean_median]}

        self.checked_btn = {}
        self.toggle_combine()

        # ---------------------------------------- Main area -----------------------------------------------------------
        self.mainBox = gui.widgetBox(self.mainArea, 'Data view')
        self.data_view_handler = DataViewHandler(self.mainBox)
        self.data_view_handler.dataframes_available_dict = {'Normalized': 'normalized_df',
                                                            'Mean': 'mean_df',
                                                            'Median': 'median_df',
                                                            'Dose-response': 'dose_response_df'}

    @Inputs.data_container
    def set_data_container(self, data_container):
        if data_container:
            self.data_container = data_container
            self.endpoint = list(self.data_container.keys())
            self.endpoints.clear()
            self.endpoint_ = 0
            self.endpoints.addItems(self.endpoint)

            self.data_container_copy = copy.deepcopy(self.data_container)
            """
                create dict with key for each available endpoint and set empty dict to store checked btn's
            """
            self.checked_btn = {key: {} for key in self.endpoint}

            for endpoint in self.endpoint:
                endpoint_states = {}
                for button in self.rules[self.data_container_copy[endpoint][0].assay_type]:
                    button_name = button.objectName()
                    endpoint_states[button_name] = button.isChecked()
                self.checked_btn[endpoint] = endpoint_states
            self.load_available_btns()

            self.combine_tr.clear()
            self.combine_tr.addItems(self.endpoint)

            self.tech_replicate = [0]
            self.add_selected_multi_cell_lines()
        else:
            self.data_container = None

    def load_available_btns(self):
        """
            set available btn's with actual state  for each selected endpoint
            the actual state is taken from self.checked_btn dict for selected endpoint
        """
        if self.endpoint_ is not None:
            selected_endpoint = self.endpoint[self.endpoint_]
            self.button_norm.setText(f'Normalize {selected_endpoint}')

            self.remove_outliers.setVisible(False)
            self.subtract_blanks.setVisible(False)
            self.subtract_blanks_percent.setVisible(False)
            self.median_control.setVisible(False)
            self.effect_median_control.setVisible(False)
            self.calc_mean_median.setVisible(False)
            self.clean_dna_.setVisible(False)
            self.casp_clean.setVisible(False)

            assay_type = self.data_container_copy[selected_endpoint][0].assay_type
            for btn in self.rules[assay_type]:
                btn.setVisible(True)
                button_id = btn.objectName()
                btn.setChecked(self.checked_btn[selected_endpoint].get(button_id, False))

    def save_checked_btn(self):
        """
            save actual state for each btn in self.checked_btn dict for selected endpoint
        """
        button_id = self.sender().objectName()
        button_state = self.sender().isChecked()
        self.save_button_state(button_id, button_state)

        # # TODO: uncheck button if another checked (median control, baseline corrections)
        # if button_id == 'effect_median_control' and self.median_control.isChecked():
        #     self.median_control.setChecked(False)
        #     self.save_button_state(self.median_control.objectName(), self.median_control.isChecked())
        #
        # if button_id == 'median_control' and self.effect_median_control.isChecked():
        #     self.effect_median_control.setChecked(False)
        #     self.save_button_state(self.effect_median_control.objectName(), self.effect_median_control.isChecked())

    def save_button_state(self, button_id, state):
        self.checked_btn[self.endpoint[self.endpoint_]][button_id] = state

    def function_map(self, selected_endpoint, todo):
        if todo == "remove":
            self.data_container_copy[selected_endpoint][1].remove_outliers_by_quantiles()
        elif todo == 'clean_dna':
            self.data_container_copy[selected_endpoint][1].clean_dna_raw()
        elif todo == 'median_control':
            self.data_container_copy[selected_endpoint][1].percentage_of_median_control(
                self.data_container_copy[selected_endpoint][0].normalized_df)
        elif todo == 'effect_median_control':
            self.data_container_copy[selected_endpoint][1].percentage_effect_from_median_control(
                self.data_container_copy[selected_endpoint][0].normalized_df)
        elif todo == 'subtract':
            self.data_container_copy[selected_endpoint][1].subtract_blank(
                self.data_container_copy[selected_endpoint][0].normalized_df)
        elif todo == "subtract_as_percent":
            self.data_container_copy[selected_endpoint][1].subtract_blank_as_percent(
                self.data_container_copy[selected_endpoint][0].normalized_df)
        elif todo == 'mean_median':
            self.data_container_copy[selected_endpoint][1].calc_mean_median()
        elif todo == 'casp_clean':
            self.data_container_copy[selected_endpoint][1].ctg_mean_df = self.data_container_copy['CTG'][0].mean_df
            self.data_container_copy[selected_endpoint][1].dapi_mean_df = self.data_container_copy['DAPI'][0].mean_df
            self.data_container_copy[selected_endpoint][1].normalize_data_to_cell_count(
                self.data_container_copy['CTG'][0].mean_df,
                self.data_container_copy['DAPI'][0].mean_df)
        else:
            print('no available function')

    def normalize(self):
        selected_endp = self.endpoint[self.endpoint_]
        self.data_container_copy[selected_endp] = copy.deepcopy(self.data_container[selected_endp])
        self.create_hts_calc_objects(selected_endp)

        for func, isAvailable in self.checked_btn[selected_endp].items():
            if isAvailable:
                self.function_map(selected_endp, func)

        self.Outputs.data_container_output.send(self.data_container_copy)

        self.view_data()

    def preprocess(self):
        if self.combine:
            common_part = os.path.commonprefix(self.tech_replicate_items)
            combined_hts_obj = self.combine_hts_object(self.data_container_copy[self.tech_replicate_items[0]][0],
                                                       self.data_container_copy[self.tech_replicate_items[1]][0],
                                                       common_part)
            del self.data_container_copy[self.tech_replicate_items[0]]
            del self.data_container_copy[self.tech_replicate_items[1]]

            self.data_container_copy[common_part] = [combined_hts_obj]
            self.data_container_copy[common_part].append(
                DNADamageNormalization(self.data_container_copy[common_part][0]))
            self.data_container_copy[common_part].append(DoseResponse(self.data_container_copy[common_part][0]))

        for key, value in self.data_container_copy.items():
            value[2].dose_response_parameters()

        self.Outputs.data_container_output.send(self.data_container_copy)

        self.view_data()

    def create_hts_calc_objects(self, selected_endp):
        if self.data_container_copy[selected_endp][0].assay_type == 'viability':
            self.data_container_copy[selected_endp].append(
                CellViabilityNormalization(self.data_container_copy[selected_endp][0]))
        elif self.data_container_copy[selected_endp][0].assay_type == 'imaging':
            self.data_container_copy[selected_endp].append(
                DNADamageNormalization(self.data_container_copy[selected_endp][0]))

        self.data_container_copy[selected_endp].append(DoseResponse(self.data_container_copy[selected_endp][0]))

    def toggle_combine(self):
        if self.combine:
            self.box3.layout().addWidget(self.combine_tr)
        else:
            self.combine_tr.setParent(None)

    def add_selected_multi_cell_lines(self):
        self.tech_replicate_items = [item.text() for item in self.combine_tr.selectedItems()]

    @staticmethod
    def combine_hts_object(hts_obj1: HTS, hts_obj2: HTS, endpoint_name: str) -> HTS:
        combined_df = pd.concat(
            [hts_obj1.normalized_df.groupby(['replicates', 'time', 'cells']).mean(),
             hts_obj2.normalized_df.groupby(['replicates', 'time', 'cells']).mean()]
        )

        average_df = combined_df.groupby(['replicates', 'time', 'cells']).mean()
        average_df.reset_index(inplace=True)

        hts_obj1.normalized_df = average_df
        hts_obj1.endpoint = endpoint_name
        normalizer = BasicNormalization(hts_obj1)
        normalizer.calc_mean_median()

        return hts_obj1

    def view_data(self):
        self.data_view_handler.data = self.data_container_copy
        self.data_view_handler.setup_ui()
        self.view()

    def view(self):
        self.data_view_handler.view()

    def save_table(self):
        self.data_view_handler.save_table()


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(HTSPreprocess).run()
