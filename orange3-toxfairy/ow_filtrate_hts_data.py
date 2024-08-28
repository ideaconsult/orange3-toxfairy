import pandas as pd
import copy
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets import gui
from AnyQt.QtWidgets import QListWidget
from Orange.widgets.settings import Setting

from tox_orange_demo.data_view import DataViewHandler


class HTSDataFiltrator(OWWidget):
    name = "HTS data filter"
    description = "Filtrate data by chosen parameters"
    icon = "icons/print.svg"

    class Inputs:
        data_container = Input("Data dictionary", dict, auto_summary=False)

    class Outputs:
        data_container_output = Output("Data dictionary", dict, auto_summary=False)

    endpoint_list = Setting([], schema_only=True)
    cell_lines_list = Setting([], schema_only=True)
    material_list = Setting([], schema_only=True)

    def __init__(self):
        super().__init__()
        self.data_container = None
        self.data_container_copy = None

        box = gui.widgetBox(self.controlArea, 'Filtrate Data', orientation='horizontal')
        self.endpoint_list_box = gui.listBox(box, self, 'endpoint_list',
                                             selectionMode=QListWidget.MultiSelection,
                                             callback=self.get_endpoints)
        # self.endpoint_list_box.setFixedHeight(100)
        self.cell_lines_box = gui.listBox(box, self, "cell_lines_list",
                                          selectionMode=QListWidget.MultiSelection)
        # self.cell_lines_box.setFixedHeight(100)
        self.material_box = gui.listBox(box, self, 'material_list',
                                        selectionMode=QListWidget.MultiSelection)
        self.filtrate_btn = gui.button(box, self, "Filter data", callback=self.filtrate)
        self.mainBox = gui.widgetBox(self.mainArea, 'Data view')
        self.data_view_handler = DataViewHandler(self.mainBox)
        self.data_view_handler.dataframes_available_dict = {'Raw data': 'raw_data_df',
                                                            'Dose-response': 'dose_response_df'}

    @Inputs.data_container
    def set_data_container(self, data_container):
        if data_container:
            self.data_container = data_container
            self.data_container_copy = self.data_container.copy()

            self.endpoint_list_box.clear()
            self.endpoint_list_box.addItems(list(self.data_container.keys()))

            self.cell_lines_box.clear()
            self.get_cell_lines()

            self.material_box.clear()
            self.get_materials()

    def get_cell_lines(self):
        cell_lines = []
        if self.endpoint_list:
            for endpoint in self.endpoint_list_box.selectedItems():
                cell_lines.append(self.data_container[endpoint.text()][0].raw_data_df['cells'])
        else:
            first_key = next(iter(self.data_container))
            cell_lines.append(self.data_container[first_key][0].raw_data_df['cells'])

        flat_cell_lines = [item for sublist in cell_lines for item in sublist]
        self.cell_lines_box.addItems(list(set(flat_cell_lines)))

    def get_endpoints(self):
        self.cell_lines_box.clear()
        self.get_cell_lines()
        self.material_box.clear()
        self.get_materials()

    def get_materials(self):
        material_values = []
        if self.endpoint_list:
            for endpoint in self.endpoint_list_box.selectedItems():
                metadata = self.data_container[endpoint.text()][0].metadata
                material_values.append([v['material'] for v in metadata.values() if 'material' in v])
        else:
            first_key = next(iter(self.data_container))
            metadata = self.data_container[first_key][0].metadata
            material_values.append([v['material'] for v in metadata.values() if 'material' in v])

        flat_material_values = [item for sublist in material_values for item in sublist]
        self.material_box.addItems(list(set(flat_material_values)))

    def filtrate(self):
        selected_items_endpoint = self.endpoint_list_box.selectedItems()
        selected_values_endpoint = [item.text() for item in selected_items_endpoint]

        selected_items_materials = self.material_box.selectedItems()
        selected_values_materials = [item.text() for item in selected_items_materials]

        selected_items_cells = self.cell_lines_box.selectedItems()
        selected_values_cells = [item.text() for item in selected_items_cells]

        self.data_container_copy = copy.deepcopy(self.data_container)
        self.data_container_copy = {key: value for key, value in self.data_container_copy.items()
                                    if key in selected_values_endpoint}

        filtered_dose_response_df = pd.DataFrame()

        for key, value in self.data_container_copy.items():
            filtered_metadata_dict = {key: value for key, value in value[0].metadata.items()
                                      if value.get('material') in selected_values_materials}
            value[0].metadata = filtered_metadata_dict

            # filtrate raw_data_df
            if key in ['DAPI', 'H2AX', '8OHG']:
                columns_to_keep = ['cells', 'replicates', 'time', 'Description'] + list(filtered_metadata_dict.keys())
            else:
                columns_to_keep = ['cells', 'replicates', 'time'] + list(filtered_metadata_dict.keys())

            filtered_raw_df = value[0].raw_data_df
            columns_to_keep = [col for col in columns_to_keep if
                               col in filtered_raw_df.columns]
            filtered_raw_df = filtered_raw_df[columns_to_keep]

            mask_raw_data_cells = filtered_raw_df['cells'].isin(selected_values_cells)
            filtered_raw_df = filtered_raw_df[mask_raw_data_cells]

            # filtrate dose-response
            filtrate_dose = value[0].dose_response_df
            if not filtrate_dose.empty:
                mask_dose_resp_materials = filtrate_dose.index.isin(selected_values_materials)
                filtered_dose_response_df = filtrate_dose[mask_dose_resp_materials]
                mask_dose_resp_cells = filtered_dose_response_df.columns.str.contains('|'.join(selected_values_cells))
                filtered_dose_response_df = filtered_dose_response_df.loc[:, mask_dose_resp_cells]

            value[0].raw_data_df = filtered_raw_df
            value[0].dose_response_df = filtered_dose_response_df

        self.Outputs.data_container_output.send(self.data_container_copy)

        self.view_data()

    def view_data(self):
        self.data_view_handler.data = self.data_container_copy
        self.data_view_handler.setup_ui()
        self.view()

    def view(self):
        self.data_view_handler.view()

    def save_table(self):
        self.data_view_handler.save_table()


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    WidgetPreview(HTSDataFiltrator).run()
