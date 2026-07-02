"""Universal PPT benchmark intake helpers."""

from .deck_ir import DECK_IR_SCHEMA_VERSION, UNIVERSAL_SCORECARD_SCHEMA_VERSION, score_deck_ir_v0
from .pptx_intake import pptx_to_deck_ir, write_pptx_intake_bundle
from .runner import run_universal_pptx_benchmark

__all__ = [
    "DECK_IR_SCHEMA_VERSION",
    "UNIVERSAL_SCORECARD_SCHEMA_VERSION",
    "pptx_to_deck_ir",
    "run_universal_pptx_benchmark",
    "score_deck_ir_v0",
    "write_pptx_intake_bundle",
]
