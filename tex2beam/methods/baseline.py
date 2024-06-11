import logging

from tex2beam.classes.latex_report import LatexReport
from tex2beam.methods.chatgpt import chatgpt_completion

logger = logging.getLogger(__name__)


def chatgpt_chat(report: str, api_key: str, n_slides: int = 7) -> dict:
    """Generates a Beamer presentation from a report.

    Args:
        report: Report.

    Returns:
        Beamer presentation.
    """
    system_message = """
    Given an academic report in LaTeX format, your task is to create a summary 
    suitable for a LaTeX Beamer presentation with {n_slides} slides. 
    The report consists of several sections, including Introduction, 
    Literature Review, Methodology, Results, Discussion, and Conclusion. 
    You shall:

    1. Extract the Main Points: Identify and summarize the main points from each 
    section, focusing on objectives, key findings, methodologies, and conclusions. 
    Use concise bullet points or short paragraphs.

    2. Generate Beamer LaTeX Code: For each summarized section, create 
    corresponding Beamer slides. Begin with a title slide including the report's 
    title, authors, and affiliation. Follow this with slides for each main section 
    of the report. Use Beamer's itemize and enumerate environments to organize the 
    summarized points effectively.

    3. Include Figures, Tables, and Equations: Where the report mentions figures, 
    tables, or equations that are crucial to understanding the research, create 
    placeholders in the Beamer presentation. Use the `\\begin{{figure}}`, 
    `\\begin{{table}}`, and `\\begin{{equation}}` environments, and indicate where the
    user should manually insert the graphic or table (e.g., `Place figure about X 
    here`).

    4. Presentation Aesthetics: Use Beamer's default theme, and use bullet points 
    for lists.

    Your input is the text of an academic report. Based on this input, generate a 
    LaTeX Beamer presentation outline with {n_slides} slides as described. 
    The output shall be in JSON format: 
    {{'presentation': 'LaTeX Beamer code for the presentation.'}}
    """

    presentation = chatgpt_completion(
        system_message=system_message.format(n_slides=n_slides),
        user_message=report,
        api_key=api_key,
    )

    return presentation


def baseline_generation(report_path: str, api_key: str, n_slides: int = 7):
    """Generates a Beamer presentation from a report using the Baseline method.

    Args:
        report_path: Path to the report.
        api_key: OpenAI API key.

    Returns:
        Beamer presentation.
    """
    report = LatexReport(report_path)
    presentation = chatgpt_chat(str(report.soup), api_key, n_slides=n_slides)
    if presentation and len(presentation.get("presentation")) > 0:
        return presentation
    else:
        logger.error(
            "Generated presentation is empty. Please check the input report and try again."
        )
