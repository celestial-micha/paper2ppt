# GPT-5 System Card 外部 PPT 项目评审与计划更新

日期：2026-07-02
论文：`test_papers/OpenAI_GPT-5_System_Card.pdf`
本轮输出目录：`benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/deliverables/`

## 1. 已补齐的 PPT 交付物

原六路 smoke 的 PPTX 已集中复制到 `deliverables/`，避免老师只看到 markdown 找不到文件：

1. `01_golden_baseline_academic.pptx`
2. `02_golden_baseline1_warm_academic.pptx`
3. `03_golden_baseline2_research_board.pptx`
4. `04_new_style_seed_scaffold.pptx`
5. `05_new_style_autonomous_a.pptx`
6. `06_new_style_autonomous_b.pptx`

新增两个外部项目参考样稿：

7. `07_ppt_master_inspired_native.pptx`
8. `08_guizang_swiss_inspired_native.pptx`

归藏风 HTML 视觉稿：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/deliverables/08_guizang_swiss_inspired_html/index.html
```

## 2. 外部项目下载与阅读状态

### `hugohe3/ppt-master`

完整 `git clone` 与 zip 下载在当前网络下多次超时，因此本轮采用 GitHub API/raw 方式拉取核心资料，保存在：

```text
external_refs/ppt-master_readonly/
```

已阅读的核心文件包括：

- `README.md`
- `README_CN.md`
- `SKILL.md`
- `why-ppt-master.md`
- `templates-architecture.md`
- contents listing: root / docs / skills / workflows / scripts

结论：本轮已经足够理解其主 pipeline 和模板思想；如果后续要直接执行它的转换脚本，还需要在网络更稳定时补一次完整 clone/cache。

### `op7418/guizang-ppt-skill`

该项目已完整浅克隆到：

```text
external_refs/guizang-ppt-skill/
```

已阅读的核心文件包括：

- `README.md`
- `SKILL.md`
- `references/layouts-swiss.md`
- `references/themes-swiss.md`
- `references/swiss-layout-lock.md`
- `references/checklist.md`
- `scripts/validate-swiss-deck.mjs`
- `assets/template-swiss.html`

本轮基于其 Swiss locked-mode 规则生成了 HTML 视觉稿，并通过其 validator：

```text
Swiss deck validation passed: 8 slide(s).
```

## 3. `ppt-master` 可借鉴之处

`ppt-master` 的核心价值不是某一种固定视觉风格，而是“从设计稿到可编辑 PPTX”的工程链路：

- 先生成 project/spec，再由 strategist 固化叙事、视觉系统和页面计划。
- 每页生成前重新读取 spec lock，降低长上下文漂移。
- 强调 SVG 作为中间表示，再转换成 PowerPoint 原生 DrawingML，最终保留可编辑对象。
- 模板拆成 brand / layout / deck 三类，可以按 segment 融合。
- 质量控制不是最后才看一眼，而是 live preview、SVG checker、post-process、export 串起来。

对 Paper2Slides 的直接启发：

- 增加 `spec_lock.md` / `style_contract.json`：把叙事、页面角色、禁用规则、字体密度和 proof object 类型先冻结。
- 增加“页面生成前重读 contract”的机制：尤其是 autonomous proposal route，避免后半段滑回 baseline 或风格漂移。
- 把新风格拆成可复用 primitives：evidence wall、metric ledger、risk stack、hierarchy diagram、system map。
- 研究原生 PPTX 后端：短期继续用当前 PPTX 生成器；中期评估 SVG-to-DrawingML 或 artifact-tool native object pipeline。

本轮 `07_ppt_master_inspired_native.pptx` 采用了这些思想做视觉试验：可编辑文本/形状、证据块、指标页、权限图、结论页，而不是单纯贴图。

## 4. `guizang-ppt-skill` 可借鉴之处

归藏项目的强项是视觉纪律和验证纪律。它的主交付是 HTML 横向滑动演示，而不是 PPTX，但里面的规则很适合转译成 Paper2Slides 的模板约束。

关键可借鉴点：

- Swiss locked-mode：正文页只能使用登记过的 S01-S22 版式，并要求每页写 `data-layout`。
- 单一 accent 色，默认 IKB blue；禁用渐变、阴影、圆角和随意装饰。
- 标题默认左上，保持网格系统，不把标题居中当作“高级感”。
- 图片槽位必须绑定 layout slot，S22 单大图有明确 21:9 规则。
- 自带 `validate-swiss-deck.mjs`，可以把风格规则变成机器 gate。

对 Paper2Slides 的直接启发：

- 新增 `layout_registry`：每个新风格必须声明可用页面类型，而不是自由拼贴。
- 新增 `style_validator`：检查标题位置、accent 数量、图片槽位、禁用组件、页脚安全区。
- 把 HTML/browser preview 当作“视觉实验室”，但最终交付仍以可编辑 PPTX 为目标。
- 给 autonomous route 增加“版式多样性”约束：7-8 页样稿至少覆盖 cover、comparison、structure diagram、metric ledger、image/evidence hero、closing。

本轮 `08_guizang_swiss_inspired_html/index.html` 是按 Swiss 规则生成的 HTML 视觉稿；`08_guizang_swiss_inspired_native.pptx` 是同一视觉语言的原生 PPTX 近似版，方便老师直接在 PowerPoint 里看效果。

## 5. 对后续计划书的调整

原来的 six-route hybrid smoke 方向仍然成立，但现在应补一条“外部模板吸收层”：

1. 保留三条 frozen references，不让它们污染新风格 route。
2. 新风格 route 增加 `external_style_brief` 输入，但不能直接复制外部项目的完整页面。
3. 每个外部 style brief 必须降维成四类机器可读资产：
   - `style_contract`
   - `layout_registry`
   - `design_primitives`
   - `validator_rules`
4. 新样稿先产出小型 8 页 visual probe，再进入完整 24 页论文 deck。
5. 对每个 probe 记录：
   - native editability
   - layout diversity
   - evidence density
   - typography risk
   - baseline similarity
   - human pick / reject / borrow notes

## 6. 下一轮建议执行顺序

1. 老师先验收 8 个 PPTX 和归藏 HTML 视觉稿。
2. 对 07 / 08 两个参考样稿标注：保留、拒绝、局部借鉴。
3. 把被接受的借鉴点写入 `style_registry.zh-CN.md` 和 machine-readable style policy。
4. 在 runner 中增加 `external_style_brief` 字段，允许 route 使用“抽象设计规则”，禁止直接读取外部完整 deck。
5. 给 autonomous proposal route 增加 layout registry 和 validator gate。
6. 再跑一轮 GPT-5 System Card 或下一篇新论文，比较是否真的提升 novelty、editability 和 human acceptance。

## 7. 本轮保守判断

`ppt-master` 值得借鉴工程 pipeline，尤其是 spec lock、模板资产分层、原生可编辑导出和预览质检。

`guizang-ppt-skill` 值得借鉴视觉纪律，尤其是 Swiss layout lock、单色系统、validator 和 HTML 预览实验场。

二者都不应被直接照搬。Paper2Slides 的目标仍是“论文理解 -> 可编辑 PPTX -> 自动 audit/repair -> human feedback registry”，外部项目应转化成模板约束、验证规则和风格原语，而不是替代现有 benchmark。
