# 新窗口交接说明

如果新开 Codex 窗口继续做 paper2ppt，请先把下面这段发给 Codex。

## 推荐发送给 Codex 的消息

```text
codex老师，我们继续做 Paper2Slides-main / paper2ppt 项目。请先阅读：

1. docs/benchmark_plan.zh-CN.md
2. docs/multistyle_aesthetic_benchmark_plan.zh-CN.md
3. docs/agent_workflow.md
4. README.zh-CN.md

当前目标不是重构已经很好看的 academic 模板，而是保护它作为 golden baseline，然后新增多模板 benchmark 和审美评分体系。

请优先做下一阶段第一步：
- 新增 style preset 层，建议从 paper2slides/generator/style_presets.py 开始。
- 保留 academic/current 模板行为，不破坏现有 Kimi K2 成功结果。
- 先实现 editorial 和 systems 两个新模板。
- 扩展 benchmark，让同一篇论文能跑 academic/editorial/systems，并输出 style leaderboard。
- 新增第一版规则型 aesthetic/content score，不要一开始就大量调用视觉模型。
- 用 Kimi_K2_Technical_Report.pdf 从 --from-stage generate 跑单篇多模板验证。

注意模型路由：
- 文本调用：deepseek-v4-flash，base_url=https://api.deepseek.com。
- 图片/多模态调用：gpt-5-mini，base_url=https://api.shunyu.tech/v1。
- 不要把 DeepSeek 用于 image_url 多模态输入。
- 不要打印或提交 API key。

注意 git：
- paper2slides/.env、outputs/、benchmark_runs/、test_papers/ 不要提交。
- 改完后先跑 python -m unittest test_phase1_pptx.py。
```

## 当前项目事实

- 工作目录：`D:\coding\agent_paper_to_slider\Paper2Slides-main`
- 当前成熟模板：`academic`
- 当前 benchmark 数据集：`ai20`，共 20 篇 PDF，位于 `test_papers/`
- Kimi K2 单篇已经跑通：
  - 报告：`benchmark_runs/ai20_20260607_005847/aggregate_report.md`
  - PPT：`outputs/Kimi_K2_Technical_Report/paper/fast/slides_academic_medium_24slides/20260607_010126/slides.pptx`
  - 结果：1/1 通过，23 页，2 个 warning
- 测试命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
C:\Users\81001\.conda\envs\paper2slides\python.exe -m unittest test_phase1_pptx.py
```

## 下一阶段实现顺序

### Step 1：保护 baseline

目标：
- 给现有 `academic` 行为增加回归测试或快照式验证。
- 确认新增模板不会改变现有 academic 渲染。

验收：
- `test_phase1_pptx.py` 通过。
- Kimi K2 的 `academic` 从 `--from-stage generate` 能继续通过。

### Step 2：style preset 层

建议新增：

```text
paper2slides/generator/style_presets.py
```

至少包含：
- `academic`
- `editorial`
- `systems`

每个 preset 应包含：
- palette
- typography
- margins
- title block policy
- section divider policy
- metric card policy
- visual/table layout policy

### Step 3：renderer 分派

改造：

```text
paper2slides/generator/pptx_renderer.py
```

原则：
- 先让不同模板共享 slide schema。
- 不让 LLM 直接控制颜色和坐标。
- 由 preset 控制视觉系统。
- academic 逻辑尽量保持不变。

### Step 4：benchmark 多模板汇总

改造：

```text
paper2slides/benchmark/runner.py
```

目标：
- 支持多 style 输出 style leaderboard。
- 汇总每个 style 的成功率、warning rate、平均耗时。
- 后续加入 content / visual / aesthetic / overall 分数。

### Step 5：第一版审美和内容评分

建议新增：

```text
paper2slides/benchmark/aesthetic.py
paper2slides/benchmark/content_quality.py
paper2slides/benchmark/style_report.py
```

第一版只做规则评分：
- 不需要先调用视觉模型。
- 从 PPTX 元素、slide spec 和 QA JSON 中提取指标。
- 输出可复现的分数。

### Step 6：Kimi 单篇多模板验证

推荐命令形态：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic,editorial,systems --slides 24 --start-index 17 --limit 1 --from-stage generate
```

如果新模板需要重新规划内容结构，再改用：

```powershell
C:\Users\81001\.conda\envs\paper2slides\python.exe -m paper2slides.benchmark.runner run --set ai20 --styles academic,editorial,systems --slides 24 --start-index 17 --limit 1 --from-stage plan
```

## 面试叙事要点

可以这样讲：

> 我先把一个成熟模板作为 golden baseline，避免为了探索新风格破坏已经稳定的能力。然后我把模板扩展成多风格系统，并用同一批论文做 benchmark。评估不只看能不能生成，还看内容组织、视觉排版和审美质量。每次迭代先看 benchmark 报告里的主要 badcase，再有针对性地修 renderer、layout preset 或 repair rule，最后用同一组论文回归，形成 pass rate、warning rate 和审美分数的提升曲线。

## 不要做的事

- 不要提交 `paper2slides/.env`。
- 不要提交 `outputs/`、`benchmark_runs/`、`test_papers/`。
- 不要把 API key 打印到日志、README 或报告里。
- 不要把 DeepSeek 文本模型用于图片输入。
- 不要为了新模板重构掉当前 `academic` baseline。
- 不要一开始就跑 ai20 全量多模板，先用 Kimi 单篇和 4 篇小集合试。

