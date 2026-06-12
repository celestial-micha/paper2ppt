"""Human-feedback benchmark rule helpers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_HUMAN_FEEDBACK_BENCHMARK = Path("benchmarks") / "from_scratch_human_feedback_benchmark.json"


def load_human_feedback_benchmark(path: Path = DEFAULT_HUMAN_FEEDBACK_BENCHMARK) -> Dict[str, Any]:
    """Load the structured human-feedback benchmark registry."""
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_human_feedback_benchmark(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact summary suitable for benchmark reports."""
    accepted = data.get("accepted_reference", {}) or {}
    rubric = data.get("aesthetic_rubric", {}) or {}
    strategy = data.get("automatic_review_strategy", {}) or {}
    return {
        "benchmark_track": data.get("benchmark_track", ""),
        "paper_case": data.get("paper_case", ""),
        "accepted_reference": accepted.get("version", ""),
        "avoid_versions": list(accepted.get("do_not_replace_with", []) or []),
        "principle_count": len(data.get("core_principles", []) or []),
        "iteration_count": len(data.get("iteration_log", []) or []),
        "badcase_count": len(data.get("badcase_rules", []) or []),
        "aesthetic_dimension_count": len(rubric.get("dimensions", []) or []),
        "cheap_check_count": len(strategy.get("cheap_non_visual_checks", []) or []),
        "selective_render_check_count": len(strategy.get("selective_render_checks", []) or []),
    }


def badcase_ids(data: Dict[str, Any]) -> List[str]:
    """Return registered badcase identifiers in declaration order."""
    return [str(item.get("id", "")) for item in data.get("badcase_rules", []) if item.get("id")]


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect human-feedback benchmark rules.")
    parser.add_argument("--path", default=str(DEFAULT_HUMAN_FEEDBACK_BENCHMARK))
    args = parser.parse_args(argv)

    data = load_human_feedback_benchmark(Path(args.path))
    print(json.dumps(summarize_human_feedback_benchmark(data), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
