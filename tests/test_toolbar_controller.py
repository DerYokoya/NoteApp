# ============================================================================
# ToolbarController Tests
# covers toolbar construction, button-to-formatting-action wiring, theming,
# and the color-swatch refresh helpers.
# A lightweight fake FormattingController stands in for the real one so we
# can assert on which method got called, with what argument, without
# depending on FormattingController's own behavior.
# ============================================================================

import pytest
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

from app.controllers.toolbar_controller import ToolbarController


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class FakeFormattingController:
    """Records every call made to it, standing in for FormattingController."""

    def __init__(self, dark=True):
        self.calls = []
        self._dark = dark
        self._current_text_color = QColor("#FFFFFF")
        self._current_bg_color = QColor("#FFFF00")

    def _get_dark(self):
        return self._dark

    @property
    def current_text_color(self):
        return self._current_text_color

    @property
    def current_bg_color(self):
        return self._current_bg_color

    def __getattr__(self, name):
        # Any formatting method (toggle_bold, insert_table, etc.) is
        # captured generically and recorded when invoked.
        def recorder(*args, **kwargs):
            self.calls.append((name, args, kwargs))
        return recorder


@pytest.fixture
def fmt():
    return FakeFormattingController()


@pytest.fixture
def parent_window(qapp):
    return QWidget()


@pytest.fixture
def controller(fmt, parent_window):
    return ToolbarController(fmt, parent_window)


@pytest.fixture
def built(controller):
    widget = controller.build("#555555")
    return controller, widget


# ------------------------------------------------------------------
# Build
# ------------------------------------------------------------------

def test_build_returns_widget_with_object_name(built):
    controller, widget = built
    assert widget is not None
    assert widget.objectName() == "FormatToolbar"
    assert controller.toolbar_widget is widget


def test_build_creates_expected_controls(built):
    controller, _ = built
    for attr in (
        "font_combo", "size_combo", "style_combo", "line_spacing_combo",
        "bold_btn", "italic_btn", "underline_btn", "strike_btn",
        "superscript_btn", "subscript_btn", "code_block_btn",
        "text_color_btn", "bg_color_btn", "link_btn", "clear_btn",
        "align_left_btn", "align_center_btn", "align_right_btn", "align_just_btn",
        "bullet_list_btn", "numbered_list_btn", "indent_btn", "outdent_btn",
        "hr_btn", "image_btn", "table_btn", "table_props_btn",
    ):
        assert hasattr(controller, attr), f"missing control: {attr}"


def test_size_combo_has_expected_options(built):
    controller, _ = built
    items = [controller.size_combo.itemText(i) for i in range(controller.size_combo.count())]
    assert items == ['8','9','10','11','12','14','16','18','20','24','28','36','48','72']
    assert controller.size_combo.currentText() == '12'


def test_style_combo_has_expected_options(built):
    controller, _ = built
    items = [controller.style_combo.itemText(i) for i in range(controller.style_combo.count())]
    assert items == [
        'Normal', 'Title', 'Subtitle',
        'Heading 1', 'Heading 2', 'Heading 3',
        'Heading 4', 'Heading 5', 'Heading 6',
        'Code Block',
    ]


def test_line_spacing_combo_has_expected_options(built):
    controller, _ = built
    items = [controller.line_spacing_combo.itemText(i) for i in range(controller.line_spacing_combo.count())]
    assert items == ['Single', '1.5x', 'Double']


# ------------------------------------------------------------------
# Button -> FormattingController wiring
# ------------------------------------------------------------------

def test_bold_button_click_calls_toggle_bold(built, fmt):
    controller, _ = built
    controller.bold_btn.click()
    assert any(c[0] == "toggle_bold" for c in fmt.calls)


def test_italic_button_click_calls_toggle_italic(built, fmt):
    controller, _ = built
    controller.italic_btn.click()
    assert any(c[0] == "toggle_italic" for c in fmt.calls)


def test_underline_button_click_calls_toggle_underline(built, fmt):
    controller, _ = built
    controller.underline_btn.click()
    assert any(c[0] == "toggle_underline" for c in fmt.calls)


def test_strike_button_click_calls_toggle_strikethrough(built, fmt):
    controller, _ = built
    controller.strike_btn.click()
    assert any(c[0] == "toggle_strikethrough" for c in fmt.calls)


def test_superscript_button_click(built, fmt):
    controller, _ = built
    controller.superscript_btn.click()
    assert any(c[0] == "apply_superscript" for c in fmt.calls)


def test_subscript_button_click(built, fmt):
    controller, _ = built
    controller.subscript_btn.click()
    assert any(c[0] == "apply_subscript" for c in fmt.calls)


def test_code_block_button_click(built, fmt):
    controller, _ = built
    controller.code_block_btn.click()
    assert any(c[0] == "insert_code_block" for c in fmt.calls)


def test_link_button_click(built, fmt):
    controller, _ = built
    controller.link_btn.click()
    assert any(c[0] == "add_link" for c in fmt.calls)


def test_clear_button_click(built, fmt):
    controller, _ = built
    controller.clear_btn.click()
    assert any(c[0] == "clear_formatting" for c in fmt.calls)


def test_align_buttons_call_set_alignment_with_expected_flag(built, fmt):
    controller, _ = built
    controller.align_left_btn.click()
    controller.align_center_btn.click()
    controller.align_right_btn.click()
    controller.align_just_btn.click()

    alignments_called = [call[1][0] for call in fmt.calls if call[0] == "set_alignment"]
    assert alignments_called == [
        Qt.AlignmentFlag.AlignLeft,
        Qt.AlignmentFlag.AlignHCenter,
        Qt.AlignmentFlag.AlignRight,
        Qt.AlignmentFlag.AlignJustify,
    ]


def test_bullet_list_button_click(built, fmt):
    controller, _ = built
    controller.bullet_list_btn.click()
    assert any(c[0] == "toggle_bullet_list" for c in fmt.calls)


def test_numbered_list_button_click(built, fmt):
    controller, _ = built
    controller.numbered_list_btn.click()
    assert any(c[0] == "toggle_numbered_list" for c in fmt.calls)


def test_indent_buttons_click(built, fmt):
    controller, _ = built
    controller.indent_btn.click()
    controller.outdent_btn.click()
    assert any(c[0] == "increase_indent" for c in fmt.calls)
    assert any(c[0] == "decrease_indent" for c in fmt.calls)


def test_hr_button_click(built, fmt):
    controller, _ = built
    controller.hr_btn.click()
    assert any(c[0] == "insert_horizontal_line" for c in fmt.calls)


def test_image_button_click(built, fmt):
    controller, _ = built
    controller.image_btn.click()
    assert any(c[0] == "insert_image" for c in fmt.calls)


def test_table_buttons_click(built, fmt):
    controller, _ = built
    controller.table_btn.click()
    controller.table_props_btn.click()
    assert any(c[0] == "insert_table" for c in fmt.calls)
    assert any(c[0] == "show_table_properties" for c in fmt.calls)


def test_font_family_change_calls_change_font_family(built, fmt):
    controller, _ = built
    controller.font_combo.currentFontChanged.emit(QFont("Georgia"))
    matching = [c for c in fmt.calls if c[0] == "change_font_family"]
    assert len(matching) == 1
    assert matching[0][1][0].family() == "Georgia"


def test_font_size_change_calls_change_font_size(built, fmt):
    controller, _ = built
    controller.size_combo.setCurrentText("24")
    assert ("change_font_size", ("24",), {}) in fmt.calls


def test_style_combo_change_calls_apply_text_style(built, fmt):
    controller, _ = built
    controller.style_combo.setCurrentText("Heading 2")
    assert ("apply_text_style", ("Heading 2",), {}) in fmt.calls


def test_line_spacing_change_calls_set_line_spacing(built, fmt):
    controller, _ = built
    controller.line_spacing_combo.setCurrentText("Double")
    matching = [c for c in fmt.calls if c[0] == "set_line_spacing"]
    assert matching[-1][1][0] == 2.0


def test_line_spacing_single_maps_to_one(built, fmt):
    controller, _ = built
    controller._on_line_spacing_changed("Single")
    matching = [c for c in fmt.calls if c[0] == "set_line_spacing"]
    assert matching[-1][1][0] == 1.0


def test_line_spacing_unknown_value_is_ignored(built, fmt):
    controller, _ = built
    before = len([c for c in fmt.calls if c[0] == "set_line_spacing"])
    controller._on_line_spacing_changed("Unknown")
    after = len([c for c in fmt.calls if c[0] == "set_line_spacing"])
    assert before == after


def test_text_color_button_click_calls_change_text_color_with_callback(built, fmt):
    controller, _ = built
    controller.text_color_btn.click()
    matching = [c for c in fmt.calls if c[0] == "change_text_color"]
    assert len(matching) == 1
    # the passed callback should be the controller's own refresh method
    assert matching[0][1][0] == controller.refresh_text_color_btn


def test_bg_color_button_click_calls_change_background_color_with_callback(built, fmt):
    controller, _ = built
    controller.bg_color_btn.click()
    matching = [c for c in fmt.calls if c[0] == "change_background_color"]
    assert len(matching) == 1
    assert matching[0][1][0] == controller.refresh_bg_color_btn


# ------------------------------------------------------------------
# Theming
# ------------------------------------------------------------------

def test_apply_theme_dark_sets_toolbar_stylesheet(built):
    controller, widget = built
    controller.apply_theme(True)
    assert "#383838" in widget.styleSheet()


def test_apply_theme_light_sets_toolbar_stylesheet(built):
    controller, widget = built
    controller.apply_theme(False)
    assert "#E8E8E8" in widget.styleSheet()


def test_apply_theme_updates_sep_color(built):
    controller, _ = built
    controller.apply_theme(False)
    assert controller._sep_color == "#BBBBBB"


def test_refresh_text_color_btn_includes_current_color(built, fmt):
    controller, _ = built
    fmt._current_text_color = QColor("#123456")
    controller.refresh_text_color_btn()
    assert "#123456" in controller.text_color_btn.styleSheet()


def test_refresh_bg_color_btn_dark_text_for_light_highlight(built, fmt):
    controller, _ = built
    fmt._current_bg_color = QColor("#FFFFFF")  # very light -> dark text
    controller.refresh_bg_color_btn()
    assert "color: #000000" in controller.bg_color_btn.styleSheet()


def test_refresh_bg_color_btn_light_text_for_dark_highlight(built, fmt):
    controller, _ = built
    fmt._current_bg_color = QColor("#000000")  # very dark -> light text
    controller.refresh_bg_color_btn()
    assert "color: #FFFFFF" in controller.bg_color_btn.styleSheet()


# ------------------------------------------------------------------
# Internal helper
# ------------------------------------------------------------------

def test_btn_helper_sets_tooltip_checkable_and_size(controller):
    btn = controller._btn("X", "tooltip text", checkable=True, width=40)
    assert btn.text() == "X"
    assert btn.toolTip() == "tooltip text"
    assert btn.isCheckable() is True
    assert btn.width() == 40
    assert btn.height() == 28


def test_btn_helper_defaults(controller):
    btn = controller._btn("Y", "tip")
    assert btn.isCheckable() is False
    assert btn.width() == 32
