from setuptools import setup

NAME = "Orange3-ToxFAIRy"

VERSION = '1'

AUTHOR = 'IDEAconsult Ltd.'

INSTALL_REQUIRES = [
    'AnyQt',
    'PyQt5',
    'matplotlib',
    'numpy',
    'orange3',
    'orange_widget_base',
    'pandas',
    'plotly',
    'rpy2',
    'scikit_learn',
    'scipy',
    'setuptools',
    'toxfairy',
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
