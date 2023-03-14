import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QSizePolicy as Policy, QGridLayout, QListWidget
from Orange.data.io import FileFormat
from Orange.data.pandas_compat import table_from_frame, table_to_frame
import Orange.data
import re

from tox_orange_demo.toxpi_r import *



class Toxpi(OWWidget):
    name = "Tox5 test"
    description = "Calculate toxcicity rank"
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
        # self.slice_name = ""

        self.all_slices = []
        self.df = None

        box = gui.widgetBox(self.controlArea, 'Tox5')
        self.combo = gui.comboBox(box, self, 'selected_cell', sendSelectedValue=True)
        self.radioBtnSelection = None
        gui.radioButtonsInBox(box, self, 'radioBtnSelection',
                              btnLabels=['Slice by time-endpoint', 'Slice by endpoint', 'Slice manually'],
                              tooltips=['Use this option for automated slicing by time-endpoint',
                                        'Use this option for automated slicing by endpoint',
                                        'Use this option for manually slicing'],
                              callback=self.engine)

        self.layout_control = QGridLayout()
        gui.widgetBox(self.controlArea, margin=0, orientation=self.layout_control)

        self.layout = QGridLayout()
        gui.widgetBox(self.mainArea, margin=0, orientation=self.layout)

        self.parameters = gui.button(None, self, 'Load parameters', callback=self.load_available_params, autoDefault=False)
        self.parameters.setSizePolicy(Policy.Maximum, Policy.Fixed)
        self.lb = gui.listBox(None, self, "file_idx", selectionMode=QListWidget.MultiSelection)
        self.lb.setSizePolicy(Policy.Maximum, Policy.Expanding)
        self.slice_name = gui.lineEdit(None, self, '', label='Slice name:', callback=self.create_new_slice_name, orientation="horizontal")
        self.slice_name.setSizePolicy(Policy.Maximum, Policy.Fixed)
        self.create_slices = gui.button(None, self, 'Create slice', callback=self.create_new_slice, autoDefault=False)
        self.create_slices.setSizePolicy(Policy.Maximum, Policy.Fixed)

        gui.button(box, self, 'Calculate', callback=self.calculate_toxpi_rank, autoDefault=False)

        # self.layout = QGridLayout()
        # gui.widgetBox(self.mainArea, margin=0, orientation=self.layout)

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

            self.layout_control.addWidget(self.parameters)
            self.layout_control.addWidget(self.lb)
            self.layout_control.addWidget(self.slice_name)
            self.layout_control.addWidget(self.create_slices)
        else:
            self.parameters.setParent(None)
            self.lb.setParent(None)
            self.slice_name.setParent(None)
            self.create_slices.setParent(None)
            if self.radioBtnSelection == 0:
                print('first btn')
                print(self.radioBtnSelection)
            else:
                print('second btn')
                print(self.radioBtnSelection)

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
        # self.file_idx_slice = []
        choosen_slice = [item.text() for item in self.lb.selectedItems()]
        sn = self.slice_name.text()

        box = gui.widgetBox(None, self.slice_name.text())
        gui.widgetLabel(box, f"{chr(10).join(choosen_slice)}")

        gui.button(box, self, 'Remove slice', callback=lambda: self.remove_slice(box, sn, choosen_slice))

        self.layout.addWidget(box)
        self.all_slices.append(choosen_slice)

        ## bl_n = gui.listBox(box, self, "file_idx_slice", selectionMode=QListWidget.MultiSelection)
        ## gui.button(box, self, 'remove slice', callback=lambda: box.deleteLater(), autoDefault=False)
        ## bl_n.addItems(choosen_slice)
        ## self.all_slices.append(choosen_slice)

    def create_new_slice_name(self):
        self.slice_names.append(self.slice_name.text())

    def remove_slice(self, widget, name_slice, slices):
        self.slice_names = [ele for ele in self.slice_names if ele != name_slice]

        self.all_slices = [[s for s in slice_ if s not in slices]for slice_ in self.all_slices]
        self.all_slices = [s for s in self.all_slices if s]
        widget.deleteLater()

    def calculate_toxpi_rank(self):
        print(self.slice_names)
        print(self.all_slices)
        df2 = pd.DataFrame()
        df, slice_names_ = calculate_first_tox5(self.df, self.selected_cell)

        if self.radioBtnSelection == 0:
            df2 = calculate_second_tox5(df, slice_names_)
            print(self.radioBtnSelection)
        elif self.radioBtnSelection == 1:
            df2 = calculate_second_tox5_by_endpoint(df, slice_names_)
            print(self.radioBtnSelection)
        else:
            print('manual functionality')
            print(self.radioBtnSelection)

        orange_table = table_from_frame(df2, force_nominal=True)
        self.Outputs.dataframe_tox.send(orange_table)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Toxpi).run()