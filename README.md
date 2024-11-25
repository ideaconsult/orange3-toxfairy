# Orange3-ToxFAIRy

## Installation Steps

1. Install the latest version of [Miniforge](https://github.com/conda-forge/miniforge#download).
2. Clone the repo.
3. Open a new Miniforge prompt and change directory to where you cloned the repo.
4. Create a new Conda environment.
```bash
conda env create
```
5. Activate the environment.
```bash
conda activate orange3-toxfairy
```
6. Run Orange.
```bash
orange-canvas
```

### Notes

- **IMPORTANT:** On the first run Orange will need to download some additional R libraries. You may see several progress bars (on Windows) or messages in the console (on Linux). The message `package 'toxpiR' successfully unpacked` in the console will indicate when the downloads are finished. On subsequent runs Orange should start much faster.
- Miniforge is the only Conda system that we test and support. Other Conda systems like the standard [Anaconda and Miniconda](https://docs.conda.io/projects/conda/en/stable/user-guide/install/download.html) should work, but we cannot provide support for them.
- Installing with Conda is the only supported method. It should be possible to use an existing Orange3 installation and also use pip to install the Python dependencies, as well as install R independently, but we cannot at the moment provide support for such solution.

## Acknowledgements

🇪🇺 This project has received funding from the European Union’s Horizon 2020 research and innovation program under [grant agreement No. 953183](https://cordis.europa.eu/project/id/953183).
