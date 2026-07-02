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
from .sixway import run_sixway_hybrid_smoke
from .universal import (
    DECK_IR_SCHEMA_VERSION,
    UNIVERSAL_SCORECARD_SCHEMA_VERSION,
    pptx_to_deck_ir,
    run_universal_pptx_benchmark,
    score_deck_ir_v0,
)
from .seed_pipeline import (
    build_human_feedback_packet,
    build_seed_full_deck_spec,
    build_seed_template_contract,
    build_seed_template_package,
    build_visual_rule_registry,
    build_visual_probe_spec,
    evaluate_promotion_gate,
    evaluate_template_gate,
    evaluate_visual_probe_spec,
    render_visual_probe_pptx,
    render_seed_full_deck_pptx,
)

__all__ = [
    "DEFAULT_HUMAN_FEEDBACK_BENCHMARK",
    "DECK_IR_SCHEMA_VERSION",
    "UNIVERSAL_SCORECARD_SCHEMA_VERSION",
    "CATEGORY_LABELS",
    "badcase_ids",
    "build_human_feedback_packet",
    "build_seed_full_deck_spec",
    "build_seed_template_contract",
    "build_seed_template_package",
    "build_visual_rule_registry",
    "build_visual_probe_spec",
    "classify_warning",
    "collect_layout_qa_results",
    "inspect_pptx_nonvisual",
    "load_human_feedback_benchmark",
    "pptx_to_deck_ir",
    "run_sixway_hybrid_smoke",
    "run_universal_pptx_benchmark",
    "render_visual_probe_pptx",
    "render_seed_full_deck_pptx",
    "score_deck_ir_v0",
    "evaluate_promotion_gate",
    "evaluate_template_gate",
    "evaluate_visual_probe_spec",
    "summarize_human_feedback_benchmark",
    "summarize_layout_qa",
    "write_summary_report",
]
