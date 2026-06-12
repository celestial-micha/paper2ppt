# paper2ppt 模板体系与从零审美 Benchmark 计划 V2

本文档是当前阶段的主计划。它重建了我们在 Kimi K2 多模板实验后的共识：成熟模板要保留，但下一阶段真正要做的是 **从已解析论文内容出发，从无审美草稿一步步迭代出全新 PPT 风格，并把这个过程变成可自动检测、可自动修复、可回归的 benchmark**。

## 一句话目标

把 paper2ppt 从“有一套好看的 golden baseline 模板”推进到：

```text
给定一篇论文的解析结果
 -> 系统能先组织内容
 -> 再生成一个粗糙但完整的 PPT
 -> 再通过 benchmark 发现内容、排版、审美问题
 -> 再自动提出或执行修复
 -> 最后迭代成一套不模仿 golden baseline 的新风格 PPT
```

## 对话复盘后的核心共识

### 1. `academic` 是 golden baseline，不动

当前 `academic` 模板已经很好看、稳定、可用。它代表项目当前成熟能力。

它的作用是：

- 作为正式论文汇报的默认模板。
- 作为 ai20 全量 benchmark 的稳定基线。
- 作为新代码改动的回归测试对象。

原则：

- 不为了新模板重构它。
- 不为了审美探索破坏它。
- 任何共享 renderer / QA / repair 改动都要确保它不回退。

### 2. `academic_warm`、`editorial`、`editorial_mono`、`data_report` 是 companion styles

这些样式用户认为好看，应该保留。

但它们不是“真正从零设计的新模板”，因为它们仍然很像 golden baseline：

- 视觉骨架相似。
- 页面节奏相似。
- 许多页面仍像标题栏 + key message + structured points 的变体。
- 本质上更接近 mature baseline suite 的可选皮肤/伴侣类型。

因此它们的定位是：

```text
mature baseline suite:
  academic
  academic_warm
  editorial
  editorial_mono
  data_report
```

后续可以继续修它们的小问题，例如 `data_report` 的青色偏怪、颜色与文字对比问题、metric/table 密度问题，但不要把它们当作下一阶段主线。

### 3. 真正的新模板必须摆脱 golden baseline 的页面骨架

我们可以复用：

- PDF 解析结果。
- RAG / summary。
- content plan。
- figure/table extraction。
- 过去迭代中总结出的 QA 问题和修复经验。

但新模板不能复用：

- golden baseline 的标题栏结构。
- golden baseline 的 key message block 主结构。
- golden baseline 的 numbered point 页面节奏。
- golden baseline 的 title / toc / section / content / visual 页宏观骨架。

简单说：

```text
可以复用论文理解和问题经验。
不能复用 baseline 的视觉骨架。
```

### 4. 从零设计会先变丑，这是正常的

真正脱离 baseline 后，第一版往往会出现：

- 页面很粗糙。
- 文本溢出。
- 卡片放不下 detail。
- 图文比例不稳定。
- 表格不可读。
- metric label/value 不好。
- 页面节奏散。
- 内容可能被美化过程裁掉。

这些不是失败，而是我们要记录进 benchmark 的 badcase。

最终目标不是让 Codex 人工一页页看，而是让 agent workflow 能自动发现：

- 有没有缺页。
- 有没有缺核心内容。
- 有没有图表丢失。
- 有没有文字溢出。
- 有没有配色或对比问题。
- 有没有太像 golden baseline。
- 哪些问题能自动修，哪些需要人确认。

## 双轨路线

### Track A：成熟套件回归

目的：保护当前成熟能力。

styles：

```text
academic,academic_warm,editorial,editorial_mono,data_report
```

用途：

- 跑 Kimi K2 单篇。
- 跑 ai20 全量。
- 统计 pass rate、warning rate、artifact success。
- 检查成熟模板是否回退。
- 修 `data_report` 的颜色、对比和 metric/table 小问题。

这条路线不承担“创造全新风格”的任务。

### Track B：从零新模板实验

目的：建立一个不依赖 golden baseline 骨架的新模板创造流程。

首选论文：

```text
test_papers/Kimi_K2_Technical_Report.pdf
```

原因：

- 已经跑通过。
- 已有解析结果和 checkpoint。
- 内容包含 agentic intelligence、RL、data pipeline、system architecture、benchmark。
- 能测试图文页、metric 页、表格页、系统机制页、结论页等多种页面。

## 从零新模板实验流程

### Step 1：内容库存 Content Inventory

输入：

- `checkpoint_summary.json`
- `checkpoint_plan.json`
- `checkpoint_slide_spec.json`
- figure/table manifest

输出：

```text
content_inventory.json
```

内容应包含：

- 论文标题、作者、机构。
- 核心贡献。
- 背景和动机。
- 方法/系统/训练流程。
- 数据与实验。
- 关键结果和指标。
- 限制、讨论、结论。
- 可用 figures。
- 可用 tables。
- 可抽取 metrics。
- 每条内容对应 evidence/source。

Benchmark 检查：

- 是否遗漏核心贡献。
- 是否遗漏方法或实验。
- 是否有 unsupported claim。
- 是否有重复内容。
- figure/table/metric 是否被登记。

### Step 2：无审美草稿

目标：先完整，不好看也可以。

输出：

- rough slide spec 或 draft PPTX。
- 每页都有 title / claim / support / proof object。
- 不要求配色、字体、精致布局。

这一步要故意降低审美要求，避免一开始为了好看裁掉内容。

Benchmark 检查：

- 是否缺页。
- 是否空页。
- 是否缺 title。
- 是否缺 claim。
- 是否缺 support/evidence。
- 是否缺 figure/table/metric。
- 是否把图表放进不匹配 layout。

### Step 3：叙事重组

目标：重新决定 PPT 怎么讲，而不是沿用 baseline 顺序。

输出：

- deck thesis。
- audience。
- section list。
- table of contents。
- slide role map。
- 每页 claim title。
- 每页 proof object 类型。

推荐 slide roles：

```text
title
thesis
agenda
section_opener
mechanism
pipeline
evidence
metric
table_interpretation
figure_explainer
comparison
limitation
conclusion
```

Benchmark 检查：

- 目录和章节页是否一致。
- slide role 分布是否合理。
- 每页是否只有一个中心 claim。
- proof object 是否能证明 claim。
- 是否有结论页。

### Step 4：视觉系统设计

目标：定义一套完全独立的新视觉语言。

必须定义：

- 画布与网格。
- 背景系统。
- 字体层级。
- palette 及语义。
- title page 语言。
- agenda / toc 语言。
- section opener 语言。
- proof object grammar。
- figure treatment。
- table grammar。
- metric grammar。
- diagram / pipeline grammar。
- footer / page marker。
- 禁用元素。

硬约束：

- 不使用 baseline 的标准标题栏骨架。
- 不使用 baseline 的 key message block 作为主结构。
- 不让 numbered points 成为所有页面的默认视觉。
- contact sheet 上必须看起来像另一套设计系统。

Benchmark 检查：

- typography consistency。
- palette harmony。
- contrast。
- whitespace balance。
- layout rhythm。
- style consistency。
- novelty_score。

### Step 5：第一版美化 PPT

目标：把无审美草稿套进新视觉系统。

输出：

- `slides.pptx`
- `speaker_script.md`
- `layout_qa.json`
- `content_quality.json`
- `aesthetic_score.json`
- `novelty_score.json`
- `iteration_report.md`

这一步允许有 warning，但必须能明确告诉我们主要问题是什么。

### Step 6：人工反馈转 benchmark rule

用户每次反馈都要整理成结构化规则：

```text
badcase:
trigger:
severity:
example_slide:
root_cause:
repair_strategy:
auto_fix:
regression_check:
```

示例：

```text
badcase: card_text_overflow
trigger: 小卡片中 detail 超过可用空间
severity: medium
root_cause: 把完整 detail 放进卡片
repair_strategy: 卡片只保留短 claim，detail 移到 notes 或右侧说明区
auto_fix: yes
regression_check: text_overflow warning 下降，content_score 不下降
```

### Step 7：自动迭代

每轮只修 Top 1-3 个主要矛盾。

流程：

```text
run -> score -> find top badcases -> repair -> rerun -> compare -> record rule
```

比较指标：

- warning count。
- severe warning count。
- content_score。
- visual_layout_score。
- aesthetic_score。
- novelty_score。
- artifact_success。

## 评分体系

### reliability_score

关注是否能稳定生成：

- PPTX 是否存在。
- speaker script 是否存在。
- layout QA 是否存在。
- 是否 QA pass。
- 是否 artifact missing。
- 是否 command failed。

### content_score

关注是否讲对：

- 核心贡献覆盖。
- 方法/系统覆盖。
- 实验/结果覆盖。
- 结论/限制覆盖。
- 每页 claim 是否明确。
- evidence 是否充足。
- proof object 是否匹配。

### visual_layout_score

关注是否看得懂：

- text overflow。
- small box long text。
- image too small。
- table unreadable。
- metric value/label 缺失。
- 元素越界。
- 留白失衡。
- 图文不匹配。

### aesthetic_score

关注是否好看：

- palette harmony。
- contrast。
- typography hierarchy。
- whitespace。
- rhythm。
- polish。
- style consistency。

### novelty_score

关注是否不像 baseline 换皮：

- header skeleton similarity。
- key message block similarity。
- numbered-point dominance。
- macro layout similarity。
- title/toc/section/content/visual/table 页是否有独立设计。
- contact sheet 是否像新模板。

注意：

- `novelty_score` 只用于 from-scratch 新模板实验。
- mature companion styles 不需要高 novelty。

## 下一窗口第一轮不要做什么

不要：

- 不要继续扩大 companion styles。
- 不要继续只改 palette。
- 不要直接从 renderer 开始写新模板。
- 不要一上来跑 ai20。
- 不要把 `academic_warm/editorial/editorial_mono/data_report` 当成新模板。
- 不要让 DeepSeek 处理图片输入。
- 不要提交 `.env`、`outputs/`、`benchmark_runs/`、`test_papers/`。

## 下一窗口第一轮要做什么

建议第一轮只做规划，不写代码：

1. 读取本文件、`docs/benchmark_plan.zh-CN.md`、`docs/next_window_handoff.zh-CN.md`。
2. 复述当前目标，确认不是继续换皮。
3. 设计 `content_inventory.json` schema。
4. 设计无审美草稿 spec schema。
5. 设计 `novelty_score` 的可执行规则。
6. 设计人工反馈如何转 benchmark rule。
7. 给出第一轮 Kimi K2 from-scratch 实验计划。

用户确认后，再进入代码实现。

## 新窗口推荐启动语

```text
codex老师，我们继续做 Paper2Slides-main / paper2ppt。请先阅读：

1. docs/benchmark_plan.zh-CN.md
2. docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
3. docs/next_window_handoff.zh-CN.md
4. docs/agent_workflow.md
5. README.zh-CN.md

请注意：这次不是继续调 academic 或 companion styles。

当前结论：
- academic 是 golden baseline，必须保护。
- academic_warm、editorial、editorial_mono、data_report 是 baseline companion styles，先保留。
- 这些 companion styles 好看，但太像 golden baseline，不是我们下一步要做的新模板。
- 下一步是 from-scratch template experiment：从 Kimi K2 已解析内容出发，先做 content inventory 和无审美草稿，再重新设计章节、页面角色、proof object 和视觉系统。
- 新模板不能模仿 golden baseline 的页面骨架，但可以复用 golden baseline 迭代中总结的问题和修复经验。

请先不要写代码。请先帮我规划：
1. content_inventory.json 应该怎么设计；
2. 无审美草稿 PPT/spec 应该怎么生成；
3. slide role 和 proof object 怎么定义；
4. novelty_score 怎么检测新模板是不是 baseline 换皮；
5. 每轮人工反馈怎么转成 benchmark rule；
6. 第一轮 Kimi K2 from-scratch 实验怎么跑。

模型路由：
- 文本：deepseek-v4-flash，base_url=https://api.deepseek.com。
- 图片/多模态：gpt-5-mini，base_url=https://api.shunyu.tech/v1。
- 不要打印或提交 API key。

git 注意：
- paper2slides/.env、outputs/、benchmark_runs/、test_papers/ 不要提交。
- 改代码后跑 python -m unittest test_phase1_pptx.py。
```

## 追加说明：Kimi K2 from-scratch v5 作为当前审美参考

在后续 human-in-the-loop 迭代中，Kimi K2 from-scratch PPT 已经从“无审美草稿”推进到一个用户认为比较美观的版本。当前应把：

```text
outputs/Kimi_K2_Technical_Report/paper/fast/from_scratch_inventory/rough_draft_v5.pptx
```

视为 from-scratch track 的阶段性 accepted reference。

这意味着下一阶段的重点不是继续随意探索视觉改动，而是：

1. 保存 v5。
2. 把 v1-v6 的人类反馈沉淀成 benchmark rules。
3. 用规则保护 v5 的主要审美方向。
4. 再接入 `--render-review-dir`、文本快照、PPTX 几何检查和选择性视觉判断。
5. 后续任何视觉优化都要和 v5 对比，防止“局部指标变好、整体观感变差”。

v6 的回退给出一个重要教训：自动化审美优化不能只看文本密度、组件面积或局部布局合理性。它还需要维护整页构图、学术庄重感和用户偏好的稳定性。

新增机器可读规则文件：

```text
benchmarks/from_scratch_human_feedback_benchmark.json
```

该文件是后续 benchmark / runner / repair loop 的候选输入，包含：

- v5 accepted reference。
- v6 regression guard。
- v1-v6 iteration log。
- badcase rule registry。
- aesthetic rubric。
- non-visual-first / selective-render review strategy。

下一轮实现建议：

1. 先让 benchmark runner 能读取 `benchmarks/from_scratch_human_feedback_benchmark.json`。
2. 在 from-scratch audit 中输出这些 rule 的命中情况。
3. 对低成本问题先做 PPTX 元数据检查，例如字体大小、shape overlap、table rows、card density、layout repetition。
4. 只有高风险页进入截图或视觉模型评审。
5. 自动 repair 每轮只修 Top 1-3 个问题，并记录是否比 v5 更好。
