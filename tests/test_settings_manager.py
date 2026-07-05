# ============================================================================
# SettingsManager Tests
# covers persistence of window geometry, recent files, open tabs, and theme
# preference. QSettings is redirected to a temp .ini file per test (via
# QSettings.setPath/setDefaultFormat) so tests never touch the real user
# settings on disk, and each test starts from a clean slate.
# ============================================================================

import pytest
from PyQt6.QtCore import QSettings, QByteArray
from PyQt6.QtWidgets import QApplication, QMainWindow

from services.settings_manager import SettingsManager
from config.app_config import AppConfig


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def manager(qapp, tmp_path, monkeypatch):
    """A SettingsManager backed by an isolated ini file in tmp_path."""
    ini_path = tmp_path / "settings.ini"

    def fake_init(self):
        self.settings = QSettings(str(ini_path), QSettings.Format.IniFormat)

    monkeypatch.setattr(SettingsManager, "__init__", fake_init)
    mgr = SettingsManager()
    yield mgr
    mgr.settings.sync()


# ------------------------------------------------------------------
# Window geometry
# ------------------------------------------------------------------

def test_save_and_restore_window_geometry(manager, qapp):
    window = QMainWindow()
    geometry = window.saveGeometry()
    state = window.saveState()

    manager.save_window_geometry(geometry, state)

    other_window = QMainWindow()
    restored = manager.restore_window_geometry(other_window)
    assert restored is True


def test_restore_window_geometry_returns_false_when_nothing_saved(manager):
    window = QMainWindow()
    assert manager.restore_window_geometry(window) is False


# ------------------------------------------------------------------
# Recent files
# ------------------------------------------------------------------

def test_get_recent_files_defaults_to_empty_list(manager):
    assert manager.get_recent_files() == []


def test_save_and_get_recent_files_filters_missing(manager, tmp_path):
    existing = tmp_path / "a.txt"
    existing.write_text("hi")
    missing = str(tmp_path / "does_not_exist.txt")

    manager.save_recent_files([str(existing), missing])

    assert manager.get_recent_files() == [str(existing)]


def test_save_recent_files_respects_max_limit(manager, tmp_path):
    files = []
    for i in range(AppConfig.MAX_RECENT_FILES + 5):
        f = tmp_path / f"file{i}.txt"
        f.write_text("x")
        files.append(str(f))

    manager.save_recent_files(files)

    assert len(manager.get_recent_files()) == AppConfig.MAX_RECENT_FILES


def test_add_recent_file_inserts_at_front(manager, tmp_path):
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("a")
    file_b.write_text("b")

    manager.add_recent_file(str(file_a))
    manager.add_recent_file(str(file_b))

    assert manager.get_recent_files() == [str(file_b), str(file_a)]


def test_add_recent_file_moves_existing_entry_to_front(manager, tmp_path):
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("a")
    file_b.write_text("b")

    manager.add_recent_file(str(file_a))
    manager.add_recent_file(str(file_b))
    manager.add_recent_file(str(file_a))  # re-add a, should move to front

    assert manager.get_recent_files() == [str(file_a), str(file_b)]


def test_add_recent_file_respects_max_limit(manager, tmp_path):
    files = []
    for i in range(AppConfig.MAX_RECENT_FILES + 3):
        f = tmp_path / f"recent{i}.txt"
        f.write_text("x")
        files.append(str(f))
        manager.add_recent_file(str(f))

    result = manager.get_recent_files()
    assert len(result) == AppConfig.MAX_RECENT_FILES
    # most recently added should be first
    assert result[0] == files[-1]


# ------------------------------------------------------------------
# Open tabs
# ------------------------------------------------------------------

def test_get_open_tabs_defaults_to_empty(manager):
    tabs, index = manager.get_open_tabs()
    assert tabs == []
    assert index == 0


def test_save_and_get_open_tabs(manager, tmp_path):
    file_a = tmp_path / "tab_a.txt"
    file_b = tmp_path / "tab_b.txt"
    file_a.write_text("a")
    file_b.write_text("b")

    manager.save_open_tabs([str(file_a), str(file_b)], 1)

    tabs, index = manager.get_open_tabs()
    assert tabs == [str(file_a), str(file_b)]
    assert index == 1


def test_save_open_tabs_filters_missing_and_empty(manager, tmp_path):
    file_a = tmp_path / "tab_a.txt"
    file_a.write_text("a")
    missing = str(tmp_path / "missing.txt")

    manager.save_open_tabs([str(file_a), missing, ""], 0)

    tabs, _ = manager.get_open_tabs()
    assert tabs == [str(file_a)]


def test_clear_open_tabs(manager, tmp_path):
    file_a = tmp_path / "tab_a.txt"
    file_a.write_text("a")
    manager.save_open_tabs([str(file_a)], 0)

    manager.clear_open_tabs()

    tabs, index = manager.get_open_tabs()
    assert tabs == []
    assert index == 0


# ------------------------------------------------------------------
# Theme preference
# ------------------------------------------------------------------

def test_get_theme_defaults_to_dark(manager):
    assert manager.get_theme() is True


def test_save_and_get_theme_light(manager):
    manager.save_theme(False)
    assert manager.get_theme() is False


def test_save_and_get_theme_dark(manager):
    manager.save_theme(False)
    manager.save_theme(True)
    assert manager.get_theme() is True
