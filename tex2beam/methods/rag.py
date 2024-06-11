import chromadb
import json
import hashlib
import logging
import os
import re
import tiktoken

from dotenv import load_dotenv
from llama_index.core import (
    Settings,
    Document,
    VectorStoreIndex,
    StorageContext,
    PromptTemplate,
)
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore


from tex2beam.classes.latex_report import LatexReport

logger = logging.getLogger(__name__)

load_dotenv()

#
Settings.llm = OpenAI(model="gpt-4o", temperature=0.0)
Settings.chunk_size = 2048
Settings.chunk_overlap = 64
Settings.tokenizer = tiktoken.encoding_for_model("gpt-4o")


class RAG:
    def __init__(
        self,
        report_path: str,
        api_key: str,
        collection_path: str = "../data/chroma_db",
    ) -> None:
        """Initialize the RAG model with the report path and API key.

        Args:
            report_path (str): Path to the LaTeX report.
            api_key (str): OpenAI API key.
            collection_path (str, optional): Path to the ChromaDB collection.
              Defaults to "../data/chroma_db".
        """
        self.report_path = report_path
        self.report = LatexReport(self.report_path)
        self.collection_path = collection_path
        self.collection_title = hashlib.md5(report_path.encode()).hexdigest()
        self.chroma_client = chromadb.PersistentClient(self.collection_path)
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            self.collection_title
        )
        self.vector_store = ChromaVectorStore(
            chroma_collection=self.chroma_collection
        )
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        self.index = None
        self.query_engine = None
        self.presentation = None
        os.environ["OPENAI_API_KEY"] = api_key

    def is_valid_json(self, json_string) -> bool:
        """Check if the provided string is a valid JSON.

        Args:
            json_string (str): JSON string.

        Returns:
            bool: True if the JSON string is valid, False otherwise.
        """
        try:
            json.loads(json_string)
        except ValueError as e:
            logger.error(f"Invalid JSON: {e}")
            logger.debug(f"JSON string: {json_string}")
            return False
        return True

    def sanitize_json_string(self, json_string) -> str:
        """Sanitize the JSON string to escape control characters and fix common
        issues.

        Args:
            json_string (str): JSON string.

        Returns:
            str: Sanitized JSON string.
        """
        # If the content only contains single and double \ and \\, they need to
        # be escaped as \\ and \\\\.
        json_string = re.sub(
            r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r"\\\\", json_string
        )
        return json_string

    def extract_and_validate_json(self, response):
        """Extract JSON content from the response and validate it."""
        try:
            if response.__str__().startswith('"slide_content"'):
                slide_content = json.loads(response.__str__())
                return slide_content
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse response as JSON.\n{response}\n\n{e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error during JSON parsing.\n{response}\n\n{e}"
            )
            return None
        try:
            match = re.search(r"```json(.*?)```", response.__str__(), re.DOTALL)
            if match:
                slide_content = match.group(1).strip()
                logging.debug(f"Extracted slide content: {slide_content}")

                # Sanitize the extracted JSON string
                slide_content = self.sanitize_json_string(slide_content)

                # Validate the JSON structure
                if self.is_valid_json(slide_content):
                    return slide_content
                else:
                    logging.error(f"Invalid JSON content: {slide_content}")
            else:
                logging.error(
                    f"Regex did not match. Response: {response.__str__()}"
                )
        except Exception as e:
            logging.error(
                f"Failed to extract and validate JSON contents.\n{response}\n\n{e}"
            )
        return None

    def get_vector_store_index(self):
        return VectorStoreIndex.from_vector_store()

    def generate_embeddings(self):
        documents = [
            Document(
                text=str(self.report.sections),
                metadata={
                    "filename": str(self.report.filepath),
                    "title": str(self.report.title),
                    "authors": str(self.report.authors),
                    "citations": str(self.report.citations),
                    "id_": str(self.report.filepath),
                },
            )
        ]
        self.index = VectorStoreIndex.from_documents(
            documents=documents,
            storage_context=self.storage_context,
        )
        self.query_engine = self.index.as_query_engine(response_mode="compact")

    def generate_presentation_single_step(self, n_slides=7):

        # Custom query prompt template
        qa_prompt_tmpl_str = """\
            Context information is below.
            ---------------------
            {context_str}
            ---------------------
            Given the academic report in the context information and not prior knowledge, 
            your task is to create a summary suitable for a LaTeX Beamer presentation with 
            {n_slides} slides. The report consists of several sections, including 
            Introduction, Literature Review, Methodology, Results, Discussion, and 
            Conclusion. You shall:

            1. Extract the Main Topics and Related Keywords:
                - Identify and summarize the main topics from each section, focusing on 
                objectives, key findings, methodologies, and conclusions. 
                - Use concise bullet points or short paragraphs.

            2. Generate Beamer LaTeX Code: 
                - For each summarized section, create corresponding Beamer slides. 
                - Begin with a title slide including the report's title, authors, and 
                affiliation. 
                - Follow this with slides for each main section of the report. 
                - Use Beamer's itemize and enumerate environments to organize the 
                summarized points effectively.
                - Limit each slide to around 30 words or 5 bullet points.
                - Slides with figures or tables shall be limited to maximum 2 bullet 
                points.
                - The total presentation should not exceed around 300 words.

            3. Include Figures, Tables, and Equations: 
                - Include figures, tables, and equations that are crucial to understanding 
                the research.
                - Use the `\\begin{{figure}}`, `\\begin{{table}}`, and 
                `\\begin{{equation}}` LaTeX environments.
                - Figures must include the filepath.

            4. Presentation Aesthetics: 
                - Use Beamer's default theme, and use bullet points for lists.

            Your input is the text of an academic report in the context information.
            Based on this input, generate a LaTeX Beamer presentation with {n_slides} 
            slides, as described. The output shall be in JSON format: 
            {{"presentation": "LaTeX Beamer code for the presentation."}}

            Answer: \
        """
        prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
        partial_prompt_tmpl = prompt_tmpl.partial_format(n_slides=n_slides)

        # Save the current prompt
        tmp_prompt_tmpl = self.query_engine.get_prompts()
        # Update query prompt
        self.query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": partial_prompt_tmpl}
        )

        try:
            response = self.query_engine.query("Generate presentation.")
        except Exception as e:
            logger.error(f"Failed to generate presentation.\n{e}")

        # Restore prompt
        self.query_engine.update_prompts(tmp_prompt_tmpl)

        presentation = self.extract_and_validate_json(response)
        if presentation:
            try:
                presentation_json = json.loads(presentation)
                logger.debug(f"Parsed slide content: {presentation_json}")
                self.presentation = presentation_json.get("presentation")
                return self.presentation
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse response as JSON.\n{presentation}\n\n{e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during JSON parsing.\n{presentation}\n\n{e}"
                )
        return

    def generate_presentation_outline(self, n_slides=7):

        # Custom query prompt template
        qa_prompt_tmpl_str = """\
            Context information is below.
            ---------------------
            {context_str}
            ---------------------
            Given the academic report in the context information and not prior knowledge, 
            generate a presentation outline for a LaTeX Beamer presentation with {n_slides}
            slides. The report consists of several sections, including Introduction, 
            Literature Review, Methodology, Results, Discussion, and Conclusion. You shall:

            1. Extract the Main Topics and Related Keywords:
            Identify and summarize the main topics from each section.
            Focuse on objectives, key findings, methodologies, and conclusions. 

            2. Generate Beamer LaTeX Slide Titles:
            For each Main Topic, create corresponding Beamer Slides Titles. 
            Begin with a title slide with title "Title Slide". 
            Follow this with slides for each Main Topic of the report. 

            Your input is the text of an academic report in the context information.
            Based on the context, generate a LaTeX Beamer presentation outline as described. 
            The output shall be in JSON format:
            {{"outline": [
                {{"title": "slide_title", "keywords": ["kw1", "kw2", "kw3", ...]}}, 
                {{...}}, 
                ...
            ]}}

            Answer: \
        """
        prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
        partial_prompt_tmpl = prompt_tmpl.partial_format(n_slides=n_slides)

        # Save the current prompt
        tmp_prompt_tmpl = self.query_engine.get_prompts()
        # Update query prompt
        self.query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": partial_prompt_tmpl}
        )

        try:
            response = self.query_engine.query("Generate presentation outline.")
        except Exception as e:
            logger.error(f"Failed to generate presentation outline.\n{e}")

        # Restore the prompt
        self.query_engine.update_prompts(tmp_prompt_tmpl)

        try:
            outline = re.search(
                r"```json(.*?)```", response.__str__(), re.DOTALL
            ).group(1)
            outline = json.loads(outline.strip())
            self.outline = outline.get("outline")
            return self.outline
        except Exception as e:
            logger.error(f"Failed to read response.\n{e}")
        return

    def generate_slide_contents(self, slide_data: dict) -> str:
        """Based on the slide title and keywords, generate slide contents.

        Args:
            slide_data (dict): Slide title and keywords.

        Returns:
            str: Slide contents in LaTeX Beamer format.
        """

        # Custom query prompt template
        qa_prompt_tmpl_str = """\
            Context information is below.
            ---------------------
            {context_str}
            ---------------------
            Slide title and related keywords are below.
            {slide_data}
            ---------------------
            Given the academic report in the context information, the slide title and 
            related keywords, generate contents for this slide in LaTeX Beamer format. 
            You shall:

            1. Identify and summarize content relevant for this slide:
            Use concise bullet points of short paragraphs.

            2. Generate Beamer LaTeX Code:
            Use Beamer's itemize and enumerate environments to organize the summarized 
            points effectively.

            3. Include Figures, Tables, and Equations: 
            Use the `\\begin{{figure}}`, `\\begin{{table}}`, and `\\begin{{equation}}`
            environments.

            4. Presentation Aesthetics: Use Beamer's default theme, and use bullet points 
            for lists.

            5. Title Slide: 
            If the slide title is "Title Slide" it shall be formatted using correct LaTeX 
            Beamer code. Include the report title, authors and their affiliations in proper
            LaTeX code.

            Your input is the text of an academic report in the context information, and 
            the slide titles with related keywords. Based on the context, slide titles and
            keywords, generate content for a single LaTeX Beamer frame as described. 
            The output shall be the content for a single slide in properly escaped JSON 
            format: ```json\\n{{"slide_content": "content"}}\\n```

            Answer: \
        """

        refine_prompt_tmpl_str = """\
            The original query is as follows: {query_str}
            We have provided an existing answer: {existing_answer}
            We have the opportunity to refine the existing answer (only if needed) with 
            some more context below.
            ------------
            {context_msg}
            ------------
            Given the new context, refine the original answer to better answer the query. 
            If the context isn't useful, return the original answer.
            The output shall be the LaTeX Beamer code for a single slide in properly 
            escaped JSON format: ```json\\n{{"slide_content": "content"}}\\n```
            Refined Answer: \
        """

        # Prepare the custom prompts
        prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
        partial_prompt_tmpl = prompt_tmpl.partial_format(slide_data=slide_data)
        refine_prompt_tmpl = PromptTemplate(refine_prompt_tmpl_str)

        if not self.query_engine:
            self.query_engine = self.get_vector_store_index().as_query_engine(
                response_mode="compact"
            )

        # Save the current prompt
        tmp_prompt_tmpl = self.query_engine.get_prompts()

        # Update query prompt
        self.query_engine.update_prompts(
            {
                "response_synthesizer:text_qa_template": partial_prompt_tmpl,
                "response_synthesizer:refine_template": refine_prompt_tmpl,
            }
        )

        try:
            response = self.query_engine.query("Generate slide contents.")
            logger.debug(f"Full response: {response}")
        except Exception as e:
            logger.error(f"Failed to generate slide contents.\n{e}")
            return

        # Restore prompt
        self.query_engine.update_prompts(tmp_prompt_tmpl)

        slide_content = self.extract_and_validate_json(response)
        if slide_content:
            try:
                slide_content_json = json.loads(slide_content)
                logger.debug(f"Parsed slide content: {slide_content_json}")
                return slide_content_json.get("slide_content")
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse response as JSON.\n{slide_content}\n\n{e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during JSON parsing.\n{slide_content}\n\n{e}"
                )
        return

    def generate_presentation_two_step(self, n_slides: int = 7):
        self.generate_presentation_outline(n_slides)
        slides = []
        len_outline = len(self.outline)
        for i, slide_data in enumerate(self.outline):
            content = self.generate_slide_contents(slide_data)
            # Clean up tags in wrong places
            if i == 0:
                # Remove \end{document} from the first slide
                content = re.sub(r"\\end{document}", "", content)
            elif i == len_outline - 1:
                # Remove \documentclass and \begin{document} from the last slide
                content = re.sub(r"\\documentclass.*\n", "", content)
                content = re.sub(r"\\begin{document}", "", content)
            else:
                # Remove lines with \documentclass, \begin{document}, \end{document}
                # from all other slides.
                content = re.sub(r"\\documentclass.*\n", "", content)
                content = re.sub(r"\\begin{document}", "", content)
                content = re.sub(r"\\end{document}", "", content)
            slides.append(content)
        self.presentation = "\n".join(slides)
        # Check that there is a \documentclass and \begin{document} command in first part of the document
        if not re.search(r"\\documentclass", self.presentation):
            self.presentation = "\\documentclass{beamer}\n" + self.presentation
        if not re.search(r"\\begin{document}", self.presentation):
            self.presentation = self.presentation.replace(
                "\\documentclass{beamer}",
                "\\documentclass{beamer}\n\\begin{document}",
            )
        # Check that the document ends with \end{document}
        if not re.search(r"\\end{document}", self.presentation):
            self.presentation = self.presentation + "\n\\end{document}"
        return self.presentation


def rag_generation(report_path: str, api_key: str, n_slides: int = 9):
    rag = RAG(report_path, api_key)
    rag.generate_embeddings()
    rag.generate_presentation_single_step(n_slides)
    return rag


def rag_two_step_generation(report_path: str, api_key: str, n_slides: int = 9):
    rag = RAG(report_path, api_key)
    rag.generate_embeddings()
    rag.generate_presentation_two_step(n_slides)
    return rag
