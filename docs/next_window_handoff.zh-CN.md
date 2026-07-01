# 新窗口交接说明 V2

本文档是给下一次 Codex 窗口的启动手册。核心目的：避免新窗口误以为下一步还是继续做 `academic` 换皮模板，而是要接住 **from-scratch template experiment**。

## 新窗口请直接发送这段话

```text
codex老师，我们继续做 Paper2Slides-main / paper2ppt。请先阅读：

1. docs/benchmark_plan.zh-CN.md
2. docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
3. docs/next_window_handoff.zh-CN.md
4. docs/agent_workflow.md
5. README.zh-CN.md

请先不要写代码，先规划。

现在的目标已经更新：

1. `academic` 是 golden baseline，必须保护，不要重构。
2. `academic_warm`、`editorial`、`editorial_mono`、`data_report` 是已经筛出来的 baseline companion styles。它们好看，要保留，但它们太像 golden baseline，不是下一步要继续创造的新模板。
3. 下一步不是继续调颜色或 preset，而是做 from-scratch template experiment。
4. from-scratch 的意思不是重新解析一切，而是可以复用 Kimi K2 已解析内容；但不能复用 golden baseline 的视觉骨架。
5. 我们要从 content inventory 开始，先做无审美但内容完整的草稿，再重新设计章节、目录、slide role、claim、proof object、视觉系统，最后用 benchmark 自动检测和迭代。
6. benchmark 不只检测是否出错，还要检测内容是否完整、排版是否清楚、审美是否好、以及新模板是否过度像 golden baseline。
7. 每轮我给你的人工反馈，都要被整理成可自动检测、可自动修复或可回归的 benchmark rule。

请你先输出一个详细执行规划，不要改代码。规划要包括：

- content_inventory.json 的 schema。
- 无审美草稿 PPT/spec 的生成方式。
- slide role / proof object 的定义。
- reliability/content/layout/aesthetic/novelty 五类评分如何做第一版规则型实现。
- 如何检测新模板是不是 golden baseline 换皮。
- 如何把人工反馈转成 badcase rule。
- 第一轮用 Kimi_K2_Technical_Report.pdf 做 from-scratch 实验的步骤。
- 哪些步骤可以复用已有 checkpoint，哪些情况才需要重新调用大模型。

模型路由：
- 文本：deepseek-v4-flash，base_url=https://api.deepseek.com。
- 图片/多模态：gpt-5-mini，base_url=https://api.shunyu.tech/v1。
- 不要把 DeepSeek 用于 image_url 多模态输入。
- 不要打印或提交 API key。

git 注意：
- paper2slides/.env、outputs/、benchmark_runs/、test_papers/ 不要提交。
- 改代码后跑 python -m unittest test_phase1_pptx.py。
```

## 新窗口的第一句话应该确认什么

新窗口 Codex 应先复述下面三点：

1. 当前不是继续打磨 `academic_warm/editorial/editorial_mono/data_report`。
2. 当前是要规划一个不模仿 golden baseline 的 from-scratch 新模板实验。
3. 第一轮先规划 schema、评分、迭代规则，不直接写代码。

如果新窗口没有复述这三点，说明它还没接住任务。

## 当前项目状态

工作目录：

```text
D:\coding\agent_paper_to_slider\Paper2Slides-main
```

当前 git checkpoint：

```text
branch: codex/from-scratch-benchmark-plan
remote: origin/codex/from-scratch-benchmark-plan
commit: ba94020 docs: clarify from-scratch benchmark plan
```

说明：

- 这个 commit 已经 push 到 GitHub 远端分支。
- 本地 `main` 也暂时指向同一个 commit，但远端 `origin/main` 还停在上一个提交。
- 当前还有 companion styles 相关代码改动未提交，包括 `paper2slides/generator/style_presets.py` 和若干 renderer/pipeline 文件。新窗口第一轮只做规划时，不要误以为这些代码已经进入远端文档 commit。
- 后续如果要保存 companion styles 代码，建议单独测试并单独 commit。

成熟模板：

```text
academic
```

保留的 companion styles：

```text
academic_warm
editorial
editorial_mono
data_report
```

这些 companion styles 的定位：

- 好看。
- 可以保留。
- 可以和 `academic` 一起做 mature suite 回归。
- 但不是 from-scratch 新模板。

当前 benchmark 数据集：

```text
ai20
```

Kimi K2 已跑通：

```text
test_papers/Kimi_K2_Technical_Report.pdf
```

golden baseline evidence：

```text
benchmark_runs/ai20_20260607_005847/aggregate_report.md
outputs/Kimi_K2_Technical_Report/paper/fast/slides_academic_medium_24slides/20260607_010126/slides.pptx
```

## 为什么要这样做

我们发现：只靠 `style_presets.py`、palette、header、key message、metric card、少量 renderer 分支，很容易得到好看的 companion styles，但它们仍然像 golden baseline。

用户真正想要的是：

```text
复用论文解析结果
但不复用 baseline 页面骨架
从内容库存开始
一步步做出全新视觉系统
并把每轮问题变成 benchmark rule
最后让 agent workflow 能自动检查和迭代
```

## 新窗口第一轮不要做什么

不要：

- 不要继续做新的换色模板。
- 不要直接改 `pptx_renderer.py`。
- 不要上来跑 Kimi K2 生成。
- 不要跑 ai20 全量。
- 不要把 `academic_warm/editorial/editorial_mono/data_report` 当作新模板。
- 不要重构 `academic`。
- 不要调用视觉模型做全量 judge。

## 新窗口第一轮应该做什么

只做规划，输出以下内容：

1. `content_inventory.json` schema。
2. rough draft spec schema。
3. slide role taxonomy。
4. proof object taxonomy。
5. 第一版规则型评分设计：
   - `reliability_score`
   - `content_score`
   - `visual_layout_score`
   - `aesthetic_score`
   - `novelty_score`
6. baseline similarity 检测规则。
7. 人工反馈到 benchmark rule 的格式。
8. 第一轮 Kimi K2 from-scratch 实验步骤。
9. 后续代码实现顺序。

## 后续如果用户确认规划

再进入代码实现，建议顺序：

1. 新增 content inventory 生成器。
2. 新增 rough draft spec 生成器。
3. 新增 content quality / novelty scoring。
4. 新增 iteration report。
5. 用 Kimi K2 单篇生成第一版 from-scratch 草稿。
6. 用户反馈。
7. 把反馈写成 benchmark rules。

## 测试命令

改代码后运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
C:\Users\81001\.conda\envs\paper2slides\python.exe -m unittest test_phase1_pptx.py
```

## 文件提交注意

不要提交：

```text
paper2slides/.env
outputs/
benchmark_runs/
test_papers/
```

不要打印、复制或提交任何 API key。

## 2026-06-12 补充：Human Feedback From-Scratch 复盘

本轮 Kimi K2 from-scratch PPT 实验已经从 v1/v2 迭代到用户认可的 v3。新的复盘文档见：

```text
docs/human_feedback_benchmark_synthesis.zh-CN.md
```

下一个窗口继续本任务时应优先阅读该文件。它补充了：

- 为什么 from-scratch 不是重新解析 PDF，而是复用已有 checkpoints。
- v1 的标题页/目录页缺失、右侧大 proof panel 单调、表格读取不足等问题。
- v2 的黑白配色、封面黑条、目录黑圆点、短文本大空框、metric 卡片质量不稳定等问题。
- v3 的暖色学术视觉系统、封面 source inventory rail、目录 deck map、section divider、evidence card stack、metric layout 重构。
- `visual_audit.json` 的 `visual_review_manifest` 设计。
- `--render-review-dir` 的可选 PPTX 页面截图导出钩子。
- 如何把用户反馈沉淀成 badcase registry、aesthetic_score、visual_feedback_score 和未来自动修复闭环。

当前 v3 本地生成物位于：

```text
outputs/Kimi_K2_Technical_Report/paper/fast/from_scratch_inventory/rough_draft_v3.pptx
```

注意：`outputs/` 和 `*.pptx` 被 `.gitignore` 忽略，不进入 Git。应提交的是代码、测试和文档，而不是生成产物。

## 2026-06-12 再补充：当前 from-scratch 参考已更新到 v5

上面的 v3 说明是上一阶段记录。当前最新人工反馈已经继续推进到 v5/v6：

- `rough_draft_v5.pptx` 是当前用户认为更好看的 accepted reference。
- `rough_draft_v6.pptx` 没有 v5 好看，已经决定回退。
- v6 的问题不是功能失败，而是一次审美回归：2x2 read path 和过度压缩 sparse evidence cards 让整体观感变差。
- 后续任何自动审美优化都应该和 v5 对比，不能只看局部密度或几何指标。

下一轮继续时，除了阅读 `docs/human_feedback_benchmark_synthesis.zh-CN.md`，还要优先阅读新增机器可读规则：

```text
benchmarks/from_scratch_human_feedback_benchmark.json
```

它记录了：

- v1-v6 的人类反馈链路。
- v5 accepted reference。
- v6 regression guard。
- badcase rules。
- aesthetic rubric。
- 当前阶段 non-visual-only 的 review 策略：不截图、不调用视觉模型。

下一轮推荐入口：

```text
请先不要重新解析论文，也不要直接重做视觉系统。
先读取 benchmarks/from_scratch_human_feedback_benchmark.json，
让 benchmark runner / from_scratch audit 能消费这些规则，
再接入 PPTX 元数据检查：字体大小、文本容量、shape overlap、table grammar、metric grammar 和低密度风险。
当前阶段不要打开 --render-review-dir，不要调用视觉模型。
```

## 2026-06-12 三补充：默认转为非视觉自动审计与纠偏

最新用户决策：当前阶段彻底放弃“生成单页图片再让视觉模型读图”的默认路线。原因是：

- 截图/视觉模型成本高。
- PowerPoint/LibreOffice 渲染依赖复杂。
- 很多问题可以直接从 PPTX 元数据判断。
- v5 的组件比例已经比较好看，不能因为局部文本密度盲目缩组件。

新窗口继续时应采用：

```text
non-visual metadata audit first
```

也就是用 PPTX 对象本身检查：

- slide role 是否有 title / agenda / section / content / closing。
- agenda 模块和 slide ranges 是否一致。
- 每页 claim / support / proof object 是否完整。
- table 是否有 native rows / columns。
- metric 是否有 value / label / context。
- shape bounding boxes 是否遮挡或越界。
- 各角色字体是否低于下限。
- text capacity 是否接近溢出。
- low density 是否只是提示，而不是自动缩组件理由。
- layout family 是否过度重复。
- 是否触发 v1-v6 human feedback badcase rules。

当前推荐工作流：

```text
reuse parsed checkpoints
 -> content inventory
 -> deck architecture contract
 -> slide semantic contract
 -> style contract
 -> render PPTX
 -> nonvisual_audit.json
 -> repair top 1-3 badcases
 -> compare with accepted reference / previous attempt
 -> stop or rerun
```

修复优先级：

```text
内容正确性 > deck 架构 > 语义匹配 > 字体/文案 > 几何位置 > 视觉系统改版
```

重要约束：

- 不要为了低密度直接缩组件。
- 已经被 v5 验证过的组件比例优先保留。
- 如果必须改组件大小，必须有 overlap、越界、表格不可读、连续重复布局等结构性理由。
- 视觉系统级改动必须写入新的 `style_contract`，不能散落成单页 patch。
- 默认不要打开 `--render-review-dir`。
- 默认不要调用视觉模型。

新增/更新的关键文件：

```text
benchmarks/from_scratch_human_feedback_benchmark.json
paper2slides/benchmark/nonvisual_audit.py
docs/human_feedback_benchmark_synthesis.zh-CN.md
docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
docs/benchmark_plan.zh-CN.md
```

下一步如果继续改文字大小问题，应先读取 `nonvisual_audit.json` 的 findings，用 typography/copy allocation 修复；除非出现结构性失败，否则不要改变整体组件构图。

## 2026-06-13 四补充：新窗口启动词与下一阶段目标

用户准备打开新窗口继续沟通。新窗口的目的不是重新总结 benchmark，也不是重新设计整套 PPT 风格，而是继续 human-in-the-loop 迭代当前 from-scratch PPT，重点解决：

```text
组件摆放和整体风格已经基本被认可；
下一步要在不破坏组件构图的前提下，
让系统自动调节字号、行距、换行、文案分配和文本密度；
实在不行时，再非常克制地微调组件大小或位置。
```

### 新窗口第一条消息建议直接发送

```text
codex老师，我们继续做 D:\coding\agent_paper_to_slider\Paper2Slides-main 这个项目。

请先阅读并遵守这些文件：

1. docs/next_window_handoff.zh-CN.md
2. docs/human_feedback_benchmark_synthesis.zh-CN.md
3. docs/benchmark_plan.zh-CN.md
4. docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
5. benchmarks/from_scratch_human_feedback_benchmark.json
6. paper2slides/benchmark/nonvisual_audit.py

当前上下文：
- 我们已经把 Kimi K2 from-scratch PPT 从 v1 迭代到 v5，v5 是当前用户认可的 accepted reference。
- v6 因为局部自动优化导致整体观感变怪，已经作为 overoptimized_density_regression 记录下来。
- 当前阶段默认不使用 --render-review-dir，不截图，不调用视觉模型。
- 默认使用 PPTX metadata-only / nonvisual-audit 来检查字体、文本容量、shape overlap、table grammar、metric grammar、layout repetition 和 badcase rules。
- 我们的目标不是重做视觉系统；v5 的组件比例、整体构图、warm academic 风格要优先保留。

这次新窗口的任务：
1. 继续 human-in-the-loop 调整 from-scratch PPT。
2. 重点解决“文字少、文字小、留白显得空”的问题。
3. 先用非视觉审计和 PPTX 元数据估算每页字号、文本容量、低密度和接近溢出风险。
4. 修复优先级必须是：字体大小 / 行距 / 换行 / 文案分配 / notes 拆分，优先于组件缩放。
5. 只有出现遮挡、越界、表格不可读、布局连续重复等结构性问题时，才允许微调组件大小或位置。
6. 每一轮发现的问题和修复经验，都要继续写回 benchmark 文档或机器可读规则，增强后续自动生成能力。

请先不要重新解析论文，也不要直接大改 PPT 风格。
请先检查当前 git 状态，确认哪些是已提交内容、哪些是遗留脏文件。
然后给我一个本轮 typography / copy fitting 迭代计划，再开始改。
```

### 新窗口不要做的事

- 不要重新解析 Kimi K2 论文 PDF。
- 不要重新设计整套视觉系统。
- 不要把 v5 的组件比例因为低密度直接缩小。
- 不要默认打开 `--render-review-dir`。
- 不要默认调用视觉模型。
- 不要把旧的 `paper2slides/core/*`、`paper2slides/generator/*` 脏文件误认为本轮必须提交的改动；先读 `git status` 判断。

### 新窗口应该优先做的事

1. 读取 `benchmarks/from_scratch_human_feedback_benchmark.json`，确认 accepted reference、badcase rules、non-visual-only policy。
2. 读取 `nonvisual_audit.json` 或重新对目标 PPTX 跑：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark nonvisual-audit --pptx <deck.pptx> --output <nonvisual_audit.json>
```

3. 把 findings 分成三类：
   - typography：字号太小、层级不清、正文/卡片字重不合适。
   - copy fitting：文字过短、过长、重复、分配不合理。
   - geometry：真正遮挡、越界、表格不可读、组件需要微调。
4. 默认先修 typography / copy fitting。
5. 如果必须修 geometry，要说明为什么不是单纯为了低密度。
6. 每轮只修 Top 1-3 个问题，避免 v6 式过度优化。
7. 生成新 PPT 后再跑 `nonvisual-audit` 和单测。
8. 把新的经验继续写入 benchmark 文档和规则文件。

### 本阶段要沉淀的新 benchmark 能力

下一阶段 human-in-the-loop 的重点是把“文字适配”沉淀成自动规则：

- 不同文本角色的字号下限和理想范围。
- claim / support / evidence card / table / metric 的文本容量估算。
- 低密度只提示，不直接缩组件。
- 短文本优先增大字号、增加层级、改写为更有信息量的 bullet，而不是改组件。
- 长文本优先拆分、改写、移动到 notes 或分配到多个 cards。
- 组件微调必须有结构性原因，并被记录为 geometry repair。

最终目标是让系统在组件摆放已经好看的基础上，自动完成第二阶段 polish：

```text
good composition
 -> typography fitting
 -> copy density fitting
 -> minimal geometry repair only if necessary
 -> benchmark rule update
```

## 2026-06-14 最新交接补充

当前 mHC 验证输出已经推进到：

```text
outputs/mHC：Manifold-Constrained Hyper-Connections/paper/fast/from_scratch_inventory/mHC_v14_table_support_balance.pptx
```

这版是在 v13 基础上继续做的 micro-polish：第 26 页和第 28 页 table-bottom 页面中，support 解释文字更靠近上方 claim，并与下方 table panel 保持更舒服的 gutter。当前相关 micro-polish badcase：

```text
agenda_read_path_header_too_close
table_support_band_off_balance
```

随后 DeepSeek_V4 已经用同一套 checkpoint-only 路径生成并推进到 v18：

```text
outputs/DeepSeek_V4/paper/fast/from_scratch_inventory/DeepSeek_V4_v18_figure_label_anchor_refine.pptx
```

DeepSeek_V4 暴露的新规则是 proof caption 容量适配：长 figure caption 需要按 caption box 的宽、高、字号截断，完整说明留在 source evidence 中。对应 badcase：

```text
proof_caption_overflow_after_cross_paper_transfer
```

DeepSeek_V4 第二轮还暴露了 figure aspect 与 proof panel aspect 的匹配问题：Figure 1 / Figure 7 这类高图应使用竖向 side proof panel；明确宽图应使用底部横向 proof panel。第三轮说明：`FIGURE / Figure N` 不应作为保留整列的硬侧栏，而应作为紧凑注释；图片和 caption 应在完整 panel 内居中。对应 badcase：

```text
figure_panel_aspect_mismatch
figure_image_off_center_in_panel
```

第四轮曾进一步说明：`Figure N` 身份标签要锚定 fitted image，而不是做成保留整列的 label rail。第五轮人工反馈修正了这里的语义：绿色 `FIGURE` 不是图片标题，而是圆角 figure panel 的类型角标，所以它必须放在 panel 内部左上角；黑色 `Figure N` 才靠近 fitted image。第六轮尝试逐字堆叠 `F / I / G / U / R / E / N`，但第七轮人工复核认为竖排观感更差。第八轮最终微调为：`Figure N` 横排放在图片外部上方，按 fitted image 水平中心线对齐，贴近图片但不进图片内部，从而和绿色 `FIGURE` 拉开距离。第九轮补充：文本框中心对齐还不够，段落本身也必须居中，否则可见文字仍会左偏。第十轮补充：普通 `visual_left` / `visual_right` figure proof panel 也不能保留整行左对齐 `Figure N` 标题，必须和宽图/高图 panel 一样先 fit image，再按图片中心线放置标签。第十一轮补充：非 figure proof panel 也遵守同一语义拆分，绿色类型角标留在 panel 左上角，黑色身份标题如 `Motivation`、`Method`、`Doc Table 1`、`Table 2` 要按下方解释文字、表格、指标或图片的主体中心线居中，且段落本身居中。底部横向图和左右侧高图都遵守这个拆分。左侧高图 panel 占住页面左下区域时，source footer 仍应放到右下角并右对齐。对应 badcase：

```text
figure_label_anchor_drift
figure_badge_identity_label_conflation
figure_label_text_alignment_off_center
panel_identity_label_anchor_drift
panel_identity_label_text_alignment_off_center
stacked_figure_identity_label_overcorrection
```

下一窗口不要把这类问题升级为重构任务。当前阶段的正确动作是：

1. 保留 v10/v14 的整体风格和构图。
2. 只接受边界清楚的局部微调。
3. 每个微调都写入 benchmark badcase、nonvisual audit rule 和测试。
4. 生成新 PPT 后跑 nonvisual audit 和 `test_phase1_pptx.py`。

## 2026-06-15 收官交接：启动三路新论文验证

当前 DeepSeek_V4 from-scratch warm academic proof-panel 风格已经迭代到用户满意版本：

```text
outputs/DeepSeek_V4/paper/fast/from_scratch_inventory/DeepSeek_V4_v25_panel_identity_label_centered.pptx
outputs/DeepSeek_V4/paper/fast/from_scratch_inventory/nonvisual_audit_DeepSeek_V4_v25_panel_identity_label_centered.json
```

并已保存为第二个黄金参考：

```text
style_id: golden_baseline1_from_scratch_warm_academic
outputs/golden_baselines/golden_baseline1_from_scratch_warm_academic/DeepSeek_V4_golden_baseline1_from_scratch_warm_academic.pptx
outputs/golden_baselines/golden_baseline1_from_scratch_warm_academic/nonvisual_audit_DeepSeek_V4_golden_baseline1_from_scratch_warm_academic.json
```

后续不要继续微调 DeepSeek_V4 v25，除非用户明确指出新问题。下一阶段目标是验证 benchmark 的泛化能力和风格隔离能力。

### 新窗口首要任务

用一篇新论文做三路验证：

1. ordinary original golden baseline：
   - style: `academic`
   - repair profile: `audit_only`
   - 用于确认成熟 baseline 未被新 benchmark 破坏。

2. golden baseline1：
   - style: `golden_baseline1_from_scratch_warm_academic`
   - repair profile: `golden_baseline1_repair`
   - 用于验证 v25 风格能否泛化并通过 scoped repair 自动迭代。

3. benchmark-improved original golden baseline：
   - style: `academic`
   - repair profile: `global_correctness_repair`
   - 只允许 global correctness auto-repair；风格相关 polish 只能 report/suggest。

每一路都要输出：

```text
slides.pptx
speaker_script.md
nonvisual_audit.json
repair_log.json
style_drift_report.json
```

### 风格隔离原则

新 benchmark 不能默认把 golden_baseline1 的 rounded proof-panel 语法套到 original `academic` baseline 上。

默认策略：

```text
global correctness rule -> 可以 auto-repair
style-specific polish rule -> style contract 匹配才 auto-repair，否则 detect/report only
```

尤其注意这些规则应 scoped：

```text
figure_label_anchor_drift
figure_label_text_alignment_off_center
panel_identity_label_anchor_drift
panel_identity_label_text_alignment_off_center
card_internal_spacing_not_scaled_to_frame
table_support_band_off_balance
```

### 必读文件

新窗口先读：

```text
docs/from_scratch_benchmark_final_synthesis.zh-CN.md
docs/benchmark_plan.zh-CN.md
docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
docs/human_feedback_benchmark_synthesis.zh-CN.md
benchmarks/from_scratch_human_feedback_benchmark.json
paper2slides/benchmark/from_scratch.py
paper2slides/benchmark/nonvisual_audit.py
test_phase1_pptx.py
```

### 给新窗口的建议开场 Prompt

```text
codex老师，我们开启 Paper2Slides benchmark 下一阶段：三路新论文验证。

项目路径：
D:\coding\agent_paper_to_slider\Paper2Slides-main

请不要切换分支，不要 git push；如果需要提交，最后只给我 git add / commit / push 命令。

当前两个黄金参考：
1. original golden baseline: academic
2. golden_baseline1_from_scratch_warm_academic:
   outputs/golden_baselines/golden_baseline1_from_scratch_warm_academic/DeepSeek_V4_golden_baseline1_from_scratch_warm_academic.pptx

请先读：
docs/from_scratch_benchmark_final_synthesis.zh-CN.md
docs/benchmark_plan.zh-CN.md
docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
docs/human_feedback_benchmark_synthesis.zh-CN.md
docs/next_window_handoff.zh-CN.md
benchmarks/from_scratch_human_feedback_benchmark.json
paper2slides/benchmark/from_scratch.py
paper2slides/benchmark/nonvisual_audit.py

下一步目标：
选择一篇新论文，解析一次，复用 checkpoint，同时生成三路 PPT：
1. 普通 academic golden baseline，repair profile = audit_only
2. golden_baseline1_from_scratch_warm_academic，repair profile = golden_baseline1_repair
3. academic + global benchmark repair，repair profile = global_correctness_repair

每一路都需要：
- slides.pptx
- speaker_script.md
- nonvisual_audit.json
- repair_log.json
- style_drift_report.json

重要原则：
- 不要把 golden_baseline1 的 rounded proof-panel polish 规则默认套到 original academic baseline。
- global correctness rule 可以 auto-repair。
- style-specific polish rule 只有 style contract 匹配时才能 auto-repair，否则只能 report/suggest。
- 每次新发现的问题都要沉淀到 benchmark / docs / badcase / tests。

请先检查当前 git 状态和现有 runner 能力，然后给我一个三路验证实施计划；如果已有代码能直接复用，就开始落地。
```

## 2026-07-01 最新交接：golden2 已封版，下一步做六路 hybrid proposal smoke

上面的“三路验证”是 `golden_baseline1` 刚封版时的历史入口。现在状态已经更新：

```text
golden_baseline0: academic
golden_baseline1: golden_baseline1_from_scratch_warm_academic
golden_baseline2: golden_baseline2_blind_rectangular_research_board
```

`golden_baseline2` 保存位置：

```text
outputs/golden_baselines/golden_baseline2_blind_rectangular_research_board/
```

它是 human-in-the-loop 调好的 frozen reference，不要把它当成 fully autonomous style proposal 的证明。下一阶段真正要验证的是：在不读取三套 golden 完整模板的前提下，一条 assisted seed scaffold 和两条 autonomous free proposals 能否通过多轮 repair loop 变好。

### 新窗口首条消息建议

用户给新论文时，建议直接发送：

```text
Codex老师，我们继续 Paper2Slides-main 下一阶段：hybrid style proposal benchmark。

项目路径：
D:\coding\agent_paper_to_slider\Paper2Slides-main

请先阅读：
1. docs/autonomous_style_proposal_benchmark_plan.zh-CN.md
2. docs/style_registry.zh-CN.md
3. docs/benchmark_recording_schema.zh-CN.md
4. docs/style_aware_multistage_benchmark_plan.zh-CN.md
5. docs/from_scratch_benchmark_final_synthesis.zh-CN.md
6. docs/human_feedback_benchmark_synthesis.zh-CN.md
7. benchmarks/from_scratch_human_feedback_benchmark.json
8. paper2slides/benchmark/nonvisual_audit.py
9. paper2slides/benchmark/fourway.py

当前状态：
- academic、golden_baseline1、golden_baseline2 都已经 frozen。
- golden2 是 human-tuned blind_rectangular_research_board，不要把它当成 autonomous style proposal 的证明。
- 下一阶段要用我提供的新论文先做一篇 smoke test。
- 同一篇论文只解析一次，然后生成六路：
  1. academic frozen reference
  2. golden_baseline1 frozen reference
  3. golden_baseline2 frozen reference
  4. assisted seed scaffold style
  5. autonomous style proposal A
  6. autonomous style proposal B
- assisted seed route 可以由 Codex 先给一个非常基础、未成熟的视觉脚手架，但不能读取或复制 golden0/1/2 完整模板、style contract、layout grammar 或 PPTX。
- autonomous style proposal 只能使用论文解析内容、设计约束、抽象 design primitives library 和 badcase registry，不能读取 golden0/1/2 完整模板或 PPTX。
- repair loop 至少支持 2-3 轮，连续两轮无改善或触发 style/human risk 后停止。

我现在给你一篇新下载的论文。请先确认它是否从未解析过，再给出 six-route hybrid smoke 执行计划、需要修改的 runner/audit 文件范围，以及预计输出目录结构。不要先跑五篇论文。
```

### 新窗口第一轮应避免

- 不要继续手工微调 golden2；
- 不要把 `golden_baseline2` 的 layout grammar 给 assisted seed 或 autonomous route 当模板；
- 不要把 assisted seed scaffold 写成成熟模板；它必须只是弱脚手架，并进入 repair loop；
- 不要直接跑 5 篇或 ai20；
- 不要删除已有 `benchmark_runs`；
- 不要在没有确认输出目录和 route schema 前大改 runner。

### 新窗口第一轮应完成

1. 确认新论文是否已有 checkpoint；
2. 如果没有，规划 parse-once checkpoint；
3. 规划六路 route config；
4. 规划 assisted seed scaffold 的 seed contract、authoring note 和 forbidden-reference attestation；
5. 规划 autonomous proposal 的 forbidden-reference attestation；
6. 检查现有 `fourway.py` 是否应升级为 generalized multi-route runner；
7. 列出要新增的 artifacts：`style_proposal_policy.json`、`human_feedback_effort.csv`、`seed_scaffold_contract.json`、`novelty_report.json`、`sixway_result.json`；
8. 只在计划确认后开始跑 smoke。
