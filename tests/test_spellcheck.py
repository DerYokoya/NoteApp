# ============================================================================
# Spell Check Tests
# covers SpellCheckService lookups/suggestions and highlighter behavior
# ============================================================================

import pytest
from PyQt6.QtWidgets import QApplication

from services.spellcheck_service import SpellCheckService
from models.document_tab import DocumentTab
from widgets.spellcheck_highlighter import SpellCheckHighlighter


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def spell_service():
    return SpellCheckService()


def test_correct_word_is_correct(spell_service):
    assert spell_service.is_correct("hello") is True


def test_misspelled_word_is_incorrect(spell_service):
    assert spell_service.is_correct("teh") is False


def test_suggestions_include_expected_correction(spell_service):
    suggestions = spell_service.suggestions("teh")
    assert "the" in suggestions


def test_add_word_marks_it_correct(spell_service):
    assert spell_service.is_correct("qwertzuiop") is False
    spell_service.add_word("qwertzuiop")
    assert spell_service.is_correct("qwertzuiop") is True


def test_add_word_is_case_insensitive(spell_service):
    spell_service.add_word("Zephyrix")
    assert spell_service.is_correct("zephyrix") is True
    assert spell_service.is_correct("ZEPHYRIX") is True


def test_match_case_preserves_capitalized_word():
    from app.controllers.context_menu_controller import ContextMenuController
    assert ContextMenuController._match_case("Thiss", "this") == "This"


def test_match_case_preserves_all_caps_word():
    from app.controllers.context_menu_controller import ContextMenuController
    assert ContextMenuController._match_case("THISS", "this") == "THIS"


def test_match_case_preserves_lowercase_word():
    from app.controllers.context_menu_controller import ContextMenuController
    assert ContextMenuController._match_case("teh", "the") == "the"


def test_highlighter_flags_misspelled_words(qtbot, spell_service):
    doc_tab = DocumentTab("Test")
    highlighter = SpellCheckHighlighter(doc_tab.text_edit.document(), spell_service)

    doc_tab.text_edit.setPlainText("This is a tesst of the spel chekcer.")

    block = doc_tab.text_edit.document().firstBlock()
    flagged_words = {
        block.text()[fmt.start:fmt.start + fmt.length]
        for fmt in block.layout().formats()
    }
    assert flagged_words == {"tesst", "spel", "chekcer"}


def test_highlighter_disabled_clears_flags(qtbot, spell_service):
    doc_tab = DocumentTab("Test")
    highlighter = SpellCheckHighlighter(doc_tab.text_edit.document(), spell_service)

    doc_tab.text_edit.setPlainText("This has a tesst in it.")
    highlighter.set_enabled(False)

    block = doc_tab.text_edit.document().firstBlock()
    formats = block.layout().formats()
    assert len(formats) == 0
