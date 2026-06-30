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
from typing import Any, Callable, Dict, Iterable, List, Optional, TypedDict

from .content_planner import ContentPlan
from .detailed_tex import generate_detailed_tex_deck
from .pptx_renderer import PptxRenderer
from .pptx_qa import evaluate_presentation_spec, inspect_pptx_layout
from .slide_schema import ImageBlock, MetricBlock, PresentationSpec, SlideSpec, TableBlock, TextBlock
from .spec_builder import build_presentation_spec

logger = logging.getLogger(__name__)
DEFAULT_PPTX_LLM_MODEL = "gpt-5-mini"


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
    qa_passed: bool
    qa_attempt: int
    qa_warnings: List[str]
    failed_slides: List[int]
    qa_repair_log: List[str]
    pptx_path: Path
    speaker_script_path: str
    validation_warnings: List[str]
    used_langgraph: bool
    used_langchain: bool
    llm_model: str
    style: str


def run_text_pptx_workflow(
    plan: ContentPlan,
    output_subdir: Path,
    spec_checkpoint_path: Path,
    save_json: SaveJsonFunc,
    title: str = "Paper2Slides Presentation",
    source_plan_path: str = "",
    style: str = "academic",
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
        "style": style,
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
    detailed_result: Dict[str, str] = {}
    try:
        detailed_result = generate_detailed_tex_deck(
            plan=plan,
            spec=spec,
            output_dir=output_subdir,
            title=spec.title or title,
        )
    except Exception as exc:
        logger.warning(f"Detailed TeX sidecar generation failed; continuing with PPTX output: {exc}")

    return {
        "pptx_path": pptx_path,
        "spec": spec,
        "validation_warnings": final_state.get("validation_warnings", []),
        "used_langgraph": final_state.get("used_langgraph", False),
        "used_langchain": final_state.get("used_langchain", False),
        "llm_model": final_state.get("llm_model", ""),
        "qa_report_path": final_state.get("qa_report_path", ""),
        "speaker_script_path": final_state.get("speaker_script_path", ""),
        "detailed_tex_path": detailed_result.get("detailed_tex_path", ""),
        "detailed_pdf_path": detailed_result.get("detailed_pdf_path", ""),
    }


def _load_package_env() -> None:
    try:
        from dotenv import load_dotenv

        env_path = Path(__file__).resolve().parents[1] / ".env"
        load_dotenv(dotenv_path=env_path, override=False)
    except Exception:
        return


def _get_pptx_llm_model() -> str:
    """Return the text model used by PPTX curation and repair metadata."""
    return (
        os.getenv("PPTX_LLM_MODEL")
        or os.getenv("LLM_MODEL")
        or DEFAULT_PPTX_LLM_MODEL
    ).strip()


def _get_figure_analysis_model() -> str:
    """Return the model used for optional source-figure understanding."""
    return (
        os.getenv("PPTX_VISION_MODEL")
        or os.getenv("PPTX_LLM_MODEL")
        or os.getenv("LLM_MODEL")
        or DEFAULT_PPTX_LLM_MODEL
    ).strip()


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
    if os.getenv("PPTX_FORCE_DETERMINISTIC", "").strip().lower() in {"1", "true", "yes"}:
        return {**state, "figure_analyses": {}}

    figures = state["source_packet"].get("figures", [])[: int(os.getenv("PPTX_MAX_FIGURE_ANALYSIS", "5"))]
    mode = os.getenv("PPTX_ENABLE_FIGURE_ANALYSIS", "auto").strip().lower()
    if mode in {"0", "false", "no", "off"}:
        return {**state, "figure_analyses": {}}
    if mode in {"1", "true", "yes", "on"}:
        enabled = True
    else:
        enabled = _should_auto_analyze_figures(figures)
    if not enabled:
        return {**state, "figure_analyses": {}}

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


def _should_auto_analyze_figures(figures: List[Dict[str, Any]]) -> bool:
    """Use figure analysis only when captions are too weak for reliable curation."""
    if not figures:
        return False
    weak_count = 0
    generic_terms = {"figure", "image", "example", "overview", "result", "diagram"}
    for fig in figures:
        caption = _clean_text(fig.get("caption", ""))
        words = caption.split()
        if len(caption) < 80 or len(words) < 10:
            weak_count += 1
            continue
        meaningful_words = [word.strip(".,:;()[]").lower() for word in words[:8]]
        if meaningful_words and all(word in generic_terms for word in meaningful_words[:3]):
            weak_count += 1
    return weak_count >= max(1, len(figures) // 2)


def _curate_spec_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
    packet = state["source_packet"]
    prompt = _build_curation_prompt(packet)
    warnings = list(state.get("validation_warnings", []))
    if os.getenv("PPTX_FORCE_DETERMINISTIC", "").strip().lower() in {"1", "true", "yes"}:
        checkpoint = state.get("spec_checkpoint_path")
        if checkpoint and checkpoint.exists():
            try:
                spec = PresentationSpec.from_dict(json.loads(checkpoint.read_text(encoding="utf-8")))
                warnings.append("PPTX_FORCE_DETERMINISTIC=1; reused existing slide spec checkpoint.")
                return {
                    **state,
                    "raw_llm_response": "",
                    "spec": spec,
                    "used_langchain": False,
                    "llm_model": _get_pptx_llm_model(),
                    "validation_warnings": warnings,
                }
            except Exception as exc:
                warnings.append(f"Existing slide spec checkpoint could not be reused: {exc}")
        warnings.append("PPTX_FORCE_DETERMINISTIC=1; used deterministic fallback slide spec.")
        return {
            **state,
            "raw_llm_response": "",
            "spec": _fallback_compact_spec(state["plan"], state.get("source_plan_path", "")),
            "used_langchain": False,
            "llm_model": _get_pptx_llm_model(),
            "validation_warnings": warnings,
        }

    try:
        raw_response, used_langchain, model = _call_deck_curator_llm(prompt)
        spec = _parse_llm_spec(raw_response, state["plan"], state.get("source_plan_path", ""))
    except Exception as exc:
        logger.warning(f"Deck curator LLM failed; using deterministic fallback spec: {exc}")
        raw_response = ""
        used_langchain = False
        model = _get_pptx_llm_model()
        spec = _fallback_compact_spec(state["plan"], state.get("source_plan_path", ""))
        warnings.append("Deck curator LLM failed; used deterministic fallback slide spec.")
    return {
        **state,
        "raw_llm_response": raw_response,
        "spec": spec,
        "used_langchain": used_langchain,
        "llm_model": model,
        "validation_warnings": warnings,
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

        slide.text_blocks = _ensure_structured_points(
            _compact_text_blocks(slide.text_blocks),
            slide,
        )
        slide.metric_blocks = _compact_metric_blocks(slide.metric_blocks)
        slide.section_label = slide.section_label or _infer_slide_section(slide)
        if not slide.metric_blocks:
            slide.metric_blocks = _extract_metrics_from_slide(slide)[:4]
        if slide.section_type != "opening" and _is_weak_point_claim(slide.title):
            slide.title = _repair_slide_title(slide)

        if slide.section_type == "opening" and not slide.image_blocks:
            cover_image = _pick_cover_figure(state["plan"])
            if cover_image:
                slide.image_blocks.append(cover_image)

        if not slide.text_blocks and not slide.image_blocks and not slide.table_blocks:
            slide.text_blocks = _ensure_structured_points(
                [TextBlock(text="Key idea unavailable.", role="bullet")],
                slide,
            )
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
        slide.layout = _normalize_slide_layout(slide)

    spec.metadata = {
        **(spec.metadata or {}),
        "generator": "llm_curated_text_pptx",
        "used_langgraph": state.get("used_langgraph", False),
        "used_langchain": state.get("used_langchain", False),
        "llm_model": state.get("llm_model", ""),
        "figure_analysis_count": len(state.get("figure_analyses", {})),
        "style": state.get("style", "academic"),
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
    renderer = PptxRenderer(style=state.get("style", "academic"))
    renderer.render(spec, pptx_path)

    qa_result = inspect_pptx_layout(pptx_path)
    spec_evaluation = evaluate_presentation_spec(spec, qa_result)
    qa_path = output_subdir / "layout_qa.json"
    save_json(qa_path, spec_evaluation)
    if spec_evaluation["warnings"]:
        for warning in spec_evaluation["warnings"][:12]:
            logger.warning(f"  QA: {warning}")

    return {
        **state,
        "pptx_path": pptx_path,
        "qa_report_path": str(qa_path),
        "qa_warnings": spec_evaluation["warnings"],
        "failed_slides": spec_evaluation["failed_slides"],
        "qa_passed": spec_evaluation["passed"],
    }


def _route_after_render(state: _PptxWorkflowState) -> str:
    max_attempts = int(os.getenv("PPTX_QA_MAX_REPAIR_ATTEMPTS", "2"))
    attempt = state.get("qa_attempt", 0)
    if not state.get("qa_passed", True) and attempt < max_attempts:
        return "repair_spec"
    return "speaker_script"


def _qa_repair_node(state: _PptxWorkflowState) -> _PptxWorkflowState:
    """Repair only failed slide specs based on evaluator and PPTX QA feedback."""
    spec = state["spec"]
    warnings = state.get("qa_warnings", [])
    attempt = state.get("qa_attempt", 0) + 1
    repair_log = list(state.get("qa_repair_log", []))

    affected_slides = set(state.get("failed_slides", [])) or _slides_from_qa_warnings(warnings)
    if not affected_slides:
        affected_slides = set()

    for slide_index in sorted(affected_slides):
        if slide_index < 1 or slide_index > len(spec.slides):
            continue
        slide = spec.slides[slide_index - 1]
        before_layout = slide.layout
        before_bullets = len(slide.text_blocks)
        slide_warnings = [warning for warning in warnings if f"slide {slide_index}:" in warning.lower()]

        slide.title = _limit_words(slide.title, 8)
        slide.takeaway = _limit_words(slide.takeaway, 12)
        slide.text_blocks = _repair_point_blocks(slide, slide.text_blocks[:3], compact_layout=bool(slide_warnings))
        slide.metric_blocks = [
            MetricBlock(
                label=_repair_metric_label(metric, slide),
                value=_limit_words(metric.value, 3),
                note=_limit_words(metric.note, 5),
            )
            for metric in _compact_metric_blocks(slide.metric_blocks)[:3]
        ]
        if not slide.metric_blocks:
            slide.metric_blocks = _extract_metrics_from_slide(slide)[:3]
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
        slide.layout = _normalize_slide_layout(slide)

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
                + "; ".join(_point_script_text(block).rstrip(".") for block in slide.text_blocks[:3])
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


def _point_script_text(block: TextBlock) -> str:
    claim = _clean_text(getattr(block, "claim", "") or "")
    detail = _clean_text(getattr(block, "detail", "") or "")
    evidence = _clean_text(getattr(block, "evidence", "") or "")
    if claim and detail and evidence:
        return f"{claim}: {detail} Evidence: {evidence}"
    if claim and detail:
        return f"{claim}: {detail}"
    return _clean_text(block.text)


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
- Use 2-4 numbered_points per slide depending on importance.
- Every numbered_point must include claim, detail, and evidence.
- claim is the short bold idea, <= 8 words.
- detail is one complete explanatory sentence, <= 22 words.
- evidence names the source section, figure/table, metric, or paper result supporting the point.
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
      "section": "Overview|Motivation|Method|Experiments|Results|Conclusion",
      "takeaway": "one-sentence message",
      "numbered_points": [
        {{
          "claim": "short claim",
          "detail": "complete sentence explaining the claim.",
          "evidence": "Figure 1, Table 2, section name, or metric"
        }}
      ],
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
    model = _get_pptx_llm_model()
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

    api_key = (
        os.getenv("PPTX_VISION_API_KEY")
        or os.getenv("RAG_VISION_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    base_url = (
        os.getenv("PPTX_VISION_BASE_URL")
        or os.getenv("RAG_VISION_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or None
    )
    model = _get_figure_analysis_model()
    if not api_key:
        logger.warning("Figure analysis skipped: set PPTX_VISION_API_KEY, RAG_VISION_API_KEY, or OPENAI_API_KEY.")
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
        text_blocks = _parse_point_blocks(item)

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
                section_label=item.get("section", "") or item.get("section_label", ""),
            )
        )

    return PresentationSpec(
        title=data.get("title") or "Paper2Slides Presentation",
        slides=slides,
        metadata={"curation": "llm"},
        source_plan_path=source_plan_path or None,
    )


def _fallback_compact_spec(plan: ContentPlan, source_plan_path: str = "") -> PresentationSpec:
    base = build_presentation_spec(
        plan,
        title=_infer_deck_title_from_plan(plan) or "Paper2Slides Presentation",
        source_plan_path=source_plan_path,
    )
    for slide in base.slides:
        slide.layout = _infer_layout(slide)
        slide.takeaway = _limit_words(slide.text_blocks[0].text if slide.text_blocks else slide.title, 22)
        slide.text_blocks = _ensure_structured_points(_compact_text_blocks(slide.text_blocks), slide)
        slide.metric_blocks = _extract_metrics_from_slide(slide)[:4]
    base.metadata = {**(base.metadata or {}), "curation": "fallback_compact"}
    return base


def _infer_deck_title_from_plan(plan: ContentPlan) -> str:
    sections = list(getattr(plan, "sections", []) or [])
    candidates = []
    if getattr(plan, "metadata", None):
        for key in ("title", "paper_title", "document_title"):
            value = plan.metadata.get(key)
            if value:
                candidates.append(str(value))
    for section in sections[:3]:
        candidates.append(str(getattr(section, "title", "") or ""))
        candidates.append(str(getattr(section, "content", "") or "")[:320])

    text = " ".join(_clean_text(item) for item in candidates if item)
    match = re.search(r"Title:\s*(.*?)(?:\s+Authors?:|$)", text, flags=re.IGNORECASE)
    if match:
        title = re.split(r"\s+Title:\s*", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0].strip()
        return _limit_words(title, 14)
    for item in candidates:
        cleaned = _clean_text(item)
        cleaned = re.sub(r"^\s*Title:\s*", "", cleaned, flags=re.IGNORECASE)
        if cleaned and len(cleaned.split()) >= 3 and not cleaned.lower().startswith(("overview", "abstract", "introduction")):
            return _limit_words(cleaned, 14)
    return ""


def _section_to_packet(section) -> Dict[str, Any]:
    return {
        "id": section.id,
        "title": section.title,
        "type": section.section_type,
        "section": getattr(section, "section_label", ""),
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


def _parse_point_blocks(item: Dict[str, Any]) -> List[TextBlock]:
    raw_points = item.get("numbered_points") or item.get("points") or item.get("bullets") or item.get("text_blocks") or []
    blocks: List[TextBlock] = []
    for point in raw_points:
        if isinstance(point, dict):
            claim = _limit_words(point.get("claim", ""), 8)
            detail = _complete_point(point.get("detail", "") or point.get("text", ""), 24)
            evidence = _limit_words(point.get("evidence", ""), 14)
            text = _format_point_text(claim, detail) or _limit_words(point.get("text", ""), 24)
            if text:
                blocks.append(TextBlock(text=text, role="bullet", bullet_level=0, claim=claim, detail=detail, evidence=evidence))
        else:
            text = _limit_words(str(point), 24)
            if text:
                blocks.append(TextBlock(text=text, role="bullet", bullet_level=0))
        if len(blocks) >= 4:
            break
    return blocks


def _ensure_structured_points(blocks: List[TextBlock], slide: SlideSpec) -> List[TextBlock]:
    structured: List[TextBlock] = []
    seen = set()
    source_blocks = blocks or [TextBlock(text=slide.takeaway or slide.title or "Key idea unavailable.", role="bullet")]
    for block in source_blocks:
        source_text = _clean_text(block.text or block.detail or block.claim)
        if not source_text and not block.claim and not block.detail:
            continue
        detail = _complete_point(block.detail or _infer_point_detail(source_text, slide), 24)
        claim = _repair_point_claim(block.claim or _infer_point_claim(source_text), detail, source_text, slide)
        if claim and detail and claim.lower().rstrip(".") == detail.lower().rstrip("."):
            detail = _complete_point(source_text if source_text.lower().rstrip(".") != claim.lower().rstrip(".") else slide.takeaway, 24)
        evidence = _limit_words(block.evidence or _infer_point_evidence(slide), 14)
        text = _format_point_text(claim, detail) or source_text
        key = text.lower()
        if not text or key in seen:
            continue
        structured.append(
            TextBlock(
                text=text,
                role="bullet",
                bullet_level=block.bullet_level,
                claim=claim,
                detail=detail,
                evidence=evidence,
            )
        )
        seen.add(key)
        if len(structured) >= 4:
            break
    return structured


def _repair_point_blocks(slide: SlideSpec, blocks: List[TextBlock], compact_layout: bool = False) -> List[TextBlock]:
    points = _ensure_structured_points(blocks, slide)
    repaired: List[TextBlock] = []
    detail_limit = 16 if compact_layout else 22
    for point in points[:3]:
        detail = _complete_point(point.detail or _infer_point_detail(point.text, slide), detail_limit)
        claim = _repair_point_claim(point.claim or _infer_point_claim(point.text), detail, point.text, slide, max_words=7)
        evidence = _limit_words(point.evidence or _infer_point_evidence(slide), 10)
        repaired.append(
            TextBlock(
                text=_format_point_text(claim, detail),
                role="bullet",
                bullet_level=0,
                claim=claim,
                detail=detail,
                evidence=evidence,
            )
        )
    if not repaired:
        repaired = _ensure_structured_points([TextBlock(text=slide.takeaway or slide.title, role="bullet")], slide)[:1]
    return repaired


def _repair_metric_label(metric: MetricBlock, slide: SlideSpec) -> str:
    label = _limit_words(metric.label, 3)
    if label.lower() in {"", "metric", "key metric", "key number", "number"}:
        context = " ".join([slide.title, slide.takeaway] + [block.text for block in slide.text_blocks])
        label = _metric_label_for_value(metric.value, context)
        if label.lower() in {"key number", "key metric"}:
            label = _context_metric_label(slide, context)
    return _limit_words(label, 3)


def _format_point_text(claim: str, detail: str) -> str:
    claim = _clean_text(claim).strip(" .;:-")
    detail = _complete_point(detail, 24)
    if claim and detail:
        return f"{claim}: {detail}"
    return detail or claim


def _repair_slide_title(slide: SlideSpec) -> str:
    candidates = []
    candidates.extend(block.claim or block.text for block in slide.text_blocks[:3])
    candidates.extend([slide.takeaway, slide.title, slide.section_label])
    for candidate in candidates:
        repaired = _repair_point_claim("", candidate, candidate, slide, max_words=8)
        if repaired and not _is_weak_point_claim(repaired):
            return _limit_words(repaired, 8)
    if slide.section_label:
        return _limit_words(f"{slide.section_label} insight", 8)
    return _limit_words(slide.title or "Key finding", 8)


def _repair_point_claim(
    claim: str,
    detail: str,
    source_text: str,
    slide: SlideSpec,
    max_words: int = 8,
) -> str:
    candidates = [
        _clean_text(claim),
        _keyword_point_claim(detail),
        _keyword_point_claim(source_text),
        _claim_from_complete_text(detail),
        _claim_from_complete_text(source_text),
        _keyword_point_claim(slide.takeaway),
        _claim_from_complete_text(slide.takeaway),
        _claim_from_complete_text(slide.title),
    ]
    for candidate in candidates:
        candidate = _limit_words(_clean_text(candidate).strip(" .;:-"), max_words)
        if candidate and not _is_weak_point_claim(candidate):
            return candidate
    if slide.section_label:
        return _limit_words(f"{slide.section_label} insight", max_words)
    return "Key insight"


def _keyword_point_claim(text: str) -> str:
    lower = _clean_text(text).lower()
    if not lower:
        return ""
    if "vanishing/exploding" in lower or ("vanishing" in lower and "exploding" in lower):
        return "Gradient instability barrier"
    if "very deep" in lower and any(term in lower for term in ("train", "training", "networks")):
        return "Very deep training challenge"
    if "optimization" in lower and "generalization" in lower:
        return "Optimization and generalization gap"
    if "projection-based shortcuts" in lower or "projection shortcuts" in lower:
        return "Projection shortcuts add cost"
    if "highway network" in lower or ("gated" in lower and "shortcut" in lower):
        return "Gated shortcuts are unreliable"
    if "training error" in lower and any(term in lower for term in ("layers", "depth", "deeper")):
        return "Depth degradation appears in training"
    if "hundreds of layers" in lower or "large depths" in lower:
        return "Depth scaling remains blocked"
    if "identity" in lower and any(term in lower for term in ("shortcut", "residual", "information flow")):
        return "Identity shortcuts preserve flow"
    if "accuracy" in lower and any(term in lower for term in ("improv", "better")) and any(term in lower for term in ("train", "training", "depth")):
        return "Accuracy gains require trainable depth"
    return ""


def _claim_from_complete_text(text: str) -> str:
    text = _strip_boilerplate_point_prefix(_strip_trailing_ellipsis(_clean_text(text))).strip(" .;:-")
    if not text:
        return ""
    if ":" in text:
        lead = text.split(":", 1)[0].strip(" -")
        if lead and not _is_weak_point_claim(lead):
            return lead
    first_clause = re.split(r",|;|\sdue to\s|\sbecause\s|\bthat\s", text, maxsplit=1, flags=re.IGNORECASE)[0].strip(" -")
    if first_clause and not _is_weak_point_claim(first_clause):
        return first_clause
    return _infer_point_claim(text)


def _strip_boilerplate_point_prefix(text: str) -> str:
    patterns = [
        r"^(?:the\s+)?paper\s+(?:addresses|targets|studies|tackles)\s+(?:the\s+)?(?:problem|challenge)\s+of\s+",
        r"^(?:this\s+)?paper\s+(?:addresses|targets|studies|tackles)\s+(?:the\s+)?(?:problem|challenge)\s+of\s+",
        r"^its\s+goal\s+is\s+to\s+make\s+it\s+",
        r"^in\s+short,?\s+",
        r"^taken\s+together,?\s+",
        r"^this\s+meant\s+",
        r"^even\s+with\s+",
        r"^they\s+can\s+help\s+but\s+are\s+not\s+",
    ]
    cleaned = _clean_text(text)
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def _is_weak_point_claim(text: str) -> bool:
    text = _clean_text(text).strip(" .;:-")
    if not text:
        return True
    lower = text.lower()
    words = lower.split()
    if re.fullmatch(r"(?:slide|page)\s*\d+", lower):
        return True
    weak_exact = {
        "in short",
        "taken together",
        "the paper addresses the problem of",
        "its goal is to make it",
        "this meant practitioners could not reliably",
        "even with improved initialization and batch",
        "they can help but are not",
    }
    if lower in weak_exact:
        return True
    if lower.startswith(("the paper addresses", "this paper addresses", "its goal is", "in short", "taken together")) and len(words) <= 9:
        return True
    if lower.startswith(("this meant", "even with", "they can help")) and len(words) <= 9:
        return True
    weak_endings = {
        "a", "an", "the", "of", "to", "in", "on", "for", "with", "by", "and", "or", "that", "which",
        "it", "its", "not", "but", "while",
    }
    if words and words[-1].strip(" ,;:-()[]").lower() in weak_endings:
        return True
    if text.count("(") != text.count(")"):
        return True
    return False


def _infer_point_claim(text: str) -> str:
    text = _strip_trailing_ellipsis(_clean_text(text))
    if not text:
        return ""
    if ":" in text:
        lead = text.split(":", 1)[0].strip(" -")
        if 2 <= len(lead.split()) <= 10:
            return lead
    first_clause = re.split(r",|;|\sdue to\s|\sbecause\s|\bthat\s", text, maxsplit=1, flags=re.IGNORECASE)[0].strip(" -")
    if 2 <= len(first_clause.split()) <= 8:
        return first_clause
    words = text.split()
    return " ".join(words[: min(6, len(words))]).strip(" .;:-")


def _infer_point_detail(text: str, slide: SlideSpec) -> str:
    text = _strip_trailing_ellipsis(_clean_text(text))
    if ":" in text:
        detail = text.split(":", 1)[1].strip(" -")
        if detail:
            return detail
    if len(text.split()) >= 5:
        return text
    return slide.takeaway or text or slide.title


def _infer_point_evidence(slide: SlideSpec) -> str:
    if slide.image_blocks:
        image = slide.image_blocks[0]
        return image.title or image.caption or image.placeholder_text or "source figure"
    if slide.table_blocks:
        table = slide.table_blocks[0]
        return table.title or table.caption or "source table"
    if slide.metric_blocks:
        metric = slide.metric_blocks[0]
        return "metric " + _clean_text(metric.value or metric.label)
    if slide.notes:
        return _limit_words(slide.notes[0], 12)
    if slide.section_label:
        return f"{slide.section_label} section"
    return slide.title or "source plan"


def _compact_text_blocks(blocks: List[TextBlock]) -> List[TextBlock]:
    compact: List[TextBlock] = []
    seen = set()
    for block in blocks:
        parts = _split_into_points(block.text)
        for part in parts:
            point = _complete_point(part, 34)
            if not point or point.lower() in seen:
                continue
            compact.append(
                TextBlock(
                    text=point,
                    role="bullet",
                    bullet_level=0,
                    claim=block.claim if point == block.text else "",
                    detail=block.detail if point == block.text else "",
                    evidence=block.evidence,
                )
            )
            seen.add(point.lower())
            if len(compact) >= 4:
                return compact
    return compact


def _complete_point(text: str, max_words: int) -> str:
    text = _strip_trailing_ellipsis(text)
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    search = " ".join(words[: max_words + 10])
    sentence_end = max(search.rfind("."), search.rfind(";"), search.rfind("!"), search.rfind("?"))
    if sentence_end > 0:
        sentence = search[: sentence_end + 1].strip()
        if len(sentence.split()) >= 5:
            return sentence

    keep = words[:max_words]
    weak_endings = {
        "a", "an", "the", "of", "to", "in", "on", "for", "with", "by", "and", "or", "that", "which", "due",
        "associated", "including", "such", "as", "from", "through", "into", "across", "between", "during",
    }
    while len(keep) > 8 and keep[-1].strip(" ,;:-").lower() in weak_endings:
        keep.pop()
    return " ".join(keep).rstrip(" ,;:-") + "."


def _compact_metric_blocks(blocks: List[MetricBlock]) -> List[MetricBlock]:
    compact: List[MetricBlock] = []
    for metric in blocks[:4]:
        label = _limit_words(_clean_text(metric.label), 4)
        raw_value = _clean_text(metric.value)
        note = _limit_words(_clean_text(metric.note), 8)
        value = _normalize_metric_block_value(raw_value, " ".join([label, note]))
        if not value and not raw_value:
            value = _first_metric_value(" ".join([label, note]))
        if not value or _looks_like_year(value) or _looks_like_noise_number(value) or _looks_like_spurious_metric(label, value, note):
            continue
        compact.append(MetricBlock(label=label or "Key metric", value=value, note=note))
    return compact


def _normalize_metric_block_value(value: str, context: str = "") -> str:
    text = _strip_trailing_ellipsis(_clean_text(value)).strip()
    if not text:
        return ""
    matches = list(_iter_metric_value_matches(text))
    if not matches:
        return ""
    for match in matches:
        clean_value = match.group(0).replace(" ", "")
        if _looks_like_year(clean_value) or _looks_like_noise_number(clean_value):
            continue
        if not _valid_metric_candidate(text, match, clean_value) and not _metric_context_allows_value(clean_value, context):
            continue
        if match.start() == 0 or "%" in clean_value or clean_value.lower().startswith(("r=", "p=")):
            return clean_value
    return ""


def _metric_context_allows_value(value: str, context: str) -> bool:
    lower_value = _clean_text(value).lower()
    if "%" in lower_value or lower_value.startswith(("r=", "p=")) or re.search(r"[a-zA-Z]", lower_value):
        return True
    context_lower = _clean_text(context).lower()
    metric_terms = (
        "accuracy", "error", "rate", "score", "map", "layer", "layers", "parameter", "params", "class", "classes",
        "task", "tasks", "image", "images", "epoch", "epochs", "batch", "token", "tokens", "benchmark", "improvement",
    )
    if not any(term in context_lower for term in metric_terms):
        return False
    try:
        number = float(lower_value)
    except ValueError:
        return False
    return number > 20 or any(term in context_lower for term in ("layer", "class", "task", "epoch", "image", "token", "batch"))


def _extract_metrics_from_slide(slide: SlideSpec) -> List[MetricBlock]:
    text = " ".join([slide.takeaway, slide.title] + [block.text for block in slide.text_blocks])
    metrics: List[MetricBlock] = []
    seen = set()
    for match in _iter_metric_value_matches(text):
        clean_value = match.group(0).replace(" ", "")
        if not _valid_metric_candidate(text, match, clean_value):
            continue
        if _looks_like_year(clean_value) or _looks_like_noise_number(clean_value):
            continue
        if clean_value in seen:
            continue
        seen.add(clean_value)
        label = _metric_label_for_value(clean_value, text)
        if _looks_like_spurious_metric(label, clean_value, text):
            continue
        metrics.append(MetricBlock(label=label, value=clean_value))
        if len(metrics) >= 4:
            break
    return metrics


def _first_metric_value(text: str) -> str:
    for match in _iter_metric_value_matches(text or ""):
        value = match.group(0).replace(" ", "")
        if not _looks_like_year(value) and _valid_metric_candidate(text or "", match, value):
            return value
    return ""


def _iter_metric_value_matches(text: str) -> Iterable[re.Match[str]]:
    pattern = (
        r"(?<![A-Za-z0-9-])"
        r"(?:"
        r"\d+(?:\.\d+)?%"
        r"|r\s*=\s*-?\d+(?:\.\d+)?"
        r"|p\s*=\s*\d+(?:\.\d+)?"
        r"|\d+(?:\.\d+)?\s*(?:x|M|B|K|ms|s|GB|MB|tokens?|layers?|params?|parameters?|classes|tasks|images|epochs|FLOPs?|GFLOPs?)"
        r"|\d+(?:\.\d+)?"
        r")"
    )
    return re.finditer(pattern, text or "", flags=re.IGNORECASE)


def _valid_metric_candidate(text: str, match: re.Match[str], value: str) -> bool:
    if _looks_like_dataset_or_model_number(text, match):
        return False
    lower_value = value.lower()
    if "%" in lower_value or lower_value.startswith(("r=", "p=")):
        return True
    if re.search(r"[a-zA-Z]", value):
        return True
    window = text[max(0, match.start() - 42): min(len(text), match.end() + 42)].lower()
    metric_terms = (
        "accuracy", "error", "rate", "score", "layer", "layers", "parameter", "params", "class", "classes",
        "task", "tasks", "image", "images", "epoch", "epochs", "token", "tokens", "benchmark", "improvement",
    )
    if not any(term in window for term in metric_terms):
        return False
    try:
        number = float(value)
    except ValueError:
        return False
    if number <= 20 and not any(term in window for term in ("layer", "class", "task", "epoch", "image", "token")):
        return False
    return True


def _looks_like_dataset_or_model_number(text: str, match: re.Match[str]) -> bool:
    left = text[max(0, match.start() - 24): match.start()].lower()
    right = text[match.end(): min(len(text), match.end() + 18)].lower()
    if left.endswith("-") or right.startswith("-"):
        token = (left + text[match.start():match.end()] + right).strip()
        if re.search(r"(cifar|imagenet|mnist|resnet|vgg|bert|gpt|vit|t5|dataset|benchmark)-?\d+", token):
            return True
    if re.search(r"(cifar|imagenet|mnist|resnet|vgg|bert|gpt|vit|t5)-$", left):
        return True
    return False


def _looks_like_spurious_metric(label: str, value: str, context: str = "") -> bool:
    label_lower = _clean_text(label).lower()
    value_clean = _clean_text(value)
    if not re.fullmatch(r"\d+(?:\.\d+)?", value_clean):
        return False
    try:
        number = float(value_clean)
    except ValueError:
        return False
    generic_labels = {"accuracy", "rating", "score", "key number", "key metric", "metric"}
    context_lower = _clean_text(context).lower()
    if label_lower in generic_labels:
        return True
    if re.search(r"(cifar|imagenet|mnist|resnet|vgg|bert|gpt|vit|t5)-\s*" + re.escape(value_clean), context_lower):
        return True
    return False


def _looks_like_year(value: str) -> bool:
    return bool(re.fullmatch(r"(?:19|20)\d{2}", value or ""))


def _looks_like_noise_number(value: str) -> bool:
    return bool(re.fullmatch(r"[1-9]", value or ""))


def _metric_label_for_value(value: str, context: str) -> str:
    lower = context.lower()
    if "%" in value and "success" in lower:
        return "Success rate"
    if "%" in value and "win" in lower:
        return "Win rate"
    if "%" in value and any(term in lower for term in ("efficiency", "improvement", "speed", "cost")):
        return "Efficiency gain"
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
    if "rating" in lower:
        return "Rating"
    if any(term in lower for term in ("parameter", "params")):
        return "Parameters"
    if any(term in lower for term in ("benchmark", "score", "win rate")):
        return "Benchmark score"
    if any(term in lower for term in ("context", "token", "window")):
        return "Context length"
    return "Key number"


def _context_metric_label(slide: SlideSpec, context: str) -> str:
    candidates = [
        getattr(slide, "title", "") or "",
        getattr(slide, "takeaway", "") or "",
    ]
    candidates.extend(getattr(block, "claim", "") or block.text for block in slide.text_blocks[:2])
    stop_words = {
        "the", "a", "an", "of", "to", "in", "and", "or", "for", "with", "that", "this", "these", "those",
        "is", "are", "was", "were", "be", "been", "being", "has", "have", "had", "can", "could", "from",
        "into", "using", "based", "compared", "new",
    }
    for candidate in candidates:
        words = [
            word.strip(" ,.;:()[]")
            for word in _clean_text(candidate).split()
            if word.strip(" ,.;:()[]")
        ]
        meaningful = [word for word in words if word.lower() not in stop_words]
        if meaningful:
            return " ".join(meaningful[:3])
    return "Slide metric"


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
        return _strip_trailing_ellipsis(text)
    sentence_end = max(text[:260].rfind("."), text[:260].rfind(";"), text[:260].rfind("!"), text[:260].rfind("?"))
    if sentence_end > 0 and len(text[:sentence_end].split()) <= max_words + 8:
        return _strip_trailing_ellipsis(text[: sentence_end + 1])
    return _strip_trailing_ellipsis(" ".join(words[:max_words]).rstrip(" ,;:"))


def _strip_trailing_ellipsis(text: str) -> str:
    text = re.sub(r"\.{2,}\s*$", "", _clean_text(text)).strip()
    return text


def _clean_text(text: str) -> str:
    cleaned = str(text or "")
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*]\s*", "", cleaned)
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
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    labels = (
        "RESEARCH PROBLEM",
        "LIMITATIONS OF EXISTING METHODS",
        "RESEARCH GAP",
        "FRAMEWORK OVERVIEW",
        "DATASET / BENCHMARK",
        "MAIN RESULTS",
        "COMPARISON ANALYSIS",
        "NOVELTY & INNOVATIONS",
        "FUTURE DIRECTIONS",
        "LIMITATIONS",
    )
    for label in labels:
        if cleaned.upper().startswith(label):
            cleaned = cleaned[len(label):].strip(" -:")
            break
    return cleaned


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


def _normalize_slide_layout(slide: SlideSpec) -> str:
    layout = (slide.layout or "auto").lower()
    allowed = {"cover", "statement", "metric_focus", "visual_right", "visual_left", "table_focus", "quote", "closing"}
    if slide.section_type == "opening":
        return "cover"
    if slide.section_type == "ending":
        return "closing"
    if layout not in allowed and layout not in {"section", "auto", ""}:
        return _infer_layout(slide)
    if layout in {"visual_left", "visual_right"} and not slide.image_blocks:
        if slide.table_blocks:
            return "table_focus"
        if slide.metric_blocks:
            return "metric_focus"
        return "statement"
    if layout == "table_focus" and not slide.table_blocks:
        if slide.image_blocks:
            return "visual_right"
        if slide.metric_blocks:
            return "metric_focus"
        return "statement"
    if layout in {"section", "auto", ""}:
        return _infer_layout(slide)
    if layout == "quote" and not slide.image_blocks and not slide.table_blocks:
        return "metric_focus" if slide.metric_blocks else "statement"
    return layout


def _infer_slide_section(slide: SlideSpec) -> str:
    text = " ".join([slide.title, slide.takeaway] + [block.text for block in slide.text_blocks]).lower()
    if slide.section_type == "opening":
        return "Overview"
    if slide.section_type == "ending":
        return "Conclusion"
    if any(word in text for word in ("motivation", "problem", "background", "challenge", "limitation")):
        return "Motivation"
    if any(word in text for word in ("method", "approach", "architecture", "algorithm", "training", "model")):
        return "Method"
    if any(word in text for word in ("experiment", "evaluation", "benchmark", "ablation", "result")):
        return "Results"
    return "Core Ideas"
