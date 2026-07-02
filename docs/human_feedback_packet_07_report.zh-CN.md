# 07 Human Feedback Packet v0 阶段报告

日期：2026-07-02

本阶段承接 `seed_strategy_07` 和 `visual_probe_spec_07`。目标是把 `human_preference_pending` 从一个 scorecard warning 升级成可追踪 artifact：系统可以预填建议，但不能假装已经获得人类确认。

## 1. 新增代码

新增模块：

```text
paper2slides/benchmark/seed_pipeline/human_feedback_packet.py
```

新增 CLI：

```text
python -m paper2slides.benchmark human-feedback-packet
```

公共导出新增：

```text
build_human_feedback_packet
```

该命令读取：

- `visual_probe_spec.json`
- `visual_probe_gate.json`
- `seed_template_package_07/`
- 可选 `universal_scorecard.v0.json`
- 可选旧 human-feedback registry：`benchmarks/from_scratch_human_feedback_benchmark.json`

它不渲染 PPTX、不调用模型、不修改 renderer。

## 2. 本轮产物

输出目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/human_feedback_packet_07/
```

包含：

```text
human_feedback_packet.json
human_feedback_packet.md
```

当前 packet 状态：

```text
feedback_status: pending_human_review
template_id: ppt_master_inspired_seed_v0
visual_probe_status: pass_with_warnings
template_gate_status: pass_with_warnings
scorecard_overall: 66.3
```

## 3. Packet v0 Schema

核心字段：

```json
{
  "schema_version": "human_feedback_packet.v0",
  "feedback_status": "pending_human_review",
  "subject": {},
  "review_prompts": [],
  "suggested_accepted_style_traits": [],
  "suggested_rejected_style_traits": [],
  "suggested_borrowable_traits": [],
  "promotion_blockers": [],
  "badcase_to_rule_candidates": [],
  "human_review_slots": {},
  "registry_context": {},
  "source_gate_context": {}
}
```

设计原则：

- `suggested_*` 是系统预填建议，不等于人类接受。
- `human_review_slots` 保持空白，等待人工写入 accepted / rejected / borrowable traits。
- `promotion_blockers` 决定模板是否能晋升为默认 seed。
- `badcase_to_rule_candidates` 是后续 template gate v1 / visual rule registry 的候选输入。

## 4. 当前建议 Traits

系统预填的 accepted trait 建议：

```text
editorial_data_reporting_language
native_editable_primitives
clear_type_hierarchy
role_based_layout_registry
restrained_palette_with_single_accent
```

系统预填的 rejected trait 建议来自 `spec_lock.forbidden_patterns`：

```text
full_slide_raster_screenshot
generic_bullet_only_page
unlabeled_proof_object
table_rendered_as_unreadable_image
repeating_one_layout_signature_across_a_full_deck
expanding_a_visual_probe_into_full_deck_without_content_coverage_gate
```

系统预填的 borrowable trait 建议：

```text
probe_role_arc
layout_candidates
native_component_primitives
layout_repair_affordances
```

这些都仍然是候选，不是最终结论。

## 5. 当前晋升阻塞项

`promotion_blockers` 当前有 3 个：

| blocker | meaning |
| --- | --- |
| `template_gate_warnings` | seed package 仍有 warning，不能直接默认晋升。 |
| `human_preference_pending` | 还没有人工确认偏好。 |
| `content_fidelity_probe_only` | 07 是 visual probe，不是 full-deck content proof。 |

因此 07 当前状态应写作：

```text
renderer prototype ready
default promotion blocked
full deck expansion blocked until content gate + human review
```

## 6. Rule Candidates

当前生成 11 个候选规则：

```text
source_template_package_has_warnings
human_feedback_required_before_default_promotion
template_gate_warnings
human_preference_pending
content_fidelity_probe_only
full_slide_raster_screenshot
generic_bullet_only_page
unlabeled_proof_object
table_rendered_as_unreadable_image
repeating_one_layout_signature_across_a_full_deck
expanding_a_visual_probe_into_full_deck_without_content_coverage_gate
```

其中前 5 个是 `human_gated`，后 6 个是 `detect_only`。这符合当前阶段策略：先记录和 gate，不自动修审美。

## 7. 与旧 Human Feedback Registry 的关系

packet 复用了旧 registry 的摘要：

```text
benchmark_track: from_scratch_paper_reading_ppt
accepted_reference: rough_draft_v5
badcase_count: 57
current_phase_policy: non_visual_only_no_screenshots_no_vision_model
```

这意味着新 07 路线没有另起一套“主观审美打分”，而是接入既有 feedback-to-rule 体系：

- 继续采用 metadata-first / nonvisual-first。
- 不默认截图。
- 不默认调用视觉模型。
- 人类偏好被结构化成规则候选，而不是一句“好看/不好看”。

## 8. 下一阶段建议

下一步仍然不建议直接生成完整 24 页 deck。更稳的顺序是：

1. 人工审阅 `human_feedback_packet.json`。
2. 把可接受 trait 写入 `human_review_slots.accepted_style_traits`。
3. 把不希望复用的视觉习惯写入 `rejected_style_traits`。
4. 把 11 个 rule candidates 分成 `auto`、`detect_only`、`human_gated`。
5. 将结果升级为 `template_gate.v1` 或 `visual_rule_registry.v0`。
6. 只有当 visual probe gate、content gate 和 human feedback gate 都不阻塞时，再进入 renderer prototype 或 full deck。

这样 07 的价值会被保留为可迁移的 seed 经验，而不是被误用成一个未经校准的默认模板。
