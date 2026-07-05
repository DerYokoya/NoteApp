# This test file is for testing the DocumentTab class.
# It uses pytest and the qtbot fixture to create a test environment for the DocumentTab widget
# The tests check the initialization, modified flag, content handling, file path management,
# and save state tracking of the DocumentTab.
from models.document_tab import DocumentTab
from app.main_window import MainWindow
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QImage, QTextDocument
from pathlib import Path

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


def test_copy_and_paste_image_between_documents(qtbot):
    """Images copied from one document should paste into another as real images."""
    source_doc = DocumentTab("Source")
    target_doc = DocumentTab("Target")
    image = QImage(12, 12, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.blue)

    source_doc.text_edit.document().addResource(
        QTextDocument.ResourceType.ImageResource,
        QUrl("copied_between_docs.png"),
        image,
    )

    cursor = source_doc.text_edit.textCursor()
    cursor.insertImage("copied_between_docs.png")
    source_doc.text_edit.setTextCursor(cursor)

    mime_data = source_doc.text_edit.createMimeDataFromSelection()
    assert mime_data is not None
    assert mime_data.hasImage()

    target_doc.text_edit.insertFromMimeData(mime_data)

    pasted_html = target_doc.text_edit.toHtml()
    assert "<img" in pasted_html
    assert "src=" in pasted_html


def test_image_html_round_trip_preserves_embedded_data(qtbot):
    """Image resources should survive HTML save/load round trips."""
    doc = DocumentTab("Test")
    image = QImage(8, 8, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.green)

    doc.text_edit.document().addResource(
        QTextDocument.ResourceType.ImageResource,
        QUrl("roundtrip.png"),
        image,
    )

    cursor = doc.text_edit.textCursor()
    cursor.insertImage("roundtrip.png")
    doc.text_edit.setTextCursor(cursor)

    html = doc.get_content_html()
    assert "data:image/png;base64," in html

    restored_doc = DocumentTab("Restored")
    restored_doc.set_content(html, is_html=True)
    restored_html = restored_doc.get_content_html()

    assert "data:image/png;base64," in restored_html


def test_session_restore_preserves_tab_order_when_files_load_out_of_order(qtbot):
    """Previously open tabs should be restored in the same order they were saved."""
    window = MainWindow()

    window._is_restoring_session = True
    window._restore_pending = 2
    window._restore_active_index = -1
    window._restore_order = [Path("a.txt"), Path("b.txt")]

    window._on_file_loaded(Path("b.txt"), "<p>second</p>", False)
    window._on_file_loaded(Path("a.txt"), "<p>first</p>", False)

    assert [tab.current_file.name for tab in window.tabs] == ["a.txt", "b.txt"]


def test_save_session_uses_visible_tab_order_after_reordering(qtbot, tmp_path):
    """Saved session order should follow the visible tab order, even after moving tabs."""
    window = MainWindow()

    first_file = tmp_path / "first.txt"
    second_file = tmp_path / "second.txt"
    third_file = tmp_path / "third.txt"
    first_file.write_text("first", encoding="utf-8")
    second_file.write_text("second", encoding="utf-8")
    third_file.write_text("third", encoding="utf-8")

    for path in [first_file, second_file, third_file]:
        window._on_file_loaded(path, "<p>content</p>", False)

    window.tab_widget.tabBar().moveTab(1, 2)

    window._save_session()
    saved_tabs, _ = window.settings_manager.get_open_tabs()

    assert saved_tabs == [str(first_file), str(third_file), str(second_file)]