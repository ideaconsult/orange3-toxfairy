from os import environ
from platform import system as host_os

if host_os() == 'Windows':
    try:
        environ['R_HOME'] = environ['CONDA_PREFIX'] + '\\lib\\R'
    except KeyError as e:
        print(f'Error: Environment variable CONDA_PREFIX is not set: {e}', file=sys.stderr)

from rpy2.robjects.packages import importr, isinstalled


def get_source_package(package_name):
    if isinstalled(package_name):
        source_package = importr(package_name)
        return source_package
    else:
        utils.install_packages(package_name)
        source_package = importr(package_name)
        return source_package


base = importr("base")
utils = importr("utils")
utils.chooseCRANmirror(ind=1)
biocmanager = get_source_package('BiocManager')
biocmanager.install('S4Vectors', update=False, ask=False)
car = get_source_package('car')
toxpiR = get_source_package('toxpiR')

# def extract_versions(package_data):
#     return dict(zip(
#         package_data.rx(True, 'Package'),
#         package_data.rx(True, 'Version')
#     ))
# i = extract_versions(utils.installed_packages())
# a = extract_versions(utils.available_packages())
# is_latest_version = i['car'] == a['car']
