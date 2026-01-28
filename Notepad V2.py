"""
Rich Text Notepad
A full-featured rich text editor with tabbed interface, search, and file management.
"""

import sys

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from pathlib import Path
from typing import Optional, List

import os

# ============================================================================
# Configuration & Constants
# ============================================================================

class AppConfig:
    """Centralized application configuration"""
    APP_NAME = "Rich Text Notepad"
    VERSION = "3.0.0"
    MAX_FILE_SIZE_MB = 10
    MAX_RECENT_FILES = 10
    AUTOSAVE_INTERVAL_MS = 30000  # 30 seconds
    
    # File filters
    FILE_FILTERS = (
        "All Supported Files (*.html *.txt);;"
        "HTML Files (*.html);;"
        "Text Files (*.txt);;"
        "All Files (*)"
    )
    
    # Default file extension
    DEFAULT_EXTENSION = ".html"

    # Script's directory. This makes relative paths work
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

class StyleSheet:
    """Application-wide stylesheet"""
    DARK_THEME = """
        QWidget {
            background-color: #2D2D2D;
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #555555;
            border-radius: 5px;
            min-height: 30px;
            background-color: #3D3D3D;
        }
        QLineEdit:focus {
            border: 1px solid #0078D4;
        }
        QPushButton {
            background-color: #4A4A4A;
            padding: 2px 8px;
            border-radius: 5px;
            min-height: 30px;
            border: 1px solid #555555;
            margin: 0;
        }
        QPushButton:hover {
            background-color: #5A5A5A;
        }
        QPushButton:pressed {
            background-color: #353535;
        }
        QPushButton:checked {
            background-color: #0078D4;
            border: 1px solid #005A9E;
        }
        QPushButton:disabled {
            background-color: #3A3A3A;
            color: #808080;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2D2D2D;
        }
        QTabBar::tab {
            background-color: #404040;
            color: #FFFFFF;
            padding: 8px 12px;
            margin-right: 2px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:selected {
            background-color: #2D2D2D;
            border-bottom: 2px solid #0078D4;
        }
        QTabBar::tab:hover {
            background-color: #4A4A4A;
        }
        QToolBar {
            background-color: #404040;
            border: 1px solid #555555;
            spacing: 5px;
            padding: 5px;
        }
        QMenuBar {
            background-color: #404040;
            border-bottom: 1px solid #555555;
        }
        QMenuBar::item {
            padding: 5px 10px;
            background-color: transparent;
        }
        QMenuBar::item:selected {
            background-color: #4A4A4A;
        }
        QMenu {
            background-color: #404040;
            border: 1px solid #555555;
        }
        QMenu::item {
            padding: 5px 30px;
        }
        QMenu::item:selected {
            background-color: #4A4A4A;
        }
        QStatusBar {
            background-color: #404040;
            border-top: 1px solid #555555;
        }
        QLabel {
            color: #CCCCCC;
        }
        QComboBox, QFontComboBox {
            min-height: 36px;
            padding: 2px 10px;
            border: 1px solid #555555;
            border-radius: 6px;
            background-color: #3D3D3D;
            color: #FFFFFF;
            font-size: 16px;
        }

        /* Right-side drop-down area */
        QComboBox::drop-down, QFontComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 30px;

            /* IMPORTANT: don't draw a separate box */
            background: transparent;
            border-left: 1px solid #555555;
        }

        QComboBox::down-arrow, QFontComboBox::down-arrow {
            width: 14px;
            height: 14px;
            image: url(icons/down_arrow.svg);
        }

        /* Fallback arrow if image is missing */
        QComboBox::down-arrow:!has-image,
        QFontComboBox::down-arrow:!has-image {
            border: none;
            background: none;
        }

        /* Popup list */
        QComboBox QAbstractItemView,
        QFontComboBox QAbstractItemView {
            background-color: #404040;
            border: 1px solid #555555;
            color: #FFFFFF;
            outline: none;
            selection-background-color: #0078D4;
        }

        /* Items inside popup */
        QComboBox QAbstractItemView::item,
        QFontComboBox QAbstractItemView::item {
            min-height: 35px;
            padding-left: 10px;
        }
        
        /* Individual items in the list */
        QComboBox QAbstractItemView::item, QFontComboBox QAbstractItemView::item {
            min-height: 35px;
            padding-left: 10px;
        }

        QComboBox QAbstractItemView::item:selected, QFontComboBox QAbstractItemView::item:selected {
            background-color: #0078D4;
            color: white;
        }
        
        QComboBox::drop-down, QFontComboBox::drop-down {
            background: transparent;
            border-left: none;
        }
        
    """

# ============================================================================
# Document Model
# ============================================================================

class DocumentTab:
    """Encapsulates a single document with its state and metadata"""
    
    def __init__(self, name: Optional[str] = None):
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setUndoRedoEnabled(True)  # Explicitly enable
        
        self.current_file: Optional[Path] = None
        self.name = name or "Untitled"
        self._last_saved_content = ""
        
        # Use Qt's built-in document modified tracking
        self.text_edit.document().setModified(False)
        
    @property
    def is_modified(self) -> bool:
        """Check if document has unsaved changes"""
        return self.text_edit.document().isModified()
    
    def mark_saved(self):
        """Mark document as saved"""
        self.text_edit.document().setModified(False)
        self._last_saved_content = self.text_edit.toHtml()
    
    def get_display_name(self) -> str:
        """Get the display name for tab/window title"""
        if self.current_file:
            filename = self.current_file.name
        else:
            filename = self.name
        return f"{'●' if self.is_modified else ''}{filename}"
    
    def get_file_path(self) -> str:
        """Get the file path as string, or empty if unsaved"""
        return str(self.current_file) if self.current_file else ""
    
    def get_content_html(self) -> str:
        """Get document content as HTML"""
        return self.text_edit.toHtml()
    
    def get_content_plain(self) -> str:
        """Get document content as plain text"""
        return self.text_edit.toPlainText()
    
    def set_content(self, content: str, is_html: bool = False):
        """Set document content, preserving undo stack"""
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        
        if is_html:
            self.text_edit.setHtml(content)
        else:
            self.text_edit.setPlainText(content)
            
        cursor.endEditBlock()
        self.text_edit.document().setModified(False)
        self._last_saved_content = content


# ============================================================================
# Custom Widgets
# ============================================================================

class SearchBar(QWidget):
    """Custom search bar with find and replace functionality"""
    
    find_next_requested = pyqtSignal()
    find_prev_requested = pyqtSignal()
    close_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find...")
        self.search_input.setClearButtonEnabled(True)
        
        # Counter label
        self.counter_label = QLabel("0/0")
        self.counter_label.setStyleSheet("color: gray; min-width: 50px;")
        
        # Navigation buttons
        self.prev_btn = QPushButton("↑")
        self.prev_btn.setFixedWidth(35)
        self.prev_btn.setToolTip("Previous (Shift+F3)")
        
        self.next_btn = QPushButton("↓")
        self.next_btn.setFixedWidth(35)
        self.next_btn.setToolTip("Next (F3)")
        
        # Case sensitive checkbox
        self.case_sensitive_cb = QCheckBox("Aa")
        self.case_sensitive_cb.setToolTip("Match case")
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedWidth(30)
        self.close_btn.setToolTip("Close (Esc)")
        
        # Add to layout
        layout.addWidget(self.search_input)
        layout.addWidget(self.counter_label)
        layout.addWidget(self.case_sensitive_cb)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.close_btn)
        
        # Connect signals
        self.search_input.returnPressed.connect(self.find_next_requested)
        self.next_btn.clicked.connect(self.find_next_requested)
        self.prev_btn.clicked.connect(self.find_prev_requested)
        self.close_btn.clicked.connect(self.close_requested)
        
    def get_search_text(self) -> str:
        """Get current search text"""
        return self.search_input.text()
    
    def is_case_sensitive(self) -> bool:
        """Check if case sensitive search is enabled"""
        return self.case_sensitive_cb.isChecked()
    
    def update_counter(self, current: int, total: int):
        """Update the match counter display"""
        self.counter_label.setText(f"{current}/{total}")
        
    def focus_input(self):
        """Focus the search input and select all text"""
        self.search_input.setFocus()
        self.search_input.selectAll()


class StatusBarWidget(QWidget):
    """Custom status bar with document info"""
    
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(15)
        
        self.file_label = QLabel("No file")
        self.cursor_label = QLabel("Line 1, Col 1")
        self.word_count_label = QLabel("0 words")
        self.encoding_label = QLabel("UTF-8")
        
        layout.addWidget(self.file_label)
        layout.addStretch()
        layout.addWidget(self.word_count_label)
        layout.addWidget(self.cursor_label)
        layout.addWidget(self.encoding_label)
    
    def update_file(self, filepath: str):
        """Update file path display"""
        if filepath:
            self.file_label.setText(filepath)
        else:
            self.file_label.setText("No file")
    
    def update_cursor(self, line: int, col: int):
        """Update cursor position display"""
        self.cursor_label.setText(f"Line {line}, Col {col}")
    
    def update_word_count(self, words: int, chars: int):
        """Update word and character count"""
        self.word_count_label.setText(f"{words} words, {chars} chars")


# ============================================================================
# File Operations Handler
# ============================================================================

class FileOperations:
    """Handles all file I/O operations with proper error handling"""
    
    @staticmethod
    def check_file_size(filepath: Path) -> bool:
        """Check if file size is within acceptable limits"""
        size_mb = filepath.stat().st_size / (1024 * 1024)
        return size_mb <= AppConfig.MAX_FILE_SIZE_MB
    
    @staticmethod
    def read_file(filepath: Path) -> tuple[str, bool]:
        """
        Read file content safely
        Returns: (content, is_html)
        Raises: IOError, UnicodeDecodeError
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if not FileOperations.check_file_size(filepath):
            raise IOError(
                f"File too large ({filepath.stat().st_size / (1024*1024):.1f} MB). "
                f"Maximum size is {AppConfig.MAX_FILE_SIZE_MB} MB."
            )
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            is_html = filepath.suffix.lower() == '.html'
            return content, is_html
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
            is_html = filepath.suffix.lower() == '.html'
            return content, is_html
    
    @staticmethod
    def write_file(filepath: Path, content: str, as_html: bool = True):
        """
        Write content to file safely
        Raises: IOError
        """
        # Create backup if file exists
        if filepath.exists():
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            try:
                backup_path.write_text(filepath.read_text(encoding='utf-8'), encoding='utf-8')
            except Exception:
                pass  # Backup is best-effort
        
        # Write new content
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write file: {e}")
    
    @staticmethod
    def delete_file(filepath: Path):
        """
        Delete file safely
        Raises: IOError
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            filepath.unlink()
        except Exception as e:
            raise IOError(f"Failed to delete file: {e}")


# ============================================================================
# Settings Manager
# ============================================================================

class SettingsManager:
    """Manages application settings persistence"""
    
    def __init__(self):
        self.settings = QSettings("RichTextNotepad", "MainApp")
    
    def save_window_geometry(self, geometry: QByteArray, state: QByteArray):
        """Save window geometry and state"""
        self.settings.setValue("window/geometry", geometry)
        self.settings.setValue("window/state", state)
    
    def restore_window_geometry(self, window: QMainWindow) -> bool:
        """Restore window geometry and state"""
        geometry = self.settings.value("window/geometry")
        state = self.settings.value("window/state")
        
        if geometry:
            window.restoreGeometry(geometry)
        if state:
            window.restoreState(state)
        
        return bool(geometry and state)
    
    def save_recent_files(self, files: List[str]):
        """Save list of recent files"""
        # Keep only existing files
        existing_files = [f for f in files if Path(f).exists()]
        self.settings.setValue("recent_files", existing_files[:AppConfig.MAX_RECENT_FILES])
    
    def get_recent_files(self) -> List[str]:
        """Get list of recent files"""
        files = self.settings.value("recent_files", [])
        if isinstance(files, str):
            files = [files] if files else []
        # Filter to only existing files
        return [f for f in files if Path(f).exists()]
    
    def add_recent_file(self, filepath: str):
        """Add a file to recent files list"""
        recent = self.get_recent_files()
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        self.save_recent_files(recent[:AppConfig.MAX_RECENT_FILES])


# ============================================================================
# Main Window
# ============================================================================

class MainWindow(QMainWindow):
    """Main application window with tabbed document interface"""
    
    def __init__(self):
        super().__init__()
        
        self.tabs: List[DocumentTab] = []
        self.tab_counter = 1
        self.settings_manager = SettingsManager()
        
        self._setup_ui()
        self._setup_shortcuts()
        self._setup_timers()
        self._restore_settings()
        
        # Create first tab
        self.new_tab()
    
    def _setup_ui(self):
        """Initialize the user interface"""
        self.setStyleSheet(StyleSheet.DARK_THEME)
        self.setWindowTitle(AppConfig.APP_NAME)
        self.setMinimumSize(QSize(800, 600))
        self.resize(QSize(1200, 700))
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create formatting toolbar
        self._create_formatting_toolbar()
        layout.addWidget(self.format_toolbar)
        
        # Create tab widget
        self._create_tab_widget()
        layout.addWidget(self.tab_widget)
        
        # Create search bar
        self.search_bar = SearchBar()
        self.search_bar.find_next_requested.connect(lambda: self._find_text(backward=False))
        self.search_bar.find_prev_requested.connect(lambda: self._find_text(backward=True))
        self.search_bar.close_requested.connect(self._hide_search_bar)
        self.search_bar.search_input.textChanged.connect(lambda: self._find_text(backward=False))
        self.search_bar.case_sensitive_cb.toggled.connect(lambda: self._find_text(backward=False))
        self.search_bar.setVisible(False)
        layout.addWidget(self.search_bar)
        
        self.setCentralWidget(central_widget)
        
        # Create custom status bar
        self.status_widget = StatusBarWidget()
        self.statusBar().addPermanentWidget(self.status_widget, 1)
    
    def _create_menu_bar(self):
        """Create application menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        new_action = QAction("&New Tab", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Recent files submenu
        self.recent_menu = file_menu.addMenu("Open &Recent")
        self._update_recent_files_menu()
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_tab_action = QAction("&Close Tab", self)
        close_tab_action.setShortcut(QKeySequence.StandardKey.Close)
        close_tab_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        delete_action = QAction("&Delete File...", self)
        delete_action.setShortcut(QKeySequence("Ctrl+Delete"))
        delete_action.triggered.connect(self.delete_file)
        file_menu.addAction(delete_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction("&Find...", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self._show_search_bar)
        edit_menu.addAction(find_action)
        
        # Format menu
        format_menu = menu_bar.addMenu("F&ormat")
        
        bold_action = QAction("&Bold", self)
        bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        bold_action.triggered.connect(self.toggle_bold)
        format_menu.addAction(bold_action)
        
        italic_action = QAction("&Italic", self)
        italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        italic_action.triggered.connect(self.toggle_italic)
        
        format_menu.addAction(italic_action)
        
        underline_action = QAction("&Underline", self)
        underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        underline_action.triggered.connect(self.toggle_underline)
        format_menu.addAction(underline_action)
        
        format_menu.addSeparator()
        
        clear_format_action = QAction("&Clear Formatting", self)
        clear_format_action.setShortcut(QKeySequence("Ctrl+\\"))
        clear_format_action.triggered.connect(self.clear_formatting)
        format_menu.addAction(clear_format_action)
    
    def _create_formatting_toolbar(self):
        """Create formatting toolbar with text style controls"""
        self.format_toolbar = QToolBar("Formatting")
        self.format_toolbar.setMovable(False)
        
        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setMaximumWidth(200)
        self.font_combo.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        self.font_combo.currentFontChanged.connect(self._change_font_family)
        self.format_toolbar.addWidget(self.font_combo)
        
        # Font size
        self.size_combo = QComboBox()
        self.size_combo.addItems(['8', '9', '10', '11', '12', '14', '16', '18', '20', '24', '28', '36', '48', '72'])
        self.size_combo.setCurrentText('14')
        self.size_combo.currentTextChanged.connect(self._change_font_size)
        self.format_toolbar.addWidget(self.size_combo)
        
        self.format_toolbar.addSeparator()
        
        # Bold button
        self.bold_btn = QPushButton("B")
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(40, 35)
        self.bold_btn.setToolTip("Bold (Ctrl+B)")
        self.bold_btn.clicked.connect(self.toggle_bold)
        self.format_toolbar.addWidget(self.bold_btn)
        
        # Italic button
        self.italic_btn = QPushButton("I")
        self.italic_btn.setFont(QFont("Arial", 10, QFont.Weight.Normal, True))
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(40, 35)
        self.italic_btn.setToolTip("Italic (Ctrl+I)")
        self.italic_btn.clicked.connect(self.toggle_italic)
        self.format_toolbar.addWidget(self.italic_btn)
        
        # Underline button
        self.underline_btn = QPushButton("U")
        font = QFont("Arial", 10)
        font.setUnderline(True)
        self.underline_btn.setFont(font)
        self.underline_btn.setCheckable(True)
        self.underline_btn.setFixedSize(40, 35)
        self.underline_btn.setToolTip("Underline (Ctrl+U)")
        self.underline_btn.clicked.connect(self.toggle_underline)
        self.format_toolbar.addWidget(self.underline_btn)
        
        # Strikethrough button
        self.strike_btn = QPushButton("S")
        font = QFont("Arial", 10)
        font.setStrikeOut(True)
        self.strike_btn.setFont(font)
        self.strike_btn.setCheckable(True)
        self.strike_btn.setFixedSize(40, 35)
        self.strike_btn.setToolTip("Strikethrough")
        self.strike_btn.clicked.connect(self.toggle_strikethrough)
        self.format_toolbar.addWidget(self.strike_btn)
        
        self.format_toolbar.addSeparator()
        
        # Text color button
        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setStyleSheet("""
            QPushButton {
                color: #FF0000;
                font-weight: bold;
                border-bottom: 3px solid #FF0000;
            }
        """)
        self.text_color_btn.setFixedSize(40, 35)
        self.text_color_btn.setToolTip("Text Color")
        self.text_color_btn.clicked.connect(self.change_text_color)
        self.format_toolbar.addWidget(self.text_color_btn)
        
        # Background color button
        self.bg_color_btn = QPushButton("H")
        self.bg_color_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFF00;
                color: #000000;
                font-weight: bold;
            }
        """)
        self.bg_color_btn.setFixedSize(40, 35)
        self.bg_color_btn.setToolTip("Highlight Color")
        self.bg_color_btn.clicked.connect(self.change_background_color)
        self.format_toolbar.addWidget(self.bg_color_btn)
        
        self.format_toolbar.addSeparator()
        
        # Link button
        self.link_btn = QPushButton("🔗")
        self.link_btn.setFixedSize(40, 35)
        self.link_btn.setToolTip("Insert Link")
        self.link_btn.clicked.connect(self.add_link)
        self.format_toolbar.addWidget(self.link_btn)
        
        # Clear formatting button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedSize(70, 35)
        self.clear_btn.setToolTip("Clear Formatting")
        self.clear_btn.clicked.connect(self.clear_formatting)
        self.format_toolbar.addWidget(self.clear_btn)
    
    def _create_tab_widget(self):
        """Create tab widget for multiple documents"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._tab_changed)
        
        # Add + button for new tabs
        plus_button = QToolButton()
        plus_button.setText("+")
        plus_button.setStyleSheet("""
            QToolButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: #4A4A4A;
            }
        """)
        plus_button.setFixedSize(25, 25)
        plus_button.setToolTip("New Tab (Ctrl+N)")
        plus_button.clicked.connect(self.new_tab)
        self.tab_widget.setCornerWidget(plus_button, Qt.Corner.TopRightCorner)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Tab navigation (Ctrl+1 through Ctrl+9)
        for i in range(1, 10):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(lambda num=i: self._switch_to_tab(num))
        
        # Search navigation
        find_next_shortcut = QShortcut(QKeySequence("F3"), self)
        find_next_shortcut.activated.connect(lambda: self._find_text(backward=False))
        
        find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self)
        find_prev_shortcut.activated.connect(lambda: self._find_text(backward=True))
    
    def _setup_timers(self):
        """Setup periodic timers for status updates"""
        # Update status bar periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_bar)
        self.status_timer.start(100)  # Update every 100ms
    
    def _restore_settings(self):
        """Restore saved application settings"""
        if not self.settings_manager.restore_window_geometry(self):
            # Center on screen if no saved geometry
            screen = QApplication.primaryScreen().geometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2
            )
    
    # ========================================================================
    # Tab Management
    # ========================================================================
    
    def new_tab(self):
        """Create a new document tab"""
        tab_name = f"Untitled {self.tab_counter}"
        doc_tab = DocumentTab(tab_name)
        
        # Connect signals
        doc_tab.text_edit.textChanged.connect(self._on_text_changed)
        doc_tab.text_edit.cursorPositionChanged.connect(self._update_format_buttons)
        doc_tab.text_edit.cursorPositionChanged.connect(self._update_status_bar)
        
        # Add tab
        index = self.tab_widget.addTab(doc_tab.text_edit, doc_tab.get_display_name())
        self.tabs.append(doc_tab)
        self.tab_widget.setCurrentIndex(index)
        self.tab_counter += 1
        
        # Focus the editor
        doc_tab.text_edit.setFocus()
    
    def close_tab(self, index: int):
        """Close tab at given index"""
        if self.tab_widget.count() <= 1:
            return  # Keep at least one tab
        
        doc_tab = self.tabs[index]
        
        # Check for unsaved changes
        if doc_tab.is_modified:
            reply = self._confirm_close_modified(doc_tab)
            if reply == QMessageBox.StandardButton.Save:
                if not self._save_document(doc_tab):
                    return  # Cancel close if save failed
            elif reply == QMessageBox.StandardButton.Cancel:
                return  # Cancel close
        
        # Remove tab
        self.tab_widget.removeTab(index)
        self.tabs.pop(index)
    
    def close_current_tab(self):
        """Close the currently active tab"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)
    
    def _tab_changed(self, index: int):
        """Handle tab change event"""
        if 0 <= index < len(self.tabs):
            doc_tab = self.tabs[index]
            self._update_window_title(doc_tab)
            self._update_format_buttons()
            self._update_status_bar()
            doc_tab.text_edit.setFocus()
    
    def _switch_to_tab(self, tab_number: int):
        """Switch to tab by number (1-9)"""
        if tab_number == 9:
            # Ctrl+9 goes to last tab
            last_index = self.tab_widget.count() - 1
            if last_index >= 0:
                self.tab_widget.setCurrentIndex(last_index)
        else:
            # Ctrl+1 through Ctrl+8 go to specific tabs
            tab_index = tab_number - 1
            if 0 <= tab_index < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(tab_index)
    
    def _get_current_tab(self) -> Optional[DocumentTab]:
        """Get the currently active document tab"""
        current_index = self.tab_widget.currentIndex()
        if 0 <= current_index < len(self.tabs):
            return self.tabs[current_index]
        return None
    
    def _update_tab_title(self, doc_tab: DocumentTab):
        """Update the tab title for a document"""
        for i, tab in enumerate(self.tabs):
            if tab == doc_tab:
                self.tab_widget.setTabText(i, doc_tab.get_display_name())
                break
    
    def _update_window_title(self, doc_tab: DocumentTab):
        """Update the main window title"""
        display_name = doc_tab.get_display_name()
        self.setWindowTitle(f"{AppConfig.APP_NAME} - {display_name}")
    
    # ========================================================================
    # File Operations
    # ========================================================================
    
    def open_file(self, filepath: Optional[str] = None):
        """Open a file in a new tab"""
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self,
                "Open File",
                "",
                AppConfig.FILE_FILTERS
            )
        
        if not filepath:
            return
        
        file_path = Path(filepath)
        
        # Check if file is already open
        for i, tab in enumerate(self.tabs):
            if tab.current_file == file_path:
                self.tab_widget.setCurrentIndex(i)
                self.statusBar().showMessage(f"File already open: {file_path.name}", 3000)
                return
        
        # Load file in background to avoid UI freeze
        QTimer.singleShot(0, lambda: self._load_file_async(file_path))
    
    def _load_file_async(self, filepath: Path):
        """Load file asynchronously to avoid UI blocking"""
        try:
            # Show loading status
            self.statusBar().showMessage(f"Loading {filepath.name}...")
            QApplication.processEvents()
            
            # Read file
            content, is_html = FileOperations.read_file(filepath)
            
            # Create new tab
            doc_tab = DocumentTab()
            doc_tab.set_content(content, is_html)
            doc_tab.current_file = filepath
            
            # Connect signals
            doc_tab.text_edit.textChanged.connect(self._on_text_changed)
            doc_tab.text_edit.cursorPositionChanged.connect(self._update_format_buttons)
            doc_tab.text_edit.cursorPositionChanged.connect(self._update_status_bar)
            
            # Add tab
            index = self.tab_widget.addTab(doc_tab.text_edit, doc_tab.get_display_name())
            self.tabs.append(doc_tab)
            self.tab_widget.setCurrentIndex(index)
            
            # Update recent files
            self.settings_manager.add_recent_file(str(filepath))
            self._update_recent_files_menu()
            
            self.statusBar().showMessage(f"Opened: {filepath.name}", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Opening File",
                f"Could not open file:\n{filepath}\n\nError: {str(e)}"
            )
            self.statusBar().clearMessage()
    
    def save(self):
        """Save the current document"""
        current_tab = self._get_current_tab()
        if current_tab:
            self._save_document(current_tab)
    
    def save_as(self, doc_tab: Optional[DocumentTab] = None):
        """Save document with a new name"""
        if not doc_tab:
            doc_tab = self._get_current_tab()
        if not doc_tab:
            return False
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            doc_tab.current_file.name if doc_tab.current_file else "untitled.html",
            AppConfig.FILE_FILTERS
        )
        
        if not filename:
            return False
        
        filepath = Path(filename)
        
        # Ensure proper extension
        if not filepath.suffix:
            filepath = filepath.with_suffix(AppConfig.DEFAULT_EXTENSION)
        
        doc_tab.current_file = filepath
        return self._save_document(doc_tab)
    
    def _save_document(self, doc_tab: DocumentTab) -> bool:
        """Save a document to disk"""
        # If no file path, use Save As
        if not doc_tab.current_file:
            return self.save_as(doc_tab)
        
        try:
            # Determine content format
            is_html = doc_tab.current_file.suffix.lower() == '.html'
            content = doc_tab.get_content_html() if is_html else doc_tab.get_content_plain()
            
            # Write file
            FileOperations.write_file(doc_tab.current_file, content, is_html)
            
            # Mark as saved
            doc_tab.mark_saved()
            self._update_tab_title(doc_tab)
            self._update_window_title(doc_tab)
            
            # Update recent files
            self.settings_manager.add_recent_file(str(doc_tab.current_file))
            self._update_recent_files_menu()
            
            self.statusBar().showMessage(f"Saved: {doc_tab.current_file.name}", 3000)
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving File",
                f"Could not save file:\n{doc_tab.current_file}\n\nError: {str(e)}"
            )
            return False
    
    def delete_file(self):
        """Delete the current file from disk"""
        current_tab = self._get_current_tab()
        if not current_tab or not current_tab.current_file:
            QMessageBox.information(
                self,
                "Delete File",
                "No file to delete. Please save the document first."
            )
            return
        
        filepath = current_tab.current_file
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to permanently delete this file?\n\n{filepath.name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            FileOperations.delete_file(filepath)
            self.statusBar().showMessage(f"Deleted: {filepath.name}", 3000)
            
            # Close the tab
            current_index = self.tab_widget.currentIndex()
            self.tab_widget.removeTab(current_index)
            self.tabs.pop(current_index)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Deleting File",
                f"Could not delete file:\n{filepath}\n\nError: {str(e)}"
            )
    
    def _update_recent_files_menu(self):
        """Update the recent files menu"""
        self.recent_menu.clear()
        recent_files = self.settings_manager.get_recent_files()
        
        if not recent_files:
            action = QAction("(Empty)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
            return
        
        for filepath in recent_files:
            path = Path(filepath)
            action = QAction(path.name, self)
            action.setData(filepath)
            action.setToolTip(filepath)
            action.triggered.connect(lambda checked, f=filepath: self.open_file(f))
            self.recent_menu.addAction(action)
        
        self.recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_menu.addAction(clear_action)
    
    def _clear_recent_files(self):
        """Clear the recent files list"""
        self.settings_manager.save_recent_files([])
        self._update_recent_files_menu()
    
    # ========================================================================
    # Text Formatting
    # ========================================================================
    
    def toggle_bold(self):
        """Toggle bold formatting"""
        current_tab = self._get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            weight = QFont.Weight.Normal if fmt.fontWeight() == QFont.Weight.Bold else QFont.Weight.Bold
            fmt.setFontWeight(weight)
            current_tab.text_edit.mergeCurrentCharFormat(fmt)
            current_tab.text_edit.setFocus()
    
    def toggle_italic(self):
        """Toggle italic formatting"""
        current_tab = self._get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            current_tab.text_edit.mergeCurrentCharFormat(fmt)
            current_tab.text_edit.setFocus()
    
    def toggle_underline(self):
        """Toggle underline formatting"""
        current_tab = self._get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            current_tab.text_edit.mergeCurrentCharFormat(fmt)
            current_tab.text_edit.setFocus()
    
    def toggle_strikethrough(self):
        """Toggle strikethrough formatting"""
        current_tab = self._get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            fmt.setFontStrikeOut(not fmt.fontStrikeOut())
            current_tab.text_edit.mergeCurrentCharFormat(fmt)
            current_tab.text_edit.setFocus()
    
    def change_text_color(self):
        """Change text color"""
        current_tab = self._get_current_tab()
        if current_tab:
            current_color = current_tab.text_edit.textColor()
            color = QColorDialog.getColor(current_color, self, "Choose Text Color")
            
            if color.isValid():
                fmt = current_tab.text_edit.currentCharFormat()
                fmt.setForeground(QBrush(color))
                current_tab.text_edit.mergeCurrentCharFormat(fmt)
                
                # Update button appearance
                self.text_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {color.name()};
                        font-weight: bold;
                        border-bottom: 3px solid {color.name()};
                        background-color: #4A4A4A;
                    }}
                    QPushButton:hover {{
                        background-color: #5A5A5A;
                    }}
                """)
                current_tab.text_edit.setFocus()
    
    def change_background_color(self):
        """Change text background (highlight) color"""
        current_tab = self._get_current_tab()
        if current_tab:
            current_fmt = current_tab.text_edit.currentCharFormat()
            current_color = current_fmt.background().color()
            color = QColorDialog.getColor(current_color, self, "Choose Highlight Color")
            
            if color.isValid():
                fmt = current_tab.text_edit.currentCharFormat()
                fmt.setBackground(QBrush(color))
                current_tab.text_edit.mergeCurrentCharFormat(fmt)
                
                # Update button appearance
                text_color = "#000000" if color.lightness() > 128 else "#FFFFFF"
                self.bg_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        color: {text_color};
                        font-weight: bold;
                        border: 1px solid #555555;
                    }}
                    QPushButton:hover {{
                        opacity: 0.9;
                    }}
                """)
                current_tab.text_edit.setFocus()
    
    def add_link(self):
        """Add a hyperlink"""
        current_tab = self._get_current_tab()
        if current_tab:
            cursor = current_tab.text_edit.textCursor()
            selected_text = cursor.selectedText()
            
            # Get URL
            url, ok = QInputDialog.getText(
                self,
                "Insert Link",
                "Enter URL:",
                QLineEdit.EchoMode.Normal,
                "https://"
            )
            
            if not ok or not url:
                return
            
            # Get link text if needed
            if not selected_text:
                link_text, ok2 = QInputDialog.getText(
                    self,
                    "Insert Link",
                    "Enter link text:",
                    QLineEdit.EchoMode.Normal,
                    url
                )
                if ok2 and link_text:
                    selected_text = link_text
                else:
                    selected_text = url
            
            # Create link format
            fmt = QTextCharFormat()
            fmt.setAnchor(True)
            fmt.setAnchorHref(url)
            fmt.setForeground(QBrush(QColor("#0078D4")))
            fmt.setFontUnderline(True)
            
            if cursor.hasSelection():
                cursor.mergeCharFormat(fmt)
            else:
                cursor.insertText(selected_text, fmt)
            
            current_tab.text_edit.setFocus()
    
    def clear_formatting(self):
        """Clear all text formatting"""
        current_tab = self._get_current_tab()
        if current_tab:
            cursor = current_tab.text_edit.textCursor()
            
            if cursor.hasSelection():
                # Clear formatting for selected text
                fmt = QTextCharFormat()
                cursor.setCharFormat(fmt)
            else:
                # Reset current format for new typing
                current_tab.text_edit.setCurrentCharFormat(QTextCharFormat())
            
            current_tab.text_edit.setFocus()
    
    def _change_font_family(self, font: QFont):
        """Change font family"""
        current_tab = self._get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            fmt.setFontFamily(font.family())
            current_tab.text_edit.mergeCurrentCharFormat(fmt)
            current_tab.text_edit.setFocus()
    
    def _change_font_size(self, size: str):
        """Change font size"""
        current_tab = self._get_current_tab()
        if current_tab and size:
            try:
                point_size = int(size)
                fmt = current_tab.text_edit.currentCharFormat()
                fmt.setFontPointSize(point_size)
                current_tab.text_edit.mergeCurrentCharFormat(fmt)
                current_tab.text_edit.setFocus()
            except ValueError:
                pass
    
    def _update_format_buttons(self):
        """Update formatting button states based on current cursor position"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        fmt = current_tab.text_edit.currentCharFormat()
        
        # Block signals to prevent triggering formatting changes
        self.bold_btn.blockSignals(True)
        self.italic_btn.blockSignals(True)
        self.underline_btn.blockSignals(True)
        self.strike_btn.blockSignals(True)
        self.font_combo.blockSignals(True)
        self.size_combo.blockSignals(True)
        
        # Update button states
        self.bold_btn.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.italic_btn.setChecked(fmt.fontItalic())
        self.underline_btn.setChecked(fmt.fontUnderline())
        self.strike_btn.setChecked(fmt.fontStrikeOut())
        
        # Update font controls
        if fmt.font().family():
            self.font_combo.setCurrentFont(fmt.font())
        if fmt.fontPointSize() > 0:
            self.size_combo.setCurrentText(str(int(fmt.fontPointSize())))
        
        # Unblock signals
        self.bold_btn.blockSignals(False)
        self.italic_btn.blockSignals(False)
        self.underline_btn.blockSignals(False)
        self.strike_btn.blockSignals(False)
        self.font_combo.blockSignals(False)
        self.size_combo.blockSignals(False)
    
    # ========================================================================
    # Search Functionality
    # ========================================================================
    
    def _show_search_bar(self):
        """Show the search bar"""
        self.search_bar.setVisible(True)
        self.search_bar.focus_input()
    
    def _hide_search_bar(self):
        """Hide the search bar and clear highlights"""
        self.search_bar.setVisible(False)
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.text_edit.setExtraSelections([])
            cursor = current_tab.text_edit.textCursor()
            cursor.clearSelection()
            current_tab.text_edit.setTextCursor(cursor)
            current_tab.text_edit.setFocus()
    
    def _find_text(self, backward: bool = False):
        """Find text in the current document"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        search_text = self.search_bar.get_search_text()
        if not search_text:
            current_tab.text_edit.setExtraSelections([])
            self.search_bar.update_counter(0, 0)
            return
        
        # Build find flags
        flags = QTextDocument.FindFlag(0)
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        if self.search_bar.is_case_sensitive():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        
        # Find next occurrence
        found = current_tab.text_edit.find(search_text, flags)
        
        # Wrap around if not found
        if not found:
            cursor = current_tab.text_edit.textCursor()
            if backward:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            current_tab.text_edit.setTextCursor(cursor)
            current_tab.text_edit.find(search_text, flags)
        
        # Highlight all occurrences
        self._highlight_all_matches(search_text)
    
    def _highlight_all_matches(self, search_text: str):
        """Highlight all occurrences of search text"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        extra_selections = []
        text = current_tab.text_edit.toPlainText()
        current_pos = current_tab.text_edit.textCursor().selectionStart()
        
        # Find all matches
        if self.search_bar.is_case_sensitive():
            search_func = text.find
        else:
            text_lower = text.lower()
            search_text_lower = search_text.lower()
            search_func = text_lower.find
            text = text_lower
            search_text = search_text_lower
        
        pos = 0
        matches = []
        while True:
            pos = search_func(search_text, pos)
            if pos == -1:
                break
            matches.append(pos)
            pos += len(search_text)
        
        # Create highlighting for each match
        current_match_idx = 0
        for i, start_pos in enumerate(matches):
            selection = QTextEdit.ExtraSelection()
            cursor = QTextCursor(current_tab.text_edit.document())
            cursor.setPosition(start_pos)
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.KeepAnchor,
                len(search_text)
            )
            selection.cursor = cursor
            
            # Different color for current match
            if start_pos == current_pos:
                selection.format.setBackground(QColor("#FF8C00"))  # Orange
                current_match_idx = i
            else:
                selection.format.setBackground(QColor("#FFD700"))  # Yellow
            
            extra_selections.append(selection)
        
        current_tab.text_edit.setExtraSelections(extra_selections)
        
        # Update counter
        total = len(matches)
        current = (current_match_idx + 1) if total > 0 else 0
        self.search_bar.update_counter(current, total)
    
    # ========================================================================
    # Undo/Redo
    # ========================================================================
    
    def _undo(self):
        """Undo last action"""
        current_tab = self._get_current_tab()
        if current_tab and current_tab.text_edit.document().isUndoAvailable():
            current_tab.text_edit.undo()
    
    def _redo(self):
        """Redo last undone action"""
        current_tab = self._get_current_tab()
        if current_tab and current_tab.text_edit.document().isRedoAvailable():
            current_tab.text_edit.redo()
    
    # ========================================================================
    # Status Bar Updates
    # ========================================================================
    
    def _update_status_bar(self):
        """Update status bar with current document info"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        # Update file path
        self.status_widget.update_file(current_tab.get_file_path())
        
        # Update cursor position
        cursor = current_tab.text_edit.textCursor()
        block = cursor.block()
        line = block.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.status_widget.update_cursor(line, col)
        
        # Update word count
        text = current_tab.get_content_plain()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.status_widget.update_word_count(words, chars)
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    def _on_text_changed(self):
        """Handle text change in any document"""
        current_tab = self._get_current_tab()
        if current_tab:
            self._update_tab_title(current_tab)
            self._update_window_title(current_tab)
    
    def _confirm_close_modified(self, doc_tab: DocumentTab) -> QMessageBox.StandardButton:
        """Ask user to save modified document before closing"""
        filename = doc_tab.get_display_name().replace('●', '').strip()
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            f"Do you want to save changes to '{filename}'?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        return reply
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Check for unsaved changes in any tab
        modified_tabs = [tab for tab in self.tabs if tab.is_modified]
        
        if modified_tabs:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"You have {len(modified_tabs)} unsaved document(s).\n"
                "Do you want to quit without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Save window geometry
        self.settings_manager.save_window_geometry(
            self.saveGeometry(),
            self.saveState()
        )
        
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle global key press events"""
        if event.key() == Qt.Key.Key_Escape:
            if self.search_bar.isVisible():
                self._hide_search_bar()
            else:
                # Close app on escape if no search bar
                self.close()
        else:
            super().keyPressEvent(event)


# ============================================================================
# Application Entry Point
# ============================================================================

def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName(AppConfig.APP_NAME)
    app.setApplicationVersion(AppConfig.VERSION)
    app.setOrganizationName("RichTextNotepad")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()