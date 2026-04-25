# Phase 1 Handoff

## 本轮目标

- 只实现 `structured slide spec + editable PPTX output`
- 保持现有 `rag -> summary -> plan -> generate` 主 pipeline 基本不变
- 不提前实现 LangGraph、retry、eval、structured logging

## 实际完成项

- 新增结构化 slide schema
- 新增 plan -> slide spec 转换器
- 新增 deterministic PPTX renderer
- 将 `slides` 的生成路径改为：
  - 读取 `checkpoint_plan.json`
  - 生成 `checkpoint_slide_spec.json`
  - 渲染 `<timestamp>/slides.pptx`
- 保留 `poster` 的旧图片生成路径
- 补充一个最小 smoke test

## 修改文件

- `paper2slides/generator/slide_schema.py`
- `paper2slides/generator/spec_builder.py`
- `paper2slides/generator/pptx_renderer.py`
- `paper2slides/generator/__init__.py`
- `paper2slides/core/stages/generate_stage.py`
- `requirements.txt`
- `README.md`
- `test_phase1_pptx.py`

## 如何验证

1. 安装新增依赖：
   `pip install -r requirements.txt`
2. 运行 smoke test：
   `python -m unittest test_phase1_pptx.py`
3. 用已有 checkpoint 直接从生成阶段跑：
   `python -m paper2slides --input test_papers/AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast --from-stage generate`
4. 检查输出目录：
   - `checkpoint_slide_spec.json`
   - `<timestamp>/slides.pptx`
5. 用 PowerPoint / WPS / LibreOffice 打开 `slides.pptx`，确认文本框、表格、图片占位可编辑

## 已知问题

- 当前 slide 布局是 deterministic 的基础版式，不追求复杂设计感
- 长段落内容只做了轻量切分，可能仍然偏长
- 表格只做 best-effort HTML 解析，复杂表格会降级
- figure 若找不到图片文件，会渲染为可编辑占位块
- 这轮没有把 `spec_build` 升成独立 stage，仍然属于 `generate` 内部步骤

## 下一轮建议

- 把 slide spec 校验补齐，至少拒绝空 slides / malformed blocks
- 考虑把 `spec_build` 从 `generate` 内部步骤提升为显式 checkpointed stage
- 补一条更接近真实 checkpoint 的集成测试
- 逐步增强 PPTX 布局策略，但继续保持 deterministic 和小步提交
