# PaperCue

[English](#english) | [中文](#中文)

PaperCue turns academic PDFs into editable PowerPoint decks and matching speaker scripts. It is built for users who want a practical "PDF in, PPTX out" workflow without paying for image-generation models.

PaperCue is derived from [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides). This fork keeps the document parsing, summarization, RAG-style extraction, and checkpoint pipeline ideas, then refactors the final generation path into a text-LLM-driven, native PPTX workflow.

## English

### What It Does

- Parses a paper PDF and extracts text, tables, and original figures.
- Uses text LLMs through LangChain/LangGraph to curate a presentation plan.
- Generates an editable `.pptx` with native PowerPoint text, tables, shapes, and the paper's own figures.
- Generates `speaker_script.md` alongside the deck.
- Runs a lightweight PPTX layout QA pass and can repair risky slide specs before final output.
- Does not call text-to-image or image-generation models for slide creation.

### Output

Each run creates an output folder containing files such as:

```text
slides.pptx
speaker_script.md
layout_qa.json
checkpoint_slide_spec.json
checkpoint_slide_spec_llm_raw.txt
```

### Installation

```powershell
conda create -n papercue python=3.12
conda activate papercue
pip install -r requirements.txt
```

If you already use the local environment from development:

```powershell
conda activate paper2slides
pip install -r requirements.txt
```

### Configuration

Create `paper2slides/.env` from the example file:

```powershell
copy paper2slides\.env.example paper2slides\.env
```

Set your text-model API information:

```env
RAG_LLM_API_KEY=your_api_key_here
RAG_LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=gpt-4o-mini
```

Optional figure understanding can use a vision-capable text model, but it still only analyzes original paper figures. It does not generate new images.

```env
PPTX_ENABLE_FIGURE_ANALYSIS=1
PPTX_VISION_MODEL=gpt-4o-mini
PPTX_MAX_FIGURE_ANALYSIS=5
```

### Usage

```powershell
python -m paper2slides --input test_papers\AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast
```

Useful options:

```text
--input       PDF path
--output      slides only
--style       academic or custom text
--length      short, medium, or long
--fast        parse directly without full RAG indexing
--from-stage  rag, summary, plan, or generate
--list        list previous outputs
```

To rerun only the PPTX curation/rendering step from existing checkpoints:

```powershell
python -m paper2slides --input test_papers\AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast --from-stage generate
```

### Architecture

```text
PDF
 -> parsing and extraction
 -> summary checkpoint
 -> content plan checkpoint
 -> LangGraph PPTX workflow
    -> source packet
    -> optional source-figure analysis
    -> text LLM deck curation
    -> slide spec validation
    -> native PPTX rendering
    -> layout QA and repair loop
    -> speaker script
```

Important modules:

```text
paper2slides/core/stages/
paper2slides/generator/content_planner.py
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/pptx_qa.py
paper2slides/generator/slide_schema.py
```

### Safety Before Publishing

Do not publish local secrets or generated private outputs. The repository ignores common sensitive files, including:

```text
paper2slides/.env
shunyu_relay_demo.py
test_api_config.py
outputs/
test_papers/*.pdf
```

Before pushing to GitHub, run:

```powershell
git status --short
git diff --check
```

### Tests

```powershell
python -m unittest test_phase1_pptx.py
```

### License and Attribution

This project inherits from [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides). Keep the original license terms and attribution when redistributing this fork.

## 中文

### 这个项目做什么

PaperCue 可以把论文 PDF 一键生成可编辑的 PowerPoint，并同时生成对应的演讲稿或讲解稿。它的目标不是把论文原文搬进 PPT，而是用文本大模型做内容策展、重点提炼和版式规划，然后用论文中已经提取到的原图和表格生成展示稿。

本项目继承自 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides)。这个 fork 保留了原项目的解析、摘要、RAG/检查点流水线思路，并把最后生成部分改成了“文本模型 + 原生 PPTX”的工作流。

### 核心特点

- 从 PDF 中提取正文、表格和论文原图。
- 使用 LangChain/LangGraph 调用文本大模型进行 PPT 内容策展。
- 输出真正可编辑的 `.pptx`，不是图片拼成的 PDF。
- PPT 中的图片来自论文原始提取结果，不调用文生图模型。
- 同步生成 `speaker_script.md`，便于汇报或讲解。
- 自动生成 `layout_qa.json`，并在发现排版风险时尝试自动压缩和返修。

### 安装

```powershell
conda create -n papercue python=3.12
conda activate papercue
pip install -r requirements.txt
```

如果你沿用当前开发环境：

```powershell
conda activate paper2slides
pip install -r requirements.txt
```

### 配置 API

复制示例配置：

```powershell
copy paper2slides\.env.example paper2slides\.env
```

填写文本模型 API：

```env
RAG_LLM_API_KEY=your_api_key_here
RAG_LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=gpt-4o-mini
```

可选：如果希望模型理解论文原图，可以开启视觉模型分析。但这一步只是读论文原图，不生成新图片。

```env
PPTX_ENABLE_FIGURE_ANALYSIS=1
PPTX_VISION_MODEL=gpt-4o-mini
PPTX_MAX_FIGURE_ANALYSIS=5
```

### 运行

```powershell
python -m paper2slides --input test_papers\AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast
```

如果已经有前面阶段的 checkpoint，只想重新调用大模型生成 PPTX：

```powershell
python -m paper2slides --input test_papers\AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast --from-stage generate
```

### 输出文件

```text
slides.pptx                 可编辑 PPT
speaker_script.md           演讲稿/讲解稿
layout_qa.json              排版 QA 报告
checkpoint_slide_spec.json  最终 slide spec
checkpoint_slide_spec_llm_raw.txt  大模型原始策展输出
```

### 上传 GitHub 前注意

不要上传本地 API key、私有论文或生成结果。以下文件已经在 `.gitignore` 中忽略：

```text
paper2slides/.env
shunyu_relay_demo.py
test_api_config.py
outputs/
test_papers/*.pdf
```

提交前建议检查：

```powershell
git status --short
git diff --check
```

### 测试

```powershell
python -m unittest test_phase1_pptx.py
```

### 项目来源

PaperCue 继承自 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides)。如果你公开发布这个 fork，请保留原项目的 license 和 attribution。
