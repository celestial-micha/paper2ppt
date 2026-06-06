# paper2ppt 自动 Benchmark 计划

本文档记录 paper2ppt 从 human-in-the-loop 人工验收到自动 benchmark / 自动迭代系统的建设计划。

## 当前状态

截至当前版本，已经完成的是 **历史 QA 汇总型 benchmark 种子**、**20 篇论文 benchmark 数据集准备**、**批量生成 runner 实现**，以及 **Kimi K2 单篇端到端生成与 QA 验证**。下一阶段重点不是盲目改当前已经成熟的 academic 模板，而是在保护它作为 golden baseline 的前提下，扩展多模板 benchmark，并把评估维度升级到内容组织、视觉排版和审美质量。

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
- 新增下一阶段计划文档：`docs/multistyle_aesthetic_benchmark_plan.zh-CN.md`，用于指导多模板、审美评分、内容组织评分和迭代曲线建设。

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

下一阶段会进一步拆成四类评分：

- `reliability_score`：是否稳定生成，是否缺产物，是否存在严重 QA 错误。
- `content_score`：章节覆盖、目录一致性、slide role 分布、claim/detail/evidence 完整性。
- `visual_layout_score`：溢出、留白、对齐、图片可读性、表格和 metric 可读性。
- `aesthetic_score`：配色协调、层级清楚、字体一致、页面专业感和模板一致性。

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

### Phase 4：多模板与审美 Benchmark

状态：已完成方案设计，待实现。

任务：

- 保护当前 `academic` 模板作为 golden baseline。状态：规划完成。
- 抽象 style / layout preset，建议新增 `paper2slides/generator/style_presets.py`。状态：待实现。
- 第一批新增 `editorial`、`conference`、`systems`、`data_report`、`visual_explainer` 等模板。状态：待实现。
- 同一篇论文复用解析、RAG、summary 和 plan checkpoint；只在模板视觉层变化时从 `--from-stage generate` 低成本重跑。状态：待实现。
- 如果模板需要改变内容组织策略，再从 `--from-stage plan` 重跑，而不是重新解析 PDF。状态：待实现。
- 输出不同模板的 pass rate、warning rate、content score、visual layout score、aesthetic score 和 overall score。状态：待实现。
- 输出 style leaderboard、最差页面、最差模板、每篇论文推荐模板。状态：待实现。

推荐第一轮实现顺序：

1. 先实现 `editorial` 和 `systems` 两个模板。
2. 用 Kimi K2 从 `--from-stage generate` 跑 `academic,editorial,systems`。
3. 记录初始 warning 和审美问题。
4. 只修主要矛盾，再重跑同一集合。
5. 形成第一张“迭代前后对比曲线”。

详细方案见：`docs/multistyle_aesthetic_benchmark_plan.zh-CN.md`。

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
