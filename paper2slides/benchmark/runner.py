"""Batch runner for paper2ppt benchmark paper sets."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from paper2slides.core.paths import get_base_dir, get_config_dir
from paper2slides.utils.path_utils import get_project_name, parse_style

from .papers import DEFAULT_MANIFEST, expand_paper_set, load_manifest, validate_paper_files
from .qa_summary import classify_warning


DEFAULT_REPORT_ROOT = Path("benchmark_runs")


def run_benchmark(
    set_name: str = "ai20",
    manifest_path: Path = DEFAULT_MANIFEST,
    output_dir: Path = Path("outputs"),
    report_root: Path = DEFAULT_REPORT_ROOT,
    styles: Optional[List[str]] = None,
    length: str = "medium",
    slides: Optional[int] = 24,
    fast: bool = True,
    from_stage: Optional[str] = None,
    limit: Optional[int] = None,
    start_index: int = 0,
    resume: bool = False,
    python_executable: str = sys.executable,
    extra_env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Run paper2ppt over a benchmark set and write aggregate reports."""
    _load_package_env()
    styles = styles or ["academic"]
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = report_root / f"{set_name}_{run_id}"
    logs_dir = report_dir / "logs"
    report_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(manifest_path)
    validation = validate_paper_files(manifest_path, set_name)
    if validation["missing"]:
        missing_ids = ", ".join(item["id"] for item in validation["missing"])
        raise RuntimeError(f"Paper set '{set_name}' has missing files: {missing_ids}")
    _preflight_environment(extra_env or {})

    papers = expand_paper_set(manifest, set_name)
    if start_index:
        papers = papers[start_index:]
    if limit is not None:
        papers = papers[: max(0, limit)]

    run_manifest = {
        "run_id": run_id,
        "set": set_name,
        "manifest_path": str(manifest_path),
        "output_dir": str(output_dir),
        "report_dir": str(report_dir),
        "styles": styles,
        "length": length,
        "slides": slides,
        "fast": fast,
        "from_stage": from_stage,
        "limit": limit,
        "start_index": start_index,
        "python_executable": python_executable,
        "papers": [{"id": paper.get("id", ""), "path": paper.get("path", "")} for paper in papers],
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_json(report_dir / "manifest.json", run_manifest)

    results: List[Dict[str, Any]] = []
    for paper_index, paper in enumerate(papers, start=start_index + 1):
        for style in styles:
            result = _run_one(
                paper=paper,
                paper_index=paper_index,
                set_name=set_name,
                style=style,
                length=length,
                slides=slides,
                fast=fast,
                from_stage=from_stage,
                output_dir=output_dir,
                logs_dir=logs_dir,
                python_executable=python_executable,
                resume=resume,
                extra_env=extra_env or {},
            )
            results.append(result)
            _write_json(report_dir / "per_paper_results.json", {"results": results})
            summary = summarize_run_results(results)
            _write_json(report_dir / "aggregate_report.json", summary)
            (report_dir / "aggregate_report.md").write_text(_render_markdown(summary, results), encoding="utf-8")

    final_summary = summarize_run_results(results)
    final_summary["completed_at"] = datetime.now().isoformat(timespec="seconds")
    _write_json(report_dir / "aggregate_report.json", final_summary)
    (report_dir / "aggregate_report.md").write_text(_render_markdown(final_summary, results), encoding="utf-8")
    return {
        "report_dir": str(report_dir),
        "summary": final_summary,
        "results": results,
    }


def _load_package_env() -> None:
    try:
        from dotenv import load_dotenv

        env_path = Path("paper2slides") / ".env"
        load_dotenv(dotenv_path=env_path, override=False)
    except Exception:
        return


def _preflight_environment(extra_env: Dict[str, str]) -> None:
    env = os.environ.copy()
    env.update(extra_env)
    include_images = env.get("RAG_FAST_INCLUDE_IMAGES", "1").strip().lower() in {"1", "true", "yes", "on"}
    figure_analysis = env.get("PPTX_ENABLE_FIGURE_ANALYSIS", "auto").strip().lower()
    needs_vision = include_images or figure_analysis not in {"0", "false", "no", "off"}
    if not needs_vision:
        return
    has_rag_vision_key = bool((env.get("RAG_VISION_API_KEY") or env.get("OPENAI_API_KEY") or "").strip())
    has_pptx_vision_key = bool(
        (
            env.get("PPTX_VISION_API_KEY")
            or env.get("RAG_VISION_API_KEY")
            or env.get("OPENAI_API_KEY")
            or ""
        ).strip()
    )
    missing = []
    if include_images and not has_rag_vision_key:
        missing.append("RAG_VISION_API_KEY or OPENAI_API_KEY")
    if figure_analysis not in {"0", "false", "no", "off"} and not has_pptx_vision_key:
        missing.append("PPTX_VISION_API_KEY, RAG_VISION_API_KEY, or OPENAI_API_KEY")
    if missing:
        raise RuntimeError(
            "Vision-capable benchmark configuration is enabled, but required vision API key(s) are missing: "
            + "; ".join(missing)
        )


def summarize_run_results(results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(results)
    total = len(rows)
    succeeded = sum(1 for row in rows if row.get("returncode") == 0 and row.get("qa_passed") is True)
    command_failed = sum(1 for row in rows if row.get("returncode") != 0)
    qa_failed = sum(1 for row in rows if row.get("returncode") == 0 and row.get("qa_passed") is False)
    artifact_missing = sum(1 for row in rows if _row_status(row) == "artifact_missing")
    skipped = sum(1 for row in rows if row.get("skipped"))
    total_elapsed = sum(float(row.get("elapsed_seconds") or 0) for row in rows)
    total_warnings = sum(int(row.get("warning_count") or 0) for row in rows)
    total_slides = sum(int(row.get("slide_count") or 0) for row in rows)
    categories: Counter[str] = Counter()
    by_style: Dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        status = _row_status(row)
        by_style[row.get("style", "unknown")][status] += 1
        for category, count in (row.get("warning_categories") or {}).items():
            categories[category] += int(count)

    return {
        "total_runs": total,
        "succeeded": succeeded,
        "command_failed": command_failed,
        "qa_failed": qa_failed,
        "artifact_missing": artifact_missing,
        "skipped": skipped,
        "success_rate": round(succeeded / total, 4) if total else 0.0,
        "total_elapsed_seconds": round(total_elapsed, 2),
        "average_elapsed_seconds": round(total_elapsed / total, 2) if total else 0.0,
        "total_slides": total_slides,
        "total_warnings": total_warnings,
        "warnings_per_slide": round(total_warnings / total_slides, 4) if total_slides else 0.0,
        "warning_categories": dict(categories),
        "by_style": {style: dict(counts) for style, counts in by_style.items()},
    }


def _run_one(
    paper: Dict[str, Any],
    paper_index: int,
    set_name: str,
    style: str,
    length: str,
    slides: Optional[int],
    fast: bool,
    from_stage: Optional[str],
    output_dir: Path,
    logs_dir: Path,
    python_executable: str,
    resume: bool,
    extra_env: Dict[str, str],
) -> Dict[str, Any]:
    paper_id = paper.get("id", "") or Path(paper.get("path", "")).stem
    paper_path = Path(paper.get("path", ""))
    log_path = logs_dir / f"{paper_index:03d}_{paper_id}_{_safe_name(style)}.log"
    config_dir = _expected_config_dir(output_dir, paper_path, style, length, slides, fast)
    existing_output = _latest_output_dir(config_dir)
    if resume and existing_output and (existing_output / "layout_qa.json").exists():
        return _result_from_existing(
            paper=paper,
            paper_index=paper_index,
            set_name=set_name,
            style=style,
            length=length,
            slides=slides,
            fast=fast,
            from_stage=from_stage,
            config_dir=config_dir,
            output_subdir=existing_output,
            log_path=log_path,
            skipped=True,
        )

    before_outputs = {path.resolve() for path in config_dir.iterdir() if path.is_dir()} if config_dir.exists() else set()
    command = _build_command(
        python_executable=python_executable,
        paper_path=paper_path,
        output_dir=output_dir,
        style=style,
        length=length,
        slides=slides,
        fast=fast,
        from_stage=from_stage,
    )
    start = time.perf_counter()
    env = os.environ.copy()
    env.update(extra_env)
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write("Command: " + " ".join(command) + "\n\n")
        log.flush()
        process = subprocess.run(
            command,
            cwd=Path.cwd(),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
    elapsed = time.perf_counter() - start
    output_subdir = _find_new_or_latest_output(config_dir, before_outputs)
    result = _result_from_existing(
        paper=paper,
        paper_index=paper_index,
        set_name=set_name,
        style=style,
        length=length,
        slides=slides,
        fast=fast,
        from_stage=from_stage,
        config_dir=config_dir,
        output_subdir=output_subdir,
        log_path=log_path,
        skipped=False,
    )
    result.update(
        {
            "command": command,
            "returncode": process.returncode,
            "elapsed_seconds": round(elapsed, 2),
        }
    )
    if process.returncode != 0:
        result["error"] = _tail_text(log_path, 40)
    return result


def _build_command(
    python_executable: str,
    paper_path: Path,
    output_dir: Path,
    style: str,
    length: str,
    slides: Optional[int],
    fast: bool,
    from_stage: Optional[str],
) -> List[str]:
    command = [
        python_executable,
        "-m",
        "paper2slides",
        "--input",
        str(paper_path),
        "--output",
        "slides",
        "--style",
        style,
        "--length",
        length,
        "--output-dir",
        str(output_dir),
    ]
    if slides is not None:
        command.extend(["--slides", str(slides)])
    if fast:
        command.append("--fast")
    if from_stage:
        command.extend(["--from-stage", from_stage])
    return command


def _expected_config_dir(output_dir: Path, paper_path: Path, style: str, length: str, slides: Optional[int], fast: bool) -> Path:
    style_type, custom_style = parse_style(style)
    config = {
        "output_type": "slides",
        "style": style_type,
        "custom_style": custom_style,
        "slides_length": length,
        "target_slides": slides,
        "fast_mode": fast,
    }
    project_name = get_project_name(str(paper_path))
    base_dir = get_base_dir(str(output_dir), project_name, "paper")
    return get_config_dir(base_dir, config)


def _find_new_or_latest_output(config_dir: Path, before_outputs: set[Path]) -> Optional[Path]:
    if not config_dir.exists():
        return None
    dirs = [path for path in config_dir.iterdir() if path.is_dir()]
    new_dirs = [path for path in dirs if path.resolve() not in before_outputs]
    return _latest_by_mtime(new_dirs or dirs)


def _latest_output_dir(config_dir: Path) -> Optional[Path]:
    if not config_dir.exists():
        return None
    return _latest_by_mtime([path for path in config_dir.iterdir() if path.is_dir()])


def _latest_by_mtime(paths: List[Path]) -> Optional[Path]:
    if not paths:
        return None
    return max(paths, key=lambda path: path.stat().st_mtime)


def _result_from_existing(
    paper: Dict[str, Any],
    paper_index: int,
    set_name: str,
    style: str,
    length: str,
    slides: Optional[int],
    fast: bool,
    from_stage: Optional[str],
    config_dir: Path,
    output_subdir: Optional[Path],
    log_path: Path,
    skipped: bool,
) -> Dict[str, Any]:
    qa_path = output_subdir / "layout_qa.json" if output_subdir else None
    qa_data = _read_json(qa_path) if qa_path and qa_path.exists() else {}
    warnings = [str(item) for item in qa_data.get("warnings", []) or []]
    categories = Counter(classify_warning(warning) for warning in warnings)
    return {
        "set": set_name,
        "paper_index": paper_index,
        "paper_id": paper.get("id", ""),
        "paper_title": paper.get("title", ""),
        "paper_path": paper.get("path", ""),
        "style": style,
        "length": length,
        "slides": slides,
        "fast": fast,
        "from_stage": from_stage,
        "config_dir": str(config_dir),
        "output_dir": str(output_subdir) if output_subdir else "",
        "pptx_path": str(output_subdir / "slides.pptx") if output_subdir else "",
        "qa_report_path": str(qa_path) if qa_path else "",
        "speaker_script_path": str(output_subdir / "speaker_script.md") if output_subdir else "",
        "log_path": str(log_path),
        "returncode": 0 if skipped else None,
        "elapsed_seconds": 0.0 if skipped else None,
        "skipped": skipped,
        "qa_passed": qa_data.get("passed") if qa_data else None,
        "failed_slides": qa_data.get("failed_slides", []) if qa_data else [],
        "warning_count": len(warnings),
        "warning_categories": dict(categories),
        "slide_count": qa_data.get("slide_count") or (qa_data.get("layout") or {}).get("slide_count") or 0,
        "error": "" if qa_data else "Missing layout_qa.json",
    }


def _row_status(row: Dict[str, Any]) -> str:
    if row.get("skipped"):
        return "skipped"
    if row.get("returncode") != 0:
        return "command_failed"
    if row.get("qa_passed") is False:
        return "qa_failed"
    if row.get("qa_passed") is True:
        return "succeeded"
    return "artifact_missing"


def _render_markdown(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    lines = [
        "# paper2ppt Benchmark Run",
        "",
        f"- Total runs: {summary['total_runs']}",
        f"- Succeeded: {summary['succeeded']}",
        f"- Command failed: {summary['command_failed']}",
        f"- QA failed: {summary['qa_failed']}",
        f"- Artifact missing: {summary.get('artifact_missing', 0)}",
        f"- Skipped: {summary['skipped']}",
        f"- Success rate: {summary['success_rate']:.2%}",
        f"- Total elapsed: {summary['total_elapsed_seconds']} seconds",
        f"- Average elapsed: {summary['average_elapsed_seconds']} seconds",
        f"- Total slides: {summary['total_slides']}",
        f"- Total warnings: {summary['total_warnings']}",
        f"- Warnings per slide: {summary['warnings_per_slide']}",
        "",
        "## Warning Categories",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    for category, count in Counter(summary.get("warning_categories", {})).most_common():
        lines.append(f"| `{category}` | {count} |")
    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| # | Paper | Style | Status | QA | Warnings | Slides | Seconds | Output |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in results:
        output_dir = row.get("output_dir", "")
        lines.append(
            "| {idx} | `{paper}` | `{style}` | {status} | {qa} | {warnings} | {slides} | {seconds} | `{output}` |".format(
                idx=row.get("paper_index", ""),
                paper=row.get("paper_id") or Path(row.get("paper_path", "")).stem,
                style=row.get("style", ""),
                status=_row_status(row),
                qa=row.get("qa_passed"),
                warnings=row.get("warning_count", 0),
                slides=row.get("slide_count", 0),
                seconds=row.get("elapsed_seconds", 0),
                output=output_dir,
            )
        )
    lines.append("")
    return "\n".join(lines)


def _read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _tail_text(path: Path, lines: int) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return ""
    return "\n".join(content[-lines:])


def _safe_name(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)[:80]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run paper2ppt over a benchmark paper set.")
    parser.add_argument("action", choices=["run"], nargs="?", default="run")
    parser.add_argument("--set", default="ai20", dest="set_name")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--report-root", default=str(DEFAULT_REPORT_ROOT))
    parser.add_argument("--styles", default="academic", help="Comma-separated style list.")
    parser.add_argument("--length", choices=["short", "medium", "long"], default="medium")
    parser.add_argument("--slides", type=int, default=24)
    parser.add_argument("--no-fast", action="store_true")
    parser.add_argument("--from-stage", choices=["rag", "summary", "plan", "generate"])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--python", default=sys.executable, dest="python_executable")
    args = parser.parse_args(argv)

    styles = [style.strip() for style in args.styles.split(",") if style.strip()]
    result = run_benchmark(
        set_name=args.set_name,
        manifest_path=Path(args.manifest),
        output_dir=Path(args.output_dir),
        report_root=Path(args.report_root),
        styles=styles,
        length=args.length,
        slides=args.slides,
        fast=not args.no_fast,
        from_stage=args.from_stage,
        limit=args.limit,
        start_index=args.start_index,
        resume=args.resume,
        python_executable=args.python_executable,
    )
    print(json.dumps({"report_dir": result["report_dir"], "summary": result["summary"]}, ensure_ascii=False, indent=2))
    has_infra_failure = result["summary"]["command_failed"] or result["summary"].get("artifact_missing", 0)
    return 0 if has_infra_failure == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
