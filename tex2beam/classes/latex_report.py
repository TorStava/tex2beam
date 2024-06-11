from tex2beam.classes.latex_base import LatexBase


class LatexReport(LatexBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return (
            f"Report Title: {self.title}\n"
            + f"Authors: {self.authors}\n"
            + f"Affiliations: {self.affiliations}\n"
            + f"Word count: {self.word_count}\n"
            + f"TOC: {self.toc}\n"
        )
