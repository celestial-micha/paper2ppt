# Hybrid Style Proposal Benchmark 下一阶段计划书

日期：2026-07-01

## 当前状态提示

截至 2026-07-02，本计划已从主线降级为历史路线与对照材料。04/05/06 的价值在于说明旧 autonomous style proposal 的边界：它能提供探索样本，也能通过 bounded repair 降低一部分低风险问题，但不能替代 template-level seed strategist 和 universal PPT benchmark。

当前主线请以以下文档为准：

```text
docs/ppt_master_universal_benchmark_upgrade_plan.zh-CN.md
docs/ppt_master_seed_pipeline_integration_plan.zh-CN.md
docs/universal_ppt_benchmark_v0_report.zh-CN.md
docs/three_seed_styles_openai_gpt5_report.zh-CN.md
```

本文件仍保留，用于解释为什么 frozen references 不能被新 proposal route 当作模板，以及为什么需要记录 autonomous / assisted / human-tuned 的不同等级。

本文档接住 `blind_rectangular_research_board` 晋升为 `golden_baseline2` 后的新阶段目标：把三套 human-tuned golden references 冻结起来，然后让系统在**不读取完整 golden 模板**的情况下，生成三个新 PPT 款式并通过 benchmark / repair / human feedback 评估它。

2026-07-01 面试前调整：三个新款式不再全部要求 fully autonomous。为避免临面试前步子过大，采用更稳的 hybrid 方案：

```text
1 assisted seed scaffold route
+ 2 autonomous free proposal routes
```

其中 assisted seed route 允许 Codex 先给一个非常基础、未成熟、未复用 golden0/1/2 的视觉脚手架；系统随后必须通过同一套 benchmark loop 迭代和修正。剩下两条 route 仍然是完全自由 proposal，只能用论文解析内容、抽象设计原语和 badcase registry。

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

但它们不应该再作为下一阶段新风格实验的输入模板。下一阶段要回答的问题不是“golden2 能不能继续套到新论文”，而是：

```text
在冻结 golden0/1/2 的前提下，
系统能不能从一个弱 assisted seed 或两个自由 proposal 出发，
再通过 benchmark repair loop 把它迭代到可用？
```

## 1. 为什么需要 Design Primitives Library，但不能给完整模板

用户提出的担忧是对的：完全不给任何审美先验，系统可能生成空、散、弱的页面；但如果直接给成熟模板，系统又会退化成“把内容塞进别人的模板”。

因此下一阶段采用双轨路线：

```text
允许：抽象 design primitives library
允许：一条 Codex-provided weak seed scaffold route
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

### 1.2 Codex seed scaffold 的边界

`assisted_seed_scaffold` route 允许 Codex 在 smoke test 开始时提供一个很基础的初始款式雏形，但它必须满足：

- 只能定义粗粒度画布、页面角色、容器类型、基础配色、初始 renderer 参数；
- 不能复用 `academic`、`golden_baseline1`、`golden_baseline2` 的完整页面骨架；
- 不能复制三套 golden reference 的 PPTX、style contract 或 layout grammar；
- 不能一步到位做成成熟模板；
- 必须输出 `seed_scaffold_contract.json` 和 `seed_authoring_note.md`，说明它只是 weak scaffold；
- 必须进入同样的 `iter0 -> audit -> repair -> rerender -> compare` loop；
- benchmark 统计时标记为 `L3.5_assisted_seed_scaffold_repair`，不能和 fully autonomous route 混在一起。

面试时可以这样解释：

> 我们把系统能力拆成层级。短期为了让实验稳定，我们允许一条 Codex 给初始弱脚手架的路线；但这个脚手架不是完整模板，也不能读取三套 golden。真正被评估的是 benchmark 能不能把这个粗糙雏形自动迭代得更好。与此同时，我们保留两条完全自由 proposal route，用来探索更高自主度。

### 1.3 禁止输入

无论 assisted seed 还是 autonomous free proposal，在生成新风格时都不得读取：

- `academic` 的完整 layout grammar；
- `golden_baseline1` 的 rounded proof-panel style contract；
- `golden_baseline2` 的 straight-rectangle research-board style contract；
- 三套 golden PPTX 当作模板；
- 从 golden references 直接抽出的页面布局参数。

### 1.4 面试口径

可以这样讲：

> 我们不是让模型从真空里凭空审美，也不是套模板。我们给它抽象设计原语，例如网格、字体层级、容器形状、proof-object 类型和约束，但不给完整 golden 模板。为了面试前实验稳定，我们保留一条 assisted seed scaffold route，由 Codex 给一个弱脚手架；另外两条 route 仍然自由 proposal。成熟模板只作为 frozen reference 和 evaluation baseline，不作为 proposal 输入。

## 2. Style Proposal / Seed Agent 设计

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

每个新风格 route 必须输出：

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

在一篇新论文 smoke test 中，系统同时生成三条新风格实验 route：

```text
assisted_seed_scaffold_style: Codex 给一个弱初始脚手架，benchmark loop 负责迭代
autonomous_style_proposal_a: 系统自由提出第一套新 style_contract + layout grammar
autonomous_style_proposal_b: 系统自由提出第二套新 style_contract + layout grammar
```

这些名字只是 route 类型，不是固定模板。三条新风格在 contact sheet 上应该明显不同，且都不复制 golden0/1/2。`assisted_seed_scaffold_style` 可以由 Codex 提供初始视觉雏形，但它必须是弱脚手架，并且必须通过 benchmark loop 才能变成可展示结果。

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
| `L3.5_assisted_seed_scaffold_repair` | Codex 给弱初始脚手架，系统用 benchmark loop 自动迭代 |
| `L4_autonomous_style_proposal_and_repair` | 系统自主提出风格并完成 bounded repair loop |

golden2 应诚实标为 `L2` 到 `L3` 之间，而不是 `L4`。下一阶段新论文的 assisted seed route 标为 `L3.5`，两条 autonomous free routes 才是冲击 `L4` 的实验。

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
| `04_assisted_seed_scaffold_style` | Codex weak seed + benchmark repair | 禁止读取 golden0/1/2 完整模板 |
| `05_autonomous_style_proposal_a` | autonomous free proposal | 禁止读取 golden0/1/2 完整模板 |
| `06_autonomous_style_proposal_b` | autonomous free proposal | 禁止读取 golden0/1/2 完整模板 |

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

assisted seed route 额外保存：

```text
seed_scaffold_contract.json
seed_authoring_note.md
design_primitives_used.json
forbidden_reference_attestation.json
```

autonomous free route 额外保存：

```text
style_contract.json
layout_grammar.json
renderer_parameters.json
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
- 三条 frozen reference route 不能被新风格 route 污染；
- assisted seed route 有 `seed_scaffold_contract.json`、`seed_authoring_note.md` 和 forbidden-reference attestation；
- 两条 autonomous free route 都有 style_contract、layout grammar、novelty report 和 forbidden-reference attestation；
- 三条新风格 route 至少一条在 3 轮内清掉 high / medium findings；
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
- assisted seed route 与 autonomous free route 的 iter0 -> iterN badcase 下降曲线；
- human feedback effort 是否下降；
- 哪些规则从 human feedback 晋升为 auto-detect / auto-repair；
- 三套 golden references、一条 assisted seed route、两条 autonomous free routes 的 style similarity / novelty 对比。

## 8. Benchmark / 代码实现顺序

### Phase A：文档与 registry

1. 冻结 golden2；
2. 更新 style registry；
3. 更新 benchmark recording schema；
4. 更新 machine-readable benchmark JSON；
5. 写入 autonomous style proposal policy。

### Phase B：Runner 扩展

1. 四路 runner 升级为 sixway runner 或 generalized multi-route runner；
2. 增加 `assisted_seed_scaffold` route；
3. 增加 `style_proposal_agent`；
4. 增加 `design_primitives_library`；
5. 增加 forbidden-reference attestation；
6. 增加 `max_iterations` / `patience` stop condition。

### Phase C：Audit / repair 扩展

1. 完成 `table_exceeds_container_bounds` 的 global correctness 检测；
2. 完成 `image_underutilized_in_wide_panel` 的 style-scoped 检测；
3. 完成 `metric_improved_visual_regressed` 的 repair-risk 记录；
4. 将 visual/human review packet 标准化为所有 autonomous route 输出；
5. 将 assisted seed 的 seed scaffold、repair curve 和 human outcome 纳入同一统计；
6. 增加 human feedback effort 统计。

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
Codex老师，我们继续 Paper2Slides-main 下一阶段：hybrid style proposal benchmark。

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
  4. assisted seed scaffold style
  5. autonomous style proposal A
  6. autonomous style proposal B
- assisted seed route 可以由 Codex 先给一个非常基础、未成熟的视觉脚手架，但不能读取或复制 golden0/1/2 完整模板、style contract、layout grammar 或 PPTX。
- autonomous style proposal 只能使用论文解析内容、设计约束、抽象 design primitives library 和 badcase registry，不能读取 golden0/1/2 完整模板或 PPTX。
- repair loop 至少支持 2-3 轮，连续两轮无改善或触发 style/human risk 后停止。

请先不要急着跑五篇论文。
先检查这篇新论文是否从未解析过，再给出 six-route smoke 执行计划和需要改动的 runner/audit 文件范围。今天先以稳定面试叙事为主，不要把三条新风格都强行做成 fully autonomous。
```
## 2026-07-02 补充：外部 PPT 项目吸收层

在 GPT-5 System Card six-way smoke 后，本计划新增一层 external style brief，用来吸收外部 PPT 项目的工程与视觉经验，但不让外部项目直接替代 Paper2Slides 的 benchmark。

本轮评审了两个项目：

- `hugohe3/ppt-master`：重点借鉴 spec lock、project pipeline、template architecture、preview/checker/export 质量链路，以及“最终 PPTX 必须保持原生可编辑对象”的工程目标。
- `op7418/guizang-ppt-skill`：重点借鉴 Swiss locked-mode、layout registry、单一 accent 色、标题左上纪律、图片 slot 绑定和 validator gate。

已生成的参考样稿位于：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/deliverables/
```

新增文件：

```text
07_ppt_master_inspired_native.pptx
08_guizang_swiss_inspired_native.pptx
08_guizang_swiss_inspired_html/index.html
```

计划调整：

1. route 04-06 可读取 external style brief，但不得读取 golden0/1/2 的完整 PPTX、完整 style contract 或 layout grammar。
2. external style brief 必须被降维成 `style_contract`、`layout_registry`、`design_primitives`、`validator_rules` 四类资产。
3. 每个新外部风格先生成 7-8 页 visual probe，覆盖 cover、comparison、structure diagram、metric ledger、evidence/image hero、closing，再决定是否扩展为完整 24 页论文 deck。
4. 新增指标：native editability、layout diversity、evidence density、typography risk、baseline similarity、human pick/reject/borrow notes。
5. HTML/browser preview 可以作为视觉实验室，但正式 benchmark 交付仍以可编辑 PPTX 为主。

详细评审与执行建议见：

```text
docs/openai_gpt5_external_ppt_project_review_plan.zh-CN.md
```
## 2026-07-02 决策修订：抛开归藏主线，转向 PPT Master-style seed pipeline

GPT-5 System Card six-way smoke 的人工复盘结论更新如下：

- 历史 route 04 `assisted_seed_scaffold_style` 是 Codex 先给弱脚手架的路线，暂不继续作为主线模板。
- 历史 route 05 `autonomous_style_proposal_a` 可归档为对照。
- 历史 route 06 `autonomous_style_proposal_b` 保留，因为它有继续调到好看的潜力。
- `07_ppt_master_inspired_native.pptx` 的视觉效果和工程思想更贴近下一阶段目标。
- `08_guizang_swiss_inspired_*` 作为规则型视觉参考归档，当前不作为主线。

下一阶段不再把“随机给一个初步款式，然后靠 bounded repair 局部修”作为默认路线。新的主线是：

```text
parse-once paper checkpoint
 -> PPT Master-style strategist
 -> seed_template_package
 -> 7-8 page visual probe
 -> template gate
 -> full deck generation
 -> template-level repair + page-level repair
 -> human feedback packet
 -> benchmark report
```

推荐新 six-route 对照：

```text
01 academic frozen reference
02 golden1 frozen reference
03 golden2 frozen reference
04 retained_autonomous_b_control
05 ppt_master_seed_probe
06 ppt_master_seed_full_repair
```

Route 06 历史下降曲线记录：

```text
total findings: 136 -> 112 -> 112, -17.6%
high severity: 26 -> 25 -> 25, -3.8%
medium severity: 34 -> 35 -> 35, +2.9%
low severity: 76 -> 52 -> 52, -31.6%
typography dimension: 88 -> 64 -> 64, -27.3%
copy_fitting problem type: 37 -> 27 -> 27, -27.0%
near_text_capacity rule: 16 -> 7 -> 7, -56.3%
```

这说明现有 bounded repair 能消化一部分文本容量/字号类问题，但不能解决模板起点、全局审美、版式骨架和中高风险视觉问题。因此，后续 benchmark 重点从 page-level local repair 前移到 seed-template generation + template-level gate。

详细计划见：

```text
docs/ppt_master_seed_pipeline_integration_plan.zh-CN.md
```
## 2026-07-02 主计划入口更新

更完整的新计划已经单独整理为：

```text
docs/ppt_master_universal_benchmark_upgrade_plan.zh-CN.md
```

该计划是下一阶段主入口。它把目标从“继续多生成几套内部模板”改为“构建可评多来源 PPT 的通用 benchmark，并用 ppt-master 的 strategist/spec_lock/seed-template 思想补强初稿生成阶段”。

第一步不是直接重写 renderer，而是先做：

```text
DeckIR + external PPTX intake + universal scorecard v0
```

只有当历史 06、07_ppt_master_inspired_native.pptx、academic frozen baseline 都能进入同一套 DeckIR 和 scorecard 后，再推进 seed strategist、visual probe、template gate、full deck repair。
