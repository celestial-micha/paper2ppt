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
    "card_text_min_pt": 9.0,
    "body_min_pt": 10.5,
    "title_claim_ideal_min_pt": 24.0,
    "support_ideal_min_pt": 12.5,
    "card_text_ideal_min_pt": 9.8,
    "body_ideal_min_pt": 12.0,
    "near_capacity_ratio": 0.82,
    "overflow_ratio": 1.03,
    "sparse_ratio": 0.16,
    "sparse_area_sq_in": 1.15,
    "overlap_ratio": 0.14,
    "container_overlap_ratio": 0.18,
    "low_occupancy_ratio": 0.18,
    "card_copy_imbalance_ratio": 2.6,
    "cover_left_min_pt": 14.0,
    "deck_typography_signal_count": 8,
    "flow_label_min_gap_in": 0.10,
    "flow_grid_max_col_gap_in": 1.75,
    "flow_grid_min_row_gap_in": 0.62,
    "flow_grid_col_to_row_ratio_max": 2.7,
    "flow_label_center_tolerance_in": 0.09,
    "paired_text_top_delta_max_in": 0.26,
    "component_label_min_inset_in": 0.30,
    "component_frame_extra_height_max_in": 0.42,
    "metric_label_gap_max_in": 0.065,
    "metric_card_min_area_sq_in": 0.40,
    "balance_container_min_area_sq_in": 3.6,
    "balance_padding_tolerance_in": 0.38,
    "balance_padding_tolerance_ratio": 0.11,
    "picture_aspect_ratio_tolerance": 0.18,
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
        slide_findings.extend(_cover_typography_findings(slide_index, records, active_rules))
        slide_findings.extend(_paired_text_stack_findings(slide_index, records, active_rules))
        slide_findings.extend(_copy_distribution_findings(slide_index, records, active_rules))
        slide_findings.extend(_flow_layout_findings(slide_index, records, active_rules))
        slide_findings.extend(_metric_stack_findings(slide_index, records, active_rules))
        slide_findings.extend(_component_boundary_findings(slide_index, records, active_rules))
        slide_findings.extend(_component_frame_fit_findings(slide_index, records, active_rules))
        slide_findings.extend(_container_balance_findings(slide_index, records, active_rules))
        slide_findings.extend(_overlap_findings(slide_index, records, active_rules))
        slide_findings.extend(_table_findings(slide_index, records))
        slide_findings.extend(_picture_findings(slide_index, records, active_rules))
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
        "summary": _summarize_findings(findings, active_rules),
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
    is_picture = shape_type == "PICTURE (13)" or shape_type == "13"
    is_line_like = width < 0.08 or height < 0.045
    is_full_background = area >= slide_w * slide_h * 0.86 and not text and not table_info.get("has_table")
    picture_info = _picture_info(shape, width, height) if is_picture else {"is_picture": False}
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
        "is_picture": is_picture,
        "picture": picture_info,
        "is_line_like": is_line_like,
        "is_full_background": is_full_background,
    }


def _picture_info(shape: Any, width: float, height: float) -> Dict[str, Any]:
    try:
        image = shape.image
        image_w, image_h = image.size
        source_aspect = image_w / image_h if image_h else None
    except Exception:
        image_w = image_h = None
        source_aspect = None
    box_aspect = width / height if height else None
    if source_aspect and box_aspect:
        distortion = abs(math.log(max(source_aspect, box_aspect) / max(0.001, min(source_aspect, box_aspect))))
    else:
        distortion = None
    return {
        "is_picture": True,
        "image_px": {"w": image_w, "h": image_h},
        "source_aspect": round(source_aspect, 3) if source_aspect else None,
        "box_aspect": round(box_aspect, 3) if box_aspect else None,
        "aspect_distortion": round(distortion, 3) if distortion is not None else None,
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
    if text.startswith("Sources:") or y > slide_h - 0.65 or (y > slide_h - 0.95 and font_avg <= 9):
        return "source_footer"
    if re.match(r"^\d{1,2}\s*/\s*\d{1,2}\b", text) or (y < 0.55 and w < 2.2 and font_avg <= 10):
        return "page_marker"
    normalized_label = _label_token(text)
    if normalized_label in {
        "ACADEMICPAPERREADING",
        "DECKMAP",
        "EVIDENCEMOSAIC",
        "EVIDENCENOTES",
        "KEYEVIDENCE",
        "MODULECHECKPOINT",
        "PAPERHIGHLIGHTS",
        "PROOFOBJECT",
        "SECTION",
        "SUMMARY",
    }:
        return "component_label"
    if text in {"Method", "Limitations", "Reading note 1", "Reading note 2", "Reading note 3"}:
        return "card_label"
    if text.isupper() and len(text) < 70 and font_avg <= 12:
        return "component_label"
    if font_avg <= 10.5 and len(text) > 18 and y > 1.0:
        return "card_text"
    if font_avg >= 20 or (font_avg >= 16 and y < 2.8 and w > 4.0 and len(text) > 48 and bbox.get("h", 0.0) >= 0.55):
        return "title_claim"
    if len(text) > 55 and font_avg <= 15:
        return "support_body"
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
        elif font_min is not None and floor:
            ideal = _font_ideal_floor(role, rules)
            if ideal and font_min < ideal and record.get("text_chars", 0) >= 28:
                findings.append(
                    _finding(
                        slide_index,
                        "below_ideal_font_band",
                        "low",
                        f"{role} text uses {font_min:.1f}pt; preferred metadata band starts near {ideal:.1f}pt.",
                        record,
                        "Prefer a small typography lift before changing component geometry.",
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
            and int(record.get("text_words") or 0) > 3
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


def _cover_typography_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    if slide_index != 1:
        return []
    candidates = [
        record
        for record in records
        if record.get("role") in {"body_text", "support_body"}
        and record.get("bbox", {}).get("x", 0.0) < 8.2
        and int(record.get("text_words") or 0) >= 2
    ]
    if not candidates:
        return []
    weakest = min(candidates, key=lambda item: item.get("font", {}).get("min_pt") or 99.0)
    font_min = weakest.get("font", {}).get("min_pt")
    floor = float(rules["cover_left_min_pt"])
    if font_min is None or font_min >= floor:
        return []
    return [
        _finding(
            slide_index,
            "cover_left_typography_underpowered",
            "medium",
            f"Cover left narrative text uses {font_min:.1f}pt below the {floor:.1f}pt cover comfort floor.",
            weakest,
            "Lift the cover's left-side title metadata/support typography as a group, then recheck wrapping before moving components.",
        )
    ]


def _paired_text_stack_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    if slide_index != 1:
        return []
    highlight_labels = {"Core result", "Scale", "Design edge"}
    findings = []
    for label in records:
        if label.get("text") not in highlight_labels:
            continue
        label_box = label.get("bbox", {})
        candidates = [
            record
            for record in records
            if record is not label
            and record.get("has_text")
            and int(record.get("text_words") or 0) >= 4
            and abs(record.get("bbox", {}).get("x", 0.0) - label_box.get("x", 0.0)) <= 0.08
            and 0 < record.get("bbox", {}).get("y", 0.0) - label_box.get("y", 0.0) <= 0.55
        ]
        if not candidates:
            continue
        body = min(candidates, key=lambda item: item.get("bbox", {}).get("y", 0.0))
        top_delta = body["bbox"].get("y", 0.0) - label_box.get("y", 0.0)
        if top_delta <= float(rules["paired_text_top_delta_max_in"]):
            continue
        findings.append(
            {
                "type": "paired_label_body_gap_too_large",
                "severity": "low",
                **_finding_meta("paired_label_body_gap_too_large", "low"),
                "slide_page": slide_index,
                "message": f"Cover highlight '{label.get('text')}' and its body start {top_delta:.2f}in apart, weakening the paired rail reading.",
                "evidence": {
                    "label": _shape_evidence(label),
                    "body": _shape_evidence(body),
                    "top_delta_in": round(top_delta, 3),
                },
                "repair_strategy": "Treat the highlight label and explanation as one stack; move the body closer before changing the overall rail positions.",
            }
        )
    return findings


def _copy_distribution_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    card_records = [
        record
        for record in records
        if record.get("role") == "card_text"
        and record.get("bbox", {}).get("area", 0.0) >= 0.45
        and int(record.get("text_words") or 0) > 0
    ]
    if len(card_records) < 3:
        return []
    counts = [max(1, int(record.get("text_words") or 0)) for record in card_records]
    smallest = min(counts)
    largest = max(counts)
    if largest / max(1, smallest) < float(rules["card_copy_imbalance_ratio"]) or smallest > 6:
        return []
    record = card_records[counts.index(smallest)]
    return [
        _finding(
            slide_index,
            "card_copy_imbalance",
            "low",
            f"Evidence cards have uneven copy distribution: shortest card has {smallest} words, longest has {largest}.",
            record,
            "Rebalance reading notes or enrich the sparse card copy; keep the accepted card group size unless geometry fails.",
        )
    ]


def _flow_layout_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    labels = [record for record in records if record.get("text") in {"Problem", "Method", "Evidence", "Takeaways"}]
    if len(labels) < 4:
        return []
    ordered = sorted(labels, key=lambda item: item.get("bbox", {}).get("x", 0.0))
    row_span = max(item["bbox"].get("y", 0.0) for item in ordered) - min(item["bbox"].get("y", 0.0) for item in ordered)
    if row_span <= 0.18:
        gaps = [
            ordered[index + 1]["bbox"].get("x", 0.0) - ordered[index]["bbox"].get("right", 0.0)
            for index in range(len(ordered) - 1)
        ]
        min_gap = min(gaps) if gaps else 0.0
        if min_gap < float(rules["flow_label_min_gap_in"]):
            findings.append(
                {
                    "type": "flow_nodes_overpacked",
                    "severity": "medium",
                    **_finding_meta("flow_nodes_overpacked", "medium"),
                    "slide_page": slide_index,
                    "message": f"Read-path labels sit in one tight row with only {min_gap:.2f}in between adjacent labels.",
                    "evidence": {
                        "labels": [_shape_evidence(item) for item in ordered],
                        "min_label_gap_in": round(min_gap, 3),
                    },
                    "repair_strategy": "Switch compact flow components to two rows when labels are crowded instead of shrinking the label typography.",
                }
            )

    nodes = [record for record in records if record.get("text") in {"P", "M", "E", "T"}]
    if len(nodes) < 4:
        return findings
    nodes_by_text = {record.get("text"): record for record in nodes}
    labels_by_text = {record.get("text"): record for record in labels}
    node_centers = {
        key: (
            item.get("bbox", {}).get("x", 0.0) + item.get("bbox", {}).get("w", 0.0) / 2,
            item.get("bbox", {}).get("y", 0.0) + item.get("bbox", {}).get("h", 0.0) / 2,
        )
        for key, item in nodes_by_text.items()
    }
    if {"P", "M", "E", "T"}.issubset(node_centers):
        col_gap = ((node_centers["M"][0] - node_centers["P"][0]) + (node_centers["T"][0] - node_centers["E"][0])) / 2
        row_gap = ((node_centers["E"][1] - node_centers["P"][1]) + (node_centers["T"][1] - node_centers["M"][1])) / 2
        ratio = col_gap / max(0.01, row_gap)
        if (
            col_gap > float(rules["flow_grid_max_col_gap_in"])
            or row_gap < float(rules["flow_grid_min_row_gap_in"])
            or ratio > float(rules["flow_grid_col_to_row_ratio_max"])
        ):
            findings.append(
                {
                    "type": "flow_grid_alignment_drift",
                    "severity": "low",
                    **_finding_meta("flow_grid_alignment_drift", "low"),
                    "slide_page": slide_index,
                    "message": f"2x2 read-path grid has column gap {col_gap:.2f}in and row gap {row_gap:.2f}in, making the component feel stretched.",
                    "evidence": {
                        "nodes": [_shape_evidence(nodes_by_text[key]) for key in ["P", "M", "E", "T"]],
                        "column_gap_in": round(col_gap, 3),
                        "row_gap_in": round(row_gap, 3),
                        "column_to_row_ratio": round(ratio, 3),
                    },
                    "repair_strategy": "Use a compact 2x2 grid: reduce column distance, give rows enough air, and keep labels centered below their nodes.",
                }
            )
    text_to_label = {"P": "Problem", "M": "Method", "E": "Evidence", "T": "Takeaways"}
    center_tolerance = float(rules["flow_label_center_tolerance_in"])
    for letter, label_text in text_to_label.items():
        node = nodes_by_text.get(letter)
        label = labels_by_text.get(label_text)
        if not node or not label:
            continue
        node_cx = node["bbox"].get("x", 0.0) + node["bbox"].get("w", 0.0) / 2
        label_cx = label["bbox"].get("x", 0.0) + label["bbox"].get("w", 0.0) / 2
        drift = abs(node_cx - label_cx)
        if drift <= center_tolerance:
            continue
        findings.append(
            {
                "type": "flow_grid_alignment_drift",
                "severity": "low",
                **_finding_meta("flow_grid_alignment_drift", "low"),
                "slide_page": slide_index,
                "message": f"Read-path label '{label_text}' is {drift:.2f}in away from the center of node {letter}.",
                "evidence": {
                    "node": _shape_evidence(node),
                    "label": _shape_evidence(label),
                    "center_drift_in": round(drift, 3),
                },
                "repair_strategy": "Center each read-path label under its circle after wrapping the flow to two rows.",
            }
        )
    return findings


def _metric_stack_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    for container in _container_records(records):
        bbox = container.get("bbox", {})
        area = bbox.get("area", 0.0)
        if area < float(rules["metric_card_min_area_sq_in"]) or area > 8.0:
            continue
        children = _contained_records(container, records, include_containers=False)
        values = [child for child in children if _looks_metric_value(child.get("text", ""))]
        if not values:
            continue
        value = max(values, key=lambda child: child.get("font", {}).get("avg_pt") or 0.0)
        labels = [
            child
            for child in children
            if child is not value
            and child.get("has_text")
            and child.get("bbox", {}).get("y", 0.0) > value.get("bbox", {}).get("y", 0.0)
            and child.get("role") in {"small_text", "card_text", "body_text", "support_body"}
        ]
        if not labels:
            continue
        label = min(labels, key=lambda child: child.get("bbox", {}).get("y", 0.0))
        gap = label["bbox"].get("y", 0.0) - value["bbox"].get("bottom", 0.0)
        if gap <= float(rules["metric_label_gap_max_in"]):
            continue
        findings.append(
            {
                "type": "metric_label_gap_too_large",
                "severity": "low",
                **_finding_meta("metric_label_gap_too_large", "low"),
                "slide_page": slide_index,
                "message": f"Metric value and label are separated by {gap:.2f}in inside one card.",
                "evidence": {
                    "container": _shape_evidence(container),
                    "value": _shape_evidence(value),
                    "label": _shape_evidence(label),
                    "gap_in": round(gap, 3),
                },
                "repair_strategy": "Treat value and label as one optical text stack; use a fixed stack gap instead of card-height proportional placement.",
            }
        )
    return findings


def _component_boundary_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    watched_labels = {"FIGURE", "TABLE"}
    containers = _container_records(records)
    min_inset = float(rules["component_label_min_inset_in"])
    for label in records:
        if label.get("role") != "component_label" or _label_token(label.get("text", "")) not in watched_labels:
            continue
        label_box = label.get("bbox", {})
        parent = _smallest_containing_container(label_box, containers)
        if not parent:
            continue
        parent_box = parent.get("bbox", {})
        insets = {
            "left": label_box.get("x", 0.0) - parent_box.get("x", 0.0),
            "top": label_box.get("y", 0.0) - parent_box.get("y", 0.0),
            "right": parent_box.get("right", 0.0) - label_box.get("right", 0.0),
            "bottom": parent_box.get("bottom", 0.0) - label_box.get("bottom", 0.0),
        }
        leading_inset = min(insets["left"], insets["top"])
        if leading_inset >= min_inset:
            continue
        findings.append(
            {
                "type": "component_boundary_inset_violation",
                "severity": "low",
                **_finding_meta("component_boundary_inset_violation", "low"),
                "slide_page": slide_index,
                "message": f"{label.get('text')} label sits only {leading_inset:.2f}in from its rounded component boundary.",
                "evidence": {
                    "label": _shape_evidence(label),
                    "container": _shape_evidence(parent),
                    "insets_in": {key: round(value, 3) for key, value in insets.items()},
                },
                "repair_strategy": "Inset component labels from rounded panel corners before fitting the figure/table content area.",
            }
        )
    return findings


def _component_frame_fit_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    for container in _container_records(records):
        bbox = container.get("bbox", {})
        if bbox.get("h", 0.0) > 2.2 or bbox.get("w", 0.0) < 1.4 or bbox.get("area", 0.0) < 1.0:
            continue
        children = [
            child
            for child in _contained_records(container, records, include_containers=False)
            if child.get("has_text") and child.get("role") not in {"source_footer", "page_marker", "component_label"}
        ]
        if len(children) < 2 or any(child.get("has_table") or child.get("is_picture") for child in children):
            continue
        if not any(child.get("role") == "card_label" for child in children):
            continue
        if not any(child.get("role") in {"card_text", "body_text", "support_body"} for child in children):
            continue
        expected_h = _expected_text_stack_height(children, bbox)
        extra_h = bbox.get("h", 0.0) - expected_h
        if extra_h <= float(rules["component_frame_extra_height_max_in"]):
            continue
        findings.append(
            {
                "type": "component_frame_overallocated_after_text_fit",
                "severity": "low",
                **_finding_meta("component_frame_overallocated_after_text_fit", "low"),
                "slide_page": slide_index,
                "message": f"Evidence card frame has about {extra_h:.2f}in more height than its fitted text stack needs.",
                "evidence": {
                    "container": _shape_evidence(container),
                    "text_children": [_shape_evidence(child) for child in sorted(children, key=lambda item: item["bbox"].get("y", 0.0))],
                    "expected_stack_height_in": round(expected_h, 3),
                    "extra_height_in": round(extra_h, 3),
                },
                "repair_strategy": "After fitting text, resize the local card frame and reflow sibling cards on the same slide instead of changing deck-wide type roles.",
            }
        )
    return findings


def _container_balance_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    for container in _container_records(records):
        bbox = container.get("bbox", {})
        if bbox.get("area", 0.0) < float(rules["balance_container_min_area_sq_in"]):
            continue
        if bbox.get("w", 0.0) > 8.0 or bbox.get("h", 0.0) > 6.8:
            continue
        children = _contained_records(container, records, include_containers=True)
        children = [
            child
            for child in children
            if child.get("role") not in {"decorative", "decorative_rule", "component_label", "source_footer", "page_marker"}
            and not child.get("is_full_background")
        ]
        if len(children) < 2:
            continue
        union = _bbox_union([child["bbox"] for child in children])
        top_pad = union.get("y", 0.0) - bbox.get("y", 0.0)
        bottom_pad = bbox.get("bottom", 0.0) - union.get("bottom", 0.0)
        delta = abs(top_pad - bottom_pad)
        tolerance = max(float(rules["balance_padding_tolerance_in"]), bbox.get("h", 0.0) * float(rules["balance_padding_tolerance_ratio"]))
        if delta <= tolerance:
            continue
        findings.append(
            {
                "type": "container_stack_off_balance",
                "severity": "low",
                **_finding_meta("container_stack_off_balance", "low"),
                "slide_page": slide_index,
                "message": f"Container content stack has uneven vertical padding: top {top_pad:.2f}in, bottom {bottom_pad:.2f}in.",
                "evidence": {
                    "container": _shape_evidence(container),
                    "child_count": len(children),
                    "stack_bbox": union,
                    "top_padding_in": round(top_pad, 3),
                    "bottom_padding_in": round(bottom_pad, 3),
                    "padding_delta_in": round(delta, 3),
                },
                "repair_strategy": "Rebalance the internal stack or enrich sparse metric cards before changing the whole slide macro-layout.",
            }
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
                severity = "high" if ratio >= 0.35 else "medium"
                findings.append(
                    {
                        "type": "shape_overlap_risk",
                        "severity": severity,
                        **_finding_meta("shape_overlap_risk", severity),
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


def _picture_findings(slide_index: int, records: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    tolerance = float(rules["picture_aspect_ratio_tolerance"])
    for record in records:
        if not record.get("is_picture"):
            continue
        picture = record.get("picture", {}) or {}
        distortion = picture.get("aspect_distortion")
        if distortion is None or distortion <= tolerance:
            continue
        findings.append(
            _finding(
                slide_index,
                "figure_picture_aspect_distortion",
                "medium",
                f"Picture box aspect ratio {picture.get('box_aspect')} differs from source image aspect ratio {picture.get('source_aspect')}.",
                record,
                "Fit the figure inside the component box while preserving the source image aspect ratio; route wide figures to horizontal proof panels when needed.",
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
                **_finding_meta("sparse_slide_risk", "low"),
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


def _summarize_findings(findings: List[Dict[str, Any]], rules: Dict[str, Any]) -> Dict[str, Any]:
    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    by_problem_type: Dict[str, int] = {}
    for finding in findings:
        by_type[finding["type"]] = by_type.get(finding["type"], 0) + 1
        by_severity[finding["severity"]] = by_severity.get(finding["severity"], 0) + 1
        problem_type = finding.get("problem_type", _problem_type_for_finding(finding["type"]))
        by_problem_type[problem_type] = by_problem_type.get(problem_type, 0) + 1
    return {
        "finding_count": len(findings),
        "by_type": by_type,
        "by_severity": by_severity,
        "by_problem_type": by_problem_type,
        "high_risk_pages": sorted({finding["slide_page"] for finding in findings if finding["severity"] == "high"}),
        "medium_risk_pages": sorted({finding["slide_page"] for finding in findings if finding["severity"] == "medium"}),
        "typography_pages": sorted({finding["slide_page"] for finding in findings if finding.get("problem_type") == "typography"}),
        "copy_fitting_pages": sorted({finding["slide_page"] for finding in findings if finding.get("problem_type") == "copy_fitting"}),
        "geometry_pages": sorted({finding["slide_page"] for finding in findings if finding.get("problem_type") == "geometry"}),
        "optical_balance_pages": sorted({finding["slide_page"] for finding in findings if finding.get("problem_type") == "optical_balance"}),
        "deck_flags": _deck_flags(by_type, rules),
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
        **_finding_meta(kind, severity),
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


def _font_ideal_floor(role: str, rules: Dict[str, Any]) -> float:
    if role == "title_claim":
        return float(rules["title_claim_ideal_min_pt"])
    if role == "support_body":
        return float(rules["support_ideal_min_pt"])
    if role == "card_text":
        return float(rules["card_text_ideal_min_pt"])
    if role == "body_text":
        return float(rules["body_ideal_min_pt"])
    return 0.0


def _finding_meta(kind: str, severity: str) -> Dict[str, Any]:
    problem_type = _problem_type_for_finding(kind)
    return {
        "problem_type": problem_type,
        "repair_priority": _repair_priority(kind, severity),
        "geometry_repair_allowed": problem_type == "geometry" or kind == "component_frame_overallocated_after_text_fit",
        "preferred_repair_scope": _preferred_repair_scope(problem_type),
    }


def _problem_type_for_finding(kind: str) -> str:
    if kind in {"low_font_size", "below_ideal_font_band", "cover_left_typography_underpowered"}:
        return "typography"
    if kind in {"estimated_text_overflow", "near_text_capacity", "low_text_density", "sparse_slide_risk", "card_copy_imbalance"}:
        return "copy_fitting"
    if kind in {
        "shape_overlap_risk",
        "weak_table_grammar",
        "dense_table_readability_risk",
        "flow_nodes_overpacked",
        "flow_grid_alignment_drift",
        "component_boundary_inset_violation",
        "figure_picture_aspect_distortion",
    }:
        return "geometry"
    if kind in {
        "metric_label_gap_too_large",
        "container_stack_off_balance",
        "paired_label_body_gap_too_large",
        "component_frame_overallocated_after_text_fit",
    }:
        return "optical_balance"
    return "metadata"


def _repair_priority(kind: str, severity: str) -> str:
    if severity == "high":
        return "P1"
    if kind in {"shape_overlap_risk", "weak_table_grammar", "dense_table_readability_risk", "component_boundary_inset_violation", "figure_picture_aspect_distortion"}:
        return "P2"
    if kind in {"low_font_size", "estimated_text_overflow", "near_text_capacity"}:
        return "P2" if severity == "medium" else "P3"
    return "P3"


def _preferred_repair_scope(problem_type: str) -> str:
    if problem_type == "typography":
        return "font hierarchy, weight, and line-height before layout changes"
    if problem_type == "copy_fitting":
        return "copy allocation, line breaks, richer notes, or notes splitting before resizing"
    if problem_type == "geometry":
        return "minimal component position/size repair only because a structural signal failed"
    if problem_type == "optical_balance":
        return "internal text-stack spacing and padding before macro-layout changes"
    return "metadata review"


def _deck_flags(by_type: Dict[str, int], rules: Dict[str, Any]) -> List[str]:
    flags = []
    typography_signals = (
        by_type.get("below_ideal_font_band", 0)
        + by_type.get("low_font_size", 0)
        + by_type.get("cover_left_typography_underpowered", 0)
    )
    if typography_signals >= int(rules["deck_typography_signal_count"]):
        flags.append("deck_type_scale_under_comfort_band")
    return flags


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


def _container_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("role") == "container"
        and not record.get("is_full_background")
        and record.get("bbox", {}).get("area", 0.0) > 0.01
    ]


def _contained_records(container: Dict[str, Any], records: List[Dict[str, Any]], include_containers: bool) -> List[Dict[str, Any]]:
    result = []
    outer = container.get("bbox", {})
    for record in records:
        if record is container:
            continue
        if record.get("role") == "container" and not include_containers:
            continue
        if record.get("is_full_background"):
            continue
        bbox = record.get("bbox", {})
        if bbox.get("area", 0.0) <= 0.0:
            continue
        if _center_inside(bbox, outer):
            result.append(record)
    return result


def _smallest_containing_container(label_box: Dict[str, float], containers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    containing = [container for container in containers if _center_inside(label_box, container.get("bbox", {}))]
    if not containing:
        return None
    return min(containing, key=lambda item: item.get("bbox", {}).get("area", 0.0))


def _expected_text_stack_height(children: List[Dict[str, Any]], container_box: Dict[str, float]) -> float:
    sorted_children = sorted(children, key=lambda item: item.get("bbox", {}).get("y", 0.0))
    usable_w = max(0.1, container_box.get("w", 0.0) - 0.36)
    text_height = 0.0
    for child in sorted_children:
        font = child.get("font", {}).get("avg_pt") or _fallback_font(child.get("role", ""))
        char_units = _effective_char_units(child.get("text", ""))
        chars_per_line = max(1.0, usable_w * 72.0 / max(1.0, font * 0.50))
        lines_needed = max(1.0, math.ceil(char_units / chars_per_line))
        text_height += lines_needed * font * 1.18 / 72.0
    gaps = max(0, len(sorted_children) - 1) * 0.12
    vertical_margins = 0.34
    return text_height + gaps + vertical_margins


def _bbox_union(boxes: List[Dict[str, float]]) -> Dict[str, float]:
    if not boxes:
        return {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0, "right": 0.0, "bottom": 0.0, "area": 0.0}
    left = min(float(box.get("x", 0.0)) for box in boxes)
    top = min(float(box.get("y", 0.0)) for box in boxes)
    right = max(float(box.get("right", 0.0)) for box in boxes)
    bottom = max(float(box.get("bottom", 0.0)) for box in boxes)
    return {
        "x": round(left, 3),
        "y": round(top, 3),
        "w": round(max(0.0, right - left), 3),
        "h": round(max(0.0, bottom - top), 3),
        "right": round(right, 3),
        "bottom": round(bottom, 3),
        "area": round(max(0.0, right - left) * max(0.0, bottom - top), 3),
    }


def _looks_metric_value(text: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)?(?:%|[TBMK])?", _clean_text(text)))


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


def _label_token(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(text or "").upper())


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
