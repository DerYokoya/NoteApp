# This test file is for testing the DocumentTab class.
# It uses pytest and the qtbot fixture to create a test environment for the DocumentTab widget
# The tests check the initialization, modified flag, content handling, file path management,
# and save state tracking of the DocumentTab.
from models.document_tab import DocumentTab
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QImage, QTextDocument

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_document_initialization(qtbot):
    """Test document tab initialization"""
    doc = DocumentTab("Test")
    assert doc.get_display_name() == "Test"
    assert doc.current_file is None
    assert doc.is_modified is False
    assert doc.text_edit.toPlainText() == ""

def test_document_modified_flag(qtbot):
    """Test modified flag works correctly"""
    doc = DocumentTab("Test")
    doc.text_edit.setPlainText("Hello")
    doc.text_edit.document().setModified(True)
    assert doc.is_modified is True
    
    doc.mark_saved()
    assert doc.is_modified is False

def test_document_content(qtbot):
    """Test getting and setting content"""
    doc = DocumentTab("Test")

    # Test plain text
    doc.set_content("Hello World", is_html=False)
    assert doc.get_content_plain() == "Hello World"
    assert doc.get_content_html() is not None

    # Test HTML content
    html_content = "<p><b>Bold</b> text</p>"
    doc.set_content(html_content, is_html=True)
    # Qt adds extra HTML wrapper, check for the bold text instead
    assert "Bold" in doc.get_content_html()
    assert "font-weight:700" in doc.get_content_html()  # Qt represents bold as font-weight:700

def test_document_file_path(qtbot, tmp_path):
    """Test file path handling"""
    doc = DocumentTab("Test")
    test_file = tmp_path / "test.txt"
    
    doc.current_file = test_file
    assert doc.get_file_path() == str(test_file)
    assert doc.get_display_name() == "test.txt"

def test_document_save_state(qtbot):
    """Test save state tracking"""
    doc = DocumentTab("Test")
    assert doc.is_modified is False
    
    doc.text_edit.setPlainText("New content")
    doc.text_edit.document().setModified(True)
    assert doc.is_modified is True
    
    doc.mark_saved()
    assert doc.is_modified is False


def test_copying_image_exposes_clipboard_image_data(qtbot):
    """Copied images should carry image data so a later paste can restore them."""
    doc = DocumentTab("Test")
    image = QImage(16, 16, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.red)

    doc.text_edit.document().addResource(
        QTextDocument.ResourceType.ImageResource,
        QUrl("copied.png"),
        image,
    )

    cursor = doc.text_edit.textCursor()
    cursor.insertImage("copied.png")
    doc.text_edit.setTextCursor(cursor)

    mime_data = doc.text_edit.createMimeDataFromSelection()

    assert mime_data is not None
    assert mime_data.hasImage()
    pasted_image = mime_data.imageData()
    assert isinstance(pasted_image, QImage)
    assert pasted_image.size() == image.size()