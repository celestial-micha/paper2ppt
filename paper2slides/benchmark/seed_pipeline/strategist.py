"""Deterministic seed strategist for PPT Master-style pipeline experiments."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from paper2slides.benchmark.from_scratch import build_content_inventory


def load_seed_template_package(package_dir: Path) -> Dict[str, Any]:
    """Load a seed_template_package directory."""
    package_dir = Path(package_dir)
    return {
        "brand": _read_json(package_dir / "brand.json"),
        "spec_lock": _read_json(package_dir / "spec_lock.json"),
        "layout_registry": _read_json(package_dir / "layout_registry.json"),
        "component_primitives": _read_json(package_dir / "component_primitives.json"),
        "page_role_roster": _read_json(package_dir / "page_role_roster.json"),
        "validator_rules": _read_json(package_dir / "validator_rules.json"),
        "provenance": _read_json(package_dir / "provenance.json"),
        "template_gate": _read_json(package_dir / "template_gate.json"),
    }


def build_seed_template_contract(
    inventory: Dict[str, Any],
    package: Dict[str, Any],
    *,
    slide_budget: int = 24,
    probe_slides: int = 8,
) -> Dict[str, Any]:
    """Build a machine-readable seed-template contract from content inventory."""
    title = inventory.get("paper", {}).get("title", "Untitled Paper")
    package_roles = package.get("page_role_roster", {})
    spec_lock = package.get("spec_lock", {})
    brand = package.get("brand", {})
    validator = package.get("validator_rules", {})
    proof_roster = _proof_object_roster(inventory)
    sections = _section_roster(inventory)

    return {
        "schema_version": "seed_template_contract.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "paper": {
            "title": title,
            "content_type": inventory.get("paper", {}).get("content_type", "paper"),
            "source_checkpoints": inventory.get("source_checkpoints", {}),
        },
        "deck_intent": {
            "task_type": "academic_paper_reading_deck",
            "deck_thesis": _deck_thesis(inventory),
            "target_audience": "technical evaluators who need a fast, evidence-grounded read of a system card",
            "success_criteria": [
                "native editable PPTX",
                "clear proof-object slots",
                "strong first-draft visual rhythm",
                "content coverage verified against checkpoint",
                "template gate before full deck expansion",
            ],
        },
        "generation_scope": {
            "slide_budget": slide_budget,
            "probe_slides": probe_slides,
            "first_deliverable": "visual_probe_spec",
            "renderer_policy": "do not render full deck until visual probe passes template gate",
        },
        "narrative_strategy": {
            "arc": [
                "cover",
                "central_thesis",
                "method_stack",
                "metric_ledger",
                "evidence_wall",
                "figure_or_table_focus",
                "risk_map",
                "closing_takeaway",
            ],
            "section_roster": sections,
            "page_rhythm_policy": spec_lock.get("page_rhythm", {}),
            "style_intent": brand.get("visual_language", ""),
        },
        "page_role_roster": {
            "probe_required": [
                "cover",
                "central_thesis",
                "method_stack",
                "metric_ledger",
                "evidence_wall",
                "figure_or_table_focus",
                "risk_map",
                "closing_takeaway",
            ],
            "full_deck_recommended": package_roles.get("recommended_full_deck_roles", []),
            "observed_seed_roles": package_roles.get("observed_role_counts", {}),
        },
        "proof_object_roster": proof_roster,
        "visual_language": {
            "brand": brand,
            "spec_lock": spec_lock,
            "component_primitives": package.get("component_primitives", {}),
            "layout_registry_summary": _layout_registry_summary(package.get("layout_registry", {})),
        },
        "content_coverage_policy": {
            "min_key_term_coverage": 0.70,
            "min_slide_title_coverage": 0.65,
            "min_section_coverage": 0.75,
            "min_evidence_ref_coverage": 0.60,
            "full_deck_content_min_score": validator.get("full_deck_content_min_score", 70.0),
            "probe_can_have_low_content_coverage": True,
        },
        "native_editability_constraints": {
            "min_editability_score": validator.get("min_editability_score", 90.0),
            "max_raster_area_ratio": validator.get("max_raster_area_ratio", 0.08),
            "allowed_primitives": [
                item.get("primitive_id")
                for item in package.get("component_primitives", {}).get("primitives", [])
                if item.get("native_pptx_required", True)
            ],
        },
        "known_badcase_guardrails": {
            "forbidden_patterns": spec_lock.get("forbidden_patterns", []),
            "inventory_reuse_forbidden": inventory.get("design_constraints", {}).get("reuse_forbidden", []),
            "plateau_avoidance": [
                "do not expand a weak probe to full deck",
                "treat deck-wide type-scale failures as template blockers",
                "repair template before page-level copy fitting",
            ],
        },
        "template_package_gate": {
            "status": package.get("template_gate", {}).get("status", ""),
            "recommendation": package.get("template_gate", {}).get("recommendation", ""),
        },
    }


def write_seed_strategy_artifacts(
    summary_checkpoint: Path,
    plan_checkpoint: Optional[Path],
    spec_checkpoint: Optional[Path],
    package_dir: Path,
    output_dir: Path,
    *,
    slide_budget: int = 24,
    probe_slides: int = 8,
) -> Dict[str, str]:
    """Write content inventory, seed contract, and human-readable brief."""
    inventory = build_content_inventory(summary_checkpoint, plan_checkpoint, spec_checkpoint)
    package = load_seed_template_package(package_dir)
    contract = build_seed_template_contract(inventory, package, slide_budget=slide_budget, probe_slides=probe_slides)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "content_inventory": str(output_dir / "content_inventory.json"),
        "seed_template_contract": str(output_dir / "seed_template_contract.json"),
        "seed_template_brief": str(output_dir / "seed_template_brief.md"),
    }
    _write_json(output_dir / "content_inventory.json", inventory)
    _write_json(output_dir / "seed_template_contract.json", contract)
    (output_dir / "seed_template_brief.md").write_text(_render_seed_template_brief(contract), encoding="utf-8")
    return paths


def _deck_thesis(inventory: Dict[str, Any]) -> str:
    highlights = inventory.get("paper_highlights", []) or []
    if highlights:
        return str(highlights[0].get("body", "") or highlights[0].get("label", ""))
    for item in inventory.get("summary_items", []) or []:
        if item.get("category") in {"motivation", "contribution"}:
            return _limit_words(item.get("text", ""), 32)
    return inventory.get("paper", {}).get("title", "Untitled Paper")


def _section_roster(inventory: Dict[str, Any]) -> List[Dict[str, Any]]:
    counts = Counter()
    for slide in inventory.get("plan_slides", []) or []:
        counts[slide.get("section", "unknown")] += 1
    if not counts:
        for slide in inventory.get("curated_slides", []) or []:
            counts[slide.get("section_label", "unknown")] += 1
    return [{"section": key, "planned_slide_count": value} for key, value in counts.items() if key]


def _proof_object_roster(inventory: Dict[str, Any]) -> Dict[str, Any]:
    assets = inventory.get("assets", {}) or {}
    figures = list(assets.get("figures", []) or [])[:12]
    tables = list(assets.get("tables", []) or [])[:12]
    metrics = list(inventory.get("metrics", []) or [])[:12]
    return {
        "schema_version": "proof_object_roster.v0",
        "figures": [_proof_item(item, "figure") for item in figures],
        "tables": [_proof_item(item, "table") for item in tables],
        "metrics": [_metric_item(item) for item in metrics],
        "counts": {
            "figures": len(assets.get("figures", []) or []),
            "tables": len(assets.get("tables", []) or []),
            "metrics": len(inventory.get("metrics", []) or []),
        },
        "selection_policy": "visual probe should cover at least one metric ledger and one table/figure/evidence page",
    }


def _proof_item(item: Dict[str, Any], kind: str) -> Dict[str, Any]:
    return {
        "id": item.get("id", ""),
        "kind": kind,
        "caption": _limit_words(item.get("caption", "") or item.get("title", ""), 24),
        "path": item.get("path", ""),
    }


def _metric_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "label": item.get("label", ""),
        "value": item.get("value", ""),
        "note": item.get("note", ""),
        "source_slide": item.get("source_slide", ""),
    }


def _layout_registry_summary(layout_registry: Dict[str, Any]) -> Dict[str, Any]:
    layouts = layout_registry.get("layouts", []) or []
    role_counts = Counter(layout.get("role", "unknown") for layout in layouts)
    return {
        "layout_count": len(layouts),
        "role_counts": dict(role_counts),
        "layout_ids": [layout.get("layout_id", "") for layout in layouts],
    }


def _render_seed_template_brief(contract: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Seed Template Brief",
            "",
            f"- Paper: {contract.get('paper', {}).get('title', '')}",
            f"- Deck thesis: {contract.get('deck_intent', {}).get('deck_thesis', '')}",
            f"- Target audience: {contract.get('deck_intent', {}).get('target_audience', '')}",
            f"- Slide budget: {contract.get('generation_scope', {}).get('slide_budget')}",
            f"- Probe slides: {contract.get('generation_scope', {}).get('probe_slides')}",
            f"- Template package gate: {contract.get('template_package_gate', {}).get('status', '')}",
            "",
            "## Narrative Arc",
            "",
            "\n".join(f"- {role}" for role in contract.get("narrative_strategy", {}).get("arc", [])),
            "",
            "## Guardrails",
            "",
            "\n".join(f"- {item}" for item in contract.get("known_badcase_guardrails", {}).get("forbidden_patterns", [])),
            "",
        ]
    )


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
    parser = argparse.ArgumentParser(description="Build seed-template contract from checkpoints and a seed package.")
    parser.add_argument("--summary-checkpoint", required=True)
    parser.add_argument("--plan-checkpoint")
    parser.add_argument("--spec-checkpoint")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--slide-budget", type=int, default=24)
    parser.add_argument("--probe-slides", type=int, default=8)
    args = parser.parse_args(argv)
    paths = write_seed_strategy_artifacts(
        Path(args.summary_checkpoint),
        Path(args.plan_checkpoint) if args.plan_checkpoint else None,
        Path(args.spec_checkpoint) if args.spec_checkpoint else None,
        Path(args.package_dir),
        Path(args.output_dir),
        slide_budget=args.slide_budget,
        probe_slides=args.probe_slides,
    )
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
