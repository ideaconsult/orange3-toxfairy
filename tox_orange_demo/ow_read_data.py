import re
import pandas as pd
import copy
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from Orange.data import table_from_frame
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets import gui
import Orange.data
from Orange.widgets.settings import Setting
from AnyQt.QtWidgets import QFileDialog
from orangewidget import widget

from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import DataReaderTmp, MetaDataReaderTmp
from TOX5.misc.utils import annotate_data


class Toxpi(OWWidget):
    name = "Read HTS data/metadata"
    description = "Read HTS data and annotate with meta data"
    icon = "icons/print.svg"

    UserAdviceMessages = [
        widget.Message("Please enter endpoints separately using either a dot and whitespace (. ) or a comma and "
                       "whitespace (, ). Available endpoints: CTG, CASP, DAPI, H2AX, OHG", '')]

    class Inputs:
        data_input = Input("Directory to data ", Orange.data.Table, default=True)
        meta_data_input = Input("File for meta data", Orange.data.Table, default=False)

    class Outputs:
        data_dict = Output("Data dictionary", dict)
        meta_data_table = Output("Meta data", Orange.data.Table)

    endpoint = Setting('', schema_only=True)
    recalculate = Setting(True, schema_only=True)
    well_volume = Setting("50", schema_only=True)
    cell_growth_area = Setting("0.079495092", schema_only=True)
    radioBtnSelection = Setting(0, schema_only=True)

    class Warning(OWWidget.Warning):
        warning_func = Msg("Function is under development, please select another one.")

    class Error(OWWidget.Error):
        no_datafiles_error = Msg("Please, load files with data")

    def __init__(self):
        super().__init__()
        self.endpoint_view = ''
        self.annot_file = None
        self.data_files_path = None

        self.endpoints_list = []
        self.selected_values_dict = {}
        self.annot_data = ''
        self.output_dict = {}
        self.previous_table = None
        self.raw_data = pd.DataFrame()

        """
        Control area with entering endpoints box, reading data and meta data box from selected dirs, 
        and recalculation dose box.
        """

        self.box_read = gui.widgetBox(self.controlArea, 'Read and annotate data from local directory')
        self.endpoint_line = gui.lineEdit(self.box_read, self, 'endpoint', label='Enter endpoints:',
                                          callback=self.endpoint_names)
        self.box_dir = gui.widgetBox(self.controlArea, 'Set proper dir')
        self.box_annot = gui.widgetBox(self.controlArea, 'Set proper annotation dir')
        self.annot_dir = gui.comboBox(self.box_annot, self, 'annot_data', label='Annotation file',
                                      sendSelectedValue=True)
        self.box_calc = gui.widgetBox(self.controlArea, 'Recalculate dose')
        self.toggle_button = gui.checkBox(self.box_calc, self, "recalculate", "Recalculate Dose",
                                          callback=self.toggle_recalculation)
        self.well_volume_label = gui.label(None, self, 'Enter well volume in μl:')
        self.well_volume_line = gui.lineEdit(None, self, 'well_volume', label='ul')
        self.cell_growth_area_label = gui.label(None, self, 'Enter plate growth area  in cm2:')
        self.cell_growth_area_line = gui.lineEdit(None, self, 'cell_growth_area', label='cm2')
        self.radioBtns = gui.radioButtonsInBox(None, self, 'radioBtnSelection',
                                               btnLabels=['Dose per Cell Area (μg/cm²)',
                                                          'Dose based on Surface Area (cm²/cm²)',
                                                          'Cell Delivered Dose (cell delivered cm²/cm²)'],
                                               tooltips=['Nominal dose per cell cell growth area (μg/cm2)',
                                                         'Nominal dose based on the material’s specific surface area '
                                                         'per cell growth area',
                                                         'The cell delivered dose per cell growth area '])
        gui.button(self.controlArea, self, 'Process', callback=self.process, autoDefault=False)

        """
        Main area with data view of chosen endpoint.
        """
        self.mainBox = gui.widgetBox(self.mainArea, 'Data view')
        self.combo_box_main = gui.comboBox(None, self, 'endpoint_view', label='Select endpoint',
                                           sendSelectedValue=True, callback=self.view)
        self.view_table = gui.widgetBox(None, 'table')
        self.saveBtn = gui.button(None, self, 'Save as', callback=self.save_table, autoDefault=False)

        self.toggle_recalculation()

    @Inputs.data_input
    def set_pat(self, data):
        if data:
            self.data_files_path = data.metas
            # self.Error.no_datafiles_error.clear()
            self.endpoint_names()
        else:
            self.data_files_path = None

    @Inputs.meta_data_input
    def set_file(self, meta_data):
        if meta_data:
            self.annot_file = meta_data.metas
            # self.Error.no_datafiles_error.clear()
            self.endpoint_names()
        else:
            self.annot_file = None

    def toggle_recalculation(self):
        if self.recalculate:
            self.box_calc.layout().addWidget(self.well_volume_label)
            self.box_calc.layout().addWidget(self.well_volume_line)
            self.box_calc.layout().addWidget(self.cell_growth_area_label)
            self.box_calc.layout().addWidget(self.cell_growth_area_line)
            self.box_calc.layout().addWidget(self.radioBtns)
        else:
            self.well_volume_label.setParent(None)
            self.cell_growth_area_label.setParent(None)
            self.well_volume_line.setParent(None)
            self.cell_growth_area_line.setParent(None)
            self.radioBtns.setParent(None)

    def endpoint_names(self):
        # if (self.annot_file and self.data_files_path) or (self.annot_file.any() and self.data_files_path.any()):
        #     self.Error.no_datafiles_error.clear()
        if self.annot_file is None or self.data_files_path is None:
            self.Error.no_datafiles_error()
        else:
            self.Error.no_datafiles_error.clear()

            if self.endpoint_line.text():
                self.endpoints_list = []
                self.endpoints_list = re.split(r'[,.]\s+', self.endpoint_line.text())
                self.endpoints_list = [x.upper() for x in self.endpoints_list]
                self.remove_existing_widgets()

            if all(item != '' for item in self.endpoints_list):
                self.chose_dir()
        # else:
        #     self.Error.no_datafiles_error()

    def chose_dir(self):
        self.selected_values_dict = {}
        meta_values = [item[0] for item in self.annot_file]
        data_values = [item[0] for item in self.data_files_path]

        for i, items in enumerate(self.endpoints_list):
            combo_box = gui.comboBox(self.box_dir, self, '', label=f'{items}', items=data_values)
            combo_box.activated.connect(
                lambda value, items=items: self.save_selected_value(items, data_values, value))

            if data_values:
                combo_box.setCurrentText(data_values[0])
                self.save_selected_value(items, data_values, 0)

        self.annot_dir.clear()
        self.annot_dir.addItems(meta_values)

        if meta_values:
            self.annot_data = meta_values[0]

    def save_selected_value(self, items, values, index):
        if index < len(values):
            self.selected_values_dict[items] = values[index]
        else:
            print(f"Index {index} out of range for values {values}")

    def remove_existing_widgets(self):
        for i in reversed(range(self.box_dir.layout().count())):
            self.box_dir.layout().itemAt(i).widget().deleteLater()

    def process(self):
        self.output_dict = {}
        meta_data_dict = {}
        for key, value in self.selected_values_dict.items():
            test_data = HTS(key)
            test_meta = MetaDataReaderTmp(self.annot_data, test_data)
            test_meta.read_meta_data()
            test_read = DataReaderTmp(self.annot_data, value, test_data)
            test_read.read_data()

            if self.recalculate:

                if self.radioBtnSelection == 0:
                    self.Warning.warning_func.clear()
                    test_meta.recalculate_dose_from_cell_growth(float(self.well_volume_line.text()),
                                                                float(self.cell_growth_area_line.text()))
                elif self.radioBtnSelection == 1:
                    self.Warning.warning_func.clear()
                    test_meta.recalculate_dose_from_sbet(float(self.well_volume_line.text()),
                                                         float(self.cell_growth_area_line.text()))
                elif self.radioBtnSelection == 2:
                    self.Warning.warning_func()

            self.output_dict[key] = [test_data]
            meta_data_dict = test_data.metadata

        df_meta_data = pd.DataFrame(meta_data_dict)

        self.combo_box_main.clear()
        self.combo_box_main.addItems(self.endpoints_list)
        self.endpoint_view = self.endpoints_list[0]
        self.mainBox.layout().addWidget(self.combo_box_main)
        self.mainBox.layout().addWidget(self.view_table)

        self.view()

        self.Outputs.data_dict.send(self.output_dict)
        self.Outputs.meta_data_table.send(table_from_frame(df_meta_data))

    def view(self):
        output_dict_copy = copy.deepcopy(self.output_dict)
        if self.previous_table:
            self.view_table.layout().itemAt(0).widget().deleteLater()

        if self.endpoint_view in output_dict_copy:
            annotate_data(output_dict_copy[self.endpoint_view][0].raw_data_df,
                          output_dict_copy[self.endpoint_view][0].metadata)

            self.raw_data = output_dict_copy[self.endpoint_view][0].raw_data_df
        else:
            print('key doesnt exist')

        table_widget = QTableWidget(self.view_table)
        num_rows, num_cols = self.raw_data.shape
        table_widget.setRowCount(num_rows)
        table_widget.setColumnCount(num_cols)
        table_widget.setHorizontalHeaderLabels(self.raw_data.columns)
        for i in range(num_rows):
            table_widget.setVerticalHeaderItem(i, QTableWidgetItem(str(self.raw_data.index[i])))
            for j in range(num_cols):
                item = QTableWidgetItem(str(self.raw_data.iloc[i, j]))
                table_widget.setItem(i, j, item)

        self.view_table.layout().addWidget(table_widget)
        self.previous_table = table_widget
        self.view_table.layout().addWidget(self.saveBtn)

    def save_table(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Table", "",
                                                   "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)",
                                                   options=options)
        if file_path:
            if file_path.endswith(".csv"):
                self.raw_data.to_csv(file_path)
            elif file_path.endswith(".xlsx"):
                self.raw_data.to_excel(file_path)
            else:
                print('no existing file format to save')


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Toxpi).run()
