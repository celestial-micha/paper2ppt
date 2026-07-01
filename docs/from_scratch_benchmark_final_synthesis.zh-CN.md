# From-Scratch Benchmark 收官总结与后续计划

本文档记录截至 2026-06-15 的结论：原 `academic` golden baseline 已经稳定；从零 warm academic proof-panel 风格也已经通过 Kimi K2、mHC、DeepSeek_V4 的 human-in-the-loop 迭代，并在 DeepSeek_V4 v25 被保存为 `golden_baseline1_from_scratch_warm_academic`。

2026-07-01 追加：Deep Residual 的 `blind_rectangular_research_board` 经过 style-aware benchmark 和 human-in-the-loop 迭代后，已保存为第三个 frozen reference：

```text
golden_baseline2_blind_rectangular_research_board
```

因此后续 benchmark 不再只有两个黄金参考，而是三套 human-tuned references 与 hybrid new-style proposal 分轨推进：一条 assisted seed scaffold 用来保证短期 smoke 稳定，两条 autonomous free proposal 用来探索更高自主度。

目标不是多保存一套 PPT，而是把“人类指出问题 -> 系统转成 badcase -> renderer 修复 -> audit 回归”的过程固化为 benchmark 和 agent workflow。

## 1. 当前两个黄金参考

### Original Golden Baseline

定位：成熟生产基线。

代表样式：`academic`。

用途：

- 作为默认稳定生成模板；
- 作为共享 renderer、QA、repair 改动的回归保护对象；
- 用于证明系统已经有一套可交付的论文汇报能力。

保护原则：

- 新 benchmark 规则不能默认改变它的视觉语法；
- 从 `golden_baseline1` 学到的圆角 panel 微调，必须先以 warning / detect-only 方式跑在 `academic` 上；
- 只有在原 baseline 回归通过后，才能允许相关规则变成默认 auto-repair。

### Golden Baseline1

定位：从零模板实验沉淀出的第二个黄金参考。

style id：

```text
golden_baseline1_from_scratch_warm_academic
```

本地稳定产物：

```text
outputs/golden_baselines/golden_baseline1_from_scratch_warm_academic/DeepSeek_V4_golden_baseline1_from_scratch_warm_academic.pptx
outputs/golden_baselines/golden_baseline1_from_scratch_warm_academic/nonvisual_audit_DeepSeek_V4_golden_baseline1_from_scratch_warm_academic.json
```

来源 checkpoint：

```text
outputs/DeepSeek_V4/paper/fast/from_scratch_inventory/DeepSeek_V4_v25_panel_identity_label_centered.pptx
```

关键视觉语法：

- warm paper background；
- muted teal / soft gold / clay 的克制学术配色；
- title / agenda / section / content / closing 的完整论文阅读结构；
- 每页一个主 claim、一个 support、一个 proof object；
- rounded proof panel 是主要证据容器；
- 绿色类型角标说明 panel 类型，固定在 panel 内部左上角；
- 黑色身份标题说明主体内容，锚定图片、表格、指标卡或解释文字的中心线；
- figure/table/caption 的位置以 fitted content box 为准，而不是以圆角矩形外框为准。

## 2. Human-in-the-loop 得到的核心经验

### 经验一：from-scratch 不是重新解析 PDF

已经稳定的 summary / plan / slide_spec / figure / table / metric checkpoint 应复用。新的工作从“论文理解已完成”开始，目标是重新组织叙事、proof object、布局和视觉系统。

### 经验二：内容完整先于审美

第一版可以丑，但不能缺标题页、目录、section、claim、support、proof object、表格行、figure 或 metric。benchmark 必须先保证内容和证据不丢，再评估美感。

### 经验三：审美反馈要翻译成可检测规则

人类说“不好看”“怪”“拥挤”“不居中”时，不能只手工挪动一页。需要落成：

- badcase id；
- trigger signals；
- root cause；
- repair strategy；
- regression check；
- test fixture；
- nonvisual audit rule。

### 经验四：微调要局部、可回归

DeepSeek_V4 后期问题大多是低风险 polish：caption 容量、figure label 锚点、source footer、proof-panel identity label 等。这类问题值得进 benchmark，但修复必须局部，不能升级成新模板重构。

### 经验五：风格规则必须有 scope

这是用户最担心、也最重要的工程结论。一个规则可能对 `golden_baseline1` 有益，却会伤害原 `academic` baseline。例如：

- rounded proof panel 的 identity label 居中规则，适合 `golden_baseline1`；
- 但如果原 `academic` 使用不同 header grammar，强行套用就可能破坏原版。

因此 benchmark 规则必须分为：

```text
global correctness rules
mature academic baseline rules
golden_baseline1 rounded proof-panel rules
experimental style rules
```

默认策略：

```text
detect first, repair only after style contract matches.
```

## 3. Benchmark 风险策略

### 问题：新 benchmark 会不会破坏原 golden baseline？

会有风险，尤其是当 rule 同时带有“检测”和“自动修复”能力时。

主要风险：

- 把某一风格的审美偏好误当成全局真理；
- 自动修复改变原 baseline 的排版节奏；
- 修复一个 panel 标签，却打破原模板的 header hierarchy；
- 低风险 polish 被错误升级成结构性重排。

### 解决策略

1. **规则分级**

全局 correctness rule 可以跨风格自动修：

```text
missing_title_slide
estimated_text_overflow
shape_overlap_risk
table_rows_missing
inline_table_payload_not_indexed
figure_picture_aspect_distortion
```

风格相关 polish rule 默认只检测：

```text
figure_label_anchor_drift
panel_identity_label_anchor_drift
card_internal_spacing_not_scaled_to_frame
table_support_band_off_balance
```

2. **规则带 style scope**

每条 rule 应声明：

```text
scope: global | academic | golden_baseline1 | experimental
mode: detect_only | suggest_repair | auto_repair
```

3. **先跑平行回归**

任何新 auto-repair 进入默认链路前，必须同时跑：

```text
original golden baseline
golden_baseline1
fresh-paper trial
```

4. **保留原 baseline artifact**

不要用 `golden_baseline1` 覆盖原 `academic`。它们是两个 reference，不是新旧替换关系。

5. **修复前检查 style contract**

如果 deck 没有 rounded proof panel grammar，就不应用 rounded proof panel 的身份标签修复。

## 4. 下一阶段评测设计

### 单篇新论文三路验证

先选一篇新论文，解析一次，然后生成三路 PPT：

1. **普通 golden baseline 生成**
   - style: `academic`
   - 不启用新 benchmark auto-repair，只做 audit；
   - 目的：确认成熟 baseline 没被破坏。

2. **golden_baseline1 当前款式生成**
   - style: `golden_baseline1_from_scratch_warm_academic`
   - 启用对应 scoped benchmark detection 和 auto-repair；
   - 目的：验证新款式泛化。

3. **benchmark 改进版 golden baseline**
   - style: `academic`
   - 启用 global correctness repair；
   - 对风格相关 polish 只 report / suggest，不默认 auto-repair；
   - 目的：验证 benchmark 能帮原 baseline 改错，但不把它改成 golden_baseline1。

单篇通过标准：

- 三路都成功生成 PPTX 和 speaker script；
- 三路都无 high / medium nonvisual findings；
- 原 `academic` 的视觉节奏不被新规则破坏；
- `golden_baseline1` 保持独立风格；
- 报告能比较三路各自发现的问题和修复收益。

### ai20 三路批量验证

单篇稳定后，在 20 篇论文上运行：

1. ordinary `academic` generation；
2. `golden_baseline1` generation with benchmark-guided repair；
3. `academic` generation with global benchmark repair and style-scoped suggestions。

每篇论文只解析一次，复用 checkpoint 给三路生成。

输出报告应包含：

- generation success rate；
- high/medium/low findings；
- repaired finding count；
- unresolved finding count；
- style drift risk；
- baseline similarity / novelty score；
- cost and runtime；
- representative artifacts；
- per-paper speaker script availability。

### 全新风格 blind loop

再选择一篇新论文，要求 agent：

```text
不要复用 original golden baseline 的视觉骨架；
不要复用 golden_baseline1 的 rounded proof-panel 语法；
只复用解析内容和 benchmark badcases；
从 rough draft 开始自动生成、audit、repair，直到无 high/medium findings。
```

目的：

- 证明 benchmark 不是只会维护已有模板；
- 证明 agent workflow 可以创造第三种风格；
- 为面试提供“从零到可用模板”的自动迭代案例。

## 5. Benchmark Harness 目标

最终 harness 应该把生成、检测、修复、对比、报告串成一条命令级工作流：

```text
input PDF
 -> parse once
 -> build reusable checkpoints
 -> generate multiple styles
 -> run nonvisual audit
 -> apply style-scoped repair loop
 -> generate speaker scripts
 -> compare outputs
 -> write benchmark report
```

核心配置：

```text
paper_set
styles
repair_profile
style_scope
max_iterations
stop_conditions
report_dir
```

建议的 repair profiles：

```text
audit_only
global_correctness_repair
golden_baseline1_repair
experimental_from_scratch_loop
```

面试时可以这样表述：

> 我不是只做了一个 PPT 生成器，而是做了一个可回归的生成评测 harness。系统解析论文一次，然后并行生成多个风格版本；benchmark 会检测内容缺失、文本溢出、图表错误、布局几何、审美 polish 和风格漂移，并且根据 style scope 决定哪些问题能自动修、哪些只能报告。这样既保护原 golden baseline，又能把 human-in-the-loop 反馈转化成可泛化的自动迭代能力。

## 6. 2026-07-01 追加：第三个 frozen reference 与下一阶段路线

### 当前三套 frozen references

```text
golden_baseline0: academic
golden_baseline1: golden_baseline1_from_scratch_warm_academic
golden_baseline2: golden_baseline2_blind_rectangular_research_board
```

`golden_baseline2` 的保存位置：

```text
outputs/golden_baselines/golden_baseline2_blind_rectangular_research_board/
```

它的意义不是证明系统已经完全自主生成了第三套风格，而是证明：

- human feedback 可以被稳定转成 scoped benchmark rules；
- style-aware repair 能发现“指标变好但视觉变差”的误修风险；
- 三套人工迭代成熟参考可以作为后续评测的 frozen baselines；
- 下一阶段可以把“成熟参考”和“自主风格生成”严格隔离。

### 下一阶段实验形态

下一篇新论文应采用六路 hybrid smoke：

1. `academic` frozen reference；
2. `golden_baseline1_from_scratch_warm_academic` frozen reference；
3. `golden_baseline2_blind_rectangular_research_board` frozen reference；
4. assisted seed scaffold style；
5. autonomous style proposal A；
6. autonomous style proposal B。

前三路允许读取各自 frozen style contract。第 4 路允许 Codex 给一个弱初始视觉脚手架，但仍禁止读取 golden0/1/2 的完整 PPTX、style contract 和 layout grammar，并且必须进入 benchmark repair loop。第 5-6 路完全自由 proposal，只允许读取：

- paper content inventory；
- deck requirements；
- abstract design primitives library；
- badcase registry；
- global / scoped rule metadata。

### 评价重点

六路结果不再只看 badcase 数量下降，而要同时记录：

- content fidelity；
- evidence coverage；
- layout safety；
- typography fit；
- component fit；
- style consistency；
- visual readability；
- repair risk；
- human acceptance；
- human feedback effort；
- native editability and traceability。

主计划见：

```text
docs/autonomous_style_proposal_benchmark_plan.zh-CN.md
```

## 7. 立即下一步

1. 在新窗口用一篇新论文做三路单篇验证；
2. 如果三路都稳定，再扩展到 ai20；
3. 然后做一次 blind from-scratch loop，证明 benchmark 能创造新风格；
4. 最后把三路生成、audit、repair、report 包装成 benchmark harness。

2026-07-01 后这四步需要改为：

1. 先用用户提供的一篇未解析新论文做六路 hybrid smoke；
2. smoke 稳定后扩展到五篇论文，而不是立刻跑 ai20 全量；
3. 重点分开统计 assisted seed route 和 autonomous free routes 的 repair curve 与 human feedback effort；
4. 再决定是否进入 10 篇或 ai20 全量。
