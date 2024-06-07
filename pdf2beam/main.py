import argparse
import json
import logging
import os

from dotenv import load_dotenv
from openai import OpenAI
from pdf2docx import Converter


logging.basicConfig(
    format="[%(asctime)s] %(levelname)-12s %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger()


def read_pdf_presentation(pdf_path: str) -> dict:
    """Reads a PDF file and returns its content.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Content of the PDF file.
    """
    logger.debug(f"Reading PDF file: {pdf_path}")
    converter = Converter(pdf_path)
    converter.parse(**converter.default_settings)
    presentation = converter.store()
    text_contents = extract_text_contents(presentation)
    return text_contents


def get_text(obj, key="text"):
    # Recursive function to find text within "blocks"
    slide_text = []
    if isinstance(obj, dict):  # If the current object is a dictionary
        for k, v in obj.items():
            if k == key:
                slide_text.append(v)  # Add the text to the list
            elif isinstance(v, (dict, list)):
                # Recurse into dictionaries/lists
                slide_text.extend(get_text(v, key))
    elif isinstance(obj, list):  # If the current object is a list
        for item in obj:
            # Recurse into each item
            slide_text.extend(get_text(item, key))
    return slide_text


def extract_text_contents(presentation: Converter) -> dict:
    """Extracts text contents from a presentation.

    Args:
        presentation: Presentation.

    Returns:
        Text contents of the presentation.
    """
    logger.info("Extracting text contents.")
    document: dict = {"frames": []}
    for page in presentation["pages"]:
        document["frames"].append([])
        frame = document["frames"][-1]
        for section in page["sections"]:
            for column in section["columns"]:
                # page_contents.append(get_text(column))
                for block in column["blocks"]:
                    frame.append(get_text(block))
    return document


def convert_to_latex(presentation: dict, api_key: str, retries: int = 3) -> str:
    """Converts a presentation to LaTeX using chatGPT API.

    Args:
        presentation: Presentation.

    Returns:
        LaTeX code.
    """
    logger.info("Converting presentation to LaTeX.")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """Convert the presentation to LaTeX Beamer.
                     Ensure to parse the title slide properly.
                     Include all text and complete all slides.""",
            },
            {"role": "user", "content": f"{json.dumps(presentation)}"},
        ],
    )
    content = response.choices[0].message.content

    logger.info("Beamer presentation generated.")
    # Check if chatGPT is been lazy and not generating the full LaTeX code
    unwanted_phrases = [
        "% Include all remaining",
        "% Include remaining",
        "% Include more",
        "% Include all other",
        "% Add more slides",
        "% Add more content",
        "% Add remaining",
        "% Adding more",
        "% Adding remaining",
        "% Content for this slide is missing",
    ]
    for phrase in unwanted_phrases:
        if phrase in content:
            if retries > 0:
                logger.info("Retrying conversion.")
                return convert_to_latex(presentation, api_key, retries - 1)
            else:
                raise ValueError(
                    "chatGPT did not generate the full LaTeX code."
                )

    return content


def write_latex(latex_code: str, output_path: str) -> None:
    """Writes LaTeX code to a file.

    Args:
        latex_code: LaTeX code.
        output_path: Path to the output LaTeX file.
    """
    logger.info(f"Writing LaTeX code to file: {output_path}")
    # Create target folder if not existing
    target_folder = os.path.dirname(output_path)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        logger.info(f"Created target folder: {target_folder}")
    with open(output_path, "w") as file:
        file.write(latex_code)
        logger.info(f"LaTeX code written to file: {output_path}")


def convert(pdf_path: str, output_path: str, api_key: str) -> None:
    """Main function.

    Args:
        args: Arguments from command-line call.
    """
    presentation = read_pdf_presentation(pdf_path)
    latex_code = convert_to_latex(presentation, api_key)
    write_latex(latex_code, output_path)


def main(args: argparse.Namespace) -> None:
    """Main function.

    Args:
        args: Arguments from command-line call.
    """
    logger.info("Starting main function.")
    if args.source_folder:
        folder_walk(args.source_folder, args.target_folder, args.api_key)
    elif args.pdf_path:
        convert(args.pdf_path, args.output_path, args.api_key)
    else:
        raise ValueError("Invalid arguments.")
    logger.info("Finished main function.")


def folder_walk(source_folder: str, target_folder: str, api_key: str) -> None:
    """Walks through a folder and converts all PDF files to LaTeX.

    Args:
        source_folder: Source folder with the PDF files to convert.
        target_folder: Target folder to save the LaTeX files.
    """
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith("-presentation.pdf"):
                target_file = os.path.join(
                    target_folder, file.replace(".pdf", ".tex")
                )
                # check if target file exists
                if not args.refresh and os.path.exists(target_file):
                    logger.info(f"Skipping {file} as it already exists.")
                    continue
                try:
                    convert(
                        pdf_path=os.path.join(root, file),
                        output_path=target_file,
                        api_key=api_key,
                    )
                except Exception as e:
                    logger.error(f"Error converting {file}: {e}")


def parse_args() -> argparse.Namespace:
    """Parses arguments from command-line call.

    Returns:
        Arguments from command-line call.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Debugging mode",
        default=False,
    )
    parser.add_argument("-k", "--api-key", type=str, help="OpenAI API key")
    parser.add_argument(
        "-r",
        "--refresh",
        action="store_true",
        help="Refresh all LaTeX files in the target folder",
        default=False,
    )
    # pdf-path and source-folder are mutually exclusive
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-p",
        "--pdf-path",
        type=str,
        help="Path to the PDF file",
    )
    group.add_argument(
        "-s",
        "--source-folder",
        help="Source folder with the PDF files to convert",
        type=str,
    )
    # output-path and target-folder are mutually exclusive
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-o",
        "--output-path",
        type=str,
        help="Path to the output LaTeX file",
    )
    group.add_argument(
        "-t",
        "--target-folder",
        help="Target folder to save the LaTeX files",
        type=str,
    )

    return parser.parse_args()


if __name__ == "__main__":
    load_dotenv()
    args = parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    # Use OpenAI API key from environment variable if not provided
    if os.environ.get("OPENAI_API_KEY", None):
        args.api_key = os.environ["OPENAI_API_KEY"]
    main(args)
