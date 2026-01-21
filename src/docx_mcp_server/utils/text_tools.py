from typing import Dict, List, Any
from docx.text.paragraph import Paragraph
from docx.table import Table

class TextTools:
    """
    Utilities for text manipulation in docx elements.
    """

    def batch_replace_text(self, elements: List[Any], replacements: Dict[str, str]) -> int:
        """
        Perform batch replacement of text in the provided elements.
        Currently strictly operates on Run level to preserve formatting.
        Does NOT handle text spanning across multiple runs (will skip those matches).

        Args:
            elements: List of docx objects (Paragraphs, Tables, or Cells) to process.
            replacements: Dictionary mapping {old_text: new_text}.

        Returns:
            Total count of replacements made.
        """
        count = 0
        for element in elements:
            if isinstance(element, Paragraph):
                count += self._process_paragraph(element, replacements)
            elif isinstance(element, Table):
                for row in element.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            count += self._process_paragraph(p, replacements)
            # Handle other types if necessary (e.g. Cell directly if passed)

        return count

    def _process_paragraph(self, paragraph: Paragraph, replacements: Dict[str, str]) -> int:
        count = 0
        for run in paragraph.runs:
            if not run.text:
                continue

            original_text = run.text
            modified_text = original_text

            for old, new in replacements.items():
                if old in modified_text:
                    matches = modified_text.count(old)
                    modified_text = modified_text.replace(old, new)
                    count += matches

            if modified_text != original_text:
                run.text = modified_text

        return count
