import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QGridLayout, QFileDialog
import copy
from orangewidget.settings import Setting
from orange3_toxfairy.data_view import DataViewHandler

from toxfairy.src.toxfairy.calculations.cell_viability_normalization import CellViabilityNormalization
from toxfairy.src.toxfairy.calculations.dna_damage_normalization import DNADamageNormalization
from toxfairy.src.toxfairy.endpoints.hts_data_container import HTS
from toxfairy.src.toxfairy.calculations.dose_response import DoseResponse
from toxfairy.src.toxfairy.calculations.basic_normalization import BasicNormalization


class Toxpi(OWWidget):
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
    sub_bl = Setting(True, schema_only=True)
    casp_clean_ = Setting(False, schema_only=True)
    mean_median = Setting(True, schema_only=True)
    clean_dna = Setting(True, schema_only=True)
    dose = Setting(True, schema_only=True)

    def __init__(self):
        super().__init__()
        self.data_container = None
        self.data_container_copy = None

        # ---------------------------------- control area ------------------------------------------------------------
        self.layout = QGridLayout()
        gui.widgetBox(self.controlArea, 'Tox5', orientation=self.layout)

        self.radioBtnSelection = None
        self.endpoints = gui.listBox(None, self, 'endpoint_', callback=self.load_available_btns)
        self.layout.addWidget(self.endpoints, 0, 0, 2, 1)

        self.box2 = gui.widgetBox(None, 'Normalizations')

        self.clean_dna_ = gui.checkBox(self.box2, self, 'clean_dna', 'Clean DAPI data',
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
        self.subtract_blanks = gui.checkBox(self.box2, self, 'sub_bl', 'Baseline correction',
                                            callback=self.save_checked_btn)
        self.subtract_blanks.setObjectName('subtract')

        self.casp_clean = gui.checkBox(self.box2, self, 'casp_clean_', 'Normalize Casp to cell amount',
                                       callback=self.save_checked_btn,
                                       tooltip='based on CTG and DAPI normalization')
        self.casp_clean.setObjectName('casp_clean')

        self.calc_mean_median = gui.checkBox(self.box2, self, 'mean_median', 'Mean and Median of replicates',
                                             callback=self.save_checked_btn)
        self.calc_mean_median.setObjectName('mean_median')

        self.box3 = gui.widgetBox(None, 'Dose - response')
        self.dr_params = gui.checkBox(self.box3, self, 'dose', 'Dose - response', callback=self.save_checked_btn)
        self.dr_params.setObjectName('dr_param')

        self.button = gui.button(None, self, f'Preprocess', autoDefault=False, callback=self.process)

        self.remove_outliers.setVisible(False)
        self.subtract_blanks.setVisible(False)
        self.median_control.setVisible(False)
        self.calc_mean_median.setVisible(False)
        self.clean_dna_.setVisible(False)
        self.casp_clean.setVisible(False)

        self.layout.addWidget(self.box2, 0, 1)
        self.layout.addWidget(self.box3, 1, 1)
        self.layout.addWidget(self.button, 2, 0, 1, 2)

        self.rules = {'CTG': [self.remove_outliers, self.median_control, self.subtract_blanks,
                              self.calc_mean_median, self.dr_params],
                      'CASP': [self.remove_outliers, self.median_control, self.subtract_blanks,
                               self.casp_clean, self.calc_mean_median, self.dr_params],
                      'DAPI': [self.clean_dna_, self.remove_outliers, self.median_control,
                               self.calc_mean_median, self.dr_params],
                      '8OHG': [self.clean_dna_, self.remove_outliers, self.median_control,
                               self.calc_mean_median, self.dr_params],
                      'H2AX': [self.clean_dna_, self.remove_outliers, self.median_control,
                               self.calc_mean_median, self.dr_params]}

        self.checked_btn = {}

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

            for endpoint, buttons in self.rules.items():
                endpoint_states = {}
                if endpoint in self.endpoint:
                    for button in buttons:
                        button_name = button.objectName()
                        endpoint_states[button_name] = button.isChecked()
                    self.checked_btn[endpoint] = endpoint_states

            self.load_available_btns()
        else:
            self.data_container = None

    def load_available_btns(self):
        """
            set available btn's with actual state  for each selected endpoint
            the actual state is taken from self.checked_btn dict for selected endpoint
        """
        if self.endpoint_ is not None:
            selected_endpoint = self.endpoint[self.endpoint_]
            self.button.setText(f'Preprocess {selected_endpoint}')

            self.remove_outliers.setVisible(False)
            self.subtract_blanks.setVisible(False)
            self.median_control.setVisible(False)
            self.calc_mean_median.setVisible(False)
            self.clean_dna_.setVisible(False)
            self.casp_clean.setVisible(False)

            if selected_endpoint in self.rules:
                for btn in self.rules[selected_endpoint]:
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

    def save_button_state(self, button_id, state):
        self.checked_btn[self.endpoint[self.endpoint_]][button_id] = state

    def function_map(self, selected_endpoint, todo):
        if todo == "remove":
            self.data_container_copy[selected_endpoint][1].remove_outliers_by_quantiles()
        elif todo == 'clean_dna':
            self.data_container_copy[selected_endpoint][1].clean_dna_raw()
        elif todo == 'median_control':
            self.data_container_copy[selected_endpoint][1].median_control(
                self.data_container_copy[selected_endpoint][0].normalized_df)
        elif todo == 'subtract':
            self.data_container_copy[selected_endpoint][1].subtract_blank(
                self.data_container_copy[selected_endpoint][0].normalized_df)
        elif todo == 'mean_median':
            self.data_container_copy[selected_endpoint][1].calc_mean_median()
        elif todo == 'dr_param':
            self.data_container_copy[selected_endpoint][2].dose_response_parameters()
        elif todo == 'casp_clean':
            self.data_container_copy[selected_endpoint][1].ctg_mean_df = self.data_container_copy['CTG'][0].mean_df
            self.data_container_copy[selected_endpoint][1].dapi_mean_df = self.data_container_copy['DAPI'][0].mean_df
            self.data_container_copy[selected_endpoint][1].normalize_data_to_cell_count()
        else:
            print('no available function')

    def process(self):
        selected_endp = self.endpoint[self.endpoint_]
        self.data_container_copy[selected_endp] = copy.deepcopy(self.data_container[selected_endp])
        self.create_hts_calc_objects(selected_endp)

        for func, isAvailable in self.checked_btn[selected_endp].items():
            if isAvailable:
                self.function_map(selected_endp, func)

        self.Outputs.data_container_output.send(self.data_container_copy)

        self.view_data()

    def create_hts_calc_objects(self, selected_endp):
        if selected_endp == 'CTG':
            self.data_container_copy[selected_endp].append(CellViabilityNormalization(self.data_container_copy[selected_endp][0]))
        elif selected_endp == 'DAPI':
            self.data_container_copy[selected_endp].append(
                DNADamageNormalization(self.data_container_copy[selected_endp][0]))
        elif selected_endp == '8OHG':
            self.data_container_copy[selected_endp].append(
                DNADamageNormalization(self.data_container_copy[selected_endp][0]))
        elif selected_endp == 'H2AX':
            self.data_container_copy[selected_endp].append(
                DNADamageNormalization(self.data_container_copy[selected_endp][0]))
        elif selected_endp == 'CASP':
            self.data_container_copy[selected_endp].append(
                CellViabilityNormalization(self.data_container_copy[selected_endp][0]))
        self.data_container_copy[selected_endp].append(DoseResponse(self.data_container_copy[selected_endp][0]))

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
    WidgetPreview(Toxpi).run()
