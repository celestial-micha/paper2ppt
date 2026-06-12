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

### 9.4 字体与密度：先做非视觉检查，再选择性截图

用户提出一个很关键的工程判断：不能指望每一页都截图并调用视觉模型，因为成本高、速度慢，而且很多问题其实可以从 PPTX 本身检测。

因此后续 benchmark 应采用两阶段策略：

```text
cheap non-visual checks first, selective rendered/vision checks second.
```

第一阶段，直接分析 PPTX：

- 每类文本的字体大小下限。
- text box 面积与词数的密度。
- card / panel 是否大而空。
- shape 是否重叠。
- table 是否有 native rows / columns。
- metric 是否有 value + label + context。
- layout family 是否过度重复。

第二阶段，只对重点页截图：

- 标题页。
- 目录页。
- section divider。
- 高风险表格页。
- 短文本证据页。
- metric 页。
- 被非视觉检查标记为 overlap / sparse / low font 的页面。

这个策略已经写入：

```text
benchmarks/from_scratch_human_feedback_benchmark.json
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
