import re
from typing import List, Dict, Tuple

class LogParser:
    def __init__(self, log_content: str):
        self.log_content = log_content

    def parse_overflows(self, threshold: float = 10.0) -> List[int]:
        """
        Parses the LaTeX log content to find pages with vertical overflow (Overfull \vbox).
        Returns a list of page numbers where the overflow amount exceeds the threshold.
        """
        overflow_pages = []
        
        # Regex to find Overfull \vbox warnings and their amounts
        # Example: Overfull \vbox (272.11372pt too high) detected at line 120
        vbox_pattern = re.compile(r"Overfull \\vbox \((\d+\.\d+)pt too high\) detected at line (\d+)")
        
        # Regex to track page numbers. 
        # LaTeX logs usually output [1] [2] etc. when shipping a page.
        # We need to map the "line number" from the warning to the "page number".
        # However, mapping line numbers to pages from log is tricky because the log 
        # interleaves page output ([1]) with warnings.
        # A more robust way for Beamer is to look at the sequence of warnings and page markers.
        
        # Strategy:
        # 1. Split log by pages. The log usually has [1] ... [2] ...
        # But this is unreliable if content is complex.
        
        # Alternative Strategy:
        # Beamer frames correspond to pages. The log messages appear *while* processing the frame.
        # When a page is shipped, [N] is written.
        # So, if we see an Overfull warning, it belongs to the *next* page marker we see, 
        # OR it belongs to the page currently being processed.
        # Actually, "Overfull \vbox ... detected at line X" usually appears *before* the [N] marker for that page.
        
        lines = self.log_content.split('\n')
        current_page = 1
        
        # We will store potential overflows and assign them to the next page marker we encounter.
        pending_overflows = []
        
        for line in lines:
            # Check for page marker, e.g., [1], [2], [10]
            # LaTeX log page markers often start with [N
            # They might be split across lines like [1 <file...>]
            # So we just look for the start of a page marker.
            # We use a lookbehind or just match [ followed by digits and a space or end of line or <
            
            # Robust regex: Match [ followed by digits, ensuring it's likely a page marker
            # Usually page markers are at the start of a line or after a space
            # But in logs they can be messy. 
            # A safe bet is \[(\d+) followed by space, <, ], or end of line
            page_match = re.search(r'\[(\d+)(?=[\]\s<]|$)', line)
            
            if page_match:
                page_num = int(page_match.group(1))
                
                # If we had pending overflows, they belong to this page
                if pending_overflows:
                    for amount in pending_overflows:
                        if amount > threshold:
                            overflow_pages.append(page_num)
                    pending_overflows = []
                
                current_page = page_num
            
            # Check for overflow warning
            vbox_match = vbox_pattern.search(line)
            if vbox_match:
                amount = float(vbox_match.group(1))
                pending_overflows.append(amount)
                
        # Remove duplicates and sort
        return sorted(list(set(overflow_pages)))

    @staticmethod
    def from_file(log_path: str) -> 'LogParser':
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return LogParser(content)
        except FileNotFoundError:
            print(f"[LogParser] Log file not found: {log_path}")
            return LogParser("")
