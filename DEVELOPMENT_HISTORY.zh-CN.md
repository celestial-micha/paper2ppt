# paper2ppt 开发历程说明

这份文档用于说明 paper2ppt 从上游 Paper2Slides 项目演进到当前版本的主要改造步骤、技术选择和阶段成果。它适合在项目展示、面试复盘或后续维护时使用。

## 1. 项目起点

paper2ppt 继承自 [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides)。

上游项目的核心能力包括：

- 解析论文 PDF。
- 提取正文、表格和图片。
- 使用 RAG/LLM 生成内容规划。
- 通过图片生成模型生成海报或幻灯片式图片。

最初的问题是：虽然可以从 PDF 一键生成“类似 PPT 的结果”，但最后产物更接近图片或 PDF，不是真正可编辑的 PowerPoint。对论文汇报来说，这会带来几个问题：

- PPT 里的文字和图形不可方便编辑。
- 图片生成模型成本较高。
- 文生图模型容易改写或失真论文原图。
- 生成结果不稳定，难以做细粒度排版控制。

因此，项目改造目标被确定为：

```text
不使用文生图模型，只使用文本大模型和论文原始素材，生成真正可编辑的 PPTX，并同步生成演讲稿。
```

## 2. 第一阶段：跑通原项目和建立检查点

第一阶段先保证原始项目可以在本地环境跑通。

主要工作：

- 梳理 conda 环境和依赖。
- 确认 `paper2slides` 环境可以运行项目。
- 使用本地 API 配置完成论文解析、摘要、规划和生成流程。
- 生成 `PROJECT_REPORT.md` 记录当时的运行过程和关键输出。

阶段成果：

- 项目可以一键从 PDF 进入完整流水线。
- 明确了各阶段 checkpoint 的位置和复用方式。
- 确认后续可以从 `--from-stage generate` 快速重跑生成阶段。

## 3. 第二阶段：从图片生成改为原生 PPTX 生成

这一阶段是项目最核心的功能改造。

原路径：

```text
PDF -> 内容规划 -> 调用图片模型生成每页图片 -> 拼成 PDF/类 PPT
```

新路径：

```text
PDF -> 内容规划 -> 文本大模型策展 slide spec -> python-pptx 渲染原生 PPTX
```

主要新增模块：

```text
paper2slides/generator/slide_schema.py
paper2slides/generator/spec_builder.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/text_pptx_workflow.py
```

关键设计：

- 用结构化 `PresentationSpec` / `SlideSpec` 描述每页 PPT。
- 文字、图片、表格、指标都作为可编辑对象进入 PPTX。
- 图片只使用论文中已经解析出来的原始图片。
- 不调用文生图模型。

阶段成果：

- 成功输出 `slides.pptx`。
- PPT 内容从图片式结果变成可编辑 PowerPoint。
- 项目开始具备“低成本生成论文汇报稿”的核心价值。

## 4. 第三阶段：接入 LangChain 和 LangGraph

为了让生成过程更像一个可维护的智能工作流，而不是简单函数串联，项目引入了 LangChain 和 LangGraph。

LangChain 用于：

- 统一调用文本大模型。
- 支持兼容 OpenAI 接口的中转服务。
- 记录使用的模型和调用方式。

LangGraph 用于：

- 把 PPT 生成拆成多个清晰节点。
- 支持后续增加 QA、修复、讲稿等节点。
- 在依赖不可用时保留非 LangGraph 的兜底路径。

核心工作流：

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
- 后续的 QA 自动返修和讲稿生成能够自然接入。

## 5. 第四阶段：改善内容质量，避免“论文搬运”

早期 PPT 的问题是文字过多，像把论文原文复制到 slide 中。

针对这个问题，做了内容策展和压缩：

- 限制每页 bullet 数量。
- 限制 bullet 字数。
- 强制每页有一个明确 takeaway。
- 鼓励使用论文图片和表格作为页面中心。
- 从正文中抽取关键数字作为 metric。
- 把详细解释放到 speaker script，而不是全部塞进 PPT。

后来又发现过度精简会让页面显得太空，所以进一步调整为“详略得当”：

- 普通页面保留 2-4 条要点。
- 方法和结果页允许更完整的上下文。
- 结论和封面页保持相对简洁。
- 讲稿承担更多解释细节。

阶段成果：

- PPT 从“论文摘抄”变成“展示稿”。
- 文字密度更适合现场汇报。
- 讲稿可以补足 PPT 中省略的解释。

## 6. 第五阶段：重构 PPTX 渲染器

最初的 PPTX 渲染器可用，但视觉效果不够稳定，存在颜色土、页面空、标题越界和结构遮挡等问题。

改造方向：

- 统一浅灰背景和青绿/蓝色强调色。
- 减少大面积黄色。
- 增加不同版式：cover、statement、visual、table、metric、closing。
- 标题字号根据长度自动调整。
- 图片按比例放入安全区域。
- caption 居中显示。
- 无指标时不再绘制空的右侧占位栏。
- 空值 metric 会被过滤，避免出现“有栏无数据”。

阶段成果：

- PPT 更像正式论文汇报 deck。
- 第 2 页和最后一页的空栏问题被修复。
- 图片注释位置和对齐更自然。
- 页面越界和遮挡风险降低。

## 7. 第六阶段：增加 PPTX QA 和自动返修

为了避免生成后仍有标题溢出、文本框过小、页面空白等问题，新增了 `pptx_qa.py`。

QA 检查内容包括：

- 形状是否超出页面范围。
- 页面是否疑似为空。
- 标题/副标题是否过长。
- 文本框是否太小。
- bullet 列表是否可能纵向溢出。

LangGraph 中加入返修循环：

```text
render -> layout_qa.json -> repair_spec -> render
```

返修动作包括：

- 压缩标题。
- 压缩 takeaway。
- 减少 bullet 数量。
- 截短过长指标。
- 压缩表格。
- 必要时调整布局。

阶段成果：

- 每次输出都会有 `layout_qa.json`。
- 发现风险时可以自动修复并重新渲染。
- 项目从“生成后人工检查”提升为“生成后自动检查和返修”。

## 8. 第七阶段：生成演讲稿

为了让生成结果不仅是 PPT，还能直接用于汇报，项目新增 `speaker_script.md`。

讲稿内容来自最终修复后的 slide spec，因此和 PPT 保持一致。

每页讲稿包含：

- 页面标题。
- Key message。
- Suggested narration。
- 需要强调的指标。
- 需要指向的图片或表格。
- Source trace。

阶段成果：

- 输出从单一 PPT 扩展为 PPT + 汇报讲稿。
- PPT 可以更简洁，详细解释放到讲稿里。
- 适合论文汇报、课程展示和项目复盘。

## 9. 第八阶段：项目清理和发布准备

在确认新路径稳定后，对项目进行了清理。

移除或计划移除的旧内容：

- 上游前端页面。
- Docker 和脚本启动入口。
- 图片生成式示例 assets。
- 旧的文生图 generator。
- 旧的 image generation prompts。
- 仅用于早期 Codex 协作的临时文档。

保留的核心能力：

- PDF 解析。
- 摘要和内容规划。
- LangGraph PPTX workflow。
- 原生 PPTX 渲染。
- PPTX QA。
- speaker script。

阶段成果：

- 项目定位更清楚。
- 运行入口更简单。
- README 和中文 README 面向新用户重写。
- `paper2slides/.env.example` 成为公开配置模板。

## 10. 当前项目能力总结

paper2ppt 当前已经具备以下能力：

- 一键从 PDF 生成 editable PPTX。
- 使用文本大模型进行内容策展。
- 使用论文原始图片，不生成新图片。
- 同步生成讲稿。
- 自动检查并修复部分排版风险。
- 支持从 checkpoint 复用前面阶段，降低重复调用成本。

当前典型命令：

```powershell
python -m paper2slides --input path\to\paper.pdf --output slides --style academic --length medium --fast
```

只重跑生成阶段：

```powershell
python -m paper2slides --input path\to\paper.pdf --output slides --style academic --length medium --fast --from-stage generate
```

## 11. 面试时可以强调的技术点

- 从“文生图式 PPT”重构为“原生可编辑 PPTX”。
- 使用结构化 slide spec 解耦内容策展和渲染。
- 使用 LangGraph 编排多节点生成流程。
- 通过 QA 节点形成生成-检查-修复闭环。
- 通过 speaker script 把详细解释从 PPT 页面中拆出来。
- 在成本上避免文生图模型，只使用文本模型和原始论文素材。
- 保留 checkpoint 机制，支持低成本重跑。

## 12. 后续可改进方向

- 增加更强的真实 PowerPoint 渲染级视觉 QA。
- 支持更多 deck theme。
- 支持自动把论文表格转换为更高级的图表。
- 支持模板导入和品牌风格约束。
- 把 speaker script 进一步拆成逐页 speaker notes 写入 PPTX。
