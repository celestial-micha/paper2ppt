# paper2ppt

[English](README.md) | [中文](README.zh-CN.md)

paper2ppt 可以把学术 PDF 论文转换成可编辑的 PowerPoint 和配套演讲稿。

当前项目目标是服务真实论文汇报：复用论文原始图片和表格，只使用文本大模型做规划和写作，渲染原生可编辑 `.pptx`，并围绕输出做面向 slide spec 和版式的 QA / 自动修复。

本项目基于 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides) 的论文处理思路和部分代码路径继续改造，同时也参考了 [gejifeng/Paper2PPT](https://github.com/gejifeng/Paper2PPT) 在章节化讲解和 TeX/Beamer 汇报上的设计思路。当前仓库的主实现仍然是基于 `paper2slides/` 的工作流，只是已经被重度改造成“纯文本大模型调用 + 原生 PPTX 生成”的路线。

![paper2ppt 效果预览](paper2ppt_preview.jpg)

## 项目来源与主要改造

从 HKUDS/Paper2Slides 中，本项目保留了有价值的论文处理基础：

- PDF 解析和论文原始素材抽取。
- 摘要、内容规划和 checkpoint 式重跑。
- 从论文生成汇报材料的命令行工作流。

本项目最核心的变化是生成路径：原先偏图片式的幻灯片生成路线，被替换成了成本更低、可编辑性更强的纯文本大模型工作流：

- 由模型规划结构化 slide spec，而不是生成整页幻灯片图片。
- 使用 `python-pptx` 渲染原生可编辑 PowerPoint 对象，包括文本框、形状、表格和论文原图。
- 模型调用统一走兼容 OpenAI chat-completions 的配置；当前模板默认使用 DeepSeek。
- 同步生成配套的 `speaker_script.md` 演讲稿。
- 增加 slide spec evaluator 和 layout QA，检查空组件、截断文本、指标卡质量、缺失结构化字段、布局与素材不匹配、无意义装饰元素。
- numbered point 在渲染前会被规范化为 `claim`、`detail`、`evidence` 三个字段。
- 增加更像正式汇报的结构：标题页、目录页、章节分隔页、key message、编号 claim/detail/evidence 要点、论文原图和紧凑指标卡。

从 gejifeng/Paper2PPT 中，本项目主要借鉴产品思路，而不是运行时依赖它的代码：

- 更强的章节化论文讲解方式。
- 面向长技术论文的详细补充材料思路。
- 可选的轻量 Beamer/TeX 旁路生成能力，该能力由本仓库自己的代码实现。

本仓库不内置 Paper2PPT，也不在运行时依赖 Paper2PPT。

## 当前状态

项目现在支持：

- 可编辑 PowerPoint 输出：`slides.pptx`。
- 配套讲稿：`speaker_script.md`。
- 可选的轻量 Beamer/TeX 旁路，由本仓库自己的代码生成。它是参考/备份路径，不是主交付物。
- 基于 LangChain/LangGraph 的文本大模型工作流。
- 通过 `.env` 配置 DeepSeek / OpenAI-compatible 文本模型。
- 使用 `--slides` 精确指定目标页数。
- 带章节意识的 PPT：标题页、目录页、章节分隔页、key message、结构化编号要点、紧凑指标卡、论文原图和表格。
- slide spec evaluator 和 PPTX 排版 QA。
- 有上限的修复循环，只修改失败页面的 slide spec，并重新渲染。
- 对不支持的 LLM layout 名称、缺少图片的视觉布局、缺少表格的表格布局做自动规范化。
- 双模型路由：文本生成使用 `deepseek-v4-flash`；图片/多模态调用使用 `gpt-5-mini`。
- 使用 `PPTX_FORCE_DETERMINISTIC=1` 从已有 checkpoint 低成本重跑 deterministic fallback。

最近一轮视觉迭代重点是让生成结果更像正式 PPT：

- 增加正式标题页，包含标题、作者、上下文/日期和右下角信息块。
- 增加目录页，并把右侧横线改成有意义的章节进度线。
- 增加章节分隔页。
- 普通页改成“标题栏 + Key message + 结构化编号要点”。
- 删除编号要点旁边无意义的小横杠。
- 恢复有价值的装饰横线和信息块，但让它们承载真实信息。
- 改进 bullet 渲染，使每条呈现“短 claim + 完整 detail 句子”，并保留 evidence 字段用于 QA 和讲稿。
- 增加 evaluator 驱动的修复逻辑，覆盖缺失要点字段、低质量 metric label/value、空组件、不支持的 layout、视觉/表格布局素材不匹配和严重版式缺陷。

## 推荐测试 PDF

当前主要本地测试论文是：

```text
test_papers/DeepSeek_V4.pdf
```

最近开发时检查的输出位于：

```text
outputs/DeepSeek_V4/paper/fast/slides_academic_medium_24slides/
```

此外也用以下论文做过跨论文验证：

```text
test_papers/Deep Residual Learning for Image Recognition.pdf
test_papers/Thinking_with_Visual_Primitives.pdf
test_papers/mHC：Manifold-Constrained Hyper-Connections.pdf
```

具体时间戳目录会随每次运行变化。成功运行后一般包含：

```text
slides.pptx
speaker_script.md
layout_qa.json
```

部分运行还可能包含：

```text
detailed_slides.tex
detailed_slides.pdf
```

这些 TeX/PDF 文件是可选参考产物。项目的主交付物仍然是 `slides.pptx` 和 `speaker_script.md`。

## 工作流程

```text
PDF
 -> 论文解析和原始素材抽取
 -> summary checkpoint
 -> content plan checkpoint
 -> LangGraph PPTX workflow
    -> source packet
    -> 可选的论文原图理解
    -> 文本大模型策划 deck spec
    -> slide spec 校验和 numbered point 规范化
    -> 原生 PPTX 渲染
    -> spec evaluator + layout QA
    -> 失败页面修复循环
    -> 生成 speaker script
    -> 可选生成详细版 Beamer/TeX 旁路
```

关于 evaluator 驱动闭环的流程图和面试讲解，可查看 [Agentic PPTX Workflow](docs/agent_workflow.md)。

生成的 PPTX 不是截图，也不是整页图片。它使用 PowerPoint 原生文本框、形状、表格和插入的论文原图，因此可以继续在 PowerPoint 里编辑。

## 环境要求

- Windows、macOS 或 Linux
- Python 3.10 或更新版本，推荐 Python 3.12
- Conda 或其他 Python 环境管理工具
- 一个兼容 OpenAI chat-completions 接口的文本模型 API

本项目开发时使用的本地 conda 环境名是 `paper2slides`，但环境名不是硬性要求。

## 安装

```powershell
conda create -n paper2ppt python=3.12
conda activate paper2ppt
pip install -r requirements.txt
```

如果你已经有合适的 Python 环境：

```powershell
pip install -r requirements.txt
```

## 配置 API

paper2ppt 从这里读取 API 配置：

```text
paper2slides/.env
```

为了避免上传 GitHub 泄露 key，仓库里只应该提交模板：

```text
paper2slides/.env.example
```

如果是新克隆的仓库，可以从模板复制本地 env 文件：

```powershell
copy paper2slides\.env.example paper2slides\.env
```

不要提交本地的 `paper2slides/.env` 文件。

典型配置：

```env
RAG_LLM_API_KEY=your_api_key_here
RAG_LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
RAG_LLM_MAX_TOKENS=8192
RAG_FAST_INCLUDE_IMAGES=1
RAG_VISION_MODEL=gpt-5-mini
RAG_VISION_API_KEY=your_openai_or_vision_api_key_here
```

可选的 PPTX 专用模型覆盖：

```env
PPTX_LLM_MODEL=deepseek-v4-flash
```

如果不需要调用模型，只想从已有 checkpoint 重渲染：

```env
PPTX_FORCE_DETERMINISTIC=1
```

可选的论文原图理解：

```env
PPTX_ENABLE_FIGURE_ANALYSIS=auto
PPTX_VISION_MODEL=gpt-5-mini
PPTX_VISION_API_KEY=your_openai_or_vision_api_key_here
PPTX_MAX_FIGURE_ANALYSIS=5
```

这一步只分析论文原图，不生成新图片。`auto` 模式只在图片 caption 看起来不足以支撑 slide curation 时自动开启。也可以用 `1` 强制开启，或用 `0` 强制关闭。需要注意模型路由不要混淆：DeepSeek 负责文本调用，启用图片输入时由 `gpt-5-mini` 处理。

fast paper 模式下会跳过冗余的 `paper_info` RAG 查询；论文标题、作者等元数据仍由 summary 阶段从解析后的 markdown 中抽取。

## 运行

典型运行：

```powershell
python -m paper2slides --input test_papers\DeepSeek_V4.pdf --output slides --style academic --length medium --slides 24 --fast
```

从已有 checkpoint 低成本重跑生成阶段：

```powershell
$env:PPTX_FORCE_DETERMINISTIC="1"
python -m paper2slides --input test_papers\DeepSeek_V4.pdf --output slides --style academic --length medium --slides 24 --fast --from-stage generate
```

常用参数：

```text
--input       PDF 文件路径
--output      slides
--style       academic 或自定义风格描述
--length      short、medium 或 long
--slides      精确指定目标内容页数，会覆盖 --length
--fast        使用直接解析/查询流程，不跑完整索引
--from-stage  rag、summary、plan 或 generate
--list        列出历史输出
--debug       输出更多日志
```

动态页数范围：

```text
short   大约 8-12 页内容页
medium  大约 14-22 页内容页
long    大约 24-36 页内容页
```

长论文建议使用 `--slides 24` 或类似显式页数，让覆盖更充分。

## 输出文件

典型时间戳输出目录：

```text
outputs/<project_name>/paper/fast/slides_academic_medium_24slides/<timestamp>/
```

常见文件：

```text
slides.pptx
speaker_script.md
layout_qa.json
checkpoint_slide_spec.json
checkpoint_slide_spec_llm_raw.txt
```

含义：

- `slides.pptx`：可编辑 PowerPoint。
- `speaker_script.md`：逐页讲稿草稿。
- `detailed_slides.tex` / `detailed_slides.pdf`：可选参考产物；启用旁路且本机有 `pdflatex` 时由本项目代码生成。
- `layout_qa.json`：spec 和排版 QA 结果，包含 warnings 和失败页面索引。
- `checkpoint_slide_spec.json`：最终结构化 slide spec，编号要点包含 `claim`、`detail`、`evidence` 字段。
- `checkpoint_slide_spec_llm_raw.txt`：如果调用了 curator LLM，会保存原始输出。

## 重要实现文件

```text
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/pptx_qa.py
paper2slides/generator/slide_schema.py
paper2slides/generator/spec_builder.py
paper2slides/generator/content_planner.py
paper2slides/generator/detailed_tex.py
paper2slides/core/stages/rag_stage.py
paper2slides/core/stages/generate_stage.py
paper2slides/core/paths.py
```

## 测试

```powershell
python -m unittest test_phase1_pptx.py
```

## Benchmark 种子

仓库里已经加入第一版 benchmark 种子，用来把之前 human-in-the-loop 的 QA 经验整理成自动化报告：

```powershell
python -m paper2slides.benchmark --outputs outputs --report-dir benchmark_runs\local_history
```

它会扫描已有的 `layout_qa.json`，把 warning 归类成稳定的 badcase 类型，并写出 `qa_summary.md` 和 `qa_summary.json`。这一版还不会重新跑 PDF-to-PPT 生成。论文清单位于 `benchmarks/papers.json`；当前 `ai20` 已经由原本 12 篇本地论文加 8 篇新增的大模型、推理、agent/评估报告组成。

当前已用 `Kimi_K2_Technical_Report.pdf` 做过一次单篇端到端验证：从 `summary` 阶段续跑，文本调用使用 `deepseek-v4-flash`，图片输入/多模态调用使用 `gpt-5-mini`，最终 1/1 通过、23 页、2 个 warning。报告位于 `benchmark_runs/ai20_20260607_005847/aggregate_report.md`。

下一阶段计划不是继续只打磨单一模板，而是保护当前 `academic` 模板作为 golden baseline，并扩展多模板与审美 benchmark。当前 from-scratch track 已把 Kimi K2 的 `rough_draft_v10_component_reflow` 记录为 candidate style，并在 mHC 验证中推进到 `mHC_v14_table_support_balance`；benchmark 规则已经覆盖宽图比例路由、inline table payload、浅窄卡片内部间距、agenda Read path 标题 clearance 和 table-bottom support band balance。最新路线拆成两条：

- 成熟套件回归：保留 `academic`，并将 `academic_warm`、`editorial`、`editorial_mono`、`data_report` 作为 baseline companion styles，用于稳定生成和 ai20 回归。
- 从零模板实验：不模仿 golden baseline 的视觉骨架，从已解析论文内容出发，先生成 content inventory 和无审美草稿，再逐步设计章节、页面角色、proof object、视觉系统和自动评估规则。

详细计划见：

```text
docs/benchmark_plan.zh-CN.md
docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
docs/next_window_handoff.zh-CN.md
```

校验 `ai20` 论文集合：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.papers validate --set ai20
```

如果在新机器上需要重新下载缺失的 `ai20` 论文，推荐使用：

```powershell
.\benchmarks\download_ai20.ps1
```

运行 `ai20` 批量 benchmark：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic --slides 24 --resume
```

如果只想先做低风险冒烟测试，可以加 `--limit 1`。报告会写到 `benchmark_runs/<set>_<timestamp>/`。

不写 `__pycache__` 的快速语法检查：

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
python -c "import ast, pathlib; ast.parse(pathlib.Path('paper2slides/generator/pptx_renderer.py').read_text(encoding='utf-8')); print('AST OK')"
```


## 常见问题

如果 API 调用失败：

- 检查 `paper2slides/.env`。
- 检查 `RAG_LLM_BASE_URL`。
- 检查所选模型是否支持足够长的上下文。

如果 PPT 太空或太密：

- 尝试不同 `--length`。
- 使用 `--slides 24` 或其他显式页数。
- 从 `--from-stage generate` 重跑。

如果接口临时不稳定或只想低成本重跑：

- 设置 `PPTX_FORCE_DETERMINISTIC=1`。

如果某页看起来拥挤或被截断：

- 查看 `layout_qa.json`。
- 尽可能从保存后的 PPTX 渲染预览图检查。

## 项目来源

paper2ppt 基于 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides) 改造，并参考了 [gejifeng/Paper2PPT](https://github.com/gejifeng/Paper2PPT) 的汇报组织思路。如果继续分发或扩展本项目，请保留上游来源说明和许可证要求。
