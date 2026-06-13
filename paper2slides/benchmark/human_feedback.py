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
    candidate = data.get("candidate_style_reference", {}) or {}
    rubric = data.get("aesthetic_rubric", {}) or {}
    strategy = data.get("automatic_review_strategy", {}) or {}
    workflow = data.get("autonomous_generation_workflow", []) or []
    repair_policy = data.get("non_visual_self_repair_policy", {}) or {}
    return {
        "benchmark_track": data.get("benchmark_track", ""),
        "paper_case": data.get("paper_case", ""),
        "accepted_reference": accepted.get("version", ""),
        "candidate_style_reference": candidate.get("version", ""),
        "candidate_style_status": candidate.get("status", ""),
        "candidate_validation_case_count": len(candidate.get("validation_cases", []) or []),
        "avoid_versions": list(accepted.get("do_not_replace_with", []) or []),
        "principle_count": len(data.get("core_principles", []) or []),
        "iteration_count": len(data.get("iteration_log", []) or []),
        "badcase_count": len(data.get("badcase_rules", []) or []),
        "aesthetic_dimension_count": len(rubric.get("dimensions", []) or []),
        "current_phase_policy": strategy.get("current_phase_policy", ""),
        "cheap_check_count": len(strategy.get("cheap_non_visual_checks", []) or []),
        "disabled_render_check_count": len(strategy.get("disabled_render_checks_for_current_phase", []) or []),
        "autonomous_workflow_stage_count": len(workflow),
        "non_visual_detectable_count": len(repair_policy.get("detectable_without_screenshots", []) or []),
        "repair_priority_count": len(repair_policy.get("repair_priority_ladder", []) or []),
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
