from setuptools import setup

NAME = "Orange3-ToxFAIRy"

AUTHOR = 'IDEAconsult Ltd.'

VERSION = '1'

INSTALL_REQUIRES = [
    'AnyQt',
    'matplotlib',
    'numpy',
    'orange3~=3.0',
    'orange_widget_base',
    'pandas',
    'PyQt5',
    'rpy2',
    'scikit_learn',
    'scipy',
    'setuptools',
    'plotly',
    'toxfairy'
]

PACKAGES = ["orange3_toxfairy"]

PACKAGE_DATA = {"orange3_toxfairy": ["icons/*.svg"]}

CLASSIFIERS = ["Example :: Invalid"]

# ENTRY_POINTS = {"orange.widgets": "ToxFAIRy = orange3-toxfairy"}
ENTRY_POINTS = {'orange.widgets': ['ToxFAIRy = orange3_toxfairy']}

setup(
    name=NAME,
    author=AUTHOR,
    version=VERSION,
    install_requires=INSTALL_REQUIRES,
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    classifiers=CLASSIFIERS,
    # Declare tox_orange_demo package to contain widgets for the "Tox_Demo" category
    entry_points=ENTRY_POINTS,
)
