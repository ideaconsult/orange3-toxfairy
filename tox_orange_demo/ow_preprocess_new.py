import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QGridLayout
from Orange.data.io import FileFormat
import Orange.data
import copy
from tox5_preprocessing.src.TOX5.calculations.casp_normalization import CaspNormalization
from tox5_preprocessing.src.TOX5.calculations.ctg_normalization import CTGNormalization
from tox5_preprocessing.src.TOX5.calculations.dapi_normalization import DapiNormalization
from tox5_preprocessing.src.TOX5.calculations.dose_response import DoseResponse
from tox5_preprocessing.src.TOX5.calculations.ohg_h2ax_normalization import OHGH2AXNormalization


class Toxpi(OWWidget):
    name = "Toxpi preprocess new"
    description = "Calculate 1st significant concentration, AUC, MAX effect"
    icon = "icons/print.svg"

    class Inputs:
        data_container = Input("Data dictionary", dict)

    class Outputs:
        dataframe_tox = Output("tox data", Orange.data.Table)

    def __init__(self):
        super().__init__()
        self.data_container = None
        self.data_container_copy = None
        self.endpoint = []

        # save checked btn state
        self.endpoint_ = -1
        self.remove_out = 0
        self.med_control = 0
        self.sub_bl = 0
        self.sd_bl = 0
        self.casp_clean_ = 0
        self.mean_median = 0
        self.clean_dna = 0
        self.dose = 0

        # control area
        self.layout = QGridLayout()
        gui.widgetBox(self.controlArea, 'Tox5', orientation=self.layout)

        self.radioBtnSelection = None
        self.endpoints = gui.listBox(None, self, 'endpoint_', callback=self.load_available_btns)
        # self.endpoints.addItems(self.endpoint)
        self.layout.addWidget(self.endpoints, 0, 0, 2, 1)

        self.box2 = gui.widgetBox(None, 'Normalizations', orientation='vertical')

        self.clean_dna_ = gui.checkBox(self.box2, self, 'clean_dna', 'clean dna raw',
                                       callback=self.save_checked_btn,
                                       tooltip='for all 0 dapi results: remove results for 8ohg + h2ax '
                                               'if dapi is 0 and remove result for dapi if imaging is failed '
                                               '(median for dapi replicates are more than 50)')
        self.clean_dna_.setObjectName('clean_dna')

        self.remove_outliers = gui.checkBox(self.box2, self, 'remove_out', 'remove_outliers',
                                            callback=self.save_checked_btn,
                                            tooltip='removing  dispersant outliers based on first and '
                                                    'third quantiles and replacing the value with NaN')
        self.remove_outliers.setObjectName('remove')
        self.median_control = gui.checkBox(self.box2, self, 'med_control', 'median_control',
                                           callback=self.save_checked_btn)
        self.median_control.setObjectName('median_control')
        self.subtract_blanks = gui.checkBox(self.box2, self, 'sub_bl', 'subtract_blanks',
                                            callback=self.save_checked_btn)
        self.subtract_blanks.setObjectName('subtract')

        self.calc_bl_sd = gui.checkBox(self.box2, self, 'sd_bl', 'calculate blank sd',
                                       callback=self.save_checked_btn)
        self.calc_bl_sd.setObjectName('sd_blank')

        self.casp_clean = gui.checkBox(self.box2, self, 'casp_clean_', 'casp_normalized',
                                       callback=self.save_checked_btn,
                                       tooltip='based on ctg and dapi normalization')
        self.casp_clean.setObjectName('casp_clean')

        self.calc_mean_median = gui.checkBox(self.box2, self, 'mean_median', 'calculate mean median',
                                             callback=self.save_checked_btn)
        self.calc_mean_median.setObjectName('mean_median')

        self.box3 = gui.widgetBox(None, 'Dose - response', orientation='vertical')
        self.dr_params = gui.checkBox(self.box3, self, 'dose', 'dose_response_params', callback=self.save_checked_btn)
        self.dr_params.setObjectName('dr_param')

        self.button = gui.button(None, self, f'Preprocess', autoDefault=False, callback=self.process)

        # self.button.clicked.connect(self.update_progress)

        self.remove_outliers.setVisible(False)
        self.subtract_blanks.setVisible(False)
        self.median_control.setVisible(False)
        self.calc_bl_sd.setVisible(False)
        self.calc_mean_median.setVisible(False)
        self.clean_dna_.setVisible(False)
        self.casp_clean.setVisible(False)

        # self.reset_button.setVisible(False)

        self.layout.addWidget(self.box2, 0, 1)
        self.layout.addWidget(self.box3, 1, 1)
        self.layout.addWidget(self.button, 2, 0, 1, 2)

        # self.layout.addWidget(self.reset_button, 3, 0, 1, 2)

        self.rules = {'CTG': [self.remove_outliers, self.median_control, self.subtract_blanks,
                              self.calc_bl_sd, self.calc_mean_median, self.dr_params],
                      'CASP': [self.remove_outliers, self.median_control, self.subtract_blanks,
                               self.calc_bl_sd, self.casp_clean, self.calc_mean_median, self.dr_params],
                      'DAPI': [self.clean_dna_, self.remove_outliers, self.median_control,
                               self.calc_bl_sd, self.calc_mean_median, self.dr_params],
                      '8OHG': [self.clean_dna_, self.remove_outliers, self.median_control,
                               self.calc_bl_sd, self.calc_mean_median, self.dr_params],
                      'H2AX': [self.clean_dna_, self.remove_outliers, self.median_control,
                               self.calc_bl_sd, self.calc_mean_median, self.dr_params]}

        self.checked_btn = {}

    @Inputs.data_container
    def set_data_container(self, data_container):
        if data_container:
            self.data_container = data_container
            self.endpoint = list(self.data_container.keys())
            self.endpoints.addItems(self.endpoint)
            self.data_container_copy = copy.deepcopy(self.data_container)
            # create dict with key for each available endpoint and set empty dict to store checked btns
            self.checked_btn = {key: {} for key in self.endpoint}

            for endpoint, buttons in self.rules.items():
                endpoint_states = {}
                if endpoint in self.endpoint:
                    for button in buttons:
                        button_name = button.objectName()
                        endpoint_states[button_name] = False
                    self.checked_btn[endpoint] = endpoint_states

            print(self.checked_btn)
        else:
            self.data_container = None

    def load_available_btns(self):
        # set available btns with actual state  for each selected endpoint
        # the actual state is taken from self.checked_btn dict for selected endpoint
        selected_endpoint = self.endpoint[self.endpoint_]
        self.button.setText(f'Preprocess {selected_endpoint}')

        self.remove_outliers.setVisible(False)
        self.subtract_blanks.setVisible(False)
        self.median_control.setVisible(False)
        self.calc_bl_sd.setVisible(False)
        self.calc_mean_median.setVisible(False)
        self.clean_dna_.setVisible(False)
        self.casp_clean.setVisible(False)

        if selected_endpoint in self.rules:
            for btn in self.rules[selected_endpoint]:
                btn.setVisible(True)
                button_id = btn.objectName()
                btn.setChecked(self.checked_btn[selected_endpoint].get(button_id, False))
        print(self.checked_btn)

    def save_checked_btn(self):
        # save actual state for each btn in self.checked_btn dict for selected endpoint
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
        elif todo == 'sd_blank':
            # can remove it
            self.data_container_copy[selected_endpoint][1].calc_blank_sd()
        elif todo == 'mean_median':
            self.data_container_copy[selected_endpoint][1].calc_mean_median()
        elif todo == 'dr_param':
            self.data_container_copy[selected_endpoint][2].dose_response_parameters()
        elif todo == 'casp_clean':
            self.data_container_copy[selected_endpoint][1].ctg_mean_df = self.data_container_copy['CTG'][0].mean_df
            self.data_container_copy[selected_endpoint][1].ctg_mean_df = self.data_container_copy['DAPI'][0].mean_df
            self.data_container_copy[selected_endpoint][1].additional_normalization()

            # if 'CTG' in self.data_container_copy:
                # if (
                #         hasattr(self.data_container_copy['CTG'][0], 'mean_df') and
                #         isinstance(self.data_container_copy['CTG'][0].mean_df, pd.DataFrame) and
                #         not self.data_container_copy['CTG'][0].mean_df.empty):
                #     self.data_container_copy[selected_endpoint][1].ctg_mean_df = self.data_container_copy['CTG'][
                #         0].mean_df
                # if (
                #         hasattr(self.data_container_copy['DAPI'][0], 'mean_df') and
                #         isinstance(self.data_container_copy['DAPI'][0].mean_df, pd.DataFrame) and
                #         not self.data_container_copy['DAPI'][0].mean_df.empty):
                #     self.data_container_copy[selected_endpoint][1].ctg_mean_df = self.data_container_copy['DAPI'][
                #         0].mean_df

        else:
            print('no available function')

    def process(self):
        selected_endp = self.endpoints.currentItem().text()
        self.data_container_copy[selected_endp] = copy.deepcopy(self.data_container[selected_endp])
        self.create_hts_calc_objects(selected_endp)

        for func, isAvailable in self.checked_btn[selected_endp].items():
            if isAvailable:
                self.function_map(selected_endp, func)

        print('//////////////////////////////// processing //////////////////////////////////////////////////////////')
        print(self.data_container_copy)

    def create_hts_calc_objects(self, selected_endp):
        if selected_endp == 'CTG':
            self.data_container_copy[selected_endp].append(CTGNormalization(self.data_container_copy[selected_endp][0]))
        elif selected_endp == 'DAPI':
            self.data_container_copy[selected_endp].append(
                DapiNormalization(self.data_container_copy[selected_endp][0]))
        elif selected_endp == '8OHG':
            self.data_container_copy[selected_endp].append(
                OHGH2AXNormalization(self.data_container_copy[selected_endp][0]))
        elif selected_endp == 'H2AX':
            self.data_container_copy[selected_endp].append(
                OHGH2AXNormalization(self.data_container_copy[selected_endp][0]))
        elif selected_endp == 'CASP':
            self.data_container_copy[selected_endp].append(
                CaspNormalization(self.data_container_copy[selected_endp][0]))
        self.data_container_copy[selected_endp].append(DoseResponse(self.data_container_copy[selected_endp][0]))


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(Toxpi).run()
