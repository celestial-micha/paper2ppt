# PPT Master 融合与通用 PPT Benchmark 升级计划书

日期：2026-07-02
目标项目：`D:\coding\agent_paper_to_slider\Paper2Slides-main`

## 0. 一句话目标

把 Paper2Slides 从“能生成并评测自己几套模板的论文转 PPT 系统”，升级为：

```text
能解析论文 -> 生成可编辑 PPTX -> 生成强初稿模板 -> 评测多来源 PPT -> 进行模板级与页面级返修 -> 沉淀 human feedback 的通用 PPT Benchmark 系统
```

这不是抛开 Paper2Slides 去追随 `ppt-master`。正确方向是：

```text
保留 Paper2Slides 的 parse-once / native PPTX / audit-repair / benchmark 资产
吸收 ppt-master 的 strategist / spec_lock / seed-template / quality-gate 思想
最终让 benchmark 能评 Paper2Slides、ppt-master、人工 PPT、其他 Agent PPT
```

### 0.1 二次复核后的硬约束

这次升级最容易犯的错，是一上来就把 `ppt-master` 当成“更好看的模板库”，然后直接改 renderer。第二次复核后，路线要更收束：

1. 第一优先级是评测泛化，不是视觉仿制。
   - 先让同一套 benchmark 能读入并解释 historical 06、07_ppt_master_inspired_native、academic frozen baseline，再谈生成新模板。
2. 第一批代码只做 `DeckIR + PPTX intake + universal scorecard v0`。
   - 这三个模块跑通以后，才进入 seed strategist。
3. `ppt-master` 的价值抽象成 pipeline 能力：
   - strategist：先决定叙事、页面角色、视觉系统；
   - spec_lock：把设计约束机器可读化；
   - template architecture：把 brand / layout / deck 分层；
   - quality gate：先验 probe，再扩展 full deck；
   - native export：最终仍要可编辑。
4. Route 06 的历史价值是“旧路线对照”，不是新主线模板。
   - 它证明 bounded repair 能压低低严重度问题，但 high / medium plateau，所以必须前移到 template gate。
5. 新 benchmark 不能只服务 Paper2Slides。
   - 所有规则都要先问一句：这条规则能不能评一个外部 PPTX？如果不能，要么降级为 Paper2Slides-only 规则，要么改写成 DeckIR 可解释规则。

因此，新窗口第一步的成功标准不是“生成更好看的 PPT”，而是“同一套 DeckIR/scorecard 能解释为什么 07 更好、为什么 06 有潜力但卡住、为什么 baseline 稳定但不够现代”。

## 1. 当前结论与路线决策

### 1.1 保留什么

保留现有项目里的核心资产：

1. `parse-once checkpoint`
   - `checkpoint_summary.json`
   - `checkpoint_plan.json`
   - `checkpoint_slide_spec.json`
   - figures / tables / metrics / evidence inventory
2. Native PPTX 交付目标
   - 输出仍以可编辑 PPTX 为主，不接受整页截图式交付作为主线。
3. `nonvisual_audit.py`
   - 继续作为 metadata-first audit 的基础。
4. `sixway.py` 的 benchmark harness 思路
   - 保留 run manifest、route directory、score curve、artifact index、repair log、human feedback effort。
5. 历史 frozen references
   - academic / golden1 / golden2 继续作为回归对照。
6. 历史 route 06
   - `autonomous_style_proposal_b` 保留为“可调潜力样式”和旧路线对照。

### 1.2 暂停什么

1. 暂停以 `04_assisted_seed_scaffold_style` 作为主线 seed。
   - 它证明了弱脚手架能进入 benchmark，但视觉起点不够强。
2. 暂停继续投入 `05_autonomous_style_proposal_a`。
   - 可归档为实验对照。
3. 暂不把 `guizang-ppt-skill` 作为主线。
   - 它很规律，适合未来做“规则型 HTML deck benchmark”参考，但当前更需要 ppt-master 的初稿生成 pipeline。

### 1.3 新主线

新主线改成：

```text
Paper content checkpoint
 -> PPT Master-style Strategist
 -> Seed Template Package
 -> 7-8 page Visual Probe
 -> Template Gate
 -> Full Deck Generation
 -> Universal PPT Benchmark
 -> Template-level Repair
 -> Page-level Repair
 -> Human Feedback Packet
 -> Benchmark Report
```

## 2. 为什么要引入 PPT Master 思想

### 2.1 当前 Paper2Slides 的强项

现有项目已经具备：

- 论文解析链路；
- 内容规划；
- 原生 PPTX 渲染；
- speaker script；
- metadata-only PPTX audit；
- 多 route 对照；
- bounded repair log；
- score curve。

这已经是一个真实的 benchmark 雏形。

### 2.2 当前 Paper2Slides 的短板

现有问题不是“不会局部修”，而是“初稿模板生成阶段太弱”：

```text
旧流程：
先生成一整套 PPT
 -> 发现问题
 -> 用 bounded repair 局部压缩文案、调字号、修 overflow
```

如果初始视觉骨架不够好，后续 repair 只能做局部缝补，难以把普通模板修成真正漂亮的 deck。

Route 06 的数据证明了这一点：

| iteration | total | high | medium | low |
|---:|---:|---:|---:|---:|
| 0 | 136 | 26 | 34 | 76 |
| 1 | 112 | 25 | 35 | 52 |
| 2 | 112 | 25 | 35 | 52 |

结论：

- total findings 下降 17.6%；
- low severity 下降 31.6%；
- typography dimension 下降 27.3%；
- near_text_capacity 下降 56.3%；
- 但 high/medium 基本 plateau。

这说明：当前 repair 能处理文本容量和字号舒适区，但不能解决模板级审美、版式骨架、视觉节奏和中高风险问题。

### 2.3 PPT Master 对应的补位

`ppt-master` 的核心不是“一个更好看的模板”，而是一个更强的初稿生成 pipeline：

```text
Source Document
 -> Create Project
 -> optional Template
 -> Strategist
 -> Image Acquisition
 -> Executor / Live Preview
 -> Quality Check
 -> Post-processing / Export
```

最值得吸收的机制：

1. `Strategist`
   - 在生成页面前先决定受众、叙事、页面角色、视觉系统、素材计划。
2. `spec_lock`
   - 把颜色、字体、页面节奏、图片/图表槽位、禁用规则写成可执行契约。
3. `brand / layout / deck` 模板分层
   - identity、structure、完整 deck 三类资产可组合、可溯源。
4. `page_rhythm`
   - 每页不是同一种 card grid，而是 anchor / dense / breathing 等节奏变化。
5. `quality gate`
   - 生成后先过质量检查，再导出。
6. `native editability`
   - 最终 PPTX 是可编辑对象，不是整页图片。

## 3. 总体架构升级

### 3.1 新系统分层

```text
Layer 0: Paper Parse Layer
  复用现有 summary / plan / slide_spec / figures / tables / metrics checkpoint

Layer 1: Content Inventory Layer
  汇总论文主题、证据、图表、表格、metrics、slide roles

Layer 2: Seed Strategist Layer
  生成 seed_template_contract，不直接生成完整 PPT

Layer 3: Template Package Layer
  生成 brand / layout / component / validator / spec_lock

Layer 4: Visual Probe Layer
  先生成 7-8 页小样，快速验证视觉系统是否值得扩展

Layer 5: Universal Benchmark Layer
  将任意 PPTX 解析为统一 DeckIR，然后按通用规则评分

Layer 6: Repair Layer
  先 template-level repair，再 page-level repair

Layer 7: Human Feedback Flywheel
  把人工判断结构化写回 rule registry / style registry / benchmark schema
```

### 3.2 新增模块建议

建议新增目录：

```text
paper2slides/benchmark/universal/
  deck_ir.py
  pptx_intake.py
  editability.py
  content_fidelity.py
  narrative.py
  visual_design.py
  scoring.py
  report.py

paper2slides/benchmark/seed_pipeline/
  content_inventory.py
  strategist.py
  template_contract.py
  template_package.py
  visual_probe.py
  template_gate.py
  template_repair.py
  page_repair.py

paper2slides/benchmark/ppt_master_bridge/
  research_notes.py
  style_brief_import.py
  spec_lock_adapter.py
  comparison_runner.py
```

短期也可以不立刻拆这么细，但计划书和 schema 应按这个边界设计，避免继续堆到 `sixway.py` 里。

## 4. Universal DeckIR：通用 benchmark 的核心

### 4.1 为什么需要 DeckIR

当前 `nonvisual_audit.py` 直接读取 PPTX 并产出 findings。它适合评我们自己的原生 PPTX，但要评任意 PPT 生成系统，需要先把不同来源统一成一个中间表示：

```text
PPTX / external deck
 -> DeckIR
 -> universal audit rules
 -> scorecard
 -> repair suggestions
```

DeckIR 是整个泛化 benchmark 的关键。

### 4.2 DeckIR 最小字段

```json
{
  "schema_version": "deck_ir.v1",
  "source": {
    "path": "...",
    "generator": "paper2slides | ppt-master | human | unknown",
    "artifact_kind": "pptx",
    "native_editability_expected": true
  },
  "deck": {
    "slide_count": 24,
    "width_in": 13.333,
    "height_in": 7.5,
    "theme_signals": {
      "palette": [],
      "font_families": [],
      "dominant_backgrounds": []
    }
  },
  "slides": [
    {
      "slide_index": 1,
      "role_guess": "cover | agenda | content | evidence | metric | closing | unknown",
      "objects": [],
      "text": {
        "title_candidates": [],
        "body_blocks": [],
        "caption_candidates": []
      },
      "layout": {
        "occupancy": 0.0,
        "alignment_groups": [],
        "safe_area_violations": []
      },
      "editability": {
        "text_chars_native": 0,
        "raster_area_ratio": 0.0,
        "native_shape_count": 0,
        "picture_count": 0
      }
    }
  ]
}
```

### 4.3 DeckIR 的第一批来源

第一轮只接三类：

1. Paper2Slides 输出：历史 06 / frozen baselines。
2. 07 `ppt_master_inspired_native.pptx`。
3. 任意用户手工 PPTX。

后续再接：

- 真实 `ppt-master` 完整运行输出；
- Gamma / Canva 导出 PPTX；
- HTML 转 PPTX；
- PDF/raster deck。

## 5. 通用 PPT Benchmark 维度

### 5.1 一级维度

建议 universal benchmark 的一级维度固定为 9 个：

| dimension | 评什么 | 自动化方式 |
|---|---|---|
| Editability | 是否原生可编辑，不是截图 | DeckIR object / raster ratio |
| Content Fidelity | 是否覆盖论文核心内容 | checkpoint vs deck text/evidence matching |
| Narrative Structure | 是否有清晰故事线和页面角色 | slide role roster / section coverage |
| Evidence Grounding | figure/table/metric 是否有来源和说明 | evidence inventory alignment |
| Layout Geometry | 越界、重叠、安全区、容器关系 | existing nonvisual audit |
| Typography | 字号、层级、文本容量、行距 | existing + expanded typography rules |
| Visual Design | 留白、节奏、对比、视觉焦点、风格一致性 | heuristic + human calibration |
| Repairability | 问题能否自动修，修后是否劣化 | repair log / delta audit |
| Human Preference | 人类保留/拒绝/局部借鉴 | structured feedback packet |

### 5.2 二级指标

#### Editability

- `native_text_ratio`
- `native_shape_ratio`
- `raster_page_ratio`
- `editable_table_count`
- `editable_chart_count`
- `background_image_overuse`

#### Content Fidelity

- `title_match`
- `section_coverage`
- `claim_coverage`
- `figure_reference_coverage`
- `table_reference_coverage`
- `metric_reference_coverage`
- `unsupported_claim_count`

#### Narrative Structure

- `role_roster_completeness`
- `section_transition_quality`
- `claim_to_evidence_flow`
- `agenda_alignment`
- `closing_takeaway_presence`

#### Evidence Grounding

- `proof_object_per_key_claim`
- `figure_caption_alignment`
- `table_readability`
- `metric_label_context`
- `source_traceability`

#### Layout Geometry

- `shape_overlap_risk`
- `text_exceeds_container_bounds`
- `table_exceeds_container_bounds`
- `picture_aspect_distortion`
- `safe_area_violation`

#### Typography

- `low_font_size`
- `below_ideal_font_band`
- `near_text_capacity`
- `estimated_text_overflow`
- `title_hierarchy_weak`
- `caption_legibility_risk`

#### Visual Design

- `visual_focus_missing`
- `rhythm_monotony`
- `palette_noise`
- `contrast_weakness`
- `overdecorated_layout`
- `underdesigned_layout`
- `style_inconsistency`
- `density_mismatch`

#### Repairability

- `repair_success_rate`
- `new_findings_introduced`
- `metric_improved_visual_regressed`
- `style_drift_after_repair`
- `template_level_blocker`

#### Human Preference

- `human_accept`
- `human_reject`
- `borrowable_trait`
- `visual_trait_to_avoid`
- `needs_template_repair`
- `needs_page_repair`

## 6. Seed Template Package 设计

### 6.1 为什么 seed template 要成为 first-class artifact

当前 proposal route 的 contract 还比较粗：

```text
visual_family
layout_grammar
proof_object_grammar
typography_system
palette_roles
container_rules
renderer_parameters
```

它还不是一个真正可复用、可评测、可修复的 template package。

升级后，每次 seed-template 生成都应产出完整目录：

```text
seed_template_package/
  design_spec.md
  spec_lock.json
  brand.json
  layout_registry.json
  component_primitives.json
  page_role_roster.json
  validator_rules.json
  provenance.json
```

### 6.2 `design_spec.md`

人类可读说明，参考 ppt-master 的 design spec，但不要照搬全部格式。

需要包含：

- deck intent；
- target audience；
- narrative strategy；
- visual language；
- page rhythm；
- proof object strategy；
- typography；
- palette；
- forbidden patterns；
- benchmark gates。

### 6.3 `spec_lock.json`

机器可读执行契约。

示例：

```json
{
  "schema_version": "spec_lock.v1",
  "canvas": {"width_in": 13.333, "height_in": 7.5},
  "palette": {
    "background": "#F4F0E8",
    "ink": "#171717",
    "accent": "#E24A2B",
    "secondary": "#164A7A"
  },
  "typography": {
    "title_pt": [42, 64],
    "claim_pt": [24, 34],
    "body_pt": [15, 21],
    "caption_pt": [9, 12]
  },
  "page_rhythm": {
    "cover": "anchor",
    "metric_ledger": "dense",
    "evidence_wall": "dense",
    "takeaway": "breathing"
  },
  "forbidden_patterns": [
    "full-slide raster screenshot",
    "generic bullet-only page",
    "unlabeled figure",
    "table rendered as unreadable image"
  ]
}
```

### 6.4 `layout_registry.json`

页面类型注册表。

第一批建议：

```text
cover
agenda
section_divider
central_thesis
method_stack
comparison
metric_ledger
evidence_wall
figure_focus
table_focus
risk_map
system_diagram
closing
```

每个 layout 需要声明：

- input content type；
- max text budget；
- proof object slot；
- typography floor；
- geometry constraints；
- expected density；
- repair affordance。

### 6.5 `component_primitives.json`

组件原语，必须可转成原生 PPTX 对象。

第一批：

```text
native_textbox
native_rect
native_rule
native_table
metric_card
evidence_note
proof_panel
step_rail
comparison_panel
source_chip
figure_slot
```

### 6.6 `validator_rules.json`

把 benchmark 规则前置成模板 gate。

例子：

```json
{
  "title_min_pt": 32,
  "body_min_pt": 14,
  "caption_min_pt": 9,
  "max_text_fill_ratio": 0.88,
  "min_native_text_ratio": 0.75,
  "max_raster_area_ratio": 0.35,
  "required_page_roles": ["cover", "central_thesis", "evidence_wall", "metric_ledger", "closing"],
  "forbidden_global_flags": ["deck_type_scale_under_comfort_band"]
}
```

## 7. 新 runner 设计

### 7.1 新 route 编排

下一轮建议不要继续旧 04/05/06，而是：

```text
01 academic_frozen_reference
02 golden1_frozen_reference
03 golden2_frozen_reference
04 retained_autonomous_b_control
05 ppt_master_seed_probe
06 ppt_master_seed_full_repair
```

解释：

- 01-03 保留稳定回归基线。
- 04 保留历史 06，看旧路线继续修能到哪里。
- 05 只生成 7-8 页 probe，验证 seed-template 是否好。
- 06 用通过 gate 的 seed-template 生成完整 24 页 deck，再跑 repair loop。

### 7.2 新 runner 文件建议

新增：

```text
paper2slides/benchmark/ppt_master_seed.py
```

或者更泛化：

```text
paper2slides/benchmark/universal_seedway.py
```

核心函数：

```python
def run_ppt_master_seed_benchmark(
    paper_path: Path,
    run_dir: Optional[Path],
    slides: int = 24,
    probe_slides: int = 8,
    max_iterations: int = 3,
) -> Dict[str, Any]:
    ...
```

### 7.3 runner 输出目录

```text
benchmark_runs/<paper>_pptmaster_seed_<timestamp>/
  manifest.json
  fresh_parse_outputs/
  content_inventory.json
  seed_template_package/
    design_spec.md
    spec_lock.json
    brand.json
    layout_registry.json
    component_primitives.json
    page_role_roster.json
    validator_rules.json
    provenance.json
  routes/
    01_academic_frozen_reference/
    02_golden1_frozen_reference/
    03_golden2_frozen_reference/
    04_retained_autonomous_b_control/
    05_ppt_master_seed_probe/
      visual_probe.pptx
      deck_ir.json
      universal_audit.json
      template_gate.json
      human_review_packet.zh-CN.md
    06_ppt_master_seed_full_repair/
      iterations/
        iter_00/
        iter_01/
        iter_02/
      repair_log.json
      deck_ir.json
      universal_audit.json
  universal_score_curve.csv
  artifact_index.csv
  benchmark_report.md
```

## 8. Repair 机制升级

### 8.1 现有 repair 的问题

当前 `_planned_repairs_from_previous` 基本是：

```text
发现 top-k finding
 -> tighten copy
 -> preserve evidence
 -> keep style contract
```

这适合低风险 copy fitting，但不适合视觉模板失败。

### 8.2 新 repair 分两级

#### Template-level repair

修模板，不修具体一页。

触发条件：

- 多页都出现 `low_font_size`；
- 多页都出现 `deck_type_scale_under_comfort_band`；
- layout / typography dimension 长期为 0；
- visual design score 低；
- human feedback 指出“整体不好看”；
- probe gate 未通过。

动作：

- 调整 type scale；
- 更换 layout role；
- 改 proof object slot；
- 改 page rhythm；
- 改 density target；
- 改 component primitive。

#### Page-level repair

修具体页面。

触发条件：

- 单页 overflow；
- 单页 table / figure / caption 问题；
- 单页 evidence missing；
- 单页文本过满。

动作：

- 缩短 copy；
- 换组件；
- 分裂页面；
- 调整图片槽位；
- 重新绑定 evidence object。

### 8.3 repair 日志升级

`repair_log.json` 需要记录：

```json
{
  "repair_level": "template | page",
  "target": "typography_system | layout_registry | slide_12",
  "finding_ids": [],
  "action": "...",
  "expected_metric_change": {},
  "actual_metric_change": {},
  "introduced_new_findings": [],
  "human_outcome": "pending | accepted | rejected | tradeoff"
}
```

## 9. Human Feedback 数据飞轮

### 9.1 反馈不是一句话

用户说“07 好看、08 规律、06 有潜力”，应该结构化为：

```json
{
  "accepted_traits": [
    "editorial data-reporting layout",
    "native evidence blocks",
    "clear visual focus"
  ],
  "rejected_traits": [
    "weak scaffold start",
    "overly regular swiss system as current mainline"
  ],
  "retain_routes": ["06_autonomous_style_proposal_b"],
  "retire_routes": ["04_assisted_seed_scaffold_style", "05_autonomous_style_proposal_a"],
  "new_direction": "ppt_master_seed_pipeline",
  "benchmark_implication": "need universal benchmark and template-level repair"
}
```

### 9.2 新文件

```text
human_feedback_packet.json
human_feedback_packet.zh-CN.md
```

### 9.3 human feedback 晋升规则

反馈进入三类资产：

1. `style_registry`
   - 记录哪些视觉 trait 被接受。
2. `badcase_registry`
   - 记录哪些问题变成规则。
3. `template_gate`
   - 记录哪些偏好变成 gate。

## 10. 通用 Benchmark 与 PPT Master 的关系

### 10.1 不直接把 ppt-master 当成终点

禁止路线：

```text
只要 ppt-master 好看 -> 直接替换 Paper2Slides
```

正确路线：

```text
ppt-master 输出 / 思想
 -> 作为强外部样本
 -> 抽象成通用指标和 seed pipeline
 -> 让 benchmark 能评 ppt-master 和其他生成器
```

### 10.2 第一轮泛化实验

用同一个 universal benchmark 评三类 deck：

| deck | 目的 |
|---|---|
| historical 06 | 旧 autonomous proposal 对照 |
| 07 ppt-master-inspired native | 强 seed 视觉参考 |
| academic / golden baselines | 稳定回归基线 |

成功标准：

- 三类 deck 都能转 DeckIR；
- 三类 deck 都能产出统一 scorecard；
- benchmark 能解释“07 为什么被人觉得好看”；
- benchmark 能解释“06 为什么有潜力但 plateau”；
- benchmark 不因为不是 Paper2Slides 原生 route 就失效。

## 11. 实施阶段计划

### Phase 0：冻结计划与新窗口启动

目标：只定计划，不大改代码。

产物：

- 本计划书；
- 新窗口启动词；
- 当前决策记录。

### Phase 1：DeckIR 与外部 PPTX intake

目标：让 benchmark 能吃任意 PPTX。

改动：

```text
paper2slides/benchmark/universal/deck_ir.py
paper2slides/benchmark/universal/pptx_intake.py
paper2slides/benchmark/universal/editability.py
```

验收：

- 能读历史 06；
- 能读 07；
- 能读 frozen baseline；
- 输出 `deck_ir.json`。

### Phase 2：Universal scorecard

目标：从 DeckIR 生成通用评分。

改动：

```text
paper2slides/benchmark/universal/scoring.py
paper2slides/benchmark/universal/report.py
```

验收：

- 输出 9 维分数；
- 输出 findings；
- 输出 human-readable report；
- 能解释 editability / typography / layout / visual_design。

### Phase 3：Seed strategist schema

目标：把 ppt-master 的 strategist 思想转为 Paper2Slides schema。

改动：

```text
paper2slides/benchmark/seed_pipeline/template_contract.py
paper2slides/benchmark/seed_pipeline/strategist.py
```

验收：

- 从 content inventory 生成 `seed_template_contract.json`；
- 生成 `design_spec.md`；
- 生成 `spec_lock.json`。

### Phase 4：Seed template package

目标：让 seed 模板成为可复用 artifact。

改动：

```text
paper2slides/benchmark/seed_pipeline/template_package.py
```

验收：

- 生成完整 `seed_template_package/`；
- 包含 brand/layout/component/validator/provenance；
- 可被 renderer/runner 读取。

### Phase 5：Visual probe runner

目标：先生成 7-8 页视觉小样。

改动：

```text
paper2slides/benchmark/seed_pipeline/visual_probe.py
paper2slides/benchmark/ppt_master_seed.py
```

验收：

- 输出 `visual_probe.pptx`；
- 输出 `template_gate.json`；
- 输出 `visual_probe_scorecard.json`。

### Phase 6：Template gate

目标：probe 先过 gate，再生成 full deck。

改动：

```text
paper2slides/benchmark/seed_pipeline/template_gate.py
```

验收：

- 如果 probe 字号/布局/可编辑性不合格，阻止 full deck；
- 输出 template-level repair suggestion。

### Phase 7：Full deck route

目标：用通过 gate 的 seed template 生成完整 deck。

改动：

```text
paper2slides/benchmark/ppt_master_seed.py
paper2slides/generator/pptx_renderer.py  # 只在必要时扩展，不要无边界重构
```

验收：

- 生成 24 页 PPTX；
- universal benchmark 可评；
- repair log 记录完整。

### Phase 8：Template-level repair

目标：突破 06 的 plateau。

改动：

```text
paper2slides/benchmark/seed_pipeline/template_repair.py
paper2slides/benchmark/seed_pipeline/page_repair.py
```

验收：

- 能区分 template blocker 和 page blocker；
- 修模板后多页同类问题下降；
- repair 不引入明显 style drift。

### Phase 9：Human feedback packet

目标：把讨论变成 benchmark 数据。

改动：

```text
paper2slides/benchmark/human_feedback.py
```

验收：

- 用户反馈写入 JSON；
- 可晋升到 style registry / badcase registry / template gate。

### Phase 10：报告与简历故事

目标：形成面试可讲的结果。

产物：

- `benchmark_report.md`
- `universal_score_curve.csv`
- before/after table；
- accepted/rejected style trait；
- 10 分钟面试讲稿。

## 12. 关键技术风险

### 风险 1：把 PPT Master 误解成模板库

应对：只吸收 pipeline 和数据结构，不直接照搬视觉或脚本。

### 风险 2：benchmark 仍然只适配自己

应对：DeckIR 必须先支持 07 / 历史 06 / frozen baseline 三类 deck。

### 风险 3：视觉设计难量化

应对：不要一开始做单一 aesthetic score。先拆成可解释信号：

```text
focus
hierarchy
density
rhythm
contrast
alignment
style consistency
native editability
```

### 风险 4：repair 只会局部修

应对：明确 template-level repair，在 gate 阶段就阻止坏模板扩展。

### 风险 5：PPT Master 的 SVG-to-DrawingML 路径过重

应对：短期不实现完整 SVG converter。短期用现有 native PPTX renderer / artifact-tool 思路模拟 seed pipeline；中期再评估 SVG backend。

### 风险 6：中文文档编码在 PowerShell 显示乱码

应对：文件保持 UTF-8；在 Codex/编辑器中读正常即可。不要因 PowerShell 显示乱码误判文件损坏。

## 13. 新窗口启动词

新窗口可以直接发：

```text
Codex 老师，我们继续 Paper2Slides-main 的下一阶段：PPT Master 融合与通用 PPT Benchmark 升级。

项目路径：
D:\coding\agent_paper_to_slider\Paper2Slides-main

本轮继续使用的论文：
D:\coding\agent_paper_to_slider\Paper2Slides-main\test_papers\OpenAI_GPT-5_System_Card.pdf

这篇论文已经完成解析和 six-way smoke，本地运行目录是：
D:\coding\agent_paper_to_slider\Paper2Slides-main\benchmark_runs\openai_gpt5_system_card_sixway_20260701_smoke

注意：benchmark_runs 是本地运行产物目录，默认不提交到 GitHub；请优先复用其中的 checkpoint、routes 和 deliverables 做下一步实验。

请先阅读：
1. docs/ppt_master_universal_benchmark_upgrade_plan.zh-CN.md
2. docs/ppt_master_seed_pipeline_integration_plan.zh-CN.md
3. docs/openai_gpt5_external_ppt_project_review_plan.zh-CN.md
4. docs/autonomous_style_proposal_benchmark_plan.zh-CN.md
5. paper2slides/benchmark/sixway.py
6. paper2slides/benchmark/nonvisual_audit.py
7. external_refs/ppt-master_readonly/SKILL.md
8. external_refs/ppt-master_readonly/templates-architecture.md
9. external_refs/ppt-master_readonly/why-ppt-master.md

当前决策：
- 保留 parse-once checkpoint、native PPTX、nonvisual audit、sixway benchmark、repair log、frozen references。
- 历史 04/05 不再作为主线；历史 06 保留为可调潜力样式和旧路线对照。
- 暂时抛开 guizang 主线，重点吸收 ppt-master 的 strategist / spec_lock / seed-template / quality-gate。
- 目标不是只向 ppt-master 靠拢，而是让 benchmark 泛化到 Paper2Slides、ppt-master、人工 PPT、其他 PPT 生成器。

请先不要大改 renderer。第一步实现 DeckIR 和 external PPTX intake：
1. 新增 paper2slides/benchmark/universal/deck_ir.py
2. 新增 paper2slides/benchmark/universal/pptx_intake.py
3. 能把历史 06、07_ppt_master_inspired_native.pptx、academic frozen baseline 都转成 deck_ir.json
4. 给出第一版 universal scorecard schema

做之前请先检查 git status，并保护已有未提交改动。
```

## 14. 第一轮验收标准

第一轮不要求完整新 pipeline，只要求证明“通用 benchmark”起步成立。

必须完成：

- DeckIR schema；
- PPTX intake；
- 06 / 07 / baseline 三类 deck 的 DeckIR；
- universal scorecard v0；
- 一份报告解释：
  - 为什么 07 更好看；
  - 为什么 06 有潜力但 plateau；
  - 旧 nonvisual audit 哪些规则仍适用；
  - 哪些新视觉规则需要 human feedback 校准。

第一轮成功后，才进入 seed strategist 和 visual probe runner。

## 15. 最终面试叙事

最终项目可以这样讲：

> 我们没有只做一个论文转 PPT demo，而是把 PPT 生成当成可评测、可返修、可积累反馈的数据系统。系统先把论文解析成可复用 checkpoint，再生成原生可编辑 PPTX，并通过通用 DeckIR 把不同来源 PPT 转成统一评测对象。Benchmark 从 severity、dimension、rule type、editability、content fidelity、visual design、repairability 等维度给出量化评分；repair loop 分为 template-level 和 page-level，能记录每次修改是否真正降低问题，是否引入视觉回退。后来我们参考 ppt-master 的 strategist/spec-lock 思想，把“生成强初稿模板”前置为 seed-template pipeline，让系统不只会局部修 PPT，而能逐步学习什么样的 PPT 初稿更容易被 benchmark 修好、更容易被人接受。

这条叙事比“我做了一个生成 PPT 的 Agent”强很多，因为它的核心是 benchmark、反馈闭环和泛化评估能力。
