from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QSizePolicy as Policy, QGridLayout, QFileDialog, QStyle, QListWidget
from Orange.data.io import FileFormat
import Orange.data
from Orange.data.pandas_compat import table_from_frame
from tox_orange_demo.toxpi_data_prep import *


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

        median_CTG, mean_CTG, df_ready_ctg = calc_params_ctg('CTG', annot_file, files_path)
        median_dapi, mean_dapi, df_ready_dapi = calc_params_imaging('Dapi', annot_file, files_path)
        median_ohg, mean_ohg, df_ready_ohg = calc_params_imaging('8OHG', annot_file, files_path)
        median_h2ax, mean_h2ax, df_ready_h2ax = calc_params_imaging('H2AX', annot_file, files_path)
        _, _, df_ready_casp = calc_params_ctg('Casp', annot_file, files_path)
        median_casp, mean_casp, df_ready_casp2 = calc_paramc_casp(annot_file, mean_CTG, mean_dapi, df_ready_casp)
        df_ready_dapi1 = calc_final(df_ready_dapi, median_dapi, annot_file, 'DAPI')
        df_ready_ctg1 = calc_final(df_ready_ctg, median_CTG, annot_file, 'CTG')
        df_ready_ohg1 = calc_final(df_ready_ohg, median_ohg, annot_file, 'OHG-1')
        df_ready_h2ax1 = calc_final(df_ready_h2ax, median_h2ax, annot_file, 'H2AX')
        df_ready_casp1 = calc_final(df_ready_casp2, median_casp, annot_file, 'CASP')
        df = df_by_cells(df_ready_dapi1, df_ready_ctg1, df_ready_ohg1, df_ready_h2ax1, df_ready_casp1)

        df_last = table_from_frame(df, force_nominal=True)

        self.Outputs.dataframe_tox.send(df_last)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Toxpi).run()

