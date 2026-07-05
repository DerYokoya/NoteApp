# ============================================================================
# MainWindow Tests
# covers tab management, open/save/delete file flows, search & replace,
# recent files, format-button sync, theme/spellcheck toggles, undo/redo,
# and close-with-unsaved-changes handling.
#
# MainWindow talks to real QSettings, real QFileDialog/QMessageBox modals,
# and spawns background QThreads for file loading. To keep tests fast,
# deterministic, and free of any real dialogs or on-disk settings:
#   - SettingsManager is redirected to a per-test temp .ini file.
#   - The status/autosave QTimers are stopped right after construction.
#   - QFileDialog / QMessageBox calls are monkeypatched per-test as needed.
#   - Background file loads are awaited with qtbot.waitUntil.
# ============================================================================

import pytest
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QFont

from app.main_window import MainWindow
from services.settings_manager import SettingsManager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def window(qapp, tmp_path, monkeypatch):
    ini_path = tmp_path / "settings.ini"

    def fake_init(self):
        self.settings = QSettings(str(ini_path), QSettings.Format.IniFormat)

    monkeypatch.setattr(SettingsManager, "__init__", fake_init)

    win = MainWindow()
    # Prevent background timers from firing mid-assertion / after the test.
    win.status_timer.stop()
    win.autosave_timer.stop()
    # isVisible() on child widgets (search bar, etc.) depends on the whole
    # ancestor chain being shown, even under the offscreen platform plugin.
    win.show()
    qapp.processEvents()
    yield win
    win.status_timer.stop()
    win.autosave_timer.stop()


def wait_for_tab_count(qtbot, window, count, timeout=3000):
    qtbot.waitUntil(lambda: len(window.tabs) == count, timeout=timeout)


# ------------------------------------------------------------------
# Initialization
# ------------------------------------------------------------------

def test_starts_with_a_single_untitled_tab(window):
    assert len(window.tabs) == 1
    assert window.tab_widget.count() == 1
    assert window.tabs[0].get_display_name() == "Untitled 1"


def test_window_title_includes_app_name(window):
    assert "Rich Text Notepad" in window.windowTitle()


# ------------------------------------------------------------------
# Tab management
# ------------------------------------------------------------------

def test_new_tab_adds_tab_and_increments_counter(window):
    window.new_tab()
    assert len(window.tabs) == 2
    assert window.tabs[1].get_display_name() == "Untitled 2"
    assert window.tab_widget.currentIndex() == 1


def test_duplicate_tab_copies_content_and_marks_modified(window):
    window.tabs[0].text_edit.setPlainText("original content")
    window.duplicate_tab()

    assert len(window.tabs) == 2
    new_tab = window.tabs[1]
    assert "original content" in new_tab.text_edit.toPlainText()
    assert new_tab.is_modified is True
    assert "(copy)" in new_tab.name


def test_duplicate_tab_noop_without_current_tab(window, monkeypatch):
    monkeypatch.setattr(window, "_get_current_tab", lambda: None)
    window.duplicate_tab()
    assert len(window.tabs) == 1


def test_close_tab_refuses_to_close_last_tab(window):
    window.close_tab(0)
    assert len(window.tabs) == 1


def test_close_tab_removes_unmodified_tab(window):
    window.new_tab()
    assert len(window.tabs) == 2
    window.close_tab(1)
    assert len(window.tabs) == 1


def test_close_tab_with_modified_content_save_choice(window, monkeypatch, tmp_path):
    window.new_tab()
    modified_tab = window.tabs[1]
    modified_tab.text_edit.setPlainText("unsaved work")
    modified_tab.text_edit.document().setModified(True)
    modified_tab.current_file = tmp_path / "existing.txt"
    modified_tab.current_file.write_text("old")

    monkeypatch.setattr(window, "_confirm_close_modified", lambda tab: QMessageBox.StandardButton.Save)
    window.close_tab(1)

    assert len(window.tabs) == 1
    assert modified_tab.current_file.read_text() == "unsaved work"


def test_close_tab_with_modified_content_cancel_choice_keeps_tab(window, monkeypatch):
    window.new_tab()
    modified_tab = window.tabs[1]
    modified_tab.text_edit.setPlainText("unsaved work")
    modified_tab.text_edit.document().setModified(True)

    monkeypatch.setattr(window, "_confirm_close_modified", lambda tab: QMessageBox.StandardButton.Cancel)
    window.close_tab(1)

    assert len(window.tabs) == 2  # tab was NOT closed


def test_close_tab_with_modified_content_discard_choice_closes_without_saving(window, monkeypatch):
    window.new_tab()
    modified_tab = window.tabs[1]
    modified_tab.text_edit.setPlainText("unsaved work")
    modified_tab.text_edit.document().setModified(True)

    monkeypatch.setattr(window, "_confirm_close_modified", lambda tab: QMessageBox.StandardButton.Discard)
    window.close_tab(1)

    assert len(window.tabs) == 1


def test_close_current_tab_closes_active_tab(window):
    window.new_tab()
    window.tab_widget.setCurrentIndex(1)
    window.close_current_tab()
    assert len(window.tabs) == 1


def test_switch_to_tab_by_number(window):
    window.new_tab()
    window.new_tab()
    window._switch_to_tab(1)
    assert window.tab_widget.currentIndex() == 0
    window._switch_to_tab(2)
    assert window.tab_widget.currentIndex() == 1


def test_switch_to_tab_9_goes_to_last_tab(window):
    window.new_tab()
    window.new_tab()
    window._switch_to_tab(9)
    assert window.tab_widget.currentIndex() == window.tab_widget.count() - 1


def test_switch_to_tab_out_of_range_is_ignored(window):
    current = window.tab_widget.currentIndex()
    window._switch_to_tab(5)
    assert window.tab_widget.currentIndex() == current


def test_get_current_tab_returns_none_when_index_out_of_range(window, monkeypatch):
    # QTabWidget.setCurrentIndex(-1) is a no-op while tabs exist, so exercise
    # the guard directly via the index it reads from.
    monkeypatch.setattr(window.tab_widget, "currentIndex", lambda: -1)
    assert window._get_current_tab() is None


def test_update_window_title_reflects_current_tab(window):
    window.tabs[0].current_file = Path("/tmp/myfile.txt")
    window._update_window_title(window.tabs[0])
    assert "myfile.txt" in window.windowTitle()


# ------------------------------------------------------------------
# Open file
# ------------------------------------------------------------------

def test_open_file_loads_content_into_new_tab(window, qtbot, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hello from disk")

    window.open_file(str(f))
    wait_for_tab_count(qtbot, window, 2)

    new_tab = window.tabs[-1]
    assert new_tab.text_edit.toPlainText() == "hello from disk"
    assert new_tab.current_file == f


def test_open_file_already_open_switches_to_existing_tab(window, qtbot, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hello from disk")

    window.open_file(str(f))
    wait_for_tab_count(qtbot, window, 2)

    window.open_file(str(f))
    qapp_instance = QApplication.instance()
    qapp_instance.processEvents()

    assert len(window.tabs) == 2  # no duplicate tab created
    assert window.tab_widget.currentIndex() == 1


def test_open_file_with_no_path_opens_file_dialog(window, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: ("", "")))
    window.open_file()
    assert len(window.tabs) == 1  # cancelled dialog -> no new tab


def test_open_file_failure_shows_error(window, qtbot, monkeypatch, tmp_path):
    shown = {}
    monkeypatch.setattr(
        QMessageBox, "critical",
        staticmethod(lambda *a, **k: shown.setdefault("shown", True))
    )
    missing = tmp_path / "does_not_exist.txt"
    window.open_file(str(missing))
    qtbot.waitUntil(lambda: shown.get("shown") is True, timeout=3000)
    assert len(window.tabs) == 1  # failed load doesn't add a tab


def test_open_file_adds_to_recent_files(window, qtbot, tmp_path):
    f = tmp_path / "recentme.txt"
    f.write_text("content")
    window.open_file(str(f))
    wait_for_tab_count(qtbot, window, 2)
    assert str(f) in window.settings_manager.get_recent_files()


# ------------------------------------------------------------------
# Save / Save As
# ------------------------------------------------------------------

def test_save_as_writes_file_and_updates_tab(window, monkeypatch, tmp_path):
    target = tmp_path / "saved.txt"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(target), "")))

    window.tabs[0].text_edit.setPlainText("save me")
    result = window.save_as()

    assert result is True
    assert target.exists()
    assert target.read_text() == "save me"
    assert window.tabs[0].current_file == target


def test_save_as_cancelled_dialog_returns_false(window, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: ("", "")))
    result = window.save_as()
    assert result is False


def test_save_as_adds_default_extension_when_missing(window, monkeypatch, tmp_path):
    target = tmp_path / "noext"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(target), "")))
    window.save_as()
    assert window.tabs[0].current_file.suffix == ".html"


def test_save_calls_save_document_for_current_tab(window, monkeypatch, tmp_path):
    target = tmp_path / "existing.txt"
    target.write_text("old content")
    window.tabs[0].current_file = target
    window.tabs[0].text_edit.setPlainText("new content")

    window.save()

    assert target.read_text() == "new content"
    assert window.tabs[0].is_modified is False


def test_save_document_without_file_prompts_save_as(window, monkeypatch, tmp_path):
    target = tmp_path / "prompted.txt"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(target), "")))

    window.tabs[0].text_edit.setPlainText("via save()")
    window.save()

    assert target.exists()
    assert target.read_text() == "via save()"


def test_save_document_failure_shows_error(window, monkeypatch, tmp_path):
    bad_path = tmp_path / "no_such_dir" / "file.txt"  # parent dir doesn't exist
    window.tabs[0].current_file = bad_path

    shown = {}
    monkeypatch.setattr(
        QMessageBox, "critical",
        staticmethod(lambda *a, **k: shown.setdefault("shown", True))
    )
    result = window._save_document(window.tabs[0])
    assert result is False
    assert shown.get("shown") is True


# ------------------------------------------------------------------
# Delete file
# ------------------------------------------------------------------

def test_delete_file_without_current_file_shows_info(window, monkeypatch):
    shown = {}
    monkeypatch.setattr(
        QMessageBox, "information",
        staticmethod(lambda *a, **k: shown.setdefault("shown", True))
    )
    window.delete_file()
    assert shown.get("shown") is True


def test_delete_file_confirmed_removes_file_and_tab(window, monkeypatch, tmp_path):
    target = tmp_path / "to_delete.txt"
    target.write_text("bye")
    window.tabs[0].current_file = target

    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    window.delete_file()

    assert not target.exists()
    assert len(window.tabs) == 1  # a fresh Untitled tab replaces the closed one


def test_delete_file_declined_keeps_file(window, monkeypatch, tmp_path):
    target = tmp_path / "keep_me.txt"
    target.write_text("still here")
    window.tabs[0].current_file = target

    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.No))
    window.delete_file()

    assert target.exists()


# ------------------------------------------------------------------
# Recent files menu
# ------------------------------------------------------------------

def test_recent_files_menu_shows_empty_placeholder(window):
    window.settings_manager.save_recent_files([])
    window._update_recent_files_menu()
    actions = window.recent_menu.actions()
    assert len(actions) == 1
    assert actions[0].text() == "(Empty)"
    assert actions[0].isEnabled() is False


def test_recent_files_menu_lists_files(window, tmp_path):
    f1 = tmp_path / "one.txt"
    f2 = tmp_path / "two.txt"
    f1.write_text("1")
    f2.write_text("2")
    window.settings_manager.save_recent_files([str(f1), str(f2)])
    window._update_recent_files_menu()

    action_texts = [a.text() for a in window.recent_menu.actions()]
    assert "one.txt" in action_texts
    assert "two.txt" in action_texts
    assert "Clear Recent Files" in action_texts


def test_clear_recent_files_empties_the_list(window, tmp_path):
    f1 = tmp_path / "one.txt"
    f1.write_text("1")
    window.settings_manager.save_recent_files([str(f1)])
    window._update_recent_files_menu()

    window._clear_recent_files()

    assert window.settings_manager.get_recent_files() == []
    assert window.recent_menu.actions()[0].text() == "(Empty)"


# ------------------------------------------------------------------
# Formatting delegation wrappers
# ------------------------------------------------------------------

def test_formatting_wrappers_delegate_to_fmt_ctrl(window, monkeypatch):
    calls = []
    for name in ("toggle_bold", "toggle_italic", "toggle_underline",
                 "toggle_strikethrough", "apply_superscript", "apply_subscript",
                 "clear_formatting", "increase_indent", "decrease_indent",
                 "toggle_bullet_list", "toggle_numbered_list", "insert_table",
                 "show_table_properties", "add_link", "insert_code_block",
                 "insert_horizontal_line", "insert_image"):
        monkeypatch.setattr(window.fmt_ctrl, name, lambda *a, n=name: calls.append(n))

    window.toggle_bold()
    window.toggle_italic()
    window.toggle_underline()
    window.toggle_strikethrough()
    window._apply_superscript()
    window._apply_subscript()
    window.clear_formatting()
    window._increase_indent()
    window._decrease_indent()
    window.toggle_bullet_list()
    window.toggle_numbered_list()
    window.insert_table()
    window.show_table_properties()
    window.add_link()
    window._insert_code_block()
    window._insert_horizontal_line()
    window._insert_image()

    assert calls == [
        "toggle_bold", "toggle_italic", "toggle_underline", "toggle_strikethrough",
        "apply_superscript", "apply_subscript", "clear_formatting",
        "increase_indent", "decrease_indent", "toggle_bullet_list",
        "toggle_numbered_list", "insert_table", "show_table_properties",
        "add_link", "insert_code_block", "insert_horizontal_line", "insert_image",
    ]


def test_set_alignment_delegates_and_updates_buttons(window, monkeypatch):
    called = {}
    monkeypatch.setattr(window.fmt_ctrl, "set_alignment", lambda a: called.setdefault("alignment", a))
    window.set_alignment(Qt.AlignmentFlag.AlignRight)
    assert called["alignment"] == Qt.AlignmentFlag.AlignRight


def test_change_font_family_delegates(window, monkeypatch):
    called = {}
    monkeypatch.setattr(window.fmt_ctrl, "change_font_family", lambda f: called.setdefault("font", f))
    font = QFont("Georgia")
    window._change_font_family(font)
    assert called["font"] is font


def test_change_font_size_delegates(window, monkeypatch):
    called = {}
    monkeypatch.setattr(window.fmt_ctrl, "change_font_size", lambda s: called.setdefault("size", s))
    window._change_font_size("16")
    assert called["size"] == "16"


def test_change_text_color_passes_toolbar_refresh_callback(window, monkeypatch):
    called = {}
    monkeypatch.setattr(window.fmt_ctrl, "change_text_color", lambda cb: called.setdefault("cb", cb))
    window.change_text_color()
    assert called["cb"] == window.toolbar_ctrl.refresh_text_color_btn


def test_change_background_color_passes_toolbar_refresh_callback(window, monkeypatch):
    called = {}
    monkeypatch.setattr(window.fmt_ctrl, "change_background_color", lambda cb: called.setdefault("cb", cb))
    window.change_background_color()
    assert called["cb"] == window.toolbar_ctrl.refresh_bg_color_btn


# ------------------------------------------------------------------
# Toolbar state sync
# ------------------------------------------------------------------

def test_update_format_buttons_reflects_bold_state(window):
    window.fmt_ctrl.toggle_bold()
    window._update_format_buttons()
    assert window.toolbar_ctrl.bold_btn.isChecked() is True


def test_update_format_buttons_noop_without_current_tab(window, monkeypatch):
    monkeypatch.setattr(window, "_get_current_tab", lambda: None)
    window._update_format_buttons()  # should not raise


# ------------------------------------------------------------------
# Theme / spellcheck toggles
# ------------------------------------------------------------------

def test_toggle_theme_switches_state_and_persists(window):
    original = window._dark_theme
    window._toggle_theme(original)  # checked == True means "light theme" is on
    assert window._dark_theme != original
    assert window.settings_manager.get_theme() == window._dark_theme


def test_toggle_spell_check_disables_highlighters(window):
    window.new_tab()
    window._toggle_spell_check(False)
    assert window.spell_check_enabled is False
    for tab in window.tabs:
        assert tab.spell_highlighter.enabled is False


def test_toggle_spell_check_reenable(window):
    window._toggle_spell_check(False)
    window._toggle_spell_check(True)
    assert window.spell_check_enabled is True


# ------------------------------------------------------------------
# Search / replace
# ------------------------------------------------------------------

def test_show_and_hide_search_bar(window):
    assert window.search_bar.isVisible() is False
    window._show_search_bar()
    assert window.search_bar.isVisible() is True
    window._show_search_bar()  # toggling again hides it
    assert window.search_bar.isVisible() is False


def test_find_text_selects_match(window):
    window.tabs[0].text_edit.setPlainText("find the needle in the haystack")
    window.search_bar.search_input.setText("needle")
    window._find_text()
    cursor = window.tabs[0].text_edit.textCursor()
    assert cursor.selectedText() == "needle"


def test_find_text_with_empty_search_clears_selections(window):
    window.tabs[0].text_edit.setPlainText("some text")
    window.search_bar.search_input.setText("")
    window._find_text()
    assert window.tabs[0].text_edit.extraSelections() == []


def test_find_text_wraps_around_when_not_found_forward(window):
    window.tabs[0].text_edit.setPlainText("alpha beta alpha")
    cursor = window.tabs[0].text_edit.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    window.tabs[0].text_edit.setTextCursor(cursor)

    window.search_bar.search_input.setText("alpha")
    window._find_text(backward=False)

    found_cursor = window.tabs[0].text_edit.textCursor()
    assert found_cursor.selectedText() == "alpha"


def test_replace_text_replaces_first_match(window):
    window.tabs[0].text_edit.setPlainText("cat sat on the mat")
    window.search_bar.search_input.setText("sat")
    window.search_bar.replace_input.setText("SAT")

    window._replace_text()

    assert "SAT" in window.tabs[0].text_edit.toPlainText()


def test_replace_text_without_search_term_warns(window, monkeypatch):
    shown = {}
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: shown.setdefault("shown", True)))
    window.search_bar.search_input.setText("")
    window._replace_text()
    assert shown.get("shown") is True


def test_replace_all_replaces_every_match(window, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))
    window.tabs[0].text_edit.setPlainText("dog dog dog")
    window.search_bar.search_input.setText("dog")
    window.search_bar.replace_input.setText("cat")

    window._replace_all_text()

    assert window.tabs[0].text_edit.toPlainText() == "cat cat cat"


def test_replace_all_with_no_matches_reports_zero(window, monkeypatch):
    info = {}
    monkeypatch.setattr(
        QMessageBox, "information",
        staticmethod(lambda parent, title, msg: info.setdefault("msg", msg))
    )
    window.tabs[0].text_edit.setPlainText("nothing matches here")
    window.search_bar.search_input.setText("zzz")
    window.search_bar.replace_input.setText("yyy")

    window._replace_all_text()

    assert "No matches found" in info["msg"]


# ------------------------------------------------------------------
# Status bar updates
# ------------------------------------------------------------------

def test_update_status_bar_reflects_word_count(window):
    window.tabs[0].text_edit.setPlainText("one two three")
    window._update_status_bar()
    assert "3 words" in window.status_widget.word_count_label.text()


def test_on_text_changed_updates_titles(window):
    window.tabs[0].text_edit.setPlainText("changed!")
    window._on_text_changed()
    assert window.tabs[0].get_display_name() in window.tab_widget.tabText(0)


# ------------------------------------------------------------------
# Undo / redo
# ------------------------------------------------------------------

def test_undo_redo_round_trip(window):
    text_edit = window.tabs[0].text_edit
    text_edit.setPlainText("hello ")
    cursor = text_edit.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    cursor.insertText("world")  # setPlainText() resets undo history; insertText() is undoable
    assert text_edit.toPlainText() == "hello world"

    window._undo()
    assert text_edit.toPlainText() == "hello "

    window._redo()
    assert text_edit.toPlainText() == "hello world"


# ------------------------------------------------------------------
# Close event
# ------------------------------------------------------------------

def test_close_event_with_no_modified_tabs_accepts(window):
    event = type("FakeEvent", (), {"_accepted": None,
                                    "accept": lambda self: setattr(self, "_accepted", True),
                                    "ignore": lambda self: setattr(self, "_accepted", False)})()
    window.closeEvent(event)
    assert event._accepted is True


def test_close_event_with_modified_tabs_and_no_choice_ignores(window, monkeypatch):
    window.tabs[0].text_edit.setPlainText("unsaved")
    window.tabs[0].text_edit.document().setModified(True)

    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.No))

    event = type("FakeEvent", (), {"_accepted": None,
                                    "accept": lambda self: setattr(self, "_accepted", True),
                                    "ignore": lambda self: setattr(self, "_accepted", False)})()
    window.closeEvent(event)
    assert event._accepted is False


def test_close_event_with_modified_tabs_and_yes_choice_accepts(window, monkeypatch):
    window.tabs[0].text_edit.setPlainText("unsaved")
    window.tabs[0].text_edit.document().setModified(True)

    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))

    event = type("FakeEvent", (), {"_accepted": None,
                                    "accept": lambda self: setattr(self, "_accepted", True),
                                    "ignore": lambda self: setattr(self, "_accepted", False)})()
    window.closeEvent(event)
    assert event._accepted is True


# ------------------------------------------------------------------
# Key press handling
# ------------------------------------------------------------------

def test_escape_key_hides_visible_search_bar(window):
    from PyQt6.QtGui import QKeyEvent
    from PyQt6.QtCore import QEvent

    window._show_search_bar()
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    window.keyPressEvent(event)
    assert window.search_bar.isVisible() is False