# Style-Aware Multi-Stage Benchmark 阶段计划书

日期：2026-06-30

本文档记录 Paper2Slides 下一阶段 benchmark 设计。当前目标不是继续手工打磨某一份 PPT，而是把现有的“badcase 数量下降曲线”升级为：

```text
多维度 eval
-> style-aware rule
-> auto repair trial
-> visual evidence packet
-> human approval / rejection
-> scoped benchmark rule
```

这条路线承认一个关键事实：PPT 质量不是单一 badcase count 能完全描述的。不同模板、组件形状、容器语法和图表类型，会改变同一个检测项的含义。比如 `figure_panel_aspect_mismatch` 在圆角 proof-panel 风格下可能是有效问题，但在直角矩形左右双栏风格下，右侧大图反而可能是更清晰、更好看的布局。

## 1. 当前阶段结论

已经完成：

- 单篇论文 fresh parse 四路 benchmark。
- 01 `academic_audit_only`。
- 02 `golden_baseline1_scoped`。
- 03 `academic_global_repair`。
- 04 `blind_experimental_loop`。
- 每条 route 保存 `slides.pptx`、`speaker_script.md`、`speaker_script_audit.json`、`nonvisual_audit.json`、`repair_log.json`、`style_drift_report.json`。
- 03 / 04 保存 iteration 级 PPT。
- 生成 `score_curve.csv`、`score_curve.svg`、badcase 前后对比、speaker audit、视觉 before/after PNG。
- 中英文报告和视觉人工复核包已保留。

暴露出的关键问题：

- 04 的 iter0 -> iter1 虽然降低了 metadata findings，但 slide06 等页面在人类看来可能被误修。
- 机器为了清除 `figure_panel_aspect_mismatch`，把原本右侧大图布局改成底部长条 evidence panel；但在当前直角矩形风格中，右侧大图可能更清晰、更符合视觉节奏。
- 因此不能把 badcase count 下降直接等价为 visual quality 提升。
- 需要新增 style-aware 和 human-review 机制，让系统知道“这个规则适用于哪种模板、哪种组件、哪种图表比例”。

## 2. 阶段目标

下一阶段目标：

```text
从 high/medium/low badcase count
升级到 multi-dimensional eval + style-aware repair loop
```

具体目标：

1. 定义多维评分，不再只统计 high / medium / low。
2. 为每个模板定义 `style_contract`，记录组件形状、容器语法、典型布局偏好。
3. 为每条 benchmark rule 增加 `scope`、`repair_mode`、`confidence` 和 `human_outcome`。
4. 将“误修”纳入 benchmark，而不是只记录“修复成功”。
5. 每次 repair trial 都生成视觉证据包，让人工可以批准、拒绝或标记 tradeoff。
6. 将 human feedback 反向沉淀为 scoped badcase 和回归测试。

## 3. 多维评分设计

早期只统计：

```text
high / medium / low finding count
```

下一阶段改成多维评分：

| 维度 | 说明 | 典型信号 |
| --- | --- | --- |
| `parse_handoff_score` | 论文解析结果是否足够支撑后续生成 | section 覆盖、figure/table 数量、evidence 引用、summary 完整度 |
| `content_fidelity_score` | PPT 是否忠实表达论文内容 | claim 是否有来源、指标是否有单位和上下文、是否幻觉 |
| `evidence_coverage_score` | 每页是否有 proof object | figure/table/metric/evidence card 覆盖 |
| `layout_safety_score` | 是否存在确定性排版错误 | overlap、overflow、出界、表格超过容器 |
| `typography_fit_score` | 字号、行距、文本容量是否合适 | low font、near capacity、estimated overflow |
| `component_fit_score` | 图、表、metric 和容器是否匹配 | 图片可读面积、表格容器高度、图表 aspect 与 panel 关系 |
| `style_consistency_score` | 是否遵守当前模板语法 | 直角/圆角、左右双栏/底栏、标题层级、留白节奏 |
| `visual_readability_score` | 人看是否清楚 | 图表大小、表格可读性、证据区是否过小 |
| `repair_risk_score` | 本次修复是否可能误修 | metric improved but visual regressed、style scope mismatch |
| `human_acceptance_score` | 人工最终接受度 | accepted、rejected、tradeoff、overcorrection |

建议报告中同时保留两种视图：

- **机器曲线**：finding count / severity / dimension score。
- **人工裁决**：accepted / rejected / tradeoff / overcorrection。

这样面试时可以说明：badcase count 是早期 machine signal，不是最终质量定义。

## 4. Rule Schema 设计

每条 badcase rule 不再只包含 `type` 和 `severity`，而是扩展为：

```json
{
  "id": "figure_panel_aspect_mismatch",
  "dimension": "component_fit",
  "severity": "medium",
  "scope": "style_aware",
  "style_scope": ["golden_baseline1_from_scratch_warm_academic"],
  "repair_mode": "auto_then_human_review",
  "confidence": 0.72,
  "machine_delta": {
    "before": 1,
    "after": 0
  },
  "human_outcome": "tradeoff_review",
  "visual_evidence": [
    "visual_compare/slide_06_before_after_human_review.png"
  ],
  "notes": "Metric improved, but current rectangular right-panel style may prefer the before layout."
}
```

关键字段：

| 字段 | 取值 | 作用 |
| --- | --- | --- |
| `dimension` | content / evidence / layout / typography / component_fit / style / repair_risk | 说明该 rule 属于哪类评测 |
| `severity` | high / medium / low | 风险等级 |
| `scope` | global / style_aware / experimental / human_feedback | 是否能跨模板使用 |
| `style_scope` | academic / golden_baseline1 / blind_rectangular 等 | 限定适用模板 |
| `repair_mode` | auto / suggest / auto_then_human_review / human_gated / detect_only | 决定修复权限 |
| `confidence` | 0.0-1.0 | 机器判断把握 |
| `human_outcome` | accepted / rejected / tradeoff_review / likely_overcorrection | 人工裁决 |

## 5. Repair Mode 分层

下一阶段不建议简单地把所有 style-aware repair 禁掉。更合理的策略是：机器可以先修，但修复是否成为“有效规则”，必须经过视觉证据和 human outcome。

| repair mode | 含义 | 适用场景 |
| --- | --- | --- |
| `auto` | 自动修复并默认接受 | 明确全局错误，如 table 超出容器、明显 overlap |
| `suggest` | 只给修复建议，不改 PPT | 风格不明、置信度低 |
| `auto_then_human_review` | 机器先试修，生成 before/after 证据，人工再批准或拒绝 | experimental route、style-aware layout |
| `human_gated` | 必须人工批准后才改 | golden baseline / golden_baseline1 中的审美或布局语法 |
| `detect_only` | 只检测，不修 | 新规则验证期 |

本阶段决策：

- 对 blind experimental，允许 `auto_then_human_review`。
- 对 original `academic` 和 `golden_baseline1`，默认更保守，style-specific rule 先 `detect_only` 或 `human_gated`。
- 如果机器修复后视觉不舒服，记录为 `likely_overcorrection` 或 `tradeoff_review`，不要算作 accepted repair。

## 6. Style Contract 设计

每个模板都需要声明自己的组件语法。当前建议：

```json
{
  "style_id": "blind_rectangular_research_board",
  "promotion_status": "experimental_candidate",
  "container_shape": "straight_rectangle",
  "container_padding_model": {
    "horizontal_in": 0.30,
    "vertical_in": 0.22,
    "space_efficiency": "high"
  },
  "preferred_layouts": {
    "moderately_wide_figure": "right_panel_large",
    "extremely_wide_figure": "bottom_band_if_readable",
    "tall_figure": "asymmetric_left_wide_or_right_narrow",
    "table": "container_fit_with_min_padding"
  },
  "protected_rhythm": [
    "straight rectangular left claim panel pairs cleanly with straight rectangular right evidence panel",
    "right-side large figure is preferred when it preserves readability"
  ]
}
```

关于第三种 style 的命名：

- 2026-06-30 时仍暂称 `blind_rectangular_research_board` experimental candidate。
- 2026-07-01 以后，经过 Deep Residual 多轮 human-in-the-loop 迭代，最终版已保存为：

```text
golden_baseline2_blind_rectangular_research_board
```

- 这个晋升是 frozen reference 晋升，不是 fully autonomous style proposal 的证明。
- 下一阶段要把 golden0/1/2 都作为 frozen reference 隔离起来；autonomous style proposal agent 不能读取三套 golden 的完整 PPTX、style contract 或 layout grammar。

## 7. 图像布局规则

### 7.1 宽图不应无脑下放

旧逻辑：

```text
宽图 -> 底部长条 panel
```

新逻辑：

```text
根据 style_contract + image aspect + readable area + container shape 决定
```

对于直角矩形风格：

- 中等宽图可以保留右侧大图布局。
- 只有非常宽的图，才考虑底部长条布局。
- 即使下放到底部，也必须检查图片实际可读面积。

建议初始阈值：

| 条件 | 策略 |
| --- | --- |
| image aspect < 2.3 | 优先右侧大图 |
| image aspect 2.3-3.2 | 比较右侧大图和底栏可读面积，进入 `auto_then_human_review` |
| image aspect > 3.2 | 可尝试底部长条，但必须满足 readable area 阈值 |

新增规则：

```text
image_underutilized_in_wide_panel
```

触发条件：

- wide panel 面积充足；
- 图片实际 bbox 只占 panel 面积很小；
- 周围留白过大；
- caption 或标签占用不成比例。

这个规则正好对应 slide06 iter1 的问题：底部长条明明很大，但图被放得很小。

### 7.2 高图需要非对称布局，但不能过度放大

slide27 的经验：

- 高图从右侧/普通 panel 变成更大的显示区域，方向是对的。
- 但直角矩形比圆角矩形更省空间，不需要像 golden_baseline1 那样把 panel 拉得过大。

新增规则：

```text
tall_figure_asymmetric_panel_fit
image_dominance_overcorrection
```

检测内容：

- 高图是否获得足够高度；
- 左右 panel 是否按图像方向非对称调整；
- 图片是否过度支配页面；
- claim/support 是否被压缩到不可读；
- 是否符合当前 style 的直角矩形节奏。

## 8. 表格容器规则

用户指出：有些页面表格高度超过了装载它的直角矩形高度。这个问题应列为 global correctness rule，因为它几乎不依赖 style 审美。

新增规则：

```text
table_exceeds_container_bounds
table_container_height_mismatch
table_readability_after_fit
```

检测逻辑：

1. 找到 table bbox。
2. 找到最近的 table container bbox。
3. 检查：
   - table top >= container top + padding；
   - table bottom <= container bottom - padding；
   - table height / container height 是否合理；
   - 最小单元格高度是否低于阈值；
   - 字号是否低于 readable floor；
   - 表格是否为了塞入容器被压得不可读。

初始策略：

- `table_exceeds_container_bounds`：global + auto。
- `table_container_height_mismatch`：global + auto_then_human_review。
- `table_readability_after_fit`：human_review。

## 9. 误修类型

下一阶段必须把误修当作一等公民。

新增 badcase：

```text
metric_improved_visual_regressed
likely_overcorrection
style_scope_mismatch
repair_introduced_new_findings
image_legibility_regression
layout_rhythm_regression
```

定义：

| 类型 | 含义 |
| --- | --- |
| `metric_improved_visual_regressed` | 机器指标下降，但人工认为视觉变差 |
| `likely_overcorrection` | 修复过度，破坏原本合理布局 |
| `style_scope_mismatch` | 把另一个 style 的规则套到当前 style |
| `repair_introduced_new_findings` | 修掉旧问题，引入新问题 |
| `image_legibility_regression` | 图像变小或细节不可读 |
| `layout_rhythm_regression` | 页面节奏、留白、组件比例变差 |

slide06 可记录为：

```text
metric_improved_visual_regressed
likely_overcorrection
style_scope_mismatch: bottom-band rule too aggressive for straight-rectangle layout
```

## 10. Visual Evidence Packet 规范

每次 repair trial 必须保存：

```text
visual_compare/
  iter_00_slide_XX.png
  iter_01_slide_XX.png
  slide_XX_before_after_human_review.png
  page_level_audit_delta.csv
  page_level_audit_delta.json
visual_human_review_packet.md
visual_human_review_packet.zh-CN.md
```

每页需要给出：

- before / after finding count；
- removed types；
- added types；
- 机器判断；
- 人工裁决；
- 高分辨率 before/after 图；
- 是否进入 accepted/rejected/tradeoff/overcorrection。

这让 benchmark 从“只有分数”升级为“分数 + 证据 + 人工反馈”。

## 11. 借鉴 AgentBench 的方式

AgentBench 的核心不是某个具体任务，而是评测思想：

```text
task definition
state / observation
action space
success criteria
automatic metric
human or environment feedback
aggregate reporting
```

Paper2Slides 可以对应为：

| AgentBench 概念 | Paper2Slides 对应 |
| --- | --- |
| task | 给定论文解析 checkpoint，生成一套可讲的 PPT |
| state | summary / plan / slide spec / style contract / current PPT audit |
| action | generate / repair typography / repair table / change layout / reject repair |
| observation | nonvisual audit、visual packet、speaker audit、human feedback |
| reward / score | 多维 eval score + human acceptance |
| success | 内容忠实、证据完整、布局安全、风格一致、人类接受 |

面试时应强调：我们不是照搬 AgentBench，而是把它的 eval 设计思想迁移到 document-to-slide generation。

## 12. 面试叙事

可以这样解释：

> 早期我们只统计 high/medium/low badcase，用 badcase 数量下降证明系统能自动发现并修复一部分问题。但后来发现，指标下降不一定等于视觉质量提升。比如某些 figure layout 修复在 metadata 上消除了 aspect mismatch，但在人类看来破坏了当前模板的视觉节奏。因此我们把 benchmark 升级成 style-aware multi-stage eval：每条规则都带 dimension、scope、repair_mode、confidence 和 human_outcome。系统可以先自动修复 experimental route，但必须输出 visual evidence packet；人类如果发现误修，就把案例标成 likely_overcorrection 或 tradeoff_review，再沉淀成 style-scoped rule。这样 benchmark 不只是数错误，而是在持续学习什么规则适用于什么模板。

如果面试官问“badcase count 是否过于简单”，可以回答：

> 是的，所以我们把它作为第一阶段 machine signal，而不是最终评分。最终评测包含 content fidelity、evidence coverage、layout safety、typography fit、component fit、style consistency、visual readability、repair risk 和 human acceptance。badcase 曲线用于定位趋势，视觉证据包和 human outcome 用于确认修复是否真正有效。

如果面试官问“论文解析成功率如何保证”，可以回答：

> 论文解析本身复用了已有 pipeline，但我们定义了 parse handoff contract。后续 benchmark 不盲目信任解析结果，而是检查 summary、section、figure、table、metric 和 evidence mapping 是否足够支撑 PPT 生成。如果解析层缺 evidence，后续生成会被标记为 parse_handoff risk，而不是把问题误归因给 PPT renderer。

## 13. 下一阶段执行顺序

建议先不急着跑新论文，按下面顺序推进：

1. 完成本文档评审，确认 benchmark 设计。
2. 在 benchmark registry 中新增 rule schema 字段：dimension、scope、repair_mode、confidence、human_outcome。
3. 为三个模板补 `style_contract`：
   - `academic`
   - `golden_baseline1_from_scratch_warm_academic`
   - `blind_rectangular_research_board`（experimental candidate）
4. 先实现三条最有价值的新规则：
   - `table_exceeds_container_bounds`
   - `image_underutilized_in_wide_panel`
   - `metric_improved_visual_regressed`
5. 将 visual human review packet 固化为每次 04 route 的标准输出。
6. 在第二篇论文上复跑四路 benchmark，检查新规则是否减少误修。
7. 再做 2-5 篇跨论文验证，决定哪些规则可以 promotion。

## 14. 2026-07-01 追加：从 golden2 封版到 autonomous style proposal

`blind_rectangular_research_board` 已经晋升为：

```text
golden_baseline2_blind_rectangular_research_board
```

但这次晋升必须诚实描述为 human-in-the-loop 结果。我们通过人工反馈发现并修复了：

- text evidence card 视觉偏上；
- figure 在大 wide panel 中使用面积不足；
- figure caption 左对齐而不是居中；
- dense table 需要 focused table view；
- focused table view 需要上方 label 和下方居中说明；
- table / text 超出容器属于 global correctness。

这些反馈已经进入 benchmark rule，而不是停留在单页手工修补。

下一阶段的路线因此调整为：

1. 三套 golden references 全部冻结：
   - `academic`
   - `golden_baseline1_from_scratch_warm_academic`
   - `golden_baseline2_blind_rectangular_research_board`
2. 用一篇从未解析过的新论文做 smoke test；
3. 同一篇论文只解析一次；
4. 生成三条 frozen reference route；
5. 另外生成三条 new-style experiment route：一条 assisted seed scaffold，两条 autonomous free proposal；
6. assisted seed scaffold 可以由 Codex 给弱初始脚手架，但不能读取或复制 golden0/1/2 的完整模板或 layout grammar；
7. autonomous proposal 只能使用抽象 design primitives、论文内容、设计约束和 badcase registry；
8. assisted seed 和 autonomous proposal 都不得读取 golden0/1/2 的完整模板或 layout grammar；
9. 每条 new-style route 支持 2-3 轮 bounded repair，连续两轮无改善或触发 repair-risk 后停止；
10. 每轮输出 score curve、repair log、style drift report、human review packet；
11. smoke 通过后，再扩展到 5 篇论文做量化。

新的主计划见：

```text
docs/autonomous_style_proposal_benchmark_plan.zh-CN.md
```

## 15. 新窗口启动 Prompt

下面这段是 2026-06-30 的历史启动词，适合复现 style-aware multistage 实现阶段。2026-07-01 之后，如果用户提供新论文做六路 smoke test，应优先使用 `docs/autonomous_style_proposal_benchmark_plan.zh-CN.md` 中的新启动语。

```text
Codex老师，我们继续 Paper2Slides benchmark 下一阶段。

项目路径：
D:\coding\agent_paper_to_slider\Paper2Slides-main

请不要切换分支，不要 git push，不要删除已有 benchmark_runs 产物。

请先阅读：
1. docs/style_aware_multistage_benchmark_plan.zh-CN.md
2. docs/benchmark_recording_schema.zh-CN.md
3. docs/from_scratch_benchmark_final_synthesis.zh-CN.md
4. docs/human_feedback_benchmark_synthesis.zh-CN.md
5. benchmarks/from_scratch_human_feedback_benchmark.json
6. paper2slides/benchmark/nonvisual_audit.py
7. paper2slides/benchmark/fourway.py

当前最新目标：
我们已经不满足于“badcase 数量下降曲线”，而是要升级为：
多维度 eval + style-aware rule + auto repair trial + human visual review packet + scoped benchmark rule。

关键背景：
- Thinking_with_Visual_Primitives 的 04 blind experimental iter0 -> iter1 虽然 metadata findings 下降，但 slide06 等页面出现 metric improvement 不等于 visual improvement 的问题。
- 直角矩形 style 下，右侧大图布局可能比底部长条布局更好。
- figure_panel_aspect_mismatch 不能无脑跨 style auto-repair。
- 表格超过容器是 global correctness 问题，应优先检测。

请先不要继续跑新论文，也不要急着大改 PPT。
请先按 docs/style_aware_multistage_benchmark_plan.zh-CN.md 做下一阶段实现计划，重点包括：
1. rule schema 如何扩展 dimension / scope / repair_mode / confidence / human_outcome；
2. style_contract 如何表示 academic、golden_baseline1、blind_rectangular_research_board；
3. 如何实现 table_exceeds_container_bounds；
4. 如何实现 image_underutilized_in_wide_panel；
5. 如何实现 metric_improved_visual_regressed；
6. 如何把 visual_human_review_packet 固化为 04 route 的标准输出；
7. 实现后应该跑哪些测试和哪一篇论文 smoke test。

请先输出实施计划和文件改动范围，再开始写代码。
```
