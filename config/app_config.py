class AppConfig:
    APP_NAME = "Rich Text Notepad"
    VERSION = "3.0.0"
    MAX_FILE_SIZE_MB = 10
    MAX_RECENT_FILES = 10
    AUTOSAVE_INTERVAL_MS = 30000
    FILE_FILTERS = (
        "All Supported Files (*.html *.txt);;"
        "HTML Files (*.html);;"
        "Text Files (*.txt);;"
        "All Files (*)"
    )
    DEFAULT_EXTENSION = ".html"