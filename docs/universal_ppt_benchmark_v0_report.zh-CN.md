# Universal PPT Benchmark v0 报告

日期：2026-07-02

本轮目标不是改 renderer，而是验证同一套 DeckIR / scorecard 能否解释多来源 PPTX。已新增：

- `paper2slides/benchmark/universal/deck_ir.py`
- `paper2slides/benchmark/universal/pptx_intake.py`
- CLI：`python -m paper2slides.benchmark universal-pptx-intake`

## 1. 本轮产物

本地运行目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/universal/
```

第二轮补充了 checkpoint-aware batch runner：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/universal_batch_v0_1/
```

该目录包含：

- `manifest.json`
- `universal_scorecards.csv`
- `universal_benchmark_report.md`
- 每个 deck 的 `deck_ir.json`、`universal_scorecard.v0.json`、`checkpoint_alignment.v0.json`

三类样本均已转成 `deck_ir.json`：

| deck | DeckIR | scorecard |
| --- | --- | --- |
| academic frozen baseline | `universal/01_academic_frozen_reference/deck_ir.json` | `universal/01_academic_frozen_reference/universal_scorecard.v0.json` |
| historical 06 autonomous B | `universal/06_autonomous_style_proposal_b/deck_ir.json` | `universal/06_autonomous_style_proposal_b/universal_scorecard.v0.json` |
| 07 ppt-master-inspired native | `universal/07_ppt_master_inspired_native/deck_ir.json` | `universal/07_ppt_master_inspired_native/universal_scorecard.v0.json` |

## 2. Universal Scorecard v0 Schema

Schema 由 `paper2slides/benchmark/universal/deck_ir.py` 中的 `universal_scorecard_schema()` 给出。核心结构：

```json
{
  "schema_version": "universal_scorecard.v0",
  "source": {},
  "deck_summary": {},
  "dimension_order": [
    "editability",
    "content_fidelity",
    "narrative_structure",
    "evidence_grounding",
    "layout_geometry",
    "typography",
    "visual_design",
    "repairability",
    "human_preference"
  ],
  "dimensions": {
    "editability": {
      "score": 0,
      "confidence": 0.0,
      "status": "auto",
      "signals": {},
      "notes": ""
    }
  },
  "overall": {},
  "findings": [],
  "calibration_notes": {}
}
```

v0 的原则：

- `editability`、`layout_geometry`、`typography` 优先复用 PPTX 元数据和 `nonvisual_audit`，可自动评分。
- `content_fidelity` 和 `evidence_grounding` 先给 proxy signal，后续接 paper checkpoint alignment 后再升级为强评分。
- `visual_design` 只给 rhythm、palette、density 等可解释 proxy，必须经 human feedback 校准。
- `human_preference` 不自动打分，只记录接受、拒绝、可借鉴 trait。

v0.1 增加了 checkpoint alignment：

- 从 `checkpoint_summary.json`、`checkpoint_plan.json`、`checkpoint_slide_spec.json` 抽取 key terms、slide titles、sections、figure/table/metric refs。
- 用 DeckIR 中的 native text 做覆盖率匹配，输出 `checkpoint_alignment.v0.json`。
- `content_fidelity` 升级为 key term / title / section coverage。
- `evidence_grounding` 升级为 proof-object metadata + checkpoint evidence ref coverage。

## 3. 三类 Deck 的 v0 结果

| deck | slides | native text chars | raster ratio | overall | editability | layout | typography | visual proxy | repairability |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| academic frozen | 21 | 7843 | 0.030 | 58.8 | 100.0 | 5.0 | 13.2 | 85.3 | 50.0 |
| historical 06 | 23 | 9509 | 0.031 | 57.2 | 100.0 | 37.0 | 6.0 | 62.1 | 56.2 |
| 07 ppt-master-inspired | 8 | 1794 | 0.000 | 67.9 | 100.0 | 57.0 | 66.8 | 74.1 | n/a |

注意：07 是 8 页 visual/reference probe，不是完整 24 页论文 deck，所以它的 content fidelity proxy 不能和 21/23 页完整 deck 直接等价比较。

## 3.1 Checkpoint-aware Batch v0.1 结果

| deck | overall | content fidelity | evidence grounding | key terms | slide titles | sections | evidence refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| academic frozen | 64.8 | 97.9 | 93.8 | 0.933 | 1.000 | 1.000 | 0.909 |
| historical 06 | 63.9 | 93.2 | 90.9 | 0.900 | 1.000 | 0.800 | 0.864 |
| 07 ppt-master-inspired | 66.3 | 36.7 | 64.0 | 0.289 | 0.250 | 0.000 | 0.273 |

这个结果比 v0 更清楚：

- academic 和 06 是完整内容 deck，所以 checkpoint coverage 高。
- 07 是 visual probe，不应该被解释为完整 paper coverage；它的 `content_fidelity=36.7` 是合理的低分。
- 即使内容覆盖低，07 的 `typography=66.8`、`layout=57.0`、`visual proxy=74.1` 仍能说明它是更强的 seed-template 方向。
- 这避免了旧 benchmark 的一个误区：把“漂亮的小样”误判成“完整论文 deck”，也避免把“内容完整但视觉卡住”的 06 误判成视觉成功。

## 4. 为什么 07 更好

DeckIR/scorecard 给出的解释和人工观感一致：

- 原生可编辑性保持满分：`raster_area_ratio = 0.000`，native shape/text 为主，不是整页截图。
- typography 明显更健康：07 的 typography score 是 `66.8`，而 academic 是 `13.2`，06 是 `6.0`。07 没有触发 `low_font_size` 和 `below_ideal_font_band`，主要剩余问题是 `near_text_capacity`、少量 `estimated_text_overflow` 和 `shape_overlap_risk`。
- layout 更像强初稿：07 的 layout score 是 `57.0`，高于 06 的 `37.0` 和 academic 的 `5.0`。DeckIR 没发现 safe-area violation，平均 occupancy 为 `0.329`，更接近 probe deck 的留白节奏。
- rhythm diversity 更好：07 的 8 页全部形成不同 layout signature，`rhythm_diversity = 1.0`；06 为 `0.391`，说明 06 更容易陷入重复页面语法。
- evidence 视觉语言更清楚：07 有 `14` 个 caption candidate、`11` 个 source-like text signal，虽然没有 native table/picture，但它用 native evidence blocks、指标块和编辑型形状表达 proof object。

所以 07 的价值不只是“好看”，而是展示了 seed-template 应该先规划页面角色、证据块、指标页和节奏，再扩展到 full deck。

## 5. 为什么 06 有潜力但 plateau

06 的潜力：

- 它是完整 deck：23 页、`9509` native text chars、`1501` native words。
- 可编辑性也是满分，`raster_area_ratio = 0.031`，仍是 native PPTX 路线。
- layout 相比 academic 更少安全区问题：DeckIR safe-area violation 为 `0`。
- repair log 证明 bounded repair 有效果：total findings `136 -> 112 -> 112`，low severity `76 -> 52 -> 52`。

06 卡住的原因：

- 高中风险没有被真正消化：high `26 -> 25 -> 25`，medium `34 -> 35 -> 35`。
- typography 仍是 blocker：最终仍有 `40` 个 `low_font_size`、`20` 个 `estimated_text_overflow`、`16` 个 `below_ideal_font_band`，并触发 `deck_type_scale_under_comfort_band`。
- style/structure 不是靠局部 copy repair 能解决：06 的 visual proxy 只有 `62.1`，layout signature diversity `0.391`，并保留 `container_stack_off_balance`、`figure_panel_aspect_mismatch`、`table_view_label_missing` 等问题。
- 因此 06 适合作为“有潜力但需要 template-level gate”的旧路线对照，不适合作为继续 page-level repair 的唯一主线。

结论：06 不是失败样本，它是说明 benchmark 价值的样本。它证明局部 repair 能压低低风险文本问题，但不能替代 seed strategist、spec lock 和 template-level repair。

## 6. 旧 Nonvisual Audit 仍适用的规则

这些规则仍然是 universal benchmark 的稳定基座，因为它们只依赖 PPTX metadata，不依赖 Paper2Slides 内部 route：

- 原生可编辑性：native text/shape/table/chart count、raster area ratio、picture count。
- 几何正确性：`shape_overlap_risk`、`text_exceeds_container_bounds`、safe-area / bounds、occupancy。
- 字体与文本容量：`low_font_size`、`below_ideal_font_band`、`estimated_text_overflow`、`near_text_capacity`。
- 图表和证据对象基础规则：table bounds、table readability、picture aspect distortion、caption/source-like signal。
- repair 记录规则：finding delta、high/medium/low delta、new findings、plateau stop reason。

这些规则可以直接评 Paper2Slides、ppt-master 导出的 PPTX、人工 PPTX 或其他生成器的 native PPTX。

## 7. 需要 Human Feedback 校准的视觉规则

以下规则不能在 v0 里假装自动审美正确，只能先作为 proxy 或 human-gated finding：

- `visual_focus_missing`：焦点是否清楚需要人类确认任务语境。
- `rhythm_monotony`：重复有时是纪律，有时是乏味，需要按 deck 类型校准。
- `palette_noise` / `contrast_weakness`：可用元数据先估计，但最终要看阅读舒适度。
- `underdesigned_layout` / `overdecorated_layout`：这类审美判断必须由 accepted/rejected 样本沉淀。
- `style_inconsistency`：不同风格的允许变化幅度不同，需要 style contract。
- `density_mismatch`：07 的留白是有意识的 probe 节奏，不能被粗暴判成低密度。
- style-scoped rules：如 `metric_label_gap_too_large`、`container_stack_off_balance`、`figure_panel_aspect_mismatch`，需要先判断当前 deck 是否属于对应 style grammar。

下一步应把用户对 07/06/baseline 的偏好写成 human feedback packet，再升级到 visual rule registry 和 template gate。

## 8. 下一步建议

1. 保持 renderer 不动，先把 `universal-pptx-intake` 接入一个小 runner，能批量处理任意 PPTX。
2. 为 07 提炼 seed-template package：`design_spec.md`、`spec_lock.json`、`layout_registry.json`、`validator_rules.json`。
3. 把 06 的 plateau 条件前移到 template gate：如果 probe 已触发 deck-level type scale、rhythm 或 evidence layout blocker，就不要扩展到 full deck。
4. 继续校准 `visual_design`：把 human preference packet 转成 style trait registry 和 template gate rules。
