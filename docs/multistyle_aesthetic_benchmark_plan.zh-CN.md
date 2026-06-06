# paper2ppt 多模板与审美 Benchmark 计划

本文档记录下一阶段目标：在保护当前成熟 academic 模板的前提下，扩展多套论文 PPT 风格模板，并把 benchmark 从“是否出错”升级为“是否正确、是否清晰、是否好看、是否稳定可迭代”。

## 核心判断

当前 academic 模板已经在 Kimi K2 单篇验证中表现很好。如果只继续在这一套模板上跑 20 篇论文，结果更像验收，不足以体现“用评估发现问题、抓主要矛盾、持续改进系统”的能力。

因此下一阶段采用 **template-first** 策略：先提出和讨论模板设计，再实现少量代表模板并做单篇/小集合验证，最后再跑 ai20 全量 benchmark。不要直接黑箱生成一堆模板并立刻跑 20 篇论文。

更适合面试叙事的路线是：

1. 把当前 academic 模板冻结为 golden baseline。
2. 新增多套风格模板，让同一篇论文可以生成不同审美取向的 PPT。
3. 用 ai20 数据集评估每个模板在不同论文上的稳定性。
4. 记录初始失败率、warning 分布、审美分数和迭代后提升曲线。
5. 用 benchmark 结果驱动模板、renderer、layout rule 和 repair rule 的改进。

这样项目从“会生成 PPT”升级为“能自动评估 agent 输出质量，并用评估闭环提升生成系统”。

## 不可破坏的基线

当前模板作为 `academic_current` 或 `academic` baseline：

- 不在多模板探索中直接重构。
- 任何 renderer / QA / repair 的共享改动，都必须跑当前模板回归测试。
- 当前模板的 Kimi K2 单篇结果作为第一条 golden evidence：
  - 报告：`benchmark_runs/ai20_20260607_005847/aggregate_report.md`
  - 输出：`outputs/Kimi_K2_Technical_Report/paper/fast/slides_academic_medium_24slides/20260607_010126/slides.pptx`
  - 结果：1/1 通过，23 页，2 个 warning。
- 新模板出现问题时，优先修改新模板 preset / layout policy，不回退 current academic 的视觉逻辑。

## 推荐模板矩阵

第一批不要做太多，建议 5 套新模板 + 1 套基线。每套模板都应支持标题页、目录页、章节页、普通内容页、metric 页、图文页、表格页和结论页。

新窗口第一步应先让 Codex 给出模板方案，而不是直接改代码。建议先输出每个模板的：

- 名称和目标使用场景。
- 颜色 palette。
- 字体和字号层级。
- 标题页、目录页、章节页、普通页、图文页、metric 页、表格页的版式草图描述。
- 最容易出问题的页面类型。
- 对应的审美评分关注点。

用户确认模板方向后，再进入代码实现。

### 1. `academic`

用途：当前成熟模板，作为论文组会和正式汇报基线。

特征：
- 克制、清晰、结构稳定。
- 标题栏 + key message + claim/detail/evidence。
- 适合长技术论文和严肃汇报。

评估角色：
- golden baseline。
- 共享逻辑回归测试。

### 2. `editorial`

用途：更像高质量技术白皮书 / 研究报告。

视觉方向：
- 大留白、强标题、细分割线、少量强调色。
- 图片和表格更像杂志版式，而不是普通课件。
- 适合 OpenAI / Anthropic / Gemini 这类 system card 或 technical report。

可能暴露的问题：
- 标题过长时容易挤压内容。
- 大留白风格容易导致信息密度不足。
- 图文比例不稳定时可能出现空区过大。

### 3. `conference`

用途：顶会论文 oral / seminar 风格。

视觉方向：
- 高对比标题区。
- 方法、实验、结论分区清晰。
- 强调公式、框架图、结果表的可读性。

可能暴露的问题：
- 论文图很多时，图文布局容易拥挤。
- metric 和表格页容易信息过载。
- 章节页和内容页的节奏需要稳定。

### 4. `systems`

用途：系统、架构、agent workflow、训练基础设施类论文。

视觉方向：
- 网格感更强。
- 支持流程图、模块卡片、pipeline、stage timeline。
- 适合 Kimi K2、agent infrastructure、deep research agent 这类论文。

可能暴露的问题：
- pipeline 元素太多时，文字和模块容易重叠。
- 自动从论文内容中挑选“系统结构”时，容易把普通列表误排成系统图。
- 箭头、模块和说明文字需要更严格的空间约束。

### 5. `data_report`

用途：评测、benchmark、数据质量、结果分析类论文。

视觉方向：
- 表格、指标卡、排行榜、对比矩阵更突出。
- 可以展示 pass rate、warning rate、scorecard、ablation。
- 适合模型评估、agent benchmark、survey 论文。

可能暴露的问题：
- metric label/value 质量差会非常明显。
- 表格过宽时容易压缩不可读。
- 多指标页需要检测视觉层级是否清楚。

### 6. `visual_explainer`

用途：更适合图多、概念多、需要讲解机制的论文。

视觉方向：
- 图像占比更高。
- 支持单图大图、图旁讲解、步骤式讲解。
- 适合视觉推理、模型结构、方法示意图丰富的论文。

可能暴露的问题：
- 如果图片 caption 不足，需要依赖多模态理解。
- 图片和文字的语义匹配必须更强。
- 没有合适图片时，不能硬套视觉大图模板。

## Benchmark 评估维度

下一阶段的 benchmark 不只检测错误，还要量化质量。建议分为四层。

### A. 可靠性评分

目标：先保证能生成、能打开、没有严重版式错误。

指标：
- `artifact_success`：是否生成 `slides.pptx`、`speaker_script.md`、`layout_qa.json`。
- `qa_passed`：是否通过现有 QA。
- `artifact_missing_rate`：产物缺失比例。
- `command_failed_rate`：命令失败比例。
- `severe_warning_rate`：严重 warning / slide。
- `repair_success_rate`：经过 repair 后是否从失败变为通过。

### B. 内容组织评分

目标：PPT 不只是排版正确，还要讲得顺。

指标：
- `section_coverage`：是否覆盖背景、方法、实验、结论、限制或未来工作。
- `toc_alignment`：目录章节和实际章节页是否一致。
- `slide_role_balance`：title / toc / section / content / visual / table / conclusion 是否比例合理。
- `evidence_density`：claim 是否带 detail / evidence。
- `redundancy_rate`：相邻页标题或要点是否重复。
- `missing_core_section`：是否遗漏论文核心贡献、方法或实验。

实现方式：
- 先用 slide spec 规则统计。
- 后续可用 LLM judge 对 `checkpoint_summary.json`、`checkpoint_plan.json`、`checkpoint_slide_spec.json` 做低成本文本评审。

### C. 视觉与排版评分

目标：页面清晰、稳定、没有视觉事故。

指标：
- `text_overflow_count`：文本溢出和标题过长。
- `layout_payload_mismatch_count`：视觉/表格布局缺少对应素材。
- `density_score`：文本密度是否过高或过低。
- `whitespace_balance`：留白是否明显失衡。
- `alignment_score`：元素是否贴齐网格和边距。
- `figure_readability`：图片是否太小、被裁切或与正文不匹配。

实现方式：
- 现有 `pptx_qa.py` 继续扩展规则。
- 后续可渲染 slide preview 后做图像级检测。

### D. 审美评分

目标：把“好看”变成可讨论、可量化、可迭代的指标。

指标：
- `palette_harmony`：颜色是否协调，强调色是否过多。
- `contrast_score`：文字和背景是否有足够对比。
- `visual_hierarchy`：标题、key message、正文、注释层级是否清楚。
- `typography_consistency`：字号、粗细、行距、标题样式是否一致。
- `style_consistency`：同一模板内页面是否像一套设计系统。
- `presentation_polish`：是否有正式汇报感，而不是普通文档堆叠。

实现方式建议分两步：

1. 规则评分：从 PPTX 元素中读取颜色、字体、字号、位置和对象数量，给出可复现的启发式分数。
2. 视觉 judge：把 slide preview 渲染成图片后，用视觉模型对每页打 1-5 分，并输出原因。视觉 judge 只用于评估，不用于直接改 PPT，避免成本失控。

## 综合分数

建议聚合为：

```text
overall_score =
  0.35 * reliability_score
  + 0.25 * content_score
  + 0.25 * visual_layout_score
  + 0.15 * aesthetic_score
```

解释：
- 可靠性权重最高，因为不能生成或严重错版时，审美没有意义。
- 内容组织和视觉布局权重接近，体现“讲得对”和“看得懂”同等重要。
- 审美分数占 15%，用于区分“能用”和“高级”，但不让主观评分盖过基础正确性。

在面试中可以强调：审美不是靠主观夸，而是拆成颜色、层级、留白、一致性、可读性等可观测维度。

## 多模板运行策略

为了控制成本，运行顺序应分阶段。

推荐顺序：

1. **模板方案讨论**：先看模板名字、配色、版式策略和审美目标。
2. **两套模板最小实现**：先实现 `editorial` 和 `systems`。
3. **Kimi 单篇多模板验证**：从 `--from-stage generate` 低成本重跑。
4. **四篇小集合验证**：覆盖 agent、后训练、评估 survey、视觉论文。
5. **修主要矛盾**：根据 benchmark 报告只修 Top 1-3 问题。
6. **ai20 全量 benchmark**：模板稳定后再跑，产出 leaderboard 和迭代曲线。

### Stage 1：单篇多模板探索

先选 `Kimi_K2_Technical_Report.pdf`。

原因：
- 已经跑通过。
- RAG / summary checkpoint 已存在。
- 内容包含 agentic data、RL、系统架构、benchmark，能测试多种页面类型。

命令形态：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic,editorial,conference,systems,data_report,visual_explainer --slides 24 --start-index 17 --limit 1 --from-stage generate
```

注意：如果新模板需要重新规划章节或页面角色，可以从 `--from-stage plan` 开始；如果只改 renderer / theme / layout preset，应优先从 `--from-stage generate` 开始。

### Stage 2：小集合多模板验证

选择 4 篇代表性论文：

- `Kimi_K2_Technical_Report.pdf`：agent / RL / 系统。
- `DeepSeek_R1.pdf`：推理 / 后训练。
- `Evaluation_Benchmarking_LLM_Agents_Survey.pdf`：评估 / survey。
- `Thinking_with_Visual_Primitives.pdf`：视觉 / 图多。

目标：
- 找出每个模板最容易失败的论文类型。
- 统计 warning category。
- 做第一轮模板修复。

### Stage 3：ai20 全量单模板回归

先保留 `academic`，跑全量 20 篇：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic --slides 24 --resume
```

目标：
- 得到当前成熟模板的全量 baseline。
- 给后续多模板对比提供参照。

### Stage 4：ai20 全量多模板 benchmark

等新模板在小集合上稳定后，再跑：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic,editorial,conference,systems,data_report,visual_explainer --slides 24 --resume
```

目标：
- 输出 template leaderboard。
- 输出每个模板的 pass rate、warning per slide、审美分、平均耗时。
- 输出每篇论文最适合的模板推荐。

## 需要新增或改造的代码模块

### 1. 模板 preset 层

建议新增：

```text
paper2slides/generator/style_presets.py
```

职责：
- 定义每个模板的 palette、字体、字号、边距、标题区、章节页风格、metric 卡片风格。
- 把 `--style academic` 从纯字符串升级为可解析 preset。
- 支持自定义 style 仍然走原来的兼容路径。

### 2. renderer 模板分派

改造：

```text
paper2slides/generator/pptx_renderer.py
```

职责：
- 根据 style preset 渲染不同页面骨架。
- 保留当前 academic renderer 行为。
- 新模板优先共用 slide schema，不改变上游 plan/spec 数据结构。

### 3. 内容角色与模板适配

改造：

```text
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/content_planner.py
```

职责：
- 让 LLM 在 plan/spec 中更明确标注 slide role。
- 对不同模板提供不同 layout hint。
- 不让 LLM 直接输出颜色和坐标，避免风格漂移；颜色和坐标由 preset 控制。

### 4. 审美与内容 benchmark

建议新增：

```text
paper2slides/benchmark/aesthetic.py
paper2slides/benchmark/content_quality.py
paper2slides/benchmark/style_report.py
```

职责：
- 从 `checkpoint_slide_spec.json`、`layout_qa.json`、PPTX 元素中提取评分。
- 输出每页分数、每套模板分数、每篇论文分数。
- 汇总到 `aggregate_report.json` 和 `aggregate_report.md`。

### 5. 预览图和视觉 judge

后续可选新增：

```text
paper2slides/benchmark/preview.py
paper2slides/benchmark/visual_judge.py
```

职责：
- 把 PPTX 或 sidecar PDF 渲染成 slide preview。
- 用视觉模型对页面审美、可读性和专业感打分。
- 保存少量最差页面截图，便于人工复盘。

## 报告输出升级

未来 benchmark 报告建议输出：

```text
benchmark_runs/<set>_<timestamp>/
  manifest.json
  per_paper_results.json
  aggregate_report.json
  aggregate_report.md
  style_leaderboard.csv
  quality_curves.json
  badcases/
    by_style/
    by_warning_category/
    worst_pages/
  previews/
```

`aggregate_report.md` 应包含：

- 总体 pass rate。
- 每套模板 leaderboard。
- 每套模板平均 warning per slide。
- 每套模板 content / layout / aesthetic / overall 分数。
- 最差模板、最差论文、最差页面。
- 修复前后对比曲线。
- 下一轮最值得修的 Top 3 问题。

## 迭代闭环

每次迭代都按这个流程：

1. 固定数据集和模板集合。
2. 跑 benchmark，得到初始报告。
3. 从报告中找最主要矛盾，例如某模板 text overflow 占 60%。
4. 只修一个主要问题。
5. 重新跑同一集合。
6. 对比 pass rate、warning rate、aesthetic score。
7. 记录改动和提升。

面试中最有说服力的是这种表述：

> 我不是凭感觉说模板好看，而是把 PPT 输出拆成可靠性、内容组织、视觉排版和审美四类指标。每次迭代先看 benchmark 报告里的主要 badcase 分布，再改 renderer 或 repair rule，并用同一批论文回归验证。最后用曲线展示 warning rate 下降、pass rate 上升、审美分提升。

## 下一窗口启动任务

新窗口可以直接按这个顺序做：

1. 阅读 `docs/benchmark_plan.zh-CN.md` 和本文档。
2. 检查当前 `academic` baseline，不破坏现有模板。
3. 新增 `style_presets.py`，先实现 `editorial` 和 `systems` 两个模板。
4. 扩展 benchmark runner，使 style 维度可以输出 leaderboard。
5. 新增规则型 aesthetic/content score 的第一版。
6. 用 Kimi K2 从 `--from-stage generate` 跑 `academic,editorial,systems` 三个模板。
7. 写出第一次多模板 benchmark 报告和下一轮修复建议。
