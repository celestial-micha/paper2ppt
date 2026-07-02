"""Build a visual-probe spec from a seed-template contract."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .strategist import load_seed_template_package


PROBE_ROLES = [
    "cover",
    "central_thesis",
    "method_stack",
    "metric_ledger",
    "evidence_wall",
    "figure_or_table_focus",
    "risk_map",
    "closing_takeaway",
]


def build_visual_probe_spec(
    inventory: Dict[str, Any],
    contract: Dict[str, Any],
    package: Dict[str, Any],
    *,
    probe_slides: int = 8,
) -> Dict[str, Any]:
    """Build a deterministic 7-8 page visual probe specification."""
    selected_roles = PROBE_ROLES[: max(1, min(probe_slides, len(PROBE_ROLES)))]
    slides = [
        _probe_slide(index, role, inventory, contract, package)
        for index, role in enumerate(selected_roles, start=1)
    ]
    return {
        "schema_version": "visual_probe_spec.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "paper_title": inventory.get("paper", {}).get("title", ""),
        "template_id": package.get("provenance", {}).get("template_id", ""),
        "purpose": "pre-render probe spec; no PPTX generated yet",
        "rules": {
            "native_editability_required": True,
            "full_deck_generation_allowed": False,
            "must_pass_template_gate_before_full_deck": True,
            "content_coverage_is_probe_level": True,
        },
        "slides": slides,
        "source_contract": {
            "schema_version": contract.get("schema_version", ""),
            "deck_thesis": contract.get("deck_intent", {}).get("deck_thesis", ""),
            "style_intent": contract.get("narrative_strategy", {}).get("style_intent", ""),
        },
    }


def evaluate_visual_probe_spec(
    spec: Dict[str, Any],
    contract: Dict[str, Any],
    package: Dict[str, Any],
) -> Dict[str, Any]:
    """Gate a visual probe spec before any renderer work."""
    slides = spec.get("slides", []) or []
    roles = [slide.get("role", "") for slide in slides]
    proofful = [slide for slide in slides if slide.get("proof_object", {}).get("type") != "none"]
    checks = [
        _check("probe_slide_count", 7 <= len(slides) <= 8, len(slides), "7-8 slides"),
        _check("required_roles", all(role in roles for role in PROBE_ROLES[: len(slides)]), roles, PROBE_ROLES[: len(slides)]),
        _check("proof_object_coverage", len(proofful) >= 4, len(proofful), "at least 4 proof-bearing slides"),
        _check("template_package_gate_not_failed", package.get("template_gate", {}).get("status") != "fail", package.get("template_gate", {}).get("status"), "not fail"),
        _check("renderer_not_invoked", spec.get("purpose") == "pre-render probe spec; no PPTX generated yet", spec.get("purpose"), "spec-only"),
    ]
    warnings = []
    if package.get("template_gate", {}).get("status") == "pass_with_warnings":
        warnings.append("source_template_package_has_warnings")
    if contract.get("template_package_gate", {}).get("status") == "pass_with_warnings":
        warnings.append("human_feedback_required_before_default_promotion")
    failed = [check for check in checks if check["status"] == "fail"]
    status = "fail" if failed else ("pass_with_warnings" if warnings else "pass")
    return {
        "schema_version": "visual_probe_gate.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "recommendation": _recommendation(status, failed, warnings),
    }


def write_visual_probe_artifacts(
    inventory_path: Path,
    contract_path: Path,
    package_dir: Path,
    output_dir: Path,
    *,
    probe_slides: int = 8,
) -> Dict[str, str]:
    inventory = _read_json(inventory_path)
    contract = _read_json(contract_path)
    package = load_seed_template_package(package_dir)
    spec = build_visual_probe_spec(inventory, contract, package, probe_slides=probe_slides)
    gate = evaluate_visual_probe_spec(spec, contract, package)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "visual_probe_spec": str(output_dir / "visual_probe_spec.json"),
        "visual_probe_gate": str(output_dir / "visual_probe_gate.json"),
        "visual_probe_brief": str(output_dir / "visual_probe_brief.md"),
    }
    _write_json(output_dir / "visual_probe_spec.json", spec)
    _write_json(output_dir / "visual_probe_gate.json", gate)
    (output_dir / "visual_probe_brief.md").write_text(_render_probe_brief(spec, gate), encoding="utf-8")
    return paths


def _probe_slide(index: int, role: str, inventory: Dict[str, Any], contract: Dict[str, Any], package: Dict[str, Any]) -> Dict[str, Any]:
    title = _title_for_role(role, inventory)
    content = _content_for_role(role, inventory, contract)
    proof_object = _proof_for_role(role, inventory, contract)
    layout_id = _layout_for_role(role, package)
    return {
        "slide_index": index,
        "slide_id": f"probe_{index:02d}",
        "role": role,
        "title": title,
        "claim": content.get("claim", ""),
        "support": content.get("support", ""),
        "proof_object": proof_object,
        "layout_candidate": layout_id,
        "component_primitives": _primitives_for_role(role),
        "text_budget_words": _text_budget_for_role(role),
        "gate_notes": [
            "render as native editable shapes/text",
            "preserve seed package typography floors",
            "do not expand to full deck before gate review",
        ],
    }


def _title_for_role(role: str, inventory: Dict[str, Any]) -> str:
    paper_title = inventory.get("paper", {}).get("title", "Untitled Paper")
    return {
        "cover": paper_title,
        "central_thesis": "Central Thesis",
        "method_stack": "Safety Stack",
        "metric_ledger": "Evaluation Ledger",
        "evidence_wall": "Evidence Wall",
        "figure_or_table_focus": "Source Evidence Focus",
        "risk_map": "Residual Risk Map",
        "closing_takeaway": "Takeaway",
    }.get(role, role.replace("_", " ").title())


def _content_for_role(role: str, inventory: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, str]:
    highlights = inventory.get("paper_highlights", []) or []
    summary_items = inventory.get("summary_items", []) or []
    if role == "cover":
        return {"claim": contract.get("deck_intent", {}).get("deck_thesis", ""), "support": "System-card reading deck with safety and evaluation emphasis."}
    if role == "central_thesis":
        return {"claim": _highlight(highlights, 0), "support": _summary_text(summary_items, "motivation")}
    if role == "method_stack":
        return {"claim": "Layered safety method combines training, monitoring, controls, and red-teaming.", "support": _summary_text(summary_items, "method")}
    if role == "metric_ledger":
        return {"claim": "Key scores summarize the safety and reliability picture.", "support": _metric_summary(inventory)}
    if role == "evidence_wall":
        return {"claim": "Evidence objects should remain source-traceable.", "support": _asset_summary(inventory)}
    if role == "figure_or_table_focus":
        return {"claim": "A single proof object gets a focused reading path.", "support": _first_table_or_figure_caption(inventory)}
    if role == "risk_map":
        return {"claim": "Residual risks remain after safeguards.", "support": _summary_text(summary_items, "motivation", offset=2)}
    if role == "closing_takeaway":
        return {"claim": _highlight(highlights, 1), "support": "Full-deck promotion requires content coverage and human preference feedback."}
    return {"claim": "", "support": ""}


def _proof_for_role(role: str, inventory: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
    roster = contract.get("proof_object_roster", {})
    metrics = roster.get("metrics", []) or []
    figures = roster.get("figures", []) or []
    tables = roster.get("tables", []) or []
    if role == "metric_ledger" and metrics:
        return {"type": "metric_set", "items": metrics[:4]}
    if role == "figure_or_table_focus":
        item = (tables or figures or [{}])[0]
        return {"type": item.get("kind", "table_or_figure"), "item": item}
    if role == "evidence_wall":
        return {"type": "evidence_set", "items": (tables[:2] + figures[:2] + metrics[:2])}
    if role in {"central_thesis", "method_stack", "risk_map"}:
        return {"type": "evidence_note", "items": (figures[:1] + tables[:1] + metrics[:1])}
    return {"type": "none", "items": []}


def _layout_for_role(role: str, package: Dict[str, Any]) -> str:
    roster = package.get("page_role_roster", {}).get("role_to_layouts", {})
    if role == "cover":
        return (roster.get("cover") or ["cover_01"])[0]
    if role == "metric_ledger":
        return (roster.get("metric") or ["metric_04"])[0]
    return (roster.get("content") or ["content_02"])[0]


def _primitives_for_role(role: str) -> List[str]:
    base = ["native_textbox", "native_rect", "source_chip"]
    if role == "metric_ledger":
        return base + ["metric_card", "evidence_note"]
    if role in {"evidence_wall", "figure_or_table_focus"}:
        return base + ["proof_panel", "native_table", "figure_slot"]
    return base + ["evidence_note"]


def _text_budget_for_role(role: str) -> int:
    return {"cover": 65, "metric_ledger": 90, "evidence_wall": 120, "figure_or_table_focus": 100, "closing_takeaway": 75}.get(role, 105)


def _highlight(highlights: List[Dict[str, Any]], index: int) -> str:
    if index < len(highlights):
        return str(highlights[index].get("body", "") or highlights[index].get("label", ""))
    return "Evidence-grounded reading path for the paper."


def _summary_text(items: List[Dict[str, Any]], category: str, offset: int = 0) -> str:
    candidates = [item for item in items if item.get("category") == category]
    if not candidates:
        candidates = items
    if not candidates:
        return ""
    item = candidates[min(offset, len(candidates) - 1)]
    return _limit_words(item.get("text", ""), 36)


def _metric_summary(inventory: Dict[str, Any]) -> str:
    metrics = inventory.get("metrics", []) or []
    if not metrics:
        return "No metrics detected; use sourced evidence notes instead."
    return "; ".join(f"{item.get('label', '')}: {item.get('value', '')}" for item in metrics[:4])


def _asset_summary(inventory: Dict[str, Any]) -> str:
    assets = inventory.get("assets", {}) or {}
    return f"{len(assets.get('figures', []) or [])} figures and {len(assets.get('tables', []) or [])} tables available from checkpoint."


def _first_table_or_figure_caption(inventory: Dict[str, Any]) -> str:
    assets = inventory.get("assets", {}) or {}
    for item in (assets.get("tables", []) or []) + (assets.get("figures", []) or []):
        caption = item.get("caption", "") or item.get("title", "") or item.get("id", "")
        if caption:
            return _limit_words(caption, 28)
    return "Use the strongest source object available in checkpoint."


def _render_probe_brief(spec: Dict[str, Any], gate: Dict[str, Any]) -> str:
    lines = [
        "# Visual Probe Spec Brief",
        "",
        f"- Paper: {spec.get('paper_title', '')}",
        f"- Template: {spec.get('template_id', '')}",
        f"- Gate status: {gate.get('status', '')}",
        f"- Recommendation: {gate.get('recommendation', '')}",
        "",
        "## Slides",
        "",
    ]
    for slide in spec.get("slides", []) or []:
        lines.append(f"- {slide.get('slide_id')}: {slide.get('role')} - {slide.get('title')}")
    lines.append("")
    return "\n".join(lines)


def _check(check_id: str, passed: bool, observed: Any, threshold: Any) -> Dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "observed": observed, "threshold": threshold}


def _recommendation(status: str, failed: List[Dict[str, Any]], warnings: List[str]) -> str:
    if status == "fail":
        return "Repair the probe spec before renderer work: " + ", ".join(check["id"] for check in failed)
    if warnings:
        return "Spec is ready for a renderer prototype, but keep it human-gated: " + ", ".join(warnings)
    return "Spec is ready for a renderer prototype."


def _limit_words(text: Any, limit: int) -> str:
    words = str(text or "").replace("\n", " ").split()
    if len(words) <= limit:
        return " ".join(words)
    return " ".join(words[:limit]).rstrip(".,;:") + "..."


def _read_json(path: Path) -> Dict[str, Any]:
    if not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build a spec-only visual probe from seed strategy artifacts.")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--probe-slides", type=int, default=8)
    args = parser.parse_args(argv)
    paths = write_visual_probe_artifacts(
        Path(args.inventory),
        Path(args.contract),
        Path(args.package_dir),
        Path(args.output_dir),
        probe_slides=args.probe_slides,
    )
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
