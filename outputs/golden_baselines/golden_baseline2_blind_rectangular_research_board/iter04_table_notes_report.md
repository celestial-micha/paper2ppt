# Iter04 Table Notes Report

Input deck:

- `04_blind_rectangular_iter03_style_refined.pptx`

Output deck:

- `04_blind_rectangular_iter04_table_notes.pptx`

Human feedback converted to benchmark rules:

- `table_view_label_missing`: table evidence pages should include the compact `Focused table view` label above the visible table, not only the generic `EVIDENCE / TABLE` component label.
- `table_caption_missing_or_not_centered`: table evidence pages should include a short centered explanatory note below the table.

Renderer changes:

- Ordinary native table evidence now uses the same table title treatment as dense-table fallback pages.
- Table notes use `proof.focus` first for concise readable captions, then fall back to parsed table caption/title when needed.
- Table notes are center-aligned under the table.

Targeted audit result on slides 08/14/23/24:

- iter03: 6 targeted findings on slides 14/23/24.
- iter04: 0 targeted findings.

Validation:

- `fourway.py` and `nonvisual_audit.py` compile successfully.
- `benchmarks/from_scratch_human_feedback_benchmark.json` parses successfully.
