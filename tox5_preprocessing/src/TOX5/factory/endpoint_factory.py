from tox5_preprocessing.src.TOX5.endpoints.read_csv_data import EndpointDataCSV
from tox5_preprocessing.src.TOX5.endpoints.read_excel_data import EndpointDataExcel


def create_data(endpoint, raw_data, meta_data, sheet=None):
    endpoint_types = {'CTG': EndpointDataCSV,
                      'Casp': EndpointDataCSV,
                      'Dapi': EndpointDataExcel,
                      'H2AX': EndpointDataExcel,
                      '8OHG': EndpointDataExcel}
    return endpoint_types[endpoint](endpoint, raw_data, meta_data, sheet)

