# 07 Visual Probe Renderer Prototype v0 阶段报告

日期：2026-07-02

本阶段承接 `visual_rule_registry_07`。由于 promotion gate 明确给出：

```text
renderer_prototype_allowed: true
default_template_promotion_allowed: false
full_deck_expansion_allowed: false
```

因此本阶段只实现独立的 8 页 visual probe renderer prototype，不改主 renderer，不生成完整 24 页 deck。

## 1. 新增代码

新增模块：

```text
paper2slides/benchmark/seed_pipeline/probe_renderer.py
```

新增 CLI：

```text
python -m paper2slides.benchmark seed-probe-render
```

公共导出新增：

```text
render_visual_probe_pptx
```

输入：

- `visual_probe_spec.json`
- `seed_template_package_07/`
- 可选 `promotion_gate.json`

输出：

- native editable PPTX
- render trace JSON

该 renderer 是独立原型，不修改 `paper2slides/generator` 或现有主渲染器。

## 2. 本轮产物

输出目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/visual_probe_render_07/
```

包含：

```text
visual_probe_seed_v0.pptx
render_trace.json
nonvisual_audit.json
universal/
  deck_ir.json
  universal_scorecard.v0.json
  nonvisual_audit.json
  checkpoint_alignment.v0.json
```

`render_trace.json` 确认：

```text
slide_count: 8
scope: visual_probe_only
native_editable_required: true
full_deck_generation_allowed: false
main_renderer_modified: false
```

## 3. DeckIR 摘要

渲染后的 PPTX 转成 DeckIR 后，关键指标：

```text
slides: 8
objects: 111
native_text_chars: 2966
pictures: 0
palette: #171717, #6B7280, #E24A2B, #FFFFFF, #D8D1C5
font: Aptos
```

这说明 prototype 输出是 native shape/text 路线，不是整页截图或图片化路线。

## 4. Universal Scorecard

`universal_scorecard.v0.json` 当前结果：

| dimension | score |
| --- | ---: |
| overall | 77.4 |
| editability | 100.0 |
| content_fidelity | 57.9 |
| evidence_grounding | 73.8 |
| layout_geometry | 74.5 |
| typography | 76.4 |
| visual_design | 79.3 |

解释：

- `overall=77.4` 说明 renderer prototype 在机器可测的 editability、layout、typography、visual proxy 上已经明显可用。
- `content_fidelity=57.9` 仍不能和 full deck 直接比较，因为它只渲染 8 页 visual probe。
- 这个分数不能作为“07 已经完整成功”的证据，只能说明 spec lock -> native PPTX 的最小执行链路跑通了。

## 5. Checkpoint Alignment

当前 coverage：

| metric | value |
| --- | ---: |
| key term coverage | 0.444 |
| slide title coverage | 0.550 |
| section coverage | 0.400 |
| figure ref coverage | 0.778 |
| table ref coverage | 0.611 |
| metric ref coverage | 0.588 |
| evidence ref coverage | 0.636 |

这符合 visual probe 定位：证据对象覆盖还可以，但全论文 section/key-term 覆盖不足，不能扩展为 full deck 成功声明。

## 6. Nonvisual Audit

`nonvisual_audit.json` 摘要：

```text
finding_count: 19
high: 3
medium: 3
low: 13
deck_flags: []
```

按 type：

```text
estimated_text_overflow: 3
low_text_density: 4
near_text_capacity: 1
below_ideal_font_band: 5
metric_label_gap_too_large: 3
text_card_vertical_alignment_top_heavy: 3
```

3 个 high 都是 `estimated_text_overflow`，不是几何越界、图片不可读或 renderer 崩溃：

- slide 1 title claim 约 1.04x box capacity；
- slide 2 title claim 约 1.32x box capacity；
- 另一个 body text 约 1.33x box capacity。

因此下一轮优先级应是 copy fitting，而不是改整体布局。

## 7. 当前结论

本阶段已经验证：

```text
visual_probe_spec
 -> seed_probe_renderer
 -> native PPTX
 -> nonvisual_audit
 -> DeckIR
 -> universal scorecard
```

这条链路可以跑通，并且保持了几条关键边界：

- 不改主 renderer；
- 不生成 full deck；
- 不图片化；
- 不自动晋升 07；
- 不假装 human feedback 已完成。

## 8. 下一阶段建议

下一阶段应做 `visual_probe_render_v1_copy_fit`：

1. 只修 Top 3 high `estimated_text_overflow`。
2. 优先使用换行、标题拆分、support 文案缩短、notes 分配。
3. 不为了低密度直接缩小组件或大改版式。
4. 重新跑 nonvisual audit 和 universal scorecard。
5. 目标不是让 8 页 probe 内容覆盖 full deck，而是让 renderer prototype 在 typography/copy fitting 上稳定到无 high finding。

如果 v1 能把 high finding 清零，同时维持 editability/layout/visual proxy，才进入更实质的 template gate v1 或 full-deck renderer adapter 讨论。

## 9. v1b Copy-fit 结果

已继续做一个受控小修，不改宏观布局，只处理 v0 的 3 个 high `estimated_text_overflow`：

- cover title 增加换行和可用高度；
- content claim 区增加高度并回到舒适字号；
- metric card label 增加高度、缩小 value-label gap，并回到 12pt。

v1b 输出目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/visual_probe_render_07_v1b_copy_fit/
```

包含：

```text
visual_probe_seed_v1b_copy_fit.pptx
render_trace.json
nonvisual_audit.json
universal/
  deck_ir.json
  universal_scorecard.v0.json
  nonvisual_audit.json
  checkpoint_alignment.v0.json
```

Nonvisual audit 从 v0 到 v1b：

| metric | v0 | v1b |
| --- | ---: | ---: |
| findings | 19 | 7 |
| high | 3 | 0 |
| medium | 3 | 3 |
| low | 13 | 4 |
| deck_flags | 0 | 0 |
| typography dimension score | 80.0 | 92.0 |
| layout dimension score | 64.0 | 100.0 |

v1b 剩余 finding：

```text
low_text_density: 4
text_card_vertical_alignment_top_heavy: 3
```

这些不应该通过强行缩放组件解决。它们更适合留给 human feedback 或下一轮内容密度校准，因为 07 当前仍是 visual probe，不是完整内容 deck。

Universal scorecard v1b：

| dimension | score |
| --- | ---: |
| overall | 81.4 |
| editability | 100.0 |
| content_fidelity | 57.9 |
| evidence_grounding | 73.8 |
| layout_geometry | 82.0 |
| typography | 92.0 |
| visual_design | 83.8 |

DeckIR v1b：

```text
slides: 8
objects: 111
native_text_chars: 2966
pictures: 0
font: Aptos
```

Checkpoint alignment 未因 copy-fit 改动而变化：

```text
key_term_coverage: 0.444
slide_title_coverage: 0.550
section_coverage: 0.400
evidence_ref_coverage: 0.636
```

结论：v1b 已经达成 visual probe renderer prototype 的第一轮工程目标：

```text
native editable PPTX
high finding cleared
deck flags cleared
typography/layout improved
full deck expansion still blocked
human preference still pending
```

下一步不建议继续为了低密度自动扩大或重排组件。更好的下一步是把 v1b 作为 renderer prototype reference，等待 human feedback 后再决定哪些 low/medium 风格问题进入 template gate v1。
