import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from AnyQt.QtWidgets import QSizePolicy as Policy, QListWidget, QScrollArea
from Orange.data.io import FileFormat
from Orange.data.pandas_compat import table_from_frame, table_to_frame
import Orange.data
import re
from tox5_preprocessing.src.TOX5.calculations.tox5 import TOX5


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
        self.file_idx = []
        self.slice_names = []
        self.all_slices = []
        self.df = None

        self.multi_cell_lines = []
        self.multi_cell_lines_items = []

        # control area
        box = gui.widgetBox(self.controlArea, 'Tox5')

        self.combo2 = gui.listBox(box, self, "multi_cell_lines",
                                  selectionMode=QListWidget.MultiSelection,
                                  callback=self.add_selected_multi_cell_lines)
        self.combo2.setFixedHeight(100)

        self.tox5_norm_info = gui.label(box, self, "Normalize each metric for each timepoint\n"
                                                   "and endpoint separately\n"
                                                   "- AUC and MAX transforming function - sqrt(x),\n"
                                                   "- 1-st significant dose transforming function - –LOG10(x) +6\n")

        self.radioBtnSelection = None
        gui.radioButtonsInBox(box, self, 'radioBtnSelection',
                              btnLabels=['Slice by time-endpoint', 'Slice by endpoint', 'Slice manually'],
                              tooltips=['Use this option for automated slicing by time-endpoint',
                                        'Use this option for automated slicing by endpoint',
                                        'Use this option for manually slicing'],
                              callback=self.engine)
        gui.button(box, self, 'Calculate tox5 scores',
                   callback=self.calculate_tox5_ranks,
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
        self.slice_name_label = gui.label(None, self, 'Write slice Name:')

    @Inputs.table
    def set_table(self, table):
        if table:
            self.table = table
            self.df = table_to_frame(self.table, include_metas=True)
            self.load_available_cells()
            self.combo2.addItems(self.list_cells)
        else:
            self.table = None

    def load_available_cells(self):
        cells = set()
        parameters = list(self.df.keys())
        for i in parameters:
            if i == 'material':
                continue
            cel = (re.match("^[^_]+", i)).group()
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
            self.box_manual_slicing.layout().addWidget(self.slice_name_label)
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

            df = self.create_auto_slices()
            slices_table = gui.widgetLabel(None, df.to_html())
            slices_table.setSizePolicy(Policy.Minimum, Policy.Fixed)

            self.box_manual_s.layout().addWidget(slices_table)

    def load_available_params(self):
        parameters = list(self.df.keys())
        self.lb.clear()
        self.list_params = []
        for i in parameters:
            if i == 'material':
                continue
            for cell in self.multi_cell_lines_items:
                if cell in i:
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
        tox5 = TOX5(self.df, self.multi_cell_lines_items, self.slice_names, self.all_slices)
        slices = []
        slices_names = []
        if self.radioBtnSelection == 0:
            slices_names, slices = tox5.generate_auto_slices()
        elif self.radioBtnSelection == 1:
            slices_names, slices = tox5.generate_auto_slices('by_endpoint')

        transpose_slices = list(map(list, zip(*slices)))
        df = pd.DataFrame(transpose_slices, columns=slices_names)
        return df

    def remove_slice(self, widget, name_slice, slices):
        self.slice_names = [ele for ele in self.slice_names if ele != name_slice]
        self.all_slices = [[s for s in slice_ if s not in slices] for slice_ in self.all_slices]
        self.all_slices = [s for s in self.all_slices if s]
        widget.deleteLater()

    def add_selected_multi_cell_lines(self):
        self.multi_cell_lines_items = [item.text() for item in self.combo2.selectedItems()]

    def calculate_tox5_ranks(self):
        tox5 = TOX5(self.df, self.multi_cell_lines_items, self.slice_names, self.all_slices)
        tox5.transform_data()

        if self.radioBtnSelection == 0:
            tox5.calculate_tox5_scores()
        elif self.radioBtnSelection == 1:
            tox5.calculate_tox5_scores(slices_pattern='by_endpoint')
        else:
            tox5.calculate_tox5_scores(manual_slicing=True)

        orange_table = table_from_frame(tox5.tox5_scores, force_nominal=True)
        self.Outputs.dataframe_tox.send(orange_table)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Toxpi).run()
