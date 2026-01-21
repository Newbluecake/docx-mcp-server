from typing import Any
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx.table import Table

class FormatPainter:
    def copy_format(self, source: Any, target: Any) -> None:
        """
        Copy format from source to target.
        Dispatches to specific methods based on type.
        """
        # Exact match dispatch
        if isinstance(source, Run) and isinstance(target, Run):
            self._copy_run_format(source, target)
        elif isinstance(source, Paragraph) and isinstance(target, Paragraph):
            self._copy_paragraph_format(source, target)
        elif isinstance(source, Table) and isinstance(target, Table):
            self._copy_table_format(source, target)

        # Smart matching (Cross-type)
        elif isinstance(source, Paragraph) and isinstance(target, Run):
            # Apply Paragraph Style's font to Run
            if source.style and hasattr(source.style, 'font'):
                self._copy_font_properties(source.style.font, target.font)
        elif isinstance(source, Run) and isinstance(target, Paragraph):
            # Apply Run's font to all runs in Paragraph
            for run in target.runs:
                self._copy_font_properties(source.font, run.font)

        else:
            raise ValueError(f"Unsupported object type or mismatch: {type(source)} -> {type(target)}")

    def _copy_font_properties(self, src_font: Any, tgt_font: Any) -> None:
        """Helper to copy font properties from one font object to another."""
        # Font name and size
        tgt_font.name = src_font.name
        tgt_font.size = src_font.size

        # Boolean properties
        tgt_font.bold = src_font.bold
        tgt_font.italic = src_font.italic
        tgt_font.underline = src_font.underline
        tgt_font.strike = src_font.strike
        tgt_font.superscript = src_font.superscript
        tgt_font.subscript = src_font.subscript

        # Color
        if src_font.color and src_font.color.rgb:
            tgt_font.color.rgb = src_font.color.rgb

        # Highlight
        if hasattr(src_font, 'highlight_color'):
            tgt_font.highlight_color = src_font.highlight_color

    def _copy_run_format(self, source: Run, target: Run) -> None:
        """Copy all font properties from source run to target run."""
        self._copy_font_properties(source.font, target.font)

    def _copy_paragraph_format(self, source: Paragraph, target: Paragraph) -> None:
        """Copy paragraph formatting and style."""
        src_fmt = source.paragraph_format
        tgt_fmt = target.paragraph_format

        # Alignment
        tgt_fmt.alignment = src_fmt.alignment

        # Indentation
        tgt_fmt.left_indent = src_fmt.left_indent
        tgt_fmt.right_indent = src_fmt.right_indent
        tgt_fmt.first_line_indent = src_fmt.first_line_indent

        # Spacing
        tgt_fmt.space_before = src_fmt.space_before
        tgt_fmt.space_after = src_fmt.space_after
        tgt_fmt.line_spacing = src_fmt.line_spacing
        tgt_fmt.line_spacing_rule = src_fmt.line_spacing_rule

        # Pagination
        tgt_fmt.keep_together = src_fmt.keep_together
        tgt_fmt.keep_with_next = src_fmt.keep_with_next
        tgt_fmt.page_break_before = src_fmt.page_break_before
        tgt_fmt.widow_control = src_fmt.widow_control

        # Style
        # Note: assigning style by name usually works in python-docx if style exists
        # We try to copy the style object or name
        target.style = source.style

    def _copy_table_format(self, source: Table, target: Table) -> None:
        """
        Copy table formatting including style, borders, and shading.
        Uses low-level OXML manipulation for borders/shading as python-docx API is limited here.
        """
        import copy
        from docx.oxml.ns import qn

        # Copy Style
        target.style = source.style

        # OXML Manipulation for Borders and Shading
        # We act on tblPr (Table Properties)
        src_tblPr = source._element.tblPr
        tgt_tblPr = target._element.tblPr

        # 1. Borders (tblBorders)
        src_borders = src_tblPr.find(qn('w:tblBorders'))
        if src_borders is not None:
            # Remove existing borders in target if any
            old_borders = tgt_tblPr.find(qn('w:tblBorders'))
            if old_borders is not None:
                tgt_tblPr.remove(old_borders)

            # Deep copy source borders and append to target
            new_borders = copy.deepcopy(src_borders)
            tgt_tblPr.append(new_borders)

        # 2. Shading (shd)
        src_shd = src_tblPr.find(qn('w:shd'))
        if src_shd is not None:
            # Remove existing shading
            old_shd = tgt_tblPr.find(qn('w:shd'))
            if old_shd is not None:
                tgt_tblPr.remove(old_shd)

            # Deep copy
            new_shd = copy.deepcopy(src_shd)
            tgt_tblPr.append(new_shd)

        # Grid/Column widths (tblGrid) - Optional but good for layout consistency
        src_grid = source._element.find(qn('w:tblGrid'))
        if src_grid is not None:
            old_grid = target._element.find(qn('w:tblGrid'))
            if old_grid is not None:
                target._element.remove(old_grid)
            target._element.insert(0, copy.deepcopy(src_grid)) # tblGrid is usually early in sequence
