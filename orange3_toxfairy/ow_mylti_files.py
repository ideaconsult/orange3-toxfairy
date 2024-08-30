import os
import Orange
import pandas as pd
from AnyQt.QtWidgets import QSizePolicy as Policy, QGridLayout, QFileDialog, QStyle
from Orange.data.io import FileFormat
from Orange.widgets import widget, gui
from Orange.widgets.utils.filedialogs import RecentPathsWidgetMixin, RecentPath, open_filename_dialog
from Orange.widgets.settings import Setting
from Orange.data.pandas_compat import table_from_frame, table_to_frame

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from Orange.widgets.widget import OWWidget, Input, Output, Msg


class RelocatablePathsWidgetMixin(RecentPathsWidgetMixin):
    """
    Do not rearrange the file list as the RecentPathsWidgetMixin does.
    """

    def add_path2(self, filename, reader):
        """Add (or move) a file name to the top of recent paths"""
        self._check_init()
        recent = RecentPath.create(filename, self._search_paths())
        if reader is not None:
            recent.file_format = reader.qualified_name()
        self.recent_paths.append(recent)

    def select_file(self, n):
        return NotImplementedError


class MultifileNames(OWWidget, RelocatablePathsWidgetMixin):
    name = "Multifiles"
    icon = "icons/print.svg"
    description = "Read multiple file names or directories."
    priority = 10

    class Outputs:
        table = Output("Data", Orange.data.Table)

    want_main_area = True
    radioBtnSelection = Setting(0, schema_only=True)
    files = Setting([], schema_only=True)
    paths = Setting([], schema_only=True)

    def __init__(self, *args, **kwargs):
        RelocatablePathsWidgetMixin.__init__(self)
        super().__init__(*args, **kwargs)

        self.prev_table = None

        box = gui.widgetBox(self.controlArea, self.name)
        gui.radioButtonsInBox(box, self, 'radioBtnSelection',
                              btnLabels=['Select files', 'Select directories'],
                              tooltips=['Use this option for files', 'Use this option for directories'],
                              callback=self.engine)

        self.layout = QGridLayout()
        gui.widgetBox(self.controlArea,
                      margin=0,
                      orientation=self.layout)
        self.file_button = gui.button(None, self, ' select multiple files',
                                      callback=self.browse_files,
                                      autoDefault=False)
        self.file_button.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.path_button = gui.button(None, self, ' select directories',
                                      callback=self.browse_directory,
                                      autoDefault=False)
        self.path_button.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.path_button.setSizePolicy(Policy.Minimum, Policy.Fixed)

        self.mainBox = gui.widgetBox(self.mainArea, 'Data view')
        self.view_table = QTableWidget()
        self.clear_selected_rows = gui.button(None, self, 'Remove selected items', self.clear_rows)

        self.engine()

    def engine(self):
        if self.radioBtnSelection == 0:
            self.layout.addWidget(self.file_button, 0, 0)
            self.create_output(self.files)
            self.path_button.setParent(None)
        else:
            self.layout.addWidget(self.path_button, 0, 0)
            self.create_output(self.paths)
            self.file_button.setParent(None)

    def browse_from_files(self):
        start_file = os.path.expanduser("~/")
        readers = [f for f in FileFormat.formats if getattr(f, 'read', None) and getattr(f, "EXTENSIONS", None)]
        filenames, reader, _ = open_filename_dialog(start_file, None, readers, dialog=QFileDialog.getOpenFileNames)

        if not filenames:
            return
        for f in filenames:
            self.add_path2(f, reader)
            self.files.append(f)

    def browse_directory(self):
        path = str(QFileDialog.getExistingDirectory(None, "Select Directory"))
        self.paths.append(path)
        self.create_output(self.paths)

    def browse_files(self):
        self.browse_from_files()
        self.create_output(self.files)

    def create_output(self, data):
        df = pd.DataFrame(data, columns=['data'])
        orange_table = table_from_frame(df)
        self.Outputs.table.send(orange_table)
        self.show_table(df)

    def show_table(self, df):
        self.mainBox.layout().addWidget(self.view_table)

        num_rows, num_cols = df.shape
        self.view_table.setRowCount(num_rows)
        self.view_table.setColumnCount(num_cols)
        self.view_table.setHorizontalHeaderLabels(df.columns)
        for i in range(num_rows):
            self.view_table.setVerticalHeaderItem(i, QTableWidgetItem(str(df.index[i])))
            for j in range(num_cols):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                self.view_table.setItem(i, j, item)

        self.mainBox.layout().addWidget(self.clear_selected_rows)

    def clear_rows(self):
        selected_rows = set(index.row() for index in self.view_table.selectedIndexes())
        # TODO: when select multiple rows I cant remove them and error occur:
        # File "d:\phd\projects\toxpi\orange-tox5\tox_orange_demo\ow_mylti_files.py", line 134, in clear_rows
        # self.files.remove(self.files[row])
        # IndexError: list index out of range

        for row in selected_rows:
            if self.radioBtnSelection == 0:
                self.files.remove(self.files[row])
                self.create_output(self.files)
            else:
                self.paths.remove(self.paths[row])
                self.create_output(self.paths)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(MultifileNames).run()
