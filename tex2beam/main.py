import argparse
import logging
import os
import re
from dotenv import load_dotenv

from tex2beam import utils
from tex2beam.methods.two_step import two_step_generation
from tex2beam.methods.baseline import baseline_generation
from tex2beam.methods.rag import rag_generation, rag_two_step_generation


load_dotenv()

logging.basicConfig(
    format="[%(asctime)s] %(levelname)-12s %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger()


def generate_presentation(
    report_path: str,
    api_key: str,
    method: str = "rag",
    output_path: str = None,
    n_slides: int = 7,
) -> None:
    """Converts a LaTeX report to a Beamer presentation.

    Args:
        report_path: Path to the LaTeX report.
        output_path: Path to the output Beamer presentation.
        api_key: OpenAI API key.
    """
    presentation = {}
    if method == "two-step":
        presentation = two_step_generation(
            latex_path=report_path, api_key=api_key, n_slides=n_slides
        )
    elif method == "baseline":
        presentation = baseline_generation(
            report_path=report_path, api_key=api_key, n_slides=n_slides
        )
    elif method == "rag":
        presentation["presentation"] = rag_generation(
            report_path=report_path, api_key=api_key, n_slides=n_slides
        ).presentation
    elif method == "rag-two-step":
        presentation["presentation"] = rag_two_step_generation(
            report_path=report_path, api_key=api_key, n_slides=n_slides
        ).presentation
    else:
        raise ValueError(f'Unknown method "{method}"')
    if not presentation or len(presentation) == 0:
        raise ValueError("Empty presentation generated")
    utils.write_beamer_presentation(
        presentation.get("presentation"), output_path
    )
    return presentation.get("presentation")


def convert_folder(
    input_folder: str,
    output_folder: str,
    api_key: str,
    method: str,
    refresh: bool = False,
    subfolder: str = None,
):
    """Walks through a folder and generates LaTex Beamer presentations from
    LaTeX reports.

    Args:
        input_folder: Source folder with the LaTeX reports.
        output_folder: Target folder to save the LaTeX Beamer presentations.
        api_key: OpenAI API key.
    """
    logger.debug("Starting folder walk.")

    def callback(file_path):
        if subfolder and subfolder not in file_path:
            return
        if file_path.endswith(".tex"):
            # Check if file is the main LaTeX file
            try:
                if not re.search(
                    r"\\begin{document}", open(file_path).read(), re.IGNORECASE
                ):
                    return
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

            # Generate output presentation file path
            target_file = os.path.join(
                output_folder,
                file_path.replace(input_folder, "").split("/")[1] + ".tex",
            )
            # check if target file exists
            if not refresh and os.path.exists(target_file):
                logger.debug(f"Skipping {target_file} as it already exists.")
                return

            try:
                logger.debug(f"Converting {file_path}.")
                generate_presentation(
                    report_path=file_path,
                    output_path=target_file,
                    api_key=api_key,
                    method=method,
                )
            except Exception as e:
                logger.error(
                    f"Error generating presentation for {file_path}: {e}"
                )

    logger.debug(f"Converting LaTeX files in {input_folder}.")
    utils.folder_walker(input_folder, callback)


def main(args: argparse.Namespace) -> None:
    """Main function.

    Args:
        args: Arguments from command-line call.
    """
    logger.info("Starting main function.")
    if args.source_folder:
        convert_folder(
            input_folder=args.source_folder,
            output_folder=args.target_folder,
            method=args.method,
            api_key=args.api_key,
            refresh=args.refresh,
            subfolder="paper-latex",
        )
    elif args.pdf_path:
        generate_presentation(
            report_path=args.pdf_path,
            output_path=args.output_path,
            method=args.method,
            api_key=args.api_key,
        )
    else:
        raise ValueError("Invalid arguments.")
    logger.info("Finished main function.")


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
    parser.add_argument(
        "-m",
        "--method",
        type=str,
        help="Method to use for generating the Beamer presentation",
        choices=["baseline", "rag", "two-step", "rag-two-step"],
        default="two-step",
    )
    # latex-path and source-folder are mutually exclusive
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-l", "--latex-path", type=str, help="Path to the LaTeX file"
    )
    group.add_argument(
        "-s",
        "--source-folder",
        type=str,
        help="Source folder with the LaTeX reports",
    )
    # output-path and target-folder are mutually exclusive
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-o",
        "--output-path",
        type=str,
        help="Path to the output Beamer file",
    )
    group.add_argument(
        "-t",
        "--target-folder",
        type=str,
        help="Target folder to save the Beamer files",
    )

    return parser.parse_args()


if __name__ == "__main__":
    load_dotenv()
    args = parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    # Override API_KEY if set on command line arguments
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key not set.")
        args.api_key = os.environ["OPENAI_API_KEY"]
    main(args)
