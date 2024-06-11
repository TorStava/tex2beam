import json
import logging
import os
import re
import tarfile

from TexSoup import TexSoup
from TexSoup.data import TexNode
from typing import Callable

logger = logging.getLogger(__name__)


def clean_texfile(texfile: str) -> str:
    """Cleans a LaTeX file.

    Args:
        texfile: LaTeX file.

    Returns:
        Cleaned LaTeX file.
    """
    logger.debug("Cleaning LaTeX file.")
    # Split string into lines
    tmp = texfile.split("\n")
    # Remove comments
    tmp = [line.strip() for line in tmp if not line.startswith("%")]
    # Remove empty lines
    tmp = [line for line in tmp if len(line) > 0]
    # Remove multiple spaces
    tmp = [re.sub(r" +", " ", line) for line in tmp]
    # Join lines back together
    return "\n".join(tmp)


def read_file(file_path: str) -> str:
    """Reads a file and returns its content.

    Args:
        file_path: Path to the file.

    Returns:
        Content of the file.
    """
    logger.debug(f"Reading file: {file_path}")
    try:
        with open(file_path, "r") as file:
            file_content = file.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None
    return file_content


def write_file(content: str, output_path: str) -> None:
    """Writes content to a file.

    Args:
        content: Content to write to file.
        output_path: Path to the output file.
    """
    logger.debug(f"Writing content to file: {output_path}")
    target_folder = os.path.dirname(output_path)
    # Create target folder if not existing
    if not os.path.exists(target_folder):
        try:
            os.makedirs(target_folder)
            logger.debug(f"Created target folder: {target_folder}")
        except Exception as e:
            logger.error(f"Error creating target folder: {e}")
    # Write content to file
    with open(output_path, "w") as file:
        try:
            file.write(content)
            logger.info(f"Content written to file: {output_path}")
        except Exception as e:
            logger.error(f"Error writing content to file: {e}")


def write_dict_to_jsonl(content: dict, file_path: str) -> None:
    """Writes a Python dictionary to a JSONL file.

    Args:
        content: Python dictionary to be written to file.
        file_path: Path to the file.
    """
    logger.debug(f"Writing content to {file_path}")
    # Append to file if exists, otherwise create new file
    mode = "a" if os.path.exists(file_path) else "w"
    with open(file_path, mode) as file:
        json.dump(content, file, ensure_ascii=False)
        file.write("\n")


def read_dict_from_jsonl(file_path: str) -> dict:
    """Reads a JSONL file and returns its content as a dictionary.

    Args:

    Returns:
    """
    content = {}
    with open(file_path, "r") as f:
        for line in f:
            content.update(json.loads(line))
    return content


def folder_walker(
    path: str,
    callback: Callable = None,
    extensions: str = None,
    subfolder: str = None,
    return_files: bool = True,
    **kwargs,
) -> list:
    """Walks through a folder and return the path of files to the callback
    function.

    Args:
        path: Path to the folder.
        callback: Callback function.
        extensions: List of extensions to filter files. Comma separated.
        **kwargs: Additional arguments to pass to the callback function.

    Raises:
        FileNotFoundError: If the path does not exist.
        NotADirectoryError: If the path is not a folder.
    """
    logger.debug(f"Starting folder walk at {path}.")
    # Check if path exists and is a folder
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path {path} does not exist.")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Path {path} is not a folder.")
    file_paths = []
    for root, dirs, files in os.walk(path):
        if subfolder:
            if subfolder not in root:
                continue
        if extensions:
            files = [
                file
                for file in files
                if file.endswith(tuple(extensions.split(",")))
            ]
        if callback:
            for file in files:
                callback(os.path.join(root, file), **kwargs)
        file_paths.extend([os.path.join(root, file) for file in files])
    if return_files:
        return file_paths
    return None


def soupify(file_path: str) -> TexSoup:
    """Creates a TexSoup object from a LaTeX file.

    Args:
        file_path: Path to the LaTeX file.

    Returns:
        TexSoup object.
    """
    logger.debug(f"Creating TexSoup object from {file_path}.")
    try:
        soup = TexSoup(read_file(file_path))
        return soup
    except Exception as e:
        logger.error(f"Error creating TexSoup object: {e}")
    return None


def make_soup(texfile: str) -> TexSoup:
    """Creates a TexSoup object from a LaTeX file.

    Args:
        texfile: LaTeX file.

    Returns:
        TexSoup object.
    """
    logger.debug("Creating TexSoup object.")
    try:
        soup = TexSoup(texfile)
        return soup
    except Exception as e:
        logger.error(f"Error creating TexSoup object: {e}")
    return None


def flatten_soup(soup: TexSoup, work_folder: str) -> list:
    """Flattens a TexSoup object.

    Args:
        soup: TexSoup object.

    Returns:
        Flattened TexSoup object.
    """
    if not soup:
        return None
    while soup.input:
        filename = soup.input.text[0]
        if not filename.endswith(".tex"):
            filename = filename + ".tex"
        include_file = os.path.join(work_folder, filename)
        include_soup = soupify(include_file)
        soup.input.replace_with(flatten_soup(include_soup, work_folder))
    return make_soup(str(soup))


def resolve(filehandle):
    """Resolve all import and update the parse tree.

    source:
    https://github.com/alvinwan/TexSoup/blob/master/examples/resolve_imports.py
    """
    # soupify
    soup = TexSoup(filehandle)

    cwd = os.path.dirname(filehandle.name)

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
        _subimport.replace_with(*resolve(open(path)).contents)

    # resolve imports
    for _import in soup.find_all("import"):
        filename = check_filename(_import.args[0].string)
        logger.debug(f"Resolving import: {filename}")
        _import.replace_with(*resolve(open(filename)).contents)

    # resolve includes
    for _include in soup.find_all("include"):
        filename = check_filename(_include.args[0].string)
        logger.debug(f"Resolving include: {filename}")
        _include.replace_with(*resolve(open(filename)).contents)

    # resolve inputs
    for _input in soup.find_all("input"):
        filename = check_filename(_input.args[0].string)
        logger.debug(f"Resolving input: {filename}")
        _input.replace_with(
            *resolve(open(os.path.join(cwd, filename))).contents
        )

    return soup


def walk_the_soup(soup):
    """Walks through a TexSoup object.

    Args:
        soup (_type_): _description_
    """
    for child in soup.children:
        if child.name:
            print(child.name)
        walk_the_soup(child)


def get_title(soup: TexSoup) -> str:
    """Extracts the title from a LaTeX file.

    Args:
        soup: TexSoup object.

    Returns:
        Title.
    """
    title = None
    try:
        if soup.find("title"):
            title = soup.find("title").text
        elif soup.find("icmltitle"):
            title = soup.find("icmltitle").text
        elif soup.find("icmltitlerunning"):
            title = soup.find("icmltitlerunning").text
        else:
            logger.warning("No title found.")
    except Exception as e:
        logger.error(f"Error extracting title: {e}")
    try:
        if isinstance(title, list):
            title = title[0]
    except Exception as e:
        logger.error(f"Error converting title to string: {e}")
    logger.debug(f"Title: {title}")
    return title


def get_title_from_texfile(filepath: str = None) -> str:
    title = None
    try:
        title = get_title(make_soup(read_file(filepath)))
    except Exception as e:
        logger.error(f"Error extracting title: {e}")
    if title:
        return title
    return None


def get_authors(soup: TexSoup) -> str:
    """Extracts authors from a LaTeX file.

    Args:
        soup: TexSoup object.

    Returns:
        Authors.
    """
    authors = None
    try:
        if soup.find("author"):
            authors = soup.find("author").text
        elif soup.find("icmlauthor"):
            authors = soup.find("icmlauthor").text
        else:
            authors = ""
    except Exception as e:
        logger.error(f"Error extracting authors: {e}")
    if authors:
        return authors
    else:
        logger.warning("No authors found.")
    return None


def get_sections(soup: TexSoup) -> list:
    """Extracts sections from a LaTeX file.

    Args:
        soup: TexSoup object.

    Returns:
        Sections.
    """
    sections = None
    try:
        sections = soup.find_all("section")
        sections = [section.text[0] for section in sections if section.text]
    except Exception as e:
        logger.error(f"Error extracting sections: {e}")
    if sections:
        return sections
    else:
        logger.warning("No sections found.")
    return None


def clean_and_merge(content: list) -> str:
    return " ".join(content).replace("\n", "").strip()


def get_frame_contents(frame: TexSoup) -> str:
    """Extracts the content of a frame from a LaTeX file.

    Args:
        frame: TexSoup object.

    Returns:
        Content of the frame.
    """
    if not isinstance(frame, TexNode):
        logger.error("Invalid TexSoup object.")
        return None
    content = []
    for node in frame:
        content.append(clean_and_merge(node.text))
    return clean_and_merge(content)


def get_presentation_contents(soup: TexSoup) -> list:
    """Extracts the contents of a presentation from a LaTeX file.

    Args:
        soup: TexSoup object.

    Returns:
        Contents of the presentation.
    """
    if not isinstance(soup, TexNode):
        logger.error("Invalid TexSoup object.")
        return None
    contents = []
    for frame in soup.find_all("frame"):
        content = get_frame_contents(frame)
        if content:
            contents.append(content)
    return contents


def remove_sequential_frames(soup: TexSoup, threshold: float = 0.9) -> TexSoup:
    # Check if all the content of the previous slide is contained in the
    # current slide. If so, drop the previous slide.
    # Use BERTscore with a threshold for comparing content.
    # NOTE that this function modifies the soup object in place.

    if not soup:
        logger.error("Invalid TexSoup object.")
        return

    previous_frame = None
    previous_content = None

    for i, frame in enumerate(soup.find_all("frame")):
        if i == 0:
            previous_frame = frame
            previous_content = get_frame_contents(frame)
            continue

        content = get_frame_contents(frame)
        if previous_frame and len(previous_content) > 0:
            common_content = [c for c in previous_content if c in content]
            if len(common_content) / len(previous_content) >= 0.95:
                previous_frame.delete()

        previous_frame = frame
        previous_content = content


def get_frames(soup: TexSoup) -> list:
    """Extracts frames from a LaTeX file.

    Args:
        soup: TexSoup object.

    Returns:
        Frames.
    """
    try:
        frames = soup.find_all("frame")
        frames = [get_frame_contents(frame) for frame in frames]
        return frames
    except Exception as e:
        logger.error(f"Error extracting frames: {e}")
    logger.warning("No frames found.")
    return []


def parse_latex_report(texfile: str, outfile: str = None) -> dict:
    """Parses a LaTeX report file.

    Args:
        texfile: LaTeX report file.

    Returns:
        Parsed LaTeX file.
    """
    logger.info(f"Parsing LaTeX file {texfile}")
    contents = read_file(texfile)
    soup = make_soup(contents)
    title = get_title(soup)
    authors = get_authors(soup)
    sections = get_sections(soup)
    parsed_content = {
        "file": texfile,
        "title": title,
        "authors": authors,
        "sections": sections,
    }
    if outfile:
        write_dict_to_jsonl(parsed_content, outfile)
    return parsed_content


def extract_archive(
    filepath: str, destination: str = None, subfolder: str = None
) -> None:
    """Extracts a tar archive.

    Args:
        filepath: Path to the tar archive.
        destination: Destination folder.
        subpath: Subpath to extract to.
    """
    logger.debug(f"Extracting archive: {filepath}")
    if not destination:
        destination = os.path.dirname(filepath)
    if subfolder:
        destination = os.path.join(destination, subfolder)
    try:
        with tarfile.open(filepath, "r") as tar:
            tar.extractall(destination)
            logger.info(f"Archive extracted to: {destination}")
    except Exception as e:
        logger.warning(f"Error extracting archive {filepath}: {e}")


def group_files_by_folder(files: list, parent_path: str) -> dict:
    """Groups files by folder.

    Args:
        files (list): list of file paths
        parent_path (str): parent path

    Returns:
        dict: dictionary of folders and files
    """
    folders: dict[str, list] = {}
    for file in files:
        folder = file.strip(parent_path).split("/")[1]
        if folder not in folders:
            folders[folder] = []
        folders[folder].append(file)
    return folders


def determine_main_tex_file(files: list) -> str:
    """Determines the main tex file from a list of files.

    Args:
        files (list): List of files

    Returns:
        str: Main tex file
    """
    for file in files:
        if file.endswith(".tex"):
            # Check if file is the main LaTeX file
            try:
                if re.search(
                    r"\\begin{document}", open(file).read(), re.IGNORECASE
                ):
                    return file
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
    logger.warning("Main .tex file not found.")
    return None


def remove_duplicates(elements: list) -> list:
    return list(dict.fromkeys(elements))


def write_beamer_presentation(
    beamer_presentation: str, output_path: str
) -> None:
    """Writes a Beamer presentation to a file.

    Args:
        beamer_presentation: Beamer presentation.
        output_path: Path to the output Beamer file.
    """
    logger.debug(f"Writing Beamer presentation to file: {output_path}")
    # Create target folder if not existing
    target_folder = os.path.dirname(output_path)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        logger.debug(f"Created target folder: {target_folder}")
    with open(output_path, "w") as file:
        try:
            file.write(beamer_presentation)
            logger.debug(f"LaTeX code written to file: {output_path}")
        except Exception as e:
            logger.error(f"Error writing LaTeX code to file: {e}")


def count_folders(folder_path):
    count = 0
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            count += 1
    return count
