from setuptools import setup

NAME = "Orange3-ToxFAIRy"

VERSION = '1'

AUTHOR = 'IDEAconsult Ltd.'

INSTALL_REQUIRES = [
    'AnyQt~=0.2.0',
    'PyQt5~=5.15.0',
    'matplotlib~=3.9.0',
    'numpy~=1.26.0',
    'orange3~=3.38',
    'orange_widget_base~=4.25',
    'pandas~=2.2.0',
    'plotly~=5.24.0',
    'rpy2~=3.5.0',
    'scikit_learn~=1.5.0',
    'scipy~=1.14.0',
    'setuptools~=75.6.0',
    'toxfairy~=0.1.0',
]

PACKAGES = ["orange3_toxfairy"]

PACKAGE_DATA = {"orange3_toxfairy": ["icons/*.svg"]}

ENTRY_POINTS = {'orange.widgets': ['ToxFAIRy = orange3_toxfairy']}

setup(
    author=AUTHOR,
    entry_points=ENTRY_POINTS,
    install_requires=INSTALL_REQUIRES,
    name=NAME,
    package_data=PACKAGE_DATA,
    packages=PACKAGES,
    version=VERSION,
)
