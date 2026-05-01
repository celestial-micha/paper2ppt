import os
import re
import shutil
from pathlib import Path

class TexLoader:
    def __init__(self, root_file_path: str, output_dir: str):
        self.root_file_path = Path(root_file_path).resolve()
        self.root_dir = self.root_file_path.parent
        self.output_dir = Path(output_dir).resolve()
        self.supplement_dir = self.output_dir / "supplement"
        
        # Ensure output directories exist
        self.supplement_dir.mkdir(parents=True, exist_ok=True)

    def load_and_flatten(self) -> str:
        """
        Loads the root TeX file and recursively resolves \input and \include commands.
        Also extracts images to the supplement directory.
        """
        print(f"[TexLoader] Loading {self.root_file_path}...")
        return self._process_file(self.root_file_path)

    def _process_file(self, file_path: Path) -> str:
        if not file_path.exists():
            # Try adding .tex extension if missing
            if file_path.with_suffix('.tex').exists():
                file_path = file_path.with_suffix('.tex')
            else:
                print(f"[TexLoader] Warning: File not found: {file_path}")
                return f"% MISSING FILE: {file_path}\n"

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Remove comments (simple approach)
        # content = re.sub(r'(?<!\\)%.*', '', content) 
        # Keeping comments might be useful for context, but usually we want clean text.
        # Let's keep it simple for now and not strip comments aggressively to avoid breaking things.

        # Resolve \input{...} and \include{...}
        # Regex captures: \input{filename} or \include{filename}
        # We need to handle nested inputs, so we process the content.
        
        def replace_input(match):
            command = match.group(1) # input or include
            rel_path = match.group(2)
            
            # Construct full path
            # Assuming paths are relative to the current file's directory or root? 
            # Usually relative to the main file in simple projects, or current dir.
            # Let's assume relative to the file being processed or root. 
            # In LaTeX, it's often relative to the working directory (root).
            
            target_path = (self.root_dir / rel_path).resolve()
            return self._process_file(target_path)

        # Pattern: \(input|include)\{([^}]+)\}
        content = re.sub(r'\\(input|include)\{([^}]+)\}', replace_input, content)

        # Extract Images
        content = self._extract_images(content, file_path)

        return content

    def _extract_images(self, content: str, current_file_path: Path) -> str:
        # Pattern: \includegraphics[options]{path} or \includegraphics{path}
        # We want to capture the path.
        
        def replace_image(match):
            full_match = match.group(0)
            # options = match.group(1) # Optional
            image_path_raw = match.group(1)
            
            # Resolve image path
            # LaTeX image paths can be relative to root or have graphicspath.
            # We'll try to find it.
            
            possible_paths = [
                self.root_dir / image_path_raw,
                current_file_path.parent / image_path_raw,
                self.root_dir / "Figures" / image_path_raw, # Common folder
                self.root_dir / "vis" / image_path_raw, # From user workspace structure
            ]
            
            found_image = None
            for p in possible_paths:
                if p.exists():
                    found_image = p
                    break
                # Try extensions
                for ext in ['.png', '.jpg', '.jpeg', '.pdf']:
                    p_ext = p.with_suffix(ext)
                    if p_ext.exists():
                        found_image = p_ext
                        break
                if found_image:
                    break
            
            if found_image:
                # Copy to supplement
                dest_name = found_image.name
                dest_path = self.supplement_dir / dest_name
                shutil.copy2(found_image, dest_path)
                print(f"[TexLoader] Extracted image: {found_image.name}")
                
                # We don't necessarily need to change the text in the flattened output 
                # because the LLM just needs to know an image exists.
                # But for the final generation, we might want to know the filename.
                # Let's leave the text as is, or maybe annotate it?
                # The design says: "Copy these images...". 
                # The Writer will decide to use them.
                return full_match
            else:
                print(f"[TexLoader] Warning: Image not found: {image_path_raw}")
                return full_match

        # Regex for \includegraphics
        # \includegraphics[...]{...} or \includegraphics{...}
        # This regex is a bit simplified.
        content = re.sub(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', replace_image, content)
        return content

if __name__ == "__main__":
    # Test
    loader = TexLoader("paper/attention_is_all_you_need/ms.tex", "output/beta_test")
    flat = loader.load_and_flatten()
    print(f"Flattened length: {len(flat)}")
    with open("output/beta_test/flattened.tex", "w") as f:
        f.write(flat)
