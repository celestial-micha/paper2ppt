# Deep Residual 四路验证记录

日期：2026-06-16

论文：

```text
test_papers/Deep Residual Learning for Image Recognition.pdf
```

本次没有复用旧 checkpoint。第一次 fresh run 因 Windows 路径过长导致 MinerU 写入 `auto/images/*.jpg` 失败；修复方式是在 fourway runner 中把输入 PDF 暂存为短名 `source.pdf`，从而把解析产物路径压到 Windows 可接受范围内。

成功 run：

```text
benchmark_runs/deep_residual_fourway_20260616_0003
```

## 四路结果

| Route | Style | Findings | High | Medium | Low |
| --- | --- | ---: | ---: | ---: | ---: |
| 01 academic audit only | academic | 207 | 23 | 62 | 122 |
| 02 golden_baseline1 scoped | golden_baseline1_from_scratch_warm_academic | 60 | 2 | 0 | 58 |
| 03 academic global repair | academic | 197 | 15 | 62 | 120 |
| 04 blind experimental loop | blind_experimental_blueprint | 97 | 28 | 0 | 69 |

## 快检结果

- 01/03 第 2 页 Contents 均包含六项：Motivation、Method、Analysis、Ablations、Results、Conclusion。
- `academic_toc_missing_canonical_sections = 0`。
- `academic_right_evidence_void = 0`。
- 02 保持 golden_baseline1 自己的 Roadmap / Deck Map 语法，没有被 academic 六项 TOC 规则污染。
- 04 保持 blind experimental 的 Route Map 语法，没有复用 original academic 或 golden_baseline1 的目录视觉。

## 已保存款式证据

Original academic：

```text
outputs/golden_baselines/original_academic_mature/DeepResidual_20260616_academic_validation_fresh_parse.pptx
outputs/golden_baselines/original_academic_mature/DeepResidual_20260616_academic_global_repair_validation.pptx
```

Golden baseline1：

```text
outputs/golden_baselines/golden_baseline1_from_scratch_warm_academic/DeepResidual_20260616_golden_baseline1_scoped_validation.pptx
```

Blind experimental：

```text
outputs/candidate_styles/blind_experimental_blueprint/DeepResidual_blind_experimental_blueprint_v2.pptx
```

## 后续问题

Deep Residual 的 academic 路线仍有较多字体、文本容量和 overlap findings。03 相比 01 有改善，但 high/medium 还没收敛到可接受状态；下一轮应把 top badcases 从 generic copy/typography/geometry 继续转成更具体、可自动修复的规则。

## 2026-07-01 补充：blind rectangular 晋升为 golden2

6 月 16 日的 `blind_experimental_blueprint` 只是早期候选。后续 Deep Residual 又进入 style-aware multistage run：

```text
benchmark_runs/deep_residual_style_aware_rescore_20260630_0001
```

在这轮中，04 route 逐步从 blind rectangular candidate 迭代到用户认可的版本：

```text
benchmark_runs/deep_residual_style_aware_rescore_20260630_0001/pptx_for_review/04_blind_rectangular_iter04_table_notes.pptx
```

最终已保存为：

```text
outputs/golden_baselines/golden_baseline2_blind_rectangular_research_board/DeepResidual_20260630_blind_rectangular_golden2_reference.pptx
```

对应 machine-readable 记录：

```text
outputs/golden_baselines/golden_baseline2_blind_rectangular_research_board/style_manifest.json
outputs/golden_baselines/golden_baseline2_blind_rectangular_research_board/PROMOTION_RECORD.zh-CN.md
```

需要注意：这个 golden2 是 human-in-the-loop 调出的 frozen reference，不是 fully autonomous style proposal 的证明。它的价值在于把人工反馈沉淀成 scoped benchmark rules，例如：

- `text_card_vertical_alignment_top_heavy`
- `image_underutilized_in_wide_panel`
- `figure_caption_not_centered_in_wide_panel`
- `table_view_label_missing`
- `table_caption_missing_or_not_centered`
- `table_underutilized_in_evidence_panel`
- `metric_improved_visual_regressed`
