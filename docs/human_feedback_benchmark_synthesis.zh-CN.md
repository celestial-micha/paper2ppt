# Human Feedback Benchmark Synthesis

本文档沉淀本轮 Kimi K2 from-scratch PPT 实验中，通过用户反馈、系统实现和多轮迭代得到的 benchmark 经验。它的目标不是记录某一版 PPT 的美化细节，而是把这些细节转成未来可复用、可检测、可回归、可自动修复的评估体系。

## 1. 当前共识

本轮实验最重要的共识是：

```text
不要重新解析论文。
复用已经做得很好的 summary / plan / slide_spec checkpoints。
从这些已解析内容出发，重新组织 PPT 叙事、proof object、布局和视觉系统。
```

也就是说，from-scratch 不是从 PDF 解析重新开始，而是从「论文理解已完成」开始。它禁止复用 golden baseline 的视觉骨架，但允许复用已有论文解析结果、内容理解、figure/table/metric 引用和过去 QA 中积累的问题修复经验。

这个方向兼顾了效率和创新：

- 复用解析链路，避免重复消耗 MinerU / RAG / LLM 时间。
- 不复用旧模板骨架，避免新方案只是 golden baseline 换皮。
- 把人类审美反馈沉淀成 benchmark rules，而不是停留在手工改图。

## 2. 与 Golden Baseline 的关系

当前项目形成两条 benchmark 路线。

### Track A: Mature Baseline Suite

用于稳定回归和生产可用性评估。

```text
academic
academic_warm
editorial
editorial_mono
data_report
```

其中 `academic` 是 golden baseline，必须保护。其他 companion styles 可以保留和回归，但它们仍然接近 baseline，不应该作为下一阶段「全新模板」的主线。

Track A 关注：

- artifact success
- QA pass rate
- warning rate
- text overflow
- table / metric readability
- style preset 回归

### Track B: From-Scratch Template Experiment

用于探索「不复用 baseline 视觉骨架」的生成能力。

Track B 可以复用：

- `checkpoint_summary.json`
- `checkpoint_plan.json`
- `checkpoint_slide_spec.json`
- figure/table/metric extraction
- 已有 QA 和人工反馈经验

Track B 禁止复用：

- baseline 标题栏骨架
- baseline key message block 主结构
- baseline numbered points 默认节奏
- baseline title / toc / section / content macro skeleton

Track B 关注：

- content inventory 是否完整
- rough draft 是否内容完整
- slide role 是否合理
- proof object 是否支撑 claim
- visual system 是否有独立审美
- novelty_score 是否足够高
- human feedback 是否被转成 badcase rules

## 3. 本轮迭代时间线

### 3.1 起点：用户确认不要重解析论文

用户指出：Kimi K2 论文已经解析得很好，重点不应该是重开 PDF 解析链路，而应该从已有大模型解析内容出发，把这些内容迭代好放进 PPT。

由此确认了 from-scratch 的边界：

- 从 checkpoints 继续。
- 不重新跑论文解析。
- 先做 content inventory。
- 再做 rough draft。
- 最后做新的视觉系统和自动审计。

### 3.2 v1 问题

第一版 rough draft 的主要问题：

- 没有像学术汇报一样的标题页。
- 没有目录页和模块拆分。
- 页面几乎总是右侧一个巨大矩形 proof panel。
- 右侧 proof panel 不管有没有图片/表格都出现，导致节奏单调。
- 文本证据页 proof panel 空，内容很少但容器很大。
- 表格没有完整读取进 PPT，导致「要放表格却只剩文字描述」。
- 系统没有能力从生成后 PPT 中抽页检查实际效果。

对应沉淀的 badcases：

```text
missing_title_slide
missing_agenda_slide
layout_monotony
empty_proof_panel
table_rows_missing
text_evidence_as_large_panel
no_rendered_visual_feedback
```

### 3.3 v2 改进与新问题

第二版加入了标题页、目录页、section divider 和更多 layout families，结构明显变好。但用户继续指出：

- 黑白配色过重，论文整体缺少生命力。
- section divider 虽然好看，但整套都是黑白，显得枯燥。
- 标题页顶部黑色横条难看。
- 标题页三个小矩形 metric chips 意义不清，位置和字体都不够好。
- 目录页 1/2/3/4 黑色圆按钮很丑。
- 目录页右侧只放 content slide count 有点单薄，需要更有意义的小组件。
- 一些 proof panel 仍然太空，尤其 limitation / motivation / method。
- 表格或组件可能遮挡文字。
- metric 页面质量不稳定：有些布局好看，有些很丑。
- 用户再次强调：不是让 Codex 人工截图，而是让系统生成后能控制 PPT 抽页、视觉读取、自动反馈和改进。

对应沉淀的 badcases：

```text
boring_black_white_palette
title_black_top_bar
meaningless_cover_chips
agenda_black_number_dots
thin_right_side_component
short_text_large_panel
metric_card_inconsistency
component_overlap_risk
system_cannot_see_rendered_deck
```

### 3.4 v3 解决方案

第三版的主要修复：

- 新增 warm academic palette：
  - warm paper background
  - muted teal
  - soft gold
  - clay accent
  - sage / light panel colors
- 标题页去掉黑条，改成暖纸底、左侧色带、右侧 source inventory rail。
- 目录页去掉黑圆点编号，改成细长模块标记和右侧 deck map。
- section divider 去掉整页黑底，改成暖底、左侧色带、底部 module checkpoint。
- 短文本 proof 不再进入大空 panel，而是进入 evidence card stack。
- metric layout 改成更稳定的三类：
  - `metric_left`
  - `metric_compact_band`
  - `metric_left_alt`
- table proof 保留 native table，并显示 parsed rows。
- `visual_audit.json` 升级到 v2，写入 `visual_review_manifest`。
- 新增可选 `--render-review-dir`，让系统在有 PowerPoint COM 或 LibreOffice 时导出重点页 PNG。

对应实现位置：

```text
paper2slides/benchmark/from_scratch.py
test_phase1_pptx.py
```

当前 v3 结果：

- `rough_draft_v3.pptx`
- 30 slides
- 4 native tables
- 6 pictures
- `inspect_pptx_layout` passed
- zero layout warnings
- `visual_audit.json` includes 14 render requests
- 当前机器无 PowerPoint COM / LibreOffice，因此 `visual_render_status.json` 正确标记为 `renderer_unavailable`

## 4. From-Scratch Benchmark Pipeline

当前 from-scratch benchmark 可以拆成 7 步。

### Step 1: Content Inventory

输入：

```text
checkpoint_summary.json
checkpoint_plan.json
checkpoint_slide_spec.json
```

输出：

```text
content_inventory.json
```

必须包含：

- paper metadata
- summary items
- plan slides
- curated slides
- figures
- tables and parsed rows
- metrics
- coverage
- source checkpoints
- reuse constraints

评估重点：

- 是否复用 checkpoint，而不是重解析 PDF。
- figures/tables/metrics 是否完整登记。
- table rows 是否真的解析出来。
- core sections 是否覆盖 motivation / method / results / contribution。

### Step 2: Rough Draft Spec

输出：

```text
rough_draft_spec.json
```

每页必须有：

- `slide_id`
- `title`
- `slide_role`
- `claim`
- `support`
- `proof_object`
- `source_evidence`

原则：

- 第一目标是内容完整。
- 不追求第一版就好看。
- 不允许为了审美删掉 evidence。

### Step 3: Narrative Organization

生成目录和模块：

```text
Motivation & Research Gap
Method & System Design
Experiments & Results
Summary & Takeaways
```

slide roles 包括：

```text
title
thesis
mechanism
figure_explainer
table_interpretation
metric
evidence
conclusion
```

评估重点：

- 目录是否存在。
- 模块是否能覆盖论文逻辑。
- section divider 是否服务叙事，而不是装饰。
- proof object 是否与 claim 匹配。

### Step 4: Visual System

本轮得到的审美经验：

- 学术 PPT 可以有颜色，但颜色应当低饱和、有语义、克制。
- 不要一整套黑白搭配，容易显得枯燥。
- 不要用黑条、黑圆点、无意义小方块当默认装饰。
- evidence container 必须承载信息关系，不能只是填空。
- 短文本证据适合小卡片或底部 strip，不适合大空 panel。
- metric cards 要保持完整 grammar：value + label + context。
- table 要优先保证行列可读，不要被大标题或色块遮挡。

### Step 5: Visual Audit Manifest

`visual_audit.json` 现在不只是统计 layout family，还包含机器可读视觉复查计划：

```json
{
  "visual_review_manifest": {
    "requires_rendered_screenshots": true,
    "render_requests": [
      {
        "page": 1,
        "reason": "title page: cover composition and color balance",
        "severity": "high",
        "expected_artifact": "slide_01.png"
      }
    ],
    "badcase_rules": [
      "cover must not use a full-width black top bar",
      "agenda module numbers must not be black circular buttons",
      "short text evidence must render as compact notes rather than a large empty proof panel"
    ]
  }
}
```

这一步把「用户觉得丑」转成了可执行检查目标：

- 哪些页要截图。
- 为什么要截图。
- 哪些坏例必须判失败。
- 未来视觉模型或截图 QA 应该看什么。

### Step 6: Render Review Hook

新增 CLI：

```powershell
python -m paper2slides.benchmark inventory `
  --summary-checkpoint <checkpoint_summary.json> `
  --plan-checkpoint <checkpoint_plan.json> `
  --spec-checkpoint <checkpoint_slide_spec.json> `
  --output-dir <out_dir> `
  --pptx-output <deck.pptx> `
  --render-review-dir <review_png_dir>
```

当前支持尝试：

- PowerPoint COM + pywin32
- LibreOffice / soffice

如果本机没有 renderer，输出：

```text
visual_render_status.json
status = renderer_unavailable
```

这是正确行为：系统不能假装已经做了视觉审阅。

### Step 7: Human Feedback To Rules

每次人工反馈都应该转成：

```text
badcase:
trigger:
severity:
example_slide:
root_cause:
repair_strategy:
auto_fix:
regression_check:
```

例如：

```text
badcase: short_text_large_panel
trigger: proof_object.type == text_evidence and text length is short, but layout uses a large panel
severity: medium
root_cause: renderer treats all proof objects as equal-size panels
repair_strategy: route short text evidence to compact card stack or bottom strip
auto_fix: yes
regression_check: rendered page should not contain a large mostly empty proof panel
```

## 5. 评分体系

未来 benchmark 应融合 golden baseline 经验和本轮 human feedback 经验，形成六类评分。

### 5.1 reliability_score

检查能不能稳定生成：

- PPTX exists
- JSON artifacts exist
- layout QA exists
- command succeeds
- no severe warnings
- repair loop does not fail

### 5.2 content_score

检查内容是否正确和完整：

- core sections covered
- slide count reasonable
- title/agenda/closing present
- claim/support/evidence complete
- table/figure/metric references preserved
- no unsupported claims

### 5.3 visual_layout_score

检查排版是否正确：

- no out-of-bounds shapes
- no text overflow
- no component overlap
- proof object readable
- table rows readable
- metric value/label visible
- whitespace not obviously broken

### 5.4 aesthetic_score

检查是否好看：

- palette harmony
- typography hierarchy
- visual rhythm
- balance between restraint and vitality
- cover polish
- agenda polish
- section divider polish
- metric card consistency
- table polish

### 5.5 novelty_score

只用于 from-scratch track，检查是否不是 baseline 换皮：

- header skeleton similarity
- key message block similarity
- numbered points dominance
- repeated macro layout similarity
- title/toc/section/content page grammar similarity
- contact sheet novelty

### 5.6 visual_feedback_score

检查系统是否具备「生成后自我看图」的闭环能力：

- `visual_review_manifest` exists
- high-risk pages selected
- render requests are precise
- screenshot export status recorded
- renderer missing is explicit
- future vision judge can consume the manifest

## 6. Badcase Registry

本轮已经沉淀的坏例：

| badcase | 现象 | 修复策略 |
| --- | --- | --- |
| `missing_title_slide` | 学术汇报没有封面 | 固定生成 title slide |
| `missing_agenda_slide` | 没有目录和模块规划 | 根据 section buckets 生成 agenda |
| `layout_monotony` | 每页都是右侧大框 | 引入 layout family counts 和重复检测 |
| `empty_proof_panel` | 大 panel 内容很少 | 短文本走 cards / strip |
| `table_rows_missing` | 表格只剩描述 | HTML table -> parsed rows -> native table |
| `boring_black_white_palette` | 黑白过重、没有生命力 | warm academic palette |
| `title_black_top_bar` | 封面黑横条丑 | 改成色带 + source inventory rail |
| `meaningless_cover_chips` | 三个小方块无意义 | 改成语义化 source inventory |
| `agenda_black_number_dots` | 目录黑圆点编号丑 | 改成细长模块标记 |
| `short_text_large_panel` | limitation/method 短证据页空 | compact evidence card stack |
| `metric_card_inconsistency` | 21 好看但 22/23/24 丑 | 稳定 metric grammar 和布局族 |
| `component_overlap_risk` | 表格/文字互相遮挡 | layout QA + render requests |
| `system_cannot_see_rendered_deck` | 只能靠人手动截图发现 | `visual_review_manifest` + `--render-review-dir` |

## 7. 当前命令

生成 Kimi K2 v3：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark inventory `
  --summary-checkpoint outputs\Kimi_K2_Technical_Report\paper\fast\checkpoint_summary.json `
  --plan-checkpoint outputs\Kimi_K2_Technical_Report\paper\fast\slides_academic_medium_24slides\checkpoint_plan.json `
  --spec-checkpoint outputs\Kimi_K2_Technical_Report\paper\fast\slides_academic_medium_24slides\checkpoint_slide_spec.json `
  --output-dir outputs\Kimi_K2_Technical_Report\paper\fast\from_scratch_inventory `
  --pptx-output outputs\Kimi_K2_Technical_Report\paper\fast\from_scratch_inventory\rough_draft_v3.pptx `
  --render-review-dir outputs\Kimi_K2_Technical_Report\paper\fast\from_scratch_inventory\review_pages_v3
```

验证：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
C:\Users\81001\.conda\envs\paper2slides\python.exe -m unittest test_phase1_pptx.py
```

## 8. 下一阶段计划

下一步不再先改审美，而是打开真实 render-review 闭环：

1. 安装或接入可用 PPTX -> PNG renderer。
2. 让 `--render-review-dir` 真正导出重点页图片。
3. 接入视觉 judge，读取 `visual_review_manifest.badcase_rules`。
4. 先做规则型判断：
   - 是否有大面积空 panel。
   - 是否有黑条/黑圆点坏例。
   - 是否有表格遮挡。
   - 是否有 metric label 缺失。
   - 字体是否过小。
5. 再做视觉模型判断：
   - cover 是否学术、简洁、大方。
   - agenda 是否规划清晰。
   - section divider 是否有生命力但不过度花。
   - metric / table 页是否专业。
6. 根据判断结果自动生成 repair hints。
7. 先修字体大小和局部布局。
8. 再扩展到 ai20。

最终目标：

```text
给定论文解析结果
 -> 自动生成内容正确 PPT
 -> 自动导出重点页截图
 -> 自动判断格式和审美 badcases
 -> 自动修复 Top 问题
 -> 形成可回归 benchmark report
```

## 9. v4-v6 追加沉淀：从“继续变好”到“知道何时回退”

本轮后续迭代进一步说明了一件重要的事：benchmark 不只要记录“修了什么”，还要记录“哪种看似合理的自动优化反而让结果变差”。因此 `rough_draft_v5` 被确认为当前人工审美接受的参考版本，而 `rough_draft_v6` 被记录为一次需要回退的视觉回归。

### 9.1 标题页：醒目组件必须承载论文亮点

用户指出，标题页右侧如果放一个很醒目的圆角矩形，不应该只写“16 figures / 6 tables / 35 metrics”这类 source inventory。对学术汇报而言，首页最重要的是让听众快速知道论文为什么值得听。

沉淀规则：

```text
cover side rail should summarize paper highlights, not only source depth.
```

修复策略：

- 从已有 `summary / plan / slide_spec / metrics` 中提取 cover-ready highlights。
- 优先展示 `Core result`、`Scale`、`Design edge`、`Evidence scope`。
- 保留“复用已解析 checkpoint，不重跑 PDF 解析”的原则。
- 如果要展示 figures / tables / metrics 数量，只能作为次要信息，不能占据标题页视觉主位。

对应 badcase：

```text
meaningless_cover_stats
trigger: cover 右侧组件只展示 source counts，没有论文贡献摘要
repair: derive 3 paper highlights from parsed checkpoints
```

### 9.2 证据卡片：版式变化要服务庄重感

v3/v4 中 evidence notes 的三张彩色卡片已经明显比大空白 proof panel 好看，但用户指出它在多页重复出现时仍然会单调；同时把这组三卡片放到左侧时，页面显得不够庄重。

沉淀规则：

```text
right-side and bottom evidence notes are preferred for formal academic pages.
left-side evidence triplets should be avoided unless a specific layout needs them.
```

修复策略：

- 短文本证据优先使用右侧 stack、底部 notes、mosaic，而不是大空 panel。
- evidence notes 可以变化，但变化不应破坏学术汇报的稳定感。
- 左侧证据组三卡片不是禁用所有左侧 proof object，而是禁用“左侧三彩卡片作为主视觉”的默认用法。

对应 badcases：

```text
short_text_large_panel
layout_monotony
left_triplet_gravitas_loss
```

### 9.3 表格遮挡：必须作为共性问题，而不是单页补丁

用户多次发现 table proof panel 会覆盖正文或说明文字。这说明问题不应只在某一页手工下移，而应成为 benchmark 的通用规则。

沉淀规则：

```text
table proof panels must reserve a readable gutter below claim/support text.
```

检测策略：

- 在非视觉层面读取 PPTX shape bounding boxes。
- 检查 title / claim / support / table / proof panel 是否发生高风险重叠。
- table_bottom layout 需要专门进入 visual_review_manifest。
- 如果渲染能力可用，高风险表格页必须导出截图复核。

对应 badcase：

```text
component_overlap
trigger: table or proof panel intersects body text box
repair: move proof panel lower, reduce proof height, or split layout
```

### 9.4 字体与密度：当前阶段只做非视觉检查

用户提出一个很关键的工程判断：不能指望每一页都截图并调用视觉模型，因为成本高、速度慢，而且很多问题其实可以从 PPTX 本身检测。

因此当前阶段 benchmark 应采用 metadata-only 策略：

```text
non-visual metadata checks only; no screenshot review; no vision model judge.
```

直接分析 PPTX：

- 每类文本的字体大小下限。
- text box 面积与词数的密度。
- card / panel 是否大而空。
- shape 是否重叠。
- table 是否有 native rows / columns。
- metric 是否有 value + label + context。
- layout family 是否过度重复。

这一路线特别强调：组件比例和构图已经被人类认可时，低密度检查只能提示“文字/字号/内容分配可能需要调整”，不能直接驱动组件缩放。v6 的回退就是反例：局部看似更贴合文字量，但整体观感变怪。

这个策略已经写入：

```text
benchmarks/from_scratch_human_feedback_benchmark.json
```

并新增代码入口：

```powershell
python -m paper2slides.benchmark nonvisual-audit --pptx <deck.pptx> --output <nonvisual_audit.json>
```

from-scratch 生成链路也会默认写出：

```text
nonvisual_audit.json
```

### 9.5 v5 是当前审美参考，v6 是一次回归样本

v6 尝试了两个看似合理的优化：

- 把 agenda read path 改成 2x2 流程组件。
- 对文字少的 evidence cards 做更激进的高度压缩。

但用户反馈是：v6 没有 v5 好看，整体感觉怪。这里的教训非常重要：局部规则指标的提升，不等于整页构图和整体审美提升。

沉淀规则：

```text
human preference is a regression guard.
```

具体含义：

- `rough_draft_v5` 是当前 accepted reference。
- 后续任何自动审美优化，如果改变 v5 的主要视觉语法，都必须证明自己更好，或者获得人工确认。
- 非视觉 density heuristic 只能作为风险提示，不能单独决定视觉改版。
- benchmark 要记录“被回退的尝试”，因为它们是未来自动 repair loop 最容易再次犯的错。

对应 badcase：

```text
overoptimized_density_regression
trigger: new heuristic improves local density but human preference worsens
repair: gate visual-system changes behind accepted-reference comparison
```

## 10. 新增机器可读 Benchmark 资产

本轮新增：

```text
benchmarks/from_scratch_human_feedback_benchmark.json
```

该文件把聊天反馈整理成机器可消费的结构：

- `accepted_reference`: 当前接受版本是 `rough_draft_v5`。
- `core_principles`: 复用已解析 checkpoints、内容优先、反馈转规则、低成本检查优先。
- `iteration_log`: v1-v6 每轮问题和修复。
- `badcase_rules`: 缺标题页、缺目录页、版式单调、短文本大空框、表格缺行、组件遮挡、黑白枯燥、封面统计无意义、agenda 侧栏干、v6 过度优化回归等。
- `aesthetic_rubric`: 把“好看”拆成 academic polish、palette vitality、layout variety、evidence readability、typography density、visual review readiness、novelty without content loss。
- `automatic_review_strategy`: 明确哪些问题先靠 PPTX 元数据检查，哪些页面才需要截图和视觉模型。

这让 benchmark 不只是文档，也可以成为后续 runner / audit / repair loop 的配置来源。

## 11. 2026-06-12 追加：从人工审美迭代抽象出的自动生成流程

这轮对话最重要的新结论是：我们不是让系统“漫无目的地从零生成 PPT”，而是让系统先选择一种明确的演示任务类型，再在这个任务类型约束下生成和审计。

对于论文汇报 PPT，任务类型不是普通营销页，也不是纯数据报告，而是：

```text
academic paper-reading deck
```

它天然要求：

1. 有正式标题页，让听众知道论文主题、作者/团队、核心亮点。
2. 有目录页，把论文拆成 motivation / method / experiments / takeaways 等模块。
3. 有 section divider，让听众知道当前进入哪一段论证。
4. 有结尾页，完成汇报闭环。
5. 每个内容页必须围绕一个主 claim，而不是堆很多平级文字。
6. 每个 claim 都要配支持性说明和 proof object：图、表、指标、机制图、evidence cards 或简洁 notes。
7. 视觉系统要服务论文阅读：克制、有层级、有生命力，但不能过度装饰。

因此，真正可自动化的流程应该是：

```text
paper checkpoints
 -> content inventory
 -> deck architecture contract
 -> slide semantic contract
 -> visual system contract
 -> first PPTX
 -> non-visual metadata audit
 -> ranked badcases
 -> bounded repair
 -> benchmark report
```

### 11.1 先定款式，再定结构，再定组件

这次 v5 成功，不是因为某一个卡片参数偶然好看，而是因为先建立了完整的“学术论文汇报语法”：

- **款式协议**：warm academic palette、纸张底色、teal/gold/clay 语义色、克制圆角和阴影。
- **deck 架构协议**：title、agenda、section、content、closing 缺一不可。
- **页面角色协议**：thesis、mechanism、evidence、table interpretation、metric、conclusion 各自有不同信息密度。
- **proof object 协议**：短文本走 evidence cards，表格走 native table，指标走 metric cards，图走 figure panel。
- **组件位置协议**：正式学术页优先右侧或底部 evidence，不默认使用左侧三彩卡片；table bottom 要预留正文 gutter。

只有这些协议先稳定，后面再微调字体大小、文本截断、行距和局部排版才不会把整体弄怪。v6 的回退说明：如果直接按文字量缩组件，局部似乎更紧凑，但会破坏整页节奏和庄重感。

### 11.2 无视觉条件下如何识别错误

没有截图和视觉模型时，系统不能真正“看见”页面，但它可以把 PPTX 当成一个结构化布局程序来检查。PPTX 里已经有足够多的可观测信息：

- shape 类型、位置、宽高、层级。
- 文本框内容、字体大小、段落数量。
- 表格行列数量、单元格文本长度。
- 图片和图表的 bounding box。
- slide role、layout family、proof object 类型。
- claim / support / evidence 的来源关系。

这些信息足以检测很多过去靠人眼发现的问题：

- 缺 title / agenda / closing。
- 目录模块和实际页码不一致。
- claim 缺 support 或 proof object。
- 短文本被放进巨大空 panel。
- table panel 和正文重叠。
- table 只有 caption，没有 native rows。
- metric card 缺 value / label / context。
- 字体低于角色下限。
- 文本接近容量上限。
- layout family 过度重复。
- 组件位置违背已接受的学术风格规则。

也就是说，当前阶段的 benchmark 不追求“像人一样审美看图”，而是先把人类反馈中可结构化的部分转成规则。审美被拆成可观测代理指标：结构完整、层级清楚、组件语义正确、留白不过度失衡、布局不过度重复、配色使用有语义。

### 11.3 自动修复优先级

后续自动修复不应该一发现低密度就缩组件。更稳妥的优先级是：

1. 先修内容正确性：缺证据、缺表格行、缺指标值、unsupported claim。
2. 再修 deck 结构：标题页、目录页、章节页、结尾页、模块页码。
3. 再修语义匹配：claim / support / proof object 是否对应。
4. 再修文字：字号下限、文案压缩、换行、拆分 notes。
5. 只有出现遮挡、越界、表格不可读、布局连续重复时，才修改组件位置或大小。
6. 已经被人类认可的组件比例不能因为低密度单独触发缩放。
7. 视觉系统级变化必须作为新的 style contract 版本，并和 v5 accepted reference 对比。

### 11.4 面向 20 篇论文的 benchmark 闭环

最终 benchmark 应该同时支持两种任务：

- **生成任务**：给定一篇论文 PDF 或已有 checkpoints，从内容库存到最终 PPT 自动生成，并通过非视觉审计做 1-3 轮 bounded repair。
- **评估任务**：对 20 篇论文和不同模板输出打分，记录 reliability、content、visual_layout、aesthetic、novelty，并输出 badcase 和修复建议。

其中 aesthetic_score 在当前非视觉阶段不是“人眼美感真值”，而是由代理规则组成：

- title / agenda / section / closing 是否完整。
- 视觉语法是否符合学术汇报风格。
- palette 是否有克制的语义色。
- layout family 是否有节奏变化。
- proof object 是否根据内容类型选择。
- 字体层级是否清楚。
- 低密度是否只作为提示，而不是破坏构图的自动改版理由。

这样，未来即使没有 human-in-the-loop，系统也能先通过规则发现大部分结构性和排版性问题，再把少数真正依赖人类审美的选择留给人工或未来可选视觉分支。

## 12. 下一轮 Human-in-the-loop 重点：Typography / Copy Fitting

当前 accepted reference 的主要问题已经不再是“有没有标题页、目录页、章节页、组件是否单调”这类第一阶段问题，而是更细的 polish 问题：

```text
组件布局好看了，
但部分页面文字偏少、字号偏小、留白显得空，
需要让系统在保留构图的基础上自动调节文字。
```

这类问题不能再简单理解为“低密度就缩组件”。v6 的回退说明，局部密度优化可能破坏整体美感。因此下一轮 human-in-the-loop 反馈要重点区分：

- **typography problem**：字号、层级、字重、行距不合适。
- **copy fitting problem**：文字太短、太长、重复或分配不均。
- **geometry problem**：真正发生遮挡、越界、表格不可读或布局重复。

默认修复策略：

1. 先调字号和字体层级。
2. 再调换行、行距和文案分配。
3. 再考虑补充或压缩 evidence 文案。
4. 只有结构性失败时才调组件大小或位置。

下一轮每条人工反馈都应该记录成下面格式：

```text
badcase:
example_slide:
problem_type: typography | copy_fitting | geometry
human_observation:
non_visual_trigger:
preferred_repair:
forbidden_repair:
regression_check:
```

示例：

```text
badcase: sparse_card_copy
example_slide: rough_draft_v5 slide 15
problem_type: copy_fitting
human_observation: evidence cards 的组件比例好看，但卡片文字显得少。
non_visual_trigger: card word density below preferred band, no overlap, no out-of-bounds.
preferred_repair: 增强 card body 文案或提高字号/层级。
forbidden_repair: 只因为文字少就缩小整组卡片。
regression_check: 组件整体比例保持，card 字号和信息密度提高。
```

这会把下一轮“文字大小调优”的人工经验继续转成 benchmark 资产。

## 10. 2026-06-13 补充：从 v10/mHC 学到的跨论文规则

Kimi K2 的 v10 样式已经被人工认为非常成功，但 mHC 交叉验证说明：一个样式在主论文上成功，并不等于可以立刻成为 golden baseline。跨论文验证的价值在于暴露不同 proof payload 的形状。

本轮新增两类问题：

- **非正方 figure 布局问题**：Figure 4 / Figure 6 这种超宽图不能继续使用普通右侧竖向 proof panel；DeepSeek_V4 的 Figure 1 / Figure 7 这类高图也不能放入接近正方形的 panel。布局选择要看图片原始长宽比，高图使用竖向 proof panel，中宽/宽图使用底部横向 proof panel，并且图片插入必须保持原始比例。
- **figure 图片居中问题**：v16 的硬侧边标签栏虽然释放了图片上方高度，但保留整列会把图片推离 panel 中心。标签应是紧凑注释，图片和 caption 才是圆角 proof panel 的居中主体。
- **inline table payload 问题**：slide_spec 里已经有 rows 的表格，如果 proof id 使用展示标题而不是 extracted table id，渲染器也必须能索引到这些 inline rows，不能退化成一个空感很强的文本面板。
- **浅窄卡片内部间距问题**：同一种 evidence card 在高卡片或宽卡片里舒服，不代表在矮且窄的卡片里也舒服。卡片内部 label/body gap、body box 高度和底部 padding 要随局部 frame 高度变化。
- **agenda rail 微间距问题**：Read path header 和 P/M/E/T 节点之间距离太近时，组件虽然没有错位，但会少一点最终 polish 的呼吸感。
- **table support band 问题**：table-bottom 页面即使没有 overlap，support 解释文字也可能离表格太近、离 claim 太远，导致阅读重心被 proof panel 往下拉。
- **proof caption 容量问题**：DeepSeek_V4 这类图注更长的论文会让固定高度 caption box 溢出；页面 caption 应按框容量截断，完整说明保留在 source evidence 中。

新增 badcase：

```text
wide_figure_forced_into_side_panel
inline_table_payload_not_indexed
figure_picture_aspect_distortion
card_internal_spacing_not_scaled_to_frame
agenda_read_path_header_too_close
table_support_band_off_balance
proof_caption_overflow_after_cross_paper_transfer
figure_panel_aspect_mismatch
figure_image_off_center_in_panel
figure_label_anchor_drift
```

DeepSeek_V4 v18 继续补充了 figure 标签的锚点问题：`FIGURE / Figure N` 不能只看作 proof panel 的标题，而要看作 fitted image 的附属注释。底部横向图的标签应贴在图片左上方；侧边高图可以让 `Figure N` 竖排贴在图片左侧；caption 固定高度并按容量截断，不能自动增高撑出圆角 panel。

这把 benchmark 的判断从“proof object 类型正确”推进到：

```text
proof object type correct
 -> proof payload exists
 -> payload shape understood
 -> component frame chosen by payload shape
 -> payload rendered without distortion or empty fallback
```

因此新的修复优先级应补充为：

1. 内容 payload 是否存在：table rows、figure file、metric value。
2. payload id 是否能解析：asset id、curated title、inline rows 都要能被索引。
3. payload 形状是否适配布局：高图、明确宽图、长表、密集 metric 不应共用同一种容器；只有约 1.9x 以上宽高比才默认下沉到底部长条 panel。
4. 渲染是否保持语义：图片不拉伸，表格保持 native row/column grammar。
5. 组件内部文字栈是否适配局部容器：浅窄卡片不能照搬高卡片或宽卡片的固定间距。
6. 最终 polish 是否需要低风险小规则：例如 agenda rail header 到节点的 clearance，figure image 到 panel center 的偏移，table 页 claim/support/table-panel 的垂直 band balance，或 proof caption 的容量适配，不应触发大范围布局重排。

这条经验很关键：human-in-the-loop 不是让 Codex 手工修某一页，而是把“这一页为什么不舒服”转成下一篇论文也能复用的规则。

## 11. 2026-06-15 收官：从单页审美到 style-scoped benchmark

DeepSeek_V4 v25 被用户确认为满意版本，并被保存为：

```text
golden_baseline1_from_scratch_warm_academic
```

这轮收官让 benchmark 从“记录某个坏例子”进一步升级为“维护多个风格参考”的系统。

### 11.1 Proof panel 标签的最终语义拆分

后期最多的反馈集中在圆角 proof panel 的标签上。最终结论是：

```text
绿色类型角标：说明这个圆角矩形是什么类型的 proof panel。
黑色身份标题：说明这个 proof panel 的主体内容是什么。
主体内容：图片、表格、指标卡或解释文字。
```

因此：

- 绿色 `FIGURE` / `TABLE` / `TEXT_EVIDENCE` 留在 panel 内部左上角；
- 黑色 `Figure N`、`Doc Table 1`、`Table 2`、`Motivation`、`Method` 等，应锚定下方主体内容的水平中心线；
- 文本框几何居中还不够，段落本身也要居中；
- 这些规则只适用于采用 rounded proof-panel grammar 的风格，不应无条件套到所有模板。

对应新增或强化的 badcase：

```text
figure_label_text_alignment_off_center
panel_identity_label_anchor_drift
panel_identity_label_text_alignment_off_center
figure_badge_identity_label_conflation
stacked_figure_identity_label_overcorrection
```

### 11.2 Style scope 成为 benchmark 必需字段

用户担心：新 benchmark 会不会反过来破坏已经迭代好的原 golden baseline。

答案是：如果不加 scope，会有风险。

所以从 v25 起，benchmark 应区分：

```text
global correctness rules
mature academic baseline rules
golden_baseline1 rounded proof-panel rules
experimental style rules
```

默认策略：

```text
全局 correctness rule 可以 auto-repair；
风格相关 polish rule 先 detect/report；
只有 active style contract 匹配时才 auto-repair。
```

这让 benchmark 同时具备两种能力：

- 保护原 `academic` golden baseline；
- 继续用 `golden_baseline1` 的经验自动改进同类风格。

### 11.3 下一阶段验证方式

下一篇新论文不应只生成一个 PPT，而应解析一次、生成三路：

1. 原 `academic` golden baseline；
2. `golden_baseline1_from_scratch_warm_academic`；
3. 原 `academic` + global benchmark repair。

这样可以同时观察：

- 原 baseline 是否回退；
- golden_baseline1 是否泛化；
- benchmark 是否能修内容/结构错误，但不造成 style drift。

单篇稳定后，再扩展到 `ai20`。最后再做一个 blind from-scratch loop：不复用 `academic` 或 `golden_baseline1` 的视觉骨架，只复用 checkpoint 内容和 benchmark badcases，让 agent 自动迭代出第三种风格。

这就是最终可以包装成 benchmark harness 的核心故事。
