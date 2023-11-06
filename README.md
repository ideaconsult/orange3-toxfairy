# orange-tox5

## Installation Steps

1. Install the latest version of [Miniforge](https://github.com/conda-forge/miniforge#download).
2. Clone the repo.
3. Open a new Miniforge prompt and change directory to where you cloned the repo.
4. Create a new Conda environment (see [Notes](#notes) below about `mamba`).
```bash
mamba env create -n orange-tox5 -f environment.yml
```
5. Activate the environment.
```bash
mamba activate orange-tox5
```
6. If you're on Windows, run this **each time** you open a new Miniforge prompt.
```bash
set R_HOME="%CONDA_PREFIX%\lib\R"
```
7. Run Orange.
```bash
orange-canvas
```

### Notes

- Miniforge is the only Conda system that we test and support. Other Conda systems like the standard [Anaconda and Miniconda](https://docs.conda.io/projects/conda/en/stable/user-guide/install/download.html) should work, but we cannot provide support for them.
- Miniforge provides [mamba](https://github.com/mamba-org/mamba) in addition to conda. `mamba` is a reimplementation of the conda package manager in C++. It is much faster in dependency resolution, which is why we stronly recommend using it instead of conda.
- Installing with Conda is the only supported method. It should be possible to use an existing Orange3 installation and also use pip to install the Python dependencies, as well as install R independently, but we cannot at the moment provide support for such solution.

## Acknowledgements

🇪🇺 This project has received funding from the European Union’s Horizon 2020 research and innovation program under [grant agreement No. 953183](https://cordis.europa.eu/project/id/953183).
