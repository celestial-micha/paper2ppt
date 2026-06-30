"""Command-line entry point for paper2ppt benchmark utilities."""

from __future__ import annotations

import sys
from typing import List, Optional

from . import fourway, from_scratch, human_feedback, nonvisual_audit, qa_summary


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
    if args and args[0] == "qa-summary":
        return qa_summary.main(args[1:])
    return qa_summary.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
