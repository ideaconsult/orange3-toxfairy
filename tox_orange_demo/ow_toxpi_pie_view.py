from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from Orange.data.pandas_compat import table_from_frame, table_to_frame
import Orange.data
from PyQt5.QtWidgets import QListWidget
from AnyQt.QtWidgets import QSizePolicy as Policy, QGridLayout, QFileDialog, QStyle

import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


class Toxpi(OWWidget):
    name = "Tox5 view"
    description = "View toxicity for each material"
    icon = "icons/print.svg"

    class Inputs:
        table = Input("Table", Orange.data.Table)

    def __init__(self):
        super().__init__()
        self.table = None
        self.list_materials = []
        self.selected_cell = []
        self.figure = plt.figure(tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.mainArea.layout().addWidget(self.toolbar)
        self.mainArea.layout().addWidget(self.canvas)

        box = gui.widgetBox(self.controlArea, self.name)

        self.combo = gui.listBox(box, self, 'selected_cell', selectionMode=QListWidget.MultiSelection)
        gui.button(box, self, 'Plot Image', callback=self.plot_tox_rank, autoDefault=False)
        gui.button(box, self, 'Save Image', callback=self.save_figure, autoDefault=False)

    @Inputs.table
    def set_table(self, table):
        if table:
            self.table = table
            self.load_available_materials()
            self.combo.addItems(self.list_materials)
        else:
            self.table = None

    def load_available_materials(self):
        df_converted = table_to_frame(self.table, include_metas=True)
        materials = df_converted['Material']
        self.list_materials = list(materials)

    def plot_tox_rank(self):
        df = table_to_frame(self.table, include_metas=True)
        materials = [self.list_materials[index] for index in self.selected_cell]

        self.figure.clear()
        plt.subplots_adjust(hspace=0.2)
        plt.suptitle("Toxpi Ranked materials", fontsize=10, y=0.95)

        columns = 4
        rows = len(materials) // columns + (len(materials) % columns > 0)

        for n, i in enumerate(materials):
            rank = (df[df['Material'] == i].iloc[:, 2]).values[0]
            label = list(df[df['Material'] == i].iloc[:, 4:])

            data_tox = df[df['Material'] == i].iloc[:, 4:].values.flatten().tolist()
            width = 2 * np.pi / len(label)
            angle = np.linspace(0.0, 2 * np.pi, len(label), endpoint=False)
            colors = cm.get_cmap('plasma', len(label)).colors

            ax = plt.subplot(rows, columns, n + 1, projection='polar')
            bars = ax.bar(angle, data_tox, width=width, bottom=0.02, color=colors, alpha=0.6, edgecolor='grey')
            ax.set_ylim(0, 1)
            # ax.set_theta_zero_location('N')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
            ax.spines['polar'].set_color('grey')
            plt.title(f"{i} {rank.round(2)}", fontsize=8)
            if n == 0:
                ax.legend(bars, label, bbox_to_anchor=(-0.1, 1.4), fontsize='small')

        self.canvas.draw()

    def save_figure(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                                  "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*) ")
        if file_path == "":
            return

        self.figure.savefig(file_path, dpi=400, bbox_inches='tight')


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(Toxpi).run()

