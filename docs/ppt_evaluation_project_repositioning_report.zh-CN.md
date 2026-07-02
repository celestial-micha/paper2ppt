# PPT 评测主线项目定位复核报告

日期：2026-07-02

## 1. 本轮复核结论

项目对外不应再被描述为单纯的“论文转 PPT 生成器”。更准确的定位是：

```text
PPTX 质量检测评估 Benchmark + 返修闭环，
同时包含论文转原生 PPTX 生成器作为候选产物来源。
```

这样更贴合简历中的表述：

- 大模型数据与评测；
- Agent Benchmark / 评测闭环；
- Badcase 分析；
- human-in-the-loop 评测闭环；
- 版本对比和可追溯评测。

## 2. README 应该传达什么

README 第一屏需要先回答“这个项目评什么”，再回答“它怎么生成 PPT”。

当前 README 已调整为：

1. 先说明项目是 PPTX evaluation benchmark and repair-loop；
2. 展示 original academic、golden_baseline1、golden_baseline2 的视觉参考；
3. 明确 benchmark 检测维度：
   - editability；
   - content alignment；
   - evidence grounding；
   - layout geometry；
   - typography / copy fitting；
   - style drift / repair risk；
   - human feedback calibration。
4. 将 `Quick Evaluation Run` 放在 `Generate A Candidate Deck` 之前；
5. 把当前能力拆成 `Current Evaluation Capabilities` 和 `Generation Capabilities`。

## 3. 计划文档应该怎么读

项目文档现在分成三类。

### 3.1 最新主线

这些文档代表当前执行方向：

```text
docs/ppt_master_universal_benchmark_upgrade_plan.zh-CN.md
docs/ppt_master_seed_pipeline_integration_plan.zh-CN.md
docs/agent_workflow.md
docs/universal_ppt_benchmark_v0_report.zh-CN.md
docs/three_seed_styles_openai_gpt5_report.zh-CN.md
```

主线不是“生成更多风格”，而是：

```text
任意 PPTX -> DeckIR -> universal scorecard -> repair log / human feedback -> template gate
```

### 3.2 历史路线与对照

这些文档保留历史价值，但不再作为主线：

```text
docs/autonomous_style_proposal_benchmark_plan.zh-CN.md
docs/benchmark_plan.zh-CN.md
docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
docs/from_scratch_benchmark_final_synthesis.zh-CN.md
```

它们说明项目如何从历史 QA 汇总、from-scratch style、six-way smoke 走到 universal benchmark。后续使用时，应重点提取 badcase、repair profile、style isolation 和 human feedback 经验，而不是继续沿用旧 04/05/06 作为默认初稿 pipeline。

### 3.3 Registry / Handoff / 修订记录

这些文档负责防止上下文丢失：

```text
docs/style_registry.zh-CN.md
docs/next_window_handoff.zh-CN.md
docs/golden_baseline2_cover_signal_patch.zh-CN.md
```

它们记录 frozen references、README 预览资产、baseline2 cover SIGNAL 修订，以及下一阶段不应重复完成的工作。

## 4. README 图片资产

新增 README 首页图：

```text
docs/assets/readme/golden_baseline1_warm_academic_montage.jpg
docs/assets/readme/golden_baseline2_blind_rectangular_montage.jpg
```

图片来源：

- golden_baseline1：`幻灯片1`、`幻灯片2`、`幻灯片4`、`幻灯片14`；
- golden_baseline2：`幻灯片1`、`幻灯片2`、`幻灯片6`、`幻灯片24`。

这两张图不是为了“展示作品集”，而是让读者一眼看到 benchmark 的 frozen references 有不同视觉语法，后续 route 需要被跨风格评测。

## 5. 下一阶段建议

1. 用人工 PPTX、ppt-master 输出、Paper2Slides 输出和 frozen baselines 继续压测 `universal-pptx-intake`。
2. 把 `human_feedback_packet`、`visual_rule_registry` 和 `template_gate` 接成可追溯的晋升决策链。
3. 给三款 seed style 设计最小偏好标注表：accepted / rejected / borrowable traits。
4. 把 scorecard 中仍需主观校准的视觉项明确标为 `human_preference_pending`，不要伪装成纯自动判断。
5. 继续保留 native PPTX、parse-once checkpoint、repair log 和 frozen reference，不回到截图式展示。
