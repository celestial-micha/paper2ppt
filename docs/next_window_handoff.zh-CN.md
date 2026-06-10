# 新窗口交接说明 V2

本文档是给下一次 Codex 窗口的启动手册。核心目的：避免新窗口误以为下一步还是继续做 `academic` 换皮模板，而是要接住 **from-scratch template experiment**。

## 新窗口请直接发送这段话

```text
codex老师，我们继续做 Paper2Slides-main / paper2ppt。请先阅读：

1. docs/benchmark_plan.zh-CN.md
2. docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
3. docs/next_window_handoff.zh-CN.md
4. docs/agent_workflow.md
5. README.zh-CN.md

请先不要写代码，先规划。

现在的目标已经更新：

1. `academic` 是 golden baseline，必须保护，不要重构。
2. `academic_warm`、`editorial`、`editorial_mono`、`data_report` 是已经筛出来的 baseline companion styles。它们好看，要保留，但它们太像 golden baseline，不是下一步要继续创造的新模板。
3. 下一步不是继续调颜色或 preset，而是做 from-scratch template experiment。
4. from-scratch 的意思不是重新解析一切，而是可以复用 Kimi K2 已解析内容；但不能复用 golden baseline 的视觉骨架。
5. 我们要从 content inventory 开始，先做无审美但内容完整的草稿，再重新设计章节、目录、slide role、claim、proof object、视觉系统，最后用 benchmark 自动检测和迭代。
6. benchmark 不只检测是否出错，还要检测内容是否完整、排版是否清楚、审美是否好、以及新模板是否过度像 golden baseline。
7. 每轮我给你的人工反馈，都要被整理成可自动检测、可自动修复或可回归的 benchmark rule。

请你先输出一个详细执行规划，不要改代码。规划要包括：

- content_inventory.json 的 schema。
- 无审美草稿 PPT/spec 的生成方式。
- slide role / proof object 的定义。
- reliability/content/layout/aesthetic/novelty 五类评分如何做第一版规则型实现。
- 如何检测新模板是不是 golden baseline 换皮。
- 如何把人工反馈转成 badcase rule。
- 第一轮用 Kimi_K2_Technical_Report.pdf 做 from-scratch 实验的步骤。
- 哪些步骤可以复用已有 checkpoint，哪些情况才需要重新调用大模型。

模型路由：
- 文本：deepseek-v4-flash，base_url=https://api.deepseek.com。
- 图片/多模态：gpt-5-mini，base_url=https://api.shunyu.tech/v1。
- 不要把 DeepSeek 用于 image_url 多模态输入。
- 不要打印或提交 API key。

git 注意：
- paper2slides/.env、outputs/、benchmark_runs/、test_papers/ 不要提交。
- 改代码后跑 python -m unittest test_phase1_pptx.py。
```

## 新窗口的第一句话应该确认什么

新窗口 Codex 应先复述下面三点：

1. 当前不是继续打磨 `academic_warm/editorial/editorial_mono/data_report`。
2. 当前是要规划一个不模仿 golden baseline 的 from-scratch 新模板实验。
3. 第一轮先规划 schema、评分、迭代规则，不直接写代码。

如果新窗口没有复述这三点，说明它还没接住任务。

## 当前项目状态

工作目录：

```text
D:\coding\agent_paper_to_slider\Paper2Slides-main
```

当前 git checkpoint：

```text
branch: codex/from-scratch-benchmark-plan
remote: origin/codex/from-scratch-benchmark-plan
commit: ba94020 docs: clarify from-scratch benchmark plan
```

说明：

- 这个 commit 已经 push 到 GitHub 远端分支。
- 本地 `main` 也暂时指向同一个 commit，但远端 `origin/main` 还停在上一个提交。
- 当前还有 companion styles 相关代码改动未提交，包括 `paper2slides/generator/style_presets.py` 和若干 renderer/pipeline 文件。新窗口第一轮只做规划时，不要误以为这些代码已经进入远端文档 commit。
- 后续如果要保存 companion styles 代码，建议单独测试并单独 commit。

成熟模板：

```text
academic
```

保留的 companion styles：

```text
academic_warm
editorial
editorial_mono
data_report
```

这些 companion styles 的定位：

- 好看。
- 可以保留。
- 可以和 `academic` 一起做 mature suite 回归。
- 但不是 from-scratch 新模板。

当前 benchmark 数据集：

```text
ai20
```

Kimi K2 已跑通：

```text
test_papers/Kimi_K2_Technical_Report.pdf
```

golden baseline evidence：

```text
benchmark_runs/ai20_20260607_005847/aggregate_report.md
outputs/Kimi_K2_Technical_Report/paper/fast/slides_academic_medium_24slides/20260607_010126/slides.pptx
```

## 为什么要这样做

我们发现：只靠 `style_presets.py`、palette、header、key message、metric card、少量 renderer 分支，很容易得到好看的 companion styles，但它们仍然像 golden baseline。

用户真正想要的是：

```text
复用论文解析结果
但不复用 baseline 页面骨架
从内容库存开始
一步步做出全新视觉系统
并把每轮问题变成 benchmark rule
最后让 agent workflow 能自动检查和迭代
```

## 新窗口第一轮不要做什么

不要：

- 不要继续做新的换色模板。
- 不要直接改 `pptx_renderer.py`。
- 不要上来跑 Kimi K2 生成。
- 不要跑 ai20 全量。
- 不要把 `academic_warm/editorial/editorial_mono/data_report` 当作新模板。
- 不要重构 `academic`。
- 不要调用视觉模型做全量 judge。

## 新窗口第一轮应该做什么

只做规划，输出以下内容：

1. `content_inventory.json` schema。
2. rough draft spec schema。
3. slide role taxonomy。
4. proof object taxonomy。
5. 第一版规则型评分设计：
   - `reliability_score`
   - `content_score`
   - `visual_layout_score`
   - `aesthetic_score`
   - `novelty_score`
6. baseline similarity 检测规则。
7. 人工反馈到 benchmark rule 的格式。
8. 第一轮 Kimi K2 from-scratch 实验步骤。
9. 后续代码实现顺序。

## 后续如果用户确认规划

再进入代码实现，建议顺序：

1. 新增 content inventory 生成器。
2. 新增 rough draft spec 生成器。
3. 新增 content quality / novelty scoring。
4. 新增 iteration report。
5. 用 Kimi K2 单篇生成第一版 from-scratch 草稿。
6. 用户反馈。
7. 把反馈写成 benchmark rules。

## 测试命令

改代码后运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
C:\Users\81001\.conda\envs\paper2slides\python.exe -m unittest test_phase1_pptx.py
```

## 文件提交注意

不要提交：

```text
paper2slides/.env
outputs/
benchmark_runs/
test_papers/
```

不要打印、复制或提交任何 API key。
