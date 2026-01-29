from services.settings_manager import SettingsManager

def test_recent_files(tmp_path, monkeypatch):
    manager = SettingsManager()
    fake_file = tmp_path / "file.txt"
    fake_file.write_text("hi")

    manager.save_recent_files([str(fake_file)])
    recent = manager.get_recent_files()

    assert str(fake_file) in recent