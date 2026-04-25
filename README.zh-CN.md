# paper2ppt

[English](README.md) | [中文](README.zh-CN.md)

paper2ppt 可以把学术论文 PDF 转换成可编辑的 PowerPoint，并同步生成一份演讲稿。它的目标是一个实用流程：输入 PDF，使用文本大模型策展内容和结构，复用论文原始图片，最后得到原生 `.pptx` 和可直接修改的讲解稿。

paper2ppt 继承自 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides)。本项目保留了上游项目的论文解析、内容提取、检查点流水线和部分 RAG 思路，同时把最后的图片生成式幻灯片路径改造成了“文本大模型 + 原生 PPTX”的生成流程。

## 功能特点

- 从 PDF 论文生成可编辑 PowerPoint。
- 同步生成 `speaker_script.md`，方便准备汇报讲稿。
- 复用论文中提取到的原始图片和表格。
- 使用 LangChain/LangGraph 进行文本大模型策展和工作流编排。
- 生成 PPT 时不调用文生图模型。
- 生成后自动进行轻量 PPTX 排版 QA，并在发现风险时自动返修。
- 保存中间检查点，后续可以从指定阶段继续运行。

## 工作流程

```text
PDF
 -> 论文解析和素材提取
 -> 摘要检查点
 -> 内容规划检查点
 -> LangGraph PPTX 工作流
    -> 构建 source packet
    -> 可选的论文原图理解
    -> 文本大模型策展 slide spec
    -> slide spec 校验
    -> 原生 PPTX 渲染
    -> 排版 QA 和自动返修
    -> 演讲稿生成
```

生成的 PPT 不是网页截图，也不是图片拼接。它使用 PowerPoint 原生文本框、形状、表格和论文原始图片，因此可以继续在 PowerPoint 中编辑。

## 环境要求

- Windows、macOS 或 Linux
- Python 3.10 或以上，推荐 Python 3.12
- Conda 或其他 Python 环境管理工具
- 一个兼容 OpenAI chat-completions 接口的文本模型 API

本项目开发测试时使用的 conda 环境名是 `paper2slides`，但环境名可以自行设置。

## 安装

克隆仓库并进入项目目录后，创建环境：

```powershell
conda create -n paper2ppt python=3.12
conda activate paper2ppt
pip install -r requirements.txt
```

如果你已经有可用的 Python 环境，可以直接在当前环境安装依赖：

```powershell
pip install -r requirements.txt
```

## 配置 API

paper2ppt 会从 `paper2slides/.env` 读取 API 配置。

先复制公开模板：

```powershell
copy paper2slides\.env.example paper2slides\.env
```

然后编辑 `paper2slides/.env`：

```env
RAG_LLM_API_KEY=your_api_key_here
RAG_LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=gpt-5-mini
```

如果希望模型理解论文原图，可以配置一个支持视觉输入的文本模型。这个步骤只分析论文原始图片，不生成新图片。

```env
PPTX_ENABLE_FIGURE_ANALYSIS=1
PPTX_VISION_MODEL=gpt-5-mini
PPTX_MAX_FIGURE_ANALYSIS=5
```

仓库中提交的是 `paper2slides/.env.example`。真正包含 API key 的 `paper2slides/.env` 应该只保留在本地。

## 第一次运行

使用任意本地 PDF 路径：

```powershell
python -m paper2slides --input path\to\paper.pdf --output slides --style academic --length medium --fast
```

如果你本地有测试论文，也可以这样运行：

```powershell
python -m paper2slides --input test_papers\AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast
```

常用参数：

```text
--input       PDF 文件路径
--output      slides
--style       academic 或自定义风格描述
--length      short、medium 或 long
--fast        使用直接解析/查询流程，不跑完整索引
--from-stage  rag、summary、plan 或 generate
--list        查看历史输出
--debug       输出更详细日志
```

## 输出文件

成功运行后，paper2ppt 会在 `outputs/` 下创建一个带时间戳的输出目录。

常见输出：

```text
slides.pptx
speaker_script.md
layout_qa.json
checkpoint_slide_spec.json
checkpoint_slide_spec_llm_raw.txt
```

文件含义：

- `slides.pptx`：可编辑 PowerPoint。
- `speaker_script.md`：逐页讲稿草稿。
- `layout_qa.json`：轻量排版 QA 结果。
- `checkpoint_slide_spec.json`：最终结构化 slide spec。
- `checkpoint_slide_spec_llm_raw.txt`：大模型策展阶段的原始输出。

## 从后续阶段继续运行

如果 PDF 已经解析过，只想重新生成 PPTX 和讲稿，可以运行：

```powershell
python -m paper2slides --input path\to\paper.pdf --output slides --style academic --length medium --fast --from-stage generate
```

这会复用前面的解析、摘要和规划检查点，只重新运行 LangGraph PPTX 工作流。

## 项目结构

```text
paper2slides/
  core/                 流水线阶段、路径和检查点逻辑
  generator/            内容规划、LangGraph 工作流、PPTX 渲染器、QA
  prompts/              论文规划和抽取提示词
  rag/                  继承自上游的 RAG 客户端和查询辅助
  raganything/          继承自上游的文档解析层
  summary/              论文/通用摘要和素材模型
  utils/                日志和文件工具

README.md
README.zh-CN.md
DEVELOPMENT_HISTORY.zh-CN.md
requirements.txt
test_phase1_pptx.py
```

重要实现文件：

```text
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/pptx_qa.py
paper2slides/generator/slide_schema.py
paper2slides/generator/content_planner.py
```

## 测试

```powershell
python -m unittest test_phase1_pptx.py
```

也可以查看 CLI 是否正常：

```powershell
python -m paper2slides --help
```

## 常见问题

如果 API 调用失败：

- 检查 `paper2slides/.env`。
- 检查 `RAG_LLM_BASE_URL`。
- 检查所选模型是否支持足够长的上下文。

如果 PPT 太空或太密：

- 尝试不同的 `--length`。
- 使用 `--from-stage generate` 重新生成。
- 在 `.env` 中切换更适合的文本模型。

如果某页看起来拥挤：

- 查看 `layout_qa.json`。
- 在 `.env` 中适当提高 `PPTX_QA_MAX_REPAIR_ATTEMPTS`。

## 项目来源

paper2ppt 继承自 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides)。如果继续分发或扩展本项目，请保留上游项目的来源说明和许可证要求。
