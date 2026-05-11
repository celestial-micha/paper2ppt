import unittest
import uuid
from pathlib import Path

from paper2slides.generator.detailed_tex import generate_detailed_tex_deck
from paper2slides.generator.config import GenerationConfig, GenerationInput, OutputType, SlidesLength, StyleType
from paper2slides.generator.content_planner import ContentPlanner
from paper2slides.generator.content_planner import ContentPlan, FigureRef, Section, TableRef
from paper2slides.generator.pptx_qa import evaluate_presentation_spec, inspect_pptx_layout
from paper2slides.generator.pptx_renderer import PptxRenderer
from paper2slides.generator.text_pptx_workflow import _build_speaker_script, _compact_metric_blocks, _ensure_structured_points, _normalize_slide_layout, _qa_repair_node
from paper2slides.generator.spec_builder import build_presentation_spec
from paper2slides.generator.slide_schema import MetricBlock, PresentationSpec, SlideSpec, TextBlock
from paper2slides.summary import FigureInfo, GeneralContent, OriginalElements, TableInfo


class Phase1PptxSmokeTest(unittest.TestCase):
    def test_builds_slide_spec_and_pptx(self):
        plan = ContentPlan(
            output_type="slides",
            sections=[
                Section(
                    id="slide_01",
                    title="Phase 1 Smoke Test",
                    section_type="opening",
                    content="This is the first editable slide. It should render as body text in a PPTX.",
                    tables=[TableRef(table_id="Table 1", focus="Key metrics")],
                    figures=[FigureRef(figure_id="Figure 1", focus="Keep as reference")],
                )
            ],
            tables_index={
                "Table 1": TableInfo(
                    table_id="Table 1",
                    caption="Example table",
                    html_content="<table><tr><th>Metric</th><th>Value</th></tr><tr><td>Slides</td><td>1</td></tr></table>",
                )
            },
            figures_index={
                "Figure 1": FigureInfo(
                    figure_id="Figure 1",
                    caption="Missing image is allowed",
                    image_path="missing.png",
                )
            },
            metadata={"page_range": [1, 1]},
        )

        spec = build_presentation_spec(plan, title="Smoke Test")
        self.assertEqual(len(spec.slides), 1)
        self.assertTrue(spec.slides[0].table_blocks)
        self.assertTrue(spec.slides[0].image_blocks)

        temp_root = Path(__file__).parent / "outputs" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        output_path = temp_root / f"slides_{uuid.uuid4().hex}.pptx"
        renderer = PptxRenderer()
        renderer.render(spec, output_path)
        self.assertTrue(output_path.exists())

    def test_toc_with_seven_sections_stays_inside_slide_bounds(self):
        slides = []
        for index in range(7):
            slides.append(
                SlideSpec(
                    slide_id=f"slide_{index + 1:02d}",
                    title=f"Section {index + 1} Slide",
                    section_label=f"Section {index + 1}",
                    layout="statement",
                    takeaway="This slide checks table of contents spacing.",
                    text_blocks=[
                        TextBlock(
                            text="Claim: The generated deck keeps section labels readable.",
                            claim="The generated deck keeps section labels readable.",
                            detail="Seven section entries should fit inside the table of contents slide.",
                            evidence="Renderer layout QA",
                        )
                    ],
                )
            )
        spec = PresentationSpec(title="TOC Fit", slides=slides)

        temp_root = Path(__file__).parent / "outputs" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        output_path = temp_root / f"toc_{uuid.uuid4().hex}.pptx"
        PptxRenderer().render(spec, output_path)

        qa = inspect_pptx_layout(output_path)
        self.assertTrue(qa.passed, qa.warnings)

    def test_slide_planning_uses_text_only_figure_manifest(self):
        planner = ContentPlanner(api_key="test-key", base_url="http://localhost", model="test-model")

        captured = {}

        def fake_text_llm(prompt):
            captured["prompt"] = prompt
            return """
```json
{"slides":[{"id":"slide_01","title":"Text-only","content":"Uses an original figure.","tables":[],"figures":[{"figure_id":"Figure 1","focus":"Pipeline"}]}]}
```
"""

        def fail_multimodal(*args, **kwargs):
            raise AssertionError("Slides planning must not call the multimodal/image path")

        planner._call_text_llm = fake_text_llm
        planner._call_multimodal_llm = fail_multimodal
        planner._load_figure_images = fail_multimodal

        gen_input = GenerationInput(
            config=GenerationConfig(
                output_type=OutputType.SLIDES,
                slides_length=SlidesLength.SHORT,
                style=StyleType.ACADEMIC,
            ),
            content=GeneralContent(content="A paper summary with a method pipeline."),
            origin=OriginalElements(
                figures=[
                    FigureInfo(
                        figure_id="Figure 1",
                        caption="Pipeline overview",
                        image_path="images/pipeline.png",
                    )
                ]
            ),
        )

        plan = planner.plan(gen_input)
        self.assertEqual(len(plan.sections), 1)
        self.assertIn("Source image: images/pipeline.png", captured["prompt"])
        self.assertNotIn("[FIGURE_IMAGES]", captured["prompt"])

    def test_qa_repair_compacts_risky_slide(self):
        long_text = " ".join(["overflow"] * 30)
        spec = PresentationSpec(
            title="QA Repair",
            slides=[
                SlideSpec(
                    slide_id="slide_01",
                    title="This title is intentionally much too long for a normal presentation header",
                    layout="statement",
                    takeaway=long_text,
                    text_blocks=[TextBlock(text=long_text) for _ in range(5)],
                    metric_blocks=[MetricBlock(label="Very long label", value="1234567890") for _ in range(4)],
                )
            ],
        )

        repaired = _qa_repair_node(
            {
                "spec": spec,
                "qa_warnings": ["slide 1: long title/subtitle may wrap or clip"],
                "validation_warnings": [],
            }
        )
        slide = repaired["spec"].slides[0]
        self.assertEqual(repaired["qa_attempt"], 1)
        self.assertLessEqual(len(slide.text_blocks), 3)
        self.assertLessEqual(len(slide.title.split()), 8)
        self.assertLessEqual(len(slide.takeaway.split()), 12)

    def test_builds_speaker_script_from_final_spec(self):
        spec = PresentationSpec(
            title="Script Test",
            slides=[
                SlideSpec(
                    slide_id="slide_01",
                    title="Opening",
                    takeaway="The method fails visually.",
                    text_blocks=[TextBlock(text="Screenshots drive most errors.")],
                    metric_blocks=[MetricBlock(label="Success rate", value="5.36%")],
                    notes=["Referenced figures: Figure 1"],
                )
            ],
        )

        script = _build_speaker_script(spec, ["attempt 1: slide 1 compressed"])
        self.assertIn("# Script Test", script)
        self.assertIn("## Slide 1: Opening", script)
        self.assertIn("Suggested narration", script)
        self.assertIn("Success rate: 5.36%", script)

    def test_drops_metrics_without_visible_values(self):
        metrics = [
            MetricBlock(label="Not really a metric", value="", note="qualitative point"),
            MetricBlock(label="Success rate", value="5.36%", note="overall"),
        ]

        compact = _compact_metric_blocks(metrics)
        self.assertEqual(len(compact), 1)
        self.assertEqual(compact[0].value, "5.36%")

    def test_structures_numbered_points_for_evaluator(self):
        slide = SlideSpec(
            slide_id="slide_01",
            title="Result",
            takeaway="The new model improves inference quality.",
            text_blocks=[TextBlock(text="Accuracy improves because the model uses stronger supervision.")],
            section_label="Results",
        )
        slide.text_blocks = _ensure_structured_points(slide.text_blocks, slide)

        point = slide.text_blocks[0]
        self.assertTrue(point.claim)
        self.assertTrue(point.detail)
        self.assertTrue(point.evidence)
        report = evaluate_presentation_spec(PresentationSpec(title="Eval", slides=[slide]))
        self.assertTrue(report["passed"])

    def test_evaluator_flags_missing_point_fields_and_bad_metric(self):
        spec = PresentationSpec(
            title="Eval",
            slides=[
                SlideSpec(
                    slide_id="slide_01",
                    title="Weak point",
                    text_blocks=[TextBlock(text="Incomplete...")],
                    metric_blocks=[MetricBlock(label="Key number", value="large")],
                )
            ],
        )
        report = evaluate_presentation_spec(spec)
        self.assertFalse(report["passed"])
        self.assertIn(1, report["failed_slides"])
        self.assertTrue(any("missing claim" in warning for warning in report["warnings"]))
        self.assertTrue(any("meaningless label" in warning for warning in report["warnings"]))

    def test_visual_layout_without_image_is_rejected_and_normalized(self):
        slide = SlideSpec(
            slide_id="slide_01",
            title="No Visual",
            layout="visual_left",
            takeaway="This slide has only text.",
            text_blocks=[
                TextBlock(
                    text="Claim: A complete detail sentence.",
                    claim="Claim",
                    detail="A complete detail sentence.",
                    evidence="source section",
                )
            ],
        )
        report = evaluate_presentation_spec(PresentationSpec(title="Eval", slides=[slide]))
        self.assertFalse(report["passed"])
        self.assertIn(1, report["failed_slides"])
        self.assertEqual(_normalize_slide_layout(slide), "statement")

    def test_unknown_content_layout_without_visual_normalizes_to_statement(self):
        slide = SlideSpec(
            slide_id="slide_01",
            title="Content Layout",
            layout="content",
            takeaway="This slide should use the full text canvas.",
            text_blocks=[
                TextBlock(
                    text="Claim: A complete detail sentence.",
                    claim="Claim",
                    detail="A complete detail sentence.",
                    evidence="source section",
                )
            ],
        )
        report = evaluate_presentation_spec(PresentationSpec(title="Eval", slides=[slide]))
        self.assertFalse(report["passed"])
        self.assertIn(1, report["failed_slides"])
        self.assertEqual(_normalize_slide_layout(slide), "statement")

    def test_generates_detailed_tex_sidecar(self):
        plan = ContentPlan(
            output_type="slides",
            sections=[
                Section(
                    id="slide_01",
                    title="Detailed Companion",
                    section_type="opening",
                    content="This slide keeps more context for a longer academic explanation. It cites the table evidence.",
                    tables=[TableRef(table_id="Table 1", focus="Evidence")],
                )
            ],
            tables_index={
                "Table 1": TableInfo(
                    table_id="Table 1",
                    caption="Example detailed table",
                    html_content="<table><tr><th>Metric</th><th>Value</th></tr><tr><td>Accuracy</td><td>92%</td></tr></table>",
                )
            },
        )
        spec = PresentationSpec(
            title="Detailed Test",
            slides=[
                SlideSpec(
                    slide_id="slide_01",
                    title="Detailed Companion",
                    takeaway="Detailed sidecar preserves extra context.",
                    text_blocks=[TextBlock(text="More evidence is shown than in the compact deck.")],
                )
            ],
        )
        temp_root = Path(__file__).parent / "outputs" / "tmp" / f"tex_{uuid.uuid4().hex}"
        result = generate_detailed_tex_deck(plan, spec, temp_root, compile_pdf=False)
        tex_path = Path(result["detailed_tex_path"])
        self.assertTrue(tex_path.exists())
        tex = tex_path.read_text(encoding="utf-8")
        self.assertIn("\\documentclass", tex)
        self.assertIn("Detailed sidecar preserves extra context.", tex)
        self.assertIn("Accuracy", tex)


if __name__ == "__main__":
    unittest.main()
