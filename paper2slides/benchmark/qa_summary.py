"""Aggregate existing PPTX QA outputs into benchmark-style reports."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List


CATEGORY_LABELS = {
    "text_overflow": "Text overflow / clipping risk",
    "layout_bounds": "Shape outside slide bounds",
    "empty_content": "Empty slide or component",
    "layout_payload_mismatch": "Layout/payload mismatch",
    "structured_point": "Missing claim/detail/evidence",
    "metric_quality": "Weak metric label/value",
    "placeholder_noise": "Meaningless placeholder/decoration",
    "unsupported_layout": "Unsupported layout",
    "truncated_text": "Truncated ellipsis",
    "other": "Other warning",
}


@dataclass
class QaRunResult:
    path: str
    project: str
    passed: bool
    slide_count: int
    warning_count: int
    failed_slides: List[int]
    categories: Dict[str, int]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "project": self.project,
            "passed": self.passed,
            "slide_count": self.slide_count,
            "warning_count": self.warning_count,
            "failed_slides": self.failed_slides,
            "categories": dict(self.categories),
            "warnings": self.warnings,
        }


def classify_warning(warning: str) -> str:
    """Classify one QA warning into a stable benchmark category."""
    text = (warning or "").lower()
    if any(marker in text for marker in ("overflow", "clip", "wrap", "very small text box", "dense bullet")):
        return "text_overflow"
    if any(marker in text for marker in ("outside", "exceeds", "bounds")):
        return "layout_bounds"
    if "empty" in text or "appears empty" in text:
        return "empty_content"
    if "visual layout has no image" in text or "table layout has no table" in text:
        return "layout_payload_mismatch"
    if any(marker in text for marker in ("missing claim", "missing detail", "missing evidence", "claim repeats detail")):
        return "structured_point"
    if any(marker in text for marker in ("metric", "meaningless label", "missing value", "non-quantitative")):
        return "metric_quality"
    if any(marker in text for marker in ("placeholder", "meaningless decoration")):
        return "placeholder_noise"
    if "unsupported layout" in text:
        return "unsupported_layout"
    if "truncated" in text or "ellipsis" in text:
        return "truncated_text"
    return "other"


def collect_layout_qa_results(outputs_dir: Path) -> List[QaRunResult]:
    """Read all layout_qa.json files under an outputs directory."""
    results: List[QaRunResult] = []
    for qa_path in sorted(outputs_dir.rglob("layout_qa.json")):
        data = _read_json(qa_path)
        if not data:
            continue
        warnings = [str(item) for item in data.get("warnings", []) or []]
        categories = Counter(classify_warning(warning) for warning in warnings)
        project = _infer_project_name(outputs_dir, qa_path)
        slide_count = (
            data.get("slide_count")
            or data.get("pages")
            or (data.get("layout") or {}).get("slide_count")
            or 0
        )
        results.append(
            QaRunResult(
                path=str(qa_path),
                project=project,
                passed=bool(data.get("passed", False)),
                slide_count=int(slide_count),
                warning_count=len(warnings),
                failed_slides=[int(item) for item in data.get("failed_slides", []) or []],
                categories=dict(categories),
                warnings=warnings,
            )
        )
    return results


def summarize_layout_qa(results: Iterable[QaRunResult]) -> Dict[str, Any]:
    """Build aggregate benchmark metrics from QA run results."""
    runs = list(results)
    category_counts: Counter[str] = Counter()
    project_counts: Dict[str, Counter[str]] = defaultdict(Counter)
    total_warnings = 0
    total_slides = 0
    failed_runs = 0

    for run in runs:
        if not run.passed:
            failed_runs += 1
        total_warnings += run.warning_count
        total_slides += run.slide_count
        for category, count in run.categories.items():
            category_counts[category] += count
            project_counts[run.project][category] += count

    pass_rate = (len(runs) - failed_runs) / len(runs) if runs else 0.0
    warnings_per_slide = total_warnings / total_slides if total_slides else 0.0

    return {
        "run_count": len(runs),
        "passed_runs": len(runs) - failed_runs,
        "failed_runs": failed_runs,
        "pass_rate": round(pass_rate, 4),
        "total_slides": total_slides,
        "total_warnings": total_warnings,
        "warnings_per_slide": round(warnings_per_slide, 4),
        "category_counts": dict(category_counts),
        "project_category_counts": {project: dict(counts) for project, counts in project_counts.items()},
        "runs": [run.to_dict() for run in runs],
    }


def write_summary_report(summary: Dict[str, Any], report_dir: Path) -> Dict[str, str]:
    """Write JSON and Markdown reports for a QA benchmark summary."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "qa_summary.json"
    md_path = report_dir / "qa_summary.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(summary), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def _render_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# PPTX QA Benchmark Summary",
        "",
        f"- Runs: {summary['run_count']}",
        f"- Passed runs: {summary['passed_runs']}",
        f"- Failed runs: {summary['failed_runs']}",
        f"- Pass rate: {summary['pass_rate']:.2%}",
        f"- Total slides: {summary['total_slides']}",
        f"- Total warnings: {summary['total_warnings']}",
        f"- Warnings per slide: {summary['warnings_per_slide']:.4f}",
        "",
        "## Warning Categories",
        "",
        "| Category | Label | Count |",
        "| --- | --- | ---: |",
    ]
    category_counts = Counter(summary.get("category_counts", {}))
    for category, count in category_counts.most_common():
        lines.append(f"| `{category}` | {CATEGORY_LABELS.get(category, category)} | {count} |")

    lines.extend(["", "## Worst Runs", "", "| Warnings | Passed | Failed slides | Path |", "| ---: | --- | --- | --- |"])
    runs = sorted(summary.get("runs", []), key=lambda item: item.get("warning_count", 0), reverse=True)
    for run in runs[:10]:
        failed = ", ".join(str(item) for item in run.get("failed_slides", [])) or "-"
        lines.append(
            f"| {run.get('warning_count', 0)} | {run.get('passed')} | {failed} | `{run.get('path', '')}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _infer_project_name(outputs_dir: Path, qa_path: Path) -> str:
    try:
        rel = qa_path.relative_to(outputs_dir)
    except ValueError:
        return "unknown"
    return rel.parts[0] if rel.parts else "unknown"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize existing paper2ppt layout QA results.")
    parser.add_argument("--outputs", default="outputs", help="Directory containing generated outputs.")
    parser.add_argument("--report-dir", default="benchmark_runs/local_history", help="Directory for summary reports.")
    args = parser.parse_args(argv)

    outputs_dir = Path(args.outputs)
    report_dir = Path(args.report_dir)
    results = collect_layout_qa_results(outputs_dir)
    summary = summarize_layout_qa(results)
    paths = write_summary_report(summary, report_dir)
    print(f"Summarized {summary['run_count']} QA run(s).")
    print(f"Markdown report: {paths['markdown']}")
    print(f"JSON report: {paths['json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
