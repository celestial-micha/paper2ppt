"""Command-line entry point for paper2ppt benchmark utilities."""

from __future__ import annotations

import sys
from typing import List, Optional

from . import fourway, from_scratch, human_feedback, nonvisual_audit, qa_summary, sixway
from .universal import pptx_intake, runner as universal_runner
from .seed_pipeline import (
    full_deck_renderer,
    human_feedback_packet,
    probe_renderer,
    strategist,
    template_package,
    visual_probe,
    visual_rule_registry,
)


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "inventory":
        return from_scratch.main(args[1:])
    if args and args[0] == "human-feedback":
        return human_feedback.main(args[1:])
    if args and args[0] == "nonvisual-audit":
        return nonvisual_audit.main(args[1:])
    if args and args[0] == "fourway":
        return fourway.main(args[1:])
    if args and args[0] == "sixway":
        return sixway.main(args[1:])
    if args and args[0] == "universal-pptx-intake":
        return pptx_intake.main(args[1:])
    if args and args[0] == "universal-run":
        return universal_runner.main(args[1:])
    if args and args[0] == "seed-template-package":
        return template_package.main(args[1:])
    if args and args[0] == "seed-strategist":
        return strategist.main(args[1:])
    if args and args[0] == "visual-probe-spec":
        return visual_probe.main(args[1:])
    if args and args[0] == "human-feedback-packet":
        return human_feedback_packet.main(args[1:])
    if args and args[0] == "visual-rule-registry":
        return visual_rule_registry.main(args[1:])
    if args and args[0] == "seed-probe-render":
        return probe_renderer.main(args[1:])
    if args and args[0] == "seed-full-deck-render":
        return full_deck_renderer.main(args[1:])
    if args and args[0] == "qa-summary":
        return qa_summary.main(args[1:])
    return qa_summary.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
