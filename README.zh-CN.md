# paper2ppt

[English](README.md) | [中文](README.zh-CN.md)

paper2ppt 是一个“论文转原生 PPTX + PPTX 质量检测评估 Benchmark + 返修闭环”项目。它可以把学术 PDF 论文转换成可编辑 PowerPoint、配套演讲稿，以及机器可读的质量评估报告。

当前项目目标已经不只是“一次性生成 PPT”。更准确地说，它是一套面向论文汇报的闭环工作流：论文只解析一次，生成多条候选路线，把生成 PPT 或外部 PPTX 转成统一 DeckIR，再用 universal scorecard 做可追溯评测，最后把 audit / repair / human feedback 记录沉淀成可复用的 benchmark 规则。

本项目基于 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides) 的论文处理思路和部分代码路径继续改造，同时也参考了 [gejifeng/Paper2PPT](https://github.com/gejifeng/Paper2PPT) 在章节化讲解和 TeX/Beamer 汇报上的设计思路。当前仓库的主实现仍然是基于 `paper2slides/` 的工作流，只是已经被重度改造成“纯文本大模型调用 + 原生 PPTX 生成”的路线。

![paper2ppt 效果预览](paper2ppt_preview.jpg)

## 项目来源与主要改造

从 HKUDS/Paper2Slides 中，本项目保留了有价值的论文处理基础：

- PDF 解析和论文原始素材抽取。
- 摘要、内容规划和 checkpoint 式重跑。
- 从论文生成汇报材料的命令行工作流。

第一层核心变化是生成路径：原先偏图片式的幻灯片生成路线，被替换成了成本更低、可编辑性更强的纯文本大模型工作流：

- 由模型规划结构化 slide spec，而不是生成整页幻灯片图片。
- 使用 `python-pptx` 渲染原生可编辑 PowerPoint 对象，包括文本框、形状、表格和论文原图。
- 模型调用统一走兼容 OpenAI chat-completions 的配置；当前模板默认使用 DeepSeek。
- 同步生成配套的 `speaker_script.md` 演讲稿。
- 增加 slide spec evaluator 和 layout QA，检查空组件、截断文本、指标卡质量、缺失结构化字段、布局与素材不匹配、无意义装饰元素。
- numbered point 在渲染前会被规范化为 `claim`、`detail`、`evidence` 三个字段。
- 增加更像正式汇报的结构：标题页、目录页、章节分隔页、key message、编号 claim/detail/evidence 要点、论文原图和紧凑指标卡。

第二层核心变化是评测路径：仓库现在把 PPTX 当成可检查的结构化产物，而不只是视觉结果：

- parse-once checkpoint 让同一篇论文可以低成本分支到多条风格路线。
- nonvisual PPTX audit 直接从 PowerPoint 元数据检查几何、字体、文本容量、表格/图片使用、证据结构和返修风险。
- DeckIR 把原生 PPTX 转成统一中间表示，使 paper2ppt 生成结果、frozen baseline、人工 PPT、其他 PPT 生成器都能进入同一套 benchmark。
- universal scorecard v0 评估可编辑性、内容对齐、证据支撑、布局几何、字体层级、视觉代理指标和 human-feedback 状态。
- repair log 和 frozen reference 让每次风格实验都能复现，而不是只依赖一次主观观感。

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
- parse-once benchmark：同一篇论文解析一次后分支到 frozen baseline、seed-template 草稿和实验路线。
- metadata-only `nonvisual-audit`：不用大量截图也能做 PPTX 质量检测。
- universal PPTX intake：为生成或外部 PPTX 写出 `deck_ir.json`、`universal_scorecard.v0.json` 和 schema。
- six-way / universal benchmark runner：比较 route 质量、repair log、style drift 和 score curve。
- PPT-master-inspired seed pipeline：strategist、spec lock、seed template package、visual probe、template gate、human-feedback packet 和 full-deck seed renderer。
- 受保护的 frozen references：`academic`、`golden_baseline1_from_scratch_warm_academic`、`golden_baseline2_blind_rectangular_research_board`。

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
 -> benchmark / evaluation layer
    -> nonvisual PPTX audit
    -> 生成或外部 PPTX 的 DeckIR intake
    -> universal scorecard v0
    -> repair log、score curve 和 frozen-reference 对比
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
nonvisual_audit.json
deck_ir.json
universal_scorecard.v0.json
repair_log.json
```

含义：

- `slides.pptx`：可编辑 PowerPoint。
- `speaker_script.md`：逐页讲稿草稿。
- `detailed_slides.tex` / `detailed_slides.pdf`：可选参考产物；启用旁路且本机有 `pdflatex` 时由本项目代码生成。
- `layout_qa.json`：spec 和排版 QA 结果，包含 warnings 和失败页面索引。
- `checkpoint_slide_spec.json`：最终结构化 slide spec，编号要点包含 `claim`、`detail`、`evidence` 字段。
- `checkpoint_slide_spec_llm_raw.txt`：如果调用了 curator LLM，会保存原始输出。
- `nonvisual_audit.json`：基于 PPTX 元数据、几何、字体、文本容量、表格、图片和返修风险的确定性质量检测。
- `deck_ir.json`：统一 DeckIR 表示，用于跨生成器比较原生 PPTX。
- `universal_scorecard.v0.json`：跨 deck 的 benchmark 评分卡，包含可编辑性、内容、证据、布局、字体、视觉代理指标和 feedback 维度。
- `repair_log.json`：benchmark route 的有界返修和 materialization 记录。

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
paper2slides/benchmark/nonvisual_audit.py
paper2slides/benchmark/sixway.py
paper2slides/benchmark/universal/deck_ir.py
paper2slides/benchmark/universal/pptx_intake.py
paper2slides/benchmark/universal/runner.py
paper2slides/benchmark/seed_pipeline/strategist.py
paper2slides/benchmark/seed_pipeline/template_package.py
paper2slides/benchmark/seed_pipeline/template_gate.py
paper2slides/benchmark/seed_pipeline/full_deck_renderer.py
```

## 测试

```powershell
python -m unittest test_phase1_pptx.py
```

## PPTX Benchmark 与评测闭环

仓库现在包含一层通用 PPTX benchmark，用来把生成或外部 PPTX 变成可比较的质量证据：

```powershell
python -m paper2slides.benchmark --outputs outputs --report-dir benchmark_runs\local_history
```

上面的 legacy 命令会扫描已有的 `layout_qa.json`，把 warning 归类成稳定 badcase，并写出 `qa_summary.md` 和 `qa_summary.json`。新的 benchmark 层直接作用于 PPTX：

```powershell
python -m paper2slides.benchmark nonvisual-audit `
  --pptx path\to\slides.pptx `
  --output path\to\nonvisual_audit.json

python -m paper2slides.benchmark universal-pptx-intake `
  --pptx path\to\slides.pptx `
  --output-dir benchmark_runs\local_intake\deck_a `
  --write-schemas
```

universal intake 会写出 `deck_ir.json`、`universal_scorecard.v0.json` 和可选 schema。因为 DeckIR 不绑定某个生成器，同一套 evaluator 可以评：

- paper2ppt 生成的 deck；
- PPT-master-inspired seed-template deck；
- 人工编辑的 PowerPoint；
- frozen golden baseline；
- 其他 PPT 生成器产出的原生可编辑 PPTX。

parse-once 多路线冒烟测试可以使用 six-way runner：

```powershell
python -m paper2slides.benchmark sixway `
  --paper test_papers\OpenAI_GPT-5_System_Card.pdf `
  --run-dir benchmark_runs\openai_gpt5_system_card_sixway_20260701_smoke `
  --slides 24
```

当前 benchmark 方向：

- 保留 parse-once checkpoint、native PPTX、nonvisual audit、six-way benchmark、repair log 和 frozen references。
- `academic`、`golden_baseline1`、`golden_baseline2` 是评测参考，不作为新 autonomous style proposal 的模板输入。
- 初稿风格 pipeline 吸收 PPT-master 的 strategist / spec-lock / seed-template / quality-gate 思想。
- 先用 DeckIR 和 universal scorecard 比较路线，再进入 human visual preference。
- 把有效的人类反馈转成可复用、可限定 scope 的 benchmark rule。

论文清单位于 `benchmarks/papers.json`；当前 `ai20` 由本地论文和新增的大模型、推理、agent/评估报告组成。

详细计划和阶段报告见：

```text
docs/benchmark_plan.zh-CN.md
docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
docs/from_scratch_benchmark_final_synthesis.zh-CN.md
docs/next_window_handoff.zh-CN.md
docs/ppt_master_universal_benchmark_upgrade_plan.zh-CN.md
docs/ppt_master_seed_pipeline_integration_plan.zh-CN.md
docs/universal_ppt_benchmark_v0_report.zh-CN.md
docs/three_seed_styles_openai_gpt5_report.zh-CN.md
docs/golden_baseline2_cover_signal_patch.zh-CN.md
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
