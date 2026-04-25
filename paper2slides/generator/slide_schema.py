"""
Structured slide specification models for editable PPTX output.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TextBlock:
    """Editable text content rendered into a text box."""
    text: str
    role: str = "body"
    bullet_level: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "role": self.role,
            "bullet_level": self.bullet_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextBlock":
        return cls(
            text=data.get("text", ""),
            role=data.get("role", "body"),
            bullet_level=data.get("bullet_level", 0),
        )


@dataclass
class ImageBlock:
    """Editable image reference for a slide."""
    path: str
    caption: str = ""
    title: str = ""
    placeholder_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "caption": self.caption,
            "title": self.title,
            "placeholder_text": self.placeholder_text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageBlock":
        return cls(
            path=data.get("path", ""),
            caption=data.get("caption", ""),
            title=data.get("title", ""),
            placeholder_text=data.get("placeholder_text", ""),
        )


@dataclass
class TableBlock:
    """Simplified table representation for deterministic PPTX rendering."""
    title: str
    rows: List[List[str]] = field(default_factory=list)
    caption: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "rows": self.rows,
            "caption": self.caption,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TableBlock":
        return cls(
            title=data.get("title", ""),
            rows=data.get("rows", []),
            caption=data.get("caption", ""),
        )


@dataclass
class MetricBlock:
    """A compact metric/callout rendered as editable text and shape."""
    label: str
    value: str
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "value": self.value,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricBlock":
        return cls(
            label=data.get("label", ""),
            value=data.get("value", ""),
            note=data.get("note", ""),
        )


@dataclass
class SlideSpec:
    """Structured representation of a single editable slide."""
    slide_id: str
    title: str
    layout: str = "auto"
    takeaway: str = ""
    text_blocks: List[TextBlock] = field(default_factory=list)
    image_blocks: List[ImageBlock] = field(default_factory=list)
    table_blocks: List[TableBlock] = field(default_factory=list)
    metric_blocks: List[MetricBlock] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    section_type: str = "content"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_id": self.slide_id,
            "title": self.title,
            "layout": self.layout,
            "takeaway": self.takeaway,
            "section_type": self.section_type,
            "text_blocks": [block.to_dict() for block in self.text_blocks],
            "image_blocks": [block.to_dict() for block in self.image_blocks],
            "table_blocks": [block.to_dict() for block in self.table_blocks],
            "metric_blocks": [block.to_dict() for block in self.metric_blocks],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SlideSpec":
        return cls(
            slide_id=data.get("slide_id", ""),
            title=data.get("title", ""),
            layout=data.get("layout", "auto"),
            takeaway=data.get("takeaway", ""),
            section_type=data.get("section_type", "content"),
            text_blocks=[TextBlock.from_dict(item) for item in data.get("text_blocks", [])],
            image_blocks=[ImageBlock.from_dict(item) for item in data.get("image_blocks", [])],
            table_blocks=[TableBlock.from_dict(item) for item in data.get("table_blocks", [])],
            metric_blocks=[MetricBlock.from_dict(item) for item in data.get("metric_blocks", [])],
            notes=data.get("notes", []),
        )


@dataclass
class PresentationSpec:
    """Structured editable presentation definition."""
    title: str
    slides: List[SlideSpec] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_plan_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slides": [slide.to_dict() for slide in self.slides],
            "metadata": self.metadata,
            "source_plan_path": self.source_plan_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PresentationSpec":
        return cls(
            title=data.get("title", "Presentation"),
            slides=[SlideSpec.from_dict(item) for item in data.get("slides", [])],
            metadata=data.get("metadata", {}),
            source_plan_path=data.get("source_plan_path"),
        )
