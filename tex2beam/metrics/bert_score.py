import logging
import torch
from evaluate import load

logger = logging.getLogger(__name__)

bertscore = load("bertscore")


def calculate_bert_score(
    predictions,
    references,
    lang: str = "en",
    # model_type: str = "roberta-large"  # default model
    # Recommended model from https://pypi.org/project/bert-score:
    model_type: str = "microsoft/deberta-xlarge-mnli",
) -> dict:
    # use cuda if available
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    logger.debug(f"Using device: {device}")
    return bertscore.compute(
        predictions=predictions,
        references=references,
        lang=lang,
        model_type=model_type,
        device=device,
    )
