import os
import glob
import re
import pandas as pd
import copy
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from Orange.data import table_from_frame
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
import Orange.data
from AnyQt.QtWidgets import QFileDialog

from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import DataReaderTmp, MetaDataReaderTmp
from TOX5.misc.utils import annotate_data


class Toxpi(OWWidget):
    name = "Read HTS data/metadata"
    description = "Read HTS data and annotate with meta data"
    icon = "icons/print.svg"

    class Inputs:
        data_input = Input("Directory to data ", Orange.data.Table)
        meta_data_input = Input("File for meta data", Orange.data.Table)

    class Outputs:
        data_dict = Output("Data dictionary", dict)

    def __init__(self):
        super().__init__()
        self.endpoint_view = ''

        self.data = None
        self.meta_data = None
        self.annot_file = None
        self.data_files_path = None

        self.endpoints_list = []
        self.selected_values_dict = {}
        self.annot_data = ''
        self.output_dict = {}
        self.previous_table = None
        self.raw_data = pd.DataFrame()

        # control area with reading box, directory box and recalculation dose box //////////////////////////////////////

        # box to enter endpoints ---------------------------------------------------------------------------------------
        self.box_read = gui.widgetBox(self.controlArea, 'Read and annotate data from local directory')
        self.endpoint = gui.lineEdit(self.box_read, self, '', label='Enter endpoints:', callback=self.endpoint_names)
        # self.endpoint.setFixedWidth(100)

        # box to set proper dir with data for each endpoint ------------------------------------------------------------
        self.box_dir = gui.widgetBox(self.controlArea, 'Set proper dir')

        # box for annotation file --------------------------------------------------------------------------------------
        self.box_annot = gui.widgetBox(self.controlArea, 'Set proper annotation dir')
        self.annot_dir = gui.comboBox(self.box_annot, self, 'annot_data', label='Annotation file',
                                      sendSelectedValue=True)

        # box to recalculate doses -------------------------------------------------------------------------------------
        self.box_calc = gui.widgetBox(self.controlArea, 'Recalculate dose')
        self.recalculate = False
        self.toggle_button = gui.checkBox(self.box_calc, self, "recalculate", "Recalculate Dose",
                                          callback=self.toggle_recalculation)
        self.well_volume_label = gui.label(None, self, 'Enter well volume in ul:')
        self.well_volume = gui.lineEdit(None, self, '', label='Enter well volume in ul')
        self.cell_growth_area_label = gui.label(None, self, 'Enter cell growth area in ul:')
        self.cell_growth_area = gui.lineEdit(None, self, '', label='Enter cell growth area in ul')
        self.radioBtnSelection = None
        self.radioBtns = gui.radioButtonsInBox(None, self, 'radioBtnSelection',
                                               btnLabels=['recalculate_dose_from_cell_growth',
                                                          'recalculate_dose_from_sbet',
                                                          'recalculate_dose_from_cell_delivered_dose'],
                                               tooltips=['Use this option for automated slicing by time-endpoint',
                                                         'Use this option for automated slicing by endpoint',
                                                         'Use this option for manually slicing'])
        gui.button(self.controlArea, self, 'Process', callback=self.process, autoDefault=False)

        # main area with choosen data view and save as a file //////////////////////////////////////////////////////////
        self.mainBox = gui.widgetBox(self.mainArea, 'Data view')
        self.combo_box_main = gui.comboBox(None, self, 'endpoint_view', label='Select endpoint',
                                           sendSelectedValue=True, callback=self.view)
        self.view_table = gui.widgetBox(None, 'table')
        self.saveBtn = gui.button(None, self, 'Save as', callback=self.save_table, autoDefault=False)

    @Inputs.data_input
    def set_pat(self, data):
        if data:
            self.data = data
            self.data_files_path = self.data.metas
        else:
            self.data = None

    @Inputs.meta_data_input
    def set_file(self, meta_data):
        if meta_data:
            self.meta_data = meta_data
            self.annot_file = self.meta_data.metas
        else:
            self.annot_file = None

    def toggle_recalculation(self):
        if self.recalculate:
            self.box_calc.layout().addWidget(self.well_volume_label)
            self.box_calc.layout().addWidget(self.well_volume)
            self.box_calc.layout().addWidget(self.cell_growth_area_label)
            self.box_calc.layout().addWidget(self.cell_growth_area)
            self.box_calc.layout().addWidget(self.radioBtns)
        else:
            self.well_volume_label.setParent(None)
            self.cell_growth_area_label.setParent(None)
            self.well_volume.setParent(None)
            self.cell_growth_area.setParent(None)
            self.radioBtns.setParent(None)

    def endpoint_names(self):
        self.endpoints_list = []
        self.endpoints_list = re.split(r'[,.]\s+', self.endpoint.text())
        self.endpoints_list = [x.upper() for x in self.endpoints_list]

        if all(item == '' for item in self.endpoints_list):
            self.remove_existing_widgets()
        else:
            self.remove_existing_widgets()
            self.chose_dir()

    def chose_dir(self):
        self.selected_values_dict = {}
        meta_values = [item[0] for item in self.meta_data.metas]
        data_values = [item[0] for item in self.data.metas]
        test = meta_values + data_values

        for i, items in enumerate(self.endpoints_list):
            combo_box = gui.comboBox(self.box_dir, self, '', label=f'{items}', items=test)
            combo_box.activated.connect(lambda value, items=items: self.save_selected_value(items, test[value]))

        self.annot_dir.clear()
        self.annot_dir.addItems(test)

    def save_selected_value(self, items, value):
        self.selected_values_dict[items] = value

    def remove_existing_widgets(self):
        for i in reversed(range(self.box_dir.layout().count())):
            self.box_dir.layout().itemAt(i).widget().deleteLater()

    def process(self):
        for key, value in self.selected_values_dict.items():
            print(key, value)
            test_data = HTS(key)
            test_meta = MetaDataReaderTmp(self.annot_data, test_data)
            test_meta.read_meta_data()
            test_read = DataReaderTmp(self.annot_data, value, test_data)
            test_read.read_data()

            if self.radioBtnSelection == 0:
                test_meta.recalculate_dose_from_cell_growth(float(self.well_volume.text()),
                                                            float(self.cell_growth_area.text()))
            elif self.radioBtnSelection == 1:
                test_meta.recalculate_dose_from_sbet(float(self.well_volume.text()),
                                                     float(self.cell_growth_area.text()))
            elif self.radioBtnSelection == 2:
                print('func is not implemented')

            if key not in self.output_dict:
                self.output_dict[key] = []
            self.output_dict[key].append(test_data)

        self.combo_box_main.clear()
        self.combo_box_main.addItems(self.endpoints_list)
        self.mainBox.layout().addWidget(self.combo_box_main)
        self.mainBox.layout().addWidget(self.view_table)

        self.Outputs.data_dict.send(self.output_dict)

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

        table_widget = QTableWidget()
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
