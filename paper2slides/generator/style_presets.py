"""Style presets for editable PPTX rendering.

The current academic renderer is the protected baseline. New presets are
visual-only variants that can reuse the same slide spec and plan checkpoints.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping


RGB = tuple[int, int, int]


@dataclass(frozen=True)
class StylePreset:
    name: str
    display_name: str
    layout_family: str
    theme: Mapping[str, object]
    reuses_academic_plan: bool = True


ACADEMIC_STYLE = "academic"


STYLE_PRESETS: Dict[str, StylePreset] = {
    "academic": StylePreset(
        name="academic",
        display_name="Academic Golden Baseline",
        layout_family="academic",
        reuses_academic_plan=False,
        theme={},
    ),
    "academic_azure": StylePreset(
        name="academic_azure",
        display_name="Formal Technical Azure",
        layout_family="academic",
        theme={
            "background": (246, 249, 252),
            "surface": (255, 255, 255),
            "surface_alt": (239, 246, 255),
            "ink": (20, 31, 50),
            "muted": (86, 99, 116),
            "rule": (197, 210, 224),
            "primary": (37, 99, 235),
            "secondary": (14, 116, 144),
            "accent": (202, 138, 4),
            "pale_primary": (219, 234, 254),
            "pale_secondary": (224, 242, 254),
            "pale_neutral": (241, 245, 249),
        },
    ),
    "academic_ink": StylePreset(
        name="academic_ink",
        display_name="Formal Technical Ink",
        layout_family="academic",
        theme={
            "background": (245, 245, 242),
            "surface": (255, 255, 251),
            "surface_alt": (239, 239, 232),
            "ink": (24, 24, 22),
            "muted": (92, 92, 86),
            "rule": (202, 199, 188),
            "primary": (31, 41, 55),
            "secondary": (99, 102, 241),
            "accent": (180, 83, 9),
            "pale_primary": (235, 235, 228),
            "pale_secondary": (232, 234, 245),
            "pale_neutral": (242, 240, 232),
        },
    ),
    "academic_warm": StylePreset(
        name="academic_warm",
        display_name="Formal Technical Warm Paper",
        layout_family="editorial",
        theme={
            "background": (250, 247, 240),
            "surface": (255, 252, 247),
            "surface_alt": (245, 238, 226),
            "ink": (39, 31, 25),
            "muted": (103, 91, 78),
            "rule": (219, 208, 190),
            "primary": (139, 92, 46),
            "secondary": (45, 91, 120),
            "accent": (169, 58, 58),
            "pale_primary": (242, 229, 210),
            "pale_secondary": (225, 238, 244),
            "pale_neutral": (246, 240, 229),
        },
    ),
    "editorial": StylePreset(
        name="editorial",
        display_name="Editorial Research Report",
        layout_family="editorial",
        theme={
            "background": (250, 247, 240),
            "surface": (255, 253, 248),
            "surface_alt": (244, 239, 229),
            "ink": (30, 30, 30),
            "muted": (103, 97, 88),
            "rule": (216, 210, 196),
            "primary": (178, 58, 72),
            "secondary": (43, 108, 176),
            "accent": (155, 98, 43),
            "pale_primary": (247, 229, 229),
            "pale_secondary": (228, 236, 246),
            "pale_neutral": (245, 240, 230),
            "title_font": "Georgia",
            "body_font": "Aptos",
        },
    ),
    "editorial_mono": StylePreset(
        name="editorial_mono",
        display_name="Editorial Monochrome",
        layout_family="editorial",
        theme={
            "background": (248, 248, 246),
            "surface": (255, 255, 252),
            "surface_alt": (236, 236, 232),
            "ink": (18, 18, 18),
            "muted": (83, 83, 78),
            "rule": (201, 201, 194),
            "primary": (20, 20, 20),
            "secondary": (89, 89, 84),
            "accent": (156, 85, 35),
            "pale_primary": (232, 232, 226),
            "pale_secondary": (240, 240, 236),
            "pale_neutral": (246, 246, 242),
            "title_font": "Georgia",
            "body_font": "Aptos",
        },
    ),
    "systems": StylePreset(
        name="systems",
        display_name="Systems Architecture",
        layout_family="systems",
        theme={
            "background": (248, 250, 252),
            "surface": (255, 255, 255),
            "surface_alt": (241, 245, 249),
            "ink": (17, 24, 39),
            "muted": (75, 85, 99),
            "rule": (210, 220, 230),
            "primary": (37, 99, 235),
            "secondary": (22, 163, 74),
            "accent": (245, 158, 11),
            "pale_primary": (219, 234, 254),
            "pale_secondary": (220, 252, 231),
            "pale_neutral": (241, 245, 249),
        },
    ),
    "systems_dark": StylePreset(
        name="systems_dark",
        display_name="Systems Dark Console",
        layout_family="systems",
        theme={
            "background": (15, 23, 42),
            "surface": (30, 41, 59),
            "surface_alt": (30, 48, 80),
            "ink": (241, 245, 249),
            "muted": (180, 190, 203),
            "rule": (71, 85, 105),
            "primary": (96, 165, 250),
            "secondary": (52, 211, 153),
            "accent": (251, 191, 36),
            "pale_primary": (30, 64, 115),
            "pale_secondary": (22, 101, 52),
            "pale_neutral": (30, 41, 59),
        },
    ),
    "data_report": StylePreset(
        name="data_report",
        display_name="Data Report Scorecard",
        layout_family="report",
        theme={
            "background": (251, 250, 247),
            "surface": (255, 255, 255),
            "surface_alt": (243, 244, 246),
            "ink": (31, 41, 55),
            "muted": (91, 100, 112),
            "rule": (209, 213, 219),
            "primary": (15, 118, 110),
            "secondary": (217, 119, 6),
            "accent": (220, 38, 38),
            "pale_primary": (204, 251, 241),
            "pale_secondary": (254, 243, 199),
            "pale_neutral": (243, 244, 246),
        },
    ),
    "conference": StylePreset(
        name="conference",
        display_name="Conference Oral",
        layout_family="conference",
        theme={
            "background": (255, 255, 255),
            "surface": (255, 255, 255),
            "surface_alt": (239, 246, 255),
            "ink": (17, 24, 39),
            "muted": (75, 85, 99),
            "rule": (203, 213, 225),
            "primary": (29, 78, 216),
            "secondary": (8, 145, 178),
            "accent": (234, 88, 12),
            "pale_primary": (219, 234, 254),
            "pale_secondary": (207, 250, 254),
            "pale_neutral": (248, 250, 252),
        },
    ),
    "visual_explainer": StylePreset(
        name="visual_explainer",
        display_name="Visual Explainer",
        layout_family="explainer",
        theme={
            "background": (247, 249, 251),
            "surface": (255, 255, 255),
            "surface_alt": (241, 245, 249),
            "ink": (15, 23, 42),
            "muted": (82, 92, 108),
            "rule": (203, 213, 225),
            "primary": (59, 130, 246),
            "secondary": (16, 185, 129),
            "accent": (249, 115, 22),
            "pale_primary": (219, 234, 254),
            "pale_secondary": (209, 250, 229),
            "pale_neutral": (241, 245, 249),
        },
    ),
}


PREDEFINED_STYLE_NAMES = frozenset(STYLE_PRESETS.keys())
VISUAL_STYLE_NAMES = frozenset(name for name in STYLE_PRESETS if name != ACADEMIC_STYLE)


def get_style_preset(style: str | None) -> StylePreset:
    key = (style or ACADEMIC_STYLE).strip().lower()
    return STYLE_PRESETS.get(key, STYLE_PRESETS[ACADEMIC_STYLE])


def is_visual_style(style: str | None) -> bool:
    return (style or "").strip().lower() in VISUAL_STYLE_NAMES
