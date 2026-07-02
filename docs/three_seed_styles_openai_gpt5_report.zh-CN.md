# OpenAI GPT-5 System Card 三款 PPT-master Seed Style 阶段报告

日期：2026-07-02

本阶段按新的方向推进：不再把 `04_new_style_seed_scaffold.pptx`、`05_new_style_autonomous_a.pptx`、`06_new_style_autonomous_b.pptx` 作为初步款式生成主线，而是把 `07_seed_full_deck_v10_final.pptx` 视为 pptx-master seed pipeline 的第一款式，并在同一套 pipeline 内增加两个 style variant。

## 1. 产物

三款 PPTX 都已复制到：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/deliverables/
```

| 款式 | 文件 | 风格定位 |
| --- | --- | --- |
| A | `07_seed_full_deck_v10_final.pptx` | editorial data report，温暖论文报告风 |
| B | `08_seed_full_deck_blueprint_v1.pptx` | blueprint system map，系统蓝图/工程图风 |
| C | `09_seed_full_deck_console_v1.pptx` | dark evidence console，暗色证据控制台风 |

对应工作目录：

```text
seed_full_deck_v10_final/
seed_full_deck_style_b_blueprint_v1/
seed_full_deck_style_c_console_v1/
```

每个目录均包含：

```text
seed_full_deck_spec.json
render_trace.json
universal/deck_ir.json
universal/universal_scorecard.v0.json
universal/nonvisual_audit.json
universal/checkpoint_alignment.v0.json
```

## 2. Pipeline 变化

新增 `--style-variant` 到：

```text
python -m paper2slides.benchmark seed-full-deck-render
```

当前支持：

```text
editorial_data_report
blueprint_system_map
dark_evidence_console
```

这不是回到旧 04/05/06 的自主提案路线。三款均复用同一套：

```text
parse-once checkpoint
-> content_inventory.json
-> seed_template_contract.json
-> seed_template_package_07
-> spec_lock / template_gate / promotion_gate
-> seed_full_deck_renderer
-> universal DeckIR + nonvisual audit + scorecard
```

第一轮只参数化 seed style，没有大改 renderer，也没有改变论文解析、内容选择、proof object 选择和主 benchmark 结构。

## 3. Universal Benchmark 摘要

批量 benchmark 输出：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/universal_seed_styles_v1/
```

核心 CSV：

```text
universal_seed_styles_v1/universal_scorecards.csv
```

| deck | slides | native chars | overall | editability | content | narrative | evidence | layout | typography | visual |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 07 editorial | 24 | 8788 | 81.0 | 100.0 | 97.2 | 87.5 | 98.4 | 82.0 | 38.0 | 63.7 |
| 08 blueprint | 24 | 8719 | 81.0 | 100.0 | 97.2 | 87.5 | 98.4 | 82.0 | 38.0 | 63.7 |
| 09 console | 24 | 8732 | 81.0 | 100.0 | 97.2 | 87.5 | 98.4 | 82.0 | 38.0 | 63.7 |

三款 checkpoint alignment 相同：

```text
key_term_coverage: 0.911
slide_title_coverage: 1.000
section_coverage: 1.000
evidence_ref_coverage: 0.977
```

nonvisual audit 均为：

```text
finding_count: 58
high: 0
medium: 19
low: 39
deck_flags: deck_type_scale_under_comfort_band
```

## 4. 视觉 QA

已通过 artifact-tool 将三款 PPTX 渲染为 PNG，每款 24 页：

```text
deliverables/qa_seed_styles/07_seed_full_deck_v10_final/
deliverables/qa_seed_styles/08_seed_full_deck_blueprint_v1/
deliverables/qa_seed_styles/09_seed_full_deck_console_v1/
```

已生成 montage：

```text
deliverables/qa_seed_styles/07_seed_full_deck_v10_final_montage.png
deliverables/qa_seed_styles/08_seed_full_deck_blueprint_v1_montage.png
deliverables/qa_seed_styles/09_seed_full_deck_console_v1_montage.png
```

抽检结果：

- 07：保持 v10 的温暖 editorial/report 风格，整体最稳。
- 08：blueprint 网格强化了系统图/工程图语义，风格差异明显；网格偏强，后续需要 human feedback 判断是否保留或降噪。
- 09：暗色 console 对 safety/evidence 主题贴合，native table 和 source figure 在抽检页可读；后续需要 human feedback 判断暗色是否适合作为通用默认候选。

## 5. 结论

现在每篇论文的初步款式 pipeline 可以从“单一 07”升级为“三款 seed styles”：

1. `editorial_data_report` 作为稳态基线。
2. `blueprint_system_map` 作为结构化/系统论文候选。
3. `dark_evidence_console` 作为安全评测、系统卡、操作信号类论文候选。

旧 04/05/06 仍可作为历史对照，但不再作为主线初步款式生成方式。下一步应让用户直接比较三份 PPTX 的偏好，再把 accepted / rejected / borrowable traits 写回 human feedback packet 和 style gate。
