"""
Lightweight PPTX layout QA for generated native decks.

This is not a full PowerPoint renderer, but it catches common defects before
delivery: out-of-bounds shapes, very long title text, empty slides, and likely
text overflow based on box size and word count.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class PptxQaResult:
    passed: bool
    warnings: List[str]
    slide_count: int

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "warnings": self.warnings,
            "slide_count": self.slide_count,
        }


def inspect_pptx_layout(pptx_path: Path) -> PptxQaResult:
    try:
        from pptx import Presentation
    except ImportError as exc:
        raise RuntimeError("python-pptx is required for PPTX QA.") from exc

    prs = Presentation(str(pptx_path))
    warnings: List[str] = []
    slide_width = int(prs.slide_width)
    slide_height = int(prs.slide_height)

    for slide_index, slide in enumerate(prs.slides, start=1):
        visible_text_shapes = 0
        visible_pictures = 0
        visible_tables = 0

        for shape in slide.shapes:
            left = int(shape.left)
            top = int(shape.top)
            right = left + int(shape.width)
            bottom = top + int(shape.height)

            if right < 0 or bottom < 0 or left > slide_width or top > slide_height:
                warnings.append(f"slide {slide_index}: shape is fully outside slide bounds")
                continue

            if left < -1000 or top < -1000 or right > slide_width + 1000 or bottom > slide_height + 1000:
                warnings.append(f"slide {slide_index}: shape partly exceeds slide bounds")

            text = ""
            if getattr(shape, "has_text_frame", False):
                text = (shape.text or "").strip()
                if text:
                    visible_text_shapes += 1
                    _check_text_box(slide_index, shape, text, warnings)

            if getattr(shape, "has_table", False):
                visible_tables += 1
            if shape.shape_type == 13:
                visible_pictures += 1

        if visible_text_shapes == 0 and visible_pictures == 0 and visible_tables == 0:
            warnings.append(f"slide {slide_index}: slide appears empty")

    severe = [w for w in warnings if "outside" in w or "exceeds" in w or "empty" in w]
    return PptxQaResult(passed=not severe, warnings=warnings, slide_count=len(prs.slides))


def _check_text_box(slide_index: int, shape, text: str, warnings: List[str]) -> None:
    width_inches = int(shape.width) / 914400
    height_inches = int(shape.height) / 914400
    words = len(text.split())
    lines = [line for line in text.splitlines() if line.strip()]

    if width_inches > 8 and height_inches < 0.35 and len(text) > 90:
        warnings.append(f"slide {slide_index}: long title/subtitle may wrap or clip")

    if height_inches < 0.25 and len(text) > 32:
        warnings.append(f"slide {slide_index}: very small text box contains long text")

    if height_inches < 0.75 and words > 22:
        warnings.append(f"slide {slide_index}: text box may overflow vertically")

    if len(lines) >= 5 and height_inches < 2.0:
        warnings.append(f"slide {slide_index}: dense bullet list may overflow")
