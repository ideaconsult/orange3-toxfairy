from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from Orange.data.pandas_compat import table_from_frame, table_to_frame
import Orange.data
from PyQt5.QtWidgets import QListWidget, QColorDialog
from AnyQt.QtWidgets import QSizePolicy as Policy, QGridLayout, QFileDialog, QStyle

import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from toxfairy.src.toxfairy.misc.utils import plot_tox_rank_pie


class Toxpi(OWWidget):
    name = "Tox5 view"
    description = "View toxicity for each material"
    icon = "icons/print.svg"

    class Inputs:
        table = Input("Tox5-scores", Orange.data.Table)
        ci_slices = Input('ci_4slices', dict, auto_summary=False)

    def __init__(self):
        super().__init__()
        self.table = None
        self.list_materials = []
        self.selected_cell = []
        self.ci_intervals_dict = None
        self.colored_by = 'endpoint'
        self.low_color = "#ff5c33"
        self.high_color = "#ff5c33"
        self.figure = plt.figure(tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.mainArea.layout().addWidget(self.toolbar)
        self.mainArea.layout().addWidget(self.canvas)

        box = gui.widgetBox(self.controlArea, self.name)

        self.combo = gui.listBox(box, self, 'selected_cell', selectionMode=QListWidget.MultiSelection)
        self.colored_param = gui.comboBox(box, self, "colored_by", items=["endpoint", "cells", "time"],
                                          label='Select colored parameter',
                                          sendSelectedValue=True)
        gui.button(box, self, "Change ci low color", callback=self.select_color_low)
        gui.button(box, self, "Change ci high color", callback=self.select_color_high)

        gui.button(box, self, 'Plot Image', callback=self.plot_tox_rank, autoDefault=False)
        gui.button(box, self, 'Save Image', callback=self.save_figure, autoDefault=False)

    @Inputs.table
    def set_table(self, table):
        if table:
            self.table = table
            self.load_available_materials()
            self.combo.clear()
            self.combo.addItems(self.list_materials)
        else:
            self.table = None

    @Inputs.ci_slices
    def set_ci_dict(self, ci_dict):
        if ci_dict:
            self.ci_intervals_dict = ci_dict
        else:
            self.ci_intervals_dict = None

    def load_available_materials(self):
        df_converted = table_to_frame(self.table, include_metas=True)
        materials = df_converted['Material']
        self.list_materials = list(materials)

    def select_color_low(self):
        color = QColorDialog.getColor()
        if color.isValid():
            print(color.name())
            self.low_color = color.name()

    def select_color_high(self):
        color = QColorDialog.getColor()
        if color.isValid():
            print(color.name())
            self.high_color = color.name()

    def plot_tox_rank(self):
        print(self.colored_by)
        if not self.table:
            return

        df = table_to_frame(self.table, include_metas=True)

        materials = [self.list_materials[index] for index in self.selected_cell]
        # self.figure, legend = plot_tox_rank_pie(df, materials, self.figure)
        self.figure, legend = plot_tox_rank_pie(df, figure=self.figure, materials=materials,
                                                colored_param=self.colored_by,
                                                transparency_bars=0.8, linewidth=0.5,
                                                conf_intervals=self.ci_intervals_dict,
                                                ci_low_color=self.low_color,
                                                ci_high_color=self.high_color)

        self.canvas.draw()
        legend.show()

    def save_figure(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                                   "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*) ")
        if file_path == "":
            return

        self.figure.savefig(file_path, dpi=400, bbox_inches='tight')


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(Toxpi).run()
