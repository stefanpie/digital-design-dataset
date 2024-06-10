# Contributing Guide

## Setting up the Development Environment

The easiest way to set up a development environment is to use `conda`. Even better would be to use `mamba` since it's a much faster version of conda. For a simple way to install mamba, see [Mambaforge](https://github.com/conda-forge/miniforge#mambaforge). If you dont want to use mamba, you can use `conda` everywhere you see `mamba` in the following instructions.

Once you have mamba installed, you can use the predefined environment file to create a new environment with all the dependencies installed. To do this, run the following command:

```bash
mamba env create -f environment.yaml
```

This should create a new environment named `digital_design_dataset`. To activate this environment, run the following command:

```bash
mamba activate digital_design_dataset
```

## File Structure

- `/digital_design_dataset/`: This is the main Python library.
  - `/digital_design_dataset/dataset/`: This is a folder that contains the code for creating datasets and loading/adding design sources from a variety of sources.
    - `/digital_design_dataset/dataset/design_dataset.py`: This is a Python module that contains the `DesignDataset` class, used to create, index, and manage a dataset of hardware designs on disk.
    - `/digital_design_dataset/dataset/datasets.py`: This is a Python module that contains the `DatasetRetriever` abstract class, used for creating specific dataset retriever subclasses that implement logic to download and preprocess design sources into a design dataset. It also includes different subclass implementations of the `DatasetRetriever` abstract class for different design sources. Examples include `OpencoresDatasetRetriever`, `EPFLDatasetRetriever`, `ISCAS85DatasetRetriever`, `VTRDatasetRetriever`, and so on.
  - `/digital_design_dataset/flows/`: This is a folder that contains the code for the different flows that can be used to process the design sources in the dataset and generate data alongside the design sources. This can include flows written in Python or flows that call external EDA tools. Much of the code here is still a work in progress and is being actively developed.
- `/demo_scripts/`: This folder contains miscellaneous demo and analysis scripts as well as interactive Jupyter notebooks used throughout the development process.
  - `/demo_scripts/wip/`: This folder contains work-in-progress scripts and notebooks that are not yet ready for use.

## Contact About Contributing and Collaborating

If you would like to reach out to me directly about contributing to this project, please contact me at my academic email, [stefanabikaram@gatech.edu](mailto:stefanabikaram@gatech.edu).

If you feel comfortable, also feel free to raise an issue or submit a pull request on this repository.
