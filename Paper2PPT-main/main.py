import os
import sys
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from src.loaders.tex_loader import TexLoader
from src.loaders.pdf_extractor import PdfExtractor
from src.loaders.markdown_loader import MarkdownLoader
from src.pipeline.planner import Planner
from src.pipeline.generator import Generator
from src.pipeline.refiner import Refiner

console = Console()

def main():
    console.print("[bold blue]Paper2PPT Beta[/bold blue]", justify="center")
    
    # 1. Configuration
    import sys
    if "--auto" in sys.argv:
        input_path = "paper/tex/attention_is_all_you_need/ms.tex"
        duration = 10
        auto_mode = True
    else:
        # Scan for available files
        available_items = []
        
        # 1. Scan PDF files
        if os.path.exists("paper/pdf"):
            for f in os.listdir("paper/pdf"):
                if f.endswith(".pdf"):
                    available_items.append({"type": "pdf", "path": os.path.join("paper/pdf", f), "display": f"[PDF] {f}"})

        # 2. Scan TeX directories
        if os.path.exists("paper/tex"):
            for d in os.listdir("paper/tex"):
                dir_path = os.path.join("paper/tex", d)
                if os.path.isdir(dir_path):
                    available_items.append({"type": "tex_dir", "path": dir_path, "display": f"[TeX Project] {d}/"})

        if not available_items:
            console.print("[red]No .pdf files in paper/pdf or directories in paper/tex found.[/red]")
            return

        console.print("\n[bold]Available Papers:[/bold]")
        for idx, item in enumerate(available_items):
            console.print(f"{idx + 1}. {item['display']}")
            
        file_idx = IntPrompt.ask("Select paper", default=1)
        if 1 <= file_idx <= len(available_items):
            selected_item = available_items[file_idx - 1]
            
            if selected_item["type"] == "pdf":
                input_path = selected_item["path"]
            else:
                # Resolve TeX directory to main file
                tex_dir = selected_item["path"]
                # Try common names
                candidates = ["ms.tex", "main.tex", "paper.tex"]
                found = False
                for c in candidates:
                    if os.path.exists(os.path.join(tex_dir, c)):
                        input_path = os.path.join(tex_dir, c)
                        found = True
                        break
                
                if not found:
                    # Fallback: Find any .tex file
                    tex_files = [f for f in os.listdir(tex_dir) if f.endswith(".tex")]
                    if not tex_files:
                        console.print(f"[red]No .tex files found in {tex_dir}[/red]")
                        return
                    # If multiple, maybe ask? For now, pick the first one or largest?
                    # Let's pick the one with 'main' or 'ms' in name if possible, else first
                    input_path = os.path.join(tex_dir, tex_files[0])
                    console.print(f"[yellow]Auto-selected TeX file: {input_path}[/yellow]")

        else:
            console.print("[red]Invalid selection.[/red]")
            return

        duration = IntPrompt.ask("Presentation Duration (min)", default=10)
        auto_mode = False
    
    if not os.path.exists(input_path):
        console.print(f"[red]Error: File {input_path} not found.[/red]")
        return
    
    # Determine Output Directory
    from pathlib import Path
    p = Path(input_path)
    if input_path.endswith(".pdf"):
        project_name = p.stem
        output_folder_name = f"{project_name}_pdf"
    else:
        # TeX
        # Check if it's in a project subdirectory (e.g., paper/tex/project/main.tex)
        # or a flat file (e.g., paper/tex/main.tex)
        parent_name = p.parent.name
        if parent_name == "tex":
            project_name = p.stem
        else:
            project_name = parent_name
        output_folder_name = f"{project_name}_tex"

    output_dir = os.path.join("output", output_folder_name)
    os.makedirs(output_dir, exist_ok=True)
    console.print(f"[blue]Output Directory: {output_dir}[/blue]")

    # 2. Ingestion (TeX or PDF)
    full_text = ""
    if input_path.endswith(".pdf"):
        md_file_path = os.path.join(output_dir, "paper.md")
        if os.path.exists(md_file_path):
            console.print(f"[yellow]Found existing Markdown at {md_file_path}. Skipping extraction.[/yellow]")
            md_path = md_file_path
        else:
            with console.status("[bold green]Extracting PDF content (MinerU)..."):
                extractor = PdfExtractor(input_path, output_dir)
                md_path = extractor.extract()
        
        loader = MarkdownLoader(md_path)
        full_text = loader.load()
    else:
        with console.status("[bold green]Reading and flattening TeX..."):
            loader = TexLoader(input_path, output_dir)
            full_text = loader.load_and_flatten()
            
    console.print(f"[green]✓[/green] Loaded {len(full_text)} characters.")

    # 3. Planning
    with console.status("[bold green]Generating Presentation Plan..."):
        planner = Planner()
        plan = planner.create_plan(full_text, duration)
    
    console.print(f"\n[bold]Plan Generated:[/bold] {plan.title} by {plan.authors}")
    
    table = Table(title="Slide Plan")
    table.add_column("Section", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("Goal", style="green")
    table.add_column("Layout", style="yellow")

    for slide in plan.slides:
        table.add_row(slide.section, slide.title, slide.content_goal[:50]+"...", slide.suggested_layout)
    
    console.print(table)
    
    if not auto_mode:
        if not Prompt.ask("Proceed with generation?", choices=["y", "n"], default="y") == "y":
            console.print("[yellow]Aborted.[/yellow]")
            return

    # 4. Generation
    with console.status("[bold green]Generating Slides and Compiling PDF..."):
        generator = Generator(output_dir)
        generator.generate_presentation(plan, full_text, plan.title, plan.authors)

    # 5. Refinement (AI Calibration)
    if auto_mode or Prompt.ask("Proceed with AI Layout Calibration?", choices=["y", "n"], default="y") == "y":
        with console.status("[bold green]Refining Layout (AI Calibration)..."):
            refiner = Refiner(output_dir)
            tex_path = os.path.join(output_dir, "presentation.tex")
            log_path = tex_path.replace(".tex", ".log")
            
            # Pass 1: Standard Refinement (Page-wise)
            # Only runs if overflows are detected
            if refiner.refine_presentation(tex_path, log_path, aggressive=False):
                console.print("[green]✓[/green] Applied standard refinement to overflowing pages.")
                generator.compile_pdf(tex_path) # Recompile to update log
            else:
                console.print("[green]✓[/green] No overflows detected or no changes needed.")

            # Pass 2: Aggressive Refinement (Page-wise)
            # Check log again after Pass 1
            if refiner.get_overflow_pages(log_path):
                console.print("[yellow]Warning: Overflows persist. Attempting AGGRESSIVE refinement (Smart Iteration)...[/yellow]")
                if refiner.refine_presentation(tex_path, log_path, aggressive=True, compile_func=generator.compile_pdf):
                    console.print("[green]✓[/green] Applied aggressive refinement.")
                
                # Final check
                final_overflows = refiner.get_overflow_pages(log_path)
                if final_overflows:
                     console.print(f"[red]Warning: Overflows still persist on pages {final_overflows}. Please check manually.[/red]")
                else:
                     console.print("[green]✓[/green] All overflows resolved.")
            else:
                console.print("[green]✓[/green] Layout clean.")

            console.print(f"[green]✓[/green] Final PDF: {tex_path.replace('.tex', '.pdf')}")

    console.print(f"\n[bold blue]Done![/bold blue] Output in {output_dir}")

if __name__ == "__main__":
    main()
