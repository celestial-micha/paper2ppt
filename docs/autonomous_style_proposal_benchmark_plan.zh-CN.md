# Autonomous Style Proposal Benchmark 下一阶段计划书

日期：2026-07-01

本文档接住 `blind_rectangular_research_board` 晋升为 `golden_baseline2` 后的新阶段目标：把三套 human-tuned golden references 冻结起来，然后让系统在**不读取完整模板**的情况下，基于论文解析内容、抽象设计原语和 badcase registry，自主提出新的 PPT 款式，并通过多轮 benchmark / repair / human feedback 评估它。

## 0. 当前结论

项目现在有三套人工参与迭代后的 frozen references：

```text
golden_baseline0: academic
golden_baseline1: golden_baseline1_from_scratch_warm_academic
golden_baseline2: golden_baseline2_blind_rectangular_research_board
```

这三套模板都可以用于：

- 生产可用的对照输出；
- 回归测试；
- 风格隔离验证；
- human-in-the-loop 经验展示。

但它们不应该再作为下一阶段 autonomous style proposal 的输入模板。下一阶段要回答的问题不是“golden2 能不能继续套到新论文”，而是：

```text
只给论文解析内容、设计约束、抽象设计原语和 badcase registry，
系统能不能自己提出新的 style_contract + layout grammar，
再通过 benchmark repair loop 把它迭代到可用？
```

## 1. 为什么需要 Design Primitives Library，但不能给完整模板

用户提出的担忧是对的：完全不给任何审美先验，系统可能生成空、散、弱的页面；但如果直接给成熟模板，系统又会退化成“把内容塞进别人的模板”。

因此下一阶段采用中间路线：

```text
允许：抽象 design primitives library
禁止：完整模板、成熟布局策略、golden style_contract
```

### 1.1 允许使用的抽象原语

`design_primitives_library` 只提供低层积木和约束，不提供整套页面答案。例如：

| primitive | 说明 |
| --- | --- |
| canvas grids | 12-column grid、asymmetric grid、evidence band grid |
| type scale | title / claim / support / caption 的字号范围 |
| color roles | background、ink、muted accent、warning accent、evidence accent |
| container shapes | rectangle、rounded panel、rule line、rail、band、chip |
| proof object families | figure fit、native table、metric card、evidence note、pipeline step |
| composition verbs | split、stack、rail、band、mosaic、focus、compare |
| constraints | avoid overflow、preserve aspect、center caption、keep table readable |

这些原语相当于“设计词汇表”，不是模板。

### 1.2 禁止输入

Autonomous style proposal agent 在生成新风格时不得读取：

- `academic` 的完整 layout grammar；
- `golden_baseline1` 的 rounded proof-panel style contract；
- `golden_baseline2` 的 straight-rectangle research-board style contract；
- 三套 golden PPTX 当作模板；
- 从 golden references 直接抽出的页面布局参数。

### 1.3 面试口径

可以这样讲：

> 我们不是让模型从真空里凭空审美，也不是套模板。我们给它抽象设计原语，例如网格、字体层级、容器形状、proof-object 类型和约束，但不给完整模板。这样系统有基本设计语言，却必须自己决定 style_contract、layout grammar 和页面节奏。成熟模板只作为 frozen reference 和 evaluation baseline，不作为 proposal 输入。

## 2. Style Proposal Agent 设计

### 2.1 输入

```json
{
  "paper_content_inventory": "由 summary / plan / slide_spec / figures / tables / metrics 汇总",
  "deck_requirements": {
    "task_type": "academic_paper_reading_deck",
    "required_roles": ["title", "agenda", "section", "content", "closing"],
    "slide_budget": "由论文长度和用户约束决定"
  },
  "design_primitives_library": "抽象原语，不含完整模板",
  "badcase_registry": "global rules + style-scoped rules 的 id/trigger/repair policy",
  "forbidden_reference_policy": "不得读取 golden0/1/2 完整 style contract 或 PPTX"
}
```

### 2.2 输出

每个 proposal 必须输出：

```json
{
  "proposal_id": "auto_style_01",
  "style_contract": {
    "style_intent": "这套风格想让听众产生什么阅读感",
    "layout_grammar": "页面角色到布局族的映射",
    "proof_object_grammar": "figure/table/metric/text evidence 怎么进入页面",
    "typography_system": "字号层级和字重",
    "palette_roles": "颜色角色，不是随意 palette",
    "container_rules": "容器形状、padding、caption、label 规则",
    "forbidden_patterns": "主动避开哪些 golden-like skeleton"
  },
  "renderer_parameters": {
    "grid": "...",
    "spacing": "...",
    "image_fit_policy": "...",
    "table_fit_policy": "...",
    "text_fit_policy": "..."
  },
  "novelty_statement": {
    "why_not_academic": "...",
    "why_not_golden1": "...",
    "why_not_golden2": "..."
  }
}
```

### 2.3 三个新风格的生成方式

在一篇新论文 smoke test 中，系统同时生成三条 autonomous proposal route：

```text
auto_style_01: structured evidence map
auto_style_02: editorial research narrative
auto_style_03: data/proof ledger
```

这些名字只是 proposal seed，不是固定模板。agent 可以根据论文内容调整，但必须保证三条 proposal 在 contact sheet 上明显不同，且都不复制 golden0/1/2。

## 3. 多轮 Repair Loop

当前系统之前常见 `iter0 -> iter1`，下一阶段要升级成真正 bounded loop：

```text
iter0 draft
 -> audit
 -> rank badcases
 -> repair top 1-3
 -> rerender
 -> rescore
 -> compare with previous iteration
 -> stop or continue
```

### 3.1 最大轮数和停止条件

建议初始参数：

```text
max_iterations: 3
patience: 2 consecutive non-improving iterations
top_k_repairs_per_iteration: 1-3
```

停止条件：

- high / medium findings 已清零；
- 连续两轮没有改善；
- 修复会违反当前 style_contract；
- 修复会触发 `metric_improved_visual_regressed` 或 human reject；
- 剩余问题只适合人工评审，不适合自动改。

### 3.2 Improvement 不只看 finding count

每轮比较必须同时看：

| 指标 | 含义 |
| --- | --- |
| `finding_delta` | high / medium / low 数量变化 |
| `dimension_score_delta` | content、layout、typography、component_fit、style、repair_risk |
| `new_findings_introduced` | 修复是否带来新问题 |
| `style_contract_violations` | 是否偏离 proposal 自己定义的语法 |
| `human_outcome` | accepted / rejected / tradeoff / overcorrection |

如果机器指标变好但人工认为变差，记录为：

```text
metric_improved_visual_regressed
```

这类样本不能被算作成功 repair，而应进入下一轮 scoped rule。

## 4. Human Feedback Effort 如何量化

golden2 的经验说明：人工参与越来越少也能把模板调好，这本身应该被量化，而不是被隐藏。

建议新增 `human_feedback_effort`：

```json
{
  "human_feedback_turns": 4,
  "human_marked_slides": [4, 5, 6, 8, 12, 21, 14, 23, 24],
  "manual_file_edits_by_human": 0,
  "manual_ppt_edits_by_human": 0,
  "codex_direct_renderer_edits": 4,
  "new_rules_added": 8,
  "auto_detectable_after_rule_conversion": 7,
  "human_outcomes_recorded": ["accepted", "rejected", "tradeoff_review"],
  "autonomy_level": "L2_human_feedback_guided_repair"
}
```

### 4.1 Autonomy Level

| level | 含义 |
| --- | --- |
| `L0_manual_template` | 人手工做 PPT 或完整模板 |
| `L1_agent_renders_given_template` | 系统只把内容放入给定模板 |
| `L2_human_feedback_guided_repair` | 系统自动渲染和修复，但人类指出主要 badcase |
| `L3_benchmark_guided_multi_round_repair` | 系统根据已有 benchmark 规则多轮自修，人类只做抽检 |
| `L4_autonomous_style_proposal_and_repair` | 系统自主提出风格并完成 bounded repair loop |

golden2 应诚实标为 `L2` 到 `L3` 之间，而不是 `L4`。下一阶段新论文的 autonomous proposal route 才是冲击 `L4` 的实验。

### 4.2 面试口径

> 我们没有把 human-in-the-loop 当成黑箱。每轮人工反馈都会记录涉及页面、问题类型、转成的 rule、是否可自动检测、是否可自动修复，以及下一轮人工参与是否减少。这样可以量化“人类参与越来越少”的趋势，而不是只说系统变聪明了。

## 5. 外部系统 PDF 如何评测

用户提供的两个外部 PDF 暴露了一个重要对比维度：别人的系统可能生成的是 PDF、图片页或 LaTeX Beamer，而不是可编辑 PPTX。

下一阶段 benchmark 应增加 `external_artifact_eval`，但它不是为了贬低其他系统，而是把“论文转 PPT”拆成更真实的交付指标。

| 维度 | 我们的 PPTX | 图片页 PDF | LaTeX/Beamer PDF |
| --- | --- | --- | --- |
| `artifact_success` | 是否生成成功 | 是否生成成功 | 是否生成成功 |
| `text_extractability_score` | 原生文本可读 | 可能为 0 | 通常较高 |
| `native_editability_score` | PowerPoint 可直接改 | 低 | 需要改 LaTeX |
| `source_asset_reuse_score` | 是否复用论文 figure/table | 可检测 | 可检测但常缺失 |
| `content_traceability_score` | 是否能映射到 source evidence | 可通过 checkpoint 追踪 | 取决于生成系统 |
| `human_edit_cost_score` | 用户改错成本 | 高 | 中到高 |
| `visual_polish_score` | 可人工/规则评审 | 可截图评审 | 可截图评审 |

用户上传的样例可以作为比较案例：

- `案例/20260417_203056/slides.pdf`：每页是 512x512 raster image，几乎不可编辑，文本抽取能力弱。
- `案例/presentation.pdf`：更像 Beamer/LaTeX，文本可抽取但视觉和 PowerPoint 可编辑性弱。

这说明我们的 benchmark 不应只统计“是否生成 PDF 成功”，而应统计：

```text
artifact success
+ native editability
+ text extractability
+ source asset reuse
+ content traceability
+ human correction cost
```

## 6. 一篇新论文 Smoke Test

用户接下来会提供一篇之前没有解析过的新论文。第一阶段只用这一篇做 smoke。

### 6.1 运行路线

同一篇论文只解析一次，复用 checkpoint，生成六路：

| route | 类型 | 是否允许读取 golden style |
| --- | --- | --- |
| `01_academic_frozen_reference` | golden0 frozen reference | 可以读取 academic |
| `02_golden1_frozen_reference` | golden1 frozen reference | 可以读取 golden1 |
| `03_golden2_frozen_reference` | golden2 frozen reference | 可以读取 golden2 |
| `04_auto_style_proposal_a` | autonomous proposal | 禁止读取 golden0/1/2 完整模板 |
| `05_auto_style_proposal_b` | autonomous proposal | 禁止读取 golden0/1/2 完整模板 |
| `06_auto_style_proposal_c` | autonomous proposal | 禁止读取 golden0/1/2 完整模板 |

### 6.2 输出产物

run 级别：

```text
manifest.json
style_proposal_policy.json
comparison_report.md
score_curve.csv
artifact_index.csv
human_feedback_effort.csv
external_artifact_eval.json
sixway_result.json
```

route 级别：

```text
slides.pptx
speaker_script.md
speaker_script_audit.json
nonvisual_audit.json
repair_log.json
style_drift_report.json
visual_human_review_packet.zh-CN.md
```

autonomous route 额外保存：

```text
style_contract.json
design_primitives_used.json
novelty_report.json
forbidden_reference_attestation.json
```

iteration 级别：

```text
iterations/iter_00/...
iterations/iter_01/...
iterations/iter_02/...
iterations/iter_03/...
```

### 6.3 Smoke 通过标准

- 六路都成功生成 `slides.pptx` 和 `speaker_script.md`；
- 三条 frozen reference route 不能被 autonomous repair 污染；
- 三条 autonomous route 都有 style_contract 和 forbidden-reference attestation；
- autonomous route 至少一条在 3 轮内清掉 high / medium findings；
- 每轮 score curve 和 repair log 完整；
- 人工抽检能指出 accepted / rejected / tradeoff，并写回 badcase registry。

## 7. 五篇论文量化测试

一篇 smoke 没问题后，扩展到 5 篇论文，必要时再到 10 篇。

### 7.1 论文选择

五篇论文应覆盖不同内容形状：

- figure-heavy；
- table-heavy；
- metric-heavy；
- method / system diagram-heavy；
- text-heavy theory or survey。

### 7.2 统计指标

每篇论文、每条 route、每个 iteration 记录：

```text
artifact_success
speaker_script_success
high / medium / low findings
dimension scores
repair_count
repair_success_count
repair_rejected_count
new_findings_introduced
human_feedback_turns
human_marked_slide_count
rules_added
autonomy_level
native_editability_score
source_asset_reuse_score
```

### 7.3 量化展示

最终报告建议展示：

- 六路总览表；
- 每篇论文的 score curve；
- autonomous route 的 iter0 -> iterN badcase 下降曲线；
- human feedback effort 是否下降；
- 哪些规则从 human feedback 晋升为 auto-detect / auto-repair；
- 三套 golden references 和三条 autonomous proposals 的 style similarity / novelty 对比。

## 8. Benchmark / 代码实现顺序

### Phase A：文档与 registry

1. 冻结 golden2；
2. 更新 style registry；
3. 更新 benchmark recording schema；
4. 更新 machine-readable benchmark JSON；
5. 写入 autonomous style proposal policy。

### Phase B：Runner 扩展

1. 四路 runner 升级为 sixway runner 或 generalized multi-route runner；
2. 增加 `style_proposal_agent`；
3. 增加 `design_primitives_library`；
4. 增加 forbidden-reference attestation；
5. 增加 `max_iterations` / `patience` stop condition。

### Phase C：Audit / repair 扩展

1. 完成 `table_exceeds_container_bounds` 的 global correctness 检测；
2. 完成 `image_underutilized_in_wide_panel` 的 style-scoped 检测；
3. 完成 `metric_improved_visual_regressed` 的 repair-risk 记录；
4. 将 visual/human review packet 标准化为所有 autonomous route 输出；
5. 增加 human feedback effort 统计。

### Phase D：Smoke + five-paper benchmark

1. 用户提供一篇新论文；
2. 跑六路 smoke；
3. 人工 review；
4. 修 schema / runner / rules；
5. 扩展到五篇；
6. 生成最终量化报告。

## 9. 新窗口启动语

用户下一个窗口给新论文时，建议直接发送：

```text
Codex老师，我们继续 Paper2Slides-main 下一阶段：autonomous style proposal benchmark。

项目路径：
D:\coding\agent_paper_to_slider\Paper2Slides-main

请先阅读：
1. docs/autonomous_style_proposal_benchmark_plan.zh-CN.md
2. docs/style_registry.zh-CN.md
3. docs/benchmark_recording_schema.zh-CN.md
4. docs/style_aware_multistage_benchmark_plan.zh-CN.md
5. benchmarks/from_scratch_human_feedback_benchmark.json
6. paper2slides/benchmark/nonvisual_audit.py
7. paper2slides/benchmark/fourway.py

当前状态：
- academic、golden_baseline1、golden_baseline2 都已经 frozen。
- golden2 是 human-tuned blind_rectangular_research_board，不要把它当成 autonomous style proposal 的证明。
- 下一阶段要用我提供的新论文先做一篇 smoke test。
- 同一篇论文只解析一次，然后生成六路：
  1. academic frozen reference
  2. golden_baseline1 frozen reference
  3. golden_baseline2 frozen reference
  4. autonomous style proposal A
  5. autonomous style proposal B
  6. autonomous style proposal C
- autonomous style proposal 只能使用论文解析内容、设计约束、抽象 design primitives library 和 badcase registry，不能读取 golden0/1/2 完整模板或 PPTX。
- repair loop 至少支持 2-3 轮，连续两轮无改善或触发 style/human risk 后停止。

请先不要急着跑五篇论文。
先检查这篇新论文是否从未解析过，再给出 six-route smoke 执行计划和需要改动的 runner/audit 文件范围。
```
