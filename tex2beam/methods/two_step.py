import json
import logging

from tex2beam.classes.latex_report import LatexReport
from tex2beam.methods.chatgpt import chatgpt_completion

logger = logging.getLogger(__name__)


def generate_presentation_outline(
    report: LatexReport, api_key: str, n_slides: int
) -> dict:
    system_message = """
    Your task is to generate a presentation outline based on the table of contents of a research paper. Here are the requirements:

    1. **Input and Format:**
    - The input is a JSON-formatted table of contents of a research paper.
    - Based on this input, generate a JSON-formatted outline for the presentation.

    2. **Presentation Structure:**
    - The presentation should be suitable for a LaTeX Beamer format.
    - The presentation should include title, introduction, and conclusion slides.
    - Target length: %s slides, including the title, introduction, and conclusion slides.
    - If there is insufficient content in the report, create a shorter presentation.

    3. **Slide Content:**
    - Each slide must reference the corresponding section and subsection of the research paper.
    - If there is no relevant subsection, only the section reference is required, with the subsection field left blank.

    4. **Output Format:**
    - The output should be a JSON-formatted array of objects structured as follows:
    ```json
    presentation = [
        {
            "section": "First Section Title",
            "slides": [
                {
                    "title": "First Slide Title",
                    "content": "Slide contents go here...",
                    "report_section": "section_name",
                    "report_subsection": "subsection_name"
                },
                {
                    "title": "Second Slide Title",
                    "content": "Slide contents go here...",
                    "report_section": "section_name",
                    "report_subsection": "subsection_name"
                }
            ]
        },
        {
            "section": "Second Section Title",
            "slides": [
                {
                    "title": "First Slide Title",
                    "content": "Slide contents go here...",
                    "report_section": "section_name",
                    "report_subsection": "subsection_name"
                },
                {
                    "title": "Second Slide Title",
                    "content": "Slide contents go here...",
                    "report_section": "section_name",
                    "report_subsection": "subsection_name"
                }
            ]
        }
    ]
    ```
    """

    response = chatgpt_completion(
        system_message=system_message % str(n_slides),
        user_message=json.dumps(report.toc),
        api_key=api_key,
    )

    return response


def generate_slide_contents(
    outline: dict, report: LatexReport, api_key: str
) -> dict:
    system_message = """
    Your task is to generate detailed slide content for a LaTeX Beamer presentation based on a provided slide outline and the context from the corresponding section of the research paper. Here are the requirements:

    1. **Input:**
    - A JSON object representing a single slide with the title, report section, and subsection.
    - The full text of the referenced report section and subsection.

    2. **Output:**
    - Populate the 'content' field for the slide with detailed content extracted and summarized from the provided context.
    - The output should be a JSON object with the same structure as the input slide but with the 'content' field filled in.
    - Only single slide shall be returned.

    3. **Content Requirements:**
    - Ensure the slide content is concise and focused on the key points relevant to its title, report section, and subsection.
    - Ensure the title slide use LaTeX commands for authors and affiliations.
    - Summarize the key information as bullet points.
    - Maximum 6 bullet points per slide.
    - Maximum 40 words per slide.
    - If a relevant figure, formula, or table is found in the context, include the label reference in the slide content if it is important for understanding the slide.
    - If a slide contains a figure, formula, or table, include a brief description in the slide content, and limit number of bullet points to 2.

    4. **Formatting:**
    - The final output should be a JSON object mirroring the structure of the input slide but with the 'content' field filled in.

    5. **Critique**
    - Before returning the slide content, critique the content according to the requirements above and make any corrections required.
    """

    for slide in outline["presentation"]:
        for s in slide["slides"]:
            if s["title"] == "Title Slide":
                s["title"] = report.title
                context = f"Title: {report.title}, Authors: {str(report.authors)}, Affiliations: {str(report.affiliations)}"
            else:
                context = report.get_section(s["report_section"])
            response = chatgpt_completion(
                system_message=system_message,
                user_message=f"Slide: {json.dumps(s)}, Context: {json.dumps(context)}",
                api_key=api_key,
            )
            s["content"] = response["content"]
    return outline


def generate_beamer_presentation(contents: dict, api_key: str) -> dict:
    system_message = """
    Your task is to generate LaTeX Beamer code for a presentation based on the provided JSON input. Here are the requirements:

    1. **Input:**
    - A JSON object representing the entire presentation. Each section contains slides with titles and detailed content.

    2. **Output:**
    - Generate LaTeX Beamer code with the structure and content from the JSON input.
    - Format the output as: {"presentation": presentation content}

    3. **Formatting Requirements:**
    - **Sections:** Start each section with `\\section{}`.
    - **Slides:** Define each slide with `\\begin{frame}` and `\\end{frame}`.
    - **Slide Titles:** Use `\\frametitle{}` for slide titles.
    - **Content:** Format slide content in bullet points, ensuring each point is a short concise summary of the original input. Use appropriate LaTeX commands for figures, tables, and formulas.
    - **Title Page:** Customize the title page using the information provided.

    4. **Special Instructions:**
    - If the content includes labels for figures, tables, or formulas, incorporate a placeholder for the corresponding LaTeX references without the LaTeX \\ref command.
    - Ensure the generated code is well-structured LaTeX Beamer and compiles without errors.
    - Ensure all environments are properly closed.

    5. **Critique**
    - Before returning the LaTeX Beamer code, critique the content according to the requirements above and make any corrections required.
    """

    presentation = chatgpt_completion(
        system_message=system_message,
        user_message=json.dumps(contents),
        api_key=api_key,
    )

    return presentation


def two_step_generation(latex_path: str, api_key: str, n_slides: int = 5):
    logger.info("Generating presentation for report: {latex_path}")
    report = LatexReport(latex_path)
    outline = generate_presentation_outline(report, api_key, n_slides)
    contents = generate_slide_contents(outline, report, api_key)
    presentation = generate_beamer_presentation(contents, api_key)
    if presentation and len(presentation.get("presentation")) > 0:
        return presentation
    else:
        logger.error(
            "Generated presentation is empty. Please check the input report and try again."
        )
