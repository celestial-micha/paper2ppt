# 07 Seed Template Package 阶段报告

日期：2026-07-02

本阶段目标：把 `07_ppt_master_inspired_native.pptx` 从一个外部参考样张，转成可复用、可 gate、可进入后续 seed strategist / visual probe runner 的 first-class template package。

## 1. 新增代码

新增模块：

```text
paper2slides/benchmark/seed_pipeline/
  __init__.py
  template_package.py
  template_gate.py
```

新增 CLI：

```text
python -m paper2slides.benchmark seed-template-package
```

该命令只读取 `deck_ir.json` 和 `universal_scorecard.v0.json`，不渲染、不调用模型、不改 renderer。

## 2. 本轮产物

输出目录：

```text
benchmark_runs/openai_gpt5_system_card_sixway_20260701_smoke/seed_template_package_07/
```

产物：

```text
design_spec.md
spec_lock.json
brand.json
layout_registry.json
component_primitives.json
page_role_roster.json
validator_rules.json
provenance.json
template_gate.json
package_index.json
```

这些文件对应计划中的 seed-template package：

- `design_spec.md`：人类可读设计说明。
- `spec_lock.json`：机器可读约束，包括 canvas、palette、typography、page rhythm、proof-object 策略和 forbidden patterns。
- `brand.json`：07 提炼出的视觉语言、色彩角色、字体和语气。
- `layout_registry.json`：从 8 页 probe 提炼出的 layout candidate，而不是直接复制 slide template。
- `component_primitives.json`：native textbox、native rect、metric card、evidence note、proof panel、source chip 等组件原语。
- `page_role_roster.json`：观察到的 probe roles 和推荐 full deck roles。
- `validator_rules.json`：下一步 template gate 的阈值。
- `template_gate.json`：本轮 gate 结果。

## 3. Template Gate 结果

`template_gate.json` 的状态：

```text
pass_with_warnings
```

通过项：

| check | observed | threshold |
| --- | ---: | ---: |
| native_editability | 100.0 | 90.0 |
| raster_area_ratio | 0.000 | 0.080 |
| typography | 66.8 | 60.0 |
| layout_geometry | 57.0 | 50.0 |
| visual_design_proxy | 74.1 | 65.0 |
| evidence_grounding_proxy | 64.0 | 55.0 |
| required_probe_roles | cover/content/metric present | cover/content/metric |
| layout_signature_count | 8 | 6 |

Warning：

| warning | meaning |
| --- | --- |
| `content_fidelity_probe_only` | 07 是 8 页 visual probe，不是 full paper deck，所以 content coverage 低是合理的。 |
| `human_preference_pending` | 还需要人工确认 accepted / rejected / borrowable traits，才能推广为默认路线。 |

结论：07 可以作为 seed-template candidate 进入下一阶段，但不能被误当成完整论文 deck 成功样本。

## 4. 从 07 提炼出的核心约束

`spec_lock.json` 当前关键值：

```json
{
  "canvas": {"width_in": 13.333, "height_in": 7.5},
  "palette": {
    "background": "#F4F0E8",
    "ink": "#171717",
    "accent": "#E24A2B",
    "muted": "#6B7280"
  },
  "typography": {
    "title_pt": [28, 52],
    "claim_pt": [20, 28],
    "body_pt": [12, 18],
    "caption_pt": [9, 12]
  }
}
```

Page rhythm：

```text
slide_01: anchor
slide_02: balanced
slide_03: breathing
slide_04: dense
slide_05: dense
slide_06: breathing
slide_07: dense
slide_08: breathing
```

Forbidden patterns：

- full-slide raster screenshot
- generic bullet-only page
- unlabeled proof object
- table rendered as unreadable image
- repeating one layout signature across a full deck
- expanding a visual probe into full deck without content coverage gate

## 5. 为什么这是下一阶段的正确桥

前一阶段 universal benchmark 已经证明：

- academic / 06 是 full deck，内容覆盖高，但 typography/layout 存在明显 blocker。
- 07 是 visual probe，内容覆盖低，但 typography/layout/rhythm 强。

本阶段把这个判断转成可执行工程资产：

```text
07 visual probe
 -> DeckIR
 -> scorecard
 -> seed_template_package
 -> template_gate
 -> next visual probe / full deck generation
```

这样后续不会把 07 当成“直接套用的模板”，而是把它降维成：

- brand constraints
- layout registry
- component primitives
- validator rules
- gate thresholds

## 6. 下一阶段建议

下一阶段可以继续做：

1. `paper2slides/benchmark/seed_pipeline/strategist.py`
   - 从 paper checkpoint 生成 seed_template_contract。
   - 明确 deck intent、audience、page role roster、proof object roster。

2. `paper2slides/benchmark/seed_pipeline/visual_probe.py`
   - 使用 seed template package 生成 7-8 页 probe spec。
   - 先跑 template gate，过关后再考虑 full deck。

3. `paper2slides/benchmark/seed_pipeline/template_gate.py` 升级
   - 当前 gate 是 scorecard-level。
   - 下一步应加入 layout_registry 级检查和 human feedback traits。

4. Human feedback packet
   - 记录 07 的 accepted traits：
     - editorial data-reporting layout
     - native evidence blocks
     - clear type hierarchy
     - rhythm diversity
   - 记录 warning：
     - visual probe content coverage low
     - needs full deck content alignment before promotion
