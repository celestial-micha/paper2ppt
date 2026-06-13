# HITL v10 Component Reflow Lessons

本文档总结 Kimi K2 from-scratch PPT 从早期草稿迭代到 `rough_draft_v10_component_reflow` 的 human-in-the-loop 经验。目标不是记录某一页怎样手工改好看，而是把人工审美反馈沉淀成可检测、可修复、可回归的 benchmark 规则。

## 1. 当前结论

`rough_draft_v10_component_reflow` 已经被人工认为在 Kimi K2 主案例上非常成功，但它还不应该立刻升级为 golden baseline。

更准确的状态是：

```text
successful style candidate
 -> pending cross-paper validation
 -> promote only after other papers expose no serious style failure
```

原因很简单：一个 PPT 样式可能非常适合 Kimi K2 的证据结构，但换成图更复杂、表更密、数学符号更多或 proof object 类型不同的论文时，仍可能暴露新问题。

## 2. 这轮 HITL 暴露的核心问题

### 2.1 局部密度优化会破坏整体美感

v6 的失败说明，看到卡片文字少、留白多，就自动缩组件，并不可靠。局部上似乎更紧凑，整页却可能失去稳定感、庄重感和呼吸感。

经验：

- 低密度本身只是提示，不是自动改组件大小的充分理由。
- 如果组件构图已经被人类认可，优先改 copy、字号、换行和层级。
- 只有出现结构性失败或内容适配失败时，才允许改组件尺寸。

### 2.2 字号是全局角色契约，不是单页自由变量

title、claim、support、card label、card body、metric value、footer 等文字角色应该有 deck-wide 的字号和层级关系。

经验：

- 单页觉得字小，先判断是否是全局 role 偏弱。
- 如果是全局问题，就做 deck-level type scale pass。
- 如果只是某个组件过空或过满，就改该组件的 frame 和同页布局，不为单页发明新字号体系。

### 2.3 组件先有结构，但结构要接受真实文字反馈

更稳定的流程不是“先定组件后永不改变”，而是：

```text
style contract
 -> component grammar
 -> real text fitting
 -> local content-fit diagnosis
 -> local component resize/reposition
 -> same-slide sibling reflow
```

这正是 v10 的核心改法。第 15 页 evidence cards 不是因为单页文字小就乱改字号，而是检测出卡片框在真实文字填入后明显过高，于是缩小本地卡片高度，并保持三张卡片同一行重排。

## 3. 人类观察如何变成机器规则

| 人类观察 | 可检测代理指标 | 新 badcase |
| --- | --- | --- |
| label 和解释文字看起来不像一组 | label/body top delta | `paired_label_body_gap_too_large` |
| 2x2 read path 变成两行后列太散、文字没居中 | column gap、row gap、label-center drift | `flow_grid_alignment_drift` |
| 卡片框比里面文字高太多 | fitted text stack height vs frame height | `component_frame_overallocated_after_text_fit` |
| FIGURE/TABLE 标签贴近圆角边界 | component label boundary inset | `component_boundary_inset_violation` |

这说明 human-in-the-loop 的真正价值是：人类指出“哪里不舒服”，系统把它转成稳定的 geometry / typography / copy-fitting / optical-balance 规则。

## 4. v10 后的 benchmark 流程

当前 from-scratch track 应按下面顺序运行：

```text
parsed checkpoints
 -> content inventory
 -> deck architecture contract
 -> slide semantic contract
 -> visual system contract
 -> real text fitting
 -> content-fit component reflow
 -> nonvisual audit
 -> human feedback
 -> badcase/rule update
 -> cross-paper validation
 -> candidate style promotion or repair
```

## 5. v10 样式保存策略

v10 应保存为 `candidate_style_reference`，而不是覆盖 `accepted_reference`。

当前机器可读记录位于：

```text
benchmarks/from_scratch_human_feedback_benchmark.json
```

推广条件：

1. 在至少两篇非 Kimi 论文上 nonvisual audit 无 high / medium finding。
2. 人工确认 contact-sheet rhythm 和关键页仍然好看。
3. 新暴露的问题先被写成 badcase，再决定是否调整样式。

## 6. mHC 验证时重点看什么

`mHC: Manifold-Constrained Hyper-Connections` 更偏数学结构和模型机制，可能暴露与 Kimi K2 不同的问题。下一轮重点观察：

- figure panel 是否仍有足够边界和标题层级；
- 数学/结构图是否在圆角容器里显得过小或过空；
- text evidence 是否能保持学术庄重感；
- table/metric 页面是否出现过挤、过空或语义不对应；
- v10 的 warm academic 风格是否仍然适合更理论化的论文。

如果 mHC 暴露新问题，应继续按同一格式沉淀：

```text
badcase:
example_slide:
problem_type: typography | copy_fitting | geometry | optical_balance
human_observation:
non_visual_trigger:
preferred_repair:
forbidden_repair:
regression_check:
```

## 7. mHC 第一轮验证结果

直接把 v10 样式用于 mHC 时，nonvisual audit 一开始暴露出大量高风险文本适配问题：长作者列表、理论化 claim、密集 support、cover highlight 和 conclusion evidence 都比 Kimi K2 更难装进同一套文字框。

这说明 v10 的视觉语法可以迁移，但文字压缩契约不能只按 Kimi K2 调参。

本轮修复后，mHC 输出达到：

```text
high findings: 0
medium findings: 0
remaining findings: low only
```

对应新增经验：

- claim/support word limit 要按 proof type 调整；
- cover author list 要自动 compact；
- closing page 不能写死 Kimi 文案；
- text-evidence conclusion 不能被塞进 metric grid；
- narrow evidence-card stack 要自动使用 compact typography。

因此 mHC 可以登记为：

```text
passed_nonvisual_audit_pending_human_visual_review
```

它还不是人工审美通过，但已经证明 candidate style 在第二篇论文上没有出现结构性/几何性失败。

## 8. mHC 第二轮视觉反馈：proof object 还要看“内容形状”

这轮 mHC 人工检查暴露了两个新问题：

1. Figure 4 / Figure 6 这类图不是接近正方形的图，而是很长的横向图。过去的规则只看 `proof_object.type == figure`，所以仍然把它们塞进右侧竖向圆角矩形。更严重的是，图片插入时给了固定宽高，可能破坏原始长宽比。
2. 有一页表格看起来像空面板。根因不是完全没识别到表格，而是 slide_spec 里有 inline table rows，但 proof id 使用的是展示标题；渲染器只按 extracted asset table id 建索引，导致找不到 rows。

这说明 proof object 的判断不能只停在 `figure / table / metric / text` 四类。还要继续判断：

- figure 的原始长宽比；
- figure 应该放右侧、左侧，还是底部长条容器；
- 图片插入后是否保持原始比例；
- table rows 来自 extracted asset，还是来自 slide_spec inline table；
- proof id 和真实 payload id 不一致时，是否仍能找到可渲染内容。

对应新增 badcase：

```text
wide_figure_forced_into_side_panel
figure_picture_aspect_distortion
inline_table_payload_not_indexed
```

修复原则：

- 超宽图优先使用底部横向 proof panel，而不是右侧竖向 proof panel；
- 所有 figure 图片都要按原始比例 fit 到内容框，不能用固定宽高硬拉伸；
- table index 要同时索引 extracted tables 和 curated inline tables；
- 如果 proof object 有展示标题但没有 asset id，先尝试用 inline rows 渲染，不要直接掉到空文本 fallback。

这一步把 benchmark 从“按证明类型排版”推进到“按证明类型 + 证明载荷形状排版”。这是跨论文验证真正有价值的地方：Kimi K2 没暴露的问题，mHC 会暴露；暴露以后，规则就变成下一篇论文的自动经验。
