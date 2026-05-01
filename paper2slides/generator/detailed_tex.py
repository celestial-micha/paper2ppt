"""
Detailed Beamer/TeX deck generation.

This module is a sidecar output path inspired by Paper2PPT's Beamer workflow:
it keeps the main editable PPTX untouched, but also emits a more content-rich
LaTeX presentation that can be edited or compiled separately.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .content_planner import ContentPlan, Section
from .slide_schema import PresentationSpec, SlideSpec


class _TableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: List[List[str]] = []
        self._row: List[str] = []
        self._cell: List[str] = []
        self._in_cell = False
        self._in_row = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
            self._in_row = True
        elif tag in {"td", "th"} and self._in_row:
            self._cell = []
            self._in_cell = True

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._in_cell:
            text = " ".join("".join(self._cell).split())
            self._row.append(text)
            self._cell = []
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if any(cell.strip() for cell in self._row):
                self.rows.append(self._row)
            self._row = []
            self._in_row = False


def generate_detailed_tex_deck(
    plan: ContentPlan,
    spec: PresentationSpec,
    output_dir: Path,
    title: str | None = None,
    compile_pdf: bool | None = None,
) -> Dict[str, str]:
    """Generate a detailed Beamer deck and optionally compile it to PDF."""
    if os.getenv("PPTX_ENABLE_DETAILED_TEX", "1").strip().lower() in {"0", "false", "no"}:
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = output_dir / "detailed_slides.tex"
    deck_title = title or spec.title or "Detailed Paper Presentation"
    tex_path.write_text(_build_tex_document(plan, spec, deck_title), encoding="utf-8")

    result: Dict[str, str] = {"detailed_tex_path": str(tex_path)}
    should_compile = (
        os.getenv("PPTX_COMPILE_DETAILED_TEX", "1").strip().lower() not in {"0", "false", "no"}
        if compile_pdf is None
        else compile_pdf
    )
    if should_compile and shutil.which("pdflatex"):
        pdf_path = _compile_tex(tex_path)
        if pdf_path:
            result["detailed_pdf_path"] = str(pdf_path)
    return result


def _build_tex_document(plan: ContentPlan, spec: PresentationSpec, title: str) -> str:
    slides = _build_frames(plan, spec)
    body = "\n\n".join(slides)
    return rf"""\documentclass[11pt,aspectratio=169]{{beamer}}

\usepackage[utf8]{{inputenc}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}
\usepackage{{adjustbox}}
\usepackage{{graphicx}}
\usepackage{{amsmath,amssymb}}
\usepackage{{hyperref}}

\usetheme{{Boadilla}}
\usecolortheme{{seahorse}}
\setbeamertemplate{{navigation symbols}}{{}}
\setbeamertemplate{{itemize/enumerate body begin}}{{\small}}
\setbeamertemplate{{itemize/enumerate subbody begin}}{{\footnotesize}}
\setlength{{\itemsep}}{{0.2em}}

\definecolor{{paperblue}}{{RGB}}{{18,65,112}}
\definecolor{{papergreen}}{{RGB}}{{22,113,92}}
\setbeamercolor{{structure}}{{fg=paperblue}}
\setbeamercolor{{frametitle}}{{fg=paperblue,bg=white}}
\setbeamercolor{{block title}}{{fg=white,bg=paperblue}}
\setbeamercolor{{block body}}{{fg=black,bg=paperblue!6}}
\setbeamercolor{{alertblock title}}{{fg=white,bg=papergreen}}
\setbeamercolor{{alertblock body}}{{fg=black,bg=papergreen!7}}

\title{{{_tex_escape(title)}}}
\subtitle{{Detailed TeX sidecar generated alongside editable PPTX}}
\author{{PaperCue / paper2ppt}}
\date{{\today}}

\begin{{document}}

\begin{{frame}}
  \titlepage
\end{{frame}}

\begin{{frame}}{{Roadmap}}
  \tableofcontents
\end{{frame}}

{body}

\begin{{frame}}{{Takeaways}}
  \begin{{alertblock}}{{Closing message}}
  This detailed deck is meant as an editable Beamer companion. Use it when the talk needs more derivation, evidence, or context than the compact PPTX.
  \end{{alertblock}}
\end{{frame}}

\end{{document}}
"""


def _build_frames(plan: ContentPlan, spec: PresentationSpec) -> List[str]:
    frames: List[str] = []
    slides_by_index = {idx: slide for idx, slide in enumerate(spec.slides)}
    last_section = ""

    for idx, section in enumerate(plan.sections):
        section_name = _section_name(section, idx, len(plan.sections))
        if section_name != last_section:
            frames.append(rf"\section{{{_tex_escape(section_name)}}}")
            last_section = section_name

        slide = slides_by_index.get(idx)
        frames.append(_section_frame(plan, section, slide, idx + 1))

    if not frames and spec.slides:
        for idx, slide in enumerate(spec.slides):
            frames.append(_spec_only_frame(slide, idx + 1))
    return frames


def _section_frame(plan: ContentPlan, section: Section, slide: SlideSpec | None, index: int) -> str:
    title = _short_title(section.title or (slide.title if slide else f"Slide {index}"))
    takeaway = (slide.takeaway if slide else "") or _first_sentence(section.content)
    bullets = _merge_points(
        [block.text for block in (slide.text_blocks if slide else [])],
        _split_points(section.content),
        max_items=6,
    )
    figures = [plan.figures_index.get(ref.figure_id) for ref in section.figures]
    figures = [fig for fig in figures if fig]
    tables = [plan.tables_index.get(ref.table_id) for ref in section.tables]
    tables = [table for table in tables if table]

    if figures:
        content = _visual_frame_content(takeaway, bullets, figures[0])
    elif tables:
        content = _table_frame_content(takeaway, bullets, tables[0])
    else:
        content = _text_frame_content(takeaway, bullets)

    return rf"""\begin{{frame}}[t]{{{_tex_escape(title)}}}
{content}
\end{{frame}}"""


def _spec_only_frame(slide: SlideSpec, index: int) -> str:
    title = _short_title(slide.title or f"Slide {index}")
    bullets = [block.text for block in slide.text_blocks[:6]]
    return rf"""\begin{{frame}}[t]{{{_tex_escape(title)}}}
{_text_frame_content(slide.takeaway, bullets)}
\end{{frame}}"""


def _visual_frame_content(takeaway: str, bullets: Sequence[str], figure: Any) -> str:
    image_path = _image_path(getattr(figure, "image_path", ""))
    caption = getattr(figure, "caption", "") or getattr(figure, "figure_id", "")
    visual = (
        rf"\includegraphics[width=\linewidth,height=0.48\textheight,keepaspectratio]{{\detokenize{{{image_path}}}}}"
        if image_path
        else rf"\begin{{alertblock}}{{Visual reference}}{_tex_escape(caption)}\end{{alertblock}}"
    )
    return rf"""  \begin{{columns}}[T,onlytextwidth]
    \begin{{column}}{{0.54\textwidth}}
{_takeaway_block(takeaway)}
{_itemize(bullets, max_items=6)}
    \end{{column}}
    \begin{{column}}{{0.42\textwidth}}
      \centering
      {visual}

      \vspace{{0.3em}}
      {{\scriptsize {_tex_escape(caption)[:360]}}}
    \end{{column}}
  \end{{columns}}"""


def _table_frame_content(takeaway: str, bullets: Sequence[str], table: Any) -> str:
    rows = _table_rows(getattr(table, "html_content", ""))[:6]
    table_tex = _render_table(rows) if rows else ""
    caption = getattr(table, "caption", "")
    return rf"""{_takeaway_block(takeaway)}
{_itemize(bullets[:4], max_items=4)}
\vspace{{0.3em}}
{table_tex}
{{\scriptsize {_tex_escape(caption)[:420]}}}"""


def _text_frame_content(takeaway: str, bullets: Sequence[str]) -> str:
    return rf"""{_takeaway_block(takeaway)}
{_itemize(bullets, max_items=6)}"""


def _takeaway_block(text: str) -> str:
    text = _clean_text(text)
    if not text:
        return ""
    return rf"""  \begin{{alertblock}}{{Key message}}
  {_tex_escape(text[:520])}
  \end{{alertblock}}"""


def _itemize(items: Sequence[str], max_items: int) -> str:
    clean_items = [_clean_text(item) for item in items if _clean_text(item)]
    clean_items = clean_items[:max_items]
    if not clean_items:
        return ""
    body = "\n".join(f"    \\item {_tex_escape(item[:260])}" for item in clean_items)
    return "\\begin{itemize}\n" + body + "\n  \\end{itemize}"


def _render_table(rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return ""
    columns = min(max(len(row) for row in rows), 4)
    normalized = [(list(row) + [""] * columns)[:columns] for row in rows[:6]]
    align = "l" + "X" * max(0, columns - 1)
    lines = [
        r"\begin{adjustbox}{max width=\textwidth,max totalheight=0.28\textheight}",
        rf"\begin{{tabularx}}{{\textwidth}}{{{align}}}",
        r"\toprule",
    ]
    for idx, row in enumerate(normalized):
        lines.append(" & ".join(_tex_escape(cell[:80]) for cell in row) + r" \\")
        lines.append(r"\midrule" if idx == 0 else "")
    lines.extend([r"\bottomrule", r"\end{tabularx}", r"\end{adjustbox}"])
    return "\n".join(line for line in lines if line)


def _table_rows(html: str) -> List[List[str]]:
    parser = _TableHTMLParser()
    parser.feed(html or "")
    return parser.rows


def _compile_tex(tex_path: Path) -> Path | None:
    log_path = tex_path.with_name("detailed_slides_pdflatex.log")
    pdf_path = tex_path.with_suffix(".pdf")
    command = ["pdflatex", "-interaction=nonstopmode", tex_path.name]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        for _ in range(2):
            result = subprocess.run(
                command,
                cwd=str(tex_path.parent),
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
    return pdf_path if pdf_path.exists() else None


def _section_name(section: Section, index: int, total: int) -> str:
    title = (section.title or "").lower()
    if index == 0 or section.section_type == "opening":
        return "Motivation"
    if index == total - 1 or section.section_type == "ending":
        return "Conclusion"
    if any(word in title for word in ["method", "approach", "model", "algorithm", "architecture"]):
        return "Method"
    if any(word in title for word in ["experiment", "result", "evaluation", "analysis"]):
        return "Results"
    if any(word in title for word in ["background", "preliminar", "problem", "definition"]):
        return "Background"
    return "Core Ideas"


def _split_points(text: str) -> List[str]:
    text = _clean_text(text)
    if not text:
        return []
    parts = re.split(r"(?:\n+|;\s+|(?<=[.!?])\s+(?=[A-Z0-9]))", text)
    return [part.strip(" -:") for part in parts if len(part.strip(" -:")) > 12]


def _merge_points(primary: Sequence[str], secondary: Sequence[str], max_items: int) -> List[str]:
    points: List[str] = []
    seen = set()
    for item in list(primary) + list(secondary):
        clean = _clean_text(item)
        key = clean.lower()
        if not clean or key in seen:
            continue
        points.append(clean)
        seen.add(key)
        if len(points) >= max_items:
            break
    return points


def _first_sentence(text: str) -> str:
    points = _split_points(text)
    return points[0] if points else _clean_text(text)


def _short_title(text: str) -> str:
    text = _clean_text(text)
    return text[:78].rstrip(" ,;:-") or "Detailed slide"


def _clean_text(text: str) -> str:
    replacements = {
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "→": "->",
        "←": "<-",
        "≤": "<=",
        "≥": ">=",
        "≈": "~",
        "±": "+/-",
        "×": "x",
        "·": ".",
        "′": "'",
        "″": '"',
        "√": "sqrt",
        "∑": "sum",
        "∏": "prod",
        "∈": "in",
        "∉": "not in",
        "∞": "infinity",
        "α": "alpha",
        "β": "beta",
        "γ": "gamma",
        "δ": "delta",
        "ε": "epsilon",
        "θ": "theta",
        "λ": "lambda",
        "μ": "mu",
        "π": "pi",
        "ρ": "rho",
        "σ": "sigma",
        "τ": "tau",
        "φ": "phi",
        "ω": "omega",
        "Γ": "Gamma",
        "Δ": "Delta",
        "Θ": "Theta",
        "Λ": "Lambda",
        "Π": "Pi",
        "Σ": "Sigma",
        "Φ": "Phi",
        "Ω": "Omega",
    }
    cleaned = str(text or "")
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    cleaned = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", cleaned).strip()


def _tex_escape(text: str) -> str:
    text = _clean_text(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _image_path(path: str) -> str:
    if not path:
        return ""
    resolved = Path(path)
    if not resolved.exists():
        return ""
    return resolved.resolve().as_posix()
