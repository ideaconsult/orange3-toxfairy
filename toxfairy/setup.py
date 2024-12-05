from setuptools import find_packages, setup

NAME = "ToxFAIRy"

VERSION = '0.1.0'

AUTHOR = 'IDEAconsult Ltd.'

INSTALL_REQUIRES = [
    'matplotlib~=3.9.0',
    'numpy~=1.26.0',
    'pandas~=2.2.0',
    'pymcdm~=1.2.0',
    'pynanomapper~=2.0.1',
    'rpy2~=3.5.0',
    'scikit_learn~=1.5.0',
    'scipy~=1.14.0',
    'setuptools~=75.6.0',
]

PACKAGES = find_packages(where='src')

setup(
    author=AUTHOR,
    install_requires=INSTALL_REQUIRES,
    name=NAME,
    package_dir={"": "src"},
    packages=PACKAGES,
    version=VERSION,
)
