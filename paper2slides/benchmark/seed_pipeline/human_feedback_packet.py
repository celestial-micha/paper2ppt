"""Build pending human-feedback packets for seed-template promotion."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..human_feedback import (
    DEFAULT_HUMAN_FEEDBACK_BENCHMARK,
    badcase_ids,
    load_human_feedback_benchmark,
    summarize_human_feedback_benchmark,
)
from .strategist import load_seed_template_package


def build_human_feedback_packet(
    visual_probe_spec: Dict[str, Any],
    visual_probe_gate: Dict[str, Any],
    package: Dict[str, Any],
    *,
    scorecard: Optional[Dict[str, Any]] = None,
    registry: Optional[Dict[str, Any]] = None,
    label: str = "",
) -> Dict[str, Any]:
    """Build a review packet without pretending human feedback exists yet."""
    scorecard = scorecard or {}
    registry = registry or {}
    template_gate = package.get("template_gate", {}) or {}
    brand = package.get("brand", {}) or {}
    spec_lock = package.get("spec_lock", {}) or {}
    component_primitives = package.get("component_primitives", {}) or {}
    layout_registry = package.get("layout_registry", {}) or {}

    gate_warnings = _warning_ids(template_gate) + list(visual_probe_gate.get("warnings", []) or [])
    promotion_blockers = _promotion_blockers(visual_probe_gate, template_gate, scorecard)
    rule_candidates = _rule_candidates(gate_warnings, promotion_blockers, spec_lock)

    return {
        "schema_version": "human_feedback_packet.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "label": label or package.get("provenance", {}).get("template_id", ""),
        "feedback_status": "pending_human_review",
        "subject": {
            "template_id": package.get("provenance", {}).get("template_id", ""),
            "paper_title": visual_probe_spec.get("paper_title", ""),
            "visual_probe_status": visual_probe_gate.get("status", ""),
            "template_gate_status": template_gate.get("status", ""),
            "scorecard_overall": scorecard.get("overall", {}).get("score"),
        },
        "review_prompts": [
            "Which suggested traits should be accepted as part of the style contract?",
            "Which traits should be rejected or treated as local one-off choices?",
            "Which warnings block default promotion?",
            "Which rule candidates should become automatic checks, human-gated checks, or notes only?",
        ],
        "suggested_accepted_style_traits": _suggested_accepted_traits(
            brand,
            spec_lock,
            component_primitives,
            layout_registry,
            scorecard,
        ),
        "suggested_rejected_style_traits": _suggested_rejected_traits(spec_lock),
        "suggested_borrowable_traits": _suggested_borrowable_traits(
            visual_probe_spec,
            component_primitives,
            layout_registry,
        ),
        "promotion_blockers": promotion_blockers,
        "badcase_to_rule_candidates": rule_candidates,
        "human_review_slots": {
            "accepted_style_traits": [],
            "rejected_style_traits": [],
            "borrowable_traits": [],
            "visual_examples_to_keep": [],
            "visual_examples_to_avoid": [],
            "notes": "",
        },
        "registry_context": _registry_context(registry),
        "source_gate_context": {
            "template_gate_warnings": _warning_ids(template_gate),
            "visual_probe_warnings": list(visual_probe_gate.get("warnings", []) or []),
            "visual_probe_checks": visual_probe_gate.get("checks", []),
        },
    }


def write_human_feedback_packet(
    visual_probe_spec_path: Path,
    visual_probe_gate_path: Path,
    package_dir: Path,
    output_dir: Path,
    *,
    scorecard_path: Optional[Path] = None,
    registry_path: Optional[Path] = DEFAULT_HUMAN_FEEDBACK_BENCHMARK,
    label: str = "",
) -> Dict[str, str]:
    """Write a JSON feedback packet and a compact review brief."""
    spec = _read_json(visual_probe_spec_path)
    gate = _read_json(visual_probe_gate_path)
    package = load_seed_template_package(package_dir)
    scorecard = _read_json(scorecard_path) if scorecard_path else None
    registry = _read_optional_registry(registry_path)
    packet = build_human_feedback_packet(
        spec,
        gate,
        package,
        scorecard=scorecard,
        registry=registry,
        label=label,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "human_feedback_packet": str(output_dir / "human_feedback_packet.json"),
        "human_feedback_brief": str(output_dir / "human_feedback_packet.md"),
    }
    _write_json(output_dir / "human_feedback_packet.json", packet)
    (output_dir / "human_feedback_packet.md").write_text(_render_feedback_brief(packet), encoding="utf-8")
    return paths


def _suggested_accepted_traits(
    brand: Dict[str, Any],
    spec_lock: Dict[str, Any],
    component_primitives: Dict[str, Any],
    layout_registry: Dict[str, Any],
    scorecard: Dict[str, Any],
) -> List[Dict[str, Any]]:
    dims = scorecard.get("dimensions", {}) or {}
    primitives = component_primitives.get("primitives", []) or []
    native_primitives = [
        item.get("primitive_id", "")
        for item in primitives
        if item.get("native_pptx_required", True) and item.get("primitive_id")
    ]
    layouts = layout_registry.get("layouts", []) or []
    return [
        {
            "id": "editorial_data_reporting_language",
            "source": "seed_brand",
            "evidence": brand.get("visual_language", ""),
            "review_status": "suggested",
        },
        {
            "id": "native_editable_primitives",
            "source": "component_primitives",
            "evidence": native_primitives,
            "review_status": "suggested",
        },
        {
            "id": "clear_type_hierarchy",
            "source": "universal_scorecard",
            "evidence": dims.get("typography", {}).get("score"),
            "review_status": "suggested",
        },
        {
            "id": "role_based_layout_registry",
            "source": "layout_registry",
            "evidence": {
                "layout_count": len(layouts),
                "roles": sorted({layout.get("role", "") for layout in layouts if layout.get("role")}),
            },
            "review_status": "suggested",
        },
        {
            "id": "restrained_palette_with_single_accent",
            "source": "spec_lock",
            "evidence": spec_lock.get("palette", {}),
            "review_status": "suggested",
        },
    ]


def _suggested_rejected_traits(spec_lock: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "id": _slug(item),
            "source": "spec_lock.forbidden_patterns",
            "evidence": item,
            "review_status": "suggested",
        }
        for item in spec_lock.get("forbidden_patterns", []) or []
    ]


def _suggested_borrowable_traits(
    visual_probe_spec: Dict[str, Any],
    component_primitives: Dict[str, Any],
    layout_registry: Dict[str, Any],
) -> List[Dict[str, Any]]:
    slides = visual_probe_spec.get("slides", []) or []
    layout_ids = [slide.get("layout_candidate", "") for slide in slides if slide.get("layout_candidate")]
    primitive_ids = [
        item.get("primitive_id", "")
        for item in component_primitives.get("primitives", []) or []
        if item.get("primitive_id")
    ]
    return [
        {
            "id": "probe_role_arc",
            "source": "visual_probe_spec",
            "evidence": [slide.get("role", "") for slide in slides],
            "review_status": "suggested",
        },
        {
            "id": "layout_candidates",
            "source": "visual_probe_spec",
            "evidence": layout_ids,
            "review_status": "suggested",
        },
        {
            "id": "native_component_primitives",
            "source": "component_primitives",
            "evidence": primitive_ids,
            "review_status": "suggested",
        },
        {
            "id": "layout_repair_affordances",
            "source": "layout_registry",
            "evidence": [
                {
                    "layout_id": layout.get("layout_id", ""),
                    "repair_affordance": layout.get("repair_affordance", ""),
                }
                for layout in layout_registry.get("layouts", []) or []
            ],
            "review_status": "suggested",
        },
    ]


def _promotion_blockers(
    visual_probe_gate: Dict[str, Any],
    template_gate: Dict[str, Any],
    scorecard: Dict[str, Any],
) -> List[Dict[str, Any]]:
    blockers: List[Dict[str, Any]] = []
    if visual_probe_gate.get("status") == "fail":
        blockers.append(_blocker("visual_probe_gate_failed", "Visual probe gate failed."))
    if template_gate.get("status") == "fail":
        blockers.append(_blocker("template_gate_failed", "Seed template package gate failed."))
    if template_gate.get("status") == "pass_with_warnings":
        blockers.append(_blocker("template_gate_warnings", "Template package still has warnings."))
    dims = scorecard.get("dimensions", {}) or {}
    human_status = dims.get("human_preference", {}).get("status")
    if human_status in {None, "pending_human_feedback"}:
        blockers.append(_blocker("human_preference_pending", "Human preference has not been reviewed."))
    content_score = dims.get("content_fidelity", {}).get("score")
    if content_score is not None and content_score < 70:
        blockers.append(_blocker("content_fidelity_probe_only", "Content coverage is probe-level, not full-deck proof."))
    return blockers


def _rule_candidates(
    warnings: List[str],
    blockers: List[Dict[str, Any]],
    spec_lock: Dict[str, Any],
) -> List[Dict[str, Any]]:
    candidates = [
        _candidate(
            warning,
            dimension="human_acceptance",
            repair_mode="human_gated",
            source="gate_warning",
        )
        for warning in warnings
    ]
    candidates.extend(
        _candidate(
            blocker.get("id", ""),
            dimension="human_acceptance",
            repair_mode="human_gated",
            source="promotion_blocker",
        )
        for blocker in blockers
    )
    for item in spec_lock.get("forbidden_patterns", []) or []:
        candidates.append(
            _candidate(
                _slug(item),
                dimension="style",
                repair_mode="detect_only",
                source="forbidden_pattern",
                description=item,
            )
        )
    return _dedupe_candidates(candidates)


def _candidate(
    rule_id: str,
    *,
    dimension: str,
    repair_mode: str,
    source: str,
    description: str = "",
) -> Dict[str, Any]:
    return {
        "id": rule_id,
        "dimension": dimension,
        "severity": "medium",
        "scope": "human_feedback",
        "repair_mode": repair_mode,
        "confidence": 0.55,
        "human_outcome": "pending_review",
        "source": source,
        "description": description,
        "promotion_target": "template_gate_v1",
    }


def _dedupe_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for item in candidates:
        key = item.get("id", "")
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _registry_context(registry: Dict[str, Any]) -> Dict[str, Any]:
    if not registry:
        return {}
    summary = summarize_human_feedback_benchmark(registry)
    return {
        "benchmark_track": summary.get("benchmark_track", ""),
        "accepted_reference": summary.get("accepted_reference", ""),
        "badcase_count": summary.get("badcase_count", 0),
        "registered_badcase_ids": badcase_ids(registry)[:24],
        "current_phase_policy": summary.get("current_phase_policy", ""),
    }


def _warning_ids(gate: Dict[str, Any]) -> List[str]:
    warnings = gate.get("warnings", []) or []
    result = []
    for item in warnings:
        if isinstance(item, dict):
            result.append(str(item.get("id", "")))
        else:
            result.append(str(item))
    return [item for item in result if item]


def _blocker(blocker_id: str, message: str) -> Dict[str, Any]:
    return {
        "id": blocker_id,
        "severity": "blocking_before_default_promotion",
        "message": message,
        "resolution": "human review or stronger gate evidence required",
    }


def _read_optional_registry(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    path = Path(path)
    if not path.exists():
        return None
    return load_human_feedback_benchmark(path)


def _read_json(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_feedback_brief(packet: Dict[str, Any]) -> str:
    subject = packet.get("subject", {}) or {}
    blockers = packet.get("promotion_blockers", []) or []
    candidates = packet.get("badcase_to_rule_candidates", []) or []
    accepted = packet.get("suggested_accepted_style_traits", []) or []
    rejected = packet.get("suggested_rejected_style_traits", []) or []
    borrowable = packet.get("suggested_borrowable_traits", []) or []
    lines = [
        "# Human Feedback Packet",
        "",
        f"- Status: {packet.get('feedback_status', '')}",
        f"- Template: {subject.get('template_id', '')}",
        f"- Paper: {subject.get('paper_title', '')}",
        f"- Visual probe gate: {subject.get('visual_probe_status', '')}",
        f"- Template gate: {subject.get('template_gate_status', '')}",
        "",
        "## Suggested Accepted Traits",
        "",
        *[f"- {item.get('id', '')}" for item in accepted],
        "",
        "## Suggested Rejected Traits",
        "",
        *[f"- {item.get('id', '')}" for item in rejected],
        "",
        "## Suggested Borrowable Traits",
        "",
        *[f"- {item.get('id', '')}" for item in borrowable],
        "",
        "## Promotion Blockers",
        "",
        *[f"- {item.get('id', '')}: {item.get('message', '')}" for item in blockers],
        "",
        "## Rule Candidates",
        "",
        *[f"- {item.get('id', '')} ({item.get('repair_mode', '')})" for item in candidates],
        "",
    ]
    return "\n".join(lines)


def _slug(text: Any) -> str:
    value = str(text or "").strip().lower()
    chars = []
    previous_underscore = False
    for char in value:
        if char.isalnum():
            chars.append(char)
            previous_underscore = False
        elif not previous_underscore:
            chars.append("_")
            previous_underscore = True
    return "".join(chars).strip("_")[:80] or "unnamed_trait"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a pending human-feedback packet for a seed visual probe.")
    parser.add_argument("--spec", required=True, help="Path to visual_probe_spec.json")
    parser.add_argument("--gate", required=True, help="Path to visual_probe_gate.json")
    parser.add_argument("--package-dir", required=True, help="Path to seed_template_package directory")
    parser.add_argument("--output-dir", required=True, help="Directory for human_feedback_packet.json")
    parser.add_argument("--scorecard", help="Optional universal_scorecard.v0.json for the seed deck")
    parser.add_argument("--registry", default=str(DEFAULT_HUMAN_FEEDBACK_BENCHMARK), help="Optional existing human-feedback registry")
    parser.add_argument("--label", default="", help="Optional packet label")
    args = parser.parse_args(argv)

    paths = write_human_feedback_packet(
        Path(args.spec),
        Path(args.gate),
        Path(args.package_dir),
        Path(args.output_dir),
        scorecard_path=Path(args.scorecard) if args.scorecard else None,
        registry_path=Path(args.registry) if args.registry else None,
        label=args.label,
    )
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
