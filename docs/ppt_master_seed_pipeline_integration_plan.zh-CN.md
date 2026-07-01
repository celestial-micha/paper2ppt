# PPT Master Seed Pipeline 融入 Paper2Slides 的计划

日期：2026-07-02

本计划回应 GPT-5 System Card six-way smoke 后的新判断：

- 历史 04 `assisted_seed_scaffold_style` 是 Codex 先给的弱脚手架，不再作为主线模板。
- 历史 05 `autonomous_style_proposal_a` 可归档为对照，不再重点投入。
- 历史 06 `autonomous_style_proposal_b` 保留，因为它有继续调好看的潜力。
- `07_ppt_master_inspired_native.pptx` 作为新的 seed-template 方向参考。
- `08_guizang_swiss_inspired_*` 暂时搁置；它规则稳定，但不是当前最优主线。

## 1. Route 06 Badcase 下降曲线

数据来源：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/routes/06_autonomous_style_proposal_b/repair_log.json
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/score_curve.csv
```

### 1.1 按严重度

| iteration | total findings | high | medium | low | note |
|---:|---:|---:|---:|---:|---|
| 0 | 136 | 26 | 34 | 76 | initial autonomous proposal B |
| 1 | 112 | 25 | 35 | 52 | after bounded repair |
| 2 | 112 | 25 | 35 | 52 | plateau |

从 iter0 到 iter2：

| metric | delta | relative change |
|---|---:|---:|
| total findings | -24 | -17.6% |
| high severity | -1 | -3.8% |
| medium severity | +1 | +2.9% |
| low severity | -24 | -31.6% |

解释：当前自动返修主要消化了低风险文本容量/字号舒适区问题；中高风险布局、视觉平衡、组件比例仍未被有效修复。

### 1.2 按 problem type

| problem type | iter0 | iter2 | delta | relative change |
|---|---:|---:|---:|---:|
| typography | 72 | 57 | -15 | -20.8% |
| copy_fitting | 37 | 27 | -10 | -27.0% |
| optical_balance | 16 | 16 | 0 | 0.0% |
| geometry | 5 | 5 | 0 | 0.0% |
| content_semantics | 6 | 7 | +1 | +16.7% |

### 1.3 按 benchmark dimension

| dimension | iter0 | iter2 | delta | relative change |
|---|---:|---:|---:|---:|
| typography | 88 | 64 | -24 | -27.3% |
| layout | 26 | 25 | -1 | -3.8% |
| style | 10 | 10 | 0 | 0.0% |
| component_fit | 6 | 6 | 0 | 0.0% |
| content | 6 | 7 | +1 | +16.7% |

### 1.4 按 rule type

| rule | iter0 | iter2 | delta | relative change |
|---|---:|---:|---:|---:|
| below_ideal_font_band | 31 | 16 | -15 | -48.4% |
| near_text_capacity | 16 | 7 | -9 | -56.3% |
| estimated_text_overflow | 21 | 20 | -1 | -4.8% |
| low_font_size | 40 | 40 | 0 | 0.0% |
| text_exceeds_container_bounds | 5 | 5 | 0 | 0.0% |
| container_stack_off_balance | 5 | 5 | 0 | 0.0% |
| figure_panel_aspect_mismatch | 6 | 6 | 0 | 0.0% |
| table_view_label_missing | 5 | 5 | 0 | 0.0% |
| weak_fragment_point_heading | 6 | 7 | +1 | +16.7% |

面试口径：06 不是“已经修好了”的成功样本，而是一个更真实、更能展示 benchmark 价值的样本。它证明现有 bounded repair 能降低文本容量和字号类问题，但也暴露出系统缺少 seed-template strategist、全局视觉预案和模板级返修。

## 2. 当前系统缺的那一步

Paper2Slides 之前的路线是：

```text
parse paper once
 -> generate PPTX from existing or weak style
 -> nonvisual audit
 -> bounded local repair
 -> human feedback
```

缺口在于：生成完整 PPT 前，没有一个足够强的“初步模板生成 / seed-template proposal”阶段。

这导致 repair loop 经常只能做局部修修补补，例如压缩文案、调字号、修少量 overflow；但如果初始视觉骨架不够强，它很难把一套不成熟风格修成真正漂亮的 deck。

## 3. 从 PPT Master 借鉴什么

`ppt-master` 的价值不只是 07 这类视觉结果，而是它把“初稿生成”拆成了严格阶段：

```text
Source Document
 -> Create Project
 -> optional Template
 -> Strategist
 -> Image Generator
 -> Executor Live Preview
 -> Quality Check
 -> Post-processing
 -> Export
```

可转译到 Paper2Slides 的关键点：

1. `spec_lock`：在生成页面前冻结颜色、字体、页面节奏、图表模板、图片槽位和禁用规则。
2. `Strategist`：先决定叙事、受众、页面角色、页面节奏和 proof object，而不是直接生成 24 页 PPT。
3. `template architecture`：把风格资产拆成 brand / layout / deck 三层。
4. `page-by-page executor`：每页生成前重读 spec lock，避免长 deck 后半段风格漂移。
5. `live preview + quality checker`：把视觉预览和质量检查放到导出前，而不是导出后人工找问题。
6. `native editability`：最终 PPTX 必须是可编辑对象，不是图片式输出。

## 4. 新的 Paper2Slides pipeline 设计

目标不是照搬 `ppt-master`，而是把它的 seed-template strategist 融进现有 benchmark。

### Stage A: Paper Content Inventory

复用当前 parse-once checkpoint：

- summary
- plan
- slide spec
- figure / table / metric inventory
- evidence highlights

输出：

```text
paper_content_inventory.json
```

### Stage B: PPT Master-style Strategist

新增一个 strategist 阶段，只生成模板策略，不生成完整 PPT。

输出：

```text
seed_template_brief.md
seed_template_contract.json
```

字段建议：

- deck thesis
- target audience
- page count and rhythm
- page role roster
- evidence object roster
- preferred visual language
- forbidden visual habits
- native editability constraints
- known badcase guardrails

### Stage C: Seed Template Package

参考 `ppt-master` 的 brand / layout / deck 分层，生成机器可读模板包：

```text
seed_template_package/
  design_spec.md
  spec_lock.json
  brand.json
  layout_registry.json
  component_primitives.json
  page_role_roster.json
  validator_rules.json
```

其中：

- `brand.json`：颜色、字体、图标、语气。
- `layout_registry.json`：cover、agenda、evidence wall、metric ledger、method stack、risk map、table view、closing 等页面类型。
- `component_primitives.json`：原生 PPTX 组件，必须可编辑。
- `validator_rules.json`：从历史 badcase 转成模板级 gate。

### Stage D: 7-8 页 Visual Probe

先生成一个小样，而不是直接 24 页。

必须覆盖：

- cover
- central thesis
- comparison
- method/system diagram
- metric ledger
- evidence/table/figure page
- risk or mitigation map
- closing

输出：

```text
visual_probe.pptx
visual_probe_audit.json
visual_probe_scorecard.json
```

### Stage E: Template Gate

probe 先过 gate，过不了就修模板，不急着铺满整篇论文。

Gate 维度：

- native editability
- layout diversity
- typography comfort
- evidence density
- style consistency
- baseline similarity / novelty
- visual balance
- component fit
- repair risk

### Stage F: Full Deck Generation

只有 seed template 过 gate 后，才生成完整 24 页 deck。

输出：

```text
slides.pptx
speaker_script.md
nonvisual_audit.json
visual_probe_trace.json
```

### Stage G: Two-level Repair

先修模板，再修单页：

1. Template-level repair：改 layout registry、字号等级、页面节奏、组件比例。
2. Page-level repair：修 overflow、局部拥挤、图表/表格/figure 槽位。

这一步是现有 bounded repair 的升级点。

### Stage H: Human Feedback Data Flywheel

人类反馈不只写一句“好看/不好看”，而是结构化写回：

```text
human_feedback_packet.json
```

字段：

- accepted_style_traits
- rejected_style_traits
- badcase_to_rule_candidates
- visual_examples_to_keep
- visual_examples_to_avoid
- resume_ready_metrics

## 5. 下一轮 route 调整

旧路线：

```text
01 academic frozen
02 golden1 frozen
03 golden2 frozen
04 assisted seed scaffold
05 autonomous proposal A
06 autonomous proposal B
```

建议新路线：

```text
01 academic frozen reference
02 golden1 frozen reference
03 golden2 frozen reference
04 retained_autonomous_b_control      # 保留历史 06，用作对照
05 ppt_master_seed_probe              # 新 seed-template 小样
06 ppt_master_seed_full_repair        # 用 seed-template 生成完整 deck 并进入 repair loop
```

这样能回答两个问题：

1. 06 这个有潜力的旧风格，继续修能修到什么程度？
2. 引入 PPT Master-style seed-template pipeline 后，是否比旧 autonomous proposal 更容易起步、更容易修好？

## 6. 十天推进节奏

| day | target | output |
|---|---|---|
| D1 | 简历先投递，项目计划冻结 | resume v1 + 本计划 |
| D2 | 实现 `seed_template_contract` schema | JSON schema + sample |
| D3 | 实现 strategist 生成 `seed_template_package` | package generator |
| D4 | 生成 7-8 页 visual probe | probe PPTX + audit |
| D5 | 接入 template gate | scorecard |
| D6 | 用通过 gate 的 seed 生成 24 页 deck | full deck iter0 |
| D7 | 两级 repair：template first, page second | iter1/iter2 curve |
| D8 | 结构化 human feedback packet | accepted/rejected traits |
| D9 | 汇总 benchmark 报告 | before/after metrics |
| D10 | 简历 v2 / 面试讲稿 | interview story |

## 7. 简历可用结论

当前可以稳妥写：

- 已构建 parse-once multi-route benchmark，可同一论文生成并对比 frozen references、assisted seed、autonomous proposal。
- 已把 badcase 拆成 severity + dimension + rule type 三层，覆盖 content、layout、typography、component-fit、style、repair-risk。
- 在 route 06 上，bounded repair 使 total findings 从 136 降到 112，下降 17.6%；其中 typography dimension 从 88 降到 64，下降 27.3%；near text capacity 从 16 降到 7，下降 56.3%。
- 同时识别出高/中风险问题 plateau：high 26 -> 25，medium 34 -> 35，说明下一步需要 seed-template strategist 和 template-level repair，而不是只做局部返修。

不建议现在写：

- “已完整集成 PPT Master pipeline”。
- “已实现 RLHF”。除非真的训练了模型，否则写 Human Feedback / HITL / feedback-to-rule 更准确。
