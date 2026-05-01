import os
import sys
import json
from pathlib import Path
from rich.console import Console

console = Console()

class PdfExtractor:
    def __init__(self, pdf_path: str, output_dir: str):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        
    def _get_mineru_model_path(self):
        """
        Dynamically find the MinerU model path in the local HuggingFace cache.
        """
        # Try to find the model in the default HuggingFace cache
        hf_home = os.getenv('HF_HOME', os.path.expanduser('~/.cache/huggingface'))
        model_dir = Path(hf_home) / 'hub' / 'models--opendatalab--PDF-Extract-Kit-1.0' / 'snapshots'
        
        if model_dir.exists():
            # Get the latest snapshot
            snapshots = [d for d in model_dir.iterdir() if d.is_dir()]
            if snapshots:
                # Sort by modification time to get the latest
                latest_snapshot = max(snapshots, key=os.path.getmtime)
                return str(latest_snapshot)
        return None

    def _configure_mineru(self):
        """
        Configures MinerU to use local models if available by monkeypatching the config reader.
        This avoids creating a physical mineru.json file.
        """
        model_path = self._get_mineru_model_path()
        
        if model_path:
            try:
                # Import config_reader to patch it
                import mineru.utils.config_reader as config_reader
                
                # Define a mock function that returns our configuration
                def mock_get_local_models_dir():
                    return {
                        "pipeline": model_path
                    }
                
                # Apply the patch
                config_reader.get_local_models_dir = mock_get_local_models_dir
                
                # Set the environment variable to force local mode
                os.environ['MINERU_MODEL_SOURCE'] = 'local'
                
                console.print(f"[blue]Using local MinerU model at: {model_path}[/blue]")
            except ImportError:
                # If we can't import it here, the main try/except block in extract will catch it later
                pass
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to configure local MinerU model: {e}. Using default behavior.[/yellow]")
        else:
            console.print("[yellow]Local MinerU model not found in cache. It may be downloaded.[/yellow]")

    def extract(self) -> str:
        """
        Extracts PDF content to Markdown and images using MinerU (magic-pdf).
        Returns the path to the generated Markdown file.
        """
        # Configure MinerU to use local models
        self._configure_mineru()

        try:
            from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
            from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
            from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
            from mineru.data.data_reader_writer import FileBasedDataWriter
            from mineru.utils.enum_class import MakeMode
        except ImportError:
            console.print("[red]Error: 'magic-pdf' (MinerU) is not installed.[/red]")
            console.print("Please install it to use PDF extraction features.")
            console.print("Refer to: https://github.com/opendatalab/MinerU")
            sys.exit(1)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")

        console.print(f"[bold green]Extracting PDF: {self.pdf_path}...[/bold green]")
        
        # 1. Read PDF
        with open(self.pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # 2. Analyze PDF
        console.print("[cyan]Running MinerU analysis (this may take time)...[/cyan]")
        parse_method = os.getenv("PDF_PARSE_METHOD", "auto")
        try:
            infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(
                pdf_bytes_list=[pdf_bytes],
                lang_list=['en'],  # Default to English for now
                parse_method=parse_method,
                formula_enable=True,
                table_enable=True
            )
        except Exception as e:
            console.print(f"[red]MinerU Analysis Failed: {e}[/red]")
            raise e

        model_json = infer_results[0]
        image_list = all_image_lists[0]
        pdf_doc = all_pdf_docs[0]
        lang = lang_list[0]
        ocr_enable = ocr_enabled_list[0]

        # 3. Prepare Output
        # We want images in 'supplement' folder
        image_subdir_name = "supplement"
        image_dir = self.output_dir / image_subdir_name
        os.makedirs(image_dir, exist_ok=True)
        
        image_writer = FileBasedDataWriter(str(image_dir))

        # 4. Convert to Middle JSON & Extract Images
        console.print("[cyan]Extracting images and structure...[/cyan]")
        middle_json = pipeline_result_to_middle_json(
            model_json,
            image_list,
            pdf_doc,
            image_writer,
            lang,
            ocr_enable,
            formula_enabled=True
        )

        # 5. Generate Markdown
        console.print("[cyan]Generating Markdown...[/cyan]")
        md_content = pipeline_union_make(
            middle_json['pdf_info'],
            MakeMode.MM_MD,
            image_subdir_name
        )

        # 6. Save Markdown
        md_filename = "paper.md"
        md_file_path = self.output_dir / md_filename
        
        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        console.print(f"[green]✓ PDF Extracted to {self.output_dir}[/green]")
        return str(md_file_path)
