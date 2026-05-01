import os
import subprocess
import difflib
import re
from typing import List
from jinja2 import Environment, FileSystemLoader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from .planner import Slide, PresentationPlan
from ..utils.llm_factory import get_llm

load_dotenv()

def escape_latex(text: str) -> str:
    """Escapes LaTeX special characters."""
    if not text:
        return ""
    chars = {
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    return "".join(chars.get(c, c) for c in text)

class Generator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.llm = get_llm(temperature=0.3)
        
        # Jinja2 Setup for LaTeX
        self.env = Environment(
            loader=FileSystemLoader("templates"),
            block_start_string='\\BLOCK{',
            block_end_string='}',
            variable_start_string='\\VAR{',
            variable_end_string='}',
            comment_start_string='\\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
        )

    def generate_slide_content(self, slide: Slide, full_text: str, available_images: List[str]) -> str:
        print(f"[Generator] Writing content for slide: {slide.title}")
        
        layout_instructions = {
            "standard": """
            **Layout: Standard**
            - Use `itemize` for bullet points.
            - **STRICT LIMIT**: Maximum **5** items total.
            - **STRICT LIMIT**: Maximum **2** lines per bullet.
            - Use `block` for key concepts.
            - NO `columns` environment.
            - **NO IMAGES**: Do NOT use `\\includegraphics` in this layout.
            """,
            "two_column": """
            **Layout: Two Column**
            - You MUST use the following structure:
              \\begin{{columns}}[T,onlytextwidth]
                  \\begin{{column}}{{0.48\\textwidth}}
                      % Left content here
                      % **STRICT LIMIT**: Max 3 bullets or 1 block.
                  \\end{{column}}
                  \\begin{{column}}{{0.48\\textwidth}}
                      % Right content here
                      % **STRICT LIMIT**: Max 3 bullets or 1 block.
                  \\end{{column}}
              \\end{{columns}}
            - **NO IMAGES**: Do NOT use `\\includegraphics` in this layout.
            """,
            "three_column": """
            **Layout: Three Column**
            - You MUST use the following structure:
              \\begin{{footnotesize}}
              \\begin{{columns}}[T,onlytextwidth]
                  \\begin{{column}}{{0.32\\textwidth}}
                      % Col 1
                      % **STRICT LIMIT**: Max 3 short bullets.
                  \\end{{column}}
                  \\begin{{column}}{{0.32\\textwidth}}
                      % Col 2
                      % **STRICT LIMIT**: Max 3 short bullets.
                  \\end{{column}}
                  \\begin{{column}}{{0.32\\textwidth}}
                      % Col 3
                      % **STRICT LIMIT**: Max 3 short bullets.
                  \\end{{column}}
              \\end{{columns}}
              \\end{{footnotesize}}
            - **NO IMAGES**: Do NOT use `\\includegraphics` in this layout.
            """,
            "image_right": """
            **Layout: Image Right**
            - You MUST use the following structure:
              \\begin{{columns}}[c,onlytextwidth]
                  \\begin{{column}}{{0.6\\textwidth}}
                      % Text content here
                      % **STRICT LIMIT**: Max 4 bullets.
                  \\end{{column}}
                  \\begin{{column}}{{0.38\\textwidth}}
                      \\centering
                      % Insert Image Here
                      % Use height constraint to prevent overflow
                      % Example: \\includegraphics[width=\\linewidth, height=0.8\\textheight, keepaspectratio]{{filename}}
                  \\end{{column}}
              \\end{{columns}}
            """,
            "image_left": """
            **Layout: Image Left**
            - You MUST use the following structure:
              \\begin{{columns}}[c,onlytextwidth]
                  \\begin{{column}}{{0.38\\textwidth}}
                      \\centering
                      % Insert Image Here
                      % Use height constraint to prevent overflow
                      % Example: \\includegraphics[width=\\linewidth, height=0.8\\textheight, keepaspectratio]{{filename}}
                  \\end{{column}}
                  \\begin{{column}}{{0.6\\textwidth}}
                      % Text content here
                      % **STRICT LIMIT**: Max 4 bullets.
                  \\end{{column}}
              \\end{{columns}}
            """,
            "full_page_image": """
            **Layout: Full Page Image**
            - Center the content.
            - Use `\\begin{{figure}}` or just `\\centering`.
            - Insert the image with: `\\includegraphics[width=\\textwidth, height=0.85\\textheight, keepaspectratio]{{filename}}`
            - Add a minimal caption or description below if needed (max 1 line).
            """,
            "vertical_split": """
            **Layout: Vertical Split**
            - Top half image, bottom half text (or vice versa).
            - Structure:
              \\centering
              \\includegraphics[width=0.8\\textwidth, height=0.45\\textheight, keepaspectratio]{{filename}}
              \\vspace{{1em}}
              \\begin{{minipage}}{{0.9\\textwidth}}
                  % Text content here (Max 3 bullets)
              \\end{{minipage}}
            """,
            "highlight_box": """
            **Layout: Highlight Box**
            - Center the content.
            - Use `\\begin{{alertblock}}{{Title}} ... \\end{{alertblock}}` for the main message.
            - **STRICT LIMIT**: Keep text minimal (max 40 words).
            - **NO IMAGES**: Do NOT use `\\includegraphics` in this layout.
            """,
            "two_column_header": """
            **Layout: Two Column with Header**
            - You MUST use the following structure:
              % Top full-width content
              \\begin{{block}}{{Overview}}
                  % Brief intro (max 2 lines)
              \\end{{block}}
              \\begin{{columns}}[T,onlytextwidth]
                  \\begin{{column}}{{0.48\\textwidth}}
                      % Left content (max 3 bullets)
                  \\end{{column}}
                  \\begin{{column}}{{0.48\\textwidth}}
                      % Right content (max 3 bullets)
                  \\end{{column}}
              \\end{{columns}}
            - **NO IMAGES**: Do NOT use `\\includegraphics` in this layout.
            """,
            "comparison_table": """
            **Layout: Comparison Table**
            - Center the content.
            - Create a standard LaTeX table using `booktabs`.
            - Example:
              \\begin{{table}}
              \\centering
              \\begin{{tabular}}{{l c c}}
                  \\toprule
                  Model & Accuracy & Speed \\\\
                  \\midrule
                  Baseline & 85\\% & 10ms \\\\
                  Ours & 92\\% & 12ms \\\\
                  \\bottomrule
              \\end{{tabular}}
              \\end{{table}}
            - **STRICT LIMIT**: Max 5 rows, Max 4 columns.
            - **NO IMAGES**: Do NOT use `\\includegraphics` in this layout.
            """
        }

        specific_instruction = layout_instructions.get(slide.suggested_layout, layout_instructions["standard"])

        system_prompt = f"""You are a LaTeX Beamer expert. Generate the body content for a slide.
        
        **STRICT CONTENT VOLUME CONTROL (CRITICAL)**:
        *   **Prevent Overflow**: The most common error is too much text.
        *   **Bullet Limit**: Never exceed the bullet limit specified in the layout.
        *   **Word Limit**: Keep bullet points SHORT (max 10-15 words).
        *   **No Nested Lists**: Do NOT use nested `itemize` or `enumerate` unless absolutely necessary and kept very short.
        *   **Vertical Space**: If you use a `block`, reduce the number of bullet points outside it.
        
        **Formatting Rules**:
        *   Use `itemize` for bullet points.
        *   **CRITICAL**: Do NOT use `[itemsep=...]` or `[topsep=...]` with `itemize` or `enumerate`. Beamer does not support this syntax.
        *   Use `block`, `alertblock`, or `exampleblock` for Definitions, Theorems, and Key Ideas.
        *   **Style Enforcement**: Use `\\textbf{{{{}}}}` for emphasis, but do not overuse.
        *   **Math**: Use standard LaTeX math environments (`equation`, `align`).
        *   **Escaping**: You MUST escape special LaTeX characters in normal text: `&` -> `\\&`, `%` -> `\\%`, `$` -> `\\$`, `#` -> `\\#`, `_` -> `\\_`.
            *   Example: "Carson & Higham" -> "Carson \\& Higham"
        
        {specific_instruction}

        When explaining a concept, prefer using a `block` environment with a title.
        Example:
        \\begin{{{{block}}}}{{{{Key Insight}}}}
        Self-attention allows the model to attend to different parts of the input sequence regardless of distance.
        \\end{{{{block}}}}
        
        **Image Handling**:
        You have access to the following images in the 'supplement' directory: {{available_images_list}}.
        *   **CRITICAL RULE**: You may ONLY use `\\includegraphics` if the layout is `image_left`, `image_right`, `full_page_image`, or `vertical_split`.
        *   **FORBIDDEN**: Do NOT insert images in `standard`, `two_column`, `three_column`, `highlight_box`, `two_column_header`, or `comparison_table` layouts.
        *   If the layout allows images and the content matches one of the available images (fuzzy match), use:
            `\\includegraphics[width=\\linewidth, height=0.8\\textheight, keepaspectratio]{{{{supplement/FILENAME}}}}` (The layout wrapper will handle sizing).
        *   If NO matching image exists, do NOT invent a filename. Instead, use a placeholder block:
            `\\begin{{{{alertblock}}}}{{{{Visual Placeholder}}}} Description of the missing figure (e.g., "Figure 1: Model Architecture"). \\end{{{{alertblock}}}}`
        """

        human_prompt = """
        Slide Title: {title}
        Section: {section}
        Goal: {content_goal}
        Layout: {layout}
        Key Visuals: {key_visuals}
        
        Relevant Paper Content (Use this to write the slide):
        {paper_text}
        
        Output ONLY the LaTeX body code for this slide. Do not include \\begin{{frame}} or \\end{{frame}}.
        Do NOT wrap the output in markdown code blocks (like ```latex ... ```). Return ONLY the raw LaTeX code.
        
        **CRITICAL**: Ensure EVERY `\\begin{{block}}`, `\\begin{{alertblock}}`, `\\begin{{exampleblock}}`, `\\begin{{itemize}}`, `\\begin{{enumerate}}`, `\\begin{{columns}}` has a corresponding `\\end{{...}}`. Double check your closing tags.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])

        # Truncate text again just in case
        truncated_text = full_text[:20000] 

        chain = prompt | self.llm
        
        response = chain.invoke({
            "title": slide.title,
            "section": slide.section,
            "content_goal": slide.content_goal,
            "layout": slide.suggested_layout,
            "key_visuals": slide.key_visuals,
            "paper_text": truncated_text,
            "available_images_list": ", ".join(available_images) if available_images else "None"
        })
        
        content = response.content

        # Post-processing: Remove Markdown code blocks if present
        content = re.sub(r'^```latex\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'```$', '', content, flags=re.MULTILINE)

        # # Post-processing: Escape special characters in block titles
        # def escape_block_title(match):
        #     env_type = match.group(1)
        #     title = match.group(2)
        #     # Escape & and % in title
        #     title = title.replace("&", "\\&").replace("%", "\\%")
        #     return f"\\begin{{{env_type}}}{{{title}}}"

        # content = re.sub(r'\\begin\{(block|alertblock|exampleblock)\}\{(.*?)\}', escape_block_title, content)

        return content

    def generate_presentation(self, plan: PresentationPlan, full_text: str, title: str, authors: str):
        # Get available images
        supplement_dir = os.path.join(self.output_dir, "supplement")
        available_images = []
        if os.path.exists(supplement_dir):
            available_images = [f for f in os.listdir(supplement_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]

        slides_content = []
        last_section = None
        for slide in plan.slides:
            content = self.generate_slide_content(slide, full_text, available_images)
            
            # Fix Image Filenames (Fuzzy Match)
            # Find all \includegraphics{...} and check if file exists
            def replace_image_path(match):
                full_match = match.group(0)
                image_path = match.group(1)
                # Extract filename from path (handle supplement/ prefix)
                filename = os.path.basename(image_path)
                
                # If exact match exists, return as is
                if filename in available_images:
                    return full_match
                
                # Try fuzzy match
                matches = difflib.get_close_matches(filename, available_images, n=1, cutoff=0.6)
                if matches:
                    print(f"[Generator] Fixed typo: {filename} -> {matches[0]}")
                    return full_match.replace(image_path, f"supplement/{matches[0]}")
                
                print(f"[Generator] Warning: Image {filename} not found and no close match.")
                return full_match

            # Regex to find \includegraphics[...]{path} or \includegraphics{path}
            # We assume standard LaTeX syntax generated by LLM
            content = re.sub(r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}', replace_image_path, content)

            # Only add section if it's different from the previous one
            current_section = escape_latex(slide.section)
            section_to_render = current_section if current_section != last_section else None
            last_section = current_section

            slides_content.append({
                "section": section_to_render,
                "title": escape_latex(slide.title),
                "content": content
            })

        # Render Template
        template = self.env.get_template("beta_beamer.tex.j2")
        tex_output = template.render(
            title=escape_latex(title),
            short_title=escape_latex(title)[:20] + "...",
            subtitle="Generated by Paper2PPT (github.com/gejifeng/Paper2PPT)",
            authors=escape_latex(authors),
            slides=slides_content
        )

        output_tex_path = os.path.join(self.output_dir, "presentation.tex")
        with open(output_tex_path, "w") as f:
            f.write(tex_output)
        
        print(f"[Generator] LaTeX written to {output_tex_path}")
        self.compile_pdf(output_tex_path)

    def compile_pdf(self, tex_path: str):
        print("[Generator] Compiling PDF...")
        # Run pdflatex twice for TOC and references
        # We need to run it in the output directory so it finds the 'supplement' folder
        cwd = os.path.dirname(tex_path)
        tex_filename = os.path.basename(tex_path)
        
        try:
            # First run
            subprocess.run(['pdflatex', '-interaction=nonstopmode', tex_filename], cwd=cwd, check=False, stdout=subprocess.DEVNULL)
            # Second run
            result = subprocess.run(['pdflatex', '-interaction=nonstopmode', tex_filename], cwd=cwd, check=False, stdout=subprocess.DEVNULL)
            
            if result.returncode == 0:
                print(f"[Generator] PDF compiled successfully: {tex_path.replace('.tex', '.pdf')}")
            else:
                print(f"[Generator] PDF compilation finished with exit code {result.returncode}. PDF might be generated but with errors (e.g. missing images).")
                print(f"[Generator] Check log in {cwd}/presentation.log")
                
        except Exception as e:
            print(f"[Generator] PDF compilation failed with exception: {e}")

