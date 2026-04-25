"""
Deterministic PPTX renderer for structured slide specs.
"""
from pathlib import Path

from .slide_schema import PresentationSpec, SlideSpec


class PptxRenderer:
    """Render structured slide specs into an editable PPTX file."""

    def render(self, spec: PresentationSpec, output_path: Path) -> Path:
        try:
            from pptx import Presentation
            from pptx.dml.color import RGBColor
            from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
            from pptx.enum.text import PP_ALIGN
            from pptx.util import Inches, Pt
        except ImportError as exc:
            raise RuntimeError(
                "python-pptx is required for PPTX rendering. Install dependencies from requirements.txt."
            ) from exc

        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        blank_layout = prs.slide_layouts[6]
        for slide_index, slide_spec in enumerate(spec.slides):
            slide = prs.slides.add_slide(blank_layout)
            layout = slide_spec.layout or "auto"

            background = slide.shapes.add_shape(
                MSO_AUTO_SHAPE_TYPE.RECTANGLE,
                0,
                0,
                prs.slide_width,
                prs.slide_height,
            )
            background.fill.solid()
            background.fill.fore_color.rgb = RGBColor(255, 253, 248)
            background.line.fill.background()

            accent = slide.shapes.add_shape(
                MSO_AUTO_SHAPE_TYPE.RECTANGLE,
                0,
                0,
                prs.slide_width,
                Inches(0.08),
            )
            accent.fill.solid()
            accent.fill.fore_color.rgb = RGBColor(15, 118, 110)
            accent.line.fill.background()
            accent_gold = slide.shapes.add_shape(
                MSO_AUTO_SHAPE_TYPE.RECTANGLE,
                0,
                0,
                Inches(2.35),
                Inches(0.08),
            )
            accent_gold.fill.solid()
            accent_gold.fill.fore_color.rgb = RGBColor(180, 126, 35)
            accent_gold.line.fill.background()

            if layout == "cover":
                self._render_cover(slide, slide_spec, RGBColor, MSO_AUTO_SHAPE_TYPE, PP_ALIGN, Inches, Pt)
                continue

            if layout in {"statement", "metric_focus", "closing"} and not slide_spec.image_blocks and not slide_spec.table_blocks:
                self._render_statement_slide(slide, slide_spec, slide_index, RGBColor, MSO_AUTO_SHAPE_TYPE, Inches, Pt)
                continue

            title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.3), Inches(12.1), Inches(0.8))
            title_frame = title_box.text_frame
            title_frame.word_wrap = True
            title_paragraph = title_frame.paragraphs[0]
            title_paragraph.text = slide_spec.title
            title_paragraph.font.size = Pt(25)
            title_paragraph.font.bold = True
            title_paragraph.font.name = "Aptos Display"
            title_paragraph.font.color.rgb = RGBColor(30, 41, 59)

            if slide_spec.takeaway:
                takeaway_box = slide.shapes.add_textbox(Inches(0.72), Inches(1.02), Inches(11.8), Inches(0.45))
                takeaway_frame = takeaway_box.text_frame
                takeaway_frame.word_wrap = True
                takeaway = takeaway_frame.paragraphs[0]
                takeaway.text = slide_spec.takeaway
                takeaway.font.size = Pt(13)
                takeaway.font.bold = True
                takeaway.font.name = "Aptos"
                takeaway.font.color.rgb = RGBColor(15, 118, 110)

            has_visuals = bool(slide_spec.image_blocks or slide_spec.table_blocks)
            body_left = Inches(0.75)
            body_top = Inches(1.62)
            body_width = Inches(5.05) if slide_spec.image_blocks else Inches(11.7)
            body_height = Inches(3.35 if slide_spec.image_blocks and slide_spec.table_blocks else 4.75 if has_visuals else 4.9)

            body_box = slide.shapes.add_textbox(body_left, body_top, body_width, body_height)
            body_frame = body_box.text_frame
            body_frame.word_wrap = True
            body_frame.clear()

            for index, block in enumerate(slide_spec.text_blocks or []):
                paragraph = body_frame.paragraphs[0] if index == 0 else body_frame.add_paragraph()
                paragraph.text = f"- {block.text}" if block.role in {"bullet", "body"} else block.text
                paragraph.level = block.bullet_level
                paragraph.font.size = Pt(15)
                paragraph.font.name = "Aptos"
                paragraph.font.color.rgb = RGBColor(37, 48, 68)
                paragraph.space_after = Pt(12)

            if not slide_spec.text_blocks:
                paragraph = body_frame.paragraphs[0]
                paragraph.text = ""
                paragraph.font.size = Pt(15)
                paragraph.font.name = "Aptos"

            if slide_spec.image_blocks:
                image_left = Inches(6.25 if layout != "visual_left" else 0.75)
                if layout == "visual_left":
                    body_box.left = Inches(6.75)
                self._render_images(
                    slide,
                    slide_spec,
                    image_left=image_left,
                    image_top=Inches(1.62),
                    image_width=Inches(6.25),
                    max_height=Inches(3.15 if slide_spec.table_blocks else 4.65),
                    RGBColor=RGBColor,
                    MSO_AUTO_SHAPE_TYPE=MSO_AUTO_SHAPE_TYPE,
                    PP_ALIGN=PP_ALIGN,
                    Inches=Inches,
                    Pt=Pt,
                )

            if slide_spec.table_blocks:
                if layout == "table_focus":
                    table_left = Inches(0.85)
                    table_top = Inches(3.55 if slide_spec.text_blocks else 1.75)
                    table_width = Inches(11.65)
                    table_height = Inches(2.45)
                else:
                    table_left = Inches(0.85)
                    table_top = Inches(5.35)
                    table_width = Inches(11.65)
                    table_height = Inches(1.45)
                self._render_table(
                    slide,
                    slide_spec,
                    table_left=table_left,
                    table_top=table_top,
                    table_width=table_width,
                    table_height=table_height,
                    RGBColor=RGBColor,
                    Pt=Pt,
                )

            if slide_spec.metric_blocks and layout != "table_focus":
                self._render_metric_band(
                    slide,
                    slide_spec,
                    left=Inches(0.75),
                    top=Inches(6.15),
                    width=Inches(11.65),
                    height=Inches(0.55),
                    RGBColor=RGBColor,
                    MSO_AUTO_SHAPE_TYPE=MSO_AUTO_SHAPE_TYPE,
                    Pt=Pt,
                )

            if slide_spec.notes:
                notes_box = slide.shapes.add_textbox(Inches(0.72), Inches(6.95), Inches(11.8), Inches(0.28))
                notes_frame = notes_box.text_frame
                notes_frame.word_wrap = True
                notes_paragraph = notes_frame.paragraphs[0]
                notes_paragraph.text = self._truncate(" | ".join(slide_spec.notes), 150)
                notes_paragraph.font.size = Pt(8)
                notes_paragraph.font.name = "Aptos"
                notes_paragraph.font.italic = True
                notes_paragraph.font.color.rgb = RGBColor(103, 116, 139)

            footer = slide.shapes.add_textbox(Inches(11.7), Inches(7.03), Inches(0.9), Inches(0.22))
            footer_p = footer.text_frame.paragraphs[0]
            footer_p.text = str(slide_index + 1)
            footer_p.font.size = Pt(8)
            footer_p.font.name = "Aptos"
            footer_p.font.color.rgb = RGBColor(100, 116, 139)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))
        return output_path

    def _render_cover(self, slide, slide_spec: SlideSpec, RGBColor, MSO_AUTO_SHAPE_TYPE, PP_ALIGN, Inches, Pt) -> None:
        title_box = slide.shapes.add_textbox(Inches(0.85), Inches(0.9), Inches(7.2), Inches(1.55))
        title_p = title_box.text_frame.paragraphs[0]
        title_p.text = slide_spec.title
        title_p.font.size = Pt(36)
        title_p.font.bold = True
        title_p.font.name = "Aptos Display"
        title_p.font.color.rgb = RGBColor(28, 38, 54)

        if slide_spec.takeaway:
            takeaway_box = slide.shapes.add_textbox(Inches(0.9), Inches(2.7), Inches(6.7), Inches(0.75))
            takeaway_p = takeaway_box.text_frame.paragraphs[0]
            takeaway_p.text = slide_spec.takeaway
            takeaway_p.font.size = Pt(18)
            takeaway_p.font.bold = True
            takeaway_p.font.name = "Aptos"
            takeaway_p.font.color.rgb = RGBColor(15, 118, 110)

        body_box = slide.shapes.add_textbox(Inches(0.95), Inches(3.65), Inches(5.95), Inches(1.85))
        body_frame = body_box.text_frame
        body_frame.clear()
        for index, block in enumerate(slide_spec.text_blocks[:4]):
            paragraph = body_frame.paragraphs[0] if index == 0 else body_frame.add_paragraph()
            paragraph.text = f"- {block.text}"
            paragraph.font.size = Pt(15)
            paragraph.font.name = "Aptos"
            paragraph.font.color.rgb = RGBColor(37, 48, 68)
            paragraph.space_after = Pt(10)

        if slide_spec.metric_blocks:
            self._render_metric_band(
                slide,
                slide_spec,
                left=Inches(0.9),
                top=Inches(5.75),
                width=Inches(6.2),
                height=Inches(0.7),
                RGBColor=RGBColor,
                MSO_AUTO_SHAPE_TYPE=MSO_AUTO_SHAPE_TYPE,
                Pt=Pt,
            )

        if slide_spec.image_blocks:
            self._render_images(
                slide,
                slide_spec,
                image_left=Inches(7.35),
                image_top=Inches(0.95),
                image_width=Inches(5.05),
                max_height=Inches(5.65),
                RGBColor=RGBColor,
                MSO_AUTO_SHAPE_TYPE=MSO_AUTO_SHAPE_TYPE,
                PP_ALIGN=PP_ALIGN,
                Inches=Inches,
                Pt=Pt,
            )

    def _render_statement_slide(self, slide, slide_spec: SlideSpec, slide_index, RGBColor, MSO_AUTO_SHAPE_TYPE, Inches, Pt) -> None:
        title_box = slide.shapes.add_textbox(Inches(0.75), Inches(0.52), Inches(11.9), Inches(0.65))
        title_p = title_box.text_frame.paragraphs[0]
        title_p.text = slide_spec.title
        title_p.font.size = Pt(24)
        title_p.font.bold = True
        title_p.font.name = "Aptos Display"
        title_p.font.color.rgb = RGBColor(30, 41, 59)

        claim = slide_spec.takeaway or (slide_spec.text_blocks[0].text if slide_spec.text_blocks else "")
        claim_box = slide.shapes.add_textbox(Inches(0.85), Inches(1.45), Inches(7.0), Inches(1.25))
        claim_p = claim_box.text_frame.paragraphs[0]
        claim_p.text = claim
        claim_p.font.size = Pt(24)
        claim_p.font.bold = True
        claim_p.font.name = "Aptos Display"
        claim_p.font.color.rgb = RGBColor(15, 118, 110)

        bullet_box = slide.shapes.add_textbox(Inches(0.95), Inches(3.05), Inches(7.1), Inches(2.65))
        bullet_frame = bullet_box.text_frame
        bullet_frame.clear()
        for index, block in enumerate(slide_spec.text_blocks[:5]):
            paragraph = bullet_frame.paragraphs[0] if index == 0 else bullet_frame.add_paragraph()
            paragraph.text = f"- {block.text}"
            paragraph.font.size = Pt(16)
            paragraph.font.name = "Aptos"
            paragraph.font.color.rgb = RGBColor(51, 65, 85)
            paragraph.space_after = Pt(11)

        if slide_spec.metric_blocks:
            self._render_metric_column(
                slide,
                slide_spec,
                left=Inches(8.45),
                top=Inches(1.55),
                width=Inches(3.55),
                height=Inches(4.6),
                RGBColor=RGBColor,
                MSO_AUTO_SHAPE_TYPE=MSO_AUTO_SHAPE_TYPE,
                Pt=Pt,
            )
        else:
            line = slide.shapes.add_shape(
                MSO_AUTO_SHAPE_TYPE.RECTANGLE,
                Inches(8.5),
                Inches(1.65),
                Inches(0.08),
                Inches(4.2),
            )
            line.fill.solid()
            line.fill.fore_color.rgb = RGBColor(180, 126, 35)
            line.line.fill.background()

        footer = slide.shapes.add_textbox(Inches(11.7), Inches(7.03), Inches(0.9), Inches(0.22))
        footer_p = footer.text_frame.paragraphs[0]
        footer_p.text = str(slide_index + 1)
        footer_p.font.size = Pt(8)
        footer_p.font.name = "Aptos"
        footer_p.font.color.rgb = RGBColor(100, 116, 139)

    def _render_images(
        self,
        slide,
        slide_spec: SlideSpec,
        image_left,
        image_top,
        image_width,
        max_height,
        RGBColor,
        MSO_AUTO_SHAPE_TYPE,
        PP_ALIGN,
        Inches,
        Pt,
    ) -> None:
        count = max(1, min(2, len(slide_spec.image_blocks)))
        slot_height = int(max_height / count)

        for index, block in enumerate(slide_spec.image_blocks[:2]):
            top = int(image_top + (slot_height * index))
            image_path = Path(block.path) if block.path else None
            picture_max_height = int(slot_height - Inches(0.35))

            if image_path and image_path.exists():
                pic_left, pic_top, pic_width, pic_height = self._fit_picture(
                    image_path=image_path,
                    box_left=image_left,
                    box_top=top,
                    box_width=image_width,
                    box_height=picture_max_height,
                )
                slide.shapes.add_picture(str(image_path), pic_left, pic_top, width=pic_width, height=pic_height)
            else:
                placeholder = slide.shapes.add_shape(
                    MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
                    image_left,
                    top,
                    image_width,
                    picture_max_height,
                )
                placeholder.fill.solid()
                placeholder.fill.fore_color.rgb = RGBColor(242, 244, 247)
                placeholder.line.color.rgb = RGBColor(180, 186, 194)
                text_frame = placeholder.text_frame
                text_frame.word_wrap = True
                paragraph = text_frame.paragraphs[0]
                paragraph.text = block.placeholder_text or block.title or "Image reference"
                paragraph.alignment = PP_ALIGN.CENTER
                paragraph.font.size = Pt(12)
                paragraph.font.name = "Aptos"

            caption_text = block.title or block.caption
            if block.title and block.caption:
                caption_text = f"{block.title}: {block.caption}"
            if caption_text:
                caption = slide.shapes.add_textbox(image_left, int(top + slot_height - Inches(0.28)), image_width, Inches(0.25))
                caption_frame = caption.text_frame
                caption_paragraph = caption_frame.paragraphs[0]
                caption_paragraph.text = self._truncate(caption_text, 120)
                caption_paragraph.font.size = Pt(10)
                caption_paragraph.font.name = "Aptos"
                caption_paragraph.font.color.rgb = RGBColor(71, 85, 105)

    def _fit_picture(self, image_path: Path, box_left, box_top, box_width, box_height):
        """Return centered picture bounds that preserve source image aspect ratio."""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                source_width, source_height = img.size
            if source_width <= 0 or source_height <= 0:
                raise ValueError("Invalid image dimensions")

            scale = min(int(box_width) / source_width, int(box_height) / source_height)
            fitted_width = max(1, int(source_width * scale))
            fitted_height = max(1, int(source_height * scale))
            fitted_left = int(box_left + (int(box_width) - fitted_width) / 2)
            fitted_top = int(box_top + (int(box_height) - fitted_height) / 2)
            return fitted_left, fitted_top, fitted_width, fitted_height
        except Exception:
            return box_left, box_top, box_width, box_height

    def _render_metric_band(self, slide, slide_spec: SlideSpec, left, top, width, height, RGBColor, MSO_AUTO_SHAPE_TYPE, Pt) -> None:
        metrics = slide_spec.metric_blocks[:4]
        if not metrics:
            return
        gap = int(width * 0.025)
        slot_width = int((int(width) - gap * (len(metrics) - 1)) / len(metrics))
        colors = [RGBColor(230, 244, 241), RGBColor(252, 244, 222), RGBColor(232, 238, 247), RGBColor(245, 239, 232)]
        accent_colors = [RGBColor(15, 118, 110), RGBColor(180, 126, 35), RGBColor(71, 85, 105), RGBColor(120, 80, 45)]
        for index, metric in enumerate(metrics):
            x = int(left + index * (slot_width + gap))
            shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, x, top, slot_width, height)
            shape.fill.solid()
            shape.fill.fore_color.rgb = colors[index % len(colors)]
            shape.line.color.rgb = accent_colors[index % len(accent_colors)]

            value_box = slide.shapes.add_textbox(x + int(slot_width * 0.06), int(top + int(height * 0.08)), int(slot_width * 0.88), int(height * 0.42))
            value_p = value_box.text_frame.paragraphs[0]
            value_p.text = metric.value
            value_p.font.size = Pt(15)
            value_p.font.bold = True
            value_p.font.name = "Aptos Display"
            value_p.font.color.rgb = accent_colors[index % len(accent_colors)]

            label_box = slide.shapes.add_textbox(x + int(slot_width * 0.06), int(top + int(height * 0.52)), int(slot_width * 0.88), int(height * 0.36))
            label_p = label_box.text_frame.paragraphs[0]
            label_p.text = self._truncate(metric.label or metric.note, 28)
            label_p.font.size = Pt(8)
            label_p.font.name = "Aptos"
            label_p.font.color.rgb = RGBColor(51, 65, 85)

    def _render_metric_column(self, slide, slide_spec: SlideSpec, left, top, width, height, RGBColor, MSO_AUTO_SHAPE_TYPE, Pt) -> None:
        metrics = slide_spec.metric_blocks[:4]
        if not metrics:
            return
        gap = int(height * 0.035)
        slot_height = int((int(height) - gap * (len(metrics) - 1)) / len(metrics))
        for index, metric in enumerate(metrics):
            y = int(top + index * (slot_height + gap))
            shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, left, y, width, slot_height)
            shape.fill.solid()
            shape.fill.fore_color.rgb = RGBColor(239, 248, 246) if index % 2 == 0 else RGBColor(253, 247, 231)
            shape.line.color.rgb = RGBColor(174, 189, 186)

            value_box = slide.shapes.add_textbox(int(left + int(width * 0.08)), y + int(slot_height * 0.12), int(width * 0.82), int(slot_height * 0.45))
            value_p = value_box.text_frame.paragraphs[0]
            value_p.text = metric.value
            value_p.font.size = Pt(22)
            value_p.font.bold = True
            value_p.font.name = "Aptos Display"
            value_p.font.color.rgb = RGBColor(15, 118, 110)

            label_box = slide.shapes.add_textbox(int(left + int(width * 0.08)), y + int(slot_height * 0.58), int(width * 0.82), int(slot_height * 0.32))
            label_p = label_box.text_frame.paragraphs[0]
            label_p.text = self._truncate(metric.label or metric.note, 36)
            label_p.font.size = Pt(9)
            label_p.font.name = "Aptos"
            label_p.font.color.rgb = RGBColor(51, 65, 85)

    def _truncate(self, text: str, max_len: int) -> str:
        text = " ".join((text or "").split())
        if len(text) <= max_len:
            return text
        return text[: max_len - 1].rstrip() + "..."

    def _render_table(self, slide, slide_spec: SlideSpec, table_left, table_top, table_width, table_height, RGBColor, Pt) -> None:
        table_block = slide_spec.table_blocks[0]
        rows = table_block.rows or [["No table data"]]
        rows = rows[:6]
        columns = max(len(row) for row in rows)
        rows = [row + [""] * (columns - len(row)) for row in rows]

        shape = slide.shapes.add_table(len(rows), columns, table_left, table_top, table_width, table_height)
        table = shape.table

        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                cell = table.cell(row_index, col_index)
                cell.text = value
                paragraph = cell.text_frame.paragraphs[0]
                paragraph.font.size = Pt(11 if row_index == 0 else 10)
                paragraph.font.bold = row_index == 0
                paragraph.font.name = "Aptos"
                paragraph.font.color.rgb = RGBColor(30, 41, 59)
                if row_index == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(222, 242, 238)
                elif row_index % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(248, 250, 252)
                else:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(255, 253, 248)

        if table_block.caption:
            caption = slide.shapes.add_textbox(table_left, int(table_top + table_height + Pt(6)), table_width, Pt(22))
            caption_p = caption.text_frame.paragraphs[0]
            caption_p.text = self._truncate(table_block.caption, 120)
            caption_p.font.size = Pt(9)
            caption_p.font.name = "Aptos"
            caption_p.font.color.rgb = RGBColor(71, 85, 105)
