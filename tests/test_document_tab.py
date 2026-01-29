from models.document_tab import DocumentTab
import pytest

def test_document_modified_flag(qtbot): # Add qtbot here
    doc = DocumentTab("Test")
    doc.text_edit.setPlainText("Hello")

    # Manually force the QDocument state to match the text input
    doc.text_edit.document().setModified(True) 

    assert doc.is_modified is True

    doc.mark_saved()
    assert doc.is_modified is False