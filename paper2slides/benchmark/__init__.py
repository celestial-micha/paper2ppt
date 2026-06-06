"""Benchmark helpers for evaluating generated PPTX decks."""

from .qa_summary import (
    CATEGORY_LABELS,
    classify_warning,
    collect_layout_qa_results,
    summarize_layout_qa,
    write_summary_report,
)

__all__ = [
    "CATEGORY_LABELS",
    "classify_warning",
    "collect_layout_qa_results",
    "summarize_layout_qa",
    "write_summary_report",
]
