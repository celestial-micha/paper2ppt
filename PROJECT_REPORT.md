# Paper2Slides 项目运行与改造报告

## 1. 我对这个项目的理解

`Paper2Slides` 是一个“把论文或文档自动转成海报 / Slides”的多阶段流水线项目。

它的核心目标不是直接把 PDF 渲染成 PPT，而是先把文档内容结构化理解，再由大模型重新规划演示结构，最后用图像生成模型产出每一页 slide 的视觉稿，并把这些页面合成为 `slides.pdf`。

从代码结构上看，项目主要分成 4 块：

- `paper2slides/raganything/`
  负责文档解析、提取图片表格、生成 markdown 和中间结构。
- `paper2slides/summary/`
  负责把原始解析结果进一步整理成适合大模型理解的内容摘要。
- `paper2slides/generator/`
  负责两件事：
  1. 用 LLM 规划 slides/poster 的页面结构。
  2. 用图片模型生成每一页 slide/poster。
- `paper2slides/core/`
  负责整个 4-stage pipeline 的编排、checkpoint 管理、断点续跑。

这个项目的一个关键设计思想是：

- 前半段做“内容理解”
- 后半段做“视觉生成”
- 中间通过 checkpoint 解耦

这使得它很适合后续做局部替换，比如：

- 换 LLM
- 换图片生成模型
- 换规划逻辑
- 换成 LangChain / LangGraph 编排


## 2. 这个项目运行的整体流程

### 2.1 命令入口

CLI 入口在：

- [paper2slides/main.py](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/main.py)

你执行的命令：

```bash
python -m paper2slides --input test_papers/AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast
```

这个命令会构造一份配置，然后交给 `core/pipeline.py` 执行。


### 2.2 四阶段流水线

主编排在：

- [paper2slides/core/pipeline.py](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/core/pipeline.py)

阶段如下：

1. `rag`
   解析 PDF，提取文本、表格、图片、markdown、中间结构。

2. `summary`
   基于解析结果生成更适合规划阶段使用的内容摘要。

3. `plan`
   调用文本大模型，把摘要、表格、图片信息组织成 slide plan。
   输出是 `checkpoint_plan.json`，里面有每一页的标题、正文、引用哪些 figure/table。

4. `generate`
   调用图片生成模型，为每一页 slide 生成图片，并最终合成 `slides.pdf`。


### 2.3 checkpoint 机制

项目非常依赖 checkpoint。

主要文件有：

- `checkpoint_rag.json`
- `checkpoint_summary.json`
- `checkpoint_plan.json`
- `state.json`

输出目录结构大致是：

```text
outputs/<project>/<content_type>/<mode>/
```

例如这次任务：

- `outputs/AGI_Is_Coming_Wordle/paper/fast/`

而某个具体配置在：

- `outputs/AGI_Is_Coming_Wordle/paper/fast/slides_academic_medium/`

最终产物在带时间戳的目录中，例如：

- [slides.pdf](/d:/coding/agent_paper_to_slider/Paper2Slides-main/outputs/AGI_Is_Coming_Wordle/paper/fast/slides_academic_medium/20260417_203056/slides.pdf)


### 2.4 fast 模式的含义

`--fast` 的意思不是“跳过全部前处理”，而是跳过更重的 RAG indexing 路径，优先走更直接的解析 + LLM 规划流程。

即使在 `fast` 模式下，项目依然会：

- 解析文档
- 提取图表
- 调用文本模型做 plan
- 调用图片模型生成页面


## 3. 这次运行遇到的问题，以及解决方式

### 3.1 现象一：输出目录里没有最终 PDF

最开始你已经看到：

- `outputs` 下有 `fast`
- 也有 `rag_output`
- 但没有你预期的最终 slide PDF

进一步排查发现，真正的原因不是“输出路径找错了”，而是 pipeline 在生成阶段之前或生成阶段内部没有真正产出有效页面。


### 3.2 问题一：图片生成链路没有走通

根因：

- 项目原始代码只支持旧的图片生成方式：
  - OpenRouter 风格的 `chat.completions`
  - Google 原生 Gemini `generateContent`
- 但你实际验证可用的是中转的：
  - `POST /v1/images/generations`

也就是说：

- `.env` 里即使写了 key / base_url / model
- 只要项目代码本身不会走这条接口
- 图片生成仍然不会成功

解决方式：

我修改了图片生成器，让它支持一个新的 provider：

- `openai_images`

对应代码：

- [paper2slides/generator/image_generator.py](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/generator/image_generator.py)

这个分支会调用：

```text
POST {IMAGE_GEN_BASE_URL}/images/generations
```

并从返回值中读取：

- `data[0].b64_json`


### 3.3 问题二：旧 checkpoint 是坏的

当时生成阶段虽然“成功执行”，但输出是：

- `Generated 0 images`

进一步检查：

- `checkpoint_plan.json` 里的 `sections` 为空数组

这意味着：

- 不是 generate 阶段不会画图
- 而是 plan 阶段先前失败后，留下了一个无效 checkpoint

解决方式：

- 删除旧的 `checkpoint_plan.json`
- 删除旧的 `state.json`
- 强制从 `plan` 重新跑

这一步之后，新的 plan 成功生成了 `9 sections`。


### 3.4 问题三：环境里存在坏掉的代理变量

这是这次最关键的真实根因之一。

环境变量里有：

- `HTTP_PROXY=http://127.0.0.1:9`
- `HTTPS_PROXY=http://127.0.0.1:9`
- `ALL_PROXY=http://127.0.0.1:9`

这会导致：

- `openai` SDK 请求中转时报连接拒绝
- `requests` 请求中转时报连接拒绝
- 甚至你写好的 `shunyu_relay_demo.py` 在这个终端里也会失败

也就是说，问题不只是项目代码，而是“当前进程的网络环境”。

解决方式：

我在：

- [paper2slides/__init__.py](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/__init__.py)

加入了一个启动时自动清理坏代理的逻辑。

注意，这里不是粗暴清空所有代理，而是只清理明显错误的占位代理，例如：

- `127.0.0.1:9`
- `localhost:9`

这样做的目的是：

- 避免误伤以后你真正需要的企业代理
- 但能保证当前这个项目默认可跑


### 3.5 问题四：state.json 状态展示不准确

在我清掉坏 checkpoint 并重建状态文件后，新的 `state.json` 里前两阶段会显示成 `pending`，虽然不影响产物，但会误导后续调试。

解决方式：

我在：

- [paper2slides/core/pipeline.py](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/core/pipeline.py)

补了初始化逻辑：

- 如果已有 `rag` / `summary` / `plan` checkpoint
- 那么重新创建 state 时就把对应阶段标记成 `completed`


## 4. 我修改了哪些部分，以及你接下来要注意什么

### 4.1 修改文件列表

这次我实际改了这些文件：

1. [paper2slides/.env](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/.env)
   重新写入了和 `shunyu_relay_demo.py` 一致的中转配置。

2. [paper2slides/generator/image_generator.py](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/generator/image_generator.py)
   新增 `openai_images` provider，支持 `images/generations`。

3. [paper2slides/__init__.py](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/__init__.py)
   加入坏代理自动清理逻辑。

4. [paper2slides/core/pipeline.py](/d:/coding/agent_paper_to_slider/Paper2Slides-main/paper2slides/core/pipeline.py)
   修复重新建 state 时的阶段状态推断。

5. [outputs/AGI_Is_Coming_Wordle/paper/fast/slides_academic_medium/state.json](/d:/coding/agent_paper_to_slider/Paper2Slides-main/outputs/AGI_Is_Coming_Wordle/paper/fast/slides_academic_medium/state.json)
   把这次运行的状态修正成真实完成状态。


### 4.2 当前可用配置

现在项目里与中转相关的关键环境变量是：

```env
RAG_LLM_API_KEY=...
RAG_LLM_BASE_URL=https://api.shunyu.tech/v1
LLM_MODEL=gpt-5-mini

IMAGE_GEN_PROVIDER=openai_images
IMAGE_GEN_API_KEY=...
IMAGE_GEN_BASE_URL=https://api.shunyu.tech/v1
IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview-0.5k
```


### 4.3 你后续要特别注意的地方

1. `shunyu_relay_demo.py` 现在是“事实上的配置真源”
   如果以后你改 key、文本模型、图片模型、base_url，最好优先维护这个 demo，再同步到 `.env`。

2. 图片生成现在默认不走 OpenRouter chat 模式
   而是走 `openai_images` 新分支。
   如果以后换模型或换供应商，需要先确认对方是否支持：
   - `POST /v1/images/generations`
   - 返回 `b64_json`

3. 如果再次出现“生成成功但 0 images”
   第一时间检查：
   - `checkpoint_plan.json` 里的 `sections` 是否为空
   - `state.json` 里的 `error`

4. 如果再次出现连接错误
   第一时间检查环境变量：
   - `HTTP_PROXY`
   - `HTTPS_PROXY`
   - `ALL_PROXY`

5. 当前最终输出其实是“图片式 slides PDF”
   不是 `.pptx`
   这一点很重要。
   项目现在生成的是：
   - 多张 slide 图片
   - 再合成 `slides.pdf`
   不是 PowerPoint 可编辑页面。


### 4.4 接下来如果你要继续跑，应该怎么跑

先激活环境：

```bash
conda activate paper2slides
```

然后在项目根目录运行：

```bash
python -m paper2slides --input test_papers/AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast
```

如果只是重新生成图片，不想重新 plan：

```bash
python -m paper2slides --input test_papers/AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast --from-stage generate
```

如果你改了文本模型、prompt、规划逻辑，建议从 `plan` 重跑：

```bash
python -m paper2slides --input test_papers/AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast --from-stage plan
```

如果你怀疑 checkpoint 污染了，就删除该配置目录下的：

- `checkpoint_plan.json`
- `state.json`

再重跑。


## 5. 给后续 LangChain 改造的思考和分析

这一部分是写给“网页版后续分析用”的。

### 5.1 这个项目很适合用 LangChain / LangGraph 改造的点

因为它天然就是一个多阶段 Agent / Workflow 项目：

- 文档解析
- 内容摘要
- 页面规划
- 图像生成
- 状态恢复

这和 LangGraph 的状态机思想非常接近。

如果后续做 LangChain / LangGraph 化，我认为最自然的切入点是：

1. 把 `rag -> summary -> plan -> generate` 显式建模成 graph
2. 把每个 stage 的输入输出 schema 明确化
3. 把 checkpoint 从“散落的 json 文件”升级成“结构化 state”
4. 给每个阶段补上可重试、可观测、可替换模型的接口层


### 5.2 当前架构的优点

1. 已经有 stage 分层
   这意味着不是一坨脚本，很适合重构。

2. 已经有 checkpoint
   说明项目本身已经接受“长流程 + 断点恢复”的思路。

3. 内容规划与图片生成已经分开
   后续你可以只替换 plan 逻辑，不一定动 generate。


### 5.3 当前架构的痛点

1. 模型接入层不够统一
   文本模型和图片模型的接入方式分散在多个模块里，provider 抽象不完整。

2. `.env` 和代码能力之间可能失配
   这次就是典型案例：
   `.env` 可以填，但代码未必真的支持那条 API。

3. checkpoint 缺乏强校验
   `checkpoint_plan.json` 即使 `sections=[]` 也能被认为存在，导致“看起来能续跑，实际上续的是坏状态”。

4. 输出语义不够清晰
   从用户视角会以为在生成“PPT”，但项目实际上生成的是“slide images + pdf”。

5. 状态与错误恢复不够强
   `state.json` 有记录，但还不够稳健，不能完全反映 checkpoint 真实情况。


### 5.4 我建议后续优先改造的方向

如果后续你想让网页版的我给出改造建议，我建议优先围绕这几个问题展开：

1. 如何把模型调用抽象成统一接口
   例如：
   - `TextLLMClient`
   - `ImageGenClient`
   - provider adapters

2. 如何让 checkpoint 有效性可验证
   例如：
   - plan checkpoint 必须有非空 `sections`
   - generate 前必须校验 section 数量 > 0

3. 如何把 pipeline 升级成 LangGraph state machine
   例如每个节点产出结构化状态：
   - `parsed_content`
   - `summary_content`
   - `presentation_plan`
   - `generated_assets`

4. 如何让“文档内容理解”和“视觉风格生成”彻底解耦
   这样以后可以：
   - 先固定 plan
   - 单独反复试 style
   - 甚至一个 plan 对应多套视觉输出

5. 是否要新增真正的 `.pptx` 输出链路
   现在这个项目离“可编辑 PPT”还有距离。
   如果业务目标真的是 PPT，而不是 PDF 展示稿，那么后续需要新增：
   - PPT 布局生成
   - python-pptx 或类似工具输出
   - 图片/文本/图表的可编辑落版


### 5.5 我建议你发给网页版我的重点问题

你把这份报告发给网页版后，可以重点让它围绕下面几个方向出谋划策：

1. 如何用 LangChain / LangGraph 重构当前 4-stage pipeline
2. 如何设计统一的模型适配层，兼容文本 LLM 和图片生成 API
3. 如何设计更鲁棒的 checkpoint 校验和恢复机制
4. 如何把当前“生成图片 PDF”的系统升级成“生成可编辑 PPTX”的系统
5. 如何在保留现有项目可运行性的前提下，做渐进式重构，而不是推倒重来


## 6. 本次最终结果

这次已经成功跑通。

最终结果文件：

- [slides.pdf](/d:/coding/agent_paper_to_slider/Paper2Slides-main/outputs/AGI_Is_Coming_Wordle/paper/fast/slides_academic_medium/20260417_203056/slides.pdf)

对应页面图片目录：

- [20260417_203056](/d:/coding/agent_paper_to_slider/Paper2Slides-main/outputs/AGI_Is_Coming_Wordle/paper/fast/slides_academic_medium/20260417_203056)

本次成功生成：

- 9 页 slide
- 1 个合成 PDF


## 7. 一句话结论

这个项目目前已经可以在你现有中转配置下正常跑通，但它的“模型接入层、checkpoint 校验、状态恢复、输出类型语义”都还有明显可重构空间；如果后续要引入 LangChain / LangGraph，这个项目是适合做渐进式重构的，不需要推倒重来。
