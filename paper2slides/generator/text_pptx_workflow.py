"""
LLM-curated, text-model PPTX generation workflow.

Slides should be a presentation, not a transcript. This workflow uses
LangGraph to orchestrate a small deck-curation pipeline:

1. Build a compact source packet from the verbose content plan.
2. Ask a text LLM, via LangChain when available, to produce a concise deck spec.
3. Validate and repair the spec so each slide stays presentation-friendly.
4. Render an editable PPTX with source figures/tables from the paper.

No image-generation model is called. Figures are reused from the extracted
paper assets.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict

from .content_planner import ContentPlan
from .pptx_renderer import PptxRenderer
from .pptx_qa import inspect_pptx_layout
from .slide_schema import ImageBlock, MetricBlock, PresentationSpec, SlideSpec, TableBlock, TextBlock
from .spec_builder import build_presentation_spec

logger = logging.getLogger(__name__)


SaveJsonFunc = Callable[[Path, Dict[str, Any]], None]


class _PptxWorkflowState(TypedDict, total=False):
    plan: ContentPlan
    title: str
    source_plan_path: str
    spec_checkpoint_path: Path
    output_subdir: Path
    source_packet: Dict[str, Any]
    raw_llm_response: str
    figure_analyses: Dict[str, Any]
    spec: PresentationSpec
    qa_report_path: str
    qa_attempt: int
    qa_warnings: List[str]
    qa_repair_log: List[str]
    pptx_path: Path
    speaker_script_path: str
    validation_warnings: List[str]
    used_langgraph: bool
    used_langchain: bool
    llm_model: str


def run_text_pptx_workflow(
    plan: ContentPlan,
    output_subdir: Path,
    spec_checkpoint_path: Path,
    save_json: SaveJsonFunc,
    title: str = "Paper2Slides Presentation",
    source_plan_path: str = "",
) -> Dict[str, Any]:
    """Curate, validate, save, and render an editable PPTX from a content plan."""
    _load_package_env()
    initial_state: _PptxWorkflowState = {
        "plan": plan,
        "title": title,
        "source_plan_path": source_plan_path,
        "spec_checkpoint_path": spec_checkpoint_path,
        "output_subdir": output_subdir,
        "validation_warnings": [],
        "used_langgraph": False,
        "used_langchain": False,
    }

    graph_runner = _build_langgraph_runner(save_json)
    if graph_runner:
        logger.info("Running LLM-curated PPTX workflow with LangGraph")
        final_state = graph_runner(initial_state)
    else:
        logger.info("Running LLM-curated PPTX workflow without LangGraph")
        state = _prepare_packet_node(initial_state)
        state = _analyze_figures_node(state)
        state = _curate_spec_node(state)
        state = _validate_node(state)
        while True:
            state = _render_node(state, save_json)
            if _route_after_render(state) != "repair_spec":
                break
            state = _qa_repair_node(state)
        final_state = _speaker_script_node(state)

    spec = final_state["spec"]
    pptx_path = final_state["pptx_path"]
    return {
        "pptx_path": pptx_path,
        "spec": spec,
        "validation_warnings": final_state.get("validation_warnings", []),
        "used_langgraph": final_state.get("used_langgraph", False),
        "used_langchain": final_state.get("used_langchain", False),
        "llm_model": final_state.get("llm_model", ""),
        "qa_report_path": final_state.get("qa_report_path", ""),
        "speaker_script_path": final_state.get("speaker_script_path", ""),
    }


def _load_package_env() -> None:
    try:
        from dotenv import load_dotenv

        env_path = Path(__file__).resolve().parents[1] / ".env"
        load_dotenv(dotenv_path=env_path, override=False)
    except Exception:
        return


def _build_langgraph_runner(save_json: SaveJsonFunc) -> Optional[Callable[[_PptxWorkflowState], _PptxWorkflowState]]:
    """Return a LangGraph runner when langgraph is available."""
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return None

    def render_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
        return _render_node(state, save_json)

    def speaker_script_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
        return _speaker_script_node(state)

    graph = StateGraph(_PptxWorkflowState)
    graph.add_node("prepare_packet", _prepare_packet_node)
    graph.add_node("analyze_figures", _analyze_figures_node)
    graph.add_node("curate_spec", _curate_spec_node)
    graph.add_node("validate", _validate_node)
    graph.add_node("render", render_node)
    graph.add_node("repair_spec", _qa_repair_node)
    graph.add_node("speaker_script", speaker_script_node)
    graph.set_entry_point("prepare_packet")
    graph.add_edge("prepare_packet", "analyze_figures")
    graph.add_edge("analyze_figures", "curate_spec")
    graph.add_edge("curate_spec", "validate")
    graph.add_edge("validate", "render")
    graph.add_conditional_edges(
        "render",
        _route_after_render,
        {
            "repair_spec": "repair_spec",
            "speaker_script": "speaker_script",
        },
    )
    graph.add_edge("repair_spec", "render")
    graph.add_edge("speaker_script", END)
    app = graph.compile()

    def _runner(state: _PptxWorkflowState) -> _PptxWorkflowState:
        state = {**state, "used_langgraph": True}
        result = app.invoke(state)
        result["used_langgraph"] = True
        return result

    return _runner


def _prepare_packet_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
    plan = state["plan"]
    source_packet = {
        "deck_title": state.get("title") or "Paper2Slides Presentation",
        "target": {
            "principle": "presentation-first, balanced density, visual-led",
            "max_bullets_per_slide": 4,
            "max_words_per_bullet": 18,
            "max_visuals_per_slide": 2,
        },
        "slides": [_section_to_packet(section) for section in plan.sections],
        "figures": [_figure_to_packet(fig_id, fig) for fig_id, fig in plan.figures_index.items()],
        "tables": [_table_to_packet(table_id, table) for table_id, table in plan.tables_index.items()],
        "metadata": plan.metadata,
    }
    return {**state, "source_packet": source_packet}


def _analyze_figures_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
    """Optionally ask a vision-capable text model to describe source figures."""
    enabled = os.getenv("PPTX_ENABLE_FIGURE_ANALYSIS", "1").strip().lower() not in {"0", "false", "no"}
    if not enabled:
        return {**state, "figure_analyses": {}}

    figures = state["source_packet"].get("figures", [])[: int(os.getenv("PPTX_MAX_FIGURE_ANALYSIS", "5"))]
    if not figures:
        return {**state, "figure_analyses": {}}

    try:
        analyses = _call_figure_analysis_llm(figures)
    except Exception as exc:
        logger.warning(f"Figure analysis failed; continuing with captions only: {exc}")
        analyses = {}

    enriched_figures = []
    for fig in state["source_packet"].get("figures", []):
        analysis = analyses.get(fig.get("figure_id", ""), {})
        enriched_figures.append({**fig, "visual_analysis": analysis})

    packet = {**state["source_packet"], "figures": enriched_figures}
    return {**state, "source_packet": packet, "figure_analyses": analyses}


def _curate_spec_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
    packet = state["source_packet"]
    prompt = _build_curation_prompt(packet)
    raw_response, used_langchain, model = _call_deck_curator_llm(prompt)
    spec = _parse_llm_spec(raw_response, state["plan"], state.get("source_plan_path", ""))
    return {
        **state,
        "raw_llm_response": raw_response,
        "spec": spec,
        "used_langchain": used_langchain,
        "llm_model": model,
    }


def _validate_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
    spec = state.get("spec") or _fallback_compact_spec(state["plan"], state.get("source_plan_path", ""))
    warnings = list(state.get("validation_warnings", []))

    if not spec.slides:
        spec = _fallback_compact_spec(state["plan"], state.get("source_plan_path", ""))
        warnings.append("LLM produced no slides; used compact fallback deck.")

    valid_figure_paths = {
        str(Path(fig.image_path))
        for fig in state["plan"].figures_index.values()
        if getattr(fig, "image_path", "")
    }

    for index, slide in enumerate(spec.slides, start=1):
        slide.slide_id = slide.slide_id or f"slide_{index:02d}"
        slide.title = _clean_text(slide.title) or f"Slide {index}"
        slide.takeaway = _limit_words(_clean_text(slide.takeaway), 22)
        slide.layout = slide.layout or _infer_layout(slide)

        slide.text_blocks = _compact_text_blocks(slide.text_blocks)
        slide.metric_blocks = _compact_metric_blocks(slide.metric_blocks)
        if not slide.metric_blocks:
            slide.metric_blocks = _extract_metrics_from_slide(slide)[:4]

        if slide.section_type == "opening" and not slide.image_blocks:
            cover_image = _pick_cover_figure(state["plan"])
            if cover_image:
                slide.image_blocks.append(cover_image)

        if not slide.text_blocks and not slide.image_blocks and not slide.table_blocks:
            slide.text_blocks = [TextBlock(text="Key idea unavailable.", role="bullet")]
            warnings.append(f"{slide.slide_id} had no content; inserted placeholder.")

        repaired_images = []
        for block in slide.image_blocks[:2]:
            if block.path and Path(block.path).exists():
                repaired_images.append(block)
            elif str(Path(block.path)) in valid_figure_paths:
                repaired_images.append(block)
            else:
                block.placeholder_text = block.placeholder_text or block.title or "Original figure"
                repaired_images.append(block)
        slide.image_blocks = repaired_images
        slide.table_blocks = slide.table_blocks[:1]
        if slide.layout in {"section", "auto"} and not slide.image_blocks and not slide.table_blocks:
            slide.layout = "metric_focus" if slide.metric_blocks else "statement"

    spec.metadata = {
        **(spec.metadata or {}),
        "generator": "llm_curated_text_pptx",
        "used_langgraph": state.get("used_langgraph", False),
        "used_langchain": state.get("used_langchain", False),
        "llm_model": state.get("llm_model", ""),
        "figure_analysis_count": len(state.get("figure_analyses", {})),
    }
    return {**state, "spec": spec, "validation_warnings": warnings}


def _render_node(state: _PptxWorkflowState, save_json: SaveJsonFunc) -> _PptxWorkflowState:
    output_subdir = state["output_subdir"]
    output_subdir.mkdir(parents=True, exist_ok=True)

    spec = state["spec"]
    spec_checkpoint_path = state["spec_checkpoint_path"]
    save_json(spec_checkpoint_path, spec.to_dict())

    raw_response = state.get("raw_llm_response", "")
    if raw_response:
        raw_path = spec_checkpoint_path.parent / "checkpoint_slide_spec_llm_raw.txt"
        raw_path.write_text(raw_response, encoding="utf-8")

    pptx_path = output_subdir / "slides.pptx"
    renderer = PptxRenderer()
    renderer.render(spec, pptx_path)

    qa_result = inspect_pptx_layout(pptx_path)
    qa_path = output_subdir / "layout_qa.json"
    save_json(qa_path, qa_result.to_dict())
    if qa_result.warnings:
        for warning in qa_result.warnings[:12]:
            logger.warning(f"  QA: {warning}")

    return {
        **state,
        "pptx_path": pptx_path,
        "qa_report_path": str(qa_path),
        "qa_warnings": qa_result.warnings,
    }


def _route_after_render(state: _PptxWorkflowState) -> str:
    max_attempts = int(os.getenv("PPTX_QA_MAX_REPAIR_ATTEMPTS", "2"))
    warnings = state.get("qa_warnings", [])
    attempt = state.get("qa_attempt", 0)
    if warnings and attempt < max_attempts:
        return "repair_spec"
    return "speaker_script"


def _qa_repair_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
    """Shrink risky slide content or switch layouts based on PPTX QA feedback."""
    spec = state["spec"]
    warnings = state.get("qa_warnings", [])
    attempt = state.get("qa_attempt", 0) + 1
    repair_log = list(state.get("qa_repair_log", []))

    affected_slides = _slides_from_qa_warnings(warnings)
    if not affected_slides:
        affected_slides = set(range(1, len(spec.slides) + 1))

    for slide_index in sorted(affected_slides):
        if slide_index < 1 or slide_index > len(spec.slides):
            continue
        slide = spec.slides[slide_index - 1]
        before_layout = slide.layout
        before_bullets = len(slide.text_blocks)

        slide.title = _limit_words(slide.title, 8)
        slide.takeaway = _limit_words(slide.takeaway, 12)
        slide.text_blocks = [
            TextBlock(text=_limit_words(block.text, 10), role=block.role, bullet_level=block.bullet_level)
            for block in slide.text_blocks[:3]
        ]
        slide.metric_blocks = [
            MetricBlock(
                label=_limit_words(metric.label, 3),
                value=_limit_words(metric.value, 3),
                note=_limit_words(metric.note, 5),
            )
            for metric in _compact_metric_blocks(slide.metric_blocks)[:3]
        ]
        slide.table_blocks = [_compact_table_block(slide.table_blocks[0])] if slide.table_blocks else []
        for image in slide.image_blocks:
            image.caption = _limit_words(image.caption, 10)
            image.placeholder_text = _limit_words(image.placeholder_text, 8)

        if slide.layout in {"visual_left", "visual_right"} and len(slide.image_blocks) > 1:
            slide.image_blocks = slide.image_blocks[:1]
        if slide.layout in {"statement", "metric_focus"} and not slide.metric_blocks and slide.image_blocks:
            slide.layout = "visual_right"
        if slide.layout == "table_focus" and not slide.table_blocks and slide.image_blocks:
            slide.layout = "visual_right"

        repair_log.append(
            f"attempt {attempt}: slide {slide_index} compressed "
            f"({before_layout}->{slide.layout}, bullets {before_bullets}->{len(slide.text_blocks)})"
        )

    warnings = list(state.get("validation_warnings", []))
    warnings.append(f"PPTX QA repair attempt {attempt}: adjusted {len(affected_slides)} slide(s).")
    spec.metadata = {
        **(spec.metadata or {}),
        "qa_repair_attempts": attempt,
        "qa_repair_log": repair_log,
    }
    return {
        **state,
        "spec": spec,
        "qa_attempt": attempt,
        "qa_repair_log": repair_log,
        "validation_warnings": warnings,
    }


def _speaker_script_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
    output_subdir = state["output_subdir"]
    script_path = output_subdir / "speaker_script.md"
    script = _build_speaker_script(state["spec"], state.get("qa_repair_log", []))
    script_path.write_text(script, encoding="utf-8")
    logger.info(f"  Speaker script: {script_path}")
    return {**state, "speaker_script_path": str(script_path)}


def _slides_from_qa_warnings(warnings: List[str]) -> set[int]:
    slide_numbers: set[int] = set()
    for warning in warnings:
        match = re.search(r"slide\s+(\d+)", warning, flags=re.IGNORECASE)
        if match:
            slide_numbers.add(int(match.group(1)))
    return slide_numbers


def _compact_table_block(table: TableBlock) -> TableBlock:
    rows = table.rows[:5]
    compact_rows = []
    for row in rows:
        compact_rows.append([_limit_words(str(cell), 6) for cell in row[:4]])
    return TableBlock(
        title=_limit_words(table.title, 5),
        rows=compact_rows,
        caption=_limit_words(table.caption, 12),
    )


def _build_speaker_script(spec: PresentationSpec, repair_log: List[str]) -> str:
    lines = [
        f"# {spec.title or 'Paper2Slides Presentation'}",
        "",
        "> This speaking script is generated from the final repaired slide specification.",
        "",
    ]
    if repair_log:
        lines.extend(["## Layout QA adjustments", ""])
        lines.extend(f"- {item}" for item in repair_log)
        lines.append("")

    for index, slide in enumerate(spec.slides, start=1):
        title = _clean_text(slide.title) or f"Slide {index}"
        lines.extend([f"## Slide {index}: {title}", ""])
        if slide.takeaway:
            lines.extend([f"**Key message:** {_clean_text(slide.takeaway)}", ""])

        script_parts = []
        if slide.takeaway:
            script_parts.append(_as_sentence(_clean_text(slide.takeaway)))
        if slide.text_blocks:
            script_parts.append(
                "The main points are "
                + "; ".join(_clean_text(block.text).rstrip(".") for block in slide.text_blocks[:3])
                + "."
            )
        if slide.metric_blocks:
            metric_text = "; ".join(
                f"{_clean_text(metric.label) or 'metric'}: {_clean_text(metric.value)}" for metric in slide.metric_blocks[:3]
            )
            script_parts.append(f"The numbers to emphasize are {metric_text}.")
        if slide.image_blocks:
            visual_text = "; ".join(
                _clean_text(image.title or image.caption or "source figure") for image in slide.image_blocks[:2]
            )
            script_parts.append(f"Use the visual evidence on this slide to point to {visual_text}.")
        if slide.table_blocks:
            table = slide.table_blocks[0]
            table_title = _clean_text(table.title) or "the table"
            script_parts.append(f"Walk through {table_title} only at the level needed to support the message.")

        if not script_parts:
            script_parts.append("Briefly state the slide message and move on.")

        lines.extend(["**Suggested narration:**", ""])
        lines.append(" ".join(part for part in script_parts if part))
        lines.append("")

        if slide.notes:
            lines.extend(["**Source trace:**", ""])
            lines.extend(f"- {_clean_text(note)}" for note in slide.notes)
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def _as_sentence(text: str) -> str:
    text = _clean_text(text).strip()
    if not text:
        return ""
    if text[-1] in ".!?":
        return text
    return text + "."


def _build_curation_prompt(packet: Dict[str, Any]) -> str:
    packet_json = json.dumps(packet, ensure_ascii=False)
    return f"""You are a senior presentation designer and research communicator.

Turn the verbose paper plan below into a concise, presentation-first PPTX spec.

Rules:
- Use ONLY the provided source content, tables, and figures.
- Do NOT create or request generated images.
- Prefer source figures/tables as the center of a slide. Text explains the visual.
- Each slide must have one message.
- Use 2-4 bullets per slide depending on importance.
- Each bullet must be <= 18 words.
- Do not paste paragraphs from the source.
- Use a short but complete takeaway, <= 22 words.
- Vary density: section/closing slides can be sparse; method/results slides should include enough context to be self-explanatory.
- Extract 2-4 important metrics for metric-led or otherwise empty slides.
- Only output a metric when it has a visible numeric/value field; otherwise turn that idea into a bullet.
- Build comparison/metric tables when they communicate better than text.
- Avoid fully empty-looking slides: if no figure/table exists, include metrics or a compact comparison table.
- The cover should use a strong source figure when one is relevant.
- Keep formulas only if essential, and make them short.
- Recommended layouts: cover, statement, metric_focus, visual_right, visual_left, table_focus, quote, closing.

Return JSON only, no markdown fences:
{{
  "title": "deck title",
  "slides": [
    {{
      "slide_id": "slide_01",
      "title": "short title",
      "layout": "cover|section|visual_right|visual_left|table_focus|quote|closing",
      "section_type": "opening|content|ending",
      "takeaway": "one-sentence message",
      "bullets": ["short bullet", "short bullet"],
      "metrics": [
        {{"label": "Success rate", "value": "5.36%", "note": "overall"}}
      ],
      "figures": [{{"figure_id": "Figure 1", "caption": "short caption"}}],
      "tables": [
        {{
          "title": "table title",
          "caption": "what the table proves",
          "rows": [["Metric", "Value"], ["Success rate", "5.36%"]]
        }}
      ],
      "speaker_notes": ["optional source trace"]
    }}
  ]
}}

Source packet:
{packet_json}
"""


def _call_deck_curator_llm(prompt: str) -> tuple[str, bool, str]:
    api_key = os.getenv("RAG_LLM_API_KEY", "")
    base_url = os.getenv("RAG_LLM_BASE_URL") or None
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    max_tokens = int(os.getenv("PPTX_LLM_MAX_TOKENS", os.getenv("RAG_LLM_MAX_TOKENS", "8000")))

    if not api_key:
        raise RuntimeError("RAG_LLM_API_KEY is required for LLM-curated PPTX generation.")

    try:
        from langchain_openai import ChatOpenAI

        logger.info(f"Calling deck curator LLM through LangChain: {model}")
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=0.2,
        )
        response = llm.invoke(prompt)
        return str(response.content or ""), True, model
    except Exception as exc:
        logger.warning(f"LangChain curator call failed, falling back to OpenAI SDK: {exc}")
        from openai import OpenAI

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content or "", False, model


def _call_figure_analysis_llm(figures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze extracted paper figures with a vision-capable text model."""
    import base64

    api_key = os.getenv("RAG_LLM_API_KEY", "")
    base_url = os.getenv("RAG_LLM_BASE_URL") or None
    model = os.getenv("PPTX_VISION_MODEL", os.getenv("LLM_MODEL", "gpt-4o-mini"))
    if not api_key:
        return {}

    content: List[Dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Analyze these source paper figures for slide design. Return JSON only: "
                "{\"figures\":[{\"figure_id\":\"Figure 1\",\"visual_summary\":\"...\","
                "\"best_slide_role\":\"cover|method|results|diagnostic|support\","
                "\"key_labels\":[\"...\"],\"design_note\":\"...\"}]}"
            ),
        }
    ]

    included = 0
    for fig in figures:
        path = Path(fig.get("path", ""))
        if not path.exists():
            continue
        suffix = path.suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg"
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("utf-8")
        content.append({"type": "text", "text": f"{fig.get('figure_id')}: {fig.get('caption', '')}"})
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
        included += 1

    if not included:
        return {}

    logger.info(f"Calling figure analysis LLM for {included} source figures: {model}")
    from openai import OpenAI

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        max_tokens=int(os.getenv("PPTX_FIGURE_ANALYSIS_MAX_TOKENS", "2000")),
    )
    raw = response.choices[0].message.content or ""
    data = _extract_json(raw)
    result: Dict[str, Any] = {}
    for item in data.get("figures", []):
        fig_id = item.get("figure_id")
        if fig_id:
            result[fig_id] = item
    return result


def _parse_llm_spec(raw_response: str, plan: ContentPlan, source_plan_path: str) -> PresentationSpec:
    data = _extract_json(raw_response)
    if not data:
        logger.warning("Deck curator did not return valid JSON; using compact fallback.")
        return _fallback_compact_spec(plan, source_plan_path)

    figure_index = plan.figures_index
    slides: List[SlideSpec] = []
    for index, item in enumerate(data.get("slides", []), start=1):
        bullets = item.get("bullets") or item.get("text_blocks") or []
        text_blocks = [
            TextBlock(text=_limit_words(str(bullet), 18), role="bullet", bullet_level=0)
            for bullet in bullets
            if _clean_text(str(bullet))
        ][:4]

        metric_blocks = []
        for metric in item.get("metrics", [])[:4]:
            metric_blocks.append(
                MetricBlock(
                    label=_limit_words(metric.get("label", ""), 5),
                    value=_limit_words(metric.get("value", ""), 6),
                    note=_limit_words(metric.get("note", ""), 10),
                )
            )

        image_blocks = []
        for fig_ref in item.get("figures", [])[:2]:
            fig_id = fig_ref.get("figure_id", "")
            fig = figure_index.get(fig_id)
            if fig:
                image_blocks.append(
                    ImageBlock(
                        path=fig.image_path,
                        title=fig.figure_id,
                        caption=_limit_words(fig_ref.get("caption") or fig.caption or "", 18),
                        placeholder_text=fig_ref.get("focus", ""),
                    )
                )
            elif fig_id:
                image_blocks.append(ImageBlock(path="", title=fig_id, placeholder_text=fig_id))

        table_blocks = []
        for table in item.get("tables", [])[:1]:
            rows = table.get("rows") or []
            if rows:
                table_blocks.append(
                    TableBlock(
                        title=_clean_text(table.get("title", "")) or "Key Data",
                        rows=[[str(cell) for cell in row[:4]] for row in rows[:6]],
                        caption=_limit_words(table.get("caption", ""), 22),
                    )
                )

        slides.append(
            SlideSpec(
                slide_id=item.get("slide_id", f"slide_{index:02d}"),
                title=item.get("title", f"Slide {index}"),
                layout=item.get("layout", "auto"),
                takeaway=item.get("takeaway", ""),
                text_blocks=text_blocks,
                image_blocks=image_blocks,
                table_blocks=table_blocks,
                metric_blocks=metric_blocks,
                notes=item.get("speaker_notes", []),
                section_type=item.get("section_type", "content"),
            )
        )

    return PresentationSpec(
        title=data.get("title") or "Paper2Slides Presentation",
        slides=slides,
        metadata={"curation": "llm"},
        source_plan_path=source_plan_path or None,
    )


def _fallback_compact_spec(plan: ContentPlan, source_plan_path: str = "") -> PresentationSpec:
    base = build_presentation_spec(plan, title="Paper2Slides Presentation", source_plan_path=source_plan_path)
    for slide in base.slides:
        slide.layout = _infer_layout(slide)
        slide.takeaway = _limit_words(slide.text_blocks[0].text if slide.text_blocks else slide.title, 22)
        slide.text_blocks = _compact_text_blocks(slide.text_blocks)
        slide.metric_blocks = _extract_metrics_from_slide(slide)[:4]
    base.metadata = {**(base.metadata or {}), "curation": "fallback_compact"}
    return base


def _section_to_packet(section) -> Dict[str, Any]:
    return {
        "id": section.id,
        "title": section.title,
        "type": section.section_type,
        "content": _clean_text(section.content)[:1400],
        "tables": [ref.__dict__ for ref in section.tables],
        "figures": [ref.__dict__ for ref in section.figures],
    }


def _figure_to_packet(fig_id: str, fig) -> Dict[str, Any]:
    return {
        "figure_id": fig_id,
        "caption": _clean_text(getattr(fig, "caption", "") or "")[:500],
        "path": getattr(fig, "image_path", ""),
    }


def _table_to_packet(table_id: str, table) -> Dict[str, Any]:
    return {
        "table_id": table_id,
        "caption": _clean_text(getattr(table, "caption", "") or "")[:300],
        "html_preview": _clean_text(getattr(table, "html_content", "") or "")[:1000],
    }


def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    json_text = fenced.group(1).strip() if fenced else text
    if not json_text.startswith("{"):
        match = re.search(r"\{.*\}", json_text, re.DOTALL)
        json_text = match.group(0) if match else json_text
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as exc:
        logger.warning(f"Failed to parse deck curator JSON: {exc}")
        return {}


def _compact_text_blocks(blocks: List[TextBlock]) -> List[TextBlock]:
    compact: List[TextBlock] = []
    seen = set()
    for block in blocks:
        parts = _split_into_points(block.text)
        for part in parts:
            point = _limit_words(part, 18)
            if not point or point.lower() in seen:
                continue
            compact.append(TextBlock(text=point, role="bullet", bullet_level=0))
            seen.add(point.lower())
            if len(compact) >= 4:
                return compact
    return compact


def _compact_metric_blocks(blocks: List[MetricBlock]) -> List[MetricBlock]:
    compact: List[MetricBlock] = []
    for metric in blocks[:4]:
        label = _limit_words(_clean_text(metric.label), 4)
        value = _limit_words(_clean_text(metric.value), 5)
        note = _limit_words(_clean_text(metric.note), 8)
        if not value:
            value = _first_metric_value(" ".join([label, note]))
        if not value:
            continue
        compact.append(MetricBlock(label=label or "Key metric", value=value, note=note))
    return compact


def _extract_metrics_from_slide(slide: SlideSpec) -> List[MetricBlock]:
    text = " ".join([slide.takeaway, slide.title] + [block.text for block in slide.text_blocks])
    candidates = re.findall(r"(?<![A-Za-z0-9])(?:\d+(?:\.\d+)?%|r\s*=\s*-?\d+(?:\.\d+)?|p\s*=\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?)", text)
    metrics: List[MetricBlock] = []
    seen = set()
    for value in candidates:
        clean_value = value.replace(" ", "")
        if clean_value in seen:
            continue
        seen.add(clean_value)
        label = _metric_label_for_value(clean_value, text)
        metrics.append(MetricBlock(label=label, value=clean_value))
        if len(metrics) >= 4:
            break
    return metrics


def _first_metric_value(text: str) -> str:
    match = re.search(r"(?<![A-Za-z0-9])(?:\d+(?:\.\d+)?%|r\s*=\s*-?\d+(?:\.\d+)?|p\s*=\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?)", text or "")
    return match.group(0).replace(" ", "") if match else ""


def _metric_label_for_value(value: str, context: str) -> str:
    lower = context.lower()
    if "%" in value and "success" in lower:
        return "Success rate"
    if "r=" in value.lower():
        return "Correlation"
    if "p=" in value.lower():
        return "p-value"
    if "attempt" in lower:
        return "Attempt"
    if "guess" in lower:
        return "Guesses"
    if "accuracy" in lower:
        return "Accuracy"
    return "Key number"


def _pick_cover_figure(plan: ContentPlan) -> Optional[ImageBlock]:
    if not plan.figures_index:
        return None
    preferred_terms = ("pipeline", "overview", "wordle", "heatmap", "accuracy")
    figures = list(plan.figures_index.values())
    figures.sort(
        key=lambda fig: any(term in ((fig.caption or "") + " " + fig.figure_id).lower() for term in preferred_terms),
        reverse=True,
    )
    fig = figures[0]
    return ImageBlock(
        path=fig.image_path,
        title=fig.figure_id,
        caption=_limit_words(fig.caption or "", 18),
        placeholder_text=fig.figure_id,
    )


def _split_into_points(text: str) -> List[str]:
    text = _clean_text(text)
    if not text:
        return []
    separators = r"(?:\s+[0-9]\)|\s+[0-9]\.\s+|;\s+|。|；|\. (?=[A-Z0-9]))"
    parts = [part.strip(" -:") for part in re.split(separators, text) if part.strip(" -:")]
    return parts or [text]


def _limit_words(text: str, max_words: int) -> str:
    text = _clean_text(text)
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(" ,;:") + "..."


def _clean_text(text: str) -> str:
    cleaned = str(text or "")
    replacements = {
        "→": "->",
        "↔": "<->",
        "≈": "~",
        "—": "-",
        "–": "-",
        "бк": "-",
        "鈥?": "-",
        "鈥檚": "'s",
        "鈥淭": '"T',
        "鈫?": "->",
        "鈫扽": "->Y",
        "鈫扜": "->G",
        "鈮?": "~",
        "鈫抯uccess": "->success",
        "鈫扽ellow": "->Yellow",
        "鈫扜reen": "->Green",
        "Gray鈫扽ellow": "Gray->Yellow",
        "Gray鈫扜reen": "Gray->Green",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return re.sub(r"\s+", " ", cleaned).strip()


def _infer_layout(slide: SlideSpec) -> str:
    if slide.section_type == "opening":
        return "cover"
    if slide.section_type == "ending":
        return "closing"
    if slide.table_blocks:
        return "table_focus"
    if slide.image_blocks:
        return "visual_right"
    if slide.metric_blocks:
        return "metric_focus"
    return "statement"
