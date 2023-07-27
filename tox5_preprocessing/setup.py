from setuptools import find_packages, setup

NAME = "TOX5"
AUTHOR = 'IDEAconsult Ltd.'

INSTALL_REQUIRES = [
    'matplotlib',
    'numpy',
    'pandas==1.5.2',
    'rpy2==3.5.7',
    'scikit_learn',
    'scipy',
    'setuptools'
]

PACKAGES = find_packages(where='src')
# CLASSIFIERS = ["tox5_preprocessing :: Invalid"]
# ENTRY_POINTS = {"orange.widgets": "Tox_Demo = tox_orange_demo"}

setup(
    name=NAME,
    author=AUTHOR,
    install_requires=INSTALL_REQUIRES,
    packages=PACKAGES,
    package_dir={"": "src"}
)

