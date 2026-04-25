"""
Prompt templates for LLM interactions
"""
from .paper_extraction import EXTRACT_PROMPTS
from .content_planning import (
    PAPER_SLIDES_PLANNING_PROMPT,
    GENERAL_SLIDES_PLANNING_PROMPT,
)

__all__ = [
    # Paper extraction
    "EXTRACT_PROMPTS",
    # Content planning
    "PAPER_SLIDES_PLANNING_PROMPT",
    "GENERAL_SLIDES_PLANNING_PROMPT",
]
