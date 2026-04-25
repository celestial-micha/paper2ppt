"""
Generate Stage - editable PPTX and speaker script generation.
"""
import logging
from pathlib import Path
from typing import Dict

from ...utils import load_json
from ..paths import get_summary_checkpoint, get_plan_checkpoint, get_output_dir

logger = logging.getLogger(__name__)


async def run_generate_stage(base_dir: Path, config_dir: Path, config: Dict) -> Dict:
    """Stage 4: Generate final presentation artifacts."""
    from paper2slides.summary import TableInfo, FigureInfo, OriginalElements
    from paper2slides.generator.content_planner import ContentPlan, Section, TableRef, FigureRef
    from paper2slides.generator import run_text_pptx_workflow
    from ...utils import save_json
    
    plan_data = load_json(get_plan_checkpoint(config_dir))
    summary_data = load_json(get_summary_checkpoint(base_dir, config))
    if not plan_data or not summary_data:
        raise ValueError("Missing checkpoints.")
    
    content_type = plan_data.get("content_type", "paper")
    
    origin_data = plan_data["origin"]
    origin = OriginalElements(
        tables=[TableInfo(
            table_id=t["id"],
            caption=t.get("caption", ""),
            html_content=t.get("html", ""),
        ) for t in origin_data.get("tables", [])],
        figures=[FigureInfo(
            figure_id=f["id"],
            caption=f.get("caption"),
            image_path=f.get("path", ""),
        ) for f in origin_data.get("figures", [])],
        base_path=origin_data.get("base_path", ""),
    )
    
    plan_dict = plan_data["plan"]
    tables_index = {t.table_id: t for t in origin.tables}
    figures_index = {f.figure_id: f for f in origin.figures}
    
    sections = []
    for s in plan_dict.get("sections", []):
        sections.append(Section(
            id=s.get("id", ""),
            title=s.get("title", ""),
            section_type=s.get("type", "content"),
            content=s.get("content", ""),
            tables=[TableRef(**t) for t in s.get("tables", [])],
            figures=[FigureRef(**f) for f in s.get("figures", [])],
        ))
    
    plan = ContentPlan(
        output_type=plan_dict.get("output_type", "slides"),
        sections=sections,
        tables_index=tables_index,
        figures_index=figures_index,
        metadata=plan_dict.get("metadata", {}),
    )

    output_type = config.get("output_type", "slides")
    if output_type != "slides":
        raise ValueError("PaperCue only supports --output slides. Legacy image/poster generation was removed.")

    logger.info("Building structured slide spec and rendering editable PPTX...")
    output_subdir = get_output_dir(config_dir)
    spec_checkpoint_path = config_dir / "checkpoint_slide_spec.json"
    workflow_result = run_text_pptx_workflow(
        plan=plan,
        output_subdir=output_subdir,
        spec_checkpoint_path=spec_checkpoint_path,
        save_json=save_json,
        title=plan.sections[0].title if plan.sections else "Paper2Slides Presentation",
        source_plan_path=str(get_plan_checkpoint(config_dir)),
    )
    spec = workflow_result["spec"]
    pptx_path = workflow_result["pptx_path"]
    logger.info(f"  Saved: {spec_checkpoint_path}")
    logger.info(f"  Saved: {pptx_path.name}")
    if workflow_result.get("used_langgraph"):
        logger.info("  Workflow: LangGraph")
    if workflow_result.get("used_langchain"):
        logger.info(f"  LLM: LangChain ({workflow_result.get('llm_model')})")
    if workflow_result.get("qa_report_path"):
        logger.info(f"  QA: {workflow_result.get('qa_report_path')}")
    if workflow_result.get("speaker_script_path"):
        logger.info(f"  Speaker script: {workflow_result.get('speaker_script_path')}")
    warnings = workflow_result.get("validation_warnings") or []
    for warning in warnings:
        logger.warning(f"  {warning}")
    logger.info("")
    logger.info(f"Output: {output_subdir}")

    return {
        "output_dir": str(output_subdir),
        "slide_spec_path": str(spec_checkpoint_path),
        "pptx_path": str(pptx_path),
        "speaker_script_path": workflow_result.get("speaker_script_path", ""),
        "qa_report_path": workflow_result.get("qa_report_path", ""),
        "num_slides": len(spec.slides),
    }
