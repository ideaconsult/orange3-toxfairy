# + tags=["parameters"]
upstream = None
product = None
folder_output = None
folder_input = None
files_input = None
metadata_templates = None
# -

from TOX5.endpoints.hts_data_container import HTS
from TOX5.endpoints.reader_from_tmp import MetaDataReaderTmp, DataReaderTmp
import os.path
import pickle


def create_data_container(endpoint, assay_type, directory=None, tmp=None, serum=False):
    _data = None

    _data = HTS(endpoint)
    _meta = MetaDataReaderTmp(tmp, _data)
    _meta.read_meta_data()
    data_reader = DataReaderTmp(tmp, directory, _data)
    data_reader.read_data()
    _data.raw_data_df = _data.raw_data_df[_data.raw_data_df['Description'] != '_']

    _data.serum_used = serum
    _data.assay_type = assay_type

    return _data


def pkl_hts_obj(hts_obj):
    for obj in hts_obj:
        if obj.serum_used:
            file_name = f'{obj.endpoint}_data_w.pkl'
        else:
            file_name = f'{obj.endpoint}_data_wo.pkl'

        with open(os.path.join(product['data'], file_name), 'wb') as f:
            pickle.dump(obj, f)


templates = [os.path.join(folder_input, file) for file in metadata_templates.split(",")]
directories = [os.path.join(folder_input, file) for file in files_input.split(",")]


config = {"config1": {
    "dapiA": {"dir": directories[0], "tmp": templates[0], "assay_type": 'imaging', "serum": True},
    "dapiB": {"dir": directories[0], "tmp": templates[0], "assay_type": 'imaging', "serum": True},
    "casp": {"dir": directories[0], "tmp": templates[0], "assay_type": 'imaging', "serum": True},
    "h2ax": {"dir": directories[0], "tmp": templates[0], "assay_type": 'imaging', "serum": True},
    "8ohg": {"dir": directories[0], "tmp": templates[0], "assay_type": 'imaging', "serum": True}
    },
    "config2": {
        "dapiA": {"dir": directories[1], "tmp": templates[1], "assay_type": 'imaging', "serum": False},
        "dapiB": {"dir": directories[1], "tmp": templates[1], "assay_type": 'imaging', "serum": False},
        "casp": {"dir": directories[1], "tmp": templates[1], "assay_type": 'imaging', "serum": False},
        "h2ax": {"dir": directories[1], "tmp": templates[1], "assay_type": 'imaging', "serum": False},
        "8ohg": {"dir": directories[1], "tmp": templates[1], "assay_type": 'imaging', "serum": False}
    }
}


obj_list = []
for key, config_item in config.items():
    for endpoint, config_data in config_item.items():
        directory = config_data.get("dir", None)
        tmp = config_data.get("tmp", None)
        serum = config_data.get("serum", None)
        assay_type = config_data.get("assay_type", None)
        tmp_obj = create_data_container(endpoint, assay_type=assay_type, directory=directory, tmp=tmp, serum=serum)
        obj_list.append(tmp_obj)

os.makedirs(product["data"], exist_ok=True)
pkl_hts_obj(obj_list)

print(len(obj_list))
print(obj_list[0])
