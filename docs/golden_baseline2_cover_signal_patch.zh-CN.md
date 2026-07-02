# Golden Baseline2 Cover SIGNAL 修订记录

日期：2026-07-02

## 问题结论

`golden_baseline2_blind_rectangular_research_board` 首页的 `S I G N A L 1/2/3` 只有标签、没有解释文字。检查 PPTX 结构后确认：冻结源文件本身就有三个空文本框，因此这是当时生成/封版阶段留下的 cover copy 缺口，不是 six-way benchmark 后续复制 deliverables 时造成的。

## 修订方式

只做最小修订：保留 baseline2 的直角矩形 research-board 视觉语法、页数、排版骨架和 frozen-reference 身份，仅填充首页三个空白说明框。

新增文案：

```text
Signal 1: Claim-first cards expose the problem, method, and evidence path.
Signal 2: Source figures and tables stay traceable inside editable proof panels.
Signal 3: Nonvisual audit converts layout defects into scoped repair rules.
```

## 已同步文件

正式冻结源：

```text
outputs/golden_baselines/golden_baseline2_blind_rectangular_research_board/DeepResidual_20260630_blind_rectangular_golden2_reference.pptx
```

six-way route：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/routes/03_golden2_frozen_reference/slides.pptx
```

deliverables 可查看修订版：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/deliverables/03_golden_baseline2_research_board_cover_fixed.pptx
```

原 deliverables 文件 `03_golden_baseline2_research_board.pptx` 当前被 PowerPoint 进程占用，Windows 拒绝覆盖。没有强行关闭 PowerPoint，因此先保留 `cover_fixed` 副本。关闭 PowerPoint 后，可以用正式冻结源覆盖原 deliverable 文件。

## 校验结果

修订后 SHA256：

```text
7370E0507C304262F822628F5D0007416CE304ED26174A161F46D0D0BE82813C
```

修订后 nonvisual audit：

```text
finding_count=92
high=16
medium=11
low=65
```

finding count 比旧版多 1，是因为新增正文被纳入字体/容量规则统计；视觉上首页信息完整度提高。已渲染第一页 PNG 检查，三条 SIGNAL 说明正常显示，无重叠或截断。

## 对整体流程的影响

不需要大改整体流程。需要保留的流程改动只有一条：`paper2slides/benchmark/sixway.py` 的 golden2 route 应优先复制正式冻结 PPTX，而不是重新调用旧 renderer 生成相似但不完全一致的文件。

因此后续流程规则是：

- frozen reference route 可以读取自己的受保护 PPTX；
- new-style proposal / seed route 不允许读取 golden2 PPTX 当模板；
- universal benchmark 可以评估 golden2，但不能把它当作 autonomous style proposal 的证明；
- 如果 frozen source 做过人工修订，必须同步 promotion record、manifest、audit 和 run 汇总。
