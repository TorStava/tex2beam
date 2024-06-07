# TEX2BEAM

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This repository contains the `tex2beam` Python package that generates LaTeX Beamer presentations from LaTeX reports.

# Requirements

Install the package requirements either using Python pip, or creating a Conda environment:

Python pip:

    pip install -r requirements.txt

Conda:

    conda env create -f environment.yml -n {ENVIRONMENT NAME}


# Installation

The package can be installed by cloning this GitHub repository and installing the package locally:

    pip install .

or directly from GitHub:

    pip install git+https://github.com/TorStava/tex2beam.git

To install the package in development (editable) mode, use the following command in a local clone of the repository:

    pip install --editable .

# Getting Started

Loading the module for use in your own code:

    import tex2beam as tb

# Generating Presentations

To generate presentations run the main `tex2beam` script in the terminal, e.g.:

    python tex2beam/main.py --source-folder {SOURCE_FOLDER} --target-folder {TARGET_FOLDER} --method "rag"

