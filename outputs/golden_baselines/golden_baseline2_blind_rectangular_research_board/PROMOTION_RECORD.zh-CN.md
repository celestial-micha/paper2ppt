# Golden Baseline2 Promotion Record

日期：2026-07-01

## 结论

`blind_rectangular_research_board` 当前正式保存为第三个人工迭代黄金参考：

```text
golden_baseline2_blind_rectangular_research_board
```

它和 `academic`、`golden_baseline1_from_scratch_warm_academic` 并列，都是 human-in-the-loop 参与后沉淀出来的 frozen reference。它不用于证明全自动 style proposal 已经完成，而用于：

- 保存一套人工认可的直角矩形 research-board 风格；
- 作为后续多风格 benchmark 的 frozen reference route；
- 把本轮人工反馈转成 scoped benchmark rule；
- 对比未来 autonomous style proposal 生成的新风格是否真正独立。

## 保存产物

```text
outputs/golden_baselines/golden_baseline2_blind_rectangular_research_board/
  DeepResidual_20260630_blind_rectangular_golden2_reference.pptx
  nonvisual_audit_DeepResidual_20260630_blind_rectangular_golden2_reference.json
  iter04_table_notes_report.md
  style_manifest.json
```

## 2026-07-02 修订记录

本次只修订首页 cover 的三个空白 `S I G N A L` 说明框，未改变 baseline2 的直角矩形 research-board 版式语法、页面数量和 frozen-reference 身份。

修订原因：原冻结 PPTX 首页已经存在 `S I G N A L 1/2/3` 标签和对应空文本框，但正文没有填入，属于当时生成/封版时留下的 cover copy 缺口，不是后续 six-way deliverables 复制流程造成的。

新增文案：

```text
Signal 1: Claim-first cards expose the problem, method, and evidence path.
Signal 2: Source figures and tables stay traceable inside editable proof panels.
Signal 3: Nonvisual audit converts layout defects into scoped repair rules.
```

修订后 SHA256：

```text
7370E0507C304262F822628F5D0007416CE304ED26174A161F46D0D0BE82813C
```

修订后 nonvisual audit：`finding_count=92`，`high=16`，`medium=11`，`low=65`。finding 数比旧版多 1，是因为新增正文被纳入字体/容量规则统计；视觉上首页信息完整度提高。

源 run：

```text
benchmark_runs/deep_residual_style_aware_rescore_20260630_0001
```

源 PPT：

```text
benchmark_runs/deep_residual_style_aware_rescore_20260630_0001/pptx_for_review/04_blind_rectangular_iter04_table_notes.pptx
```

## 为什么可以晋升

本风格最初不是完全由 autonomous style proposal agent 从抽象原语生成，而是在 Codex/human 共同给出初始 renderer scaffold 后，通过 benchmark 和人工反馈不断细化。

这意味着它不适合直接拿来统计“全自动修复 loop 的 badcase 下降效果”。但它适合晋升为 frozen reference，因为：

- 用户已确认最终视觉效果足够好；
- 多轮人工反馈已经被沉淀成可检测规则；
- 它的视觉语法和 `academic`、`golden_baseline1` 明显不同；
- 它能帮助下一阶段区分“人工迭代成熟模板”和“系统自主提出新模板”。

## 本轮转成规则的人工反馈

| badcase | scope | 处理策略 |
| --- | --- | --- |
| `text_exceeds_container_bounds` | global correctness | auto repair |
| `table_exceeds_container_bounds` | global correctness | auto repair |
| `text_card_vertical_alignment_top_heavy` | golden2 / straight-rectangle | detect + style-scoped repair |
| `image_underutilized_in_wide_panel` | golden2 / wide evidence panel | style-scoped repair |
| `figure_caption_not_centered_in_wide_panel` | golden2 / wide figure panel | style-scoped repair |
| `table_underutilized_in_evidence_panel` | golden2 / focused table view | style-scoped repair |
| `table_view_label_missing` | golden2 / focused table view | style-scoped repair |
| `table_caption_missing_or_not_centered` | golden2 / focused table view | style-scoped repair |
| `metric_improved_visual_regressed` | repair risk | human outcome required |

## 未来使用规则

### 可以

- 在“frozen reference route”中生成或评估 golden2；
- 用 golden2 的规则检测同类直角矩形风格；
- 把本轮人工反馈作为 badcase registry 的样本；
- 用它做面试展示里的 human-in-the-loop evidence。

### 不可以

- 在 autonomous style proposal 阶段读取本 PPTX 当模板；
- 在 autonomous style proposal 阶段读取完整 golden2 layout grammar；
- 把 golden2 的直角矩形规则无条件套到 `academic` 或 `golden_baseline1`；
- 用 golden2 的最终质量声称它是完全自动生成出来的。

## 面试口径

可以这样说：

> 我们先用 human-in-the-loop 把第三种风格迭代成熟，并把每次人类指出的问题转成 scoped benchmark rule。这个阶段不伪装成全自动，而是把人工参与本身量化：记录 feedback turn、changed rule、auto-repair eligibility 和 human outcome。下一阶段再把三套 human-tuned golden references 冻结，只允许系统读取抽象 design primitives 和 badcase registry，从而测试它能不能在不复制模板的情况下自主提出新风格。
