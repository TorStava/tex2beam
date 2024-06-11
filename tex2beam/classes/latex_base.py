import logging
import os
import TexSoup

from tex2beam import utils

logger = logging.getLogger(__name__)


class LatexBase:
    """Base class for a LaTeX documents."""

    def __init__(self, filepath: str = None, source: str = None):
        """Initializes the LatexBase class.

        Args:
            filepath: Path to the LaTeX file.
            source: LaTeX source code.
        """
        if source:
            self.soup = TexSoup.TexSoup(source)
        elif filepath:
            self.filepath = filepath
            self.soup = self.make_soup()
        else:
            raise ValueError("Either filepath or source must be provided.")

    @staticmethod
    def clean_and_merge(content: list) -> str:
        if isinstance(content, str):
            return content
        return " ".join(content).replace("\n", "").strip()

    @property
    def bibliography(self):
        return self.soup.find("thebibliography")

    @property
    def bibitems(self):
        if not self.bibliography:
            return {}
        items = {}
        start_parse = False
        for node in self.bibliography:
            if (
                isinstance(node, TexSoup.data.TexNode)
                and node.name == "bibitem"
            ):
                key = str(node.args[0].string)
                items[key] = [node]
                start_parse = True
            if start_parse:
                items[key].append(node)
        return items

    @property
    def citations(self):
        return self.soup.find_all("cite")

    @property
    def figures(self):
        return self.soup.find_all("figure")

    @property
    def tables(self):
        return self.soup.find_all("table")

    @property
    def toc(self) -> list:
        toc = []
        for section in self.sections:
            toc.append(
                {
                    "section": section["section"],
                    "subsections": [
                        subsection["section"]
                        for subsection in section["subsections"]
                    ],
                }
            )
        return toc

    @property
    def word_count(self) -> int:
        """Calculates the word count of the report.

        Returns:
            Word count.
        """
        if not self.soup.document:
            logger.error("No document section found.")
            return None
        return len(" ".join(self.soup.document.text).split())

    @property
    def sections(self) -> list:
        if not self.soup.document:
            logger.error("No document section found.")
            return []

        sections: list = []
        parse = False
        is_section = False
        is_subsection = False
        labels = [
            "label",
            "footnote",
            "cite",
            "citet",
            "citep",
            "ref",
            "$",
            "emph",
            "textit",
            "textbf",
            "paragraph",
            "tilde",
        ]
        symbols = [
            "in",
            "alpha",
            "phi",
            "perp",
            "cdot",
            "times",
            "log",
            "exp",
            "right",
            "sqrt",
            "theta",
            "sum",
            "Phi",
            "tau",
            "Theta",
        ]

        def append(data):
            try:
                if is_section:
                    sections[-1]["content"] += data
                elif is_subsection:
                    sections[-1]["subsections"][-1]["content"] += data
            except Exception as e:
                logger.error(f"Error appending data: {e}")

        for node in self.soup.document.descendants:
            if (
                isinstance(node, TexSoup.data.TexNode)
                and node.name == "section"
            ):
                parse = True
            if not parse:
                continue
            if (
                isinstance(node, TexSoup.data.TexNode)
                and node.name == "section"
            ):
                sections.append(
                    {
                        "section": node.string,
                        "content": "",
                        "subsections": [],
                        "figures": [],
                    }
                )
                is_section = True
                is_subsection = False
            elif (
                isinstance(node, TexSoup.data.TexNode)
                and node.name == "subsection"
            ):
                try:
                    sections[-1]["subsections"].append(
                        {
                            "section": node.string,
                            "content": "",
                            "subsubsections": [],
                            "figures": [],
                        }
                    )
                except Exception as e:
                    logger.error(f"Error adding subsection: {e}")
                is_section = False
                is_subsection = True
            elif isinstance(node, str):
                append(node.strip("\n"))
            elif isinstance(node, TexSoup.data.TexNode) and node.name in labels:
                append(str(node).strip("\n"))
            elif (
                isinstance(node, TexSoup.data.TexNode) and node.name == "figure"
            ):
                append(str(node))
            elif isinstance(node, TexSoup.data.TexNode) and node.name in [
                "align",
                "align*",
            ]:
                append(str(node))
            elif (
                isinstance(node, TexSoup.data.TexNode) and node.name in symbols
            ):
                append(f"${node}$")
            elif isinstance(node, TexSoup.data.TexNode) and node.name in [
                "bibliography",
                "bibliographystyle",
                "appendix",
            ]:
                parse = False
            elif isinstance(node, TexSoup.data.TexNode):
                append(str(node))
            else:
                logger.warning(
                    f"Unknown node: {type(node)}, {node.name}, {node}"
                )
        return sections

    @property
    def title(self) -> str:
        """Extracts the title from a LaTeX file.

        Args:
            soup: TexSoup object.

        Returns:
            Title.
        """
        title = None
        try:
            if self.soup.find("title"):
                title = self.soup.find("title").text
            elif self.soup.find("icmltitle"):
                title = self.soup.find("icmltitle").text
            elif self.soup.find("icmltitlerunning"):
                title = self.soup.find("icmltitlerunning").text
            else:
                logger.debug("No title found.")
        except Exception as e:
            logger.error(f"Error extracting title: {e}")
        try:
            if isinstance(title, list):
                title = title[0]
        except Exception as e:
            logger.error(f"Error converting title to string: {e}")
        return title

    @property
    def authors(self) -> list:
        """Extracts authors from a LaTeX file.

        Args:
            soup: TexSoup object.

        Returns:
            Authors.
        """
        authors = None
        try:
            if self.soup.find("author"):
                authors = self.soup.find_all("author")
            elif self.soup.find("icmlauthor"):
                authors = self.soup.find_all("icmlauthor")
        except Exception as e:
            logger.error(f"Error extracting authors: {e}")
        if authors:
            return authors
        else:
            logger.debug("No authors found.")
        return []

    @property
    def affiliations(self) -> list:
        """Extracts affiliations from a LaTeX file.

        Args:
            soup: TexSoup object.

        Returns:
            affiliations.
        """
        affiliations = []
        try:
            if self.soup.find("affiliation"):
                affiliations = self.soup.find_all("affiliation")
            elif self.soup.find("icmlaffiliation"):
                affiliations = self.soup.find_all("icmlaffiliation")
        except Exception as e:
            logger.error(f"Error extracting affiliations: {e}")
        return affiliations

    @property
    def institutes(self) -> list:
        """Extracts institutes from a LaTeX file.

        Args:
            soup: TexSoup object.

        Returns:
            Institutes.
        """
        institutes = None
        try:
            if self.soup.find("institute"):
                institutes = self.soup.find_all("institute")
            elif self.soup.find("icmlinstitute"):
                institutes = self.soup.find_all("icmlinstitute")
        except Exception as e:
            logger.error(f"Error extracting institutes: {e}")
        if institutes:
            return institutes
        else:
            logger.debug("No institutes found.")
        return []

    def make_soup(self):
        """Parses the LaTeX file into a TexSoup object.

        Returns:
            TexSoup object.
        """
        with open(self.filepath, "r") as file:
            soup = self.resolve_imports(file)
        return soup

    def get_section(self, section_title: str) -> dict:
        """Extract a named section from the report."""
        for section in self.sections:
            if section["section"] == section_title:
                return section
            for subsection in section["subsections"]:
                if subsection["section"] == section_title:
                    return subsection
        return {}

    def resolve_imports(self, file):
        """Resolves imports in the report."""

        soup = TexSoup.TexSoup(file, tolerance=1)

        cwd = os.path.dirname(file.name)

        def check_filename(filename):
            if not filename.endswith(".tex"):
                return filename + ".tex"
            return filename

        # resolve subimports
        for _subimport in soup.find_all("subimport"):
            logger.debug(
                f"Resolving subimport: {_subimport.args[0]}{_subimport.args[1]}"
            )
            path = _subimport.args[0] + _subimport.args[1]
            _subimport.replace_with(*self.resolve_imports(open(path)).contents)

        # resolve imports
        for _import in soup.find_all("import"):
            filename = check_filename(_import.args[0].string)
            logger.debug(f"Resolving import: {filename}")
            _import.replace_with(*self.resolve_imports(open(filename)).contents)

        # resolve includes
        for _include in soup.find_all("include"):
            filename = check_filename(_include.args[0].string)
            logger.debug(f"Resolving include: {filename}")
            _include.replace_with(
                *self.resolve_imports(open(filename)).contents
            )

        # resolve inputs
        for _input in soup.find_all("input"):
            filename = check_filename(_input.args[0].string)
            logger.debug(f"Resolving input: {filename}")
            _input.replace_with(
                self.resolve_imports(open(os.path.join(cwd, filename)))
            )

        return TexSoup.TexSoup(utils.clean_texfile(str(soup)), tolerance=1)

    def get_citation(self, key):
        for bibitem in self.bibitems:
            if key in bibitem.string:
                return bibitem.string
        return None

    def get_bibitem(self, key, bibliography: dict):
        if key in bibliography:
            return bibliography[key]

    def add_bibliography(self, bibliography):
        if self.bibliography:
            logger.warning("Bibliography already exists.")
            return
        self.soup.document.insert(-1, bibliography.copy())

    def add_bibitem(self, bibitem):
        if not self.bibliography:
            logger.warning("No bibliography found.")
            self.create_bibliography([bibitem])
            return
        self.bibliography.insert(-1, bibitem.copy())

    def create_bibliography(self, bibitems):
        bibliography = TexSoup.TexNode("thebibliography", *bibitems)
        self.add_bibliography(bibliography)

    def generate_bibliography(self, bibliography):
        for citation in self.citations:
            key = citation.string
            bibitem = self.get_bibitem(key, bibliography)
            if bibitem:
                self.add_bibitem(bibitem)
            else:
                logger.warning(f"No bibitem found for {key}")

    def replace_bibliography(self, bibliography):
        if self.bibliography:
            self.bibliography.replace_with(bibliography.copy())
        else:
            logger.warning("No bibliography found.")

    def save(self, filepath):
        with open(filepath, "w") as file:
            file.write(str(self.soup))
        logger.info(f"Saved to {filepath}")
        return filepath
