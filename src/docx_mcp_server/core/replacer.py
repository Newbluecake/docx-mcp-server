from typing import List, Tuple
from docx.text.paragraph import Paragraph

def replace_text_in_paragraph(paragraph: Paragraph, old_text: str, new_text: str) -> bool:
    """
    Simple replacement: checks if old_text is in the whole paragraph text.
    If yes, it attempts to replace it.

    Strategy:
    1. Check if match exists in full text.
    2. If it exists strictly within single runs, replace inplace (preserves formatting).
    3. If it spans runs, we fall back to a safer but destructive approach:
       - Keep the style of the paragraph.
       - Clear content.
       - Add new run with replaced text.
       (This loses mixed formatting within the paragraph, but guarantees text correctness).

    TODO: A full stitching algorithm that preserves mixed formatting is complex
    and requires tracking character indices across runs. For this version,
    we prioritize text correctness and single-run formatting preservation.
    """

    # 1. Try single run replacement (best case)
    replaced_in_run = False
    for run in paragraph.runs:
        if old_text in run.text:
            run.text = run.text.replace(old_text, new_text)
            replaced_in_run = True

    if replaced_in_run:
        return True

    # 2. Check full text
    full_text = paragraph.text
    if old_text not in full_text:
        return False

    # 3. Fallback: Replace text but reset runs
    # We try to preserve the *paragraph* style/alignment but runs are reset.
    # We could try to copy font from the first run?

    first_run_font = None
    if paragraph.runs:
        # Shallow copy font props from first run to apply to new run?
        # A bit risky if None.
        pass

    new_full_text = full_text.replace(old_text, new_text)
    paragraph.clear()
    run = paragraph.add_run(new_full_text)

    return True
