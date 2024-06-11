import logging
import numpy as np
import os
import pandas as pd

from scipy.stats import kendalltau

from tex2beam import utils
from tex2beam.classes.latex_presentation import LatexPresentation
from tex2beam.classes.latex_report import LatexReport
from tex2beam.metrics.rouge_score import calculate_rouge_score
from tex2beam.metrics.bert_score import calculate_bert_score

logger = logging.getLogger(__name__)


def scoring(predictions: list, references: list, method="ROUGE") -> dict:
    """Scores two strings using ROUGE and BERTScore. For each prediction a score
    is calculated against each of the references.

    Args:
        predictions: List.
        references: List.

    Returns:
        Dictionary with ROUGE and BERTScore metrics.
    """
    logger.info(f"Evaluating metrics using {method}.")

    # Check if predictions and references are not empty
    if not predictions:
        raise ValueError("Predictions is empty.")
    if not references:
        raise ValueError("References is empty.")

    scores = {}
    for pred in predictions:
        if not pred:
            raise ValueError("Prediction is empty.")
        scores[pred] = {}
        for ref in references:
            if not ref:
                raise ValueError("Reference is empty.")
            if method.lower() == "bert":
                # Evaluate BERTScore
                scores[pred][ref] = calculate_bert_score([pred], [ref])
            elif method.lower() == "rouge":
                # Evaluate ROUGE
                scores[pred][ref] = calculate_rouge_score([pred], [ref])

    return scores


def match_elements(
    candidate_elements: list,
    reference_elements: list,
    f1_threshold: float = 0.6,
    decimals: int = 3,
) -> dict:
    """Match candidate elements to reference elements based on BERTScore F1
    score.

    Args:
        candidate_elements (list): list of candidate elements
        reference_elements (list): list of reference elements
        f1_threshold (float, optional): F1 threshold for matching. Defaults to 0.6.

    Returns:
        dict: dictionary of matched elements
    """
    logger.debug("Matching candidate elements to reference elements.")

    # Remove duplicates while preserving order
    candidate_elements = list(dict.fromkeys(candidate_elements))
    reference_elements = list(dict.fromkeys(reference_elements))

    # Generate possible permutations
    permutations = []
    for i, ct in enumerate(candidate_elements):
        for j, rt in enumerate(reference_elements):
            permutations.append((ct, i, rt, j))

    # Calculate BERTScore for all permutations
    bertscore = calculate_bert_score(
        [cand for cand, _, ref, _ in permutations],
        [ref for cand, _, ref, _ in permutations],
    )

    # Update function to append matches
    def append(cand, i, ref, j, precision, recall, f1):
        matches.append(
            {
                "candidate": {"element": cand, "index": i},
                "reference": {"element": ref, "index": j},
                "score": {
                    "precision": round(precision, decimals),
                    "recall": round(recall, decimals),
                    "f1": round(f1, decimals),
                },
            }
        )

    matches = []
    for k, (cand, i, ref, j) in enumerate(permutations):
        # Check for exact matches
        if cand == ref:
            append(cand, i, ref, j, 1.0, 1.0, 1.0)
            continue
        else:
            precision = bertscore["precision"][k]
            recall = bertscore["recall"][k]
            f1 = bertscore["f1"][k]
        if f1 >= f1_threshold:
            append(cand, i, ref, j, precision, recall, f1)
    return matches


def calculate_confusion_matrix(
    candidate_titles: list, reference_titles: list, matches: dict
) -> np.array:
    """Generate confusion matrix based on matched elements.

    Args:
        candidate_titles (list): candidate elements
        reference_titles (list): reference elements
        matches (dict): matched elements

    Returns:
        np.array: confusion matrix
    """
    logger.debug("Generating confusion matrix.")
    TP, FP, FN, TN = 0, 0, 0, 0
    TP = len(matches)
    FP = len(set(candidate_titles)) - len(
        set([match["candidate"]["element"] for match in matches])
    )
    FN = len(set(reference_titles)) - len(
        set([match["reference"]["element"] for match in matches])
    )

    return np.array([[TP, FP], [FN, TN]])


def calculate_precision_recall_f1(
    confusion_matrix: np.array, decimals: int = 3
) -> dict:
    """Calculate precision, recall and F1 score based on confusion matrix.

    Args:
        confusion_matrix (np.array): confusion matrix

    Returns:
        dict: dictionary of precision, recall and F1 score
    """
    logger.debug("Calculating precision, recall and F1 score.")
    TP, FP, FN, TN = confusion_matrix.ravel()
    precision = TP / (TP + FP)
    recall = TP / (TP + FN)
    if (precision + recall) == 0:
        f1 = 0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
    return {
        "precision": round(precision, decimals),
        "recall": round(recall, decimals),
        "f1": round(f1, decimals),
    }


def calculate_kendall_tau(matches: dict, decimals: int = 3, **kwargs) -> float:
    """Calculates the Kendall Tau correlation between the candidate and
    reference indices.

    Args:
        matches (dict): A dictionary containing the matches between the 
          candidate and reference titles.
        **kwargs: Additional arguments to pass to `scipy.stats.kendalltau`.

    Returns:
        float: The Kendall Tau correlation.
    """
    logger.debug("Calculating Kendall tau.")
    # If we have only one item then we set the Kendall Tau to 1
    if len(matches) == 1:
        return 1.0
    candidate_indices = [match["candidate"]["index"] for match in matches]
    reference_indices = [match["reference"]["index"] for match in matches]
    kendall_tau = kendalltau(
        candidate_indices, reference_indices, **kwargs
    ).statistic
    if np.isnan(kendall_tau):
        return 0.0
    return round(kendall_tau, decimals)


def calculate_metrics(
    candidates: list, references: list, f1_threshold: float = 0.6, scoring_method: str = "bert"
) -> dict:
    """Calculates metrics.

    Args:
        candidates: Candidate elements.
        references: Reference elements.
        f1_threshold: F1 threshold.

    Returns:
        Scores.
    """
    logger.debug("Calculating metrics.")
    if scoring_method == "rouge":
        scores = calculate_rouge_score(
            predictions=[str(candidates)], 
            references=[str(references)]
            )
        return scores

    matches = match_elements(candidates, references, f1_threshold)
    confusion_matrix = calculate_confusion_matrix(
        candidates, references, matches
    )
    precision_recall_f1 = calculate_precision_recall_f1(confusion_matrix)
    kendall_tau = calculate_kendall_tau(matches)
    return {
        "candidates": candidates,
        "references": references,
        "matches": matches,
        "confusion_matrix": confusion_matrix.tolist(),
        "precision_recall_f1": precision_recall_f1,
        "kendall_tau": kendall_tau,
    }

def report_statistics(
    folder_path, subfolder: str = None, file_suffix: str = ".tex"
):
    author_count = []
    section_count = []
    word_count = []

    report_paths = []
    if subfolder:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if subfolder in root and file.endswith(file_suffix):
                    report_paths.append(os.path.join(root, file))
    else:
        report_paths = [
            os.path.join(folder_path, file)
            for file in os.listdir(folder_path)
            if file.endswith(file_suffix)
        ]

    for item_path in report_paths:
        if not utils.determine_main_tex_file([item_path]):
            continue
        try:
            report = LatexReport(item_path)
        except Exception as e:
            print(f"Error: {e}")
            continue
        author_count.append(len(report.authors))
        section_count.append(len(report.sections))
        word_count.append(report.word_count)

    return pd.DataFrame(
        {
            "Author Count": author_count,
            "Section Count": section_count,
            "Word Count": word_count,
        }
    )


def presentation_statistics(
    folder_path, subfolder: str = None, file_suffix: str = ".tex"
):
    frame_count = []
    section_count = []
    word_count = []
    bullets_per_frame = []
    words_per_frame = []

    presentation_paths = []
    if subfolder:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if subfolder in root and file.endswith(file_suffix):
                    presentation_paths.append(os.path.join(root, file))
    else:
        presentation_paths = [
            os.path.join(folder_path, file)
            for file in os.listdir(folder_path)
            if file.endswith(".tex")
        ]

    for item_path in presentation_paths:
        try:
            presentation = LatexPresentation(item_path)
        except Exception as e:
            print(f"Error: {e}")
            continue
        frame_count.append(len(presentation.frames))
        section_count.append(len(presentation.sections))
        word_count.append(presentation.word_count)
        bullets_per_frame.append(presentation.bullets_per_frame)
        words_per_frame.append(presentation.words_per_frame)

    return pd.DataFrame(
        {
            "Frame Count": frame_count,
            "Section Count": section_count,
            "Word Count": word_count,
            "Bullets/Frame": bullets_per_frame,
            "Words/Frame": words_per_frame,
        }
    )


def folder_metrics(
    candidate_folder: str,
    reference_folder: str,
    output_file: str,
    match: str = "title",
    scoring_method: str = "bert",
    **kwargs,
) -> None:
    """Walks through a folder of candidate presentations and compares them
    against the reference presentations."""

    def handle_metrics(candidate_file, reference_folder, **kwargs):
        # Generate reference file path
        if candidate_file.endswith("-presentation-beamer.tex"):
            basename = os.path.basename(candidate_file).replace(
                "-presentation-beamer.tex", "-presentation.tex"
            )
        elif candidate_file.endswith(".tex"):
            basename = os.path.basename(candidate_file).replace(
                ".tex", "-presentation.tex"
            )
        else:
            logger.warning(
                f"Skipping {candidate_file} as it is not a LaTeX Beamer presentation."
            )
            return
        reference_subfolder = os.path.join(
            basename.rstrip("-presentation.tex"), "presentation-latex"
        )
        reference_file = os.path.join(
            reference_folder, reference_subfolder, basename
        )

        # Check if reference file exists
        if not os.path.exists(reference_file):
            logger.warning(
                f"Skipping {candidate_file} as reference file {reference_file} does not exist."
            )
            return
        logger.debug(f"Processing {candidate_file}.")

        # Read candidate and reference presentations
        try:
            candidate_presentation = LatexPresentation(candidate_file)
            reference_presentation = LatexPresentation(reference_file)
        except Exception as e:
            logger.error(f"Error reading presentations: {e}")
            return

        # Evaluate metrics using ROUGE metrics
        if scoring_method == "rouge":
            try:
                results = calculate_rouge_score(
                    [str(candidate_presentation.contents)],
                    [str(reference_presentation.contents)],
                )
                results["file"] = candidate_file
                utils.write_dict_to_jsonl(
                    content=results,
                    file_path=output_file,
                )
                return
            except Exception as e:
                logger.error(f"Error evaluating metrics for {candidate_file}: {e}")
                return

        # Evaluate metrics using BERTScore
        # Match candidate and reference elements
        if match == "title":
            candidate_elements = candidate_presentation.frame_titles
            logger.debug(candidate_elements)
            reference_elements = reference_presentation.frame_titles
            logger.debug(reference_elements)
        elif match == "content":
            candidate_elements = candidate_presentation.contents
            reference_elements = reference_presentation.contents
        else:
            raise ValueError(
                "Invalid match type. Valid options are 'title' and 'content'."
            )

        # Calculate metrics
        try:
            results = calculate_metrics(
                candidates=candidate_elements,
                references=reference_elements,
                **kwargs,
            )

            results["file"] = candidate_file
            utils.write_dict_to_jsonl(
                content=results,
                file_path=output_file,
            )
        except Exception as e:
            logger.error(f"Error evaluating metrics for {candidate_file}: {e}")

    # Walk through the candidate folder
    utils.folder_walker(
        path=candidate_folder,
        callback=handle_metrics,
        reference_folder=reference_folder,
        **kwargs,
    )


def expand_confusion_matrix(confusion_matrix):
    # Expand the confusion matrix and extend the metrics dataframe
    [TP, FP], [FN, TN] = confusion_matrix
    return pd.Series(data=[TP, FP, FN, TN], index=["TP", "FP", "FN", "TN"])


def expand_to_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        df_tmp = pd.concat([df, pd.DataFrame(df[col].tolist())], axis=1)
        df_tmp.drop(col, axis=1, inplace=True)
    return df_tmp


def read_metrics_from_jsonl(filepath: str) -> pd.DataFrame:
    df = pd.read_json(filepath, lines=True)
    df = expand_to_columns(df, ["precision_recall_f1"])
    df["f1_threshold"] = (
        df["f1_threshold"].apply(lambda x: f"{x:.1f}").astype("str")
    )
    return df


def summarize_metrics(df: pd.DataFrame) -> pd.DataFrame:
    select_columns = ["precision", "recall", "f1", "kendall_tau"]
    df_results = df.groupby(["method", "f1_threshold"])[select_columns].mean()
    df_results.columns = [
        "Precision",
        "Recall",
        "F1-score",
        "Kendall's $\\tau$",
    ]
    df_results.index.names = ["Method", "Threshold"]
    return df_results


def metrics_to_latex(df: pd.DataFrame) -> str:
    latex_table = df.to_latex(
        float_format="{%.2f}",
        header=["Precision", "Recall", "F1-score", "Kendall's $\\tau$"],
    )
    print(latex_table)


def read_result_files(result_files: list) -> pd.DataFrame:
    df = pd.concat(
        [
            pd.read_json(file, lines=True).assign(threshold=threshold)
            for file, threshold in result_files
        ],
        ignore_index=True,
    )
    df = pd.concat(
        [df, pd.DataFrame(df["precision_recall_f1"].tolist())], axis=1
    )
    df.drop(columns="precision_recall_f1", inplace=True)
    return df

