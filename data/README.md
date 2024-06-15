# Data

The dataset can be downloaded here (2.35 GB): https://drive.google.com/drive/folders/1kG0tcNenHC9Yr0eIcGl1kNw2flkF04Xh?usp=sharing

Unpack the archive in this folder.

The files are organized in subfolders:

    lastname-year-conference
        paper-latex 
        paper-pdf
        presentation-latex
        presentation-pdf

The paper-latex folder contains the report $\LaTeX$ source files downloaded from arXiv.xom in .tar.gz format. 

The paper-pdf folder contains the report in PDF format downloaded from arXiv.org.

The presentation-pdf folder contains the presentation in PDF format, downloaded from the respective conference websites.

The presentation-latex folder contains the presentation in $\LaTeX$ Beamer format, converted from the original PDF presentation, using the `pdf2beam` module that's part of the `tex2beam` package. The `tex2beam` package can be downloaded from GitHub: https://github.com/TorStava/tex2beam