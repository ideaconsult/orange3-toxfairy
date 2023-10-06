from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QSizePolicy as Policy, QGridLayout, QFileDialog, QStyle, QListWidget
from Orange.data.io import FileFormat
import Orange.data
from Orange.data.pandas_compat import table_from_frame
import pandas as pd

from tox5_preprocessing.src.TOX5.calculations.casp_normalization import CaspNormalization
from tox5_preprocessing.src.TOX5.calculations.ctg_normalization import CTGNormalization
from tox5_preprocessing.src.TOX5.calculations.dapi_normalization import DapiNormalization
from tox5_preprocessing.src.TOX5.calculations.dose_response import DoseResponse
from tox5_preprocessing.src.TOX5.calculations.ohg_h2ax_normalization import OHGH2AXNormalization
from tox5_preprocessing.src.TOX5.endpoints.hts_data import HTSData
from tox5_preprocessing.src.TOX5.endpoints.hts_data_reader import HTSDataReader


class Toxpi(OWWidget):
    name = "Toxpi preprocess"
    description = "Calculate 1st significant concentration, AUC, MAX effect"
    icon = "icons/print.svg"

    class Inputs:
        path = Input("Directory", Orange.data.Table)
        files = Input("Files", Orange.data.Table)

    class Outputs:
        dataframe_tox = Output("tox data", Orange.data.Table)

    want_main_area = False

    def __init__(self):
        super().__init__()
        self.path = None
        self.file = None

        layout = QGridLayout()
        gui.widgetBox(self.controlArea, margin=0, orientation=layout)

        file_button = gui.button(None, self, 'Calculate', callback=self.calculate, autoDefault=False)
        file_button.setSizePolicy(Policy.Maximum, Policy.Fixed)
        layout.addWidget(file_button, 0, 0)

    @Inputs.path
    def set_pat(self, path):
        if path:
            self.path = path
        else:
            self.path = None

    @Inputs.files
    def set_file(self, file):
        if file:
            self.file = file
        else:
            self.file = None

    def calculate(self):
        annot_file = self.file.metas[0][0]
        files_path = self.path.metas[0][0]

        # Standard ctg processing
        ctg_data = HTSData('CTG', annot_file)
        ctg_reader = HTSDataReader(files_path, annot_file, ctg_data)
        ctg_reader.read_data_csv()
        ctg_normalize = CTGNormalization(ctg_data)
        ctg_normalize.remove_outliers_by_quantiles()
        ctg_normalize.median_control(ctg_data.normalized_df)
        ctg_normalize.subtract_blank(ctg_data.normalized_df)
        # ctg_normalize.calc_blank_sd()
        ctg_normalize.calc_mean_median()
        ctg_dose_responce = DoseResponse(ctg_data)
        ctg_dose_responce.dose_response_parameters()

        # Standard dapi processing
        dapi_data = HTSData('Dapi', annot_file)
        dapi_reader = HTSDataReader(files_path, annot_file, dapi_data, 'Imaging raw')
        dapi_reader.read_data_excel()
        dapi_normalize = DapiNormalization(dapi_data)
        dapi_normalize.clean_dna_raw()
        dapi_normalize.remove_outliers_by_quantiles()
        dapi_normalize.median_control(dapi_data.normalized_df)
        # dapi_normalize.calc_blank_sd()
        dapi_normalize.calc_mean_median()
        dapi_dose_responce = DoseResponse(dapi_data)
        dapi_dose_responce.dose_response_parameters()

        # Standard h2ax processing
        h2ax_data = HTSData('H2AX', annot_file)
        h2ax_reader = HTSDataReader(files_path, annot_file, h2ax_data, 'Imaging raw')
        h2ax_reader.read_data_excel()
        h2ax_normalize = OHGH2AXNormalization(h2ax_data)
        h2ax_normalize.clean_dna_raw()
        h2ax_normalize.remove_outliers_by_quantiles()
        h2ax_normalize.median_control(h2ax_data.normalized_df)
        # h2ax_normalize.calc_blank_sd()
        h2ax_normalize.calc_mean_median()
        h2ax_dose_responce = DoseResponse(h2ax_data)
        h2ax_dose_responce.dose_response_parameters()

        # Standard 8ohg processing
        ohg_data = HTSData('8OHG', annot_file)
        ohg_reader = HTSDataReader(files_path, annot_file, ohg_data, 'Imaging raw')
        ohg_reader.read_data_excel()
        ohg_normalize = OHGH2AXNormalization(ohg_data)
        ohg_normalize.clean_dna_raw()
        ohg_normalize.remove_outliers_by_quantiles()
        ohg_normalize.median_control(ohg_data.normalized_df)
        # ohg_normalize.calc_blank_sd()
        ohg_normalize.calc_mean_median()
        ohg_dose_responce = DoseResponse(ohg_data)
        ohg_dose_responce.dose_response_parameters()

        # Standard casp processing
        casp_data = HTSData('Casp', annot_file)
        casp_reader = HTSDataReader(files_path, annot_file, casp_data)
        casp_reader.read_data_csv()
        casp_normalize = CaspNormalization(casp_data, ctg_data.mean_df, dapi_data.mean_df)
        casp_normalize.remove_outliers_by_quantiles()
        casp_normalize.median_control(casp_data.normalized_df)
        casp_normalize.subtract_blank(casp_data.normalized_df)
        # casp_normalize.calc_blank_sd()
        casp_normalize.additional_normalization()
        casp_normalize.calc_mean_median()
        casp_dose_responce = DoseResponse(casp_data)
        casp_dose_responce.dose_response_parameters()

        df = pd.concat([casp_data.dose_response_df,
                        ohg_data.dose_response_df,
                        h2ax_data.dose_response_df,
                        ctg_data.dose_response_df,
                        dapi_data.dose_response_df], axis=1)
        df = df.reset_index().rename(columns={'index': 'material'})

        df_last = table_from_frame(df, force_nominal=True)

        self.Outputs.dataframe_tox.send(df_last)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Toxpi).run()

