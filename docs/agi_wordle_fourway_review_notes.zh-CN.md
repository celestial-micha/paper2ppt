# AGI Wordle 四路验证人工复查记录

日期：2026-06-15

本记录补充 `benchmark_runs/agi_wordle_fourway_20260615_0001`。目标是把人工快速检查发现的问题，沉淀为可复现的 benchmark 规则和回归测试，而不是只手工修一份 PPT。

## 本次人工发现

用户复查 01 `academic_audit_only` 和 03 `academic_global_repair` 后指出：第 9 页和第 13 页右半边明显空白。两页都是原 `academic` golden baseline 风格下的“左侧 claim/support + 底部全宽表格”页面，但右侧本应承载 metric 或 evidence notes。

对应 before 图：

- `D:/coding/agent_paper_to_slider/临时图片/slides/幻灯片9.JPG`
- `D:/coding/agent_paper_to_slider/临时图片/slides/幻灯片13.JPG`

这不是 `golden_baseline1` 的圆角 proof-panel 问题。02 `golden_baseline1_scoped` 和 04 `blind_experimental_loop` 在这条反馈上不需要被修改。

用户随后复查第二页 Contents，指出原 `academic` golden baseline 的成熟目录应保留六项：

```text
Motivation
Method
Analysis
Ablations
Results
Conclusion
```

AGI Wordle 的 01/03 在上一轮只渲染了 Motivation、Method、Results、Conclusion 四项，说明系统只学习了局部 badcase，没有完整保存 mHC golden baseline 的六模块目录结构。

## 根因

`paper2slides/generator/pptx_renderer.py` 的原 academic `_render_visual_or_mixed` 分支在遇到 `table + metrics + no image` 页面时，先进入底部表格渲染分支，导致后面的 metric fallback 没有机会执行。结果是表格被放到底部，右侧 evidence 区域没有任何有效对象。

旧 benchmark 只检查了 overlap、字体、文本容量、表格语法等问题，没有 style-scoped 地检查“原 academic 底部表格页的右侧证据区是否被填充”，所以漏掉了这个视觉空洞。

## 已补规则

新增 badcase：

```text
academic_right_evidence_void
academic_toc_missing_canonical_sections
```

scope：

```text
mature_academic_baseline
```

触发条件是原 academic 页面语法，而不是 baseline1 语法：

- 页面存在 `Key message` 标签；
- 存在底部全宽 native table；
- 右侧上半 evidence 区域没有 metric、note、figure 或其他有效证据对象。

对应文件：

- `benchmarks/from_scratch_human_feedback_benchmark.json`
- `paper2slides/benchmark/nonvisual_audit.py`
- `paper2slides/generator/pptx_renderer.py`
- `test_phase1_pptx.py`

`academic_toc_missing_canonical_sections` 的触发条件：

- 页面是原 `academic` Contents 语法，而不是 `golden_baseline1` 的 Roadmap；
- 缺少 Motivation、Method、Analysis、Ablations、Results、Conclusion 中任意一项；
- 尤其捕捉四项 TOC 把 Analysis/Ablations 合并进 Results 的回归。

## 已补修复

原 academic renderer 现在在底部表格页补右侧证据区：

- 若 slide spec 有 `metric_blocks` 且没有图片，右侧渲染 metric cards；
- 若没有 metric 但有文字证据，右侧渲染 compact evidence notes；
- 不改 `golden_baseline1` 的 rounded proof-panel 规则。

重跑后验证：

- 01 第 9 页右侧出现 `5.36%`、`Success rate`、`3.25`、`Avg. solved guesses`；
- 01 第 13 页右侧出现 `304`、`Gray->Yellow errors`、`256`、`Gray->Green errors`；
- 03 同样通过；
- 四路 `nonvisual_audit.json` 中 `academic_right_evidence_void` 计数均为 0。
- `benchmark_runs/agi_wordle_fourway_20260615_0003` 中 01/03 第 2 页 Contents 已恢复六项，且 `academic_toc_missing_canonical_sections` 计数为 0。

## 记录格式建议

当前 run 目录结构基本够用：

- `comparison_report.md`：四路总览、坏例摘要、人工快检清单；
- `score_curve.csv`：后续画曲线的主数据；
- `routes/*/nonvisual_audit.json`：每路每类 badcase 明细；
- `routes/*/repair_log.json`：自动修复迭代证据；
- `routes/*/slides.pptx`：人工复查对象。

本次已新增 run 级人工复查记录：

```text
benchmark_runs/agi_wordle_fourway_20260615_0001/human_review_notes.json
```

后续做 2 到 3 篇 smoke test、最终 10 篇统一展示时，建议再加两个聚合文件：

1. `benchmark_runs/index.csv`
   - 每行一篇论文、一路生成、一次迭代；
   - 字段包含 paper_id、route_id、style_id、iteration、high、medium、low、stop_reason、human_accept、artifact_path。

2. `benchmark_runs/badcase_index.csv`
   - 每行一个代表性 badcase；
   - 字段包含 paper_id、route_id、slide_page、badcase_id、severity、before_artifact、after_artifact、repair_status、human_note。

这样最终可以直接展示：

- PDF 到 PPT 的完整链路；
- benchmark 打分曲线；
- 自动发现问题和自动返修前后对比；
- 2 篇到 10 篇论文的结果表；
- 代表性 badcase；
- 人工快速检查如何回灌 benchmark。
