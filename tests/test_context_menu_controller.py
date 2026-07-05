# ============================================================================
# ContextMenuController Tests
# covers building the context menu (table sub-menu, alignment sub-menu,
# spelling suggestions, image resize entry) and the action wiring behind it.
# QMenu.exec / QDialog.exec are monkeypatched so no real modal blocks the
# test run; the fake exec captures the menu/dialog instance instead so we
# can inspect its actions directly.
# ============================================================================

import pytest
from PyQt6.QtWidgets import QApplication, QTextEdit, QMenu, QDialog, QMessageBox
from PyQt6.QtGui import QTextTableFormat, QImage, QTextDocument, QTextCursor
from PyQt6.QtCore import Qt, QPoint, QUrl

from app.controllers.context_menu_controller import ContextMenuController


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class FakeSpellService:
    def __init__(self, misspelled=None, suggestions=None):
        self._misspelled = misspelled or set()
        self._suggestions = suggestions or {}
        self.added_words = []

    def is_correct(self, word):
        return word.lower() not in self._misspelled

    def suggestions(self, word):
        return self._suggestions.get(word.lower(), [])

    def add_word(self, word):
        self.added_words.append(word)


@pytest.fixture
def text_edit(qapp):
    te = QTextEdit()
    # Needs real geometry so cursorForPosition()/cursorRect() resolve
    # correctly (e.g. to find the table cell under a click position).
    te.resize(400, 300)
    te.show()
    qapp.processEvents()
    return te


@pytest.fixture
def captured_menu(monkeypatch):
    """Patch QMenu.exec to capture the menu instance instead of blocking."""
    box = {}

    def fake_exec(self, *args, **kwargs):
        box["menu"] = self
        return None

    monkeypatch.setattr(QMenu, "exec", fake_exec)
    return box


def _action_texts(menu):
    return [a.text() for a in menu.actions()]


# ------------------------------------------------------------------
# Basic menu construction (no table, no spellcheck, no image)
# ------------------------------------------------------------------

def test_show_builds_menu_with_alignment_submenu(text_edit, captured_menu):
    controller = ContextMenuController(lambda flag: None, None)
    text_edit.setPlainText("hello world")
    controller.show(QPoint(0, 0), text_edit)

    menu = captured_menu["menu"]
    submenu_titles = [a.menu().title() for a in menu.actions() if a.menu()]
    assert "Alignment" in submenu_titles
    assert "Table" not in submenu_titles


def test_alignment_submenu_actions_delegate_to_set_alignment(text_edit, captured_menu):
    seen = []
    controller = ContextMenuController(lambda flag: seen.append(flag), None)
    controller.show(QPoint(0, 0), text_edit)

    menu = captured_menu["menu"]
    align_menu = next(a.menu() for a in menu.actions() if a.menu() and a.menu().title() == "Alignment")
    labels = {a.text(): a for a in align_menu.actions()}
    assert set(labels) == {"Align Left", "Center", "Align Right", "Justify"}

    labels["Align Right"].trigger()
    assert seen == [Qt.AlignmentFlag.AlignRight]


def test_show_without_spell_service_adds_no_suggestions(text_edit, captured_menu):
    controller = ContextMenuController(lambda flag: None, None, spell_service=None)
    text_edit.setPlainText("helllo")
    controller.show(QPoint(0, 0), text_edit)
    menu = captured_menu["menu"]
    assert not any("Dictionary" in t for t in _action_texts(menu))


# ------------------------------------------------------------------
# Table sub-menu
# ------------------------------------------------------------------

def test_show_with_table_adds_table_submenu(text_edit, captured_menu):
    cursor = text_edit.textCursor()
    table = cursor.insertTable(3, 3, QTextTableFormat())
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    menu = captured_menu["menu"]
    table_menu = next((a.menu() for a in menu.actions() if a.menu() and a.menu().title() == "Table"), None)
    assert table_menu is not None
    action_names = _action_texts(table_menu)
    assert "Insert Row Above" in action_names
    assert "Insert Row Below" in action_names
    assert "Insert Column Left" in action_names
    assert "Insert Column Right" in action_names
    assert "Delete Row" in action_names
    assert "Delete Column" in action_names
    assert "Table Properties…" in action_names


def test_insert_row_above_action_grows_table(text_edit, captured_menu):
    cursor = text_edit.textCursor()
    table = cursor.insertTable(2, 2, QTextTableFormat())
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    menu = captured_menu["menu"]
    table_menu = next(a.menu() for a in menu.actions() if a.menu() and a.menu().title() == "Table")
    actions = {a.text(): a for a in table_menu.actions()}
    actions["Insert Row Above"].trigger()
    assert table.rows() == 3


def test_delete_row_action_shrinks_table(text_edit, captured_menu):
    cursor = text_edit.textCursor()
    table = cursor.insertTable(3, 2, QTextTableFormat())
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    menu = captured_menu["menu"]
    table_menu = next(a.menu() for a in menu.actions() if a.menu() and a.menu().title() == "Table")
    actions = {a.text(): a for a in table_menu.actions()}
    actions["Delete Row"].trigger()
    assert table.rows() == 2


def test_delete_row_action_refuses_to_remove_last_row(text_edit, captured_menu):
    cursor = text_edit.textCursor()
    table = cursor.insertTable(1, 2, QTextTableFormat())
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    menu = captured_menu["menu"]
    table_menu = next(a.menu() for a in menu.actions() if a.menu() and a.menu().title() == "Table")
    actions = {a.text(): a for a in table_menu.actions()}
    actions["Delete Row"].trigger()
    assert table.rows() == 1  # guarded: never delete the only row


def test_delete_column_action_refuses_to_remove_last_column(text_edit, captured_menu):
    cursor = text_edit.textCursor()
    table = cursor.insertTable(2, 1, QTextTableFormat())
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    menu = captured_menu["menu"]
    table_menu = next(a.menu() for a in menu.actions() if a.menu() and a.menu().title() == "Table")
    actions = {a.text(): a for a in table_menu.actions()}
    actions["Delete Column"].trigger()
    assert table.columns() == 1


def test_insert_column_left_action_grows_table(text_edit, captured_menu):
    cursor = text_edit.textCursor()
    table = cursor.insertTable(2, 2, QTextTableFormat())
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    menu = captured_menu["menu"]
    table_menu = next(a.menu() for a in menu.actions() if a.menu() and a.menu().title() == "Table")
    actions = {a.text(): a for a in table_menu.actions()}
    actions["Insert Column Left"].trigger()
    assert table.columns() == 3


def test_table_properties_action_opens_dialog(text_edit, captured_menu, monkeypatch):
    cursor = text_edit.textCursor()
    table = cursor.insertTable(2, 2, QTextTableFormat())
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    opened = {}
    from app.controllers import context_menu_controller as cmc_module

    class FakeDialog:
        def __init__(self, table_arg, parent):
            opened["table"] = table_arg

        def exec(self):
            return None

    monkeypatch.setattr(cmc_module, "TablePropertiesDialog", FakeDialog)

    menu = captured_menu["menu"]
    table_menu = next(a.menu() for a in menu.actions() if a.menu() and a.menu().title() == "Table")
    actions = {a.text(): a for a in table_menu.actions()}
    actions["Table Properties…"].trigger()
    assert opened["table"] == table


# ------------------------------------------------------------------
# Spelling suggestions
# ------------------------------------------------------------------

def test_show_adds_suggestions_for_misspelled_word(text_edit, captured_menu):
    spell = FakeSpellService(misspelled={"helllo"}, suggestions={"helllo": ["hello", "hell"]})
    controller = ContextMenuController(lambda flag: None, None, spell_service=spell)
    text_edit.setPlainText("helllo there")
    cursor = text_edit.textCursor()
    cursor.setPosition(2)
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller.show(text_edit.cursorRect(cursor).center(), text_edit)
    menu = captured_menu["menu"]
    texts = _action_texts(menu)
    assert "hello" in texts
    assert "hell" in texts
    assert 'Add "helllo" to Dictionary' in texts


def test_suggestion_action_replaces_word_in_document(text_edit, captured_menu):
    spell = FakeSpellService(misspelled={"helllo"}, suggestions={"helllo": ["hello"]})
    controller = ContextMenuController(lambda flag: None, None, spell_service=spell)
    text_edit.setPlainText("helllo there")
    cursor = text_edit.textCursor()
    cursor.setPosition(2)
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller.show(text_edit.cursorRect(cursor).center(), text_edit)
    menu = captured_menu["menu"]
    action = next(a for a in menu.actions() if a.text() == "hello")
    action.trigger()

    assert "hello there" in text_edit.toPlainText()
    assert "helllo" not in text_edit.toPlainText()


def test_add_to_dictionary_action_calls_spell_service(text_edit, captured_menu):
    spell = FakeSpellService(misspelled={"helllo"}, suggestions={"helllo": ["hello"]})
    controller = ContextMenuController(lambda flag: None, None, spell_service=spell)
    text_edit.setPlainText("helllo there")
    cursor = text_edit.textCursor()
    cursor.setPosition(2)
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller.show(text_edit.cursorRect(cursor).center(), text_edit)
    menu = captured_menu["menu"]
    action = next(a for a in menu.actions() if a.text() == 'Add "helllo" to Dictionary')
    action.trigger()
    assert spell.added_words == ["helllo"]


def test_show_with_correctly_spelled_word_adds_no_suggestions(text_edit, captured_menu):
    spell = FakeSpellService(misspelled={"helllo"})
    controller = ContextMenuController(lambda flag: None, None, spell_service=spell)
    text_edit.setPlainText("hello there")
    cursor = text_edit.textCursor()
    cursor.setPosition(2)
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller.show(text_edit.cursorRect(cursor).center(), text_edit)
    menu = captured_menu["menu"]
    assert not any("Dictionary" in t for t in _action_texts(menu))


def test_show_with_no_suggestions_available_shows_disabled_entry(text_edit, captured_menu):
    spell = FakeSpellService(misspelled={"zzzzz"}, suggestions={})
    controller = ContextMenuController(lambda flag: None, None, spell_service=spell)
    text_edit.setPlainText("zzzzz there")
    cursor = text_edit.textCursor()
    cursor.setPosition(2)
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller.show(text_edit.cursorRect(cursor).center(), text_edit)
    menu = captured_menu["menu"]
    no_sugg = next(a for a in menu.actions() if a.text() == "No suggestions")
    assert no_sugg.isEnabled() is False


# ------------------------------------------------------------------
# _match_case (static helper) — already covered in test_spellcheck.py,
# included here too for completeness alongside its sibling behaviors.
# ------------------------------------------------------------------

def test_match_case_mixed_case_uses_first_letter_rule():
    assert ContextMenuController._match_case("Foo", "bar") == "Bar"


# ------------------------------------------------------------------
# Image resize entry
# ------------------------------------------------------------------

def test_show_with_image_under_cursor_adds_resize_action(text_edit, captured_menu):
    image = QImage(10, 10, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.red)
    text_edit.document().addResource(
        QTextDocument.ResourceType.ImageResource, QUrl("pic.png"), image
    )
    cursor = text_edit.textCursor()
    cursor.insertImage("pic.png")
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    menu = captured_menu["menu"]
    assert "Resize Image…" in _action_texts(menu)


def test_show_without_image_has_no_resize_action(text_edit, captured_menu):
    text_edit.setPlainText("just text")
    controller = ContextMenuController(lambda flag: None, None)
    controller.show(QPoint(0, 0), text_edit)
    menu = captured_menu["menu"]
    assert "Resize Image…" not in _action_texts(menu)


def test_resize_image_action_opens_resize_dialog(text_edit, captured_menu, monkeypatch):
    image = QImage(20, 10, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.blue)
    text_edit.document().addResource(
        QTextDocument.ResourceType.ImageResource, QUrl("pic2.png"), image
    )
    cursor = text_edit.textCursor()
    cursor.insertImage("pic2.png")
    text_edit.setTextCursor(cursor)
    QApplication.processEvents()

    controller = ContextMenuController(lambda flag: None, None)
    controller.show(text_edit.cursorRect(cursor).center(), text_edit)

    dialog_opened = {}
    monkeypatch.setattr(
        QDialog, "exec",
        lambda self: (dialog_opened.setdefault("opened", True), QDialog.DialogCode.Rejected)[1]
    )

    menu = captured_menu["menu"]
    resize_action = next(a for a in menu.actions() if a.text() == "Resize Image…")
    resize_action.trigger()
    assert dialog_opened.get("opened") is True


def test_resize_image_with_no_image_shows_message(text_edit, monkeypatch):
    """_resize_image is only wired up when an image is present, but calling
    it directly with no image under the cursor should show an info box
    rather than raise."""
    text_edit.setPlainText("no image here")
    controller = ContextMenuController(lambda flag: None, None)

    shown = {}
    monkeypatch.setattr(
        QMessageBox, "information",
        staticmethod(lambda *a, **k: shown.setdefault("shown", True))
    )
    controller._resize_image(text_edit)
    assert shown.get("shown") is True
