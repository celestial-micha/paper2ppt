import os
from rich.console import Console

console = Console()

class MarkdownLoader:
    def __init__(self, input_path: str):
        self.input_path = input_path

    def load(self) -> str:
        """
        Loads the Markdown content from the file.
        """
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Markdown file not found: {self.input_path}")
            
        console.print(f"[cyan]Loading Markdown: {self.input_path}[/cyan]")
        with open(self.input_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return content
