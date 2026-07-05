# ============================================================================
# FormattingController Tests
# covers character formatting, alignment, indentation, line spacing, text
# styles, lists, tables, links, and special inserts.
# Dialog-driven methods (color pickers, insert_table, insert_image,
# show_table_properties, add_link) are exercised by monkeypatching the Qt
# dialog classes so no real modal is shown.
# ============================================================================

import pytest
from PyQt6.QtWidgets import QApplication, QColorDialog, QDialog, QInputDialog
from PyQt6.QtGui import QFont, QTextListFormat, QTextCharFormat
from PyQt6.QtCore import Qt

from app.controllers.formatting_controller import FormattingController
from models.document_tab import DocumentTab


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def tab(qapp):
    return DocumentTab("Test")


@pytest.fixture
def controller(tab):
    return FormattingController(
        get_current_tab=lambda: tab,
        get_dark_theme=lambda: True,
        parent_widget=None,
    )


@pytest.fixture
def empty_controller():
    """A controller whose get_current_tab returns None (no open document)."""
    return FormattingController(
        get_current_tab=lambda: None,
        get_dark_theme=lambda: True,
        parent_widget=None,
    )


# ------------------------------------------------------------------
# No-current-tab guards: every method should simply no-op, never raise
# ------------------------------------------------------------------

@pytest.mark.parametrize("method_name, args", [
    ("toggle_bold", ()),
    ("toggle_italic", ()),
    ("toggle_underline", ()),
    ("toggle_strikethrough", ()),
    ("apply_superscript", ()),
    ("apply_subscript", ()),
    ("clear_formatting", ()),
    ("change_font_size", ("12",)),
    ("set_alignment", (Qt.AlignmentFlag.AlignLeft,)),
    ("increase_indent", ()),
    ("decrease_indent", ()),
    ("set_line_spacing", (1.5,)),
    ("apply_text_style", ("Title",)),
    ("toggle_bullet_list", ()),
    ("toggle_numbered_list", ()),
    ("insert_horizontal_line", ()),
    ("insert_code_block", ()),
])
def test_methods_noop_without_current_tab(empty_controller, method_name, args):
    """Every formatting op should tolerate there being no open document tab."""
    method = getattr(empty_controller, method_name)
    method(*args)  # should not raise


def test_change_font_family_noop_without_current_tab(empty_controller):
    empty_controller.change_font_family(QFont("Arial"))


# ------------------------------------------------------------------
# Basic character formatting toggles
# ------------------------------------------------------------------

def test_toggle_bold(controller, tab):
    assert tab.text_edit.currentCharFormat().fontWeight() != QFont.Weight.Bold
    controller.toggle_bold()
    assert tab.text_edit.currentCharFormat().fontWeight() == QFont.Weight.Bold
    controller.toggle_bold()
    assert tab.text_edit.currentCharFormat().fontWeight() == QFont.Weight.Normal


def test_toggle_italic(controller, tab):
    assert tab.text_edit.currentCharFormat().fontItalic() is False
    controller.toggle_italic()
    assert tab.text_edit.currentCharFormat().fontItalic() is True
    controller.toggle_italic()
    assert tab.text_edit.currentCharFormat().fontItalic() is False


def test_toggle_underline(controller, tab):
    controller.toggle_underline()
    assert tab.text_edit.currentCharFormat().fontUnderline() is True
    controller.toggle_underline()
    assert tab.text_edit.currentCharFormat().fontUnderline() is False


def test_toggle_strikethrough(controller, tab):
    controller.toggle_strikethrough()
    assert tab.text_edit.currentCharFormat().fontStrikeOut() is True
    controller.toggle_strikethrough()
    assert tab.text_edit.currentCharFormat().fontStrikeOut() is False


def test_apply_superscript_toggles_and_is_exclusive_with_subscript(controller, tab):
    controller.apply_superscript()
    fmt = tab.text_edit.currentCharFormat()
    assert fmt.verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignSuperScript
    controller.apply_superscript()
    fmt = tab.text_edit.currentCharFormat()
    assert fmt.verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignNormal


def test_apply_subscript_toggles(controller, tab):
    controller.apply_subscript()
    fmt = tab.text_edit.currentCharFormat()
    assert fmt.verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignSubScript
    controller.apply_subscript()
    fmt = tab.text_edit.currentCharFormat()
    assert fmt.verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignNormal


def test_clear_formatting_resets_current_char_format(controller, tab):
    controller.toggle_bold()
    controller.toggle_italic()
    assert tab.text_edit.currentCharFormat().fontWeight() == QFont.Weight.Bold
    controller.clear_formatting()
    fmt = tab.text_edit.currentCharFormat()
    assert fmt.fontWeight() != QFont.Weight.Bold
    assert fmt.fontItalic() is False


def test_clear_formatting_with_selection(controller, tab):
    tab.text_edit.setPlainText("Hello World")
    cursor = tab.text_edit.textCursor()
    cursor.select(cursor.SelectionType.Document)
    tab.text_edit.setTextCursor(cursor)
    controller.toggle_bold()
    controller.clear_formatting()
    cursor = tab.text_edit.textCursor()
    assert cursor.charFormat().fontWeight() != QFont.Weight.Bold


# ------------------------------------------------------------------
# Font family / size
# ------------------------------------------------------------------

def test_change_font_family(controller, tab):
    controller.change_font_family(QFont("Courier New"))
    assert tab.text_edit.currentCharFormat().fontFamily() == "Courier New"


def test_change_font_size_valid(controller, tab):
    controller.change_font_size("18")
    assert tab.text_edit.currentCharFormat().fontPointSize() == 18


def test_change_font_size_invalid_is_ignored(controller, tab):
    original = tab.text_edit.currentCharFormat().fontPointSize()
    controller.change_font_size("not-a-number")
    assert tab.text_edit.currentCharFormat().fontPointSize() == original


def test_change_font_size_empty_string_is_ignored(controller, tab):
    original = tab.text_edit.currentCharFormat().fontPointSize()
    controller.change_font_size("")
    assert tab.text_edit.currentCharFormat().fontPointSize() == original


# ------------------------------------------------------------------
# Alignment
# ------------------------------------------------------------------

@pytest.mark.parametrize("alignment", [
    Qt.AlignmentFlag.AlignLeft,
    Qt.AlignmentFlag.AlignHCenter,
    Qt.AlignmentFlag.AlignRight,
    Qt.AlignmentFlag.AlignJustify,
])
def test_set_alignment(controller, tab, alignment):
    controller.set_alignment(alignment)
    assert tab.text_edit.alignment() == alignment


# ------------------------------------------------------------------
# Indentation
# ------------------------------------------------------------------

def test_increase_indent(controller, tab):
    cursor = tab.text_edit.textCursor()
    assert cursor.blockFormat().indent() == 0
    controller.increase_indent()
    cursor = tab.text_edit.textCursor()
    assert cursor.blockFormat().indent() == 1


def test_decrease_indent_does_not_go_below_zero(controller, tab):
    controller.decrease_indent()
    cursor = tab.text_edit.textCursor()
    assert cursor.blockFormat().indent() == 0


def test_increase_then_decrease_indent(controller, tab):
    controller.increase_indent()
    controller.increase_indent()
    controller.decrease_indent()
    cursor = tab.text_edit.textCursor()
    assert cursor.blockFormat().indent() == 1


# ------------------------------------------------------------------
# Line spacing
# ------------------------------------------------------------------

def test_set_line_spacing_no_selection(controller, tab):
    controller.set_line_spacing(2.0)
    cursor = tab.text_edit.textCursor()
    assert cursor.blockFormat().lineHeight() == 200


def test_set_line_spacing_with_selection(controller, tab):
    tab.text_edit.setPlainText("line one\nline two\nline three")
    cursor = tab.text_edit.textCursor()
    cursor.select(cursor.SelectionType.Document)
    tab.text_edit.setTextCursor(cursor)

    controller.set_line_spacing(1.5)

    block = tab.text_edit.document().firstBlock()
    while block.isValid():
        assert block.blockFormat().lineHeight() == 150
        block = block.next()


# ------------------------------------------------------------------
# Text styles
# ------------------------------------------------------------------

def test_apply_text_style_unknown_style_is_noop(controller, tab):
    original = tab.text_edit.currentCharFormat().fontPointSize()
    controller.apply_text_style("Not A Real Style")
    assert tab.text_edit.currentCharFormat().fontPointSize() == original


@pytest.mark.parametrize("style_name, expected_size, expected_bold", [
    ("Normal", 12, False),
    ("Title", 28, True),
    ("Subtitle", 18, True),
    ("Heading 1", 24, True),
    ("Heading 6", 12, True),
])
def test_apply_text_style_sets_size_and_weight(controller, tab, style_name, expected_size, expected_bold):
    controller.apply_text_style(style_name)
    fmt = tab.text_edit.currentCharFormat()
    assert fmt.fontPointSize() == expected_size
    assert (fmt.fontWeight() == QFont.Weight.Bold) is expected_bold


def test_apply_text_style_code_block_sets_family_and_colors(controller, tab):
    controller.apply_text_style("Code Block")
    fmt = tab.text_edit.currentCharFormat()
    assert fmt.fontFamily() == "Courier New"
    cursor = tab.text_edit.textCursor()
    assert cursor.blockFormat().background().color().name() == "#2b2b2b"


def test_apply_text_style_heading_adds_margins(controller, tab):
    controller.apply_text_style("Heading 1")
    cursor = tab.text_edit.textCursor()
    block_fmt = cursor.blockFormat()
    assert block_fmt.topMargin() == 12
    assert block_fmt.bottomMargin() == 12


def test_apply_text_style_normal_after_heading_clears_margins(controller, tab):
    controller.apply_text_style("Heading 1")
    controller.apply_text_style("Normal")
    cursor = tab.text_edit.textCursor()
    block_fmt = cursor.blockFormat()
    assert block_fmt.topMargin() == 0
    assert block_fmt.bottomMargin() == 0


# ------------------------------------------------------------------
# Lists
# ------------------------------------------------------------------

def test_toggle_bullet_list_creates_list(controller, tab):
    controller.toggle_bullet_list()
    cursor = tab.text_edit.textCursor()
    current_list = cursor.currentList()
    assert current_list is not None
    assert current_list.format().style() == QTextListFormat.Style.ListDisc


def test_toggle_bullet_list_twice_removes_list(controller, tab):
    controller.toggle_bullet_list()
    controller.toggle_bullet_list()
    cursor = tab.text_edit.textCursor()
    assert cursor.currentList() is None


def test_toggle_numbered_list_creates_list(controller, tab):
    controller.toggle_numbered_list()
    cursor = tab.text_edit.textCursor()
    current_list = cursor.currentList()
    assert current_list is not None
    assert current_list.format().style() == QTextListFormat.Style.ListDecimal


def test_toggle_numbered_list_twice_removes_list(controller, tab):
    controller.toggle_numbered_list()
    controller.toggle_numbered_list()
    cursor = tab.text_edit.textCursor()
    assert cursor.currentList() is None


def test_switching_from_bullet_to_numbered_list(controller, tab):
    controller.toggle_bullet_list()
    controller.toggle_numbered_list()
    cursor = tab.text_edit.textCursor()
    current_list = cursor.currentList()
    assert current_list is not None
    assert current_list.format().style() == QTextListFormat.Style.ListDecimal


# ------------------------------------------------------------------
# Special inserts
# ------------------------------------------------------------------

def test_insert_horizontal_line(controller, tab):
    controller.insert_horizontal_line()
    assert "─" * 60 in tab.text_edit.toPlainText()


def test_insert_code_block_without_selection(controller, tab):
    controller.insert_code_block()
    assert "# Enter your code here" in tab.text_edit.toPlainText()


def test_insert_code_block_with_selection_preserves_text(controller, tab):
    tab.text_edit.setPlainText("print('hi')")
    cursor = tab.text_edit.textCursor()
    cursor.select(cursor.SelectionType.Document)
    tab.text_edit.setTextCursor(cursor)

    controller.insert_code_block()

    assert "print('hi')" in tab.text_edit.toPlainText()


# ------------------------------------------------------------------
# Tables
# ------------------------------------------------------------------

def _find_table(tab):
    """insert_table() doesn't re-sync the widget's own QTextCursor after
    inserting, so look the table up directly on the document instead of via
    tab.text_edit.textCursor().currentTable()."""
    from PyQt6.QtGui import QTextTable
    frame = tab.text_edit.document().rootFrame()
    for child in frame.childFrames():
        if isinstance(child, QTextTable):
            return child
    return None


def test_insert_table_via_accepted_dialog(controller, tab, monkeypatch):
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    controller.insert_table()
    table = _find_table(tab)
    assert table is not None
    assert table.rows() == 3
    assert table.columns() == 3


def test_insert_table_via_rejected_dialog_inserts_nothing(controller, tab, monkeypatch):
    monkeypatch.setattr(QDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    controller.insert_table()
    assert _find_table(tab) is None


def test_show_table_properties_without_table_shows_message(controller, tab, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    called = {}

    def fake_information(*args, **kwargs):
        called["shown"] = True

    monkeypatch.setattr(QMessageBox, "information", staticmethod(fake_information))
    controller.show_table_properties()
    assert called.get("shown") is True


def test_show_table_properties_with_table_opens_dialog(controller, tab, monkeypatch):
    # Build a table directly on the document (bypassing the insert_table
    # dialog) and position the real widget cursor inside it, since
    # show_table_properties reads cursor.currentTable() from the live cursor.
    from PyQt6.QtGui import QTextTableFormat
    cursor = tab.text_edit.textCursor()
    cursor.insertTable(2, 2, QTextTableFormat())
    tab.text_edit.setTextCursor(cursor)

    opened = {}
    from app.controllers import formatting_controller as fc_module

    class FakeDialog:
        def __init__(self, table, parent):
            opened["table"] = table

        def exec(self):
            return None

    monkeypatch.setattr(fc_module, "TablePropertiesDialog", FakeDialog)
    controller.show_table_properties()
    assert "table" in opened


# ------------------------------------------------------------------
# Hyperlinks
# ------------------------------------------------------------------

def test_add_link_with_selection_and_url(controller, tab, monkeypatch):
    tab.text_edit.setPlainText("click here")
    cursor = tab.text_edit.textCursor()
    cursor.select(cursor.SelectionType.Document)
    tab.text_edit.setTextCursor(cursor)

    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: ("https://example.com", True)))
    controller.add_link()

    cursor = tab.text_edit.textCursor()
    cursor.select(cursor.SelectionType.Document)
    assert cursor.charFormat().anchorHref() == "https://example.com"


def test_add_link_cancelled_dialog_does_nothing(controller, tab, monkeypatch):
    tab.text_edit.setPlainText("click here")
    cursor = tab.text_edit.textCursor()
    cursor.select(cursor.SelectionType.Document)
    tab.text_edit.setTextCursor(cursor)

    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: ("", False)))
    controller.add_link()

    cursor = tab.text_edit.textCursor()
    cursor.select(cursor.SelectionType.Document)
    assert cursor.charFormat().anchorHref() == ""


def test_add_link_without_selection_inserts_link_text(controller, tab, monkeypatch):
    responses = iter([("https://example.com", True), ("Example", True)])
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(lambda *a, **k: next(responses)))
    controller.add_link()
    assert "Example" in tab.text_edit.toPlainText()


# ------------------------------------------------------------------
# Colour pickers
# ------------------------------------------------------------------

def test_change_text_color_updates_state_and_calls_callback(controller, tab, monkeypatch):
    from PyQt6.QtGui import QColor
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor("#123456")))
    callback_called = {}
    controller.change_text_color(lambda: callback_called.setdefault("called", True))
    assert controller.current_text_color.name() == "#123456"
    assert callback_called.get("called") is True


def test_change_text_color_invalid_color_is_ignored(controller, tab, monkeypatch):
    from PyQt6.QtGui import QColor
    original = controller.current_text_color
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor()))  # invalid
    controller.change_text_color(lambda: None)
    assert controller.current_text_color == original


def test_change_background_color_updates_state(controller, tab, monkeypatch):
    from PyQt6.QtGui import QColor
    monkeypatch.setattr(QColorDialog, "getColor", staticmethod(lambda *a, **k: QColor("#ABCDEF")))
    controller.change_background_color(lambda: None)
    assert controller.current_bg_color.name() == "#abcdef"
