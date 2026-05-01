"""
Content Planner
"""
import json
import logging
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any
from openai import OpenAI

from .config import GenerationInput
from ..summary import FigureInfo, TableInfo
from ..prompts.content_planning import (
    PAPER_SLIDES_PLANNING_PROMPT,
    GENERAL_SLIDES_PLANNING_PROMPT,
)


logger = logging.getLogger(__name__)


@dataclass
class TableRef:
    """Table reference for a section."""
    table_id: str           # e.g., "Table 1"
    extract: str = ""       # Optional: which part to show, html content
    focus: str = ""         # Optional: what aspect to emphasize


@dataclass
class FigureRef:
    """Figure reference for a section."""
    figure_id: str          # e.g., "Figure 1"
    focus: str = ""         # Optional: what to emphasize, description of the figure


@dataclass
class Section:
    """A single section/slide in the output."""
    id: str
    title: str
    section_type: str  
    content: str
    tables: List[TableRef] = field(default_factory=list)
    figures: List[FigureRef] = field(default_factory=list)
    section_label: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "title": self.title,
            "type": self.section_type,
            "section": self.section_label,
            "content": self.content,
        }
        
        # Tables with optional extract/focus
        result["tables"] = []
        for t in self.tables:
            t_dict = {"table_id": t.table_id}
            if t.extract:
                t_dict["extract"] = t.extract
            if t.focus:
                t_dict["focus"] = t.focus
            result["tables"].append(t_dict)
        
        # Figures with optional focus
        result["figures"] = []
        for f in self.figures:
            f_dict = {"figure_id": f.figure_id}
            if f.focus:
                f_dict["focus"] = f.focus
            result["figures"].append(f_dict)
        
        return result


@dataclass
class ContentPlan:
    """Planned content structure for generation."""
    output_type: str
    sections: List[Section] = field(default_factory=list)
    tables_index: Dict[str, TableInfo] = field(default_factory=dict)
    figures_index: Dict[str, FigureInfo] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_section_tables(self, section: Section) -> List[tuple]:
        """Get (TableInfo, extract) pairs for a section."""
        result = []
        for ref in section.tables:
            if ref.table_id in self.tables_index:
                result.append((self.tables_index[ref.table_id], ref.extract))
        return result
    
    def get_section_figures(self, section: Section) -> List[tuple]:
        """Get (FigureInfo, focus) pairs for a section."""
        result = []
        for ref in section.figures:
            if ref.figure_id in self.figures_index:
                result.append((self.figures_index[ref.figure_id], ref.focus))
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_type": self.output_type,
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata,
        }


class ContentPlanner:
    """Plans content structure using LLMs.

    Slides are planned in text-only mode: figures are exposed to the model as
    IDs, captions, and file paths so the final PPTX can reuse the extracted
    source images without invoking a vision or image-generation model.
    """
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = "gpt-5-mini",
        max_tokens: int = None,
    ):
        import os
        self.api_key = api_key or os.getenv("RAG_LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("RAG_LLM_BASE_URL")
        self.model = model
        # max_tokens: default 16000, override via RAG_LLM_MAX_TOKENS env or constructor
        # Note: deepseek has 8192 limit, set RAG_LLM_MAX_TOKENS=8192 if using deepseek
        self.max_tokens = max_tokens or int(os.getenv("RAG_LLM_MAX_TOKENS", "16000"))
        
        kwargs = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self.client = OpenAI(**kwargs)
    
    def plan(self, gen_input: GenerationInput) -> ContentPlan:
        """Create a content plan from generation input."""
        # Build tables index
        tables_index = {}
        for tbl in gen_input.origin.tables:
            tables_index[tbl.table_id] = tbl
        
        # Build figures index
        figures_index = {}
        for fig in gen_input.origin.figures:
            figures_index[fig.figure_id] = fig
        
        # Get summary and format tables/figures
        summary = gen_input.get_summary_text()
        tables_md = gen_input.origin.get_tables_markdown()
        
        figure_manifest = self._build_figure_manifest(gen_input.origin)
        sections = self._plan_slides(gen_input, summary, tables_md, figure_manifest)
        
        return ContentPlan(
            output_type=gen_input.config.output_type.value,
            sections=sections,
            tables_index=tables_index,
            figures_index=figures_index,
            metadata={
                "page_range": gen_input.config.get_page_range(),
            },
        )
    
    def _plan_slides(
        self,
        gen_input: GenerationInput,
        summary: str,
        tables_md: str,
        figure_manifest: str,
    ) -> List[Section]:
        """Plan slides sections."""
        min_pages, max_pages = gen_input.config.get_page_range()
        
        # Select prompt template based on content type
        template = PAPER_SLIDES_PLANNING_PROMPT if gen_input.is_paper() else GENERAL_SLIDES_PLANNING_PROMPT
        
        # Build assets section based on available tables/figures. This is
        # deliberately text-only for PPTX generation.
        assets_section = self._build_assets_section(tables_md, figure_manifest)
        
        prompt = template.format(
            min_pages=min_pages,
            max_pages=max_pages,
            summary=self._truncate(summary, 10000),
            assets_section=assets_section,
        )
        
        if self._force_deterministic():
            logger.warning("PPTX_FORCE_DETERMINISTIC=1; using deterministic fallback plan.")
            return self._fallback_sections_from_summary(gen_input, summary, min_pages, max_pages)

        try:
            result = self._call_text_llm(prompt)
            return self._parse_sections(result, is_slides=True)
        except Exception as exc:
            logger.warning(f"LLM planning failed; using deterministic fallback plan: {exc}")
            return self._fallback_sections_from_summary(gen_input, summary, min_pages, max_pages)
    
    def _build_assets_section(self, tables_md: str, figures: Any) -> str:
        """Build the tables/figures section based on available assets."""
        has_tables = bool(tables_md)
        has_figures = bool(figures)
        
        if not has_tables and not has_figures:
            return ""
        
        parts = ["\n## Original Tables and Figures"]
        
        if has_tables and has_figures:
            parts.append("Below are the original tables and figures. Tables contain precise data, figures illustrate concepts visually. Use them to supplement the content.")
        elif has_tables:
            parts.append("Below are the original tables containing precise data. Use them to supplement the content.")
        else:
            parts.append("Below are the original figures illustrating concepts visually. Use them to supplement the content.")
        
        if has_tables:
            parts.append(f"\n{tables_md}")
        
        if has_figures:
            if isinstance(figures, str):
                parts.append(f"\n{figures}")
            else:
                parts.append("\n[FIGURE_IMAGES]")
        
        parts.append("")  # Trailing newline
        return "\n".join(parts)

    def _build_figure_manifest(self, origin) -> str:
        """Build a text-only figure manifest for slide planning."""
        if not origin.figures:
            return ""

        parts = ["### Figures"]
        for fig in sorted(origin.figures, key=lambda x: x.line_number):
            image_path = fig.image_path
            if origin.base_path and image_path and not Path(image_path).is_absolute():
                image_path = str(Path(origin.base_path) / image_path)

            caption = (fig.caption or "").strip()
            parts.append(f"- {fig.figure_id}")
            if caption:
                parts.append(f"  Caption: {caption}")
            if image_path:
                parts.append(f"  Source image: {image_path}")

        parts.append(
            "\nUse these figure_id values exactly when a slide should include an original paper figure. "
            "Do not invent new figures or request generated images."
        )
        return "\n".join(parts)

    def _call_text_llm(self, text_prompt: str) -> str:
        """Call a text-only chat completion model."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"Calling {self.model} in text-only mode with max_tokens={self.max_tokens}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": text_prompt}],
                max_tokens=self.max_tokens,
            )
            result = response.choices[0].message.content or ""
            logger.info(f"LLM returned {len(result)} characters")
            return result
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            logger.error(f"Model: {self.model}")
            raise
    
    def _parse_sections(self, llm_response: str, is_slides: bool = True) -> List[Section]:
        """Parse LLM response into Section objects.
        
        Args:
            llm_response: The LLM response containing JSON
            is_slides: If True, auto-determine section_type based on position (opening/content/ending).
        """
        # Debug: Log the raw LLM response
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=" * 80)
        logger.info("LLM Response for Content Planning:")
        logger.info("-" * 80)
        logger.info(llm_response[:2000])  # Log first 2000 chars
        if len(llm_response) > 2000:
            logger.info(f"... (truncated, total length: {len(llm_response)} chars)")
        logger.info("=" * 80)
        
        # Extract JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            logger.info("Found JSON in code block")
        else:
            logger.warning("No JSON code block found, trying to extract raw JSON")
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            json_str = json_match.group(0) if json_match else "{}"
            if not json_match:
                logger.error("No JSON found in LLM response at all!")
        
        # Clean up invalid escape sequences before parsing
        # Replace invalid escape sequences with safe versions
        def fix_invalid_escapes(s):
            """Fix common invalid escape sequences in JSON strings."""
            # Find all escape sequences
            result = []
            i = 0
            while i < len(s):
                if s[i] == '\\' and i + 1 < len(s):
                    next_char = s[i + 1]
                    # Valid JSON escape sequences: " \ / b f n r t u
                    if next_char in ['"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u']:
                        result.append(s[i:i+2])
                        i += 2
                    else:
                        # Invalid escape sequence, escape the backslash itself
                        result.append('\\\\')
                        result.append(next_char)
                        i += 2
                else:
                    result.append(s[i])
                    i += 1
            return ''.join(result)
        
        json_str = fix_invalid_escapes(json_str)
        
        try:
            data = json.loads(json_str)
            items = data.get("slides") or data.get("sections") or []
            
            sections = []
            total = len(items)
            for idx, item in enumerate(items):
                # Parse tables
                tables = []
                for t in item.get("tables", []):
                    tables.append(TableRef(
                        table_id=t.get("table_id", ""),
                        extract=t.get("extract", ""),
                        focus=t.get("focus", ""),
                    ))
                
                # Parse figures
                figures = []
                for f in item.get("figures", []):
                    figures.append(FigureRef(
                        figure_id=f.get("figure_id", ""),
                        focus=f.get("focus", ""),
                    ))
                
                # Auto-determine section_type based on position (slides only)
                if is_slides:
                    if idx == 0:
                        section_type = "opening"
                    elif idx == total - 1:
                        section_type = "ending"
                    else:
                        section_type = "content"
                else:
                    section_type = "content"
                
                sections.append(Section(
                    id=item.get("id", f"section_{idx+1}"),
                    title=item.get("title", ""),
                    section_type=section_type,
                    content=item.get("content", ""),
                    tables=tables,
                    figures=figures,
                    section_label=item.get("section", "") or item.get("chapter", ""),
                ))
            return sections
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Failed to parse JSON string (first 500 chars): {json_str[:500]}")
            logger.warning("Using fallback sections due to JSON parse error")
            return self._fallback_sections()
        except Exception as e:
            logger.error(f"Unexpected error in _parse_sections: {e}")
            logger.warning("Using fallback sections due to unexpected error")
            return self._fallback_sections()
    
    def _fallback_sections(self) -> List[Section]:
        """Return minimal fallback sections if parsing fails."""
        return [
            Section(id="section_01", title="Title", section_type="opening", content=""),
            Section(id="section_02", title="Content", section_type="content", content=""),
        ]

    def _fallback_sections_from_summary(
        self,
        gen_input: GenerationInput,
        summary: str,
        min_pages: int,
        max_pages: int,
    ) -> List[Section]:
        """Build a usable slide plan from the existing summary when the LLM is unavailable."""
        chapters = self._split_summary_chapters(summary)
        target = self._choose_target_slides(
            summary=summary,
            min_pages=min_pages,
            max_pages=max_pages,
            figure_count=len(getattr(gen_input.origin, "figures", []) or []),
            table_count=len(getattr(gen_input.origin, "tables", []) or []),
            explicit=getattr(gen_input.config, "target_slides", None),
        )
        slide_plan = self._expand_chapters_to_slide_plan(chapters, target)
        figures = list(getattr(gen_input.origin, "figures", []) or [])
        tables = list(getattr(gen_input.origin, "tables", []) or [])

        sections: List[Section] = []
        table_cursor = 0
        for idx, item in enumerate(slide_plan):
            title = item["title"]
            content = item["content"]
            section_type = "opening" if idx == 0 else "ending" if idx == len(slide_plan) - 1 else "content"
            section_figures = []
            section_tables = []
            chapter = item["chapter"]
            if figures and chapter in {"Method", "Architecture", "Results"} and idx % 2 == 0:
                fig = figures[min(idx // 2, len(figures) - 1)]
                section_figures.append(FigureRef(figure_id=fig.figure_id, focus=fig.caption or title))
            if tables and chapter in {"Evaluation", "Results"}:
                table = tables[min(table_cursor, len(tables) - 1)]
                table_cursor += 1
                section_tables.append(TableRef(table_id=table.table_id, focus=table.caption or title))
            sections.append(
                Section(
                    id=f"section_{idx + 1:02d}",
                    title=title,
                    section_type=section_type,
                    content=content,
                    tables=section_tables,
                    figures=section_figures,
                    section_label=chapter,
                )
            )
        return sections

    def _split_summary_chapters(self, summary: str) -> List[Dict[str, Any]]:
        raw = summary or ""
        matches = list(re.finditer(r"(?m)^#\s+(.+?)\s*$", raw))
        chapters: List[Dict[str, Any]] = []
        if matches:
            for idx, match in enumerate(matches):
                start = match.end()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
                heading = match.group(1).strip()
                content = raw[start:end].strip()
                if content:
                    chapters.append({"chapter": self._normalize_chapter(heading), "heading": heading, "content": content})
        if not chapters:
            chapters.append({"chapter": "Core Ideas", "heading": "Core Ideas", "content": raw})
        return chapters

    def _normalize_chapter(self, heading: str) -> str:
        lower = heading.lower()
        if "paper" in lower or "title" in lower:
            return "Overview"
        if "motivation" in lower or "problem" in lower or "background" in lower:
            return "Motivation"
        if "solution" in lower or "method" in lower or "architecture" in lower:
            return "Method"
        if "result" in lower or "experiment" in lower or "evaluation" in lower:
            return "Results"
        if "contribution" in lower or "conclusion" in lower:
            return "Conclusion"
        return heading[:32] or "Core Ideas"

    def _choose_target_slides(
        self,
        summary: str,
        min_pages: int,
        max_pages: int,
        figure_count: int,
        table_count: int,
        explicit: int | None,
    ) -> int:
        if explicit:
            return max(4, int(explicit))
        estimated = round(len(summary or "") / 1500) + min(figure_count, 6) // 2 + min(table_count, 6) // 3
        return max(min_pages, min(max_pages, estimated))

    def _expand_chapters_to_slide_plan(self, chapters: List[Dict[str, Any]], target: int) -> List[Dict[str, str]]:
        weights = [max(1, len(chapter["content"])) for chapter in chapters]
        total_weight = sum(weights) or 1
        counts = [max(1, round(target * weight / total_weight)) for weight in weights]
        while sum(counts) < target:
            counts[weights.index(max(weights))] += 1
        while sum(counts) > target and max(counts) > 1:
            idx = counts.index(max(counts))
            counts[idx] -= 1

        slides: List[Dict[str, str]] = []
        for chapter, count in zip(chapters, counts):
            chunks = self._chunk_chapter_content(chapter["content"], count)
            for chunk_index, chunk in enumerate(chunks):
                title = self._fallback_slide_title(chapter["chapter"], chunk, chunk_index, len(chunks))
                slides.append({"chapter": chapter["chapter"], "title": title, "content": chunk})
        return slides[:target]

    def _chunk_chapter_content(self, content: str, count: int) -> List[str]:
        points = self._summary_points(content)
        if not points:
            return [content[:1200]]
        chunk_size = max(2, round(len(points) / max(1, count)))
        chunks = []
        for start in range(0, len(points), chunk_size):
            chunks.append(" ".join(points[start:start + chunk_size]))
            if len(chunks) >= count:
                break
        while len(chunks) < count:
            chunks.append(chunks[-1] if chunks else content[:1000])
        return chunks

    def _summary_points(self, content: str) -> List[str]:
        cleaned = self._clean_markdown_text(content)
        parts = re.split(r"(?:\n\s*[-*]\s+|\n\s*\d+\.\s+|(?<=[.!?])\s+(?=[A-Z0-9]))", cleaned)
        return [part.strip(" -:") for part in parts if len(part.strip(" -:")) > 35]

    def _fallback_slide_title(self, chapter: str, content: str, index: int, total: int) -> str:
        first = self._summary_points(content)
        if first:
            point = self._strip_leading_label(first[0])
            words = point.split()
            candidate = " ".join(words[:6]).strip(" ,;:-")
            if 8 <= len(candidate) <= 58:
                return candidate
        if total <= 1:
            return chapter
        return f"{chapter} {index + 1}"

    def _clean_markdown_text(self, text: str) -> str:
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text or "")
        text = re.sub(r"(?m)^#+\s*", "", text)
        text = re.sub(r"(?m)^\s*[-*]\s*", "", text)
        text = re.sub(r"\s+", " ", text)
        return self._strip_leading_label(text.strip())

    def _strip_leading_label(self, text: str) -> str:
        labels = [
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
        ]
        cleaned = text.strip(" -:")
        for label in labels:
            if cleaned.upper().startswith(label):
                cleaned = cleaned[len(label):].strip(" -:")
                break
        return cleaned
    
    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_len:
            return text
        return text[:max_len] + "\n\n[Content truncated...]"

    def _force_deterministic(self) -> bool:
        import os

        return os.getenv("PPTX_FORCE_DETERMINISTIC", "").strip().lower() in {"1", "true", "yes"}
