import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QSizePolicy as Policy, QGridLayout, QFileDialog, QStyle, QListWidget, QHBoxLayout, QScrollArea
from Orange.data.io import FileFormat
from Orange.data.pandas_compat import table_from_frame, table_to_frame
import Orange.data
import re
import rpy2
from rpy2.robjects import pandas2ri

from tox_orange_demo.toxpi_r import *


class Toxpi(OWWidget):
    name = "Tox5"
    description = "Calculate TOX5 prioritization index"
    icon = "icons/print.svg"

    class Inputs:
        table = Input("Table", Orange.data.Table)

    class Outputs:
        dataframe_tox = Output("tox data", Orange.data.Table)

    def __init__(self):
        super().__init__()
        self.table = None
        self.list_cells = []
        self.list_params = []
        self.selected_cell = 0
        self.file_idx = []
        self.slice_names = []
        self.all_slices = []
        self.df = None

        # control area
        box = gui.widgetBox(self.controlArea, 'Tox5')
        self.combo = gui.comboBox(box, self, 'selected_cell',
                                  sendSelectedValue=True)
        self.radioBtnSelection = None
        gui.radioButtonsInBox(box, self, 'radioBtnSelection',
                              btnLabels=['Slice by time-endpoint', 'Slice by endpoint', 'Slice manually'],
                              tooltips=['Use this option for automated slicing by time-endpoint',
                                        'Use this option for automated slicing by endpoint',
                                        'Use this option for manually slicing'],
                              callback=self.engine)
        gui.button(box, self, 'Calculate',
                   callback=self.calculate_toxpi_rank,
                   autoDefault=False)

        # main area
        self.main = gui.hBox(self.mainArea, spacing=6)
        self.box_manual_slicing = gui.vBox(None, "Manual slicing")
        self.box_manual_s = gui.vBox(None, 'Slices')
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.box_manual_s)
        scroll_area.setWidgetResizable(True)
        self.main.layout().addWidget(scroll_area)

        self.parameters = gui.button(None, self, 'Load parameters',
                                     callback=self.load_available_params,
                                     autoDefault=False)
        self.lb = gui.listBox(None, self, "file_idx",
                              selectionMode=QListWidget.MultiSelection)
        self.slice_name = gui.lineEdit(None, self, '',
                                       label='Slice name:',
                                       callback=self.create_new_slice_name)
        self.create_slices = gui.button(None, self, 'Create slice',
                                        callback=self.create_new_slice,
                                        autoDefault=False)

    @Inputs.table
    def set_table(self, table):
        if table:
            self.table = table
            self.df = table_to_frame(self.table, include_metas=True)
            self.load_available_cells()
            self.combo.addItems(self.list_cells)
        else:
            self.table = None

    def load_available_cells(self):
        cells = set()
        parameters = list(self.df.keys())
        for i in parameters:
            if i == 'material':
                continue
            cel = (re.match("^[^_,-]+", i)).group()
            cells.add(cel)
        self.list_cells = list(cells)

    def engine(self):
        if self.radioBtnSelection == 2:
            for i in reversed(range(self.box_manual_s.layout().count())):
                self.box_manual_s.layout().itemAt(i).widget().deleteLater()

            self.slice_names = []
            self.all_slices = []

            self.main.layout().addWidget(self.box_manual_slicing)
            self.box_manual_slicing.layout().addWidget(self.parameters)
            self.box_manual_slicing.layout().addWidget(self.lb)
            self.box_manual_slicing.layout().addWidget(self.slice_name)
            self.box_manual_slicing.layout().addWidget(self.create_slices)

        else:
            self.box_manual_slicing.setParent(None)
            self.parameters.setParent(None)
            self.lb.setParent(None)
            self.slice_name.setParent(None)
            self.create_slices.setParent(None)

            for i in reversed(range(self.box_manual_s.layout().count())):
                self.box_manual_s.layout().itemAt(i).widget().deleteLater()

            auto_slices1, auto_slices2 = self.create_auto_slices()

            if self.radioBtnSelection == 0:
                slices_to_print = self.print_dict(auto_slices2)
                first_slices = gui.widgetLabel(None, slices_to_print)
                first_slices.setSizePolicy(Policy.Minimum, Policy.Fixed)
                self.box_manual_s.layout().addWidget(first_slices)
            else:
                slices_to_print = self.print_dict(auto_slices1)
                first_slices = gui.widgetLabel(None, slices_to_print)

                first_slices.setSizePolicy(Policy.Minimum, Policy.Fixed)
                self.box_manual_s.layout().addWidget(first_slices)

    def load_available_params(self):
        parameters = list(self.df.keys())
        self.lb.clear()
        self.list_params = []
        for i in parameters:
            if i == 'material':
                continue
            if self.selected_cell in i:
                self.list_params.append(i)
        self.lb.addItems(self.list_params)

    def create_new_slice(self):
        chosen_slice = [item.text() for item in self.lb.selectedItems()]
        sn = self.slice_name.text()

        box = gui.widgetBox(None, self.slice_name.text())
        gui.widgetLabel(box, f"{chr(10).join(chosen_slice)}")

        gui.button(box, self, 'Remove slice', callback=lambda: self.remove_slice(box, sn, chosen_slice))
        self.box_manual_s.layout().addWidget(box)

        self.all_slices.append(chosen_slice)
        self.file_idx = []

    def create_new_slice_name(self):
        self.slice_names.append(self.slice_name.text())

    def create_auto_slices(self):
        df_columns = [col for col in self.df if col.startswith(self.selected_cell)]
        endpoints = ['Dapi', 'CASP', 'H2AX', 'OHG', 'CASP']
        time_points = ['6', '24', '72']

        first_dict = {}
        second_dict = {}
        for e in endpoints:
            tmp_e_list = []
            for t in time_points:
                tmp_t_list = []
                for i in df_columns:
                    if re.search(e, i, re.IGNORECASE):
                        tmp_e_list.append(i)
                        if re.search(t, i, re.IGNORECASE):
                            tmp_t_list.append(i)
                second_dict[f'{e}_{t}H'] = tmp_t_list
            first_dict[e] = tmp_e_list

        return first_dict, second_dict

    def print_dict(self, dict_to_print):
        final_string = ''
        for key, value in dict_to_print.items():
            final_string += f'Slice {key} :'
            for i, elem in enumerate(value):
                if i == 0 or i % 4 == 0:
                    final_string += "\n"
                final_string += f'{elem}, '
            final_string += "\n"

        return final_string

    def remove_slice(self, widget, name_slice, slices):
        self.slice_names = [ele for ele in self.slice_names if ele != name_slice]
        self.all_slices = [[s for s in slice_ if s not in slices]for slice_ in self.all_slices]
        self.all_slices = [s for s in self.all_slices if s]
        widget.deleteLater()

    def calculate_toxpi_rank(self):
        df2 = pd.DataFrame()
        df, slice_names_ = calculate_first_tox5(self.df, self.selected_cell)

        if self.radioBtnSelection == 0:
            df2 = calculate_second_tox5_by_endpoint_time(df, slice_names_)
        elif self.radioBtnSelection == 1:
            df2 = calculate_second_tox5_by_endpoint(df, slice_names_)
        else:
            df2 = calculate_manual_slicing(df, self.slice_names, self.all_slices)

        orange_table = table_from_frame(df2, force_nominal=True)
        self.Outputs.dataframe_tox.send(orange_table)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Toxpi).run()
