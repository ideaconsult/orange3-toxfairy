from Orange.widgets.widget import OWWidget, Input
from Orange.widgets import gui
import Orange

from TOX5.misc.utils import generate_annotation_file


class AutofillTmp(OWWidget):
    name = "Auto-fill template"
    description = "Auto-fill HTS_METADATA template"
    icon = "icons/print.svg"
    priority = 10

    class Inputs:
        data_input = Input("Directory to data ", Orange.data.Table)
        meta_data_input = Input("File for meta data", Orange.data.Table)

    want_main_area = False

    def __init__(self):
        super().__init__()

        self.data = None
        self.meta_data = None
        self.info_label = gui.label(self.controlArea, self, 'The HTS_METADATA template will be automatically '
                                                            '\npopulated in the "file sheet". You will need to '
                                                            '\nmanually fill out the "front sheet". '
                                                            '\nAfter populating the HTS_METADATA template, '
                                                            '\nyou may need to manually correct any inconsistencies '
                                                            '\nthat occur.')

        self.auto_fill_tmp_btn = gui.button(self.controlArea, self, 'Auto-fill template', callback=self.auto_fill_tmp,
                                            autoDefault=False)

    @Inputs.data_input
    def set_pat(self, data):
        if data:
            self.data = data
        else:
            self.data = None

    @Inputs.meta_data_input
    def set_file(self, meta_data):
        if meta_data:
            self.meta_data = meta_data
        else:
            self.meta_data = None

    def auto_fill_tmp(self):
        directories = [item[0] for item in self.data.metas]
        generate_annotation_file(directories, self.meta_data.metas[0][0])


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(AutofillTmp).run()
