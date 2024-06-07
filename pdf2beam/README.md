# PDF2Beam

This code is used to convert PDF presentations into $\LaTeX$ Beamer format.

## Recursive conversion

`python main.py --source-folder {SOURCE_PATH} --target-folder {TARGET_PATH}`

This will walk through the SOURCE_PATH folder and convert files ending in `-presentation.pdf` into $\LaTeX$ Beamer format and saving to the TARGET_PATH folder.

## One-off conversion

`python main.py --pdf-path {PDF_PATH} --output-path {OUTPUT_PATH}`

This will convert the PDF_PATH file into $\LaTeX$ Beamer format and save it to OUTPUT_PATH.
