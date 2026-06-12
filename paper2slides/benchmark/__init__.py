"""Benchmark helpers for evaluating generated PPTX decks."""

from .qa_summary import (
    CATEGORY_LABELS,
    classify_warning,
    collect_layout_qa_results,
    summarize_layout_qa,
    write_summary_report,
)
from .human_feedback import (
    DEFAULT_HUMAN_FEEDBACK_BENCHMARK,
    badcase_ids,
    load_human_feedback_benchmark,
    summarize_human_feedback_benchmark,
)
from .nonvisual_audit import inspect_pptx_nonvisual

__all__ = [
    "DEFAULT_HUMAN_FEEDBACK_BENCHMARK",
    "CATEGORY_LABELS",
    "badcase_ids",
    "classify_warning",
    "collect_layout_qa_results",
    "inspect_pptx_nonvisual",
    "load_human_feedback_benchmark",
    "summarize_human_feedback_benchmark",
    "summarize_layout_qa",
    "write_summary_report",
]
