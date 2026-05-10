# paper2ppt

[English](README.md) | [中文](README.zh-CN.md)

paper2ppt converts academic PDF papers into editable PowerPoint decks, matching speaker scripts, and an optional detailed Beamer/TeX sidecar deck.

The current project goal is practical paper presentation generation: reuse the paper's original figures and tables, use only text LLMs for planning and writing, render native editable `.pptx` slides, and keep a lightweight QA/repair loop around the output.

This project is derived from [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides). It keeps the upstream PDF parsing, extraction, checkpoint, and paper-processing ideas, while replacing the final image-generation slide path with a native PPTX workflow.

## Current Status

The project now supports:

- Editable PowerPoint output: `slides.pptx`.
- A matching narration draft: `speaker_script.md`.
- A detailed Beamer/TeX sidecar: `detailed_slides.tex` and, when `pdflatex` is available, `detailed_slides.pdf`.
- LangChain/LangGraph-based text LLM orchestration.
- Default text model configuration using `gpt-5-mini`.
- Optional exact slide count with `--slides`.
- Section-aware decks with title page, contents page, section dividers, key-message blocks, numbered point layouts, compact metric cards, source figures, and tables.
- Lightweight PPTX layout QA and automatic repair.
- Deterministic fallback generation with `PPTX_FORCE_DETERMINISTIC=1` for cheap reruns from existing checkpoints.

The most recent visual iteration focused on making the generated deck look like a real presentation:

- Added a proper title page with title, authors, context/date, and summary tiles.
- Added a contents page with meaningful section progress lines.
- Added section divider pages.
- Reworked normal slides into title bar + key message + numbered points.
- Removed meaningless tiny connector marks beside numbered bullets.
- Restored useful decorative bars and tiles when they carry information.
- Improved bullet rendering so points try to show a short claim plus a complete detail sentence instead of clipped ellipses.

## Recommended Test PDF

The current main local test paper is:

```text
test_papers/DeepSeek_V4.pdf
```

The latest checked output during development was generated under:

```text
outputs/DeepSeek_V4/paper/fast/slides_academic_medium_24slides/
```

The exact timestamped folder changes per run. A successful run should include:

```text
slides.pptx
speaker_script.md
detailed_slides.tex
detailed_slides.pdf
layout_qa.json
```

## How It Works

```text
PDF
 -> parsing and source asset extraction
 -> summary checkpoint
 -> content plan checkpoint
 -> LangGraph PPTX workflow
    -> source packet
    -> optional source-figure understanding
    -> text LLM deck curation
    -> slide spec validation
    -> native PPTX rendering
    -> layout QA and repair loop
    -> speaker script generation
    -> detailed Beamer/TeX sidecar generation
```

The generated PPTX is not a screenshot deck. It uses native PowerPoint text boxes, shapes, tables, and inserted source images, so it remains editable in PowerPoint.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer; Python 3.12 is recommended
- Conda or another Python environment manager
- A text-model API compatible with the OpenAI chat-completions interface

The project has been developed in a local conda environment named `paper2slides`, but the name is not required.

## Installation

```powershell
conda create -n paper2ppt python=3.12
conda activate paper2ppt
pip install -r requirements.txt
```

If you already have a suitable Python environment:

```powershell
pip install -r requirements.txt
```

## Configure the API

paper2ppt reads API settings from:

```text
paper2slides/.env
```

For public GitHub safety, only the template should be committed:

```text
paper2slides/.env.example
```

If setting up a new clone, create the local env file from the template:

```powershell
copy paper2slides\.env.example paper2slides\.env
```

In this local workspace, `paper2slides/.env` already exists and should not be uploaded.

Typical configuration:

```env
RAG_LLM_API_KEY=your_api_key_here
RAG_LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=gpt-5-mini
```

Important cost rule:

```env
LLM_MODEL=gpt-5-mini
PPTX_VISION_MODEL=gpt-5-mini
```

If model calls are not needed and you only want to rerender from existing checkpoints:

```env
PPTX_FORCE_DETERMINISTIC=1
```

Optional figure understanding:

```env
PPTX_ENABLE_FIGURE_ANALYSIS=1
PPTX_VISION_MODEL=gpt-5-mini
PPTX_MAX_FIGURE_ANALYSIS=5
```

This analyzes source paper figures. It does not generate new images.

## Run

Typical run:

```powershell
python -m paper2slides --input test_papers\DeepSeek_V4.pdf --output slides --style academic --length medium --slides 24 --fast
```

Cheap rerun from existing checkpoints:

```powershell
$env:PPTX_FORCE_DETERMINISTIC="1"
python -m paper2slides --input test_papers\DeepSeek_V4.pdf --output slides --style academic --length medium --slides 24 --fast --from-stage generate
```

Main options:

```text
--input       PDF file path
--output      slides
--style       academic or a custom style description
--length      short, medium, or long
--slides      exact target content-slide count; overrides --length
--fast        use direct parsing/query flow instead of full indexing
--from-stage  rag, summary, plan, or generate
--list        list previous outputs
--debug       print more logs
```

Dynamic slide count:

```text
short   roughly 8-12 content slides
medium  roughly 14-22 content slides
long    roughly 24-36 content slides
```

Use `--slides 24` or a similar explicit value for long papers that need fuller coverage.

## Output Files

Typical timestamped output folder:

```text
outputs/<project_name>/paper/fast/slides_academic_medium_24slides/<timestamp>/
```

Typical files:

```text
slides.pptx
speaker_script.md
detailed_slides.tex
detailed_slides.pdf
layout_qa.json
checkpoint_slide_spec.json
checkpoint_slide_spec_llm_raw.txt
```

Meaning:

- `slides.pptx`: editable PowerPoint deck.
- `speaker_script.md`: slide-by-slide narration draft.
- `detailed_slides.tex`: detailed Beamer/TeX deck.
- `detailed_slides.pdf`: compiled Beamer PDF when `pdflatex` is available.
- `layout_qa.json`: lightweight layout QA result.
- `checkpoint_slide_spec.json`: final structured slide specification.
- `checkpoint_slide_spec_llm_raw.txt`: raw LLM output when a curator call was used.

## Important Implementation Files

```text
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/pptx_qa.py
paper2slides/generator/slide_schema.py
paper2slides/generator/spec_builder.py
paper2slides/generator/detailed_tex.py
paper2slides/core/stages/generate_stage.py
paper2slides/core/paths.py
```

The user also downloaded another reference project locally:

```text
Paper2PPT-main/
```

It is useful as inspiration, especially for detailed TeX output, but it should not replace the current paper2ppt generation path.

## Test

```powershell
python -m unittest test_phase1_pptx.py
```

Quick syntax check without writing `__pycache__`:

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
python -c "import ast, pathlib; ast.parse(pathlib.Path('paper2slides/generator/pptx_renderer.py').read_text(encoding='utf-8')); print('AST OK')"
```

## Next Development Direction: ReAct / Plan-and-Solve

The current deck is visually much better, but content quality still needs a stronger closed loop. The next planned upgrade is to move from one-pass slide curation to an evaluation-driven agent loop:

```text
Plan-and-Solve
 -> generate structured slide plan
 -> require each point to contain claim, detail, evidence
 -> render PPTX
 -> critique with ReAct-style QA
 -> repair only failed slides
 -> rerender and recheck
```

Target checks:

- No empty visual components.
- No meaningless decorative elements.
- No clipped ellipses in deliverable text.
- Each numbered point should have a short claim and a complete explanatory sentence when possible.
- Metrics should have meaningful labels and values.
- Section/contents/title visual elements must carry real information.
- All model calls should use `gpt-5-mini`.

Suggested prompt for a new conversation:

```text
Please read README.md, README.zh-CN.md, and DEVELOPMENT_HISTORY.zh-CN.md first.

Then continue from the current paper2ppt project state. The current priority is to implement a ReAct / Plan-and-Solve closed loop for PPT generation:
1. Generate or repair slide specs so each numbered point has claim, detail, and evidence fields.
2. Add an evaluator that checks empty components, meaningless decorative marks, clipped ellipses, missing claim/detail pairs, metric label/value quality, and layout QA.
3. Add a repair loop that edits only failed slides and rerenders.
4. Keep all model calls on gpt-5-mini.
5. Use DeepSeek_V4.pdf as the main test PDF and rerun from --from-stage generate whenever possible.

Important: the user was very happy with the current visual style. Do not aggressively delete the cover summary tiles, contents progress lines, or section-divider bars; keep those layouts and make them more semantic through QA and repair.
```

## Troubleshooting

If the API call fails:

- Check `paper2slides/.env`.
- Check `RAG_LLM_BASE_URL`.
- Check whether the selected model supports the needed context length.

If the deck is too sparse or too dense:

- Try a different `--length`.
- Use `--slides 24` or another explicit count.
- Rerun from `--from-stage generate`.

If the endpoint is unstable or you want a cheap rerun:

- Set `PPTX_FORCE_DETERMINISTIC=1`.

If a slide looks crowded or clipped:

- Inspect `layout_qa.json`.
- Rerender previews from the saved PPTX if possible.

## Attribution

paper2ppt is derived from [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides). Keep the upstream attribution and license terms when redistributing or extending this project.
