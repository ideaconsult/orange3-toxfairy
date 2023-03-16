
from setuptools import setup

NAME = "Tox_Demo"

AUTHOR = 'IDEAconsult Ltd.'

INSTALL_REQUIRES = [
    'AnyQt',
    'matplotlib',
    'numpy',
    'orange3~=3.0',
    'orange_widget_base',
    'pandas',
    'PyQt5',
    'rpy2==3.5.7',
    'scikit_learn',
    'scipy',
    'setuptools'
]

PACKAGES = ["tox_orange_demo"]

PACKAGE_DATA = {"tox_orange_demo": ["icons/*.svg"]}

CLASSIFIERS = ["Example :: Invalid"]

ENTRY_POINTS = {"orange.widgets": "Tox_Demo = tox_orange_demo"}

setup(
    name=NAME,
    author=AUTHOR,
    install_requires=INSTALL_REQUIRES,
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    classifiers=CLASSIFIERS,
    # Declare tox_orange_demo package to contain widgets for the "Tox_Demo" category
    entry_points=ENTRY_POINTS,
)


