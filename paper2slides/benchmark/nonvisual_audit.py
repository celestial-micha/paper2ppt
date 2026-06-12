"""Non-visual PPTX geometry and text-capacity audit.

This module inspects PPTX metadata directly. It does not render slides, take
screenshots, or call a vision model.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


EMU_PER_INCH = 914400

NONVISUAL_AUDIT_RULES = {
    "title_claim_min_pt": 20.0,
    "support_min_pt": 11.0,
    "card_text_min_pt": 9.5,
    "body_min_pt": 10.5,
    "near_capacity_ratio": 0.82,
    "overflow_ratio": 1.03,
    "sparse_ratio": 0.16,
    "sparse_area_sq_in": 1.15,
    "overlap_ratio": 0.14,
    "container_overlap_ratio": 0.18,
    "low_occupancy_ratio": 0.18,
}


def inspect_pptx_nonvisual(pptx_path: Path, rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Inspect a PPTX without rendering pages."""
    from pptx import Presentation

    active_rules = dict(NONVISUAL_AUDIT_RULES)
    if rules:
        active_rules.update(rules)

    prs = Presentation(pptx_path)
    slide_w = _emu_to_inches(prs.slide_width)
    slide_h = _emu_to_inches(prs.slide_height)
    findings: List[Dict[str, Any]] = []
    slide_summaries: List[Dict[str, Any]] = []

    for slide_index, slide in enumerate(prs.slides, start=1):
        records = [_shape_record(shape, idx, slide_w, slide_h) for idx, shape in enumerate(slide.shapes)]
        for record in records:
            record["role"] = _infer_role(record, slide_h)

        slide_findings: List[Dict[str, Any]] = []
        slide_findings.extend(_text_capacity_findings(slide_index, records, active_rules))
        slide_findings.extend(_overlap_findings(slide_index, records, active_rules))
        slide_findings.extend(_table_findings(slide_index, records))
        slide_findings.extend(_slide_density_findings(slide_index, records, slide_w, slide_h, active_rules))
        findings.extend(slide_findings)
        slide_summaries.append(_slide_summary(slide_index, records, slide_findings, slide_w, slide_h))

    return {
        "schema_version": "pptx_nonvisual_audit.v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "pptx_path": str(pptx_path),
        "review_mode": "non_visual_metadata_only",
        "rendering_used": False,
        "vision_model_used": False,
        "slide_count": len(prs.slides),
        "slide_size": {"width_in": round(slide_w, 3), "height_in": round(slide_h, 3)},
        "rules": active_rules,
        "summary": _summarize_findings(findings),
        "findings": findings,
        "slides": slide_summaries,
        "repair_policy": {
            "preserve_component_composition": True,
            "default_text_repair": "adjust typography, copy allocation, or line breaks before resizing visual components",
            "avoid": [
                "auto-shrinking accepted v5 components only because text density is low",
                "moving cards to a new macro-layout without accepted-reference comparison",
                "rendering every slide for visual judging",
            ],
        },
    }


def _shape_record(shape: Any, index: int, slide_w: float, slide_h: float) -> Dict[str, Any]:
    text = _clean_text(getattr(shape, "text", "") if getattr(shape, "has_text_frame", False) else "")
    table_info = _table_info(shape)
    left = _emu_to_inches(getattr(shape, "left", 0))
    top = _emu_to_inches(getattr(shape, "top", 0))
    width = _emu_to_inches(getattr(shape, "width", 0))
    height = _emu_to_inches(getattr(shape, "height", 0))
    font_sizes = _font_sizes(shape)
    area = max(0.0, width * height)
    shape_type = str(getattr(shape, "shape_type", ""))
    is_line_like = width < 0.08 or height < 0.045
    is_full_background = area >= slide_w * slide_h * 0.86 and not text and not table_info.get("has_table")
    return {
        "index": index,
        "name": getattr(shape, "name", ""),
        "shape_type": shape_type,
        "has_text": bool(text),
        "text": text,
        "text_chars": len(text),
        "text_words": len(text.split()),
        "has_table": bool(table_info.get("has_table")),
        "table": table_info,
        "bbox": {
            "x": round(left, 3),
            "y": round(top, 3),
            "w": round(width, 3),
            "h": round(height, 3),
            "right": round(left + width, 3),
            "bottom": round(top + height, 3),
            "area": round(area, 3),
        },
        "font": {
            "sizes_pt": font_sizes,
            "min_pt": min(font_sizes) if font_sizes else None,
            "avg_pt": round(sum(font_sizes) / len(font_sizes), 2) if font_sizes else None,
        },
        "is_picture": shape_type == "PICTURE (13)" or shape_type == "13",
        "is_line_like": is_line_like,
        "is_full_background": is_full_background,
    }


def _table_info(shape: Any) -> Dict[str, Any]:
    if not getattr(shape, "has_table", False):
        return {"has_table": False}
    table = shape.table
    rows = []
    for row in table.rows:
        cells = [_clean_text(cell.text) for cell in row.cells]
        if any(cells):
            rows.append(cells)
    return {
        "has_table": True,
        "row_count": len(table.rows),
        "col_count": len(table.columns),
        "non_empty_rows": len(rows),
        "preview_rows": rows[:4],
    }


def _font_sizes(shape: Any) -> List[float]:
    if not getattr(shape, "has_text_frame", False):
        return []
    sizes: List[float] = []
    for paragraph in shape.text_frame.paragraphs:
        if paragraph.font.size is not None:
            sizes.append(round(paragraph.font.size.pt, 2))
        for run in paragraph.runs:
            if run.font.size is not None:
                sizes.append(round(run.font.size.pt, 2))
    return sizes


def _infer_role(record: Dict[str, Any], slide_h: float) -> str:
    text = record.get("text", "")
    bbox = record.get("bbox", {})
    font_avg = record.get("font", {}).get("avg_pt") or 0
    area = bbox.get("area", 0.0)
    x = bbox.get("x", 0.0)
    y = bbox.get("y", 0.0)
    w = bbox.get("w", 0.0)

    if record.get("is_full_background"):
        return "background"
    if record.get("has_table"):
        return "table"
    if record.get("is_picture"):
        return "picture"
    if not text:
        if record.get("is_line_like"):
            return "decorative_rule"
        if area > 0.2:
            return "container"
        return "decorative"
    if text.startswith("Sources:") or y > slide_h - 0.65:
        return "source_footer"
    if re.match(r"^\d{1,2}\s*/\s*\d{1,2}\b", text) or (y < 0.55 and w < 2.2 and font_avg <= 10):
        return "page_marker"
    if text in {"EVIDENCE NOTES", "EVIDENCE MOSAIC", "PAPER HIGHLIGHTS", "DECK MAP", "KEY EVIDENCE"}:
        return "component_label"
    if text in {"Method", "Limitations", "Reading note 1", "Reading note 2", "Reading note 3"}:
        return "card_label"
    if font_avg <= 10 and len(text) > 18 and y > 1.0:
        return "card_text"
    if font_avg >= 20 or (y < 2.8 and w > 4.0 and len(text) > 48 and (bbox.get("h", 0.0) >= 0.55 or font_avg >= 18)):
        return "title_claim"
    if len(text) > 55 and font_avg <= 15:
        return "support_body"
    if text.isupper() and len(text) < 70 and font_avg <= 12:
        return "component_label"
    if font_avg <= 10:
        return "small_text"
    return "body_text"


def _text_capacity_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    for record in records:
        if not record.get("has_text"):
            continue
        role = record.get("role", "")
        if role in {"source_footer", "page_marker", "component_label", "card_label"}:
            continue
        estimate = _text_capacity_estimate(record)
        record["text_capacity"] = estimate
        font_min = record.get("font", {}).get("min_pt")
        floor = _font_floor(role, rules)
        if record.get("text_chars", 0) < 28 and role in {"card_text", "small_text", "body_text"}:
            floor = 0.0
        if role == "title_claim" and (record.get("font", {}).get("avg_pt") or 0) < 18:
            floor = 0.0
        if font_min is not None and floor and font_min < floor:
            findings.append(
                _finding(
                    slide_index,
                    "low_font_size",
                    "medium" if role in {"title_claim", "support_body", "body_text"} else "low",
                    f"{role} text uses {font_min:.1f}pt below the {floor:.1f}pt metadata floor.",
                    record,
                    "Increase font size or shorten copy while preserving the component's accepted composition.",
                )
            )
        fill_ratio = estimate["fill_ratio"]
        if fill_ratio >= float(rules["overflow_ratio"]):
            findings.append(
                _finding(
                    slide_index,
                    "estimated_text_overflow",
                    "high",
                    f"{role} text is estimated at {fill_ratio:.2f}x box capacity.",
                    record,
                    "Shorten text, add a line break, or move secondary detail into notes; resize only if capacity remains impossible.",
                )
            )
        elif fill_ratio >= float(rules["near_capacity_ratio"]):
            findings.append(
                _finding(
                    slide_index,
                    "near_text_capacity",
                    "low",
                    f"{role} text is estimated at {fill_ratio:.2f}x box capacity.",
                    record,
                    "Keep composition fixed; slightly shorten text or raise the box's assigned font only after checking capacity.",
                )
            )
        elif (
            fill_ratio <= float(rules["sparse_ratio"])
            and record.get("bbox", {}).get("area", 0) >= float(rules["sparse_area_sq_in"])
            and role in {"support_body", "card_text", "body_text"}
        ):
            findings.append(
                _finding(
                    slide_index,
                    "low_text_density",
                    "low",
                    f"{role} text occupies only {fill_ratio:.2f}x of estimated capacity in a large box.",
                    record,
                    "Prefer stronger typography or richer evidence text; do not auto-shrink the component because low density hurt v6.",
                )
            )
    return findings


def _text_capacity_estimate(record: Dict[str, Any]) -> Dict[str, Any]:
    bbox = record.get("bbox", {})
    text = record.get("text", "")
    font = record.get("font", {}).get("avg_pt") or _fallback_font(record.get("role", ""))
    usable_w = max(0.1, float(bbox.get("w", 0.0)) - 0.18)
    usable_h = max(0.1, float(bbox.get("h", 0.0)) - 0.12)
    chars_per_line = max(1.0, usable_w * 72.0 / max(1.0, font * 0.50))
    line_count = max(1.0, usable_h * 72.0 / max(1.0, font * 1.18))
    capacity = max(1.0, chars_per_line * line_count * 0.92)
    effective_chars = _effective_char_units(text)
    return {
        "font_pt": round(font, 2),
        "capacity_chars": round(capacity, 1),
        "effective_chars": round(effective_chars, 1),
        "estimated_lines": round(line_count, 2),
        "fill_ratio": round(effective_chars / capacity, 3),
    }


def _overlap_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    for i, left in enumerate(records):
        if _ignore_overlap_record(left):
            continue
        for right in records[i + 1 :]:
            if _ignore_overlap_record(right):
                continue
            overlap = _intersection(left["bbox"], right["bbox"])
            if overlap <= 0:
                continue
            smaller = max(0.01, min(left["bbox"].get("area", 0.0), right["bbox"].get("area", 0.0)))
            ratio = overlap / smaller
            if _is_allowed_containment(left, right):
                continue
            threshold = float(rules["container_overlap_ratio"]) if "container" in {left.get("role"), right.get("role")} else float(rules["overlap_ratio"])
            if ratio >= threshold:
                findings.append(
                    {
                        "type": "shape_overlap_risk",
                        "severity": "high" if ratio >= 0.35 else "medium",
                        "slide_page": slide_index,
                        "message": f"{left.get('role')} overlaps {right.get('role')} by {ratio:.2f} of the smaller shape.",
                        "evidence": {
                            "shape_a": _shape_evidence(left),
                            "shape_b": _shape_evidence(right),
                            "overlap_area_sq_in": round(overlap, 3),
                            "overlap_ratio": round(ratio, 3),
                        },
                        "repair_strategy": "Move proof/table/card systems within their existing composition grid; do not rely on rendered screenshots to discover this.",
                    }
                )
    return findings


def _table_findings(slide_index: int, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    findings = []
    for record in records:
        if record.get("role") != "table":
            continue
        table = record.get("table", {})
        bbox = record.get("bbox", {})
        rows = int(table.get("row_count") or 0)
        cols = int(table.get("col_count") or 0)
        if rows <= 1 or cols <= 1:
            findings.append(
                _finding(
                    slide_index,
                    "weak_table_grammar",
                    "medium",
                    "Native table has too few rows or columns to carry table evidence.",
                    record,
                    "Check table extraction before changing layout; table proof should preserve row/column grammar.",
                )
            )
        row_height = bbox.get("h", 0) / max(1, rows)
        col_width = bbox.get("w", 0) / max(1, cols)
        if row_height < 0.18 or col_width < 0.45:
            findings.append(
                _finding(
                    slide_index,
                    "dense_table_readability_risk",
                    "medium",
                    f"Table cell estimate is tight: row height {row_height:.2f}in, column width {col_width:.2f}in.",
                    record,
                    "Preserve table size and simplify visible columns/rows, or move dense detail into appendix-style treatment.",
                )
            )
    return findings


def _slide_density_findings(
    slide_index: int,
    records: List[Dict[str, Any]],
    slide_w: float,
    slide_h: float,
    rules: Dict[str, Any],
) -> List[Dict[str, Any]]:
    meaningful = [r for r in records if _meaningful_for_occupancy(r)]
    occupied = sum(r["bbox"].get("area", 0.0) for r in meaningful)
    occupancy = occupied / max(0.01, slide_w * slide_h)
    words = sum(int(r.get("text_words") or 0) for r in meaningful)
    if occupancy < float(rules["low_occupancy_ratio"]) and words < 28 and len(meaningful) <= 5:
        return [
            {
                "type": "sparse_slide_risk",
                "severity": "low",
                "slide_page": slide_index,
                "message": f"Slide has low metadata occupancy ({occupancy:.2f}) and only {words} visible words.",
                "evidence": {"occupancy_ratio": round(occupancy, 3), "visible_words": words, "meaningful_shape_count": len(meaningful)},
                "repair_strategy": "First enrich or rebalance text hierarchy; avoid shrinking well-composed components solely to fill whitespace.",
            }
        ]
    return []


def _slide_summary(
    slide_index: int,
    records: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
    slide_w: float,
    slide_h: float,
) -> Dict[str, Any]:
    meaningful = [r for r in records if _meaningful_for_occupancy(r)]
    occupied = sum(r["bbox"].get("area", 0.0) for r in meaningful)
    role_counts: Dict[str, int] = {}
    for record in records:
        role_counts[record.get("role", "unknown")] = role_counts.get(record.get("role", "unknown"), 0) + 1
    return {
        "page": slide_index,
        "shape_count": len(records),
        "meaningful_shape_count": len(meaningful),
        "visible_words": sum(int(r.get("text_words") or 0) for r in meaningful),
        "occupancy_ratio": round(occupied / max(0.01, slide_w * slide_h), 3),
        "role_counts": role_counts,
        "finding_count": len(findings),
        "finding_types": sorted({finding["type"] for finding in findings}),
    }


def _summarize_findings(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    for finding in findings:
        by_type[finding["type"]] = by_type.get(finding["type"], 0) + 1
        by_severity[finding["severity"]] = by_severity.get(finding["severity"], 0) + 1
    return {
        "finding_count": len(findings),
        "by_type": by_type,
        "by_severity": by_severity,
        "high_risk_pages": sorted({finding["slide_page"] for finding in findings if finding["severity"] == "high"}),
        "medium_risk_pages": sorted({finding["slide_page"] for finding in findings if finding["severity"] == "medium"}),
    }


def _finding(
    slide_index: int,
    kind: str,
    severity: str,
    message: str,
    record: Dict[str, Any],
    repair_strategy: str,
) -> Dict[str, Any]:
    return {
        "type": kind,
        "severity": severity,
        "slide_page": slide_index,
        "message": message,
        "evidence": {"shape": _shape_evidence(record)},
        "repair_strategy": repair_strategy,
    }


def _shape_evidence(record: Dict[str, Any]) -> Dict[str, Any]:
    text = record.get("text", "")
    return {
        "index": record.get("index"),
        "role": record.get("role"),
        "bbox": record.get("bbox"),
        "font": record.get("font"),
        "text_preview": text[:90],
        "text_words": record.get("text_words", 0),
        "text_capacity": record.get("text_capacity", {}),
    }


def _font_floor(role: str, rules: Dict[str, Any]) -> float:
    if role == "title_claim":
        return float(rules["title_claim_min_pt"])
    if role == "support_body":
        return float(rules["support_min_pt"])
    if role == "card_text":
        return float(rules["card_text_min_pt"])
    if role == "body_text":
        return float(rules["body_min_pt"])
    return 0.0


def _fallback_font(role: str) -> float:
    return {
        "title_claim": 24.0,
        "support_body": 12.0,
        "card_text": 9.0,
        "body_text": 11.0,
        "small_text": 8.0,
    }.get(role, 10.0)


def _effective_char_units(text: str) -> float:
    total = 0.0
    for char in text:
        if char.isspace():
            total += 0.35
        elif ord(char) > 127:
            total += 1.75
        elif char in ".,;:!|":
            total += 0.35
        else:
            total += 1.0
    return total


def _ignore_overlap_record(record: Dict[str, Any]) -> bool:
    return record.get("role") in {"background", "decorative", "decorative_rule", "source_footer", "page_marker", "component_label"} or record.get("bbox", {}).get("area", 0) <= 0.01


def _meaningful_for_occupancy(record: Dict[str, Any]) -> bool:
    if record.get("role") in {"background", "decorative", "decorative_rule", "source_footer", "page_marker", "component_label"}:
        return False
    return bool(record.get("has_text") or record.get("has_table") or record.get("is_picture") or record.get("role") == "container")


def _is_allowed_containment(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    roles = {a.get("role"), b.get("role")}
    if roles == {"container"}:
        return True
    if "container" not in roles:
        return False
    container = a if a.get("role") == "container" else b
    contained = b if a.get("role") == "container" else a
    if contained.get("role") in {"picture", "table"}:
        return _center_inside(contained["bbox"], container["bbox"])
    if contained.get("role") == "title_claim" and (contained.get("text_words") or 0) <= 2:
        return _center_inside(contained["bbox"], container["bbox"])
    if contained.get("role") in {"card_label", "card_text", "small_text", "body_text", "support_body"}:
        return _center_inside(contained["bbox"], container["bbox"])
    return False


def _center_inside(inner: Dict[str, float], outer: Dict[str, float]) -> bool:
    cx = inner.get("x", 0.0) + inner.get("w", 0.0) / 2
    cy = inner.get("y", 0.0) + inner.get("h", 0.0) / 2
    return outer.get("x", 0.0) <= cx <= outer.get("right", 0.0) and outer.get("y", 0.0) <= cy <= outer.get("bottom", 0.0)


def _intersection(a: Dict[str, float], b: Dict[str, float]) -> float:
    x1 = max(float(a.get("x", 0.0)), float(b.get("x", 0.0)))
    y1 = max(float(a.get("y", 0.0)), float(b.get("y", 0.0)))
    x2 = min(float(a.get("right", 0.0)), float(b.get("right", 0.0)))
    y2 = min(float(a.get("bottom", 0.0)), float(b.get("bottom", 0.0)))
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return (x2 - x1) * (y2 - y1)


def _emu_to_inches(value: Any) -> float:
    try:
        return float(value) / EMU_PER_INCH
    except Exception:
        return 0.0


def _clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect PPTX geometry and text capacity without rendering slides.")
    parser.add_argument("--pptx", required=True, help="Path to PPTX file.")
    parser.add_argument("--output", help="Optional path to write nonvisual audit JSON.")
    args = parser.parse_args(argv)

    audit = inspect_pptx_nonvisual(Path(args.pptx))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
