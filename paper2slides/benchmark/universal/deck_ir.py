"""DeckIR and universal scorecard v0 schema helpers.

DeckIR is intentionally metadata-first: it normalizes any editable PPTX into a
small JSON surface that later benchmark rules can consume without knowing which
generator produced the deck.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DECK_IR_SCHEMA_VERSION = "deck_ir.v1"
UNIVERSAL_SCORECARD_SCHEMA_VERSION = "universal_scorecard.v0"

UNIVERSAL_DIMENSIONS = [
    "editability",
    "content_fidelity",
    "narrative_structure",
    "evidence_grounding",
    "layout_geometry",
    "typography",
    "visual_design",
    "repairability",
    "human_preference",
]


def deck_ir_schema() -> Dict[str, Any]:
    """Return a compact machine-readable schema description."""
    return {
        "schema_version": DECK_IR_SCHEMA_VERSION,
        "required_top_level": ["schema_version", "source", "deck", "slides", "summary"],
        "source": {
            "path": "absolute or workspace-relative source artifact path",
            "generator": "paper2slides | ppt-master | human | other | unknown",
            "artifact_kind": "pptx",
            "native_editability_expected": True,
            "label": "human readable deck label",
        },
        "deck": {
            "slide_count": "integer",
            "width_in": "float",
            "height_in": "float",
            "theme_signals": {
                "palette": ["#RRGGBB"],
                "font_families": ["font family names observed in runs"],
                "dominant_backgrounds": ["#RRGGBB or object-derived background colors"],
            },
        },
        "slide": {
            "slide_index": "1-based integer",
            "role_guess": "cover | agenda | section | content | evidence | metric | closing | unknown",
            "objects": ["normalized native object records"],
            "text": {
                "title_candidates": ["short high-position or large-font text blocks"],
                "body_blocks": ["native body text snippets"],
                "caption_candidates": ["caption/source-like snippets"],
            },
            "layout": {
                "occupancy": "sum of meaningful object areas divided by canvas area",
                "alignment_groups": ["shared x/y edge groups inferred from object geometry"],
                "safe_area_violations": ["object ids outside default safe area"],
            },
            "editability": {
                "text_chars_native": "integer",
                "raster_area_ratio": "picture area divided by slide area",
                "native_shape_count": "integer",
                "picture_count": "integer",
                "table_count": "integer",
                "chart_count": "integer",
            },
        },
    }


def universal_scorecard_schema() -> Dict[str, Any]:
    """Return the first version of the universal scorecard schema."""
    return {
        "schema_version": UNIVERSAL_SCORECARD_SCHEMA_VERSION,
        "required_top_level": [
            "schema_version",
            "created_at",
            "source",
            "score_model",
            "content_alignment",
            "dimension_order",
            "dimensions",
            "overall",
            "findings",
            "calibration_notes",
        ],
        "score_model": {
            "scale": "0..100; null means not automatically scored in v0",
            "principle": "metadata-first, source-neutral PPT benchmark",
            "sources": [
                "DeckIR geometry/editability/text metadata",
                "optional nonvisual_audit summary",
                "optional repair_log curve",
                "optional paper checkpoint alignment in later versions",
                "human feedback for visual preference calibration",
            ],
        },
        "content_alignment": {
            "schema_version": "checkpoint_deck_alignment.v0",
            "coverage": {
                "key_term_coverage": "0..1",
                "slide_title_coverage": "0..1",
                "section_coverage": "0..1",
                "figure_ref_coverage": "0..1",
                "table_ref_coverage": "0..1",
                "metric_ref_coverage": "0..1",
                "evidence_ref_coverage": "0..1",
            },
            "status": "optional; present when checkpoints are supplied",
        },
        "dimensions": {
            "editability": "native text/shape/table/chart availability and low raster-page dependence",
            "content_fidelity": "checkpoint-to-deck coverage; v0 records proxy signals and waits for source alignment",
            "narrative_structure": "role roster, cover/closing, section and agenda signals, rhythm diversity",
            "evidence_grounding": "figure/table/metric/source/caption signals and traceability hooks",
            "layout_geometry": "safe area, occupancy, overlap/bounds findings from nonvisual audit",
            "typography": "font floors, text capacity, title/body hierarchy findings",
            "visual_design": "palette/font consistency, rhythm diversity, focus/density proxies; human calibrated",
            "repairability": "repair log improvement, plateau, and new finding risk",
            "human_preference": "accepted/rejected/borrowable traits; always human-gated in v0",
        },
        "dimension_payload": {
            "score": "number or null",
            "confidence": "0..1",
            "status": "auto | partial | needs_checkpoint | human_calibrated | pending_human_feedback | not_applicable",
            "signals": "machine-readable evidence values",
            "notes": "short human-readable interpretation",
        },
    }


def score_deck_ir_v0(
    deck_ir: Dict[str, Any],
    nonvisual_audit: Optional[Dict[str, Any]] = None,
    repair_log: Optional[Dict[str, Any]] = None,
    content_alignment: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a first-pass universal scorecard from DeckIR and optional audits."""
    summary = deck_ir.get("summary", {})
    editability = _score_editability(summary)
    layout = _score_layout_geometry(deck_ir, nonvisual_audit)
    typography = _score_typography(nonvisual_audit)
    narrative = _score_narrative(deck_ir)
    evidence = _score_evidence_grounding(deck_ir, content_alignment)
    visual = _score_visual_design(deck_ir, nonvisual_audit)
    repairability = _score_repairability(repair_log)
    content = _score_content_fidelity(deck_ir, content_alignment)
    human = _score_human_preference()

    dimensions = {
        "editability": editability,
        "content_fidelity": content,
        "narrative_structure": narrative,
        "evidence_grounding": evidence,
        "layout_geometry": layout,
        "typography": typography,
        "visual_design": visual,
        "repairability": repairability,
        "human_preference": human,
    }
    auto_scores = [
        float(payload["score"])
        for name, payload in dimensions.items()
        if payload.get("score") is not None and name != "human_preference"
    ]
    overall = {
        "score": round(sum(auto_scores) / len(auto_scores), 1) if auto_scores else None,
        "scored_dimension_count": len(auto_scores),
        "unscored_dimensions": [name for name, payload in dimensions.items() if payload.get("score") is None],
        "interpretation": "v0 overall averages scored machine dimensions only; visual and human dimensions remain calibration-aware.",
    }
    return {
        "schema_version": UNIVERSAL_SCORECARD_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": deck_ir.get("source", {}),
        "deck_summary": {
            "slide_count": deck_ir.get("deck", {}).get("slide_count", 0),
            "width_in": deck_ir.get("deck", {}).get("width_in"),
            "height_in": deck_ir.get("deck", {}).get("height_in"),
            "role_counts": summary.get("role_counts", {}),
            "native_text_chars": summary.get("native_text_chars", 0),
            "raster_area_ratio": summary.get("raster_area_ratio", 0.0),
        },
        "content_alignment": content_alignment or {},
        "score_model": {
            "scale": "0..100",
            "score_source": "DeckIR v1 + optional nonvisual audit + optional repair log",
            "warning": "v0 is intentionally conservative; visual preference requires human calibration before promotion.",
        },
        "dimension_order": UNIVERSAL_DIMENSIONS,
        "dimensions": dimensions,
        "overall": overall,
        "findings": _scorecard_findings(dimensions),
        "calibration_notes": _calibration_notes(nonvisual_audit),
    }


def write_schema_bundle(output_dir: Path) -> Dict[str, str]:
    """Write DeckIR and scorecard schema files into an output directory."""
    import json

    output_dir.mkdir(parents=True, exist_ok=True)
    deck_path = output_dir / "deck_ir_schema.v1.json"
    scorecard_path = output_dir / "universal_scorecard_schema.v0.json"
    deck_path.write_text(json.dumps(deck_ir_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    scorecard_path.write_text(json.dumps(universal_scorecard_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"deck_ir_schema": str(deck_path), "universal_scorecard_schema": str(scorecard_path)}


def _score_editability(summary: Dict[str, Any]) -> Dict[str, Any]:
    raster_ratio = float(summary.get("raster_area_ratio", 0.0) or 0.0)
    native_text_chars = int(summary.get("native_text_chars", 0) or 0)
    native_shape_count = int(summary.get("native_shape_count", 0) or 0)
    picture_count = int(summary.get("picture_count", 0) or 0)
    total_objects = max(1, int(summary.get("object_count", 0) or 0))
    native_object_ratio = min(1.0, (native_shape_count + int(summary.get("table_count", 0) or 0) + int(summary.get("chart_count", 0) or 0)) / total_objects)
    text_signal = 1.0 if native_text_chars >= 1200 else native_text_chars / 1200.0
    score = 100.0
    score -= min(55.0, raster_ratio * 100.0)
    score += min(15.0, text_signal * 15.0)
    score += min(10.0, native_object_ratio * 10.0)
    if picture_count and native_text_chars < 250:
        score -= 20.0
    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "confidence": 0.88,
        "status": "auto",
        "signals": {
            "native_text_chars": native_text_chars,
            "native_shape_count": native_shape_count,
            "picture_count": picture_count,
            "native_object_ratio": round(native_object_ratio, 3),
            "raster_area_ratio": round(raster_ratio, 3),
        },
        "notes": "Rewards native text/shapes and penalizes decks that depend on raster page imagery.",
    }


def _score_content_fidelity(deck_ir: Dict[str, Any], alignment: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    summary = deck_ir.get("summary", {})
    if alignment:
        coverage = alignment.get("coverage", {})
        key_term = float(coverage.get("key_term_coverage", 0.0) or 0.0)
        title = float(coverage.get("slide_title_coverage", 0.0) or 0.0)
        section = float(coverage.get("section_coverage", 0.0) or 0.0)
        score = 20.0 + key_term * 32.0 + title * 30.0 + section * 18.0
        return {
            "score": round(max(0.0, min(100.0, score)), 1),
            "confidence": 0.68,
            "status": "partial_checkpoint_alignment",
            "signals": {
                "checkpoint_alignment_available": True,
                "key_term_coverage": round(key_term, 3),
                "slide_title_coverage": round(title, 3),
                "section_coverage": round(section, 3),
                "native_text_words": summary.get("native_text_words", 0),
            },
            "notes": "Uses checkpoint-derived keyword, title, and section coverage. Claim-level semantic matching is still future work.",
        }
    words = int(summary.get("native_text_words", 0) or 0)
    role_counts = summary.get("role_counts", {})
    proxy_score = 42.0
    if words >= 800:
        proxy_score += 18.0
    elif words >= 300:
        proxy_score += 10.0
    if role_counts.get("evidence", 0) or summary.get("table_count", 0) or summary.get("picture_count", 0):
        proxy_score += 12.0
    if role_counts.get("metric", 0):
        proxy_score += 6.0
    return {
        "score": round(min(72.0, proxy_score), 1),
        "confidence": 0.34,
        "status": "needs_checkpoint",
        "signals": {
            "native_text_words": words,
            "evidence_role_slides": role_counts.get("evidence", 0),
            "metric_role_slides": role_counts.get("metric", 0),
            "checkpoint_alignment_available": False,
        },
        "notes": "v0 uses only coverage proxies. A real content score needs paper checkpoint-to-deck matching.",
    }


def _score_narrative(deck_ir: Dict[str, Any]) -> Dict[str, Any]:
    slides = deck_ir.get("slides", []) or []
    role_counts = Counter(slide.get("role_guess", "unknown") for slide in slides)
    roles_present = {role for role, count in role_counts.items() if count}
    target_roles = {"cover", "agenda", "content", "evidence", "metric", "closing"}
    role_coverage = len(roles_present & target_roles) / len(target_roles)
    unknown_ratio = role_counts.get("unknown", 0) / max(1, len(slides))
    repeated_role_ratio = max(role_counts.values() or [0]) / max(1, len(slides))
    score = 35.0 + role_coverage * 45.0
    score -= unknown_ratio * 20.0
    if repeated_role_ratio > 0.65:
        score -= (repeated_role_ratio - 0.65) * 35.0
    if slides and slides[0].get("role_guess") == "cover":
        score += 8.0
    if slides and slides[-1].get("role_guess") == "closing":
        score += 7.0
    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "confidence": 0.62,
        "status": "partial",
        "signals": {
            "role_counts": dict(role_counts),
            "role_coverage": round(role_coverage, 3),
            "unknown_ratio": round(unknown_ratio, 3),
            "repeated_role_ratio": round(repeated_role_ratio, 3),
        },
        "notes": "Uses slide role roster and rhythm diversity; semantic story quality remains human/checkpoint gated.",
    }


def _score_evidence_grounding(deck_ir: Dict[str, Any], alignment: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    summary = deck_ir.get("summary", {})
    slide_count = max(1, int(deck_ir.get("deck", {}).get("slide_count", 0) or 0))
    evidence_objects = int(summary.get("picture_count", 0) or 0) + int(summary.get("table_count", 0) or 0) + int(summary.get("metric_like_text_count", 0) or 0)
    caption_count = int(summary.get("caption_candidate_count", 0) or 0)
    evidence_density = evidence_objects / slide_count
    score = 38.0 + min(32.0, evidence_density * 18.0) + min(18.0, caption_count * 2.0)
    if summary.get("source_like_text_count", 0):
        score += 8.0
    signals = {
        "picture_count": summary.get("picture_count", 0),
        "table_count": summary.get("table_count", 0),
        "metric_like_text_count": summary.get("metric_like_text_count", 0),
        "caption_candidate_count": caption_count,
        "source_like_text_count": summary.get("source_like_text_count", 0),
        "evidence_objects_per_slide": round(evidence_density, 3),
    }
    status = "partial"
    confidence = 0.48
    if alignment:
        coverage = alignment.get("coverage", {})
        figure_cov = float(coverage.get("figure_ref_coverage", 0.0) or 0.0)
        table_cov = float(coverage.get("table_ref_coverage", 0.0) or 0.0)
        metric_cov = float(coverage.get("metric_ref_coverage", 0.0) or 0.0)
        evidence_cov = float(coverage.get("evidence_ref_coverage", 0.0) or 0.0)
        score = max(score, 25.0 + evidence_cov * 35.0 + figure_cov * 14.0 + table_cov * 14.0 + metric_cov * 12.0)
        signals.update(
            {
                "checkpoint_alignment_available": True,
                "figure_ref_coverage": round(figure_cov, 3),
                "table_ref_coverage": round(table_cov, 3),
                "metric_ref_coverage": round(metric_cov, 3),
                "evidence_ref_coverage": round(evidence_cov, 3),
            }
        )
        status = "partial_checkpoint_alignment"
        confidence = 0.62
    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "confidence": confidence,
        "status": status,
        "signals": signals,
        "notes": "Counts proof-object and caption/source signals, with checkpoint evidence reference coverage when available.",
    }


def _score_layout_geometry(deck_ir: Dict[str, Any], audit: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    slide_count = max(1, int(deck_ir.get("deck", {}).get("slide_count", 0) or 0))
    safe_violations = sum(len(slide.get("layout", {}).get("safe_area_violations", []) or []) for slide in deck_ir.get("slides", []) or [])
    occupancy_values = [float(slide.get("layout", {}).get("occupancy", 0.0) or 0.0) for slide in deck_ir.get("slides", []) or []]
    avg_occupancy = sum(occupancy_values) / max(1, len(occupancy_values))
    score = 82.0
    score -= min(32.0, safe_violations * 3.5)
    if avg_occupancy < 0.18:
        score -= 15.0
    elif avg_occupancy > 0.92:
        score -= 20.0
    summary = (audit or {}).get("summary", {})
    by_dimension = summary.get("by_dimension", {})
    if by_dimension:
        score -= min(45.0, float(by_dimension.get("layout", 0)) * 2.5)
    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "confidence": 0.78 if audit else 0.58,
        "status": "auto" if audit else "partial",
        "signals": {
            "safe_area_violation_count": safe_violations,
            "safe_area_violations_per_slide": round(safe_violations / slide_count, 3),
            "avg_occupancy": round(avg_occupancy, 3),
            "nonvisual_layout_findings": by_dimension.get("layout", None),
        },
        "notes": "Combines DeckIR safe-area/occupancy with nonvisual layout findings when available.",
    }


def _score_typography(audit: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not audit:
        return {
            "score": None,
            "confidence": 0.0,
            "status": "not_applicable",
            "signals": {"nonvisual_audit_available": False},
            "notes": "Typography score requires nonvisual audit or run-level text measurements.",
        }
    summary = audit.get("summary", {})
    by_dimension = summary.get("by_dimension", {})
    by_type = summary.get("by_type", {})
    score = 100.0
    score -= min(64.0, float(by_dimension.get("typography", 0)) * 2.0)
    score -= min(18.0, float(by_type.get("low_font_size", 0)) * 1.5)
    score -= min(12.0, float(by_type.get("estimated_text_overflow", 0)) * 1.2)
    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "confidence": 0.84,
        "status": "auto",
        "signals": {
            "typography_findings": by_dimension.get("typography", 0),
            "low_font_size": by_type.get("low_font_size", 0),
            "below_ideal_font_band": by_type.get("below_ideal_font_band", 0),
            "near_text_capacity": by_type.get("near_text_capacity", 0),
            "estimated_text_overflow": by_type.get("estimated_text_overflow", 0),
            "deck_flags": summary.get("deck_flags", []),
        },
        "notes": "Reuses global nonvisual audit typography/copy-fitting rules.",
    }


def _score_visual_design(deck_ir: Dict[str, Any], audit: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    summary = deck_ir.get("summary", {})
    slide_count = max(1, int(deck_ir.get("deck", {}).get("slide_count", 0) or 0))
    font_count = len(deck_ir.get("deck", {}).get("theme_signals", {}).get("font_families", []) or [])
    palette_count = len(deck_ir.get("deck", {}).get("theme_signals", {}).get("palette", []) or [])
    layout_signatures = set(summary.get("layout_signatures", []) or [])
    role_counts = summary.get("role_counts", {})
    role_diversity = len([role for role, count in role_counts.items() if count]) / max(1, min(7, slide_count))
    rhythm_diversity = len(layout_signatures) / max(1, slide_count)
    score = 45.0 + min(20.0, role_diversity * 20.0) + min(22.0, rhythm_diversity * 35.0)
    if 2 <= font_count <= 6:
        score += 6.0
    elif font_count > 9:
        score -= 8.0
    if 3 <= palette_count <= 12:
        score += 7.0
    elif palette_count > 20:
        score -= 8.0
    by_dimension = (audit or {}).get("summary", {}).get("by_dimension", {})
    score -= min(20.0, float(by_dimension.get("style", 0)) * 1.5)
    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "confidence": 0.42,
        "status": "human_calibrated",
        "signals": {
            "font_family_count": font_count,
            "palette_color_count": palette_count,
            "role_diversity": round(role_diversity, 3),
            "layout_signature_count": len(layout_signatures),
            "rhythm_diversity": round(rhythm_diversity, 3),
            "nonvisual_style_findings": by_dimension.get("style", None),
        },
        "notes": "Heuristic only. Focus, rhythm, polish, and taste must be calibrated with human feedback.",
    }


def _score_repairability(repair_log: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not repair_log:
        return {
            "score": None,
            "confidence": 0.0,
            "status": "not_applicable",
            "signals": {"repair_log_available": False},
            "notes": "No repair log was provided for this deck.",
        }
    iterations = repair_log.get("iterations", []) or []
    if len(iterations) < 2:
        return {
            "score": 50.0,
            "confidence": 0.46,
            "status": "partial",
            "signals": {"iteration_count": len(iterations)},
            "notes": "Single-iteration audit only; repairability is not yet proven.",
        }
    first = _iteration_counts(iterations[0])
    last = _iteration_counts(iterations[-1])
    total_delta = first["total"] - last["total"]
    high_delta = first["high"] - last["high"]
    medium_delta = first["medium"] - last["medium"]
    low_delta = first["low"] - last["low"]
    plateau = total_delta <= 0 or (high_delta <= 1 and medium_delta <= 0)
    score = 48.0 + min(24.0, max(0, total_delta) * 0.8) + min(15.0, max(0, high_delta) * 3.0) + min(10.0, max(0, medium_delta) * 1.8)
    if plateau:
        score -= 14.0
    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "confidence": 0.74,
        "status": "partial",
        "signals": {
            "iteration_count": len(iterations),
            "first": first,
            "last": last,
            "total_delta": total_delta,
            "high_delta": high_delta,
            "medium_delta": medium_delta,
            "low_delta": low_delta,
            "plateau_detected": plateau,
            "stop_reason": iterations[-1].get("stop_reason", ""),
        },
        "notes": "Rewards lower high/medium/total findings across repair iterations; flags plateau.",
    }


def _score_human_preference() -> Dict[str, Any]:
    return {
        "score": None,
        "confidence": 0.0,
        "status": "pending_human_feedback",
        "signals": {
            "human_accept": None,
            "human_reject": None,
            "borrowable_traits": [],
            "visual_traits_to_avoid": [],
        },
        "notes": "Human preference is intentionally not auto-scored in v0.",
    }


def _iteration_counts(iteration: Dict[str, Any]) -> Dict[str, int]:
    summary = iteration.get("audit_summary", {}) or {}
    severity = summary.get("by_severity", {}) or {}
    return {
        "total": int(summary.get("finding_count", 0) or 0),
        "high": int(severity.get("high", 0) or 0),
        "medium": int(severity.get("medium", 0) or 0),
        "low": int(severity.get("low", 0) or 0),
    }


def _scorecard_findings(dimensions: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for name, payload in dimensions.items():
        score = payload.get("score")
        status = payload.get("status")
        if score is not None and float(score) < 45.0:
            findings.append({"dimension": name, "severity": "high", "message": payload.get("notes", "")})
        elif score is not None and float(score) < 65.0:
            findings.append({"dimension": name, "severity": "medium", "message": payload.get("notes", "")})
        elif status in {"needs_checkpoint", "pending_human_feedback"}:
            findings.append({"dimension": name, "severity": "info", "message": payload.get("notes", "")})
    return findings


def _calibration_notes(audit: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    audit_summary = (audit or {}).get("summary", {})
    return {
        "nonvisual_rules_reused": sorted((audit_summary.get("by_type", {}) or {}).keys()),
        "human_calibration_required_for": [
            "visual_focus_missing",
            "rhythm_monotony",
            "underdesigned_layout",
            "overdecorated_layout",
            "style_inconsistency",
            "density_mismatch",
            "human_preference",
        ],
        "v0_limitations": [
            "Content fidelity is not final until paper checkpoint alignment is wired in.",
            "Visual design score is a proxy, not an aesthetic judge.",
            "Human preference is recorded, not inferred.",
        ],
    }


def short_text(text: str, limit: int = 96) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def quantized_layout_signature(slide: Dict[str, Any]) -> str:
    objects = slide.get("objects", []) or []
    meaningful = [obj for obj in objects if obj.get("kind") not in {"background", "decorative"}]
    cols = Counter()
    rows = Counter()
    for obj in meaningful:
        bbox = obj.get("bbox", {})
        cols[int(round(float(bbox.get("x", 0.0)) * 2))] += 1
        rows[int(round(float(bbox.get("y", 0.0)) * 2))] += 1
    top_cols = "-".join(str(key) for key, _ in cols.most_common(4))
    top_rows = "-".join(str(key) for key, _ in rows.most_common(4))
    return f"{slide.get('role_guess', 'unknown')}|x:{top_cols}|y:{top_rows}|n:{len(meaningful)}"


def count_metric_like_text(snippets: Iterable[str]) -> int:
    import re

    count = 0
    for text in snippets:
        if re.search(r"\b\d+(?:\.\d+)?\s*(?:%|x|k|m|b|tokens?|pages?|models?|tasks?)\b", text, flags=re.IGNORECASE):
            count += 1
    return count


def top_items(counter: Counter, limit: int = 12) -> List[Any]:
    return [key for key, _ in counter.most_common(limit)]
