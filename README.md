# paper2ppt

[English](README.md) | [中文](README.zh-CN.md)

paper2ppt converts academic PDF papers into editable PowerPoint decks and matching speaker scripts. It is designed for a practical workflow: give it a PDF, let a text LLM curate the story, reuse the paper's original figures, and receive a native `.pptx` plus a readable narration draft.

paper2ppt is derived from [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides). This project keeps the upstream parsing, extraction, checkpoint, and paper-processing ideas, while replacing the final image-generation slide path with a text-model-driven native PPTX workflow.

## Features

- Convert a PDF paper into an editable PowerPoint file.
- Generate a matching `speaker_script.md` for presentation narration.
- Reuse figures and tables extracted from the original paper.
- Use LangChain/LangGraph for text-LLM deck curation and workflow orchestration.
- Avoid text-to-image generation for slide creation.
- Run lightweight PPTX layout QA and automatic repair before final output.
- Save intermediate checkpoints so later runs can resume from a selected stage.

## How It Works

```text
PDF
 -> paper parsing and asset extraction
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
```

The generated deck is not a set of screenshots. It uses native PowerPoint text boxes, shapes, tables, and inserted source images, so you can keep editing it in PowerPoint.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer, Python 3.12 recommended
- Conda or another Python environment manager
- A text-model API compatible with the OpenAI chat-completions interface

The project was developed and tested in a conda environment named `paper2slides`, but the environment name is not important.

## Installation

Clone the repository, enter the project directory, then create an environment:

```powershell
conda create -n paper2ppt python=3.12
conda activate paper2ppt
pip install -r requirements.txt
```

If you already have an environment, install the dependencies inside it:

```powershell
pip install -r requirements.txt
```

## Configure the API

paper2ppt reads API settings from `paper2slides/.env`.

Create it from the public template:

```powershell
copy paper2slides\.env.example paper2slides\.env
```

Then edit `paper2slides/.env`:

```env
RAG_LLM_API_KEY=your_api_key_here
RAG_LLM_BASE_URL=https://api.example.com/v1
LLM_MODEL=gpt-5-mini
```

Optional figure understanding can be enabled with a vision-capable text model. This step analyzes the original paper figures; it does not generate new images.

```env
PPTX_ENABLE_FIGURE_ANALYSIS=1
PPTX_VISION_MODEL=gpt-5-mini
PPTX_MAX_FIGURE_ANALYSIS=5
```

The committed file is `paper2slides/.env.example`. Your real `paper2slides/.env` should remain local.

## Run Your First Conversion

Use any local PDF path:

```powershell
python -m paper2slides --input path\to\paper.pdf --output slides --style academic --length medium --fast
```

Example with a local test paper:

```powershell
python -m paper2slides --input test_papers\AGI_Is_Coming_Wordle.pdf --output slides --style academic --length medium --fast
```

Main options:

```text
--input       PDF file path
--output      slides
--style       academic or a custom style description
--length      short, medium, or long
--fast        use direct parsing/query flow instead of full indexing
--from-stage  rag, summary, plan, or generate
--list        list previous outputs
--debug       print more logs
```

## Output Files

After a successful run, paper2ppt creates a timestamped output folder under `outputs/`.

Typical files:

```text
slides.pptx
speaker_script.md
layout_qa.json
checkpoint_slide_spec.json
checkpoint_slide_spec_llm_raw.txt
```

What they mean:

- `slides.pptx`: the editable PowerPoint deck.
- `speaker_script.md`: slide-by-slide narration draft.
- `layout_qa.json`: lightweight layout QA result.
- `checkpoint_slide_spec.json`: the final structured slide specification.
- `checkpoint_slide_spec_llm_raw.txt`: raw deck-curation output from the LLM.

## Resume From a Later Stage

If the PDF has already been parsed and you only want to regenerate the PPTX and script, run:

```powershell
python -m paper2slides --input path\to\paper.pdf --output slides --style academic --length medium --fast --from-stage generate
```

This reuses previous extraction, summary, and planning checkpoints, then reruns the LangGraph PPTX workflow.

## Project Structure

```text
paper2slides/
  core/                 pipeline stages, paths, checkpoint flow
  generator/            slide planning, LangGraph workflow, PPTX renderer, QA
  prompts/              paper planning and extraction prompts
  rag/                  RAG client/query helpers inherited from upstream
  raganything/          document parsing layer inherited from upstream
  summary/              paper/general summarization and asset models
  utils/                logging and file helpers

README.md
README.zh-CN.md
DEVELOPMENT_HISTORY.zh-CN.md
requirements.txt
test_phase1_pptx.py
```

Important implementation files:

```text
paper2slides/generator/text_pptx_workflow.py
paper2slides/generator/pptx_renderer.py
paper2slides/generator/pptx_qa.py
paper2slides/generator/slide_schema.py
paper2slides/generator/content_planner.py
```

## Test

```powershell
python -m unittest test_phase1_pptx.py
```

You can also check the CLI:

```powershell
python -m paper2slides --help
```

## Troubleshooting

If the API call fails:

- Check `paper2slides/.env`.
- Check `RAG_LLM_BASE_URL`.
- Check whether your selected model supports the needed context length.

If the deck is too sparse or too dense:

- Try a different `--length`.
- Regenerate from `--from-stage generate`.
- Adjust the LLM model in `.env`.

If a slide looks crowded:

- Inspect `layout_qa.json`.
- Increase `PPTX_QA_MAX_REPAIR_ATTEMPTS` in `.env`.

## Attribution

paper2ppt is derived from [HKUDS/Paper2Slides](https://github.com/HKUDS/Paper2Slides). Please keep the upstream attribution and license terms when redistributing or extending this project.
