# + tags=["parameters"]
upstream = None
enm_api_url = None
enm_api_key = None
folder_output = None
query = None
product = None
db = None
# -

# # for testing outside of pipeline
# enm_api_url = "https://api.ideaconsult.net/calibrate"
# db = "calibrate"
# query = "type=citationowner&search=MISVIK"
# enm_api_key = ''

from pynanomapper import aa
import os, os.path
import requests
import pynanomapper.datamodel.ambit as m2n
import traceback
import json

os.makedirs(product["data"], exist_ok=True)


def substances2json(url_db, auth, pjson):
    substances = m2n.Substances(**pjson)
    for substance in substances.substance:
        try:
            sjson = None
            url = "{}/substance/{}/study&media=application/json&max={}".format(url_db, substance.i5uuid, 10000)
            # url = "{}/study?media=application/json&max=10000".format(substance.URI)
            response = requests.get(url, auth=auth)
            if response.status_code == 200:
                sjson = response.json()
                substance.study = m2n.Study(**sjson).study
            else:
                print(response.status_code, url)
        except Exception as err:
            print("An exception occurred: %s", str(err))
            print("Exception traceback:\n%s", traceback.format_exc())
            print(substance.i5uuid)
            # Write JSON data to the file
            with open(os.path.join(product["data"], "{}.json".format(substance.i5uuid)), 'w') as json_file:
                json.dump(sjson, json_file, indent=4)
            break

    return substances


config, config_servers, config_security, auth_object, msg = aa.parseOpenAPI3()
if auth_object != None:
    auth_object.setKey('')

rows = 1000
url_db = "{}/enm/{}/substance?{}&media=application/json&max={}".format(enm_api_url, db, query, rows)

OK = False
response = requests.get(url_db, auth=auth_object)
if response.status_code == 200:
    pjson = response.json()
    with open(os.path.join(product["data"], "substances_parsed.json"), 'w') as json_file:
        json.dump(pjson, json_file, indent=4)

    OK = True
else:
    print(response.status_code)

substances = substances2json("{}/enm/{}".format(enm_api_url, db), auth_object, pjson)
substances_json = substances.to_json()
print(substances_json)
with open(os.path.join(product["data"], "substances_obj.json"), 'w') as json_file:
    json_file.write(substances_json)
