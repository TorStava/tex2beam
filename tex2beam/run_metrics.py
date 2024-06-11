import argparse
import logging

from tex2beam.metrics.utils import calculate_metrics, folder_metrics
from tex2beam.classes.latex_presentation import LatexPresentation

logger = logging.getLogger()


def main(args: argparse.Namespace) -> None:
    """Main function.

    Args:
        args: Arguments from command-line call.
    """
    logger.info("Starting main function.")
    if args.predictions_folder:
        folder_metrics(
            candidate_folder=args.predictions_folder,
            reference_folder=args.references_folder,
            output_file=args.output,
            match=args.match,
            scoring_method=args.scoring_method,
            f1_threshold=args.threshold,
        )
    elif args.predictions_file:
        results = calculate_metrics(
            LatexPresentation(args.predictions_file).contents,
            LatexPresentation(args.references_file).contents,
            f1_threshold=args.threshold,
            scoring_method=args.scoring_method,
        )
        logger.info(f"Results: {results}")
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
        dest="debug",
        help="Debugging mode",
        default=False,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to the output file",
    )
    parser.add_argument(
        "-m",
        "--match",
        type=str,
        help="Match type",
        default="title",
        choices=["title", "content"],
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        help="F1 matching threshold value for BERTscore",
        default="0.7",
    )
    parser.add_argument(
        "-s",
        "--scoring-method",
        type=str,
        help="Scoring method",
        default="bert",
        choices=["rouge", "bert"],
    )
    # latex-path and source-folder are mutually exclusive
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-p",
        "--predictions-file",
        type=str,
        help="Path to generated LaTeX Beamer presentation",
    )
    group.add_argument(
        "-f",
        "--predictions-folder",
        type=str,
        help="Folder with the generated LaTeX Beamer presentations",
    )
    # output-path and target-folder are mutually exclusive
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-r",
        "--references-file",
        type=str,
        help="Path to the ground-truth LaTeX Beamer presentation",
    )
    group.add_argument(
        "-e",
        "--references-folder",
        type=str,
        help="Folder with the ground-truth LaTeX Beamer presentations",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    main(args)
