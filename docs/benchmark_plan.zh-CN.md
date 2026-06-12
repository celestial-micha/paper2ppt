# paper2ppt 自动 Benchmark 计划

本文档记录 paper2ppt 从 human-in-the-loop 人工验收到自动 benchmark / 自动迭代系统的建设计划。

## 当前状态

截至当前版本，已经完成的是 **历史 QA 汇总型 benchmark 种子**、**20 篇论文 benchmark 数据集准备**、**批量生成 runner 实现**，以及 **Kimi K2 单篇端到端生成与 QA 验证**。随后我们尝试了多套样式，确认 `academic` 应继续作为 golden baseline，同时筛出 `academic_warm`、`editorial`、`editorial_mono`、`data_report` 作为 baseline companion styles。

新的核心判断是：这些 companion styles 虽然好看，但与 golden baseline 太像，更适合作为成熟套件的可选样式，而不是“从无到有的新模板”。下一阶段 benchmark 要走双轨路线：

1. **成熟套件回归**：保护 `academic`，保留 `academic_warm`、`editorial`、`editorial_mono`、`data_report`，用于稳定生成、ai20 回归和可靠性统计。
2. **从零模板实验**：不模仿 golden baseline 的视觉骨架，只复用论文解析结果和之前积累的问题/修复经验，从 content inventory、无审美草稿、章节/目录/slide role、proof object、视觉系统一步步迭代出全新模板，并把过程中遇到的问题沉淀为可自动检测和自动修复的 benchmark rule。

当前文档 checkpoint 已提交并推送到远端分支 `codex/from-scratch-benchmark-plan`，提交为 `ba94020 docs: clarify from-scratch benchmark plan`。更完整的新窗口交接说明见 `docs/next_window_handoff.zh-CN.md`。

当前 DeepSeek 路线使用 `deepseek-v4-flash`，不是 `deepseek-v4-pro`。项目采用双模型路由，避免把文本模型和多模态模型混淆：

```env
LLM_MODEL=deepseek-v4-flash
RAG_LLM_BASE_URL=https://api.deepseek.com
PPTX_LLM_MODEL=deepseek-v4-flash
RAG_FAST_INCLUDE_IMAGES=1
RAG_VISION_MODEL=gpt-5-mini
RAG_VISION_BASE_URL=https://api.shunyu.tech/v1
RAG_VISION_API_KEY=your_openai_or_vision_api_key_here
PPTX_ENABLE_FIGURE_ANALYSIS=auto
PPTX_VISION_MODEL=gpt-5-mini
PPTX_VISION_BASE_URL=https://api.shunyu.tech/v1
PPTX_VISION_API_KEY=your_openai_or_vision_api_key_here
```

其中 DeepSeek V4 Flash 只负责文本调用；当 fast RAG 阶段需要把论文原图作为 `image_url` 输入，或 PPTX 阶段需要做 figure analysis 时，使用 `gpt-5-mini` 处理多模态输入。
注意：DeepSeek key 不能用于 `gpt-5-mini` 多模态调用；需要单独配置 OpenAI 或兼容服务商的视觉模型 API key。

已完成内容：

- 新增 `paper2slides/benchmark/qa_summary.py`，可以扫描已有输出目录中的 `layout_qa.json`。
- 将历史 warning 归类为稳定 badcase 类型，例如文本溢出、布局越界、空组件、metric 质量问题、布局与素材不匹配、结构化要点缺失等。
- 新增命令：

```powershell
python -m paper2slides.benchmark --outputs outputs --report-dir benchmark_runs\local_history
```

- 当前本地运行结果扫描到 30 个历史 QA run，来自过去已经生成过的 `outputs/**/layout_qa.json`。
- 当前报告显示：30 个历史 QA run，28 个通过，2 个失败，pass rate 为 93.33%，共 575 页、146 个 warning，主要问题集中在 text overflow / clipping risk。
- 新增 `benchmarks/papers.json`，登记现有 `test_papers` 中的 12 篇本地论文，作为后续正式 benchmark 的种子集合 `local_12`。
- 新增 `ai20` 集合：它由 `local_12` 加 8 篇新增论文组成，当前 20 篇 PDF 已全部下载到 `test_papers/`。
- `Kimi_K2_Technical_Report.pdf` 已完成一次单篇端到端验证：解析/RAG 复用已完成 checkpoint，从 `summary` 阶段续跑，文本模型使用 `deepseek-v4-flash`，fast RAG 的图片输入使用 `gpt-5-mini`。
- Kimi 单篇最终报告位于 `benchmark_runs/ai20_20260607_005847/aggregate_report.md`；PPTX 输出位于 `outputs/Kimi_K2_Technical_Report/paper/fast/slides_academic_medium_24slides/20260607_010126/slides.pptx`。
- Kimi 单篇结果：1/1 通过，23 页，耗时 298.5 秒，2 个 warning，warning categories 为 `structured_point` 和 `text_overflow`；生成阶段触发过一次 PPTX QA repair，自动调整 9 页。
- 更新下一阶段计划文档：`docs/multistyle_aesthetic_benchmark_plan.zh-CN.md`，用于指导 mature baseline suite、from-scratch template experiment、审美评分、内容组织评分、novelty score 和迭代规则建设。

需要特别说明：

- 当前 QA 汇总命令不会重新下载论文。
- 当前 benchmark 命令不会重新执行 PDF-to-PPT 生成。
- 当前 benchmark 命令统计的是历史输出中的 QA 文件，所以 “30 个 QA run” 不等于 “30 篇论文”。
- 当前 `test_papers/` 已经补齐到 20 篇 PDF；可以用下面的命令检查集合完整性。
- 可以用下面的命令检查当前集合缺失情况：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.papers validate --set ai20
```

如果 `python --version` 没有输出，说明当前终端可能走到了 WindowsApps 的 Python 占位入口；请优先使用上面的 conda 环境 Python。

## 为什么先做历史 QA 汇总

项目早期的质量提升主要来自人工观察 PPT 结果后的多轮迭代，例如：

- 页面空白或组件为空。
- 左右栏 / 上下栏布局与图片、表格素材不匹配。
- 标题越界、正文溢出、缺字、截断省略号。
- metric 卡片 label 太泛或 value 缺失。
- numbered point 缺少 `claim/detail/evidence`。
- 目录页、章节页和普通页在不同论文上稳定性不足。

历史 QA 汇总的意义是把这些人工经验变成可统计、可回归、可面试讲清楚的评价维度。它是从 human-in-the-loop 走向自动 benchmark 的第一步。

## 目标形态

正式版本的 benchmark 应该支持：

```powershell
python -m paper2slides.benchmark run --set ai20 --styles academic,visual,report --slides 24 --fast
```

目标输出：

```text
benchmark_runs/<timestamp>/
  manifest.json
  per_paper_results.json
  aggregate_report.md
  leaderboard.csv
  badcases/
  previews/
```

当前 runner 的实际输出目录格式为：

```text
benchmark_runs/<set>_<timestamp>/
  manifest.json
  per_paper_results.json
  aggregate_report.json
  aggregate_report.md
  logs/
```

核心指标：

- 论文级 pass rate。
- 页面级 severe warning rate。
- warning per slide。
- repair attempts。
- 平均耗时、估算 token、估算成本。
- 版式成功率，例如 academic / visual / report。
- badcase 类型分布。
- 最差论文、最差页面和最差版式。

下一阶段会进一步拆成五类评分：

- `reliability_score`：是否稳定生成，是否缺产物，是否存在严重 QA 错误。
- `content_score`：章节覆盖、目录一致性、slide role 分布、claim/detail/evidence 完整性。
- `visual_layout_score`：溢出、留白、对齐、图片可读性、表格和 metric 可读性。
- `aesthetic_score`：配色协调、层级清楚、字体一致、页面专业感和模板一致性。
- `novelty_score`：用于 from-scratch 新模板实验，检测新模板是否只是 golden baseline 换皮。

## 20 篇论文 Benchmark 数据集计划

`local_12` 已有 12 篇本地论文：

```text
test_papers/2025_AI_Agent_Index.pdf
test_papers/Agentic_Large_Language_Models_Survey.pdf
test_papers/AGI_Is_Coming_Wordle.pdf
test_papers/Deep Residual Learning for Image Recognition.pdf
test_papers/DeepSeek_V4.pdf
test_papers/Deep_Research_Agents_Systematic_Examination.pdf
test_papers/Evaluation_Benchmarking_LLM_Agents_Survey.pdf
test_papers/Infrastructure_for_AI_Agents.pdf
test_papers/LLM_Agent_Survey_Methodology_Applications_Challenges.pdf
test_papers/mHC：Manifold-Constrained Hyper-Connections.pdf
test_papers/Open_Reproducible_Deep_Research_Agent.pdf
test_papers/Thinking_with_Visual_Primitives.pdf
```

已补充 8 篇，使集合达到 20 篇。新增论文已写入 `benchmarks/papers.json` 的 `ai20.additional_papers`：

```text
OpenAI_GPT-5_System_Card.pdf
OpenAI_gpt-oss_Model_Card.pdf
Anthropic_Claude_Opus_4.5_System_Card.pdf
Google_DeepMind_Gemini_2.5_Technical_Report.pdf
DeepSeek_R1.pdf
Kimi_K2_Technical_Report.pdf
ByteDance_Seed_Thinking_v1.5.pdf
Xiaomi_MiMo_VL.pdf
```

补充原则：

- 优先选择官方技术报告、arXiv 论文或机构正式发布的 PDF。
- 覆盖 OpenAI、Anthropic、Google DeepMind / Gemini、DeepSeek、字节 / 豆包、Kimi / Moonshot、MiMo / 小米等方向。
- 同时覆盖大模型、后训练、agent、deep research、模型评估和 benchmark 论文。
- 下载前记录来源 URL、发布时间、组织、标签和许可情况。
- 所有新 PDF 已下载到 `test_papers/`，`benchmarks/papers.json` 中对应条目的 `download_status` 已更新为 `downloaded`。

如需在新机器或清空 `test_papers/` 后复现下载，使用下面的命令下载缺失论文：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.papers download --set ai20
```

也可以使用封装好的脚本，它会在下载前后自动校验：

```powershell
.\benchmarks\download_ai20.ps1
```

## 分阶段实现

### Phase 1：历史 QA 汇总

状态：已完成。

交付物：

- `paper2slides/benchmark/qa_summary.py`
- `paper2slides/benchmark/__main__.py`
- `benchmarks/papers.json`
- `benchmark_runs/local_history/qa_summary.md` 本地生成产物

### Phase 2：20 篇论文清单与下载

状态：已完成。

任务：

- 查找并确认 8 篇新增论文。状态：已完成。
- 在 `benchmarks/papers.json` 中新增 `ai20` 集合。状态：已完成。
- 增加清单校验命令，确认每个 PDF 存在且可读取。状态：已完成。
- 下载 PDF 到 `test_papers/`。状态：已完成。

### Phase 3：批量生成 Runner

状态：已实现，Kimi K2 单篇端到端验证已通过，待全量 20 篇运行。

任务：

- 新增 `paper2slides/benchmark/runner.py`。状态：已完成。
- 根据 manifest 批量执行 `python -m paper2slides --input ... --fast --slides 24`。状态：已完成。
- 支持 `--from-stage generate`，避免重复解析已完成 checkpoint。状态：已完成。
- 记录每篇论文输出目录、运行时间、是否成功、QA 路径和错误信息。状态：已完成。
- 生成 `manifest.json`、`per_paper_results.json`、`aggregate_report.json`、`aggregate_report.md` 和逐论文日志。状态：已完成。
- 将“命令返回 0 但缺少 `layout_qa.json` / PPTX 产物”的情况归类为 `artifact_missing`，避免把产物缺失误报为 unknown。状态：已完成。
- 使用 `DeepSeek_V4.pdf` 这篇论文的历史 24-slide 输出做过 `--resume --limit 1` 冒烟测试。这里的 DeepSeek_V4 是论文文件名，不代表该历史输出由 DeepSeek API 生成。runner 能正确读取输出目录、QA 结果、warning 分类并生成聚合报告。状态：已完成。
- 使用 `Kimi_K2_Technical_Report.pdf` 做过真正的 DeepSeek 文本通道单篇生成验证：先发现 `RAG_LLM_API_KEY` 被误配成视觉模型中转 key，导致 summary 阶段 401；修复为 DeepSeek key 后，从 `--from-stage summary` 续跑成功。状态：已完成。

Kimi 单篇验证命令：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic --slides 24 --start-index 17 --limit 1 --from-stage summary
```

这次验证的意义：

- 证明文本模型和视觉模型没有混淆：summary / plan / PPTX curator 使用 `deepseek-v4-flash`；fast RAG 的图片输入使用 `gpt-5-mini`。
- 证明已有 checkpoint 可以复用：不需要重新跑耗时较长的 MinerU 解析和 fast RAG。
- 证明 benchmark runner 可以收集单篇输出目录、QA 路径、耗时、warning category 和日志。
- 证明当前已有自动修复闭环雏形：生成后 QA 检出问题，PPTX QA repair 对 9 页做了调整，最终 QA 通过，仅剩 2 个 warning。

推荐先冒烟测试一篇：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic --slides 24 --limit 1
```

全量运行：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic --slides 24 --resume
```

### Phase 4：成熟套件回归与从零模板 Benchmark

状态：方向已更新，待按新路线实现。

#### Phase 4A：成熟套件回归

成熟套件包括：

```text
academic
academic_warm
editorial
editorial_mono
data_report
```

定位：

- `academic` 是 golden baseline。
- 其余样式是 baseline companion styles。
- 它们用于稳定生成和全量回归，不再作为“全新模板设计”的主线。

任务：

- 保护当前 `academic` 模板作为 golden baseline。状态：持续要求。
- 保留 `academic_warm`、`editorial`、`editorial_mono`、`data_report`。状态：人工确认保留。
- 对 mature suite 跑 Kimi 单篇和 ai20 全量回归。状态：待实现。
- 输出 mature style leaderboard、warning rate、artifact success、QA pass rate。状态：待实现。
- 修复 `data_report` 当前主色偏怪、部分颜色/文字排版问题。状态：待实现。

#### Phase 4B：从零模板实验

目标不是继续给 baseline 换皮，而是建立一个从已解析论文内容到全新 PPT 风格的迭代流程。

任务：

- 从 Kimi K2 已有 checkpoint 生成 `content_inventory`。状态：待实现。
- 先生成“不追求好看但内容完整”的无审美草稿。状态：待实现。
- 重新设计章节、目录、slide role、claim、proof object。状态：待实现。
- 设计完全独立于 golden baseline 的视觉系统。状态：待实现。
- 新增 `novelty_score` 或 baseline similarity 检测，防止新模板只是换皮。状态：待实现。
- 将人工反馈沉淀为 badcase rule、检测规则和修复建议。状态：待实现。
- 用 Kimi K2 单篇先迭代 2-3 轮，再扩展到 4 篇小集合，最后再跑 ai20。状态：待实现。

推荐第一轮实现顺序：

1. 冻结 mature suite：`academic,academic_warm,editorial,editorial_mono,data_report`。
2. 生成 Kimi K2 的 content inventory。
3. 做一个无审美草稿，先保证内容完整。
4. 设计第一套完全不同于 golden baseline 的新模板。
5. 跑 Kimi K2 单篇，记录内容缺失、溢出、图文不匹配、审美问题和 baseline similarity。
6. 只修 Top 1-3 个主要矛盾。
7. 把每个问题和修复策略写入 benchmark rule。

详细方案见：`docs/multistyle_aesthetic_benchmark_plan.zh-CN.md`。

新窗口继续本任务时，第一轮建议只做规划，不直接改代码、不直接跑 Kimi K2 生成。应该先确认：

- mature suite 与 from-scratch experiment 的边界是否清楚。
- `content_inventory.json` 和 rough draft spec 的 schema 是否能承载 Kimi K2 已解析内容。
- slide role / proof object / claim-detail-evidence 的定义是否足够明确。
- `reliability_score`、`content_score`、`visual_layout_score`、`aesthetic_score`、`novelty_score` 的第一版规则型实现是否可落地。
- 人工反馈如何转成 badcase rule、repair hint 和 regression case。

完整交接提示见：`docs/next_window_handoff.zh-CN.md`。

### Phase 5：自动修复与迭代建议

状态：已有 PPTX QA repair 雏形，待升级为 benchmark 驱动的多模板修复闭环。

任务：

- 根据 badcase 类型生成修复建议。
- 对 spec 层问题优先走局部 spec repair。
- 对 renderer / layout 层问题输出可人工确认的代码修改建议。
- 保留每次迭代前后的 benchmark 对比报告，形成面试可讲的 regression evidence。
- 把每次修复前后的 `aggregate_report.json` 和 `aggregate_report.md` 进行 diff，生成 pass rate / warning rate / aesthetic score 曲线。
- 将“好看”拆成配色、对比度、视觉层级、字体一致性、留白平衡、专业感等可观测指标。
- 对视觉 judge 保持可控成本：先用规则分数，必要时只对最差页面截图调用视觉模型。

## 面试讲法

可以这样概括：

> 这个项目早期靠人工看 PPT 找问题，例如缺字、空页、左右栏不匹配、metric 卡片质量差。现在我把这些人工验收标准工程化为 benchmark，先从历史 QA 文件中抽取 badcase 类型和统计分布，再扩展到 20 篇论文、多模板、多轮自动评估和局部返修。它不是单纯生成 PPT，而是把 agent 输出物变成可评估、可回归、可自动迭代的工程系统。

进一步可以这样讲审美评估：

> 我把 PPT 质量拆成可靠性、内容组织、视觉排版和审美四类指标。可靠性保证能生成且没有严重错误；内容组织检查目录、章节、核心贡献和 evidence；视觉排版检查溢出、留白、对齐和素材匹配；审美则量化配色、对比、层级、字体一致性和专业感。这样 benchmark 不只是找 bug，也能驱动模板设计和审美质量提升。

## 2026-06-12 追加：把 v1-v6 人类审美反馈纳入 Benchmark

Kimi K2 from-scratch track 已经完成多轮人工反馈迭代，当前最重要的新结论是：

```text
rough_draft_v5.pptx 是当前人工接受的审美参考；
rough_draft_v6.pptx 是一次局部自动优化导致整体观感下降的回归样本。
```

因此 benchmark 需要新增一类能力：不仅能判断“有没有生成成功”和“有没有文本溢出”，还要能记录人类偏好、检测审美回归，并把每次反馈转成可复用规则。

本轮新增机器可读规则文件：

```text
benchmarks/from_scratch_human_feedback_benchmark.json
```

它补充了以下内容：

- accepted reference：`rough_draft_v5.pptx`。
- iteration log：v1-v6 每轮问题、用户反馈和修复策略。
- badcase rules：缺标题页、缺目录页、版式单调、短文本大空框、表格缺行、组件遮挡、黑白枯燥、封面统计无意义、agenda 侧栏干、v6 过度优化回归等。
- aesthetic rubric：将“好看”拆成 academic polish、palette vitality、layout variety、evidence readability、typography density、visual review readiness、novelty without content loss。
- automatic review strategy：优先使用低成本 PPTX 元数据检查，只对高风险页或代表页截图和视觉判断。

这部分经验会改变下一阶段自动 benchmark 的设计：

1. **当前阶段不做截图/视觉模型评审**：只做 shape overlap、字体大小、text density、table rows、metric grammar、layout repetition 等非视觉检查。
2. **低密度不是自动缩组件的理由**：组件比例和构图如果已经被人类认可，先调整字体、copy 分配、行文强弱，而不是直接改变卡片/面板尺寸。
3. **视觉改动要和 v5 对比**：任何改变 v5 主要视觉语法的规则，都需要证明更好或获得人工确认。
4. **把回退也记录为经验**：v6 的 2x2 read path 和过度压缩 evidence cards 不是单纯失败，而是未来自动 repair loop 需要避免重复犯的 regression case。
5. **继续复用已解析论文内容**：from-scratch track 仍然从 checkpoint_summary / checkpoint_plan / checkpoint_slide_spec 出发，不重跑已稳定的 PDF 解析链路。

后续 runner 可以逐步接入这个规则文件，形成如下闭环：

```text
generate vN
 -> run PPTX metadata-only checks
 -> estimate font, text capacity, overlap, table grammar, metric grammar
 -> compare against accepted reference rules when visual grammar changes
 -> emit badcase hits and repair hints
 -> repair Top 1-3 issues without resizing accepted components by default
 -> record whether vN improves or regresses from v5
```

新增非视觉审查命令：

```powershell
python -m paper2slides.benchmark nonvisual-audit --pptx <deck.pptx> --output <nonvisual_audit.json>
```

## 2026-06-12 再追加：Benchmark 驱动的非视觉自动纠偏路线

当前最新共识是：下一阶段不再把 `--render-review-dir`、单页截图和视觉模型作为默认审美闭环。默认路线改为：

```text
PPTX metadata-only audit
```

也就是直接读取 PPTX 的结构化对象，检查页面角色、组件位置、文本容量、字体大小、表格语法、metric 语法、layout family 分布和 badcase rule 命中。

### 自动生成流程

针对一篇新论文，benchmark runner 未来应按下面顺序工作：

1. **复用解析结果**：优先使用 `checkpoint_summary.json`、`checkpoint_plan.json`、`checkpoint_slide_spec.json`、figure/table/metric 结果，不重跑稳定的 PDF 解析链路。
2. **生成 content inventory**：收集论文标题、作者、核心贡献、章节、figures、tables、metrics、source evidence。
3. **生成 deck architecture**：确定这是 academic paper-reading deck，并生成 title、agenda、section divider、content slides、closing。
4. **生成 slide semantic map**：每页只保留一个主 claim，配 support 和 proof object。
5. **生成 style contract**：确定 palette、typography、layout families、proof-object grammar、metric/table/card 语法和禁止项。
6. **渲染第一版 PPTX**：先让内容和组件语法完整，不追求靠局部参数一次到位。
7. **运行非视觉审计**：输出 `nonvisual_audit.json`，包含 overlap、font、capacity、density、table、metric、layout repetition 等 findings。
8. **按优先级修复**：每轮只修 Top 1-3 个 badcases。
9. **对比 accepted reference / previous attempt**：如果改动破坏 v5 类似的已接受构图，必须阻止或记录为 style-contract 变更。
10. **输出 benchmark report**：记录分数、badcase、修复建议、是否停止。

### 非视觉纠偏原则

修复顺序必须保持稳定：

```text
内容正确性 > deck 架构 > 语义匹配 > 字体/文案 > 几何位置 > 视觉系统改版
```

具体规则：

- 缺表格行、缺指标值、缺 evidence 时，先回到内容/Spec 层修。
- 缺标题页、目录页、章节页、结尾页时，先修 deck architecture。
- claim 和 proof object 不匹配时，先修 slide semantic map。
- 字体偏小或文字稀疏时，先改字号、换行、文案分配。
- 只有遮挡、越界、表格不可读、连续重复布局时，才移动或缩放组件。
- 低密度不应自动触发组件缩小；v6 已经证明这会伤害整体观感。
- 视觉系统级改动必须显式进入 `style_contract`，并和 accepted reference 对比。

### 新增评分维度落地方式

当前 benchmark 的五类评分可以这样落地：

- `reliability_score`：命令是否成功，产物是否完整，QA/审计是否能运行。
- `content_score`：章节覆盖、claim/support/evidence、table/figure/metric 保存情况。
- `visual_layout_score`：overlap、out-of-bounds、font floors、text capacity、table readability。
- `aesthetic_score`：用非视觉代理指标估计：deck 结构完整、layout rhythm、palette 语义、组件语法一致、低密度不过度修、accepted grammar 不被破坏。
- `novelty_score`：检查是否复用 golden baseline 的 header/key-message/numbered-point/macro skeleton。

注意：当前阶段的 `aesthetic_score` 不是像素级审美真值，而是工程化代理分数。它用于自动发现大多数结构性审美问题，并保护已经被人类认可的构图方向。

### Stop Condition

自动修复应该有停止条件，避免越修越怪：

- 没有 high / medium non-visual findings。
- 剩余问题主要是低密度或轻微字号风险，继续修会破坏组件比例。
- 连续两轮 content/layout 分数不再提升。
- 修复建议要求改变 accepted reference 的主要视觉语法，但没有新的 style-contract 批准。

这让 benchmark 从“生成后检查”升级为“可控自动迭代系统”：能自己发现问题、知道先修什么、知道什么时候停。

## 2026-06-13 追加：布局确定后的 Typography / Copy Fitting 阶段

当前 from-scratch PPT 的组件搭配、整体构图和 warm academic 风格已经基本被用户认可。下一阶段 benchmark 不应继续大改组件，而应进入第二层 polish：

```text
good component composition
 -> typography fitting
 -> copy density fitting
 -> minimal geometry repair only if necessary
```

### 阶段目标

让系统在不依赖截图和视觉模型的情况下，自动判断：

- 哪些页面文字偏少但组件不应缩小。
- 哪些正文、卡片、表格或 metric 字号偏小。
- 哪些文本框接近容量上限。
- 哪些卡片文字层级弱、显得空。
- 哪些问题可以通过字号、行距、换行、文案分配解决。
- 哪些问题才需要微调组件大小或位置。

### 检查项

下一轮 `nonvisual-audit` 或 repair runner 应逐步补充这些规则：

| 维度 | 可检测信号 | 默认修复 |
| --- | --- | --- |
| font floor | 按 title/claim/support/card/table/footer 检查字号下限 | 提升字号或改文本角色 |
| ideal font band | 字号虽未违规但低于推荐范围 | 轻微增大字号 |
| text capacity | 词数 / 文本框面积接近上限 | 压缩文案、拆分 notes、调整换行 |
| low density | 大卡片中词数过少 | 只提示；优先增强文案或层级，不缩组件 |
| hierarchy weakness | claim/support/card 字号差距不足 | 调整字号层级和字重 |
| card copy split | 三张 evidence cards 内容分配严重不均 | 重新分配 reading notes |
| table readability | 表格字号过小或列宽不足 | 优先调表格字体/列宽，必要时拆页 |
| geometry necessity | overlap/out-of-bounds/unreadable table | 才允许移动或缩放组件 |

### 修复顺序

本阶段的修复顺序更细化为：

1. 保留当前 accepted component composition。
2. 提升低于角色下限的字号。
3. 调整标题、claim、support、card label、card body 的层级比例。
4. 对短文本补充信息量或改成更强的 reading note。
5. 对长文本做压缩、拆句、换行或 notes 分配。
6. 只有结构性失败时才改组件大小或位置。
7. 任何 geometry 改动都要记录原因，不能只写“文字少所以缩小”。

### 需要沉淀的 badcase

未来 human-in-the-loop 发现问题时，应按下面方向沉淀：

- `body_font_too_small`
- `card_font_too_small`
- `weak_typography_hierarchy`
- `sparse_card_copy`
- `overcompressed_card_regression`
- `copy_density_mismatch`
- `geometry_changed_without_structural_need`

这些 badcase 应继续写入 `benchmarks/from_scratch_human_feedback_benchmark.json`，并在测试中保护摘要字段。
