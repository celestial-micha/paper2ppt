# 07 Seed Full Deck v10 Final 阶段报告

日期：2026-07-02

本阶段在用户授权下，从 8 页 visual probe 继续推进到完整 24 页 PPTX 草案。注意：这仍是 `prototype_only` 的完整交付草案，不代表 07 已被默认晋升为模板；`promotion_gate` 仍然要求 human feedback 后才能默认推广。

## 1. 新增代码

新增模块：

```text
paper2slides/benchmark/seed_pipeline/full_deck_renderer.py
```

新增 CLI：

```text
python -m paper2slides.benchmark seed-full-deck-render
```

公共导出新增：

```text
build_seed_full_deck_spec
render_seed_full_deck_pptx
```

该 renderer 独立于主 renderer，输入为：

- `content_inventory.json`
- `seed_template_contract.json`
- `seed_template_package_07/`
- `promotion_gate.json`

本轮使用 `--allow-blocked-prototype`，含义是允许生成 review-only 完整草案，但不解除 promotion gate 的默认晋升阻塞。

## 2. 最终 PPT 产物

最终工作目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/seed_full_deck_v10_final/
```

核心文件：

```text
slides_seed_full_v10_final.pptx
seed_full_deck_spec.json
render_trace.json
nonvisual_audit.json
universal/
  deck_ir.json
  universal_scorecard.v0.json
  checkpoint_alignment.v0.json
```

已复制到 deliverables：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/deliverables/07_seed_full_deck_v10_final.pptx
```

## 3. Render Trace

`render_trace.json` 确认：

```text
slide_count: 24
scope: seed_full_deck_prototype
native_editable_required: true
prototype_only: true
default_template_promotion_allowed: false
main_renderer_modified: false
allow_blocked_prototype: true
```

页面结构：

```text
cover: 1
agenda: 1
section divider: 4
content: 16
metric ledger: 1
closing: 1
```

## 4. 迭代收敛

本阶段从 v0 迭代到 v10，主要修复 copy fitting、header overlap、type scale 和 figure evidence。

| version | purpose | findings | high | key result |
| --- | --- | ---: | ---: | --- |
| v0 | 初版完整 deck | 116 | 17 | 能生成 24 页，但文案容量过满。 |
| v1 | 收紧文案预算 | 100 | 6 | high 下降，但仍有 overflow。 |
| v3 | 消除 high | 103 | 0 | high 清零，但 typography 仍弱。 |
| v5 | 保持 high=0 且 layout=100 | 91 | 0 | 纯 native table/text evidence 的稳态版本。 |
| v8 | 条件式 claim fitting | 63 | 0 | content / layout / copy fitting 更平衡。 |
| v10 | 加入 figure evidence 并修高风险 | 58 | 0 | 最终候选，含图片证据。 |

## 5. 最终 Nonvisual Audit

`nonvisual_audit.json` 摘要：

```text
finding_count: 58
high: 0
medium: 19
low: 39
deck_flags: deck_type_scale_under_comfort_band
```

按类型：

```text
near_text_capacity: 19
container_stack_off_balance: 2
weak_fragment_point_heading: 2
below_ideal_font_band: 12
table_support_band_off_balance: 6
table_view_label_missing: 6
table_caption_missing_or_not_centered: 6
figure_panel_aspect_mismatch: 5
```

重要解释：

- 已清零 high risk。
- 已清零 geometry_pages。
- 剩余问题主要是 medium/low 的风格和证据呈现规则。
- `deck_type_scale_under_comfort_band` 仍保留，说明还需要人类审阅 type scale 是否接受。

## 6. Universal Scorecard

最终 `universal_scorecard.v0.json`：

| dimension | score |
| --- | ---: |
| overall | 81.0 |
| editability | 100.0 |
| content_fidelity | 97.2 |
| evidence_grounding | 98.4 |
| layout_geometry | 82.0 |
| typography | 38.0 |
| visual_design | 63.7 |

解释：

- 内容覆盖和证据 grounding 已达到完整 deck 水平。
- editability 保持满分。
- layout_geometry 明显优于旧路线。
- typography 仍是主要短板，主要来自 type scale 与 table/figure label 规则。

## 7. DeckIR 摘要

最终 `deck_ir.json`：

```text
slides: 24
objects: 289
native_text_chars: 8788
pictures: 5
native tables: 6
font: Aptos
palette: #6B7280, #171717, #E24A2B, #FFFFFF, #D8D1C5
```

这说明最终 PPT 不是截图式输出，而是 native text / native table / source figure 混合的可编辑 PPTX。

## 8. Checkpoint Alignment

最终 `checkpoint_alignment.v0.json`：

| metric | value |
| --- | ---: |
| key term coverage | 0.911 |
| slide title coverage | 1.000 |
| section coverage | 1.000 |
| figure ref coverage | 1.000 |
| table ref coverage | 0.944 |
| metric ref coverage | 1.000 |
| evidence ref coverage | 0.977 |

这说明 v10 已不再是 8 页 visual probe，而是完整论文 deck 草案。

## 9. 与 Promotion Gate 的关系

虽然已经生成完整 PPTX，但 gate 状态仍应保持：

```text
renderer prototype: allowed
default template promotion: blocked
full deck expansion: generated as review-only prototype by explicit user authorization
human feedback: pending
```

换句话说：这份 PPT 可以审阅和继续沟通，但不能把 07 自动写入默认模板。下一步应由人类看最终 PPT，决定：

- 是否接受当前 editorial data-reporting 风格；
- 是否接受小字号/表格标签策略；
- 是否继续做 table/figure label polish；
- 哪些规则进入 template_gate.v1。

## 10. 下一步建议

下一轮最值得做的不是再大改 renderer，而是基于最终 PPT 做 human feedback：

1. 人工检查 cover、agenda、1 个 table slide、1 个 figure slide、metric ledger、closing。
2. 如果整体风格接受，则把 accepted traits 写回 `human_feedback_packet.json`。
3. 如果表格和 figure label 仍显粗糙，则把 medium findings 升级为 template gate v1 规则。
4. 只在用户认可 v10 视觉方向后，再考虑 full-deck renderer adapter 接入主 pipeline。
