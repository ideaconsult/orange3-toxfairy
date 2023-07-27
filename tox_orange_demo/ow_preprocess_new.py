from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QGridLayout
from Orange.data.io import FileFormat
import Orange.data
from tox5_preprocessing.src.TOX5.calculations.casp_normalization import CaspNormalization
from tox5_preprocessing.src.TOX5.calculations.ctg_normalization import CTGNormalization
from tox5_preprocessing.src.TOX5.calculations.dapi_normalization import DapiNormalization
from tox5_preprocessing.src.TOX5.calculations.dose_response import DoseResponse
from tox5_preprocessing.src.TOX5.calculations.ohg_h2ax_normalization import OHGH2AXNormalization
from tox5_preprocessing.src.TOX5.endpoints.hts_data import HTSData
from tox5_preprocessing.src.TOX5.endpoints.hts_data_reader import HTSDataReader


class Toxpi(OWWidget):
    name = "Toxpi preprocess new"
    description = "Calculate 1st significant concentration, AUC, MAX effect"
    icon = "icons/print.svg"

    class Inputs:
        path = Input("Directory", Orange.data.Table)
        files = Input("Files", Orange.data.Table)

    class Outputs:
        dataframe_tox = Output("tox data", Orange.data.Table)

    def __init__(self):
        super().__init__()
        self.path = None
        self.file = None

        self.annot_file = None
        self.files_path = None

        # create endpoint objects
        self.ctg_data = None
        self.dapi_data = None
        self.h2ax_data = None
        self.ohg_data = None
        self.casp_data = None

        # create normalized data object
        self.ctg_n = None
        self.dapi_n = None
        self.h2ax_n = None
        self.ohg_n = None
        self.casp_n = None

        # create dose-response object
        self.ctg_d = None
        self.dapi_d = None
        self.h2ax_d = None
        self.ohg_d = None
        self.casp_d = None

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

        self.endpoint = ['CTG', 'CASP', 'DAPI', '8OHG', 'H2AX']

        # control area
        self.layout = QGridLayout()
        gui.widgetBox(self.controlArea, 'Tox5', orientation=self.layout)

        self.radioBtnSelection = None
        self.endpoints = gui.listBox(None, self, 'endpoint_', callback=self.load_available_btns)
        self.endpoints.addItems(self.endpoint)
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

        self.layout.addWidget(self.box2, 0, 1)
        self.layout.addWidget(self.box3, 1, 1)
        self.layout.addWidget(self.button, 2, 0, 1, 2)

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

        self.checked_btn = {'CTG': {},
                            'CASP': {},
                            'DAPI': {},
                            '8OHG': {},
                            'H2AX': {}}

        self.endpoints_obj = {'CTG': [self.ctg_data, self.ctg_n, self.ctg_d],
                              'CASP': [self.casp_data, self.casp_n, self.casp_d],
                              'DAPI': [self.dapi_data, self.dapi_n, self.dapi_d],
                              '8OHG': [self.ohg_data, self.ohg_n, self.ohg_d],
                              'H2AX': [self.h2ax_data, self.h2ax_n, self.h2ax_d]}

    @Inputs.path
    def set_pat(self, path):
        if path:
            self.path = path
            self.files_path = self.path.metas[0][0]
        else:
            self.path = None

    @Inputs.files
    def set_file(self, file):
        if file:
            self.file = file
            self.annot_file = self.file.metas[0][0]
        else:
            self.file = None

    def load_available_btns(self):
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

    def save_checked_btn(self):
        button_id = self.sender().objectName()
        button_state = self.sender().isChecked()
        self.save_button_state(button_id, button_state)

    def save_button_state(self, button_id, state):
        self.checked_btn[self.endpoint[self.endpoint_]][button_id] = state

    def function_map(self, selected_endpoint, todo):
        if todo == "remove":
            self.endpoints_obj[selected_endpoint][1].remove_outliers_by_quantiles()
        elif todo == 'clean_dna':
            self.endpoints_obj[selected_endpoint][1].clean_dna_raw()
        elif todo == 'median_control':
            self.endpoints_obj[selected_endpoint][1].median_control(
                self.endpoints_obj[selected_endpoint][0].normalized_df)
        elif todo == 'subtract':
            self.endpoints_obj[selected_endpoint][1].subtract_blank(
                self.endpoints_obj[selected_endpoint][0].normalized_df)
        elif todo == 'sd_blank':
            self.endpoints_obj[selected_endpoint][1].calc_blank_sd()
        elif todo == 'mean_median':
            self.endpoints_obj[selected_endpoint][1].calc_mean_median()
        elif todo == 'dr_param':
            self.endpoints_obj[selected_endpoint][2].dose_response_parameters()
        elif todo == 'casp_clean':
            self.endpoints_obj[selected_endpoint][1].calc_paramc_casp()
        else:
            print('no available function')

    def process(self):
        selected_endp = self.endpoints.currentItem().text()
        self.read_data_2(selected_endp)
        print(self.endpoints_obj[selected_endp][0].raw_data_df)

        for func, isAvailable in self.checked_btn[selected_endp].items():
            if isAvailable:
                print(func)
                self.function_map(selected_endp, func)

        print(self.endpoints_obj[selected_endp][0].raw_data_df)
        print(self.endpoints_obj[selected_endp][0].normalized_df)
        print(self.endpoints_obj[selected_endp][0].mean_df)
        print(self.endpoints_obj[selected_endp][0].median_df)
        print(self.endpoints_obj[selected_endp][0].dose_response_df)

    def read_data_2(self, selected_endp):
        if selected_endp == 'CTG':
            self.ctg_data = HTSData('CTG', self.annot_file)
            self.endpoints_obj['CTG'][0] = self.ctg_data
            ctg_reader = HTSDataReader(self.files_path, self.annot_file, self.ctg_data)
            ctg_reader.read_data_csv()
            self.ctg_n = CTGNormalization(self.ctg_data)
            self.endpoints_obj['CTG'][1] = self.ctg_n
            self.ctg_d = DoseResponse(self.ctg_data)
            self.endpoints_obj['CTG'][2] = self.ctg_d
        elif selected_endp == 'CASP':
            self.casp_data = HTSData('Casp', self.annot_file)
            self.endpoints_obj['CASP'][0] = self.casp_data
            casp_reader = HTSDataReader(self.files_path, self.annot_file, self.casp_data)
            casp_reader.read_data_csv()
            self.casp_n = CaspNormalization(self.casp_data, self.ctg_data, self.dapi_data)
            self.endpoints_obj['CASP'][1] = self.casp_n
            self.casp_d = DoseResponse(self.casp_data)
            self.endpoints_obj['CASP'][2] = self.casp_d
        elif selected_endp == 'DAPI':
            self.dapi_data = HTSData('Dapi', self.annot_file)
            self.endpoints_obj['DAPI'][0] = self.dapi_data
            dapi_reader = HTSDataReader(self.files_path, self.annot_file, self.dapi_data, 'Imaging raw')
            dapi_reader.read_data_excel()
            self.dapi_n = DapiNormalization(self.dapi_data)
            self.endpoints_obj['DAPI'][1] = self.dapi_n
            self.dapi_d = DoseResponse(self.dapi_data)
            self.endpoints_obj['DAPI'][2] = self.dapi_d
        elif selected_endp == '8OHG':
            self.ohg_data = HTSData('8OHG', self.annot_file)
            self.endpoints_obj['8OHG'][0] = self.ohg_data
            ohg_reader = HTSDataReader(self.files_path, self.annot_file, self.ohg_data, 'Imaging raw')
            ohg_reader.read_data_excel()
            self.ohg_n = OHGH2AXNormalization(self.ohg_data)
            self.endpoints_obj['8OHG'][1] = self.ohg_n
            self.ohg_d = DoseResponse(self.ohg_data)
            self.endpoints_obj['8OHG'][2] = self.ohg_d
        elif selected_endp == 'H2AX':
            self.h2ax_data = HTSData('H2AX', self.annot_file)
            self.endpoints_obj['H2AX'][0] = self.h2ax_data
            h2ax_reader = HTSDataReader(self.files_path, self.annot_file, self.h2ax_data, 'Imaging raw')
            h2ax_reader.read_data_excel()
            self.h2ax_n = OHGH2AXNormalization(self.h2ax_data)
            self.endpoints_obj['H2AX'][1] = self.h2ax_n
            self.h2ax_d = DoseResponse(self.h2ax_data)
            self.endpoints_obj['H2AX'][2] = self.h2ax_d


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(Toxpi).run()
