import pandas as pd
from Orange.widgets.widget import OWWidget
from Orange.widgets import gui
from AnyQt.QtWidgets import QGridLayout, QFileDialog
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem


class DataViewHandler(OWWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.data = {}
        self.endpoint_view = ''
        self.dataframe_view = ''
        self.table = pd.DataFrame()
        self.dataframes_available_dict = {}
        self.dataframes_available = []

        self.combo_box_endpoint = gui.comboBox(None, self, 'endpoint_view', label='Select endpoint',
                                               sendSelectedValue=True)
        self.combo_box_dataframe = gui.comboBox(None, self, 'dataframe_view', label='Select dataframe',
                                                sendSelectedValue=True, callback=self.view)
        self.view_table = gui.widgetBox(None, 'table')
        self.table_to_view = QTableWidget(self.view_table)
        self.saveBtn = gui.button(None, self, 'Save as', callback=self.save_table, autoDefault=False)

    def setup_ui(self):
        self.combo_box_endpoint.clear()
        self.combo_box_endpoint.addItems(list(self.data.keys()))
        self.parent.layout().addWidget(self.combo_box_endpoint)
        self.combo_box_dataframe.clear()

        self.dataframes_available = list(self.dataframes_available_dict.keys())
        self.combo_box_dataframe.addItems(self.dataframes_available)

        self.endpoint_view = list(self.data.keys())[0]
        self.dataframe_view = self.dataframes_available[0]

        self.parent.layout().addWidget(self.combo_box_dataframe)
        self.parent.layout().addWidget(self.view_table)

    def view(self):
        if self.endpoint_view in self.data:
            self.table = getattr(self.data[self.endpoint_view][0],
                                 self.dataframes_available_dict[self.dataframe_view])
        else:
            print('key doesnt exist')

        num_rows, num_cols = self.table.shape
        self.table_to_view.setRowCount(num_rows)
        self.table_to_view.setColumnCount(num_cols)
        self.table_to_view.setHorizontalHeaderLabels(self.table.columns)
        for i in range(num_rows):
            self.table_to_view.setVerticalHeaderItem(i, QTableWidgetItem(str(self.table.index[i])))
            for j in range(num_cols):
                item = QTableWidgetItem(str(self.table.iloc[i, j]))
                self.table_to_view.setItem(i, j, item)

        self.view_table.layout().addWidget(self.table_to_view)
        self.view_table.layout().addWidget(self.saveBtn)

    def save_table(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Table", "",
                                                   "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)",
                                                   options=options)
        if file_path:
            if file_path.endswith(".csv"):
                self.table.to_csv(file_path)
            elif file_path.endswith(".xlsx"):
                self.table.to_excel(file_path)
            else:
                print('no existing file format to save')
