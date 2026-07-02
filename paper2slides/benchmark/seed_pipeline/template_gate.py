"""Template gate v0 for seed-template packages."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def evaluate_template_gate(
    deck_ir: Dict[str, Any],
    scorecard: Dict[str, Any],
    package: Dict[str, Any],
) -> Dict[str, Any]:
    """Evaluate whether a seed template is ready for a full-deck experiment."""
    rules = package.get("validator_rules", {})
    dims = scorecard.get("dimensions", {})
    summary = deck_ir.get("summary", {})
    role_counts = summary.get("role_counts", {})
    checks = []

    checks.append(
        _score_check(
            "native_editability",
            _dimension_score(dims, "editability"),
            float(rules.get("min_editability_score", 90.0)),
            "native PPTX editability must stay high",
        )
    )
    checks.append(
        _max_check(
            "raster_area_ratio",
            float(summary.get("raster_area_ratio", 0.0) or 0.0),
            float(rules.get("max_raster_area_ratio", 0.08)),
            "seed output should not depend on raster pages",
        )
    )
    checks.append(
        _score_check(
            "typography",
            _dimension_score(dims, "typography"),
            float(rules.get("min_typography_score", 60.0)),
            "probe typography should be comfortable before full-deck expansion",
        )
    )
    checks.append(
        _score_check(
            "layout_geometry",
            _dimension_score(dims, "layout_geometry"),
            float(rules.get("min_layout_geometry_score", 50.0)),
            "layout geometry must be above the first gate threshold",
        )
    )
    checks.append(
        _score_check(
            "visual_design_proxy",
            _dimension_score(dims, "visual_design"),
            float(rules.get("min_visual_design_proxy_score", 65.0)),
            "visual proxy must be strong enough to justify template extraction",
        )
    )
    checks.append(
        _score_check(
            "evidence_grounding_proxy",
            _dimension_score(dims, "evidence_grounding"),
            float(rules.get("min_evidence_grounding_proxy_score", 55.0)),
            "probe needs visible evidence/source signals",
        )
    )
    checks.append(
        _role_check(
            "required_probe_roles",
            role_counts,
            list(rules.get("required_probe_roles", ["cover", "content", "metric"])),
        )
    )
    checks.append(
        _min_check(
            "layout_signature_count",
            len(set(summary.get("layout_signatures", []) or [])),
            int(rules.get("min_layout_signature_count", 6)),
            "probe should demonstrate multiple page rhythms",
        )
    )

    content_score = _dimension_score(dims, "content_fidelity")
    if content_score is not None and content_score < float(rules.get("full_deck_content_min_score", 70.0)):
        checks.append(
            {
                "id": "content_fidelity_probe_only",
                "status": "warn",
                "observed": round(content_score, 1),
                "threshold": rules.get("full_deck_content_min_score", 70.0),
                "message": "content coverage is low because this is a visual probe, not a full paper deck",
            }
        )

    if dims.get("human_preference", {}).get("status") == "pending_human_feedback":
        checks.append(
            {
                "id": "human_preference_pending",
                "status": "warn",
                "observed": "pending_human_feedback",
                "threshold": "human review",
                "message": "template promotion still needs human accepted/rejected/borrowable trait feedback",
            }
        )

    failed = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warn"]
    if failed:
        status = "fail"
    elif warnings:
        status = "pass_with_warnings"
    else:
        status = "pass"

    return {
        "schema_version": "template_gate.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "template_id": package.get("provenance", {}).get("template_id", ""),
        "status": status,
        "checks": checks,
        "summary": {
            "passed": sum(1 for check in checks if check["status"] == "pass"),
            "warnings": len(warnings),
            "failed": len(failed),
        },
        "recommendation": _recommendation(status, failed, warnings),
    }


def _score_check(check_id: str, value: Any, threshold: float, message: str) -> Dict[str, Any]:
    if value is None:
        return {"id": check_id, "status": "warn", "observed": None, "threshold": threshold, "message": f"{message}; score unavailable"}
    observed = float(value)
    return {
        "id": check_id,
        "status": "pass" if observed >= threshold else "fail",
        "observed": round(observed, 1),
        "threshold": threshold,
        "message": message,
    }


def _min_check(check_id: str, value: int, threshold: int, message: str) -> Dict[str, Any]:
    return {
        "id": check_id,
        "status": "pass" if int(value) >= int(threshold) else "fail",
        "observed": int(value),
        "threshold": int(threshold),
        "message": message,
    }


def _max_check(check_id: str, value: float, threshold: float, message: str) -> Dict[str, Any]:
    return {
        "id": check_id,
        "status": "pass" if float(value) <= float(threshold) else "fail",
        "observed": round(float(value), 3),
        "threshold": float(threshold),
        "message": message,
    }


def _role_check(check_id: str, role_counts: Dict[str, Any], required: List[str]) -> Dict[str, Any]:
    missing = [role for role in required if int(role_counts.get(role, 0) or 0) <= 0]
    return {
        "id": check_id,
        "status": "pass" if not missing else "fail",
        "observed": role_counts,
        "threshold": required,
        "message": "probe must include required page-role signals",
        "missing": missing,
    }


def _dimension_score(dimensions: Dict[str, Any], name: str) -> Any:
    return dimensions.get(name, {}).get("score")


def _recommendation(status: str, failed: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> str:
    if status == "fail":
        failed_ids = ", ".join(check.get("id", "") for check in failed)
        return f"Do not expand to full deck until failed template checks are repaired: {failed_ids}."
    if warnings:
        warning_ids = ", ".join(check.get("id", "") for check in warnings)
        return f"Use as seed-template candidate, but collect human feedback and address warnings: {warning_ids}."
    return "Template candidate is ready for a controlled visual-probe to full-deck experiment."
