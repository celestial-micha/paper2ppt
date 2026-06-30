# Deep Residual 语义修复补记

日期：2026-06-16

这份补记专门记录《Deep Residual Learning for Image Recognition》在 original academic route 上暴露出的两类新 badcase。它们和之前已经修掉的 `academic_toc_missing_canonical_sections`、`academic_right_evidence_void` 不一样，属于“内容语义已经坏了，但旧 benchmark 还没抓住”的问题。

## 新 badcase 1：weak_fragment_point_heading

表现：

- 页面标题或编号点标题是半截短语。
- 典型例子：
  - `The paper addresses the problem of`
  - `Its goal is to make it`
  - `In short`

问题本质：

- LLM 产出了句子前缀。
- 旧版 point-claim 规范化逻辑把这些前缀直接当成了标题，没有继续修成完整观点。

这次修复：

- 在 `text_pptx_workflow.py` 里加入弱标题判定。
- 遇到 boilerplate prefix、弱结尾词、括号不闭合等情况时，不再直接保留原 claim。
- 改为从 detail / takeaway / source text 里重建完整 idea phrase。

## 新 badcase 2：spurious_generic_metric_card

表现：

- 右侧 metric card 出现 `10 / Accuracy` 这种看起来像指标、实际没有意义的卡片。

问题本质：

- 旧版 metric extraction 把 `CIFAR-10`、`ResNet-50` 这类数据集或模型名字里的数字误识别成 KPI。
- 再结合上下文里出现的 `accuracy` 词，错误生成泛化标签。

这次修复：

- metric extraction 不再接受数据集 / 模型命名里的数字。
- 小整数 bare value 如果只有 `Accuracy / Score / Rating / Key metric` 这类泛化标签，会被直接过滤。
- nonvisual audit 新增同名 badcase，用于回放旧 PPT 时也能把这个问题报出来。

## 记录层更新

为了让这类问题之后能更直观看到，记录结构也一起补强：

- 每条 route 保存 `speaker_script.md` 和 `speaker_script_audit.json`
- 每轮 blind iteration 也保存 script 与 audit
- run 根目录新增 `artifact_index.csv`
- blind route 新增 `style_contract.json`

对应说明见：

- [benchmark_recording_schema.zh-CN.md](/D:/coding/agent_paper_to_slider/Paper2Slides-main/docs/benchmark_recording_schema.zh-CN.md)
