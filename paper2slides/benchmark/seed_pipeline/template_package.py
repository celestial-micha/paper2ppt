"""Build a seed-template package from a strong DeckIR probe."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .template_gate import evaluate_template_gate


def build_seed_template_package(
    deck_ir: Dict[str, Any],
    scorecard: Dict[str, Any],
    *,
    template_id: str = "ppt_master_inspired_seed_v0",
    source_label: str = "07_ppt_master_inspired_native",
) -> Dict[str, Any]:
    """Build machine-readable seed-template artifacts from DeckIR signals."""
    brand = _brand(deck_ir, source_label)
    spec_lock = _spec_lock(deck_ir, scorecard, brand)
    layout_registry = _layout_registry(deck_ir)
    component_primitives = _component_primitives(deck_ir)
    page_role_roster = _page_role_roster(deck_ir, layout_registry)
    validator_rules = _validator_rules(scorecard)
    provenance = {
        "schema_version": "seed_template_provenance.v0",
        "template_id": template_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_label": source_label,
        "source_deck_ir": deck_ir.get("source", {}),
        "source_scorecard_schema": scorecard.get("schema_version", ""),
        "policy": {
            "derived_from_external_reference": True,
            "copy_full_slide_templates": False,
            "use_as_seed_template_contract": True,
            "requires_human_feedback_before_default_promotion": True,
        },
    }
    package = {
        "schema_version": "seed_template_package.v0",
        "template_id": template_id,
        "brand": brand,
        "spec_lock": spec_lock,
        "layout_registry": layout_registry,
        "component_primitives": component_primitives,
        "page_role_roster": page_role_roster,
        "validator_rules": validator_rules,
        "provenance": provenance,
    }
    return package


def write_seed_template_package(
    deck_ir_path: Path,
    scorecard_path: Path,
    output_dir: Path,
    *,
    template_id: str = "ppt_master_inspired_seed_v0",
    source_label: str = "07_ppt_master_inspired_native",
) -> Dict[str, str]:
    """Write a seed_template_package directory and template gate result."""
    deck_ir = _read_json(deck_ir_path)
    scorecard = _read_json(scorecard_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    package = build_seed_template_package(deck_ir, scorecard, template_id=template_id, source_label=source_label)
    gate = evaluate_template_gate(deck_ir, scorecard, package)

    paths = {
        "design_spec": str(output_dir / "design_spec.md"),
        "spec_lock": str(output_dir / "spec_lock.json"),
        "brand": str(output_dir / "brand.json"),
        "layout_registry": str(output_dir / "layout_registry.json"),
        "component_primitives": str(output_dir / "component_primitives.json"),
        "page_role_roster": str(output_dir / "page_role_roster.json"),
        "validator_rules": str(output_dir / "validator_rules.json"),
        "provenance": str(output_dir / "provenance.json"),
        "template_gate": str(output_dir / "template_gate.json"),
        "package_index": str(output_dir / "package_index.json"),
    }
    (output_dir / "design_spec.md").write_text(_render_design_spec(package, scorecard, gate), encoding="utf-8")
    _write_json(output_dir / "spec_lock.json", package["spec_lock"])
    _write_json(output_dir / "brand.json", package["brand"])
    _write_json(output_dir / "layout_registry.json", package["layout_registry"])
    _write_json(output_dir / "component_primitives.json", package["component_primitives"])
    _write_json(output_dir / "page_role_roster.json", package["page_role_roster"])
    _write_json(output_dir / "validator_rules.json", package["validator_rules"])
    _write_json(output_dir / "provenance.json", package["provenance"])
    _write_json(output_dir / "template_gate.json", gate)
    _write_json(
        output_dir / "package_index.json",
        {
            "schema_version": "seed_template_package_index.v0",
            "template_id": template_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "paths": paths,
            "gate_status": gate.get("status", ""),
        },
    )
    return paths


def _brand(deck_ir: Dict[str, Any], source_label: str) -> Dict[str, Any]:
    theme = deck_ir.get("deck", {}).get("theme_signals", {})
    palette = list(theme.get("palette", []) or [])
    if not palette:
        palette = ["#F7F3EA", "#171717", "#2E6F7E", "#E05D3F", "#38495C"]
    fonts = list(theme.get("font_families", []) or [])
    if not fonts:
        fonts = ["Aptos", "Arial", "Calibri"]
    dominant_backgrounds = list(theme.get("dominant_backgrounds", []) or [])
    background = _first_light(dominant_backgrounds + palette) or "#F4F0E8"
    ink = _first_dark(palette) or "#171717"
    return {
        "schema_version": "seed_brand.v0",
        "brand_name": source_label,
        "visual_language": "editorial data-reporting deck with native evidence blocks and restrained accent color",
        "palette": {
            "observed": palette[:12],
            "background": background,
            "ink": ink,
            "accent": _first_accent(palette) or palette[min(2, len(palette) - 1)],
            "muted": "#6B7280",
        },
        "font_families": fonts[:8],
        "tone": ["editorial", "analytical", "source-grounded", "native-editable"],
    }


def _spec_lock(deck_ir: Dict[str, Any], scorecard: Dict[str, Any], brand: Dict[str, Any]) -> Dict[str, Any]:
    deck = deck_ir.get("deck", {})
    typography = _typography_ranges(deck_ir)
    return {
        "schema_version": "spec_lock.v0",
        "canvas": {"width_in": deck.get("width_in", 13.333), "height_in": deck.get("height_in", 7.5)},
        "palette": brand.get("palette", {}),
        "typography": typography,
        "page_rhythm": _page_rhythm(deck_ir),
        "proof_object_strategy": {
            "default": "native evidence block with source/caption chip",
            "metric_pages": "metric ledger with compact explanatory notes",
            "figure_pages": "figure/table slot must remain native or traceable to source evidence",
        },
        "forbidden_patterns": [
            "full-slide raster screenshot",
            "generic bullet-only page",
            "unlabeled proof object",
            "table rendered as unreadable image",
            "repeating one layout signature across a full deck",
            "expanding a visual probe into full deck without content coverage gate",
        ],
        "source_score_signals": {
            "editability": _dimension_score(scorecard, "editability"),
            "typography": _dimension_score(scorecard, "typography"),
            "layout_geometry": _dimension_score(scorecard, "layout_geometry"),
            "visual_design": _dimension_score(scorecard, "visual_design"),
        },
    }


def _layout_registry(deck_ir: Dict[str, Any]) -> Dict[str, Any]:
    layouts: List[Dict[str, Any]] = []
    for slide in deck_ir.get("slides", []) or []:
        role = slide.get("role_guess", "unknown")
        layout_id = _layout_id(role, slide.get("slide_index", 0), slide.get("layout", {}).get("layout_signature", ""))
        objects = slide.get("objects", []) or []
        editability = slide.get("editability", {})
        layouts.append(
            {
                "layout_id": layout_id,
                "source_slide_index": slide.get("slide_index"),
                "role": role,
                "input_content_type": _content_type_for_role(role),
                "expected_density": _density_band(slide.get("layout", {}).get("occupancy", 0.0)),
                "max_text_budget_words": _max_text_budget(role),
                "proof_object_slot": _proof_slot(objects),
                "typography_floor_pt": _typography_floor(role),
                "geometry_constraints": [
                    "keep meaningful objects inside slide safe area",
                    "preserve native text/shape editability",
                    "align source/caption chips to their proof object",
                ],
                "repair_affordance": _repair_affordance(role),
                "layout_signature": slide.get("layout", {}).get("layout_signature", ""),
            }
        )
    return {
        "schema_version": "layout_registry.v0",
        "purpose": "layout candidates extracted from the 07 visual probe, not full slide templates",
        "layouts": layouts,
    }


def _component_primitives(deck_ir: Dict[str, Any]) -> Dict[str, Any]:
    counts = Counter()
    for slide in deck_ir.get("slides", []) or []:
        for obj in slide.get("objects", []) or []:
            counts[obj.get("kind", "unknown")] += 1
    primitives = [
        _primitive("native_textbox", "native editable text for title, claim, support, captions", counts.get("text", 0)),
        _primitive("native_rect", "native shape container for evidence and metric groups", counts.get("shape", 0)),
        _primitive("native_rule", "thin native rule or separator line", counts.get("decorative", 0)),
        _primitive("metric_card", "editable metric value plus label plus context note", 0),
        _primitive("evidence_note", "short sourced claim or annotation tied to proof object", 0),
        _primitive("proof_panel", "container that groups figure/table/metric evidence with source chip", 0),
        _primitive("source_chip", "small source/caption marker, native text not image", 0),
        _primitive("figure_slot", "image or chart slot with aspect-preserving fit", counts.get("picture", 0)),
        _primitive("native_table", "editable table object when data is tabular", counts.get("table", 0)),
    ]
    return {
        "schema_version": "component_primitives.v0",
        "native_editability_required": True,
        "observed_kind_counts": dict(counts),
        "primitives": primitives,
    }


def _page_role_roster(deck_ir: Dict[str, Any], layout_registry: Dict[str, Any]) -> Dict[str, Any]:
    role_counts = deck_ir.get("summary", {}).get("role_counts", {})
    layouts = layout_registry.get("layouts", [])
    return {
        "schema_version": "page_role_roster.v0",
        "observed_role_counts": role_counts,
        "required_probe_roles": ["cover", "content", "metric"],
        "recommended_full_deck_roles": [
            "cover",
            "agenda",
            "central_thesis",
            "method_stack",
            "metric_ledger",
            "evidence_wall",
            "figure_focus",
            "table_focus",
            "risk_map",
            "closing",
        ],
        "role_to_layouts": {
            role: [item["layout_id"] for item in layouts if item.get("role") == role]
            for role in sorted({item.get("role", "unknown") for item in layouts})
        },
    }


def _validator_rules(scorecard: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": "validator_rules.v0",
        "min_editability_score": 90.0,
        "max_raster_area_ratio": 0.08,
        "min_typography_score": 60.0,
        "min_layout_geometry_score": 50.0,
        "min_visual_design_proxy_score": 65.0,
        "min_evidence_grounding_proxy_score": 55.0,
        "full_deck_content_min_score": 70.0,
        "required_probe_roles": ["cover", "content", "metric"],
        "min_layout_signature_count": 6,
        "body_min_pt": 14,
        "caption_min_pt": 9,
        "title_min_pt": 28,
        "max_text_fill_ratio": 0.88,
        "human_feedback_required_before_promotion": True,
        "source_scorecard": {
            "overall": scorecard.get("overall", {}).get("score"),
            "human_preference_status": scorecard.get("dimensions", {}).get("human_preference", {}).get("status"),
        },
    }


def _render_design_spec(package: Dict[str, Any], scorecard: Dict[str, Any], gate: Dict[str, Any]) -> str:
    brand = package["brand"]
    spec = package["spec_lock"]
    roles = package["page_role_roster"]
    return "\n".join(
        [
            "# PPT Master Inspired Seed Template v0",
            "",
            "## Intent",
            "",
            "Create a native-editable, editorial data-reporting seed template for paper decks. This is a template contract extracted from the 07 visual probe, not a copied slide template.",
            "",
            "## Visual Language",
            "",
            f"- Brand language: {brand.get('visual_language')}",
            f"- Tone: {', '.join(brand.get('tone', []))}",
            f"- Palette: {json.dumps(brand.get('palette', {}), ensure_ascii=False)}",
            f"- Fonts: {', '.join(brand.get('font_families', []))}",
            "",
            "## Narrative Strategy",
            "",
            "- Start with a strong cover or central thesis.",
            "- Alternate dense evidence pages with breathing explanatory pages.",
            "- Use metric ledgers and evidence notes as proof objects instead of generic bullets.",
            "- Treat full content coverage as a separate gate from visual-probe quality.",
            "",
            "## Page Roles",
            "",
            f"- Observed probe roles: {json.dumps(roles.get('observed_role_counts', {}), ensure_ascii=False)}",
            f"- Recommended full deck roles: {', '.join(roles.get('recommended_full_deck_roles', []))}",
            "",
            "## Spec Lock",
            "",
            f"- Canvas: {json.dumps(spec.get('canvas', {}), ensure_ascii=False)}",
            f"- Typography: {json.dumps(spec.get('typography', {}), ensure_ascii=False)}",
            f"- Forbidden patterns: {', '.join(spec.get('forbidden_patterns', []))}",
            "",
            "## Template Gate",
            "",
            f"- Status: {gate.get('status')}",
            f"- Recommendation: {gate.get('recommendation')}",
            "",
        ]
    )


def _typography_ranges(deck_ir: Dict[str, Any]) -> Dict[str, Any]:
    sizes = []
    for slide in deck_ir.get("slides", []) or []:
        for obj in slide.get("objects", []) or []:
            sizes.extend(float(size) for size in obj.get("font", {}).get("sizes_pt", []) or [])
    if not sizes:
        return {"title_pt": [34, 56], "claim_pt": [22, 32], "body_pt": [14, 20], "caption_pt": [9, 12]}
    sizes = sorted(sizes)
    return {
        "title_pt": [max(28, int(_percentile(sizes, 0.80))), max(36, int(max(sizes)))],
        "claim_pt": [max(20, int(_percentile(sizes, 0.60))), max(28, int(_percentile(sizes, 0.85)))],
        "body_pt": [max(12, int(_percentile(sizes, 0.25))), max(18, int(_percentile(sizes, 0.65)))],
        "caption_pt": [9, max(10, int(_percentile(sizes, 0.25)))],
    }


def _page_rhythm(deck_ir: Dict[str, Any]) -> Dict[str, str]:
    rhythm = {}
    for slide in deck_ir.get("slides", []) or []:
        occ = float(slide.get("layout", {}).get("occupancy", 0.0) or 0.0)
        role = slide.get("role_guess", "unknown")
        if role == "cover":
            value = "anchor"
        elif occ >= 0.52 or role == "metric":
            value = "dense"
        elif occ <= 0.30:
            value = "breathing"
        else:
            value = "balanced"
        rhythm[f"slide_{int(slide.get('slide_index', 0)):02d}"] = value
    return rhythm


def _layout_id(role: str, slide_index: int, signature: str) -> str:
    token = "".join(char if char.isalnum() else "_" for char in f"{role}_{slide_index:02d}").strip("_")
    return token or f"layout_{slide_index:02d}"


def _content_type_for_role(role: str) -> str:
    return {
        "cover": "deck thesis and source identity",
        "metric": "metrics, evaluation scores, or compact comparisons",
        "evidence": "figure, table, or sourced evidence",
        "content": "claim, explanation, and supporting notes",
        "closing": "summary and next-step takeaway",
    }.get(role, "general slide content")


def _max_text_budget(role: str) -> int:
    return {"cover": 70, "metric": 90, "evidence": 110, "content": 125, "closing": 80}.get(role, 100)


def _typography_floor(role: str) -> int:
    return {"cover": 18, "metric": 12, "evidence": 11, "content": 13, "closing": 14}.get(role, 12)


def _proof_slot(objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    structured = [obj for obj in objects if obj.get("kind") in {"picture", "table", "chart"}]
    text_blocks = [obj for obj in objects if obj.get("kind") == "text"]
    if structured:
        primary = max(structured, key=lambda item: item.get("bbox", {}).get("area", 0.0))
        return {"kind": primary.get("kind"), "bbox": primary.get("bbox", {})}
    if text_blocks:
        primary = max(text_blocks, key=lambda item: item.get("bbox", {}).get("area", 0.0))
        return {"kind": "native_text_evidence", "bbox": primary.get("bbox", {})}
    return {"kind": "none", "bbox": {}}


def _density_band(value: Any) -> str:
    occ = float(value or 0.0)
    if occ < 0.28:
        return "breathing"
    if occ > 0.56:
        return "dense"
    return "balanced"


def _repair_affordance(role: str) -> str:
    if role == "metric":
        return "swap metric card density or split ledger before shrinking type"
    if role == "cover":
        return "adjust hierarchy and subtitle length before moving anchor objects"
    return "tighten copy and proof-object labels before macro-layout changes"


def _primitive(name: str, purpose: str, observed_count: int) -> Dict[str, Any]:
    return {
        "primitive_id": name,
        "purpose": purpose,
        "native_pptx_required": True,
        "observed_count": int(observed_count),
    }


def _dimension_score(scorecard: Dict[str, Any], name: str) -> Any:
    return scorecard.get("dimensions", {}).get(name, {}).get("score")


def _first_dark(palette: List[str]) -> Optional[str]:
    for color in palette:
        if _luma(color) < 95:
            return color
    return None


def _first_light(palette: List[str]) -> Optional[str]:
    for color in palette:
        if _luma(color) >= 190:
            return color
    return None


def _first_accent(palette: List[str]) -> Optional[str]:
    for color in palette:
        luma = _luma(color)
        if 80 <= luma <= 210:
            return color
    return None


def _luma(color: str) -> float:
    text = str(color or "").lstrip("#")
    if len(text) != 6:
        return 128.0
    try:
        r = int(text[0:2], 16)
        g = int(text[2:4], 16)
        b = int(text[4:6], 16)
    except ValueError:
        return 128.0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    index = max(0, min(len(values) - 1, int(round((len(values) - 1) * pct))))
    return values[index]


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build a seed-template package from DeckIR and scorecard.")
    parser.add_argument("--deck-ir", required=True, help="deck_ir.json path.")
    parser.add_argument("--scorecard", required=True, help="universal_scorecard.v0.json path.")
    parser.add_argument("--output-dir", required=True, help="Output seed_template_package directory.")
    parser.add_argument("--template-id", default="ppt_master_inspired_seed_v0")
    parser.add_argument("--source-label", default="07_ppt_master_inspired_native")
    args = parser.parse_args(argv)
    paths = write_seed_template_package(
        Path(args.deck_ir),
        Path(args.scorecard),
        Path(args.output_dir),
        template_id=args.template_id,
        source_label=args.source_label,
    )
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
