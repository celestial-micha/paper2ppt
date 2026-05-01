import os
import json
import re
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv
from ..utils.llm_factory import get_llm

load_dotenv()

class Slide(BaseModel):
    section: str = Field(description="The section of the presentation (e.g., Introduction, Methodology)")
    title: str = Field(description="The title of the slide")
    content_goal: str = Field(description="What specific content should be covered in this slide")
    suggested_layout: Literal['standard', 'two_column', 'three_column', 'highlight_box', 'image_right', 'image_left', 'two_column_header', 'comparison_table'] = Field(description="The visual layout of the slide")
    key_visuals: str = Field(description="Description of any figures or diagrams needed", default="")

class PresentationPlan(BaseModel):
    title: str = Field(description="The title of the paper")
    authors: str = Field(description="The authors of the paper")
    slides: List[Slide] = Field(description="List of slides for the presentation")

class Planner:
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
        self.parser = PydanticOutputParser(pydantic_object=PresentationPlan)

    def _fix_json_string(self, json_str: str) -> str:
        # Remove markdown code blocks if present
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        
        if json_str.endswith("```"):
            json_str = json_str[:-3]
            
        json_str = json_str.strip()
        
        # Fix invalid escape sequences
        # Pattern: backslash followed by a character that is NOT in " \ / b f n r t u
        # We use negative lookahead to find backslashes that are NOT followed by a valid escape char
        pattern = r'\\(?![\\"/bfnrtu])'
        fixed_str = re.sub(pattern, r'\\\\', json_str)
        
        return fixed_str

    def create_plan(self, full_text: str, duration_minutes: int = 10) -> PresentationPlan:
        print(f"[Planner] Generating plan for {duration_minutes} min presentation...")
        
        # Estimate slide count: ~1.5 mins per slide
        target_slides = max(5, int(duration_minutes / 1.5))
        
        system_prompt = """You are an expert academic presenter. Analyze the paper and create a presentation outline following this standard flow:
        1.  **Introduction/Motivation**: What is the problem? Why is it hard?
        2.  **Background/Preliminaries**: Key definitions and existing gaps.
        3.  **Methodology/Proposed Approach**: The core contribution (Architecture, Algorithm).
        4.  **Theoretical Analysis**: (If applicable) Convergence, Complexity, Proof sketches.
        5.  **Experiments/Results**: Key tables, plots, and comparisons.
        6.  **Conclusion & Future Work**: Summary and impact.

        **Layout Strategy (Choose carefully based on content volume)**:
        *   `standard`: Best for general bullet points. (Capacity: Max 5 bullets)
        *   `two_column`: Best for comparing two concepts or splitting long lists. (Capacity: Max 3 bullets per column)
        *   `three_column`: Best for 3 distinct points/metrics. (Capacity: Max 3 short bullets per column)
        *   `image_right`: Best for "Text + Figure". (Capacity: Max 4 bullets + 1 Image)
        *   `image_left`: Best for "Figure + Text". (Capacity: 1 Image + Max 4 bullets)
        *   `highlight_box`: Best for a SINGLE key definition, theorem, or quote. (Capacity: Max 40 words)
        *   `two_column_header`: Best for "Concept + Two Examples". Top full-width text, then two columns below.
        *   `comparison_table`: Best for comparing models/results. Use a LaTeX table.

        **Constraints**:
        *   **NO Title Slide**: Do NOT create a separate slide for Title and Authors. The presentation template already includes a title page. Start directly with Introduction.
        *   **Concise Titles**: Keep slide titles VERY short (max 5 words). Example: "Model Architecture" instead of "The Proposed Transformer Model Architecture".
        *   **Clean TOC**: Group slides into high-level sections (e.g., "Introduction", "Method", "Experiments"). Do NOT create a new section for every single slide. Multiple slides can share the same section.
        *   **Content Density**: Do NOT try to cram too much information into one slide. If a topic is complex, split it into two slides (e.g., "Methodology I", "Methodology II").
        *   **JSON Safety**: CRITICAL: You MUST escape all backslashes in the JSON output. For example, write "\\\\alpha" instead of "\\alpha". Do NOT use single backslashes. It is safer to use plain text descriptions (e.g. "alpha") and avoid LaTeX syntax entirely in the JSON fields.

        Identify the 'Core Mathematical Contribution' of the paper. Ensure there is at least one slide dedicated to the formal problem statement (using a Definition block) and one slide for the main Algorithm or Theorem.
        
        Target approximately {target_slides} slides (excluding title).
        """

        human_prompt = """Here is the content of the paper:
        {paper_text}
        
        Generate a JSON plan for the presentation.
        {format_instructions}
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])

        # Truncate text if too long (DeepSeek has 32k context, usually enough for papers, but let's be safe)
        # A paper is usually 5-10k tokens.
        truncated_text = full_text[:50000] # Rough char limit

        chain = prompt | self.llm | self.parser
        
        try:
            plan = chain.invoke({
                "target_slides": target_slides,
                "paper_text": truncated_text,
                "format_instructions": self.parser.get_format_instructions()
            })
            return plan
        except OutputParserException as e:
            print(f"[Planner] JSON parsing failed. Attempting to fix...")
            if hasattr(e, 'llm_output') and e.llm_output:
                fixed_json = self._fix_json_string(e.llm_output)
                try:
                    return self.parser.parse(fixed_json)
                except Exception as e2:
                    print(f"[Planner] Failed to parse fixed JSON: {e2}")
                    raise e
            else:
                raise e
        except Exception as e:
            print(f"[Planner] Error generating plan: {e}")
            raise e

if __name__ == "__main__":
    # Test
    with open("output/beta_test/flattened.tex", "r") as f:
        text = f.read()
    planner = Planner()
    plan = planner.create_plan(text)
    print(json.dumps(plan.dict(), indent=2))
