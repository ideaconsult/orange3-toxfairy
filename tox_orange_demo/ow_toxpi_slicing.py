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
    name = "Tox5 Score"
    description = "Transforming slicing and calculate TOX5 prioritization index"
    icon = "icons/print.svg"

    class Inputs:
        data_container = Input("Data dictionary", dict)

    class Outputs:
        df_transformed = Output("transformed data", Orange.data.Table)
        dataframe_tox = Output("tox data", Orange.data.Table)

    def __init__(self):
        super().__init__()
        self.data_container = None

        self.list_cells = []
        self.list_params = []
        self.file_idx = []
        self.slice_names = []
        self.all_slices = []
        self.df = None
        self.df2 = None

        self.multi_cell_lines = []
        self.multi_cell_lines_items = []

        # transforming functions
        self.tf_1st = 'log10x_6'
        self.tf_auc = 'sqrt_x'
        self.tf_max = 'log10x_6'
        self.tf = ['log10x_6', 'sqrt_x', 'yeo_johnson']
        self.tf_dict = {"1st": self.tf_1st,
                        "auc": self.tf_auc,
                        "max": self.tf_max}

        self.tox5 = None

        # control area
        box = gui.widgetBox(self.controlArea, 'Tox5Scores')
        gui.label(box, self, "Select cell lines:")

        self.multi_cell_selection = gui.listBox(box, self, "multi_cell_lines",
                                                selectionMode=QListWidget.MultiSelection,
                                                callback=self.add_selected_multi_cell_lines)
        self.multi_cell_selection.setFixedHeight(100)

        gui.label(box, self, "Select transforming functions:")
        self.tf_1st_btn = gui.comboBox(box, self, 'tf_1st',
                                       items=self.tf,
                                       label='1st significant dose',
                                       sendSelectedValue=True,
                                       callback=self.update_tf_dict)
        self.tf_auc_btn = gui.comboBox(box, self, 'tf_auc',
                                       items=self.tf,
                                       label='Area under curve',
                                       sendSelectedValue=True,
                                       callback=self.update_tf_dict)
        self.tf_max_btn = gui.comboBox(box, self, 'tf_max',
                                       items=self.tf,
                                       label='Maximum dose',
                                       sendSelectedValue=True,
                                       callback=self.update_tf_dict)

        gui.label(box, self, "Select slicing pattern")
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

    @Inputs.data_container
    def set_data_container(self, data_container):
        if data_container:
            self.data_container = data_container
            concatenated_df = None
            for key, data_list in self.data_container.items():
                hts_obj = data_list[0]
                df_params = hts_obj.dose_response_df
                if concatenated_df is None:
                    concatenated_df = df_params
                else:
                    concatenated_df = pd.concat([concatenated_df, df_params], axis=1)
            self.df = concatenated_df.reset_index().rename(columns={'index': 'material'})

            self.load_available_cells()
            self.multi_cell_selection.addItems(self.list_cells)
            # print(self.df)

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
        self.tox5 = TOX5(self.df, self.multi_cell_lines_items)
        slices = []
        slices_names = []
        if self.radioBtnSelection == 0:
            slices_names, slices = self.tox5.generate_auto_slices()
        elif self.radioBtnSelection == 1:
            slices_names, slices = self.tox5.generate_auto_slices('by_endpoint')

        transpose_slices = list(map(list, zip(*slices)))
        df = pd.DataFrame(transpose_slices, columns=slices_names)
        return df

    def remove_slice(self, widget, name_slice, slices):
        self.slice_names = [ele for ele in self.slice_names if ele != name_slice]
        self.all_slices = [[s for s in slice_ if s not in slices] for slice_ in self.all_slices]
        self.all_slices = [s for s in self.all_slices if s]
        widget.deleteLater()

    def add_selected_multi_cell_lines(self):
        self.multi_cell_lines_items = [item.text() for item in self.multi_cell_selection.selectedItems()]

    def calculate_tox5_ranks(self):
        self.tox5.manual_names = self.slice_names
        self.tox5.manual_slices = self.all_slices
        self.tox5.transform_data(self.tf_dict)

        if self.radioBtnSelection == 0:
            self.tox5.calculate_tox5_scores()
        elif self.radioBtnSelection == 1:
            self.tox5.calculate_tox5_scores(slices_pattern='by_endpoint')
        else:
            self.tox5.calculate_tox5_scores(manual_slicing=True)

        orange_table = table_from_frame(self.tox5.tox5_scores, force_nominal=True)
        self.Outputs.dataframe_tox.send(orange_table)

        orange_table_transformed = table_from_frame(self.tox5.transformed_data, force_nominal=True)
        self.Outputs.df_transformed.send(orange_table_transformed)

    def update_tf_dict(self):
        self.tf_dict['1st'] = self.tf_1st
        self.tf_dict['auc'] = self.tf_auc
        self.tf_dict['max'] = self.tf_max


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Toxpi).run()
