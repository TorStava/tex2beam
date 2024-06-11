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

# OpenAI API Token

All methods that access the OpenAI API requires a valid API TOKEN to be set in the `.env` file, or given as input parameter on the command line, or as input to the specific function. See the docstrings for the relevant functions for more details.

# Getting Started

Loading the module for use in your own code:

    import tex2beam as tb

# Generating Presentations

To generate a presentation from the report $\LaTeX$ source file run the `tex2beam.main` module in the terminal, e.g.:

    python -m tex2beam.main --latex-path {LATEX_PATH} --output-path {OUTPUT_PATH} --method "rag"


To generate presentations from all report source file in a folder run the main `tex2beam` script in the terminal, e.g.:

    python -m tex2beam.main --source-folder {SOURCE_FOLDER} --target-folder {TARGET_FOLDER} --method "rag"

NOTE: Be careful if you run this on a large dataset as the conversions can consume a lot of tokens, which will incur costs.

Available command line options can be viewed in the help output:

    python -m tex2beam.main --help

See the code docstrings for more information.

# Metrics

To calculate the metrics for a generated presentation against a reference presentation, use the following command:

    python -m tex2beam.run_metrics --scoring-method {bert, rouge} \\
        --predictions-file {PREDICTIONS_FILE} \\
        --reference-file {REFERENCE_FILE} \\
        --output {OUTPUT_FILE}

Available command line options can be viewed in the help output:

    python -m tex2beam.run_metrics --help

See the code docstrings for more information.