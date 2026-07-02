"""Create visual rule registries and promotion gates from feedback packets."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


REVIEWED_STATUSES = {"reviewed", "human_reviewed", "accepted", "approved"}


def build_visual_rule_registry(feedback_packet: Dict[str, Any], *, label: str = "") -> Dict[str, Any]:
    """Convert a human-feedback packet into a rule registry draft."""
    rules = [_registry_rule(item) for item in feedback_packet.get("badcase_to_rule_candidates", []) or []]
    traits = {
        "accepted": _trait_entries(
            feedback_packet.get("suggested_accepted_style_traits", []) or [],
            default_state="suggested_pending_human_review",
        ),
        "rejected": _trait_entries(
            feedback_packet.get("suggested_rejected_style_traits", []) or [],
            default_state="active_package_policy",
        ),
        "borrowable": _trait_entries(
            feedback_packet.get("suggested_borrowable_traits", []) or [],
            default_state="suggested_pending_human_review",
        ),
    }
    active_rules = [rule for rule in rules if rule.get("activation_status") == "active_package_policy"]
    pending_rules = [rule for rule in rules if rule.get("activation_status") == "pending_human_review"]
    return {
        "schema_version": "visual_rule_registry.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "label": label or feedback_packet.get("label", ""),
        "source_packet": {
            "schema_version": feedback_packet.get("schema_version", ""),
            "feedback_status": feedback_packet.get("feedback_status", ""),
            "template_id": feedback_packet.get("subject", {}).get("template_id", ""),
            "paper_title": feedback_packet.get("subject", {}).get("paper_title", ""),
            "visual_probe_status": feedback_packet.get("subject", {}).get("visual_probe_status", ""),
            "template_gate_status": feedback_packet.get("subject", {}).get("template_gate_status", ""),
        },
        "policy": {
            "default_promotion_requires_reviewed_packet": True,
            "visual_preference_auto_repair_allowed": False,
            "non_visual_first": _non_visual_first(feedback_packet),
            "pending_traits_are_not_style_contract": True,
        },
        "traits": traits,
        "rules": rules,
        "summary": {
            "total_rules": len(rules),
            "active_package_policy_rules": len(active_rules),
            "pending_human_review_rules": len(pending_rules),
            "suggested_accepted_traits": len(traits["accepted"]),
            "suggested_rejected_traits": len(traits["rejected"]),
            "suggested_borrowable_traits": len(traits["borrowable"]),
        },
    }


def evaluate_promotion_gate(feedback_packet: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate whether the seed template can be promoted."""
    subject = feedback_packet.get("subject", {}) or {}
    blockers = feedback_packet.get("promotion_blockers", []) or []
    reviewed = feedback_packet.get("feedback_status", "") in REVIEWED_STATUSES
    blocker_ids = {item.get("id", "") for item in blockers}
    checks = [
        _check(
            "feedback_packet_present",
            feedback_packet.get("schema_version") == "human_feedback_packet.v0",
            feedback_packet.get("schema_version", ""),
            "human_feedback_packet.v0",
            blocking=True,
        ),
        _check(
            "visual_probe_not_failed",
            subject.get("visual_probe_status") != "fail",
            subject.get("visual_probe_status", ""),
            "not fail",
            blocking=True,
        ),
        _check(
            "template_gate_not_failed",
            subject.get("template_gate_status") != "fail",
            subject.get("template_gate_status", ""),
            "not fail",
            blocking=True,
        ),
        _check(
            "feedback_reviewed",
            reviewed,
            feedback_packet.get("feedback_status", ""),
            sorted(REVIEWED_STATUSES),
            blocking=True,
        ),
        _check(
            "no_promotion_blockers",
            len(blockers) == 0,
            [item.get("id", "") for item in blockers],
            [],
            blocking=True,
        ),
        _check(
            "content_gate_cleared",
            "content_fidelity_probe_only" not in blocker_ids,
            "content_fidelity_probe_only" if "content_fidelity_probe_only" in blocker_ids else "clear",
            "clear",
            blocking=True,
        ),
        _check(
            "rule_candidates_classified",
            all(rule.get("activation_status") for rule in registry.get("rules", []) or []),
            len(registry.get("rules", []) or []),
            "all rules classified",
            blocking=False,
        ),
        _check(
            "detect_only_guardrails_available",
            registry.get("summary", {}).get("active_package_policy_rules", 0) > 0,
            registry.get("summary", {}).get("active_package_policy_rules", 0),
            "> 0",
            blocking=False,
        ),
    ]
    blocking_failures = [check for check in checks if check["blocking"] and check["status"] == "fail"]
    if blocking_failures and not reviewed:
        status = "blocked_pending_human_review"
    elif blocking_failures:
        status = "blocked"
    else:
        status = "pass"

    renderer_allowed = subject.get("visual_probe_status") != "fail" and subject.get("template_gate_status") != "fail"
    default_allowed = status == "pass"
    full_deck_allowed = default_allowed and "content_fidelity_probe_only" not in blocker_ids
    return {
        "schema_version": "promotion_gate.v0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "decision": {
            "renderer_prototype_allowed": renderer_allowed,
            "default_template_promotion_allowed": default_allowed,
            "full_deck_expansion_allowed": full_deck_allowed,
            "template_gate_v1_ready": True,
        },
        "checks": checks,
        "blocking_failures": [check["id"] for check in blocking_failures],
        "recommendation": _recommendation(status, renderer_allowed, blocker_ids),
    }


def write_visual_rule_registry_artifacts(packet_path: Path, output_dir: Path, *, label: str = "") -> Dict[str, str]:
    """Write visual_rule_registry.json, promotion_gate.json, and a brief."""
    packet = _read_json(packet_path)
    registry = build_visual_rule_registry(packet, label=label)
    gate = evaluate_promotion_gate(packet, registry)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "visual_rule_registry": str(output_dir / "visual_rule_registry.json"),
        "promotion_gate": str(output_dir / "promotion_gate.json"),
        "visual_rule_registry_brief": str(output_dir / "visual_rule_registry.md"),
    }
    _write_json(output_dir / "visual_rule_registry.json", registry)
    _write_json(output_dir / "promotion_gate.json", gate)
    (output_dir / "visual_rule_registry.md").write_text(_render_registry_brief(registry, gate), encoding="utf-8")
    return paths


def _registry_rule(candidate: Dict[str, Any]) -> Dict[str, Any]:
    source = candidate.get("source", "")
    repair_mode = candidate.get("repair_mode", "")
    if source == "forbidden_pattern" and repair_mode == "detect_only":
        activation_status = "active_package_policy"
        review_requirement = "review before changing enforcement level"
    else:
        activation_status = "pending_human_review"
        review_requirement = "human review required before promotion"
    return {
        "id": candidate.get("id", ""),
        "dimension": candidate.get("dimension", ""),
        "severity": candidate.get("severity", ""),
        "scope": candidate.get("scope", ""),
        "repair_mode": repair_mode,
        "source": source,
        "activation_status": activation_status,
        "review_requirement": review_requirement,
        "human_outcome": candidate.get("human_outcome", "pending_review"),
        "promotion_target": candidate.get("promotion_target", "template_gate_v1"),
        "description": candidate.get("description", ""),
    }


def _trait_entries(items: List[Dict[str, Any]], *, default_state: str) -> List[Dict[str, Any]]:
    return [
        {
            "id": item.get("id", ""),
            "source": item.get("source", ""),
            "review_state": default_state,
            "evidence": item.get("evidence"),
        }
        for item in items
        if item.get("id")
    ]


def _check(
    check_id: str,
    passed: bool,
    observed: Any,
    expected: Any,
    *,
    blocking: bool,
) -> Dict[str, Any]:
    return {
        "id": check_id,
        "status": "pass" if passed else "fail",
        "blocking": blocking,
        "observed": observed,
        "expected": expected,
    }


def _recommendation(status: str, renderer_allowed: bool, blocker_ids: set[str]) -> str:
    if status == "pass":
        return "Template can be promoted according to current gate."
    prefix = "Renderer prototype may proceed; " if renderer_allowed else "Renderer prototype is blocked; "
    if "content_fidelity_probe_only" in blocker_ids:
        return prefix + "default promotion and full-deck expansion remain blocked until human review and content gate pass."
    return prefix + "default promotion remains blocked until human review clears promotion blockers."


def _non_visual_first(packet: Dict[str, Any]) -> bool:
    policy = str(packet.get("registry_context", {}).get("current_phase_policy", ""))
    return "non_visual" in policy or "no_screenshots" in policy


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_registry_brief(registry: Dict[str, Any], gate: Dict[str, Any]) -> str:
    summary = registry.get("summary", {}) or {}
    decision = gate.get("decision", {}) or {}
    lines = [
        "# Visual Rule Registry",
        "",
        f"- Status: {gate.get('status', '')}",
        f"- Renderer prototype allowed: {decision.get('renderer_prototype_allowed')}",
        f"- Default template promotion allowed: {decision.get('default_template_promotion_allowed')}",
        f"- Full deck expansion allowed: {decision.get('full_deck_expansion_allowed')}",
        f"- Total rules: {summary.get('total_rules', 0)}",
        f"- Active package policy rules: {summary.get('active_package_policy_rules', 0)}",
        f"- Pending human review rules: {summary.get('pending_human_review_rules', 0)}",
        "",
        "## Blocking Failures",
        "",
        *[f"- {item}" for item in gate.get("blocking_failures", []) or []],
        "",
        "## Recommendation",
        "",
        gate.get("recommendation", ""),
        "",
    ]
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a visual rule registry and promotion gate from a feedback packet.")
    parser.add_argument("--packet", required=True, help="Path to human_feedback_packet.json")
    parser.add_argument("--output-dir", required=True, help="Directory for visual_rule_registry artifacts")
    parser.add_argument("--label", default="", help="Optional registry label")
    args = parser.parse_args(argv)

    paths = write_visual_rule_registry_artifacts(Path(args.packet), Path(args.output_dir), label=args.label)
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
