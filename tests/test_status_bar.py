# ============================================================================
# StatusBarWidget Tests
# covers initial labels and the update_file/update_cursor/update_word_count
# display helpers.
# ============================================================================

import pytest
from PyQt6.QtWidgets import QApplication

from widgets.status_bar import StatusBarWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def status_bar(qapp):
    return StatusBarWidget()


def test_initial_labels(status_bar):
    assert status_bar.file_label.text() == "No file"
    assert status_bar.cursor_label.text() == "Line 1, Col 1"
    assert status_bar.word_count_label.text() == "0 words"
    assert status_bar.encoding_label.text() == "UTF-8"


def test_update_file_with_path(status_bar):
    status_bar.update_file("/home/user/notes.txt")
    assert status_bar.file_label.text() == "/home/user/notes.txt"


def test_update_file_with_empty_path_shows_no_file(status_bar):
    status_bar.update_file("/home/user/notes.txt")
    status_bar.update_file("")
    assert status_bar.file_label.text() == "No file"


def test_update_file_with_none_shows_no_file(status_bar):
    status_bar.update_file(None)
    assert status_bar.file_label.text() == "No file"


def test_update_cursor(status_bar):
    status_bar.update_cursor(5, 12)
    assert status_bar.cursor_label.text() == "Line 5, Col 12"


def test_update_word_count(status_bar):
    status_bar.update_word_count(42, 210)
    assert status_bar.word_count_label.text() == "42 words, 210 chars"


def test_update_word_count_zero(status_bar):
    status_bar.update_word_count(0, 0)
    assert status_bar.word_count_label.text() == "0 words, 0 chars"
