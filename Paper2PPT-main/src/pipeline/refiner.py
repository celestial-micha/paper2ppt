import os
import re
from typing import List, Tuple, Dict
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from ..utils.llm_factory import get_llm
from .log_parser import LogParser

load_dotenv()

class Refiner:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.llm = get_llm(temperature=0.1)
        # Load max output tokens from env, default to 4000
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "4000"))

    def get_overflow_pages(self, log_path: str) -> List[int]:
        """Uses LogParser to find pages with overflow."""
        parser = LogParser.from_file(log_path)
        return parser.parse_overflows(threshold=10.0)

    def split_tex_content(self, content: str) -> Tuple[str, List[str], str]:
        """
        Splits TeX content into Preamble, List of Frames, and Postamble.
        Returns: (preamble, frames, postamble)
        """
        # Find \begin{document}
        doc_start_match = re.search(r'\\begin\{document\}', content)
        if not doc_start_match:
            return "", [content], ""
        
        preamble = content[:doc_start_match.end()]
        body_and_post = content[doc_start_match.end():]
        
        # Find \end{document}
        doc_end_match = re.search(r'\\end\{document\}', body_and_post)
        if doc_end_match:
            body = body_and_post[:doc_end_match.start()]
            postamble = body_and_post[doc_end_match.start():]
        else:
            body = body_and_post
            postamble = ""

        # Split body into frames using regex
        # We look for \begin{frame} ... \end{frame}
        # We also need to capture content BETWEEN frames (like \section{})
        
        # Pattern to capture: (content before frame)(frame content)
        # This is tricky because of nested braces. But usually frames are top level.
        # Let's use a simpler approach: Split by \begin{frame}
        
        # Improved splitting logic to handle \section{} outside frames
        # We want to keep \section{} attached to the following frame or as a separate item?
        # For simplicity, let's treat everything as a list of "chunks".
        # A chunk can be a frame, or a section command, or random text.
        
        # Regex to find \begin{frame} ... \end{frame}
        # Using non-greedy match for content inside
        frame_pattern = re.compile(r'(\\begin\{frame\}.*?\\end\{frame\})', re.DOTALL)
        
        parts = frame_pattern.split(body)
        # parts will be: [text_before, frame1, text_between, frame2, ...]
        
        chunks = [p for p in parts if p.strip()]
        
        return preamble, chunks, postamble

    def refine_page(self, page_content: str, aggressive: bool) -> str:
        """Refines a single page (frame) of TeX code."""
        
        if aggressive:
            system_prompt = """You are a LaTeX Beamer Layout Expert. 
            This specific slide has OVERFLOWED (content goes off the bottom).
            You must be AGGRESSIVE in reducing space.
            
            ### AGGRESSIVE Strategy (Priority Order):
            1.  **Use `adjustbox`**: Wrap the ENTIRE content inside the frame (after title) in an `adjustbox`.
                Example:
                \\begin{{frame}}{{Title}}
                    \\begin{{adjustbox}}{{max totalheight=0.8\\textheight, keepaspectratio}}
                    \\begin{{minipage}}{{\\linewidth}}
                        ... content ...
                    \\end{{minipage}}
                    \\end{{adjustbox}}
                \\end{{frame}}
            
            2.  **Force Shrink**: Add `[shrink=15]` to `\\begin{{frame}}`.
            
            3.  **Reduce Spacing**: 
                - Use `\\setlength{{\\itemsep}}{{0pt}}` INSIDE the itemize environment.
                - **CRITICAL**: Do NOT use `\\begin{{itemize}}[itemsep=...]`. This causes compilation errors.
                - Use `\\vspace{{-1em}}` to pull content up.
            
            Return ONLY the refined LaTeX code for this frame.
            """
        else:
            system_prompt = """You are a LaTeX Beamer Layout Expert. 
            This specific slide has OVERFLOWED (content goes off the bottom).
            Your goal is to fix the overflow by optimizing layout and content, WITHOUT simply shrinking everything.
            
            ### Refinement Strategy (Priority Order):
            1.  **Reduce Vertical Spacing (Level 1)**:
                - Add `\\vspace{{-0.5em}}` between blocks or before lists.
                - Reduce `itemsep` by adding `\\setlength{{\\itemsep}}{{0pt}}` INSIDE the list.
                - **CRITICAL**: Do NOT use `\\begin{{itemize}}[itemsep=...]`. This causes compilation errors.
            
            2.  **Reduce Font Size (Level 2)**:
                - Use `\\small` or `\\footnotesize` for list environments.
            
            3.  **Condense Content (Level 3)**:
                - Shorten bullet points (remove filler words).
                - If a block has too much text, summarize it.
            
            4.  **Split Page (Level 4 - Last Resort)**:
                - If the content is simply TOO MUCH for one page, split it into two frames.
                - Title the second frame "Title (Cont.)".
                - Return BOTH frames in your response.
            
            Return ONLY the refined LaTeX code for this frame (or frames).
            """

        human_template = """
        Here is the LaTeX code for the overflowing slide:
        ```latex
        {page_content_var}
        ```
        
        Fix the overflow. Return only the raw LaTeX code.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template)
        ])

        chain = prompt | self.llm
        response = chain.invoke({"page_content_var": page_content})
        
        content = response.content
        # Clean up markdown code blocks
        content = re.sub(r'^```latex\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'```$', '', content, flags=re.MULTILINE)
        
        return content.strip()

    def apply_scale_to_frame(self, frame_content: str, scale: float) -> str:
        """
        Wraps the frame content in an adjustbox with the specified scale.
        """
        lines = frame_content.split('\n')
        if not lines:
            return frame_content
            
        start_idx = -1
        for i, line in enumerate(lines):
            if '\\begin{frame}' in line:
                start_idx = i
                break
        
        if start_idx == -1:
            return frame_content
            
        end_idx = -1
        for i in range(len(lines)-1, -1, -1):
            if '\\end{frame}' in lines[i]:
                end_idx = i
                break
                
        if end_idx == -1 or end_idx <= start_idx:
            return frame_content

        has_adjustbox = False
        for i in range(start_idx+1, end_idx):
            if '\\begin{adjustbox}' in lines[i]:
                has_adjustbox = True
                break
        
        if has_adjustbox:
            for i in range(start_idx+1, end_idx):
                if '\\begin{adjustbox}' in lines[i]:
                    lines[i] = re.sub(r'max totalheight=[\d\.]+\\textheight', f'max totalheight={scale:.2f}\\\\textheight', lines[i])
                    return '\n'.join(lines)
            return frame_content
        else:
            prefix = lines[:start_idx+1]
            content = lines[start_idx+1:end_idx]
            suffix = lines[end_idx:]
            
            adjust_start = [
                f"\\begin{{adjustbox}}{{max totalheight={scale:.2f}\\textheight, keepaspectratio, center}}",
                "\\begin{minipage}{\\linewidth}"
            ]
            adjust_end = [
                "\\end{minipage}",
                "\\end{adjustbox}"
            ]
            
            return '\n'.join(prefix + adjust_start + content + adjust_end + suffix)

    def iterative_refine(self, tex_path: str, log_path: str, compile_func) -> bool:
        """
        Iteratively scales overflowing pages until they fit or limit is reached.
        """
        print("[Refiner] Starting Iterative Refinement (Smart Scaling)...")
        
        overflows = self.get_overflow_pages(log_path)
        if not overflows:
            return False
            
        page_scales = {} 
        max_iterations = 5
        current_scale_step = 0.05
        changes_made_total = False
        
        for i in range(max_iterations):
            if not overflows:
                print("[Refiner] All overflows resolved!")
                break
                
            print(f"[Refiner] Iteration {i+1}: Overflows on {overflows}")
            
            with open(tex_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            preamble, chunks, postamble = self.split_tex_content(content)
            new_chunks = chunks.copy()
            
            current_page = 1
            changes_made_iteration = False
            
            for idx, chunk in enumerate(chunks):
                if "\\begin{frame}" in chunk:
                    if current_page in overflows:
                        current_scale = page_scales.get(current_page, 1.0)
                        new_scale = current_scale - current_scale_step
                        
                        if new_scale < 0.6:
                            print(f"[Refiner] Page {current_page} reached min scale 0.6. Skipping.")
                        else:
                            page_scales[current_page] = new_scale
                            print(f"[Refiner] Scaling Page {current_page} to {new_scale:.2f}")
                            new_chunks[idx] = self.apply_scale_to_frame(chunk, new_scale)
                            changes_made_iteration = True
                            changes_made_total = True
                    
                    current_page += 1
            
            if not changes_made_iteration:
                print("[Refiner] No more changes possible (min scale reached).")
                break
                
            full_content = preamble + "\n".join(new_chunks) + postamble
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
                
            compile_func(tex_path)
            overflows = self.get_overflow_pages(log_path)
            
        return changes_made_total

    def refine_presentation(self, tex_path: str, log_path: str, aggressive: bool = False, compile_func=None) -> bool:
        """
        Refines the presentation by only targeting pages that overflowed.
        Returns True if any changes were made.
        """
        if aggressive and compile_func:
             return self.iterative_refine(tex_path, log_path, compile_func)

        if not os.path.exists(tex_path) or not os.path.exists(log_path):
            print("[Refiner] TeX or Log file not found.")
            return False

        # 1. Detect Overflow Pages
        overflow_pages = self.get_overflow_pages(log_path)
        if not overflow_pages:
            print("[Refiner] No overflows detected. Skipping refinement.")
            return False
        
        print(f"[Refiner] Detected overflows on pages: {overflow_pages}")

        # 2. Read and Split TeX
        with open(tex_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        preamble, chunks, postamble = self.split_tex_content(content)
        
        # 3. Map Pages to Chunks
        # This is the tricky part. We need to know which chunk corresponds to which page number.
        # Beamer pages increment on each frame.
        # However, \titlepage is a frame, \tableofcontents is a frame.
        # We iterate through chunks, count frames, and match with overflow_pages.
        
        new_chunks = chunks.copy()
        current_page = 1 # Beamer starts at page 1
        
        changes_made = False
        
        for i, chunk in enumerate(chunks):
            # Check if this chunk is a frame
            if "\\begin{frame}" in chunk:
                # This chunk represents a page (or multiple if allowframebreaks, but we assume 1 frame = 1 page for now)
                # Note: If a frame has overlays (<1->), it might generate multiple PDF pages, 
                # but usually Overfull \vbox is reported for the frame processing.
                # Let's assume 1 frame = 1 page index for simplicity in mapping.
                
                if current_page in overflow_pages:
                    print(f"[Refiner] Refining Page {current_page} (Aggressive: {aggressive})...")
                    refined_content = self.refine_page(chunk, aggressive)
                    new_chunks[i] = refined_content
                    changes_made = True
                
                current_page += 1
            else:
                # It's a section header or comment, doesn't consume a page number usually
                # Unless it's a \frame{...} command, but we use environments.
                pass
        
        if not changes_made:
            return False

        # 4. Reassemble
        full_content = preamble + "\n".join(new_chunks) + postamble
        
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
        return True
