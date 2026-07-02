# Paper2Slides Style Registry

日期：2026-07-01

本文记录当前已经保存的 PPT 款式引用，避免后续窗口只记得“有个 golden baseline”，却没有保存好具体 artifact、规则边界和验证证据。

## Original Academic Golden Baseline

style id：

```text
academic
```

保存目录：

```text
outputs/golden_baselines/original_academic_mature/
```

核心参考：

- `mHC_20260511_010937_academic_original_reference.pptx`
- `mHC_20260511_010937_academic_original_reference_fixed.pptx`
- `DeepSeek_V4_20260510_195014_academic_original_reference.pptx`

结构锚点以 mHC 为准。它的第 2 页 Contents 必须保留六项：

```text
Motivation
Method
Analysis
Ablations
Results
Conclusion
```

DeepSeek_V4 旧版保留为 original academic 的视觉和内容节奏参考，但它的四项 Contents 不应覆盖 mHC 的六模块结构规则。

已验证规则：

- `academic_toc_missing_canonical_sections`
- `academic_right_evidence_void`

已保存验证：

- AGI Wordle：`AGI_Wordle_20260615_academic_validation_six_toc_right_evidence.pptx`
- Deep Residual：`DeepResidual_20260616_academic_validation_fresh_parse.pptx`
- Deep Residual benchmark repair：`DeepResidual_20260616_academic_global_repair_validation.pptx`

## Golden Baseline1

style id：

```text
golden_baseline1_from_scratch_warm_academic
```

保存目录：

```text
outputs/golden_baselines/golden_baseline1_from_scratch_warm_academic/
```

核心 artifact：

```text
DeepSeek_V4_golden_baseline1_from_scratch_warm_academic.pptx
```

定位：

- 从零模板实验沉淀出的 warm academic proof-panel 款式；
- 不替代 original academic；
- rounded proof-panel、绿色类型角标、黑色主体身份标签等规则只在该 style scope 内生效。

新增验证：

- Deep Residual：`DeepResidual_20260616_golden_baseline1_scoped_validation.pptx`

README 预览图：

```text
docs/assets/readme/golden_baseline1_warm_academic_montage.jpg
```

## Golden Baseline2

style id：

```text
golden_baseline2_blind_rectangular_research_board
```

保存目录：

```text
outputs/golden_baselines/golden_baseline2_blind_rectangular_research_board/
```

核心 artifact：

```text
DeepResidual_20260630_blind_rectangular_golden2_reference.pptx
nonvisual_audit_DeepResidual_20260630_blind_rectangular_golden2_reference.json
style_manifest.json
PROMOTION_RECORD.zh-CN.md
```

README 预览图：

```text
docs/assets/readme/golden_baseline2_blind_rectangular_montage.jpg
```

定位：

- 由 `blind_rectangular_research_board` human-in-the-loop 迭代后晋升；
- 和 `academic`、`golden_baseline1_from_scratch_warm_academic` 并列，作为第三个 frozen reference；
- 用于后续多风格 benchmark 的对照 route、回归检查和 human feedback 证据；
- 不用于证明完全自动 style proposal 已经完成。

关键视觉语法：

- 直角矩形 research-board；
- 淡背景网格、顶部细 rail、清晰左右/上下 evidence container；
- 左侧 claim panel 与右侧 evidence panel 的强对齐；
- figure / table 应充分利用大 evidence panel，而不是保守缩小；
- focused table view 需要有上方 label 与下方居中说明；
- text evidence card 的正文不应视觉上顶到卡片上沿。

重要边界：

```text
新风格实验不能读取 golden0/1/2 的完整 PPTX、style contract 或 layout grammar。
assisted seed scaffold route 可以由 Codex 给弱初始脚手架，但不能复制 golden 模板。
autonomous proposal route 只能使用抽象 design primitives library、论文解析内容、设计约束和 badcase registry。
```

新增/固化规则：

- `text_card_vertical_alignment_top_heavy`
- `image_underutilized_in_wide_panel`
- `figure_caption_not_centered_in_wide_panel`
- `table_underutilized_in_evidence_panel`
- `table_view_label_missing`
- `table_caption_missing_or_not_centered`
- `metric_improved_visual_regressed`

## Blind Experimental Blueprint

style id：

```text
blind_experimental_blueprint
```

保存目录：

```text
outputs/candidate_styles/blind_experimental_blueprint/
```

定位：

- 完全不复用 original academic 和 golden_baseline1 视觉模板；
- 只复用内容理解和 benchmark badcases；
- 当前是保存候选，不是 golden baseline。

状态更新：

- 早期 `blind_experimental_blueprint` 仍保留为 candidate archive；
- 后续 Deep Residual 路线中的 `blind_rectangular_research_board` 已另行晋升为 `golden_baseline2_blind_rectangular_research_board`；
- 这不代表 blind route 已经 fully autonomous，因为它经过了 Codex/human scaffold 与多轮人工反馈；
- 下一阶段的 autonomous proposal 必须和三套 golden references 隔离。

已保存候选：

- AGI Wordle v1：`AGI_Wordle_blind_experimental_blueprint_v1.pptx`
- Deep Residual v2：`DeepResidual_blind_experimental_blueprint_v2.pptx`

晋升条件：

- 至少再通过两篇 fresh-paper smoke test；
- high/medium finding 能通过 benchmark-driven repair 明显下降；
- 人工确认它作为独立款式有用；
- 反复出现的问题全部转为 scoped badcase。

## 提交注意

`outputs/` 和 `benchmark_runs/` 默认不进 Git。需要提交的是：

- style registry 文档；
- benchmark JSON 中的机器可读引用；
- renderer / audit / runner / test 代码；
- 每次人工反馈沉淀的 badcase 说明文档。

如果需要把 frozen reference artifact 保存到 GitHub，需要显式 force-add 对应 `outputs/golden_baselines/...` 目录；普通 benchmark_runs 产物仍不提交。
