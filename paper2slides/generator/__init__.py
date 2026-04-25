"""
Generator module

Generates poster images or slides from RAG summary content.
"""
from .config import (
    OutputType,
    PosterDensity,
    SlidesLength,
    StyleType,
    SLIDES_PAGE_RANGES,
    GenerationConfig,
    GenerationInput,
)
from .content_planner import (
    TableRef,
    FigureRef,
    Section,
    ContentPlan,
    ContentPlanner,
)
from .slide_schema import (
    TextBlock,
    ImageBlock,
    TableBlock,
    MetricBlock,
    SlideSpec,
    PresentationSpec,
)
from .spec_builder import build_presentation_spec
from .pptx_renderer import PptxRenderer
from .text_pptx_workflow import run_text_pptx_workflow


__all__ = [
    # Config
    "OutputType",
    "PosterDensity",
    "SlidesLength",
    "StyleType",
    "SLIDES_PAGE_RANGES",
    "GenerationConfig",
    "GenerationInput",
    # Content Planner
    "TableRef",
    "FigureRef",
    "Section",
    "ContentPlan",
    "ContentPlanner",
    # Slide spec / PPTX
    "TextBlock",
    "ImageBlock",
    "TableBlock",
    "MetricBlock",
    "SlideSpec",
    "PresentationSpec",
    "build_presentation_spec",
    "PptxRenderer",
    "run_text_pptx_workflow",
]
