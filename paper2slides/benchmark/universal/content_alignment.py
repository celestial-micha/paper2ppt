"""Checkpoint-to-DeckIR alignment helpers for universal PPT scoring."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


STOPWORDS = {
    "about",
    "across",
    "after",
    "again",
    "against",
    "also",
    "and",
    "are",
    "because",
    "been",
    "between",
    "both",
    "but",
    "can",
    "could",
    "from",
    "has",
    "have",
    "into",
    "its",
    "more",
    "not",
    "over",
    "per",
    "such",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "through",
    "using",
    "while",
    "with",
    "within",
    "without",
}


def align_deck_to_checkpoints(
    deck_ir: Dict[str, Any],
    *,
    summary_checkpoint: Optional[Path] = None,
    plan_checkpoint: Optional[Path] = None,
    spec_checkpoint: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Compare DeckIR text against available paper parse checkpoints."""
    if not any([summary_checkpoint, plan_checkpoint, spec_checkpoint]):
        return None
    profile = build_checkpoint_profile(
        summary_checkpoint=summary_checkpoint,
        plan_checkpoint=plan_checkpoint,
        spec_checkpoint=spec_checkpoint,
    )
    deck_text = _deck_text(deck_ir)
    deck_tokens = set(_tokens(deck_text))
    key_terms = profile.get("key_terms", [])
    covered_terms = [term for term in key_terms if term in deck_tokens or term in deck_text]

    title_matches = _phrase_coverage(profile.get("slide_titles", []), deck_text)
    section_matches = _phrase_coverage(profile.get("sections", []), deck_text)
    figure_matches = _phrase_coverage(profile.get("figure_refs", []), deck_text)
    table_matches = _phrase_coverage(profile.get("table_refs", []), deck_text)
    metric_matches = _phrase_coverage(profile.get("metric_refs", []), deck_text)
    evidence_matches = _phrase_coverage(profile.get("evidence_refs", []), deck_text)

    return {
        "schema_version": "checkpoint_deck_alignment.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_checkpoints": profile.get("source_checkpoints", {}),
        "deck_label": deck_ir.get("source", {}).get("label", ""),
        "profile": {
            "key_term_count": len(key_terms),
            "slide_title_count": len(profile.get("slide_titles", [])),
            "section_count": len(profile.get("sections", [])),
            "figure_ref_count": len(profile.get("figure_refs", [])),
            "table_ref_count": len(profile.get("table_refs", [])),
            "metric_ref_count": len(profile.get("metric_refs", [])),
        },
        "coverage": {
            "key_term_coverage": _ratio(len(covered_terms), len(key_terms)),
            "slide_title_coverage": title_matches["coverage"],
            "section_coverage": section_matches["coverage"],
            "figure_ref_coverage": figure_matches["coverage"],
            "table_ref_coverage": table_matches["coverage"],
            "metric_ref_coverage": metric_matches["coverage"],
            "evidence_ref_coverage": evidence_matches["coverage"],
        },
        "matches": {
            "covered_key_terms": covered_terms[:60],
            "missing_key_terms": [term for term in key_terms if term not in covered_terms][:60],
            "slide_titles": title_matches,
            "sections": section_matches,
            "figures": figure_matches,
            "tables": table_matches,
            "metrics": metric_matches,
            "evidence": evidence_matches,
        },
    }


def build_checkpoint_profile(
    *,
    summary_checkpoint: Optional[Path] = None,
    plan_checkpoint: Optional[Path] = None,
    spec_checkpoint: Optional[Path] = None,
) -> Dict[str, Any]:
    """Extract source-neutral alignment targets from parse checkpoints."""
    summary_data = _load_json(summary_checkpoint) if summary_checkpoint else {}
    plan_data = _load_json(plan_checkpoint) if plan_checkpoint else {}
    spec_data = _load_json(spec_checkpoint) if spec_checkpoint else {}

    plan_slides = _plan_slides(plan_data)
    spec_slides = _spec_slides(spec_data)
    summary_content = summary_data.get("content", {}) if isinstance(summary_data, dict) else {}

    titles = _unique(
        [slide.get("title", "") for slide in plan_slides]
        + [slide.get("title", "") for slide in spec_slides]
    )
    sections = _unique(
        [slide.get("section", "") for slide in plan_slides]
        + [slide.get("section_label", "") for slide in spec_slides]
    )
    figures = _figure_refs(summary_content, spec_slides)
    tables = _table_refs(summary_content, spec_slides)
    metrics = _metric_refs(spec_slides)
    evidence = _unique(figures + tables + metrics)

    keyword_source_text = " ".join(
        titles
        + sections
        + [slide.get("content", "") for slide in plan_slides]
        + [slide.get("takeaway", "") for slide in spec_slides]
        + [point for slide in spec_slides for point in _slide_point_texts(slide)]
        + [str(summary_content.get(key, ""))[:6000] for key in ("motivation", "solution", "conclusion")]
    )
    key_terms = _top_keywords(keyword_source_text, limit=90)
    return {
        "schema_version": "checkpoint_alignment_profile.v0",
        "source_checkpoints": {
            "summary": str(summary_checkpoint) if summary_checkpoint else "",
            "plan": str(plan_checkpoint) if plan_checkpoint else "",
            "slide_spec": str(spec_checkpoint) if spec_checkpoint else "",
        },
        "key_terms": key_terms,
        "slide_titles": titles,
        "sections": sections,
        "figure_refs": figures,
        "table_refs": tables,
        "metric_refs": metrics,
        "evidence_refs": evidence,
    }


def _plan_slides(plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    plan = plan_data.get("plan", {}) if isinstance(plan_data, dict) else {}
    slides = plan.get("sections", []) if isinstance(plan, dict) else []
    return [slide for slide in slides if isinstance(slide, dict)]


def _spec_slides(spec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    slides = spec_data.get("slides", []) if isinstance(spec_data, dict) else []
    return [slide for slide in slides if isinstance(slide, dict)]


def _figure_refs(summary_content: Dict[str, Any], spec_slides: Sequence[Dict[str, Any]]) -> List[str]:
    refs: List[str] = []
    for item in _asset_items(summary_content.get("figures", "")):
        refs.extend([item.get("id", ""), item.get("caption", "")])
    for slide in spec_slides:
        for block in slide.get("image_blocks", []) or []:
            if isinstance(block, dict):
                refs.extend([block.get("title", ""), block.get("caption", ""), block.get("placeholder_text", "")])
    return _clean_reference_list(refs)


def _table_refs(summary_content: Dict[str, Any], spec_slides: Sequence[Dict[str, Any]]) -> List[str]:
    refs: List[str] = []
    for item in _asset_items(summary_content.get("tables", "")):
        refs.extend([item.get("id", ""), item.get("caption", ""), item.get("title", "")])
    for slide in spec_slides:
        for block in slide.get("table_blocks", []) or []:
            if isinstance(block, dict):
                refs.extend([block.get("title", ""), block.get("caption", "")])
    return _clean_reference_list(refs)


def _metric_refs(spec_slides: Sequence[Dict[str, Any]]) -> List[str]:
    refs: List[str] = []
    for slide in spec_slides:
        for block in slide.get("metric_blocks", []) or []:
            if isinstance(block, dict):
                refs.extend([block.get("label", ""), block.get("value", ""), block.get("note", "")])
    return _clean_reference_list(refs)


def _asset_items(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, dict):
        for key in ("figures", "tables", "items"):
            items = value.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _slide_point_texts(slide: Dict[str, Any]) -> List[str]:
    texts: List[str] = []
    for block in slide.get("text_blocks", []) or []:
        if isinstance(block, dict):
            texts.extend([block.get("text", ""), block.get("claim", ""), block.get("detail", ""), block.get("evidence", "")])
    return texts


def _phrase_coverage(phrases: Sequence[str], deck_text: str) -> Dict[str, Any]:
    cleaned = [_clean_text(phrase) for phrase in phrases if _clean_text(phrase)]
    matches = []
    misses = []
    deck_tokens = set(_tokens(deck_text))
    for phrase in cleaned:
        phrase_tokens = [token for token in _tokens(phrase) if token not in STOPWORDS]
        if not phrase_tokens:
            continue
        direct = phrase in deck_text
        overlap = len([token for token in phrase_tokens if token in deck_tokens]) / max(1, len(set(phrase_tokens)))
        if direct or overlap >= 0.42:
            matches.append({"phrase": phrase[:120], "token_overlap": round(overlap, 3), "direct": direct})
        else:
            misses.append({"phrase": phrase[:120], "token_overlap": round(overlap, 3)})
    total = len(matches) + len(misses)
    return {
        "coverage": _ratio(len(matches), total),
        "matched_count": len(matches),
        "total_count": total,
        "matched": matches[:30],
        "missing": misses[:30],
    }


def _deck_text(deck_ir: Dict[str, Any]) -> str:
    texts: List[str] = []
    for slide in deck_ir.get("slides", []) or []:
        for obj in slide.get("objects", []) or []:
            if obj.get("text"):
                texts.append(str(obj.get("text", "")))
        text_model = slide.get("text", {})
        for key in ("title_candidates", "body_blocks", "caption_candidates"):
            texts.extend(str(item) for item in text_model.get(key, []) or [])
    return _clean_text(" ".join(texts))


def _top_keywords(text: str, limit: int) -> List[str]:
    counts = Counter(_tokens(text))
    items = []
    for token, count in counts.most_common(limit * 4):
        if token in STOPWORDS or len(token) < 4 or token.isdigit():
            continue
        if count < 2 and len(items) >= limit // 2:
            continue
        items.append(token)
        if len(items) >= limit:
            break
    return items


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}|\d+(?:\.\d+)?%?", str(text or "").lower())


def _clean_reference_list(values: Sequence[Any]) -> List[str]:
    return _unique([str(value) for value in values if _meaningful_reference(value)])


def _meaningful_reference(value: Any) -> bool:
    text = _clean_text(str(value or ""))
    if len(text) < 3:
        return False
    if text.startswith("![]("):
        return False
    return True


def _unique(values: Sequence[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 3)


def _clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _load_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path:
        return {}
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
