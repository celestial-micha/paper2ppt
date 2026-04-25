"""
Convert content plans into structured slide specifications.
"""
import html
import re
from typing import List

from .content_planner import ContentPlan, Section
from .slide_schema import ImageBlock, PresentationSpec, SlideSpec, TableBlock, TextBlock


def build_presentation_spec(
    plan: ContentPlan,
    title: str = "Presentation",
    source_plan_path: str = "",
) -> PresentationSpec:
    """Build a structured presentation spec from an existing content plan."""
    slides = [build_slide_spec(section, plan) for section in plan.sections]
    return PresentationSpec(
        title=title,
        slides=slides,
        metadata=plan.metadata,
        source_plan_path=source_plan_path or None,
    )


def build_slide_spec(section: Section, plan: ContentPlan) -> SlideSpec:
    """Map a plan section into a single slide specification."""
    text_blocks = [
        TextBlock(text=text, role="body", bullet_level=0)
        for text in _content_to_blocks(section.content)
    ]
    image_blocks = _build_image_blocks(section, plan)
    table_blocks = _build_table_blocks(section, plan)
    notes = _build_notes(section)

    return SlideSpec(
        slide_id=section.id,
        title=section.title or "Untitled Slide",
        text_blocks=text_blocks,
        image_blocks=image_blocks,
        table_blocks=table_blocks,
        notes=notes,
        section_type=section.section_type,
    )


def _content_to_blocks(content: str) -> List[str]:
    """Split long plan content into editable paragraph-sized blocks."""
    normalized = re.sub(r"\s+", " ", (content or "").strip())
    if not normalized:
        return []

    sentences = re.split(r"(?<=[.!?;])\s+(?=[A-Z0-9(])", normalized)
    blocks: List[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= 220:
            current = candidate
            continue

        if current:
            blocks.append(current)
        current = sentence

    if current:
        blocks.append(current)

    if len(blocks) > 6:
        head = blocks[:5]
        tail = " ".join(blocks[5:])
        head.append(tail)
        blocks = head

    return blocks


def _build_image_blocks(section: Section, plan: ContentPlan) -> List[ImageBlock]:
    blocks: List[ImageBlock] = []
    for ref in section.figures:
        figure = plan.figures_index.get(ref.figure_id)
        if not figure:
            blocks.append(
                ImageBlock(
                    path="",
                    title=ref.figure_id,
                    placeholder_text=ref.focus or ref.figure_id,
                )
            )
            continue

        placeholder = ref.focus or figure.caption or figure.figure_id
        blocks.append(
            ImageBlock(
                path=figure.image_path,
                caption=figure.caption or "",
                title=figure.figure_id,
                placeholder_text=placeholder,
            )
        )
    return blocks


def _build_table_blocks(section: Section, plan: ContentPlan) -> List[TableBlock]:
    blocks: List[TableBlock] = []
    for ref in section.tables:
        table = plan.tables_index.get(ref.table_id)
        if not table:
            continue
        rows = _html_table_to_rows(ref.extract or table.html_content)
        if not rows:
            fallback_rows = [["Reference", ref.table_id], ["Focus", ref.focus or table.caption or ""]]
            rows = fallback_rows
        blocks.append(
            TableBlock(
                title=ref.table_id,
                rows=rows[:6],
                caption=ref.focus or table.caption or "",
            )
        )
    return blocks


def _build_notes(section: Section) -> List[str]:
    notes: List[str] = []
    if section.figures:
        notes.append("Referenced figures: " + ", ".join(ref.figure_id for ref in section.figures))
    if section.tables:
        notes.append("Referenced tables: " + ", ".join(ref.table_id for ref in section.tables))
    return notes


def _html_table_to_rows(table_html: str) -> List[List[str]]:
    """Best-effort parser for simple extracted HTML tables."""
    if not table_html:
        return []

    row_matches = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, flags=re.IGNORECASE | re.DOTALL)
    rows: List[List[str]] = []
    for row_html in row_matches:
        cell_matches = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.IGNORECASE | re.DOTALL)
        cells = [_clean_cell_text(cell) for cell in cell_matches]
        if cells:
            rows.append(cells)

    max_columns = max((len(row) for row in rows), default=0)
    if max_columns:
        rows = [row + [""] * (max_columns - len(row)) for row in rows]
    return rows


def _clean_cell_text(value: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
