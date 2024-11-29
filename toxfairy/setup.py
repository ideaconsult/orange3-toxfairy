from setuptools import find_packages, setup

NAME = "ToxFAIRy"

VERSION = '0.1.0'

AUTHOR = 'IDEAconsult Ltd.'

INSTALL_REQUIRES = [
    'matplotlib',
    'numpy',
    'pandas',
    'pymcdm',
    'pynanomapper',
    'rpy2',
    'scikit_learn',
    'scipy',
    'setuptools',
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
