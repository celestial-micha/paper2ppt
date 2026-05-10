# paper2ppt 开发历史

这份文档记录 `paper2ppt` 如何在 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides) 的基础上改造成“纯文本大模型生成可编辑 PPTX + 演讲稿”的系统，也记录了从 [gejifeng/Paper2PPT](https://github.com/gejifeng/Paper2PPT) 借鉴到的章节化和 TeX/Beamer 思路。本文面向项目维护和公开浏览，记录稳定的技术演进、当前能力和验证方式。

## 1. 项目起点

本项目主要继承自 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides)，同时参考了 [gejifeng/Paper2PPT](https://github.com/gejifeng/Paper2PPT)。

Paper2Slides 提供了很有价值的基础能力：

- 解析论文 PDF。
- 提取正文、表格和图片。
- 使用 RAG / LLM 生成内容规划。
- 通过图片生成模型生成海报或幻灯片式图片。

最初的问题是：虽然可以从 PDF 一键得到“像 PPT 的结果”，但最终产物更接近图片或 PDF，不是真正可编辑的 PowerPoint。对于论文汇报，这会带来几个问题：

- PPT 里的文字和图形不方便编辑。
- 图片生成模型成本较高。
- 文生图模型容易改写或失真论文原图。
- 结果不稳定，难以做精细排版控制。

因此本项目的核心改造目标被确定为：

```text
不使用文生图模型，只使用文本大模型和论文原始素材，生成真正可编辑的 PPTX，并同步生成演讲稿。
```

Paper2PPT 对本项目的影响主要在产品设计层面：

- 让论文汇报有更清晰的章节结构。
- 对长论文生成更详略得当的补充材料。
- 用 TeX / Beamer 作为详细稿或参考稿的生成思路。

本仓库没有内置 Paper2PPT，也不在运行时依赖 Paper2PPT。

## 2. 第一阶段：跑通原项目并建立检查点

第一阶段先保证原始项目可以在本地环境跑通。

主要工作：

- 梳理 conda 环境和依赖。
- 确认 `paper2slides` 环境可以运行项目。
- 使用本地 API 配置完成论文解析、摘要、规划和生成流程。
- 记录各阶段 checkpoint 的位置和复用方式。

阶段成果：

- 项目可以从 PDF 进入完整流水线。
- 明确了各阶段 checkpoint 的位置。
- 后续可以用 `--from-stage generate` 快速重跑生成阶段，不必每次重新解析 PDF。

## 3. 第二阶段：改为原生 PPTX 生成

这一阶段是项目最核心的功能改造。

原路径：

```text
PDF -> 内容规划 -> 调用图片模型生成每页图片 -> 拼成 PDF / 类 PPT
```

新路径：

```text
PDF -> 内容规划 -> 文本大模型生成 slide spec -> python-pptx 渲染原生 PPTX
```

主要新增或重点改造的模块：

```text
paper2slides/generator/slide_schema.py
paper2slides/generator/spec_builder.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/text_pptx_workflow.py
```

关键设计：

- 用结构化 `PresentationSpec` / `SlideSpec` 描述每页 PPT。
- 文字、图片、表格和指标都作为可编辑对象进入 PPTX。
- 图片只使用论文中已经解析出来的原始图片。
- 不调用文生图模型。

阶段成果：

- 成功输出 `slides.pptx`。
- PPT 内容从图片式结果变成可编辑 PowerPoint。
- 项目具备“低成本生成论文汇报稿”的核心价值。

## 4. 第三阶段：接入 LangChain 和 LangGraph

为了让生成过程更像一个可维护的智能工作流，而不是简单函数串联，项目引入了 LangChain 和 LangGraph。

LangChain 用于：

- 统一调用文本大模型。
- 支持兼容 OpenAI 接口的中转服务。
- 记录模型和调用方式。

LangGraph 用于：

- 把 PPT 生成拆成多个清晰节点。
- 承载 QA、修复、讲稿等节点。
- 在依赖不可用时保留非 LangGraph 的兜底路径。

当前核心工作流大致为：

```text
prepare_packet
 -> analyze_figures
 -> curate_spec
 -> validate
 -> render
 -> repair_spec
 -> speaker_script
```

阶段成果：

- PPT 生成过程具备清晰节点边界。
- 代码更容易扩展和调试。
- QA 自动返修、spec evaluator 和局部修复循环可以自然接入。

## 5. 第四阶段：全部模型调用统一为 gpt-5-mini

项目约定：只要调用模型，统一使用 `gpt-5-mini`，避免昂贵的 `gpt-4o`。

当前约定：

- 所有文本模型调用默认使用 `gpt-5-mini`。
- 不再使用 `gpt-4o` 做 PPT 生成、修复、讲稿或详细稿生成。
- figure analysis、deck curation、repair 相关模型调用也统一走 `gpt-5-mini`。

这条约定非常重要，后续开发不要因为示例代码、默认配置或第三方项目习惯而回退到更贵模型。

## 6. 第五阶段：借鉴 Paper2PPT 的章节化和 TeX 思路

参考项目 [gejifeng/Paper2PPT](https://github.com/gejifeng/Paper2PPT) 的优点是：

- 能生成更详略得当的论文讲解材料。
- 使用 TeX / Beamer 路径生成较详细的 slide PDF。
- 章节结构感更强。

这个参考项目主要用于启发本项目的章节组织和详细稿思路，不是当前项目的主线依赖。本项目没有替换原来的 PPTX 生成路径，也不会 import 或运行 Paper2PPT 的代码。

当前项目的主交付物是：

```text
slides.pptx
speaker_script.md
```

设计目标：

- `slides.pptx`：可编辑、适合正式汇报和后期修改。
- `speaker_script.md`：配套演讲稿。
- `detailed_slides.tex` / `detailed_slides.pdf`：如果启用旁路且本机有 `pdflatex`，可以由本项目自己的轻量 sidecar 代码生成，作为参考/备份材料；它不是主交付物，也不依赖 Paper2PPT。

因此，上传 GitHub 时不建议把外部参考项目作为 vendored folder 放进仓库。如果本地仍想留作参考，可以让 `.gitignore` 忽略 `Paper2PPT-main/`，并用 `git rm -r --cached Paper2PPT-main` 取消 Git 跟踪。

## 7. 第六阶段：DeepSeek_V4.pdf 与动态页数

当前推荐测试 PDF 已改为：

```text
test_papers\DeepSeek_V4.pdf
```

长论文不适合只生成 8 页左右，因此项目增加了更灵活的页数控制。

当前常用命令：

```powershell
python -m paper2slides --input test_papers\DeepSeek_V4.pdf --output slides --style academic --length medium --slides 24 --fast
```

说明：

- `--slides 24` 可以指定目标页数。
- `--length medium` 控制内容密度。
- `--fast` 复用快速路径。
- 如果已经有解析结果，优先使用 `--from-stage generate` 重跑生成阶段。

确定性重跑命令：

```powershell
$env:PPTX_FORCE_DETERMINISTIC="1"
python -m paper2slides --input test_papers\DeepSeek_V4.pdf --output slides --style academic --length medium --slides 24 --fast --from-stage generate
```

## 8. 第七阶段：章节结构和视觉编排

早期 PPT 的问题是内容基本正确，但像“文字搬运”，缺少真正 PPT 的章节感和组件化排版。

后来逐步增加了：

- 标题页。
- 目录页。
- 章节分隔页。
- Motivation / Method / Results / Conclusion 等章节划分。
- 标题、重点信息、编号要点、指标卡片、图片说明等不同组件。
- 更合适的字体大小和留白。

这一阶段的目标不是单纯把文字塞进 slide，而是让 PPT 像真正可以交付的汇报稿。

## 9. 视觉编排修复

这一阶段的重要修复集中在 `pptx_renderer.py` 和 `text_pptx_workflow.py`，目标是保留已经形成的正式汇报感，同时减少无意义装饰和截断文本。

修复背景：

- 保留封面、目录、章节页的版式美感。
- 只删除真正无意义或干扰理解的小横杠。
- numbered points 需要有“重点句 + 解释句”，并且句子尽量完整，不要都是省略号。

当前已经修好的点：

- 封面右下角三个 summary tiles 被恢复，并填入真实内容，例如 `Sections`、`Content slides`、`Source figures`。
- 目录页右侧的横线被保留，但改成有意义的进度线 / 视觉引导线，不再像空横杠。
- 章节分隔页的横线被恢复，保持简洁好看的过渡页风格。
- numbered point 旁边无意义的小连接横杠被移除。
- numbered point 尽量拆成“claim + detail”的两层结构。
- 对长句和省略号做了改进，减少因为布局截断导致的不可交付感。
- metric / key number 卡片的填充逻辑更谨慎，避免大卡片里只有很小、很空的文字。

参考输出示例：

```text
outputs\DeepSeek_V4\paper\fast\slides_academic_medium_24slides\20260510_174945
```

其中包含：

```text
slides.pptx
speaker_script.md
layout_qa.json
previews
```

部分运行还可能包含 `detailed_slides.tex` 和 `detailed_slides.pdf`，但它们只是可选参考产物。

该次 `layout_qa.json` 显示：

```text
passed: true
pages: 29
```

仍有一些非致命 warning，例如长标题或少量文本溢出提示，但整体已经通过当前 QA。

## 10. 第八阶段：Spec Evaluator 与局部修复闭环

这一阶段把原先偏版式的 QA 升级为“slide spec 语义检查 + PPTX layout QA”的组合评估，并在 LangGraph 工作流中形成有上限的局部修复循环。

核心改动：

- `TextBlock` 增加 `claim`、`detail`、`evidence` 字段，用于结构化 numbered point。
- LLM deck curation prompt 要求输出 `numbered_points`，每条包含 claim、detail、evidence。
- 对旧格式 bullet / text block 保持兼容，在 validate 阶段自动补齐结构化字段。
- `pptx_renderer.py` 渲染 numbered point 时优先使用结构化 claim/detail。
- `pptx_qa.py` 增加 spec evaluator，检查：
  - 空 slide / 空组件。
  - 无意义占位和装饰性 placeholder。
  - 截断省略句。
  - numbered point 缺少 claim、detail 或 evidence。
  - metric label / value 质量。
  - PPTX layout QA 结果。
- repair loop 只在 evaluator 判定 `passed: false` 时触发，并只修改失败页面的 slide spec。
- repair loop 有最大迭代次数，默认由 `PPTX_QA_MAX_REPAIR_ATTEMPTS` 控制。
- 所有模型调用继续固定为 `gpt-5-mini`。

阶段成果：

- `checkpoint_slide_spec.json` 中的 numbered point 具备稳定的 `claim`、`detail`、`evidence` 结构。
- `layout_qa.json` 从单纯排版结果升级为综合 QA 报告，包含 `passed`、`warnings`、`failed_slides`、`layout` 和 `checks`。
- DeepSeek_V4 生成路径可以从 `--from-stage generate` 重跑，并通过当前综合 QA。

## 11. 当前关键文件

当前主线实现文件：

```text
README.md
README.zh-CN.md
DEVELOPMENT_HISTORY.zh-CN.md
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/pptx_qa.py
paper2slides/generator/slide_schema.py
paper2slides/generator/spec_builder.py
```

其中：

- `text_pptx_workflow.py` 负责文本 PPTX 工作流、模型调用、spec 生成、QA / repair loop、讲稿和详细稿。
- `pptx_renderer.py` 负责把结构化 spec 渲染成 PPTX，并包含当前大部分视觉编排逻辑。
- `pptx_qa.py` 负责 spec evaluator 和 PPTX layout QA。
- `slide_schema.py` 定义结构化 slide spec，包括 numbered point 的 `claim`、`detail`、`evidence` 字段。
- `spec_builder.py` 提供 spec 构造和兜底逻辑。

## 12. 当前验证方式

当前已通过的单元测试：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
C:\Users\81001\.conda\envs\paper2slides\python.exe -m unittest test_phase1_pptx.py
```

结果：

```text
Ran 8 tests
OK
```

当前 DeepSeek_V4 验证命令：

```powershell
$env:PPTX_FORCE_DETERMINISTIC='1'
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides --input test_papers\DeepSeek_V4.pdf --output slides --style academic --length medium --slides 24 --fast --from-stage generate
```

最近一次验证输出：

```text
outputs\DeepSeek_V4\paper\fast\slides_academic_medium_24slides\20260510_195014
```

验证结果：

```text
layout_qa.json: passed true
checkpoint_slide_spec.json: 24 slides; all numbered points include claim/detail/evidence
model metadata: gpt-5-mini
```

推荐人工验证方式：

1. 用 DeepSeek_V4.pdf 重跑生成。
2. 打开 `slides.pptx` 检查封面、目录、章节页和 numbered point 页面。
3. 查看 `layout_qa.json` 是否 `passed: true`。
4. 重点检查是否存在空卡片、无意义横杠、截断省略句、缺少 claim/detail/evidence 的编号点。

## 13. Git 注意事项

本地 `paper2slides\.env` 已经存在，用于保存 API key。不要提交 `.env`。

可以提交：

```text
.gitignore
README.md
README.zh-CN.md
DEVELOPMENT_HISTORY.zh-CN.md
paper2ppt_preview.jpg
paper2slides/generator/slide_schema.py
paper2slides/generator/pptx_qa.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/text_pptx_workflow.py
test_phase1_pptx.py
```

通常不建议提交：

```text
paper2slides\.env
outputs\
__pycache__\
Paper2PPT-main\
```

如果需要把生成好的 PPT 单独备份，可以手动复制或 release，不建议默认纳入源码提交。

如果 `Paper2PPT-main/` 已经被 Git 跟踪，但希望本地保留它、GitHub 不再上传它，推荐使用：

```powershell
git rm -r --cached Paper2PPT-main
```

这只会从 Git 索引里移除它，不会删除本地文件。配合 `.gitignore` 里的 `Paper2PPT-main/`，后续它不会再被误提交。
