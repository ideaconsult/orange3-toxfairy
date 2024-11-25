from setuptools import find_packages, setup

NAME = "ToxFAIRy"
AUTHOR = 'IDEAconsult Ltd.'
VERSION = '0.1.0'

INSTALL_REQUIRES = [
    'matplotlib',
    'numpy',
    'pandas',
    'pynanomapper',
    'rpy2',
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
    version=VERSION,
    install_requires=INSTALL_REQUIRES,
    packages=PACKAGES,
    package_dir={"": "src"}
)

