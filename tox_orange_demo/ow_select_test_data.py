import Orange
import pandas as pd
import os
from Orange.widgets.widget import OWWidget, Output, Msg
from Orange.widgets.settings import Setting
from Orange.widgets import gui
from AnyQt.QtWidgets import QGridLayout, QStyle, QListWidget
from Orange.data.pandas_compat import table_from_frame
from TOX5 import test_data


class TestData(OWWidget):
    name = "Select test data"
    description = "select test data"
    icon = "icons/print.svg"

    class Outputs:
        table = Output("Data", Orange.data.Table)

    want_main_area = False
    radioBtnSelection = Setting(0, schema_only=True)
    files = Setting([], schema_only=True)
    paths = Setting([], schema_only=True)
    data = Setting([], schema_only=True)

    def __init__(self):
        super().__init__()

        self.directory_names = test_data.get_dirs()
        self.files_from_tmp = test_data.get_files_from_dir(self.directory_names[0])
        self.test_data_dirs = self.directory_names[1:]
        self.package_path = test_data.loc

        box = gui.widgetBox(self.controlArea, self.name)
        gui.radioButtonsInBox(box, self, 'radioBtnSelection',
                              btnLabels=['Select files', 'Select directories'],
                              tooltips=['Use this option for files', 'Use this option for directories'],
                              callback=self.engine)

        self.layout = QGridLayout()
        gui.widgetBox(self.controlArea,
                      margin=0,
                      orientation=self.layout)
        self.file_button = gui.listBox(None, self, 'files',
                                       callback=self.add_files,
                                       selectionMode=QListWidget.MultiSelection)
        self.file_button.setFixedHeight(100)

        self.path_button = gui.listBox(None, self, 'paths',
                                       callback=self.add_paths,
                                       selectionMode=QListWidget.MultiSelection)
        self.path_button.setFixedHeight(100)

        self.clear_button = gui.button(self.controlArea, self, ' clear output',
                                       callback=self.clear,
                                       autoDefault=False)
        self.clear_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))

        if self.paths and self.data:
            self.add_paths()

        if self.files and self.data:
            self.add_files()

        self.engine()

    def engine(self):
        if self.radioBtnSelection == 0:
            self.file_button.clear()
            self.layout.addWidget(self.file_button, 0, 0)
            self.file_button.addItems(self.files_from_tmp)
            self.path_button.setParent(None)
        else:
            self.path_button.clear()
            self.layout.addWidget(self.path_button, 0, 0)
            self.path_button.addItems(self.test_data_dirs)
            self.file_button.setParent(None)

    def add_files(self):
        selected_files = [self.files_from_tmp[index] for index in self.files]

        self.data = []
        for file in selected_files:
            full_path = os.path.join(self.package_path, self.directory_names[0], file)
            self.data.append(full_path)
        self.create_output(self.data)

    def add_paths(self):
        selected_paths = [self.test_data_dirs[index] for index in self.paths]

        self.data = []
        for path in selected_paths:
            full_path = os.path.join(self.package_path, path)
            self.data.append(full_path)
        self.create_output(self.data)

    def create_output(self, data):
        df = pd.DataFrame(data, columns=['data'])
        orange_table = table_from_frame(df)
        self.Outputs.table.send(orange_table)

    def clear_output(self):
        self.Outputs.table.send(None)

    def clear(self):
        if self.radioBtnSelection == 0:
            self.files = []
            self.clear_output()
        else:
            self.paths = []
            self.clear_output()


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(TestData).run()
