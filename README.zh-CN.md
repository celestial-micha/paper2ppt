# paper2ppt

[English](README.md) | [中文](README.zh-CN.md)

paper2ppt 可以把学术 PDF 论文转换成可编辑的 PowerPoint、配套演讲稿，以及可选的详细版 Beamer/TeX 旁路汇报。

当前项目目标是服务真实论文汇报：复用论文原始图片和表格，只使用文本大模型做规划和写作，渲染原生可编辑 `.pptx`，并围绕输出做轻量 QA 和自动修复。

本项目继承自 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides)。我们保留了上游项目的 PDF 解析、素材抽取、checkpoint 和论文处理思路，但把最后的图片生成式幻灯片路径替换成了原生 PPTX 工作流。

![paper2ppt 效果预览](paper2ppt_preview.jpg)

## 当前状态

项目现在支持：

- 可编辑 PowerPoint 输出：`slides.pptx`。
- 配套讲稿：`speaker_script.md`。
- 可选的轻量 Beamer/TeX 旁路，由本仓库自己的代码生成。它是参考/备份路径，不是主交付物。
- 基于 LangChain/LangGraph 的文本大模型工作流。
- 默认文本模型配置使用 `gpt-5-mini`。
- 使用 `--slides` 精确指定目标页数。
- 带章节意识的 PPT：标题页、目录页、章节分隔页、key message、编号要点、紧凑指标卡、论文原图和表格。
- 轻量 PPTX 排版 QA 和自动修复。
- 使用 `PPTX_FORCE_DETERMINISTIC=1` 从已有 checkpoint 低成本重跑 deterministic fallback。

最近一轮视觉迭代重点是让生成结果更像正式 PPT：

- 增加正式标题页，包含标题、作者、上下文/日期和右下角信息块。
- 增加目录页，并把右侧横线改成有意义的章节进度线。
- 增加章节分隔页。
- 普通页改成“标题栏 + Key message + 编号要点”。
- 删除编号要点旁边无意义的小横杠。
- 恢复有价值的装饰横线和信息块，但让它们承载真实信息。
- 改进 bullet 渲染，使每条尽量呈现“短 claim + 完整 detail 句子”，而不是被截断的省略句。

## 推荐测试 PDF

当前主要本地测试论文是：

```text
test_papers/DeepSeek_V4.pdf
```

最近开发时检查的输出位于：

```text
outputs/DeepSeek_V4/paper/fast/slides_academic_medium_24slides/
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
    -> slide spec 校验
    -> 原生 PPTX 渲染
    -> layout QA 和修复循环
    -> 生成 speaker script
    -> 可选生成详细版 Beamer/TeX 旁路
```

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

当前本地工作区里，`paper2slides/.env` 已经存在，不需要再复制，也不要上传。

典型配置：

```env
RAG_LLM_API_KEY=your_api_key_here
RAG_LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=gpt-5-mini
```

重要成本规则：

```env
LLM_MODEL=gpt-5-mini
PPTX_VISION_MODEL=gpt-5-mini
```

如果不需要调用模型，只想从已有 checkpoint 重渲染：

```env
PPTX_FORCE_DETERMINISTIC=1
```

可选的论文原图理解：

```env
PPTX_ENABLE_FIGURE_ANALYSIS=1
PPTX_VISION_MODEL=gpt-5-mini
PPTX_MAX_FIGURE_ANALYSIS=5
```

这一步只分析论文原图，不生成新图片。

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
- `layout_qa.json`：轻量排版 QA 结果。
- `checkpoint_slide_spec.json`：最终结构化 slide spec。
- `checkpoint_slide_spec_llm_raw.txt`：如果调用了 curator LLM，会保存原始输出。

## 重要实现文件

```text
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/pptx_qa.py
paper2slides/generator/slide_schema.py
paper2slides/generator/spec_builder.py
paper2slides/generator/detailed_tex.py
paper2slides/core/stages/generate_stage.py
paper2slides/core/paths.py
```

开发过程中，用户还在本地下载了另一个项目作为参考：

```text
Paper2PPT-main/
```

这个文件夹只是用来研究 `gejifeng/Paper2PPT` 的思路，尤其是章节化汇报和 TeX/Beamer 风格。它不是当前 paper2ppt 主流程的一部分，代码不会 import 它，运行时也不需要它。GitHub 仓库应该保留基于 `paper2slides/` 的魔改实现，不应该把 `Paper2PPT-main/` 作为内置项目提交进去。

## 测试

```powershell
python -m unittest test_phase1_pptx.py
```

不写 `__pycache__` 的快速语法检查：

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
python -c "import ast, pathlib; ast.parse(pathlib.Path('paper2slides/generator/pptx_renderer.py').read_text(encoding='utf-8')); print('AST OK')"
```

## 下一阶段方向：ReAct / Plan-and-Solve

当前 PPT 视觉已经明显变好，但内容质量还需要更强的闭环。下一阶段计划从一次性生成 slide spec，升级为评估驱动的 agent 循环：

```text
Plan-and-Solve
 -> 生成结构化 slide plan
 -> 要求每条 point 包含 claim、detail、evidence
 -> 渲染 PPTX
 -> 用 ReAct 风格 QA 批判检查
 -> 只修复失败页面
 -> 重新渲染并再次检查
```

目标检查项：

- 不出现空视觉组件。
- 不出现没有意义的装饰元素。
- 交付文本不出现被截断的省略句。
- 编号要点尽量有短 claim 和完整 detail 说明句。
- 指标卡必须有有意义的 label 和 value。
- 标题页、目录页、章节页的视觉元素必须承载真实信息。
- 所有模型调用都使用 `gpt-5-mini`。

新开对话时建议这样说：

```text
这是一个从 HKUDS/Paper2Slides 魔改来的 paper2ppt 项目。主线代码在 paper2slides/ 里：它会解析论文 PDF，只用文本大模型规划原生可编辑 PPTX，并生成配套演讲稿。当前主交付物是 slides.pptx 和 speaker_script.md。Paper2PPT-main 只是曾经用于参考的本地项目，不应该当作运行路径的一部分。

请先阅读 README.md、README.zh-CN.md 和 DEVELOPMENT_HISTORY.zh-CN.md。

然后从当前 paper2ppt 项目状态继续。现在优先实现 ReAct / Plan-and-Solve 闭环来改进 PPT 生成：
1. 生成或修复 slide spec，让每个 numbered point 都有 claim、detail、evidence 字段。
2. 增加 evaluator，检查空组件、无意义装饰、截断省略句、缺少 claim/detail、metric label/value 质量和 layout QA。
3. 增加 repair loop，只修改失败页面并重新渲染。
4. 所有模型调用保持使用 gpt-5-mini。
5. 用 DeepSeek_V4.pdf 作为主要测试 PDF，尽量从 --from-stage generate 重跑。

注意：上一轮用户已经非常满意当前 PPT 的视觉风格，不要暴力删掉封面 summary tiles、目录进度线或章节分隔页横线；要在保留这些版式美感的基础上做语义化和 QA 闭环。
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

paper2ppt 继承自 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides)。如果继续分发或扩展本项目，请保留上游来源说明和许可证要求。
