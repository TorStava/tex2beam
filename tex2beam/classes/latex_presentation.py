import logging
import TexSoup

from tex2beam.classes.latex_base import LatexBase

logger = logging.getLogger(__name__)


class LatexPresentation(LatexBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_sequential_frames()

    def __str__(self):
        return (
            f"Presentation Title: {self.title}\n"
            + f"Frames: {len(self.frames)}\n"
            + f"Sections: {len(self.sections)}\n"
            + f"Word count: {self.word_count}\n"
            + f"Bullets per frame (mean): {self.bullets_per_frame}\n"
        )

    @property
    def frames(self) -> list[TexSoup.TexNode]:
        return self.soup.find_all("frame")

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def bullets(self) -> list[TexSoup.TexNode]:
        return self.soup.find_all("item")

    @property
    def bullets_per_frame(self) -> float:
        if len(self.frames) == 0:
            return 0
        return len(self.bullets) / len(self.frames)

    @property
    def words_per_frame(self) -> float:
        if self.frame_count == 0:
            return 0
        return self.word_count / self.frame_count

    @property
    def frame_titles(self) -> list:
        """Extracts the titles of frames from a LaTeX file.

        Args:
            soup: TexSoup object.

        Returns:
            Titles of frames.
        """
        try:
            frames = self.soup.find_all("frame")
            titles = []
            for frame in frames:
                title = self.get_frame_title(frame)
                if title:
                    titles.append(title)
            return titles
        except Exception as e:
            logger.warning(f"No frame titles found!\n{e}")
        return []

    @property
    def contents(self) -> list:
        """Extracts the contents of a presentation from a LaTeX file.

        Args:
            soup: TexSoup object.

        Returns:
            Contents of the presentation.
        """

        contents = []
        for frame in self.soup.find_all("frame"):
            if self.title and frame.titlepage:
                content = []
                content.append(str(self.title))
                try:
                    content.append(
                        " ".join([author.string for author in self.authors])
                    )
                except Exception as e:
                    logger.debug(f"Failed to extract authors:\n{e}")
                try:
                    content.append(
                        " ".join(
                            [
                                affiliation.string
                                for affiliation in self.affiliations
                            ]
                        )
                    )
                except Exception as e:
                    logger.debug(f"Failed to extract affiliations:\n{e}")
                try:
                    content.append(
                        " ".join(
                            [institute.string for institute in self.institutes]
                        )
                    )
                except Exception as e:
                    logger.debug(f"Failed to extract institutes:\n{e}")
                contents.append(self.clean_and_merge(content))
            else:
                frame_content = self.get_frame_contents(frame)
                if frame_content:
                    contents.append(frame_content)
        return contents

    def get_frame_contents(self, frame: TexSoup.TexSoup) -> str:
        if not isinstance(frame, TexSoup.TexNode):
            logger.error("Invalid TexSoup object.")
            return None
        content = []
        for node in frame:
            content.append(self.clean_and_merge(node.text))
        return self.clean_and_merge(content)

    def remove_sequential_frames(self, threshold: float = 0.9):
        previous_frame = None
        previous_content = None

        for i, frame in enumerate(self.soup.find_all("frame")):
            logger.debug(f"Processing frame {i}.")
            if i == 0:
                previous_frame = frame
                previous_content = self.get_frame_contents(frame).split()
                continue

            content = self.get_frame_contents(frame).split()
            if previous_frame and len(previous_content) > 0:
                common_content = [c for c in previous_content if c in content]
                logger.debug(f"Common content: {common_content}")
                if len(common_content) / len(previous_content) >= threshold:
                    logger.debug(f"Removing frame {i}.")
                    previous_frame.delete()

            previous_frame = frame
            previous_content = content

    def slide(self, index: int) -> TexSoup.TexNode:
        """Returns a slide from a LaTeX file. Alias for `frame`.

        Args:
            index (int): Index of the slide.

        Returns:
            TexSoup.TexNode: Slide.
        """
        return self.frame(index)

    def frame(self, index: int) -> TexSoup.TexNode:
        """Returns a frame from a LaTeX file.

        Args:
            index (int): Index of the frame.

        Returns:
            TexSoup.TexNode: Frame.
        """

        if index not in range(self.frame_count):
            logger.error("Invalid frame index.")
            return None
        return self.frames[index]

    def get_frame_title(self, frame: TexSoup) -> str:
        """Extracts the title of a TexSoup frame node.

        Args:
            frame: TexSoup object.

        Returns:
            Title of the frame.
        """
        try:
            if self.title and frame.titlepage:
                return str(self.title)

            title = frame.args
            if title:
                logger.debug(f"Found title in frame args: {title}")
                title = title[0].string
                if not isinstance(title, str):
                    raise TypeError("Title is not a string.")
                if "\\titlepage" in title:
                    return str(self.title) if self.title else None
                return str(title)

            title = frame.frametitle
            if title:
                logger.debug(f"Found title in \\frametitle: {title}")
                title = title.text[0]
                if not isinstance(title, str):
                    raise TypeError("Title is not a string.")
                return str(title)

        except Exception as e:
            logger.error(f"Error extracting title: {e}")
            return None

        logger.debug("Title not found!")
        return None
