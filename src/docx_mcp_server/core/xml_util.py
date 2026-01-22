from typing import Optional, List, Any, Iterator, Union, TYPE_CHECKING
from docx.text.paragraph import Paragraph
from docx.table import Table, _Cell
from docx.oxml.xmlchemy import BaseOxmlElement
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

if TYPE_CHECKING:
    from docx.document import Document

class ElementNavigator:
    """
    Helps navigate the underlying XML structure of python-docx objects.
    Provides robust methods to access parents, siblings, and paths.
    """

    @staticmethod
    def get_parent_xml(element_xml: BaseOxmlElement) -> Optional[BaseOxmlElement]:
        """Get the parent XML element."""
        return element_xml.getparent()

    @staticmethod
    def get_docx_parent(element: Any, session_document: Optional['Document'] = None) -> Any:
        """
        Attempt to resolve the high-level python-docx parent object.
        This is tricky because python-docx objects are often transient wrappers around XML.

        Args:
            element: The python-docx object (Paragraph, Table, etc.)
            session_document: Optional Document object to use as root/fallback.

        Returns:
            The parent python-docx object (Document, _Cell, etc.) or None.
        """
        # Try internal attribute first (most reliable for direct children of body)
        if hasattr(element, '_parent') and element._parent:
            return element._parent

        # If we have the XML parent, we might be able to infer context
        if hasattr(element, '_element'):
            parent_xml = element._element.getparent()
            if parent_xml is None:
                return None

            # If parent is body, and we have the document, return document
            if session_document and hasattr(session_document, '_body') and hasattr(session_document._body, '_element'):
                if parent_xml == session_document._body._element:
                    return session_document

            # TODO: Handle Cell parents properly by looking up in session registry?
            # Re-wrapping cells from XML is hard without the Table context.

        return None

    @staticmethod
    def get_next_sibling_xml(element_xml: BaseOxmlElement) -> Optional[BaseOxmlElement]:
        """Get the next sibling XML element."""
        return element_xml.getnext()

    @staticmethod
    def get_prev_sibling_xml(element_xml: BaseOxmlElement) -> Optional[BaseOxmlElement]:
        """Get the previous sibling XML element."""
        return element_xml.getprevious()

    @staticmethod
    def iter_children_xml(parent_xml: BaseOxmlElement) -> Iterator[BaseOxmlElement]:
        """Iterate over child XML elements."""
        return parent_xml.iterchildren()

    @staticmethod
    def get_path(element: Any) -> str:
        """
        Generate a simplified breadcrumb path for the element.
        e.g., "Body/Table[0]/Row[1]/Cell[0]/Paragraph[2]"
        """
        if not hasattr(element, '_element'):
            return "Unknown"

        xml = element._element
        path_parts = []

        current = xml
        while current is not None:
            tag = current.tag.split('}')[-1]  # Remove namespace

            # Calculate index among same-tag siblings
            idx = 0
            prev = current.getprevious()
            while prev is not None:
                if prev.tag == current.tag:
                    idx += 1
                prev = prev.getprevious()

            name = tag
            if tag == 'body':
                name = 'Body'
            elif tag == 'tbl':
                name = 'Table'
            elif tag == 'tr':
                name = 'Row'
            elif tag == 'tc':
                name = 'Cell'
            elif tag == 'p':
                name = 'Para'
            elif tag == 'r':
                name = 'Run'

            path_parts.append(f"{name}[{idx}]")
            current = current.getparent()

            # Stop at document root (usually body's parent is document)
            if current is not None and current.tag.endswith('document'):
                path_parts.append("Document")
                break

        return "/".join(reversed(path_parts))


class ElementManipulator:
    """
    Handles low-level XML insertion and manipulation.
    """

    @staticmethod
    def insert_xml_before(target_xml: BaseOxmlElement, new_xml: BaseOxmlElement):
        """Insert new_xml immediately before target_xml."""
        target_xml.addprevious(new_xml)

    @staticmethod
    def insert_xml_after(target_xml: BaseOxmlElement, new_xml: BaseOxmlElement):
        """Insert new_xml immediately after target_xml."""
        target_xml.addnext(new_xml)

    @staticmethod
    def append_xml_to_parent(parent_xml: BaseOxmlElement, new_xml: BaseOxmlElement):
        """Append new_xml to the end of parent's children."""
        parent_xml.append(new_xml)

    @staticmethod
    def insert_at_index(parent_xml: BaseOxmlElement, new_xml: BaseOxmlElement, index: int):
        """Insert new_xml at specific index in parent."""
        parent_xml.insert(index, new_xml)
