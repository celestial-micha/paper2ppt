# paper2ppt 开发历史与接力说明

这份文档用于帮助新的对话快速理解当前项目状态。它记录了 `paper2ppt` 如何在 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides) 的基础上改造成“纯文本大模型生成可编辑 PPTX + 演讲稿”的系统，也记录了从 [gejifeng/Paper2PPT](https://github.com/gejifeng/Paper2PPT) 借鉴到的章节化和 TeX/Beamer 思路。下一步如果要按 ReAct Agent / Plan-and-Solve 继续改，可以从本文末尾的接力说明开始。

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
- 支持后续增加 QA、修复、讲稿等节点。
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
- 后续 QA 自动返修、ReAct Agent、Plan-and-Solve 都能自然接入。

## 5. 第四阶段：全部模型调用统一为 gpt-5-mini

用户明确要求：只要调用模型，通通只使用 `gpt-5-mini`，避免昂贵的 `gpt-4o`。

当前约定：

- 所有文本模型调用默认使用 `gpt-5-mini`。
- 不再使用 `gpt-4o` 做 PPT 生成、修复、讲稿或详细稿生成。
- 如果将来新增 evaluator / repair agent，也必须继续使用 `gpt-5-mini`。

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

用户发现论文较长时不应只生成 8 页左右，因此项目增加了更灵活的页数控制。

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

## 9. 最近一次用户非常满意的视觉修复

最近一次重要修复集中在 `pptx_renderer.py` 和 `text_pptx_workflow.py`，用户确认效果“超级超级满意”。

修复背景：

- 用户不希望暴力删除好看的装饰组件。
- 希望保留封面、目录、章节页的版式美感。
- 只删除真正无意义或干扰理解的小横杠。
- 希望 numbered points 有“重点句 + 解释句”，并且句子尽量完整，不要都是省略号。

当前已经修好的点：

- 封面右下角三个 summary tiles 被恢复，并填入真实内容，例如 `Sections`、`Content slides`、`Source figures`。
- 目录页右侧的横线被保留，但改成有意义的进度线 / 视觉引导线，不再像空横杠。
- 章节分隔页的横线被恢复，保持简洁好看的过渡页风格。
- numbered point 旁边无意义的小连接横杠被移除。
- numbered point 尽量拆成“claim + detail”的两层结构。
- 对长句和省略号做了改进，减少因为布局截断导致的不可交付感。
- metric / key number 卡片的填充逻辑更谨慎，避免大卡片里只有很小、很空的文字。

当前满意输出示例：

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

## 10. 当前关键文件

建议下一轮对话优先阅读：

```text
README.md
README.zh-CN.md
DEVELOPMENT_HISTORY.zh-CN.md
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/slide_schema.py
paper2slides/generator/spec_builder.py
```

其中：

- `text_pptx_workflow.py` 负责文本 PPTX 工作流、模型调用、spec 生成、讲稿和详细稿。
- `pptx_renderer.py` 负责把结构化 spec 渲染成 PPTX，并包含当前大部分视觉编排逻辑。
- `slide_schema.py` 定义结构化 slide spec。
- `spec_builder.py` 提供 spec 构造和兜底逻辑。

## 11. 当前验证方式

之前已通过的单元测试：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
C:\Users\81001\.conda\envs\paper2slides\python.exe -m unittest test_phase1_pptx.py
```

结果：

```text
Ran 6 tests
OK
```

推荐人工验证方式：

1. 用 DeepSeek_V4.pdf 重跑生成。
2. 打开 `slides.pptx` 检查封面、目录、章节页和 numbered point 页面。
3. 查看 `layout_qa.json` 是否 `passed: true`。
4. 重点检查是否存在空卡片、无意义横杠、截断省略句、缺少 claim/detail 的编号点。

## 12. 当前已知限制

虽然视觉效果已经明显改善，但仍然存在一些结构性问题，适合下一轮用 ReAct Agent / Plan-and-Solve 继续解决：

- 有些 numbered point 只有 detail，没有清晰 claim。
- 有些 claim/detail 是后处理推断出来的，不一定足够稳定。
- 当前 QA 更偏布局检查，还不是完整的语义质量评估。
- 当前 repair 还没有形成真正的“评估 -> 定位问题 -> 局部修复 -> 再评估”闭环。
- 对“句子是否完整”“是否可交付”“是否出现无意义装饰”的判断还比较规则化。

## 13. 下一步建议：ReAct Agent / Plan-and-Solve 闭环

用户希望后续引入 ReAct Agent、Plan-and-Solve 技术，让系统可以评估驱动地闭环迭代。

建议目标架构：

```text
Generate slide spec
 -> Plan QA checks
 -> Evaluate each slide
 -> Identify failed slides and reasons
 -> Repair only failed slide specs
 -> Rerender PPTX
 -> Re-evaluate
 -> Stop when pass or reach max iterations
```

建议新增或改造的能力：

- 在 slide spec 层面明确每个 numbered point 的结构：
  - `claim`
  - `detail`
  - `evidence`
  - `source_section`
- 增加 evaluator，检查：
  - 封面 summary tiles 是否为空。
  - 目录页和章节页的装饰是否有语义。
  - numbered point 是否缺 claim 或 detail。
  - 是否出现孤立横杠、空组件、无意义 label。
  - 是否出现 `...` 形式的截断省略句。
  - metric 卡片是否有 label 和 value，且内容匹配。
  - layout QA 是否通过。
- 增加 repair prompt：
  - 只修复失败页面。
  - 不整体重写全部 PPT。
  - 保留已有好看的布局和用户确认满意的视觉风格。
  - 所有模型调用继续使用 `gpt-5-mini`。
- 增加迭代上限，例如最多 2-3 轮，避免无限循环。

## 14. 新对话推荐提示词

新开对话时，可以直接把下面这段发给 Codex：

```text
这是一个基于 HKUDS/Paper2Slides 改造、并参考 gejifeng/Paper2PPT 设计思路的 paper2ppt 项目。主线代码在 paper2slides/ 里：它会解析论文 PDF，只用文本大模型规划原生可编辑 PPTX，并生成配套演讲稿。当前主交付物是 slides.pptx 和 speaker_script.md。Paper2PPT 只是外部设计参考，不是运行时依赖。

请先阅读 README.md、README.zh-CN.md 和 DEVELOPMENT_HISTORY.zh-CN.md。

然后从当前 paper2ppt 项目状态继续。现在优先实现 ReAct / Plan-and-Solve 闭环来改进 PPT 生成：
1. 生成或修复 slide spec，让每个 numbered point 都有 claim、detail、evidence 字段。
2. 增加 evaluator，检查空组件、无意义装饰、截断省略句、缺少 claim/detail、metric label/value 质量和 layout QA。
3. 增加 repair loop，只修改失败页面并重新渲染。
4. 所有模型调用保持使用 gpt-5-mini。
5. 用 DeepSeek_V4.pdf 作为主要测试 PDF，尽量从 --from-stage generate 重跑。

注意：上一轮用户已经非常满意当前 PPT 的视觉风格，不要暴力删掉封面 summary tiles、目录进度线或章节分隔页横线；要在保留这些版式美感的基础上做语义化和 QA 闭环。
```

## 15. Git 注意事项

本地 `paper2slides\.env` 已经存在，用于保存 API key。不要提交 `.env`。

可以提交：

```text
.gitignore
README.md
README.zh-CN.md
DEVELOPMENT_HISTORY.zh-CN.md
paper2ppt_preview.jpg
paper2slides/generator/pptx_renderer.py
paper2slides/generator/text_pptx_workflow.py
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
