"""Batch runner for universal PPT benchmark scorecards."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .deck_ir import write_schema_bundle
from .pptx_intake import write_pptx_intake_bundle


def run_universal_pptx_benchmark(
    deck_specs: List[Dict[str, Any]],
    output_dir: Path,
    *,
    summary_checkpoint: Optional[Path] = None,
    plan_checkpoint: Optional[Path] = None,
    spec_checkpoint: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run DeckIR intake and scorecard generation for multiple PPTX decks."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    schema_paths = write_schema_bundle(output_dir)

    results = []
    for spec in deck_specs:
        label = _safe_label(spec.get("label") or Path(spec["pptx"]).stem)
        deck_dir = output_dir / label
        paths = write_pptx_intake_bundle(
            Path(spec["pptx"]),
            deck_dir,
            label=spec.get("label") or label,
            generator=spec.get("generator", "unknown"),
            audit_path=Path(spec["audit"]) if spec.get("audit") else None,
            repair_log_path=Path(spec["repair_log"]) if spec.get("repair_log") else None,
            summary_checkpoint=summary_checkpoint,
            plan_checkpoint=plan_checkpoint,
            spec_checkpoint=spec_checkpoint,
            run_nonvisual_audit=not bool(spec.get("no_audit", False)),
        )
        scorecard = _read_json(Path(paths["universal_scorecard"]))
        result = {
            "label": spec.get("label") or label,
            "generator": spec.get("generator", "unknown"),
            "pptx": str(Path(spec["pptx"])),
            "output_dir": str(deck_dir),
            "paths": paths,
            "scorecard": scorecard,
        }
        results.append(result)

    csv_path = output_dir / "universal_scorecards.csv"
    rows = _scorecard_rows(results)
    _write_csv(csv_path, rows)
    report_path = output_dir / "universal_benchmark_report.md"
    report_path.write_text(_render_report(results, rows), encoding="utf-8")

    manifest = {
        "schema_version": "universal_pptx_benchmark_run.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "source_checkpoints": {
            "summary": str(summary_checkpoint) if summary_checkpoint else "",
            "plan": str(plan_checkpoint) if plan_checkpoint else "",
            "slide_spec": str(spec_checkpoint) if spec_checkpoint else "",
        },
        "deck_count": len(deck_specs),
        "decks": [
            {
                "label": result["label"],
                "generator": result["generator"],
                "pptx": result["pptx"],
                "deck_ir": result["paths"].get("deck_ir", ""),
                "scorecard": result["paths"].get("universal_scorecard", ""),
            }
            for result in results
        ],
        "scorecards_csv": str(csv_path),
        "report": str(report_path),
        "schemas": schema_paths,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "manifest": str(manifest_path),
        "scorecards_csv": str(csv_path),
        "report": str(report_path),
        "results": results,
    }


def _scorecard_rows(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for result in results:
        scorecard = result["scorecard"]
        dims = scorecard.get("dimensions", {})
        row = {
            "label": result["label"],
            "generator": result["generator"],
            "slides": scorecard.get("deck_summary", {}).get("slide_count", 0),
            "native_text_chars": scorecard.get("deck_summary", {}).get("native_text_chars", 0),
            "raster_area_ratio": scorecard.get("deck_summary", {}).get("raster_area_ratio", 0.0),
            "overall": scorecard.get("overall", {}).get("score", ""),
        }
        for name in scorecard.get("dimension_order", []) or []:
            payload = dims.get(name, {})
            row[name] = payload.get("score", "")
            row[f"{name}_status"] = payload.get("status", "")
        alignment = scorecard.get("content_alignment", {}).get("coverage", {})
        row["key_term_coverage"] = alignment.get("key_term_coverage", "")
        row["slide_title_coverage"] = alignment.get("slide_title_coverage", "")
        row["section_coverage"] = alignment.get("section_coverage", "")
        row["evidence_ref_coverage"] = alignment.get("evidence_ref_coverage", "")
        rows.append(row)
    return rows


def _render_report(results: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Universal PPT Benchmark Report",
        "",
        f"- Created at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Deck count: `{len(results)}`",
        "",
        "## Score Summary",
        "",
        "| Deck | Generator | Slides | Overall | Editability | Content | Evidence | Layout | Typography | Visual | Repair |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['label']}` | `{row['generator']}` | {row['slides']} | {_fmt(row.get('overall'))} | "
            f"{_fmt(row.get('editability'))} | {_fmt(row.get('content_fidelity'))} | {_fmt(row.get('evidence_grounding'))} | "
            f"{_fmt(row.get('layout_geometry'))} | {_fmt(row.get('typography'))} | {_fmt(row.get('visual_design'))} | "
            f"{_fmt(row.get('repairability'))} |"
        )
    lines.extend(
        [
            "",
            "## Checkpoint Coverage",
            "",
            "| Deck | Key Terms | Slide Titles | Sections | Evidence Refs |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row['label']}` | {_fmt(row.get('key_term_coverage'))} | {_fmt(row.get('slide_title_coverage'))} | "
            f"{_fmt(row.get('section_coverage'))} | {_fmt(row.get('evidence_ref_coverage'))} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `content_fidelity` uses checkpoint-derived keyword/title/section coverage when checkpoints are provided.",
            "- `evidence_grounding` uses proof-object metadata plus checkpoint figure/table/metric reference coverage.",
            "- `visual_design` is still a heuristic proxy and remains human-calibrated.",
            "- `human_preference` is intentionally unscored in v0.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["label"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_deck_spec(text: str) -> Dict[str, Any]:
    parts = text.split("|")
    if len(parts) < 2:
        raise ValueError("--deck must be label|pptx|generator|audit|repair_log")
    parts = parts + [""] * (5 - len(parts))
    label, pptx, generator, audit, repair_log = parts[:5]
    return {
        "label": label,
        "pptx": pptx,
        "generator": generator or "unknown",
        "audit": audit,
        "repair_log": repair_log,
    }


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_label(text: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in str(text or "deck"))
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "deck"


def _fmt(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):.1f}"
    except Exception:
        return str(value)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run universal PPTX benchmark on multiple decks.")
    parser.add_argument("--output-dir", required=True, help="Directory for manifest, CSV, report, and per-deck bundles.")
    parser.add_argument(
        "--deck",
        action="append",
        required=True,
        help="Deck spec: label|pptx|generator|audit_json|repair_log_json. audit/repair_log can be blank.",
    )
    parser.add_argument("--summary-checkpoint", help="checkpoint_summary.json for content alignment.")
    parser.add_argument("--plan-checkpoint", help="checkpoint_plan.json for content alignment.")
    parser.add_argument("--spec-checkpoint", help="checkpoint_slide_spec.json for content alignment.")
    args = parser.parse_args(argv)

    deck_specs = [_parse_deck_spec(text) for text in args.deck]
    result = run_universal_pptx_benchmark(
        deck_specs,
        Path(args.output_dir),
        summary_checkpoint=Path(args.summary_checkpoint) if args.summary_checkpoint else None,
        plan_checkpoint=Path(args.plan_checkpoint) if args.plan_checkpoint else None,
        spec_checkpoint=Path(args.spec_checkpoint) if args.spec_checkpoint else None,
    )
    print(json.dumps({key: value for key, value in result.items() if key != "results"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
