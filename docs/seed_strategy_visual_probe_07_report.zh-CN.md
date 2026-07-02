# 07 Seed Strategist 与 Visual Probe Spec 阶段报告

日期：2026-07-02

本阶段承接 `07_ppt_master_inspired_native.pptx` 的 seed-template package。目标不是改 renderer，也不是直接铺满 24 页完整 deck，而是先把论文 checkpoint、07 模板约束和 proof object 库融合成一个可 gate 的 strategist contract，再产出 7-8 页 visual probe spec。

## 1. 新增代码

新增模块：

```text
paper2slides/benchmark/seed_pipeline/
  strategist.py
  visual_probe.py
```

新增 CLI：

```text
python -m paper2slides.benchmark seed-strategist
python -m paper2slides.benchmark visual-probe-spec
```

这两个命令都只读本地 checkpoint / seed package，不调用模型、不渲染 PPTX、不修改 renderer。

## 2. 本轮产物

Strategist 输出目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/seed_strategy_07/
```

包含：

```text
content_inventory.json
seed_template_contract.json
seed_template_brief.md
```

Visual probe spec 输出目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/visual_probe_spec_07/
```

包含：

```text
visual_probe_spec.json
visual_probe_gate.json
visual_probe_brief.md
```

## 3. Seed Strategist 做了什么

`seed_template_contract.json` 把三层信息合并成机器可读 contract：

- 论文内容：复用 parse-once checkpoint 中的 summary、plan、slide spec、figure/table/metric inventory。
- 叙事策略：固定 8 页 probe arc，包括 cover、central thesis、method stack、metric ledger、evidence wall、figure/table focus、risk map、closing。
- 模板约束：复用 07 package 中的 palette、typography、layout registry、component primitives、forbidden patterns 和 template gate。

关键约束：

```text
slide_budget: 24
probe_slides: 8
first_deliverable: visual_probe_spec
renderer_policy: do not render full deck until visual probe passes template gate
```

Proof object roster 当前统计：

```text
figures: 30
tables: 27
metrics: 10
```

这一步的意义是把“论文内容要讲什么”和“07 风格能怎么讲”分开锁定。后续 renderer 只应该执行 contract，而不是在页面级临时猜测整套风格。

## 4. Visual Probe Spec 做了什么

`visual_probe_spec.json` 生成了 8 页 spec-only probe：

| slide | role | title | layout candidate |
| --- | --- | --- | --- |
| probe_01 | cover | GPT-5 System Card: Safety, Evaluations, and Mitigations | cover_01 |
| probe_02 | central_thesis | Central Thesis | content_02 |
| probe_03 | method_stack | Safety Stack | content_02 |
| probe_04 | metric_ledger | Evaluation Ledger | metric_04 |
| probe_05 | evidence_wall | Evidence Wall | content_02 |
| probe_06 | figure_or_table_focus | Source Evidence Focus | content_02 |
| probe_07 | risk_map | Residual Risk Map | content_02 |
| probe_08 | closing_takeaway | Takeaway | content_02 |

每页 spec 都包含：

- role / title / claim / support
- proof_object
- layout_candidate
- component_primitives
- text_budget_words
- gate_notes

这一步仍然没有生成 PPTX。它是 renderer 之前的检查点，方便在进入视觉实现前先确认角色覆盖、证据覆盖和模板约束是否合理。

## 5. Gate 结果

Seed template package gate：

```text
status: pass_with_warnings
passed: 8
warnings: 2
failed: 0
```

warnings：

```text
content_fidelity_probe_only
human_preference_pending
```

Visual probe gate：

```text
status: pass_with_warnings
```

通过项：

| check | observed | expected |
| --- | --- | --- |
| probe_slide_count | 8 | 7-8 slides |
| required_roles | all required roles present | selected probe roles |
| proof_object_coverage | 6 proof-bearing slides | at least 4 |
| template_package_gate_not_failed | pass_with_warnings | not fail |
| renderer_not_invoked | spec-only | spec-only |

warnings：

```text
source_template_package_has_warnings
human_feedback_required_before_default_promotion
```

结论：spec 可以进入 renderer prototype，但不能晋升为默认模板，也不能直接扩展为 full deck。下一步必须先补 human feedback packet，把 07 的 accepted / rejected / borrowable traits 明确下来。

## 6. 为什么这一步是正确的下一阶段

前一阶段 universal benchmark 已经证明：

- academic frozen 和 06 是内容覆盖高的完整 deck，但 typography / layout 明显弱。
- 07 是内容覆盖低的 8 页 visual probe，但 editability、typography、layout、rhythm 更强。

因此当前正确动作不是让 07 直接取代 academic，也不是继续对 06 做局部 repair，而是把 07 降维成：

- seed template package
- strategist contract
- visual probe spec
- template gate 输入
- human feedback packet 输入

这样后续可以在不大改 renderer 的前提下，逐步升级为：

```text
checkpoint
 -> content inventory
 -> seed_template_contract
 -> visual_probe_spec
 -> visual_probe renderer prototype
 -> universal scorecard
 -> human feedback packet
 -> template gate v1
 -> full deck generation
```

## 7. 下一阶段建议

下一阶段建议先做 `human_feedback_packet.v0`，不要马上生成完整 PPT：

1. 从 07 package 和 visual probe spec 生成一个待人工确认的 feedback packet。
2. 字段包括 accepted_style_traits、rejected_style_traits、borrowable_traits、rule_candidates、promotion_blockers。
3. 把 `human_preference_pending` 从 scorecard warning 升级为可追踪 artifact。
4. template gate 读取该 packet 后，才能决定 07 是否可作为默认 seed template。

这会把“好看但主观”的判断变成可记录、可复用、可回归的 benchmark 资产。
