import pandas as pd
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets import gui
from AnyQt.QtWidgets import QListWidget
from Orange.data.io import FileFormat
from Orange.data.pandas_compat import table_from_frame
import Orange.data
from Orange.widgets.settings import Setting
import re
from PyQt5.QtWidgets import QTableWidgetItem, QTableWidget
from TOX5.calculations.tox5 import TOX5


class Toxpi(OWWidget):
    name = "Tox5 Score"
    description = "Transforming slicing and calculate TOX5 prioritization index"
    icon = "icons/print.svg"

    class Inputs:
        data_container = Input("Data dictionary", dict, auto_summary=False)

    class Outputs:
        df_transformed = Output("transformed data", Orange.data.Table)
        dataframe_tox = Output("tox data", Orange.data.Table)
        ci_slices_dict = Output('ci_4slices', dict, auto_summary=False)

    class Error(OWWidget.Error):
        weight_value = Msg("Invalid weight value. Please enter an integer value.")
        set_weight = Msg('No selected metric, please select.')
        empty_weight = Msg('Please add weight value')
        manual_slices_length = Msg('Manual slices need to be with equal length.')
        manual_slices_names = Msg('Slices names need to be unique.You can not duplicate slices names.')
        empty_slices = Msg('Slice name or slice metrics are empty.')

    tf_1st = Setting('log10x_6', schema_only=True)
    tf_auc = Setting('sqrt_x', schema_only=True)
    tf_max = Setting('log10x_6', schema_only=True)
    radioBtnSelection = Setting(0, schema_only=True)
    multi_cell_lines = Setting([], schema_only=True)

    def __init__(self):
        super().__init__()
        self.data_container = None

        self.list_cells = []
        self.list_params = []
        self.file_idx = []
        self.df = None
        self.df_copy = None
        self.selected_items_for_weight = []
        self.items_to_remove = []

        self.multi_cell_lines_items = []
        self.tf = ['log10x_6', 'sqrt_x', 'yeo_johnson']
        self.tf_dict = {"1st": self.tf_1st,
                        "auc": self.tf_auc,
                        "max": self.tf_max}
        self.tox5 = None
        self.manual_slices_df = pd.DataFrame()
        self.weight_df = pd.DataFrame()

        # control area
        box = gui.widgetBox(self.controlArea, 'Tox5-scores')
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
        gui.radioButtonsInBox(box, self, 'radioBtnSelection',
                              btnLabels=['Slice by time-endpoint', 'Slice by endpoint', 'Slice manually'],
                              tooltips=['Use this option for automated slicing by time-endpoint',
                                        'Use this option for automated slicing by endpoint',
                                        'Use this option for manually slicing'],
                              callback=self.manage_slicing_pattern)
        gui.button(box, self, 'Calculate tox5 scores',
                   callback=self.calculate_tox5_ranks,
                   autoDefault=False)
        gui.button(box, self, "Compute Bootstrap CIs", callback=self.compute_bootstrap_ci)

        # main area
        self.main = gui.hBox(self.mainArea)
        self.box_manual_slicing = gui.vBox(None, "Manual slicing")
        self.box_manual_s = gui.vBox(None, 'Slices')

        self.parameters = gui.button(self.box_manual_slicing, self, 'Load parameters',
                                     callback=self.load_available_params,
                                     autoDefault=False)
        self.lb = gui.listBox(self.box_manual_slicing, self, "file_idx",
                              selectionMode=QListWidget.MultiSelection)

        self.slice_name = gui.lineEdit(self.box_manual_slicing, self, '',
                                       label='Slice name:')

        self.create_slices = gui.button(self.box_manual_slicing, self, 'Create slice',
                                        callback=self.create_new_slice,
                                        autoDefault=False)

        self.view_table = QTableWidget(self.box_manual_s)
        self.set_weight = gui.lineEdit(self.box_manual_s, self, '', label='Set weight:')
        self.add_weight_btn = gui.button(self.box_manual_s, self, 'Add weight', callback=self.add_weight)
        self.clear_weight = gui.button(self.box_manual_s, self, 'Clear weight', callback=self.clear_weight)
        self.clear_selected_cols = gui.button(self.box_manual_s, self, 'Remove selected slices',
                                              callback=self.clear_cols)

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
            self.multi_cell_selection.clear()
            self.multi_cell_selection.addItems(self.list_cells)

            self.multi_cell_lines = [0]
            self.add_selected_multi_cell_lines()
            self.tox5 = TOX5(self.df, self.multi_cell_lines_items)
            self.manage_slicing_pattern()

    def load_available_cells(self):
        cells = set()
        parameters = list(self.df.keys())
        for i in parameters:
            if i == 'material':
                continue
            cel = (re.match("^[^_]+", i)).group()
            cells.add(cel)
        self.list_cells = list(cells)

    def manage_slicing_pattern(self):
        self.selected_items_for_weight = []
        self.items_to_remove = []
        self.df_copy = self.df.copy(deep=True)
        self.tox5.data = self.df

        self.Error.clear()

        self.main.layout().addWidget(self.box_manual_s)
        if self.radioBtnSelection == 2:
            self.tox5.data = self.df
            self.show_table(self.manual_slices_df)
            self.main.layout().addWidget(self.box_manual_slicing)
        else:
            self.box_manual_slicing.setParent(None)
            df = self.create_auto_slices()
            self.show_table(df)

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
        self.Error.manual_slices_length.clear()
        self.Error.manual_slices_names.clear()
        self.Error.empty_slices.clear()

        if not sn.strip() or not chosen_slice:
            self.Error.empty_slices()
            return

        if sn in self.manual_slices_df.columns:
            self.Error.manual_slices_names()
            return
        try:
            self.manual_slices_df[sn] = chosen_slice
        except ValueError:
            self.Error.manual_slices_length()
            return

        self.manage_slicing_pattern()

    def create_auto_slices(self):
        self.tox5.cell = self.multi_cell_lines_items
        if self.radioBtnSelection == 0:
            self.tox5.generate_auto_slices()
        elif self.radioBtnSelection == 1:
            self.tox5.generate_auto_slices('by_endpoint')

        transpose_slices = list(map(list, zip(*self.tox5.slices)))
        df = pd.DataFrame(transpose_slices, columns=self.tox5.slice_names)
        return df

    def add_selected_multi_cell_lines(self):
        self.multi_cell_lines_items = [item.text() for item in self.multi_cell_selection.selectedItems()]

    def calculate_tox5_ranks(self):
        self.tox5.transform_data(self.tf_dict)

        if self.radioBtnSelection == 0 or self.radioBtnSelection == 1:
            self.tox5.calculate_tox5_scores()
        else:
            self.tox5.calculate_tox5_scores(manual_slicing=True)

        orange_table = table_from_frame(self.tox5.tox5_scores, force_nominal=True)
        self.Outputs.dataframe_tox.send(orange_table)

        orange_table_transformed = table_from_frame(self.tox5.transformed_data, force_nominal=True)
        self.Outputs.df_transformed.send(orange_table_transformed)

        self.manage_slicing_pattern()

    def compute_bootstrap_ci(self):
        if self.tox5.transformed_data is not None:
            ci_slices = self.tox5.ci_slices()
            self.Outputs.ci_slices_dict.send(ci_slices)

        if self.tox5.tox5_scores is not None:
            _, _ = self.tox5.ci_scores()

            orange_table = table_from_frame(self.tox5.tox5_scores, force_nominal=True)
            self.Outputs.dataframe_tox.send(orange_table)

    def update_tf_dict(self):
        self.tf_dict['1st'] = self.tf_1st
        self.tf_dict['auc'] = self.tf_auc
        self.tf_dict['max'] = self.tf_max

    def add_weight(self):
        weight_text = self.set_weight.text()
        weight_factor = None
        current_selected = []

        if weight_text.strip():
            self.Error.empty_weight.clear()
            try:
                weight_factor = int(weight_text)
                self.Error.weight_value.clear()
            except ValueError:
                self.Error.weight_value()
                return
        else:
            self.Error.empty_weight()
            return

        selected_indexes = self.view_table.selectedIndexes()

        if not selected_indexes:
            self.Error.set_weight()
            return

        self.Error.set_weight.clear()

        for index in selected_indexes:
            row = index.row()
            col = index.column()
            item = self.view_table.item(row, col)

            if item is not None:
                original_value = item.text()
                match = re.match(r'^(.*?)_\(?\d*\)?$', original_value)
                if match:
                    original_value = match.group(1)

                self.selected_items_for_weight.append(original_value)
                current_selected.append(original_value)
                new_item = f'{original_value}_({weight_factor})'
                item.setText(new_item)

        for i in range(1, weight_factor):
            for col_name in current_selected:
                new_col_name = f'{col_name}_w{i + 1}'
                self.df_copy[new_col_name] = self.df_copy[col_name]

        self.tox5.data = self.df_copy
        self.update_slices_and_slices_names()

    def clear_weight(self):
        selected_indexes = self.view_table.selectedIndexes()

        for index in selected_indexes:
            row = index.row()
            col = index.column()
            item = self.view_table.item(row, col)

            if item is not None:
                original_value = item.text()
                match = re.match(r'^(.*?)_\(?\d*\)?$', original_value)
                if match:
                    original_value = match.group(1)
                    self.items_to_remove.append(original_value)

                new_item = f'{original_value}'
                item.setText(new_item)

        suffixes_to_remove = [f'{item}_w' for item in self.items_to_remove]

        columns_to_remove = self.df_copy.columns[self.df_copy.columns.str.contains('|'.join(suffixes_to_remove))]
        self.df_copy = self.df_copy.drop(columns=columns_to_remove)
        self.tox5.data = self.df_copy

        self.update_slices_and_slices_names()

    def show_table(self, df):
        self.box_manual_s.layout().addWidget(self.view_table)

        num_rows, num_cols = df.shape
        self.view_table.setRowCount(num_rows)
        self.view_table.setColumnCount(num_cols)
        self.view_table.setHorizontalHeaderLabels(df.columns)
        for i in range(num_rows):
            self.view_table.setVerticalHeaderItem(i, QTableWidgetItem(str(df.index[i])))
            for j in range(num_cols):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                self.view_table.setItem(i, j, item)

    def clear_cols(self):
        selected_columns = set(index.column() for index in self.view_table.selectedIndexes())
        for col in sorted(selected_columns, reverse=True):
            self.view_table.removeColumn(col)
        self.update_slices_and_slices_names()

    def update_slices_and_slices_names(self):
        column_names = []
        column_values = []
        for col in range(self.view_table.columnCount()):
            header_item = self.view_table.horizontalHeaderItem(col)
            if header_item is not None:
                column_name = header_item.text()
                column_names.append(column_name)

            values = []
            for row in range(self.view_table.rowCount()):
                item = self.view_table.item(row, col)
                if item is not None:
                    original_value = item.text()
                    match = re.match(r'(.+)_\((\d+)\)', original_value)
                    if match:
                        original, weight_factor = match.group(1), int(match.group(2))
                        values.append(original)
                        for i in range(1, weight_factor):
                            new_name = f'{original}_w{i + 1}'
                            values.append(new_name)
                    else:
                        values.append(original_value)
            column_values.append(values)

        if self.radioBtnSelection == 2:
            self.tox5.manual_slices = column_values
            self.tox5.manual_names = column_names
        else:
            self.tox5.slices = column_values
            self.tox5.slice_names = column_names


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(Toxpi).run()
