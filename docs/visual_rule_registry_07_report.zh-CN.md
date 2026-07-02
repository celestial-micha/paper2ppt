# 07 Visual Rule Registry v0 与 Promotion Gate 阶段报告

日期：2026-07-02

本阶段承接 `human_feedback_packet_07`。目标是把 pending feedback packet 转成机器可读的 `visual_rule_registry.v0`，并生成一个明确的 promotion gate，防止 07 在未经过人工偏好确认和内容 gate 前被误晋升为默认模板。

## 1. 新增代码

新增模块：

```text
paper2slides/benchmark/seed_pipeline/visual_rule_registry.py
```

新增 CLI：

```text
python -m paper2slides.benchmark visual-rule-registry
```

公共导出新增：

```text
build_visual_rule_registry
evaluate_promotion_gate
```

该命令只读取 `human_feedback_packet.json`，不渲染 PPTX、不调用模型、不修改 renderer。

## 2. 本轮产物

输出目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/visual_rule_registry_07/
```

包含：

```text
visual_rule_registry.json
promotion_gate.json
visual_rule_registry.md
```

## 3. Visual Rule Registry v0 结果

当前 registry 摘要：

```text
total_rules: 11
active_package_policy_rules: 6
pending_human_review_rules: 5
suggested_accepted_traits: 5
suggested_rejected_traits: 6
suggested_borrowable_traits: 4
```

策略：

```text
default_promotion_requires_reviewed_packet: true
visual_preference_auto_repair_allowed: false
non_visual_first: true
pending_traits_are_not_style_contract: true
```

这意味着：

- 来自 `spec_lock.forbidden_patterns` 的 6 条规则可以作为 `active_package_policy` 的 detect-only guardrail。
- 和审美偏好、默认晋升相关的 5 条规则保持 `pending_human_review`。
- 系统可以记录、检测和阻塞，但不能自动宣布“这个风格已被人类接受”。

## 4. Promotion Gate 结果

`promotion_gate.json` 当前状态：

```text
status: blocked_pending_human_review
```

决策：

| decision | value |
| --- | --- |
| renderer_prototype_allowed | true |
| default_template_promotion_allowed | false |
| full_deck_expansion_allowed | false |
| template_gate_v1_ready | true |

阻塞检查：

```text
feedback_reviewed
no_promotion_blockers
content_gate_cleared
```

推荐语：

```text
Renderer prototype may proceed; default promotion and full-deck expansion remain blocked until human review and content gate pass.
```

## 5. 为什么允许 Renderer Prototype，但阻塞默认晋升

当前 07 已经满足几个工程条件：

- visual probe gate 没有失败。
- template package gate 没有失败。
- native editability、typography、layout rhythm 已经优于旧路线。
- forbidden-pattern guardrails 已经结构化。

因此可以进入受控 renderer prototype，验证 spec lock 和 layout registry 是否能实际产出 native PPTX。

但 07 仍不能默认晋升：

- `human_feedback_packet.feedback_status` 仍是 `pending_human_review`。
- `promotion_blockers` 仍包含 `template_gate_warnings`、`human_preference_pending`、`content_fidelity_probe_only`。
- 07 是 8 页 visual probe，不是 full-deck content proof。

这个 gate 正好把两件事分开：

```text
可以做工程原型
不可以默认推广
```

## 6. 与 Universal Benchmark 的关系

Universal scorecard 回答“07 为什么值得继续”：

- editability 高；
- typography 高；
- layout / rhythm 高；
- content fidelity 低但符合 visual probe 定位。

Visual rule registry 回答“07 怎么继续才不越界”：

- detect-only guardrails 可以先启用；
- human preference 必须保留 pending；
- default promotion 必须被 gate 阻塞；
- full deck expansion 必须等待 content gate。

二者结合后，benchmark 不再只给一个总分，而是能给出可执行决策。

## 7. 下一阶段建议

下一阶段可以进入一个非常小的 renderer prototype，但范围应保持受控：

1. 只渲染 `visual_probe_spec_07` 的 8 页，不生成 24 页 full deck。
2. renderer 必须读取 `spec_lock.json`、`layout_registry.json`、`component_primitives.json`。
3. 输出后重新跑 `universal-pptx-intake`、`nonvisual-audit`、`visual-rule-registry`。
4. 如果触发 active package policy，先修 spec/layout，不扩大到 full deck。
5. 只有当 human feedback packet 被人工确认、content gate 通过、promotion gate 解除阻塞，才考虑完整 deck。

这样下一步就能测试 PPT Master-style seed pipeline 的执行力，同时仍保持 benchmark 的边界干净。
