from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from typing import Optional, List
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from config.app_config import AppConfig
from config.styles import StyleSheet
from models.document_tab import DocumentTab
from services.file_operations import FileOperations, FileLoadWorker
from services.settings_manager import SettingsManager
from widgets.search_bar import SearchBar
from widgets.status_bar import StatusBarWidget
from widgets.table_dialog import TablePropertiesDialog

from app.controllers.formatting_controller import FormattingController
from app.controllers.toolbar_controller import ToolbarController
from app.controllers.context_menu_controller import ContextMenuController


class MainWindow(QMainWindow):
    """Main application window with tabbed document interface"""

    def __init__(self):
        super().__init__()

        self.tabs: List[DocumentTab] = []
        self.tab_counter = 1
        self.settings_manager = SettingsManager()
        self._is_restoring_session = False
        self._restore_pending = 0
        self._restore_active_index = -1
        self._load_threads: dict = {}  # filepath -> (QThread, FileLoadWorker), keeps them alive

        self._setup_ui()
        self._setup_shortcuts()
        self._setup_timers()
        self._restore_settings()
        self._restore_session()

    def _setup_ui(self):
        """Initialize the user interface"""
        self._dark_theme = self.settings_manager.get_theme()

        # ── controllers ──────────────────────────────────────────────
        self.fmt_ctrl = FormattingController(
            get_current_tab=self._get_current_tab,
            get_dark_theme=lambda: self._dark_theme,
            parent_widget=self,
        )
        self.toolbar_ctrl = ToolbarController(self.fmt_ctrl, self)
        self.ctx_menu_ctrl = ContextMenuController(
            set_alignment_fn=self.set_alignment,
            parent_widget=self,
        )

        tokens = StyleSheet.toolbar_tokens(self._dark_theme)
        self._toolbar_sep_color = tokens["sep_color"]

        self.setStyleSheet(StyleSheet.get(self._dark_theme))
        self.setWindowTitle(AppConfig.APP_NAME)
        self.setMinimumSize(QSize(800, 600))
        self.resize(QSize(1200, 700))

        self._create_menu_bar()

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Build toolbar via controller
        self.format_toolbar = self.toolbar_ctrl.build(self._toolbar_sep_color)
        self.toolbar_ctrl.apply_theme(self._dark_theme)
        layout.addWidget(self.format_toolbar)

        self._create_tab_widget()
        layout.addWidget(self.tab_widget)

        self.search_bar = SearchBar()
        self.search_bar.find_next_requested.connect(lambda: self._find_text(backward=False))
        self.search_bar.find_prev_requested.connect(lambda: self._find_text(backward=True))
        self.search_bar.close_requested.connect(self._hide_search_bar)
        self.search_bar.search_input.textChanged.connect(lambda: self._find_text(backward=False))
        self.search_bar.case_sensitive_cb.toggled.connect(lambda: self._find_text(backward=False))
        self.search_bar.setVisible(False)
        layout.addWidget(self.search_bar)

        self.setCentralWidget(central_widget)

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

        print_action = QAction("&Print...", self)
        print_action.setShortcut(QKeySequence.StandardKey.Print)
        print_action.triggered.connect(self._print_document)
        file_menu.addAction(print_action)

        export_pdf_action = QAction("Export as &PDF...", self)
        export_pdf_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_pdf_action.triggered.connect(self._export_to_pdf)
        file_menu.addAction(export_pdf_action)

        file_menu.addSeparator()

        close_tab_action = QAction("&Close Tab", self)
        close_tab_action.setShortcut(QKeySequence.StandardKey.Close)
        close_tab_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_tab_action)

        duplicate_tab_action = QAction("&Duplicate Tab", self)
        duplicate_tab_action.setShortcut(QKeySequence("Ctrl+Shift+K"))
        duplicate_tab_action.triggered.connect(self.duplicate_tab)
        file_menu.addAction(duplicate_tab_action)

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

        replace_action = QAction("&Replace...", self)
        replace_action.triggered.connect(self._show_search_bar_with_replace)
        edit_menu.addAction(replace_action)

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

        align_left_action = QAction("Align &Left", self)
        align_left_action.setShortcut(QKeySequence("Ctrl+L"))
        align_left_action.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        format_menu.addAction(align_left_action)

        align_center_action = QAction("&Center", self)
        align_center_action.setShortcut(QKeySequence("Ctrl+E"))
        align_center_action.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignHCenter))
        format_menu.addAction(align_center_action)

        align_right_action = QAction("Align &Right", self)
        align_right_action.setShortcut(QKeySequence("Ctrl+R"))
        align_right_action.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        format_menu.addAction(align_right_action)

        align_justify_action = QAction("&Justify", self)
        align_justify_action.setShortcut(QKeySequence("Ctrl+J"))
        align_justify_action.triggered.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignJustify))
        format_menu.addAction(align_justify_action)

        format_menu.addSeparator()

        bullet_list_action = QAction("&Bullet List", self)
        bullet_list_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        bullet_list_action.triggered.connect(self.toggle_bullet_list)
        format_menu.addAction(bullet_list_action)

        numbered_list_action = QAction("&Numbered List", self)
        numbered_list_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        numbered_list_action.triggered.connect(self.toggle_numbered_list)
        format_menu.addAction(numbered_list_action)

        format_menu.addSeparator()

        table_action = QAction("Insert &Table...", self)
        table_action.setShortcut(QKeySequence("Ctrl+T"))
        table_action.triggered.connect(self.insert_table)
        format_menu.addAction(table_action)

        table_props_action = QAction("Table &Properties...", self)
        table_props_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        table_props_action.triggered.connect(self.show_table_properties)
        format_menu.addAction(table_props_action)

        format_menu.addSeparator()

        clear_format_action = QAction("&Clear Formatting", self)
        clear_format_action.setShortcut(QKeySequence("Ctrl+\\"))
        clear_format_action.triggered.connect(self.clear_formatting)
        format_menu.addAction(clear_format_action)

        format_menu.addSeparator()

        superscript_action = QAction("Superscript", self)
        superscript_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        superscript_action.triggered.connect(self._apply_superscript)
        format_menu.addAction(superscript_action)

        subscript_action = QAction("Subscript", self)
        subscript_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        subscript_action.triggered.connect(self._apply_subscript)
        format_menu.addAction(subscript_action)

        format_menu.addSeparator()

        code_block_action = QAction("Code Block", self)
        code_block_action.setShortcut(QKeySequence("Ctrl+`"))
        code_block_action.triggered.connect(self._insert_code_block)
        format_menu.addAction(code_block_action)

        format_menu.addSeparator()

        line_spacing_menu = format_menu.addMenu("Line Spacing")

        single_spacing = QAction("Single", self)
        single_spacing.triggered.connect(lambda: self._set_line_spacing(1.0))
        line_spacing_menu.addAction(single_spacing)

        spacing_15 = QAction("1.5 Lines", self)
        spacing_15.triggered.connect(lambda: self._set_line_spacing(1.5))
        line_spacing_menu.addAction(spacing_15)

        double_spacing = QAction("Double", self)
        double_spacing.triggered.connect(lambda: self._set_line_spacing(2.0))
        line_spacing_menu.addAction(double_spacing)

        view_menu = menu_bar.addMenu("&View")

        self.theme_action = QAction("Light Theme", self)
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(not self._dark_theme)
        self.theme_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.theme_action)

    def _toggle_theme(self, checked: bool):
        """Switch between dark and light themes and persist the choice."""
        self._dark_theme = not checked
        self.setStyleSheet(StyleSheet.get(self._dark_theme))
        self.toolbar_ctrl.apply_theme(self._dark_theme)
        self.theme_action.setText("Light Theme")
        self.settings_manager.save_theme(self._dark_theme)

    def duplicate_tab(self):
        """Duplicate the current tab's content into a new tab."""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        html = current_tab.get_content_html()
        new_name = (current_tab.name + " (copy)") if not current_tab.current_file \
                   else (current_tab.current_file.stem + " (copy)")
        doc_tab = DocumentTab(new_name)
        doc_tab.set_content(html, is_html=True)
        # set_content() marks the document unmodified, but a duplicate is a
        # new, never-saved document - flag it modified so the unsaved (●)
        # indicator shows immediately, same as any other new tab.
        doc_tab.text_edit.document().setModified(True)
        self._wire_tab(doc_tab)
        index = self.tab_widget.addTab(doc_tab.text_edit, doc_tab.get_display_name())
        self.tabs.append(doc_tab)
        self.tab_widget.setCurrentIndex(index)
        self.tab_counter += 1
        doc_tab.text_edit.setFocus()

    def _create_tab_widget(self):
        """Create tab widget for multiple documents"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._tab_changed)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(5, 0, 5, 5)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        plus_button = QToolButton()
        plus_button.setText("+")
        plus_button.setStyleSheet("""
            QToolButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                font-size: 16pt;
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

        button_layout.addWidget(plus_button)
        self.tab_widget.setCornerWidget(button_container, Qt.Corner.TopRightCorner)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        for i in range(1, 10):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(lambda num=i: self._switch_to_tab(num))

        find_next_shortcut = QShortcut(QKeySequence("F3"), self)
        find_next_shortcut.activated.connect(lambda: self._find_text(backward=False))

        find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self)
        find_prev_shortcut.activated.connect(lambda: self._find_text(backward=True))

        self.search_bar.replace_requested.connect(self._replace_text)
        self.search_bar.replace_all_requested.connect(self._replace_all_text)

        replace_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        replace_shortcut.activated.connect(self._show_search_bar_with_replace)

    def _setup_timers(self):
        """Setup periodic timers for status updates and autosave"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_bar)
        self.status_timer.start(100)

        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self._autosave_all)
        self.autosave_timer.start(AppConfig.AUTOSAVE_INTERVAL_MS)

    def _autosave_all(self):
        """Autosave all modified tabs that have an existing file path"""
        saved_any = False
        for tab in self.tabs:
            if tab.is_modified and tab.current_file and tab.current_file.exists():
                try:
                    is_html = tab.current_file.suffix.lower() == '.html'
                    content = tab.get_content_html() if is_html else tab.get_content_plain()
                    FileOperations.write_file(tab.current_file, content, is_html)
                    tab.mark_saved()
                    self._update_tab_title(tab)
                    saved_any = True
                except Exception:
                    pass  # Silent fail — autosave is best-effort
        if saved_any:
            self.statusBar().showMessage("Autosaved", 2000)

    def _restore_settings(self):
        """Restore saved application settings"""
        if not self.settings_manager.restore_window_geometry(self):
            screen = QApplication.primaryScreen().geometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2,
            )

    def _restore_session(self):
        """Restore previously open tabs from last session"""
        open_tabs, active_index = self.settings_manager.get_open_tabs()

        if not open_tabs:
            self.new_tab()
            return

        # Loads happen on background threads, so we can't just check
        # tab_widget.count() right after kicking them off - track how many
        # are still outstanding and finish restoring once they've all
        # reported back (success or failure).
        self._is_restoring_session = True
        self._restore_pending = len(open_tabs)
        self._restore_active_index = active_index

        for filepath in open_tabs:
            self._load_file_async(Path(filepath))

    def _on_restore_step_done(self):
        """Called once per restored tab (success or failure) during session restore"""
        self._restore_pending -= 1
        if self._restore_pending > 0:
            return

        self._is_restoring_session = False
        if 0 <= self._restore_active_index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(self._restore_active_index)
        if self.tab_widget.count() == 0:
            self.new_tab()

    def _save_session(self):
        """Save currently open tabs for next session"""
        open_tabs = [str(tab.current_file) for tab in self.tabs if tab.current_file]
        active_index = self.tab_widget.currentIndex()
        self.settings_manager.save_open_tabs(open_tabs, active_index)

    # ── Tab management ────────────────────────────────────────────────

    def new_tab(self):
        """Create a new document tab"""
        tab_name = f"Untitled {self.tab_counter}"
        doc_tab = DocumentTab(tab_name)
        self._wire_tab(doc_tab)
        index = self.tab_widget.addTab(doc_tab.text_edit, doc_tab.get_display_name())
        self.tabs.append(doc_tab)
        self.tab_widget.setCurrentIndex(index)
        self.tab_counter += 1
        doc_tab.text_edit.setFocus()

    def _wire_tab(self, doc_tab: DocumentTab):
        """Connect signals for a newly created or loaded DocumentTab."""
        doc_tab.text_edit.textChanged.connect(self._on_text_changed)
        doc_tab.text_edit.cursorPositionChanged.connect(self._update_format_buttons)
        doc_tab.text_edit.cursorPositionChanged.connect(self._update_status_bar)
        doc_tab.text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        doc_tab.text_edit.customContextMenuRequested.connect(
            lambda pos, te=doc_tab.text_edit: self.ctx_menu_ctrl.show(pos, te)
        )

    def close_tab(self, index: int):
        """Close tab at given index"""
        if self.tab_widget.count() <= 1:
            return

        doc_tab = self.tabs[index]

        if doc_tab.is_modified:
            reply = self._confirm_close_modified(doc_tab)
            if reply == QMessageBox.StandardButton.Save:
                if not self._save_document(doc_tab):
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.tab_widget.removeTab(index)
        self.tabs.pop(index)

        if not self._is_restoring_session:
            self._save_session()

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

            if not self._is_restoring_session:
                self._save_session()

    def _switch_to_tab(self, tab_number: int):
        """Switch to tab by number (1-9)"""
        if tab_number == 9:
            last_index = self.tab_widget.count() - 1
            if last_index >= 0:
                self.tab_widget.setCurrentIndex(last_index)
        else:
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

    # ── File operations ───────────────────────────────────────────────

    def open_file(self, filepath: Optional[str] = None):
        """Open a file in a new tab"""
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Open File", "", AppConfig.FILE_FILTERS
            )

        if not filepath:
            return

        file_path = Path(filepath)

        for i, tab in enumerate(self.tabs):
            if tab.current_file == file_path:
                self.tab_widget.setCurrentIndex(i)
                self.statusBar().showMessage(f"File already open: {file_path.name}", 3000)
                return

        self._load_file_async(file_path)

    def _load_file_async(self, filepath: Path):
        """
        Load a file on a background QThread so reading it never blocks the
        UI, regardless of file size. Completion/failure are delivered back
        via signals and handled on the main thread.
        """
        if str(filepath) in self._load_threads:
            # Already loading this file; don't start a second read.
            return

        self.statusBar().showMessage(f"Loading {filepath.name}...")

        thread = QThread(self)
        worker = FileLoadWorker(filepath)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(lambda content, is_html: self._on_file_loaded(filepath, content, is_html))
        worker.failed.connect(lambda msg: self._on_file_load_failed(filepath, msg))
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(lambda: self._load_threads.pop(str(filepath), None))

        self._load_threads[str(filepath)] = (thread, worker)
        thread.start()

    def _on_file_loaded(self, filepath: Path, content: str, is_html: bool):
        """Handle a successful background file load (runs on the main thread)."""
        doc_tab = DocumentTab()
        doc_tab.set_content(content, is_html)
        doc_tab.current_file = filepath

        self._wire_tab(doc_tab)

        index = self.tab_widget.addTab(doc_tab.text_edit, doc_tab.get_display_name())
        self.tabs.append(doc_tab)
        self.tab_widget.setCurrentIndex(index)

        self.settings_manager.add_recent_file(str(filepath))
        self._update_recent_files_menu()

        if self._is_restoring_session:
            self._on_restore_step_done()
        else:
            self._save_session()

        self.statusBar().showMessage(f"Opened: {filepath.name}", 3000)

    def _on_file_load_failed(self, filepath: Path, message: str):
        """Handle a failed background file load (runs on the main thread)."""
        QMessageBox.critical(
            self, "Error Opening File",
            f"Could not open file:\n{filepath}\n\nError: {message}"
        )
        self.statusBar().clearMessage()

        if self._is_restoring_session:
            self._on_restore_step_done()

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
            self, "Save File As",
            doc_tab.current_file.name if doc_tab.current_file else "untitled.html",
            AppConfig.FILE_FILTERS,
        )

        if not filename:
            return False

        filepath = Path(filename)
        if not filepath.suffix:
            filepath = filepath.with_suffix(AppConfig.DEFAULT_EXTENSION)

        doc_tab.current_file = filepath
        return self._save_document(doc_tab)

    def _save_document(self, doc_tab: DocumentTab) -> bool:
        """Save a document to disk"""
        if not doc_tab.current_file:
            return self.save_as(doc_tab)

        try:
            is_html = doc_tab.current_file.suffix.lower() == '.html'
            content = doc_tab.get_content_html() if is_html else doc_tab.get_content_plain()

            FileOperations.write_file(doc_tab.current_file, content, is_html)

            doc_tab.mark_saved()
            self._update_tab_title(doc_tab)
            self._update_window_title(doc_tab)

            self.settings_manager.add_recent_file(str(doc_tab.current_file))
            self._update_recent_files_menu()

            self._save_session()

            self.statusBar().showMessage(f"Saved: {doc_tab.current_file.name}", 3000)
            return True

        except Exception as e:
            QMessageBox.critical(
                self, "Error Saving File",
                f"Could not save file:\n{doc_tab.current_file}\n\nError: {str(e)}"
            )
            return False

    def delete_file(self):
        """Delete the current file from disk"""
        current_tab = self._get_current_tab()
        if not current_tab or not current_tab.current_file:
            QMessageBox.information(self, "Delete File",
                                    "No file to delete. Please save the document first.")
            return

        filepath = current_tab.current_file
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to permanently delete this file?\n\n{filepath.name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            FileOperations.delete_file(filepath)
            self.statusBar().showMessage(f"Deleted: {filepath.name}", 3000)

            current_index = self.tab_widget.currentIndex()
            self.tab_widget.removeTab(current_index)
            self.tabs.pop(current_index)

            if self.tab_widget.count() == 0:
                self.new_tab()

            self._save_session()

        except Exception as e:
            QMessageBox.critical(self, "Error Deleting File",
                                 f"Could not delete file:\n{filepath}\n\nError: {str(e)}")

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

    # ── Formatting – thin delegating wrappers (called by menus/shortcuts) ──

    def toggle_bold(self):
        self.fmt_ctrl.toggle_bold()

    def toggle_italic(self):
        self.fmt_ctrl.toggle_italic()

    def toggle_underline(self):
        self.fmt_ctrl.toggle_underline()

    def toggle_strikethrough(self):
        self.fmt_ctrl.toggle_strikethrough()

    def _apply_superscript(self):
        self.fmt_ctrl.apply_superscript()

    def _apply_subscript(self):
        self.fmt_ctrl.apply_subscript()

    def clear_formatting(self):
        self.fmt_ctrl.clear_formatting()

    def set_alignment(self, alignment: Qt.AlignmentFlag):
        self.fmt_ctrl.set_alignment(alignment)
        self._update_format_buttons()

    def _increase_indent(self):
        self.fmt_ctrl.increase_indent()

    def _decrease_indent(self):
        self.fmt_ctrl.decrease_indent()

    def _set_line_spacing(self, spacing: float):
        self.fmt_ctrl.set_line_spacing(spacing)

    def toggle_bullet_list(self):
        self.fmt_ctrl.toggle_bullet_list()

    def toggle_numbered_list(self):
        self.fmt_ctrl.toggle_numbered_list()

    def insert_table(self):
        self.fmt_ctrl.insert_table()

    def show_table_properties(self):
        self.fmt_ctrl.show_table_properties()

    def add_link(self):
        self.fmt_ctrl.add_link()

    def _insert_code_block(self):
        self.fmt_ctrl.insert_code_block()

    def _insert_horizontal_line(self):
        self.fmt_ctrl.insert_horizontal_line()

    def _insert_image(self):
        self.fmt_ctrl.insert_image()

    def _change_font_family(self, font: QFont):
        self.fmt_ctrl.change_font_family(font)

    def _change_font_size(self, size: str):
        self.fmt_ctrl.change_font_size(size)

    def change_text_color(self):
        self.fmt_ctrl.change_text_color(self.toolbar_ctrl.refresh_text_color_btn)

    def change_background_color(self):
        self.fmt_ctrl.change_background_color(self.toolbar_ctrl.refresh_bg_color_btn)

    # ── Toolbar state sync ─────────────────────────────────────────────

    def _update_format_buttons(self):
        """Update formatting button states based on current cursor position"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        fmt = current_tab.text_edit.currentCharFormat()
        tc = self.toolbar_ctrl

        for widget in (tc.bold_btn, tc.italic_btn, tc.underline_btn,
                       tc.strike_btn, tc.superscript_btn, tc.subscript_btn,
                       tc.font_combo, tc.size_combo,
                       tc.align_left_btn, tc.align_center_btn,
                       tc.align_right_btn, tc.align_just_btn):
            widget.blockSignals(True)

        tc.bold_btn.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        tc.italic_btn.setChecked(fmt.fontItalic())
        tc.underline_btn.setChecked(fmt.fontUnderline())
        tc.strike_btn.setChecked(fmt.fontStrikeOut())

        va = fmt.verticalAlignment()
        tc.superscript_btn.setChecked(va == QTextCharFormat.VerticalAlignment.AlignSuperScript)
        tc.subscript_btn.setChecked(va == QTextCharFormat.VerticalAlignment.AlignSubScript)

        ps = fmt.fontPointSize()
        if ps and ps > 0:
            tc.size_combo.setCurrentText(str(int(ps)))

        alignment = current_tab.text_edit.alignment()
        tc.align_left_btn.setChecked(alignment in (Qt.AlignmentFlag.AlignLeft,
                                                    Qt.AlignmentFlag.AlignAbsolute))
        tc.align_center_btn.setChecked(alignment == Qt.AlignmentFlag.AlignHCenter)
        tc.align_right_btn.setChecked(alignment == Qt.AlignmentFlag.AlignRight)
        tc.align_just_btn.setChecked(alignment == Qt.AlignmentFlag.AlignJustify)

        for widget in (tc.bold_btn, tc.italic_btn, tc.underline_btn,
                       tc.strike_btn, tc.superscript_btn, tc.subscript_btn,
                       tc.font_combo, tc.size_combo,
                       tc.align_left_btn, tc.align_center_btn,
                       tc.align_right_btn, tc.align_just_btn):
            widget.blockSignals(False)

    # ── Search / replace ──────────────────────────────────────────────

    def _show_search_bar(self):
        if self.search_bar.isVisible():
            self._hide_search_bar()
        else:
            self.search_bar.setVisible(True)
            self.search_bar.focus_input()

    def _hide_search_bar(self):
        self.search_bar.setVisible(False)
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.text_edit.setExtraSelections([])
            cursor = current_tab.text_edit.textCursor()
            cursor.clearSelection()
            current_tab.text_edit.setTextCursor(cursor)
            current_tab.text_edit.setFocus()

    def _find_text(self, backward: bool = False):
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        search_text = self.search_bar.get_search_text()
        if not search_text:
            current_tab.text_edit.setExtraSelections([])
            self.search_bar.update_counter(0, 0)
            return

        flags = QTextDocument.FindFlag(0)
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        if self.search_bar.is_case_sensitive():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        found = current_tab.text_edit.find(search_text, flags)

        if not found:
            cursor = current_tab.text_edit.textCursor()
            if backward:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            current_tab.text_edit.setTextCursor(cursor)
            current_tab.text_edit.find(search_text, flags)

        self._highlight_all_matches(search_text)

    def _highlight_all_matches(self, search_text: str):
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        extra_selections = []
        text = current_tab.text_edit.toPlainText()
        current_pos = current_tab.text_edit.textCursor().selectionStart()

        if self.search_bar.is_case_sensitive():
            search_func = text.find
        else:
            text_lower = text.lower()
            search_text_lower = search_text.lower()
            search_func = text_lower.find
            text = text_lower
            search_text = search_text_lower

        pos = 0
        match_count = 0
        current_match = 0

        while True:
            pos = search_func(search_text, pos)
            if pos == -1:
                break

            match_count += 1
            if pos <= current_pos:
                current_match = match_count

            selection = QTextEdit.ExtraSelection()
            cursor = current_tab.text_edit.textCursor()
            cursor.setPosition(pos)
            cursor.setPosition(pos + len(search_text), QTextCursor.MoveMode.KeepAnchor)
            selection.cursor = cursor
            selection.format.setBackground(QBrush(QColor("#FFD700")))
            selection.format.setForeground(QBrush(QColor("#000000")))
            extra_selections.append(selection)

            pos += len(search_text)

        current_tab.text_edit.setExtraSelections(extra_selections)
        self.search_bar.update_counter(current_match, match_count)

    def _show_search_bar_with_replace(self):
        if self.search_bar.isVisible() and self.search_bar.replace_widget.isVisible():
            self.search_bar.replace_widget.setVisible(False)
            self.search_bar.toggle_replace_btn.setChecked(False)
            self.search_bar.search_input.setFocus()
        else:
            self._show_search_bar()
            self.search_bar.show_replace = True
            self.search_bar.replace_widget.setVisible(True)
            self.search_bar.toggle_replace_btn.setChecked(True)
            self.search_bar.replace_input.setFocus()

    def _replace_text(self):
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        search_text = self.search_bar.get_search_text()
        replace_text = self.search_bar.get_replace_text()

        if not search_text:
            QMessageBox.warning(self, "Replace", "Please enter text to find")
            return

        cursor = current_tab.text_edit.textCursor()
        flags = QTextDocument.FindFlag(0)
        if self.search_bar.is_case_sensitive():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if cursor.hasSelection():
            selected = cursor.selectedText()
            matches = (selected == search_text) if self.search_bar.is_case_sensitive() \
                     else (selected.lower() == search_text.lower())
            if matches:
                cursor.insertText(replace_text)
                current_tab.text_edit.setTextCursor(cursor)
                self._find_text(backward=False)
                return

        if current_tab.text_edit.find(search_text, flags):
            cursor = current_tab.text_edit.textCursor()
            cursor.insertText(replace_text)
            current_tab.text_edit.setTextCursor(cursor)
            self._find_text(backward=False)

    def _replace_all_text(self):
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        search_text = self.search_bar.get_search_text()
        replace_text = self.search_bar.get_replace_text()

        if not search_text:
            QMessageBox.warning(self, "Replace All", "Please enter text to find")
            return

        cursor = current_tab.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        current_tab.text_edit.setTextCursor(cursor)

        flags = QTextDocument.FindFlag(0)
        if self.search_bar.is_case_sensitive():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        count = 0
        while current_tab.text_edit.find(search_text, flags):
            cursor = current_tab.text_edit.textCursor()
            cursor.insertText(replace_text)
            current_tab.text_edit.setTextCursor(cursor)
            count += 1

        if count > 0:
            QMessageBox.information(self, "Replace All",
                                    f"Replaced {count} occurrence{'s' if count != 1 else ''}")
        else:
            QMessageBox.information(self, "Replace All", "No matches found")

        self._highlight_all_matches(replace_text)

    # ── Print / PDF ───────────────────────────────────────────────────

    def _export_to_pdf(self):
        current_tab = self._get_current_tab()
        if not current_tab:
            QMessageBox.warning(self, "Export PDF", "No document to export")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("PDF Export Options")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Select font size for PDF:"))

        scale_combo = QComboBox()
        scale_combo.addItems(["Normal (10pt)", "Large (12pt)", "Extra Large (14pt)", "Huge (16pt)"])
        scale_combo.setCurrentIndex(1)
        layout.addWidget(scale_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        scale_index = scale_combo.currentIndex()
        font_sizes = [10, 12, 14, 16]
        font_size = font_sizes[scale_index]

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export as PDF",
            current_tab.current_file.stem if current_tab.current_file else "document",
            "PDF Files (*.pdf)",
        )
        if not filename:
            return

        if not filename.endswith('.pdf'):
            filename += '.pdf'

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filename)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        margins = QMarginsF(25.4, 25.4, 25.4, 25.4)
        printer.setPageMargins(margins, QPageLayout.Unit.Millimeter)

        original_html = current_tab.get_content_html()
        css_style = f"""
        <style>
            body {{ font-size: {font_size}pt; line-height: 1.5; }}
            h1 {{ font-size: {font_size + 14}pt; }}
            h2 {{ font-size: {font_size + 10}pt; }}
            h3 {{ font-size: {font_size + 8}pt; }}
            p {{ font-size: {font_size}pt; }}
            pre, code {{ font-size: {font_size - 1}pt; }}
        </style>
        """
        if '<head>' in original_html:
            modified_html = original_html.replace('<head>', f'<head>{css_style}')
        elif '<html>' in original_html:
            modified_html = original_html.replace('<html>', f'<html><head>{css_style}</head>')
        else:
            modified_html = f'<html><head>{css_style}</head><body>{original_html}</body></html>'

        temp_doc = QTextDocument()
        temp_doc.setHtml(modified_html)
        temp_doc.print(printer)

        QMessageBox.information(
            self, "Success",
            f"PDF exported successfully to:\n{filename}\n\nFont size: {font_size}pt"
        )

    def _print_document(self):
        current_tab = self._get_current_tab()
        if not current_tab:
            QMessageBox.warning(self, "Print", "No document to print")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        margins = QMarginsF(25.4, 25.4, 25.4, 25.4)
        printer.setPageMargins(margins, QPageLayout.Unit.Millimeter)

        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() == QDialog.DialogCode.Accepted:
            original_html = current_tab.get_content_html()
            css_style = """
            <style>
                body { font-size: 12pt; line-height: 1.5; }
                h1 { font-size: 24pt; }
                h2 { font-size: 20pt; }
                h3 { font-size: 18pt; }
                p { font-size: 12pt; }
            </style>
            """
            if '<head>' in original_html:
                modified_html = original_html.replace('<head>', f'<head>{css_style}')
            elif '<html>' in original_html:
                modified_html = original_html.replace('<html>', f'<html><head>{css_style}</head>')
            else:
                modified_html = f'<html><head>{css_style}</head><body>{original_html}</body></html>'

            temp_doc = QTextDocument()
            temp_doc.setHtml(modified_html)
            temp_doc.print(printer)
            QMessageBox.information(self, "Print", "Document sent to printer successfully")

    # ── Status bar ────────────────────────────────────────────────────

    def _update_status_bar(self):
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        self.status_widget.update_file(current_tab.get_file_path())

        cursor = current_tab.text_edit.textCursor()
        block = cursor.block()
        line = block.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.status_widget.update_cursor(line, col)

        text = current_tab.get_content_plain()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.status_widget.update_word_count(words, chars)

    # ── Event handlers ────────────────────────────────────────────────

    def _on_text_changed(self):
        current_tab = self._get_current_tab()
        if current_tab:
            self._update_tab_title(current_tab)
            self._update_window_title(current_tab)

    def _confirm_close_modified(self, doc_tab: DocumentTab) -> QMessageBox.StandardButton:
        filename = doc_tab.get_display_name().replace('●', '').strip()
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            f"Do you want to save changes to '{filename}'?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        return reply

    def closeEvent(self, event):
        modified_tabs = [tab for tab in self.tabs if tab.is_modified]
        if modified_tabs:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                f"You have {len(modified_tabs)} unsaved document(s).\n"
                "Do you want to quit without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        self.settings_manager.save_window_geometry(
            self.saveGeometry(),
            self.saveState(),
        )
        self._save_session()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.search_bar.isVisible():
                self._hide_search_bar()
            else:
                self.close()
        else:
            super().keyPressEvent(event)

    def _undo(self):
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.text_edit.undo()

    def _redo(self):
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.text_edit.redo()
