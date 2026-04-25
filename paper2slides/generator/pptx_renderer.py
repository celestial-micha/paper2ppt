"""
Deterministic PPTX renderer for structured slide specs.

The renderer intentionally stays native-PPTX and editable, but it behaves more
like a small layout engine than a fixed template: it applies a restrained deck
theme, reserves safe regions, adapts type size to text length, and uses
different compositions for metric, visual, table, and cover slides.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from .slide_schema import MetricBlock, PresentationSpec, SlideSpec, TextBlock


@dataclass(frozen=True)
class DeckTheme:
    background: tuple[int, int, int] = (247, 248, 250)
    surface: tuple[int, int, int] = (255, 255, 255)
    surface_alt: tuple[int, int, int] = (242, 246, 248)
    ink: tuple[int, int, int] = (24, 32, 45)
    muted: tuple[int, int, int] = (84, 96, 112)
    rule: tuple[int, int, int] = (205, 214, 224)
    primary: tuple[int, int, int] = (10, 115, 112)
    secondary: tuple[int, int, int] = (45, 76, 138)
    accent: tuple[int, int, int] = (128, 92, 45)
    pale_primary: tuple[int, int, int] = (229, 244, 242)
    pale_secondary: tuple[int, int, int] = (232, 238, 248)
    pale_neutral: tuple[int, int, int] = (241, 243, 246)
    title_font: str = "Aptos Display"
    body_font: str = "Aptos"


class PptxRenderer:
    """Render structured slide specs into an editable PPTX file."""

    def __init__(self, theme: DeckTheme | None = None):
        self.theme = theme or DeckTheme()

    def render(self, spec: PresentationSpec, output_path: Path) -> Path:
        try:
            from pptx import Presentation
            from pptx.dml.color import RGBColor
            from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
            from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
            from pptx.util import Inches, Pt
        except ImportError as exc:
            raise RuntimeError(
                "python-pptx is required for PPTX rendering. Install dependencies from requirements.txt."
            ) from exc

        self.RGBColor = RGBColor
        self.MSO_AUTO_SHAPE_TYPE = MSO_AUTO_SHAPE_TYPE
        self.PP_ALIGN = PP_ALIGN
        self.MSO_ANCHOR = MSO_ANCHOR
        self.Inches = Inches
        self.Pt = Pt

        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        blank_layout = prs.slide_layouts[6]
        for slide_index, slide_spec in enumerate(spec.slides, start=1):
            slide = prs.slides.add_slide(blank_layout)
            self._paint_background(slide, prs)

            layout = self._normalized_layout(slide_spec)
            if layout == "cover":
                self._render_cover(slide, slide_spec, slide_index)
            elif layout in {"statement", "metric_focus", "closing"} and not slide_spec.image_blocks and not slide_spec.table_blocks:
                self._render_statement(slide, slide_spec, slide_index, closing=(layout == "closing"))
            elif layout == "table_focus":
                self._render_table_focus(slide, slide_spec, slide_index)
            else:
                self._render_visual_or_mixed(slide, slide_spec, slide_index, visual_left=(layout == "visual_left"))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))
        return output_path

    def _normalized_layout(self, slide_spec: SlideSpec) -> str:
        layout = (slide_spec.layout or "auto").lower()
        if slide_spec.section_type == "opening":
            return "cover"
        if slide_spec.section_type == "ending":
            return "closing"
        if layout == "auto":
            if slide_spec.table_blocks:
                return "table_focus"
            if slide_spec.image_blocks:
                return "visual_right"
            if slide_spec.metric_blocks:
                return "metric_focus"
            return "statement"
        return layout

    def _paint_background(self, slide, prs) -> None:
        t = self.theme
        bg = slide.shapes.add_shape(self.MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = self._rgb(t.background)
        bg.line.fill.background()

        rail = slide.shapes.add_shape(self.MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, 0, prs.slide_width, self.Inches(0.06))
        rail.fill.solid()
        rail.fill.fore_color.rgb = self._rgb(t.primary)
        rail.line.fill.background()

        short_rail = slide.shapes.add_shape(self.MSO_AUTO_SHAPE_TYPE.RECTANGLE, 0, 0, self.Inches(1.75), self.Inches(0.06))
        short_rail.fill.solid()
        short_rail.fill.fore_color.rgb = self._rgb(t.secondary)
        short_rail.line.fill.background()

    def _render_cover(self, slide, slide_spec: SlideSpec, slide_index: int) -> None:
        t = self.theme
        title = self._clean_title(slide_spec.title)
        self._add_text(
            slide,
            title,
            self.Inches(0.78),
            self.Inches(0.82),
            self.Inches(6.75),
            self.Inches(1.35),
            size=self._fit_title_size(title, base=34, min_size=25),
            bold=True,
            color=t.ink,
            font=t.title_font,
            max_lines=2,
        )

        if slide_spec.takeaway:
            self._add_text(
                slide,
                slide_spec.takeaway,
                self.Inches(0.82),
                self.Inches(2.42),
                self.Inches(6.25),
                self.Inches(0.72),
                size=17,
                bold=True,
                color=t.primary,
                font=t.body_font,
                max_lines=2,
            )

        bullets_top = self.Inches(3.42)
        self._add_bullet_list(
            slide,
            slide_spec.text_blocks[:3],
            self.Inches(0.9),
            bullets_top,
            self.Inches(5.8),
            self.Inches(1.45),
            size=13,
            max_items=3,
        )

        if slide_spec.metric_blocks:
            self._render_metric_band(
                slide,
                slide_spec.metric_blocks[:3],
                self.Inches(0.88),
                self.Inches(5.38),
                self.Inches(5.9),
                self.Inches(0.72),
            )

        if slide_spec.image_blocks:
            self._render_images(
                slide,
                slide_spec,
                self.Inches(7.35),
                self.Inches(0.88),
                self.Inches(5.15),
                self.Inches(5.55),
                caption=True,
            )
        else:
            self._render_abstract_mark(slide, self.Inches(7.55), self.Inches(1.15), self.Inches(4.8), self.Inches(4.8))

        self._footer(slide, slide_index)

    def _render_statement(self, slide, slide_spec: SlideSpec, slide_index: int, closing: bool = False) -> None:
        t = self.theme
        title = self._clean_title(slide_spec.title)
        self._add_text(
            slide,
            title,
            self.Inches(0.75),
            self.Inches(0.52),
            self.Inches(11.85),
            self.Inches(0.58),
            size=self._fit_title_size(title, base=23, min_size=18),
            bold=True,
            color=t.ink,
            font=t.title_font,
            max_lines=1,
        )

        claim = slide_spec.takeaway or (slide_spec.text_blocks[0].text if slide_spec.text_blocks else "")
        self._add_text(
            slide,
            claim,
            self.Inches(0.86),
            self.Inches(1.42),
            self.Inches(7.05),
            self.Inches(1.05),
            size=self._fit_title_size(claim, base=22 if not closing else 24, min_size=17),
            bold=True,
            color=t.primary if not closing else t.secondary,
            font=t.title_font,
            max_lines=2,
        )

        self._add_bullet_list(
            slide,
            slide_spec.text_blocks[:5],
            self.Inches(0.96),
            self.Inches(2.88),
            self.Inches(7.0),
            self.Inches(2.85),
            size=14,
            max_items=5,
        )

        if slide_spec.metric_blocks:
            self._render_metric_column(
                slide,
                slide_spec.metric_blocks[:4],
                self.Inches(8.5),
                self.Inches(1.42),
                self.Inches(3.45),
                self.Inches(4.75),
            )
        else:
            self._render_abstract_mark(slide, self.Inches(8.65), self.Inches(1.7), self.Inches(3.15), self.Inches(3.7))

        self._footer(slide, slide_index)

    def _render_visual_or_mixed(self, slide, slide_spec: SlideSpec, slide_index: int, visual_left: bool = False) -> None:
        t = self.theme
        self._render_header(slide, slide_spec)

        image_left = self.Inches(0.75 if visual_left else 6.2)
        text_left = self.Inches(6.85 if visual_left else 0.82)
        visual_width = self.Inches(5.65 if visual_left else 6.25)
        text_width = self.Inches(5.6 if visual_left else 5.0)

        has_table = bool(slide_spec.table_blocks)
        image_height = self.Inches(3.0 if has_table else 4.45)
        self._render_images(
            slide,
            slide_spec,
            image_left,
            self.Inches(1.55),
            visual_width,
            image_height,
            caption=True,
        )

        self._add_bullet_list(
            slide,
            slide_spec.text_blocks[:4],
            text_left,
            self.Inches(1.65),
            text_width,
            self.Inches(3.1 if has_table else 3.85),
            size=13,
            max_items=4,
        )

        if has_table:
            self._render_table(
                slide,
                slide_spec,
                self.Inches(0.85),
                self.Inches(5.35),
                self.Inches(11.6),
                self.Inches(1.25),
            )
        elif slide_spec.metric_blocks:
            self._render_metric_band(
                slide,
                slide_spec.metric_blocks[:3],
                text_left,
                self.Inches(5.55),
                text_width,
                self.Inches(0.66),
            )

        self._footer(slide, slide_index)

    def _render_table_focus(self, slide, slide_spec: SlideSpec, slide_index: int) -> None:
        self._render_header(slide, slide_spec)
        has_image = bool(slide_spec.image_blocks)
        if has_image:
            self._render_images(
                slide,
                slide_spec,
                self.Inches(0.85),
                self.Inches(1.55),
                self.Inches(5.15),
                self.Inches(2.25),
                caption=False,
            )
            bullet_left = self.Inches(6.35)
            bullet_width = self.Inches(5.9)
        else:
            bullet_left = self.Inches(0.9)
            bullet_width = self.Inches(11.45)

        self._add_bullet_list(
            slide,
            slide_spec.text_blocks[:4],
            bullet_left,
            self.Inches(1.58),
            bullet_width,
            self.Inches(1.78 if has_image else 1.6),
            size=12.5,
            max_items=4,
        )

        if slide_spec.metric_blocks and not has_image:
            self._render_metric_band(
                slide,
                slide_spec.metric_blocks[:4],
                self.Inches(0.9),
                self.Inches(2.95),
                self.Inches(11.35),
                self.Inches(0.58),
            )

        table_top = self.Inches(4.08 if has_image else 3.75)
        table_height = self.Inches(2.18)
        self._render_table(slide, slide_spec, self.Inches(0.9), table_top, self.Inches(11.45), table_height)
        self._footer(slide, slide_index)

    def _render_header(self, slide, slide_spec: SlideSpec) -> None:
        t = self.theme
        title = self._clean_title(slide_spec.title)
        self._add_text(
            slide,
            title,
            self.Inches(0.72),
            self.Inches(0.34),
            self.Inches(11.85),
            self.Inches(0.52),
            size=self._fit_title_size(title, base=22, min_size=17),
            bold=True,
            color=t.ink,
            font=t.title_font,
            max_lines=1,
        )
        if slide_spec.takeaway:
            self._add_text(
                slide,
                slide_spec.takeaway,
                self.Inches(0.74),
                self.Inches(0.92),
                self.Inches(11.45),
                self.Inches(0.38),
                size=11.5,
                bold=True,
                color=t.primary,
                font=t.body_font,
                max_lines=1,
            )

    def _render_images(self, slide, slide_spec: SlideSpec, image_left, image_top, image_width, max_height, caption: bool) -> None:
        count = max(1, min(2, len(slide_spec.image_blocks)))
        slot_height = int(max_height / count)

        for index, block in enumerate(slide_spec.image_blocks[:2]):
            top = int(image_top + slot_height * index)
            picture_height = int(slot_height - (self.Inches(0.32) if caption else self.Inches(0.08)))
            image_path = Path(block.path) if block.path else None

            if image_path and image_path.exists():
                left, fitted_top, width, height = self._fit_picture(
                    image_path,
                    image_left,
                    top,
                    image_width,
                    picture_height,
                )
                slide.shapes.add_picture(str(image_path), left, fitted_top, width=width, height=height)
            else:
                self._placeholder(slide, image_left, top, image_width, picture_height, block.placeholder_text or block.title)

            caption_text = self._truncate(f"{block.title}: {block.caption}" if block.title and block.caption else block.title or block.caption, 96)
            if caption and caption_text:
                self._add_text(
                    slide,
                    caption_text,
                    image_left,
                    int(top + slot_height - self.Inches(0.32)),
                    image_width,
                    self.Inches(0.3),
                    size=8.0,
                    color=self.theme.muted,
                    font=self.theme.body_font,
                    max_lines=1,
                )

    def _render_metric_band(self, slide, metrics: Sequence[MetricBlock], left, top, width, height) -> None:
        metrics = list(metrics)[:4]
        if not metrics:
            return
        gap = int(width * 0.018)
        slot_width = int((int(width) - gap * (len(metrics) - 1)) / len(metrics))
        fills = [self.theme.pale_primary, self.theme.pale_secondary, self.theme.pale_neutral, (238, 242, 244)]
        accents = [self.theme.primary, self.theme.secondary, self.theme.ink, self.theme.accent]
        for index, metric in enumerate(metrics):
            x = int(left + index * (slot_width + gap))
            self._rounded_rect(slide, x, top, slot_width, height, fills[index % len(fills)], self.theme.rule)
            self._add_text(slide, self._metric_value(metric.value), x + int(slot_width * 0.07), int(top + height * 0.08), int(slot_width * 0.86), int(height * 0.42), 14, True, accents[index % len(accents)], self.theme.title_font, 1)
            self._add_text(slide, self._metric_label(metric), x + int(slot_width * 0.07), int(top + height * 0.53), int(slot_width * 0.86), int(height * 0.32), 7.8, False, self.theme.muted, self.theme.body_font, 1)

    def _render_metric_column(self, slide, metrics: Sequence[MetricBlock], left, top, width, height) -> None:
        metrics = list(metrics)[:4]
        if not metrics:
            return
        gap = int(height * 0.035)
        slot_height = int((int(height) - gap * (len(metrics) - 1)) / len(metrics))
        for index, metric in enumerate(metrics):
            y = int(top + index * (slot_height + gap))
            fill = self.theme.pale_primary if index % 2 == 0 else self.theme.pale_secondary
            self._rounded_rect(slide, left, y, width, slot_height, fill, self.theme.rule)
            self._add_text(slide, self._metric_value(metric.value), int(left + width * 0.08), y + int(slot_height * 0.12), int(width * 0.84), int(slot_height * 0.42), 20, True, self.theme.primary, self.theme.title_font, 1)
            self._add_text(slide, self._metric_label(metric), int(left + width * 0.08), y + int(slot_height * 0.6), int(width * 0.84), int(slot_height * 0.28), 8.5, False, self.theme.muted, self.theme.body_font, 1)

    def _render_table(self, slide, slide_spec: SlideSpec, table_left, table_top, table_width, table_height) -> None:
        if not slide_spec.table_blocks:
            return
        table_block = slide_spec.table_blocks[0]
        rows = (table_block.rows or [["No table data"]])[:6]
        columns = min(max(len(row) for row in rows), 4)
        rows = [(row + [""] * columns)[:columns] for row in rows]

        shape = slide.shapes.add_table(len(rows), columns, table_left, table_top, table_width, table_height)
        table = shape.table
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                cell = table.cell(row_index, col_index)
                cell.text = self._truncate(str(value), 44)
                paragraph = cell.text_frame.paragraphs[0]
                paragraph.font.size = self.Pt(9.5 if row_index else 10.5)
                paragraph.font.bold = row_index == 0
                paragraph.font.name = self.theme.body_font
                paragraph.font.color.rgb = self._rgb(self.theme.ink)
                cell.fill.solid()
                cell.fill.fore_color.rgb = self._rgb(self.theme.pale_primary if row_index == 0 else self.theme.surface if row_index % 2 else self.theme.surface_alt)

        if table_block.caption:
            self._add_text(slide, self._truncate(table_block.caption, 110), table_left, int(table_top + table_height + self.Pt(5)), table_width, self.Pt(20), 8.5, False, self.theme.muted, self.theme.body_font, 1)

    def _add_bullet_list(self, slide, blocks: Sequence[TextBlock], left, top, width, height, size: float, max_items: int) -> None:
        blocks = list(blocks)[:max_items]
        if not blocks:
            return
        text = "\n".join(f"- {self._truncate(block.text, 86)}" for block in blocks)
        self._add_text(slide, text, left, top, width, height, size=size, color=self.theme.ink, font=self.theme.body_font, max_lines=max_items)

    def _add_text(self, slide, text: str, left, top, width, height, size: float, bold: bool = False, color=None, font: str | None = None, max_lines: int = 2):
        text = self._truncate_lines(text or "", max_lines=max_lines)
        box = slide.shapes.add_textbox(left, top, width, height)
        frame = box.text_frame
        frame.word_wrap = True
        frame.margin_left = self.Inches(0.02)
        frame.margin_right = self.Inches(0.02)
        frame.margin_top = self.Inches(0.01)
        frame.margin_bottom = self.Inches(0.01)
        frame.vertical_anchor = self.MSO_ANCHOR.TOP
        frame.clear()
        lines = text.split("\n") or [""]
        for index, line in enumerate(lines):
            p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            p.text = line
            p.font.size = self.Pt(size)
            p.font.bold = bold
            p.font.name = font or self.theme.body_font
            p.font.color.rgb = self._rgb(color or self.theme.ink)
            p.space_after = self.Pt(5 if len(lines) > 1 else 0)
        return box

    def _rounded_rect(self, slide, left, top, width, height, fill, line) -> None:
        shape = slide.shapes.add_shape(self.MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = self._rgb(fill)
        shape.line.color.rgb = self._rgb(line)

    def _placeholder(self, slide, left, top, width, height, text: str) -> None:
        self._rounded_rect(slide, left, top, width, height, self.theme.surface_alt, self.theme.rule)
        self._add_text(slide, text or "Original figure", left, int(top + height * 0.43), width, self.Inches(0.28), 10, False, self.theme.muted, self.theme.body_font, 1)

    def _render_abstract_mark(self, slide, left, top, width, height) -> None:
        for index, scale in enumerate((1.0, 0.72, 0.46)):
            w = int(width * scale)
            h = int(height * (0.18 + index * 0.03))
            y = int(top + height * (0.18 + index * 0.2))
            fill = [self.theme.pale_primary, self.theme.pale_secondary, self.theme.pale_neutral][index]
            self._rounded_rect(slide, int(left), y, w, h, fill, self.theme.rule)

    def _footer(self, slide, slide_index: int) -> None:
        self._add_text(slide, str(slide_index), self.Inches(11.95), self.Inches(7.03), self.Inches(0.45), self.Inches(0.18), 8, False, self.theme.muted, self.theme.body_font, 1)

    def _fit_picture(self, image_path: Path, box_left, box_top, box_width, box_height):
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                source_width, source_height = img.size
            scale = min(int(box_width) / max(1, source_width), int(box_height) / max(1, source_height))
            width = max(1, int(source_width * scale))
            height = max(1, int(source_height * scale))
            left = int(box_left + (int(box_width) - width) / 2)
            top = int(box_top + (int(box_height) - height) / 2)
            return left, top, width, height
        except Exception:
            return box_left, box_top, box_width, box_height

    def _fit_title_size(self, text: str, base: int, min_size: int) -> int:
        length = len(text or "")
        if length <= 42:
            return base
        if length <= 62:
            return max(min_size, base - 3)
        if length <= 82:
            return max(min_size, base - 6)
        return min_size

    def _clean_title(self, text: str) -> str:
        return self._truncate((text or "").replace(" - Cover", ""), 82)

    def _truncate_lines(self, text: str, max_lines: int) -> str:
        lines = [line.strip() for line in str(text).split("\n") if line.strip()]
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = self._truncate(lines[-1], max(12, len(lines[-1]) - 3))
        return "\n".join(lines)

    def _truncate(self, text: str, max_len: int) -> str:
        text = " ".join((text or "").split())
        if len(text) <= max_len:
            return text
        return text[: max_len - 1].rstrip(" ,;:-") + "..."

    def _metric_value(self, value: str) -> str:
        return self._truncate(value or "", 18)

    def _metric_label(self, metric: MetricBlock) -> str:
        label = metric.label or metric.note
        if not label and metric.note:
            label = metric.note
        return self._truncate(label or "", 34)

    def _rgb(self, value):
        return self.RGBColor(*value)
