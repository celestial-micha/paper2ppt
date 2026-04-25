# Task: Incrementally Refactor Paper2Slides into a Text-First, Editable PPTX Agent Workflow

## 1. Background

I am working on the open-source project `Paper2Slides`:

- Repo: https://github.com/HKUDS/Paper2Slides

The current system is a 4-stage pipeline:

1. rag
2. summary
3. plan
4. generate

At the moment, the project effectively does:

- parse document
- summarize content
- plan slide pages with LLM
- generate slide images with an image model
- combine them into a PDF

This means the final output is **not a truly editable PPTX**, but rather image-based slides / PDF.

I want to incrementally refactor it into a **text-first, structured, editable presentation generation system**.

---

## 2. Final Goal

Refactor the project toward this target architecture:

- **Pure text / structured planning**
- **Editable PPTX output**
- **Explicit workflow / state machine**
- **Tool use**
- **State recovery**
- **Retry**
- **Evaluation**
- **Structured logging**

Important constraint:

- Do **not** rewrite everything at once
- Do **not** break the current CLI unless necessary
- Do **not** do a huge redesign in one step
- Work in **small, reviewable, minimal steps**

---

## 3. High-Level Refactor Strategy

Please follow this order:

### Phase 1 — Replace image-based output with structured slide specs + editable PPTX renderer
Keep the existing upstream stages as much as possible:

- rag
- summary
- plan

But replace the current `generate` stage behavior:

From:

- plan -> image generation -> slide images -> pdf

To:

- plan -> structured slide specs -> pptx renderer -> editable `.pptx`

This is the highest-priority phase.

### Phase 2 — Introduce typed structured state
Add a unified structured state object / schema for pipeline execution.

### Phase 3 — Add checkpoint validation and safer recovery
Improve checkpoint validity checks and resume behavior.

### Phase 4 — Add structured logging
Each stage should emit machine-readable logs.

### Phase 5 — Introduce LangGraph (or similar explicit state-machine orchestration)
Only after the state and stage boundaries are clear.

### Phase 6 — Add tool use, retry, and evaluation
Build practical agent features incrementally.

---

## 4. Critical Constraints

1. Preserve existing project structure as much as possible
2. Prefer incremental refactor over large rewrite
3. Keep backward compatibility where reasonable
4. Make each step independently runnable and testable
5. Prefer explicit schemas and deterministic behavior
6. Avoid introducing unnecessary abstractions too early
7. The first milestone must produce a real editable `.pptx`

---

## 5. Current Project Understanding

The repo structure is approximately:

- `paper2slides/core/` — pipeline orchestration
- `paper2slides/raganything/` — parsing / RAG
- `paper2slides/summary/` — summarization / extraction
- `paper2slides/generator/` — planning and image generation

Likely relevant files include:

- `paper2slides/core/pipeline.py`
- `paper2slides/core/state.py`
- `paper2slides/core/stages/plan_stage.py`
- `paper2slides/core/stages/generate_stage.py`
- `paper2slides/generator/content_planner.py`
- `paper2slides/generator/image_generator.py`

Please inspect the code before changing anything.

---

## 6. Phase 1 Detailed Goal

### Objective
Implement the **smallest viable refactor** that changes the final output from image-based slides to editable PPTX.

### Required result
After Phase 1, the system should be able to:

1. Read the existing plan output
2. Convert it into a structured slide specification
3. Render an editable `.pptx`
4. Save artifacts in the output folder
5. Preserve resume/checkpoint semantics as much as possible

### Important
Do **not** introduce LangGraph yet in Phase 1.

---

## 7. Proposed Phase 1 Design

### 7.1 Add a structured slide schema
Create a schema layer for slide representation.

Suggested file:

- `paper2slides/generator/slide_schema.py`

Suggested concepts:

- `PresentationSpec`
- `SlideSpec`
- `TextBlock`
- `ImageBlock`
- `TableBlock`
- `ChartBlock` (optional placeholder)
- `ReferenceBlock` (optional)

Keep it simple and pragmatic.

### 7.2 Add a plan-to-slide-spec converter
Create a converter that transforms current planning output into structured slide specs.

Suggested file:

- `paper2slides/generator/spec_builder.py`

This converter should:
- read existing plan data
- map sections/pages into slide specs
- preserve title/body/reference information
- leave unsupported content as placeholders when necessary

### 7.3 Add a PPTX renderer
Create a deterministic renderer using `python-pptx` or similar.

Suggested file:

- `paper2slides/generator/pptx_renderer.py`

Requirements:
- create editable slides
- support title + bullet content first
- support image placeholders or actual inserted images if available
- save output as `.pptx`
- do not depend on image-generation models

### 7.4 Refactor generate stage
Update the generate stage so it can run in a new mode:

- `render_mode=image_pdf` (legacy)
- `render_mode=pptx` (new)

Default for my refactor target can become `pptx`, but please decide based on least disruptive implementation.

### 7.5 Output artifacts
Expected artifacts after a successful run:

- `checkpoint_plan.json`
- `checkpoint_slide_spec.json`
- `slides.pptx`
- `state.json`
- logs

---

## 8. Phase 1 Acceptance Criteria

Phase 1 is complete only if:

1. The pipeline can generate a valid `.pptx`
2. The `.pptx` is editable in PowerPoint / WPS / LibreOffice
3. Existing plan-stage output can be reused
4. The change is incremental, not a total rewrite
5. The code is organized and readable
6. There is at least one simple test or demo path
7. The README or a short dev note explains the new flow

---

## 9. Phase 2 Preview (Do not fully implement yet unless Phase 1 is stable)

After Phase 1 is done, next step is to add typed pipeline state.

Suggested state fields:

- `input_files`
- `parsed_content`
- `summary_content`
- `presentation_plan`
- `slide_specs`
- `rendered_artifacts`
- `execution_meta`
- `error_info`

This state should later become the base for LangGraph orchestration.

---

## 10. Phase 3 Preview — Checkpoint Validation

Later we want:

- reject empty or invalid plan checkpoints
- reject malformed slide specs
- distinguish recoverable vs non-recoverable errors
- support restart from `plan`, `spec`, `render`, `validate`

But do not overbuild this in Phase 1.

---

## 11. Phase 4 Preview — Logging

Later we want structured logs for each stage:

- `run_id`
- `stage`
- `status`
- `latency_ms`
- `retry_count`
- `input_summary`
- `output_summary`
- `error_type`
- `error_message`

For now, light preparation is okay.

---

## 12. Phase 5 Preview — LangGraph Migration

Only after the system is stable:

Potential nodes:

- parse_node
- summary_node
- plan_node
- spec_build_node
- render_node
- validate_node
- retry_router

Potential state transitions:

- parse -> summary -> plan -> spec_build -> render -> validate
- failure -> retry / human_fix / abort

Do not implement this before the core PPTX path works.

---

## 13. Phase 6 Preview — Tool Use / Retry / Evaluation

Future tool candidates:

- `validate_slide_spec`
- `collect_references`
- `resolve_assets`
- `render_pptx`
- `check_pptx_integrity`

Future evaluation metrics:

- structural completeness
- reference coverage
- slide count consistency
- render success rate
- retry success rate
- editability / openability of pptx

Again: do not overbuild this now.

---

## 14. What I Want From You Right Now

Please do the following in order:

1. Inspect the current code structure carefully
2. Propose the smallest Phase 1 implementation plan
3. List the exact files you will modify / add
4. Explain any dependency changes
5. Implement only Phase 1
6. Keep the patch as small and clean as possible
7. After implementation, summarize:
   - what changed
   - what still remains
   - what the next minimal step should be

---

## 15. Important Engineering Preferences

Please follow these preferences:

- prefer explicit data structures over loose dict chains
- prefer deterministic rendering over prompt-only layout control
- prefer backward-compatible changes
- prefer small helper modules over giant god files
- prefer clear checkpoints over magical auto-recovery
- prefer code that is interview-explainable

---

## 16. Deliverables for This Iteration

For this iteration, I want:

1. A working editable PPTX generation path
2. Minimal new modules for slide schema / spec builder / pptx renderer
3. Integration into the existing pipeline
4. Brief usage instructions
5. A short note on next-step LangGraph migration

---

## 17. Please Avoid

- full project rewrite
- immediate LangGraph overhauls
- huge abstraction layers
- introducing too many dependencies
- changing unrelated modules
- trying to solve all future phases now

---

## 18. Expected Response Format

Please respond with:

1. Codebase understanding
2. Minimal implementation plan
3. File change list
4. Risks / assumptions
5. Implementation
6. Validation instructions
7. Next-step recommendation

If something in the repo structure differs from my assumptions, adapt the plan based on the actual code.