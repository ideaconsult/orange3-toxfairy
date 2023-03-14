from Orange.widgets import widget, gui, settings
from AnyQt.QtWidgets import QSizePolicy as Policy, QGridLayout


class OWEditDomain(widget.OWWidget):
    name = "widget for testing"
    description = "Rename variables, edit categories and variable annotations."
    icon = "icons/EditDomain.svg"
    priority = 3125
    keywords = ["rename", "drop", "reorder", "order"]

    def __init__(self):
        super().__init__()
        self.parameters = gui.button(self.controlArea, self, 'Load btn 2', callback=self.add_btn,
                                     autoDefault=False)

        main = gui.hBox(self.mainArea, spacing=6)
        self.box1 = gui.vBox(main, "Variables")
        # self.layout_control = QGridLayout()
        # self.test1 = gui.widgetBox(None, margin=0, orientation=self.layout_control)
        self.parameters1 = gui.button(None, self, 'Load parameters1')
        self.parameters2 = gui.button(None, self, 'Load parameters2')
        # self.layout_control.addWidget(self.parameters1)
        # self.layout_control.addWidget(self.parameters2)

        # box.layout().addWidget(self.test1)
        self.box1.layout().addWidget(self.parameters1)
        # box.layout().addWidget(self.parameters2)

        self.box2 = gui.vBox(main, "Edit")
        self.layout2 = QGridLayout()
        self.test2 = gui.widgetBox(None, margin=0, orientation=self.layout2)
        self.parameters3 = gui.button(None, self, 'Load parameters3')
        self.parameters4 = gui.button(None, self, 'Load parameters4')
        self.layout2.addWidget(self.parameters3)
        self.layout2.addWidget(self.parameters4)

        # self.box2.layout().addWidget(self.test2)

    def add_btn(self):
        self.box2.layout().addWidget(self.test2)

        self.box1.layout().addWidget(self.parameters2)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(OWEditDomain).run()