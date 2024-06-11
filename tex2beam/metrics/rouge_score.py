import evaluate

rogue = evaluate.load("rouge")


def calculate_rouge_score(
    predictions: list[str],
    references: list[str]
) -> dict:
    """Calculate ROUGE score.

    Args:
        predictions: List of predictions.
        references: List of references.

    Returns:
        ROUGE score.
    """
    return rogue.compute(
        predictions=predictions,
        references=references,
        rouge_types=["rouge1", "rouge2", "rougeL"],
    )
