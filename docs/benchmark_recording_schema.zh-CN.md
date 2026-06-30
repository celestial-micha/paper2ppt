# Benchmark 记录结构补充

日期：2026-06-16

这次补充的目标不是再造一套新 benchmark，而是把“PDF -> PPT -> benchmark 打分 -> 自动返修 -> 二次打分 -> 人工快检”这条链路记录得更适合展示、复盘和后续批量统计。

## 1. run 级别必须保留

- `manifest.json`：本次 run 的论文、参数、入口信息。
- `comparison_report.md`：四路结果总览。
- `score_curve.csv`：每条 route 每一轮的 high / medium / low finding 曲线。
- `artifact_index.csv`：每条 route 每一轮对应的 `pptx / speaker script / audit` 文件索引。
- `fourway_result.json`：程序侧汇总结果。

## 2. route 级别必须保留

- `slides.pptx`
- `speaker_script.md`
- `speaker_script_audit.json`
- `nonvisual_audit.json`
- `repair_log.json`
- `style_drift_report.json`

如果是 blind experimental route，再额外保留：

- `style_contract.json`

它的作用是明确声明：这一轮 blind route 不继承 `academic`、`golden_baseline1`、以及之前保存过的 blind candidate 的视觉语法，只复用 fresh-parse checkpoint 和 benchmark badcases。

## 3. iteration 级别必须保留

每一轮自动修正都要单独留档，而不是只保留最终版：

- `iterations/iter_XX/slides.pptx`
- `iterations/iter_XX/speaker_script.md`
- `iterations/iter_XX/speaker_script_audit.json`
- `iterations/iter_XX/nonvisual_audit.json`

这样后面做曲线图、badcase 对比、以及“自动返修前后对比页”时，证据链是完整的。

## 4. speaker script 的规则

speaker script 不应该只按论文生成一份通稿，而应该按 route 生成。

原因：

- `academic` 讲的是 key message + numbered claims。
- `golden_baseline1` 讲的是 claim + proof panel。
- `blind experimental` 讲的是 claim / evidence ledger。

同一篇论文，不同 route 的页面结构、证据节奏、强调点都不同，所以 script 也必须跟着 route 变化。

最低限度的 script audit 建议：

- script 里的 slide 数量与 PPTX 页数一致。
- script 的 slide 标题能覆盖 PPTX 里的真实标题。
- 不允许出现明显的占位语句或半截短语。
- blind route 的 script 要显式提示 presenter 指向 evidence cue。

## 5. 建议最终展示方式

做找工作展示时，建议至少准备：

- 2 篇论文的四路结果表。
- 每篇论文的 `score_curve.csv` 曲线图。
- 2 到 4 个典型 badcase 的自动返修前后对比。
- blind route 的 `style_contract.json` + 每轮 PPT 版本留档。
- 一份人工快检清单，证明最后还有 human-in-the-loop。

这样展示出来的重点就不只是“我能生成 PPT”，而是“我搭了一个可自动诊断、可自动返修、可追溯版本、可人工兜底的 benchmark 系统”。

## 6. 2026-07-01 扩展：六路 smoke 与 autonomous proposal 记录

`golden_baseline2_blind_rectangular_research_board` 封版后，下一阶段 benchmark 从四路升级为六路：

```text
01 academic frozen reference
02 golden_baseline1 frozen reference
03 golden_baseline2 frozen reference
04 autonomous style proposal A
05 autonomous style proposal B
06 autonomous style proposal C
```

这要求 run 级别新增：

- `style_proposal_policy.json`：记录 autonomous route 能读什么、不能读什么。
- `design_primitives_library.json`：记录可用抽象原语；不包含完整模板。
- `human_feedback_effort.csv`：记录人工参与程度。
- `external_artifact_eval.json`：记录与 PDF / raster / Beamer 类外部系统的可编辑性、文本抽取和溯源对比。
- `sixway_result.json`：六路汇总。

autonomous route 必须额外保留：

- `style_contract.json`
- `layout_grammar.json`
- `renderer_parameters.json`
- `novelty_report.json`
- `forbidden_reference_attestation.json`
- `design_primitives_used.json`

## 7. Rule schema v2

每条 rule 应逐步迁移到下面字段：

```json
{
  "id": "image_underutilized_in_wide_panel",
  "dimension": "component_fit",
  "severity": "medium",
  "scope": "style_aware",
  "style_scope": ["golden_baseline2_blind_rectangular_research_board"],
  "repair_mode": "auto_then_human_review",
  "confidence": 0.76,
  "human_outcome": "pending_review"
}
```

字段含义：

| 字段 | 说明 |
| --- | --- |
| `dimension` | content / evidence / layout / typography / component_fit / style / repair_risk |
| `scope` | global / style_aware / experimental / human_feedback |
| `style_scope` | 允许自动修复的 style id；空数组表示只 detect/report |
| `repair_mode` | auto / suggest / auto_then_human_review / human_gated / detect_only |
| `confidence` | 机器判断置信度 |
| `human_outcome` | pending_review / accepted / rejected / tradeoff_review / likely_overcorrection |

## 8. Human feedback effort schema

人类参与不再只写在聊天记录里，而要量化：

```json
{
  "human_feedback_turns": 3,
  "human_marked_slide_count": 6,
  "human_marked_slides": [4, 5, 6, 8, 12, 21],
  "manual_ppt_edits_by_human": 0,
  "codex_direct_renderer_edits": 3,
  "new_rules_added": 6,
  "auto_detectable_after_rule_conversion": 5,
  "auto_repairable_after_rule_conversion": 4,
  "human_outcome_counts": {
    "accepted": 2,
    "rejected": 1,
    "tradeoff_review": 1
  },
  "autonomy_level": "L2_human_feedback_guided_repair"
}
```

建议 autonomy level：

| level | 含义 |
| --- | --- |
| `L0_manual_template` | 人类手工设计模板或手工改 PPT |
| `L1_agent_renders_given_template` | 系统把内容填入给定模板 |
| `L2_human_feedback_guided_repair` | 系统渲染/修复，人类指出主要 badcase |
| `L3_benchmark_guided_multi_round_repair` | 系统依据已有规则多轮自修，人类抽检 |
| `L4_autonomous_style_proposal_and_repair` | 系统自主提出 style 并完成 bounded repair |

## 9. External artifact eval schema

为了公平比较其他系统生成的 PDF / raster deck / Beamer deck，记录：

```json
{
  "artifact_kind": "native_pptx | pdf_text | pdf_raster | beamer_pdf | image_deck",
  "page_count": 20,
  "text_extractable_page_ratio": 1.0,
  "raster_page_ratio": 0.0,
  "native_editability_score": 0.4,
  "source_asset_reuse_score": 0.2,
  "content_traceability_score": 0.3,
  "human_edit_cost_score": 0.7,
  "notes": "Text is extractable but editing requires LaTeX rather than PowerPoint."
}
```

这让 benchmark 不只比较“能不能生成”，还比较是否可编辑、可溯源、可人工修正。
