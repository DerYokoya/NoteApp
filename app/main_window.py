from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from typing import Optional, List
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from config.app_config import AppConfig
from config.styles import StyleSheet
from models.document_tab import DocumentTab
from services.file_operations import FileOperations
from services.settings_manager import SettingsManager
from widgets.search_bar import SearchBar
from widgets.status_bar import StatusBarWidget
from widgets.table_dialog import TablePropertiesDialog


class MainWindow(QMainWindow):
    """Main application window with tabbed document interface"""
    
    def __init__(self):
        super().__init__()
        
        self.tabs: List[DocumentTab] = []
        self.tab_counter = 1
        self.settings_manager = SettingsManager()
        self._is_restoring_session = False
        
        self._setup_ui()
        self._setup_shortcuts()
        self._setup_timers()
        self._restore_settings()
        self._restore_session()
    
    def _setup_ui(self):
        """Initialize the user interface"""
        self.setStyleSheet(StyleSheet.DARK_THEME)
        self.setWindowTitle(AppConfig.APP_NAME)
        self.setMinimumSize(QSize(800, 600))
        self.resize(QSize(1200, 700))
        
        self._create_menu_bar()
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._create_formatting_toolbar()
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
    
    def _make_tool_btn(self, text: str, tooltip: str, checkable: bool = False,
                       width: int = 32, font_override: QFont = None) -> QPushButton:
        """Create a clean, consistently sized toolbar button"""
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCheckable(checkable)
        btn.setFixedSize(width, 28)
        if font_override:
            btn.setFont(font_override)
        return btn

    def _create_formatting_toolbar(self):
        """Create two-row formatting toolbar that looks like a real app"""
        # We use a plain QWidget with two QHBoxLayout rows instead of QToolBar
        # so we have full control over spacing and appearance.
        self.format_toolbar = QWidget()
        self.format_toolbar.setObjectName("FormatToolbar")
        self.format_toolbar.setStyleSheet("""
            QWidget#FormatToolbar {
                background-color: #383838;
                border-bottom: 1px solid #222222;
            }
        """)

        outer = QVBoxLayout(self.format_toolbar)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(8)  # More spacing between rows

        row1 = QHBoxLayout()
        row1.setSpacing(2)
        row2 = QHBoxLayout()
        row2.setSpacing(2)
        outer.addLayout(row1)
        outer.addLayout(row2)

        def sep(row):
            line = QFrame()
            line.setFrameShape(QFrame.Shape.VLine)
            line.setStyleSheet("color: #555555; max-width: 1px; margin: 2px 4px;")
            row.addWidget(line)

        # ── ROW 1: Font family | Font size | Bold Italic Underline Strike | Colors | Link ──

        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setFixedWidth(160)
        self.font_combo.setFixedHeight(28)
        self.font_combo.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        self.font_combo.currentFontChanged.connect(self._change_font_family)
        row1.addWidget(self.font_combo)

        row1.addSpacing(4)

        # Font size — editable combo with better visibility
        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.setFixedWidth(80)  # Increased from 58
        self.size_combo.setFixedHeight(28)
        self.size_combo.addItems(['8','9','10','11','12','14','16','18','20','24','28','36','48','72'])
        self.size_combo.setCurrentText('12')
        # Make font size text larger and more readable
        sz_font = QFont()
        sz_font.setPointSize(10)
        self.size_combo.setFont(sz_font)
        if self.size_combo.lineEdit():
            self.size_combo.lineEdit().setFont(sz_font)
        self.size_combo.currentTextChanged.connect(self._change_font_size)
        self.size_combo.lineEdit().returnPressed.connect(
            lambda: self._change_font_size(self.size_combo.currentText())
        )
        row1.addWidget(self.size_combo)

        sep(row1)

        # Text Styles dropdown
        self.style_combo = QComboBox()
        self.style_combo.setFixedWidth(130)
        self.style_combo.setFixedHeight(28)
        self.style_combo.addItems([
            'Normal',
            'Title',
            'Subtitle',
            'Heading 1',
            'Heading 2',
            'Heading 3',
            'Heading 4',
            'Heading 5',
            'Heading 6',
        ])
        self.style_combo.currentTextChanged.connect(self._apply_text_style)
        row1.addWidget(self.style_combo)

        sep(row1)

        # Bold
        bold_font = QFont("Georgia", 10, QFont.Weight.Bold)
        self.bold_btn = self._make_tool_btn("B", "Bold (Ctrl+B)", checkable=True,
                                            font_override=bold_font)
        self.bold_btn.clicked.connect(self.toggle_bold)
        row1.addWidget(self.bold_btn)

        # Italic
        italic_font = QFont("Georgia", 10)
        italic_font.setItalic(True)
        self.italic_btn = self._make_tool_btn("I", "Italic (Ctrl+I)", checkable=True,
                                              font_override=italic_font)
        self.italic_btn.clicked.connect(self.toggle_italic)
        row1.addWidget(self.italic_btn)

        # Underline
        ul_font = QFont("Arial", 9)
        ul_font.setUnderline(True)
        self.underline_btn = self._make_tool_btn("U", "Underline (Ctrl+U)", checkable=True,
                                                 font_override=ul_font)
        self.underline_btn.clicked.connect(self.toggle_underline)
        row1.addWidget(self.underline_btn)

        # Strikethrough
        st_font = QFont("Arial", 9)
        st_font.setStrikeOut(True)
        self.strike_btn = self._make_tool_btn("S", "Strikethrough", checkable=True,
                                              font_override=st_font)
        self.strike_btn.clicked.connect(self.toggle_strikethrough)
        row1.addWidget(self.strike_btn)

        # Superscript
        sup_font = QFont("Arial", 8)
        self.superscript_btn = self._make_tool_btn("x²", "Superscript (Ctrl+Shift+P)", checkable=True,
                                                   font_override=sup_font, width=32)
        self.superscript_btn.clicked.connect(self._apply_superscript)
        row1.addWidget(self.superscript_btn)

        # Subscript
        sub_font = QFont("Arial", 8)
        self.subscript_btn = self._make_tool_btn("x₂", "Subscript (Ctrl+Shift+B)", checkable=True,
                                                 font_override=sub_font, width=32)
        self.subscript_btn.clicked.connect(self._apply_subscript)
        row1.addWidget(self.subscript_btn)

        # Code Block
        code_font = QFont("Courier", 8)
        self.code_block_btn = self._make_tool_btn("<>", "Code Block (Ctrl+`)", checkable=False,
                                                  font_override=code_font, width=32)
        self.code_block_btn.clicked.connect(self._insert_code_block)
        row1.addWidget(self.code_block_btn)

        sep(row1)

        # Text colour — shows a small coloured underline like Word
        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setFixedSize(32, 28)
        self.text_color_btn.setToolTip("Text Color")
        self._current_text_color = QColor("#FFFFFF")
        self._refresh_text_color_btn()
        self.text_color_btn.clicked.connect(self.change_text_color)
        row1.addWidget(self.text_color_btn)

        # Highlight colour
        self.bg_color_btn = QPushButton("ab")
        self.bg_color_btn.setFixedSize(34, 28)
        self.bg_color_btn.setToolTip("Highlight Color")
        self._current_bg_color = QColor("#FFFF00")
        self._refresh_bg_color_btn()
        self.bg_color_btn.clicked.connect(self.change_background_color)
        row1.addWidget(self.bg_color_btn)

        sep(row1)

        # Link
        self.link_btn = self._make_tool_btn("🔗", "Insert Link (Ctrl+K)", width=34)
        self.link_btn.clicked.connect(self.add_link)
        row1.addWidget(self.link_btn)

        sep(row1)

        # Clear formatting
        self.clear_btn = self._make_tool_btn("Tx", "Clear Formatting (Ctrl+\\)", width=34)
        self.clear_btn.setStyleSheet("""
            QPushButton { font-weight: bold; color: #CCCCCC; }
            QPushButton:hover { background-color: #5A5A5A; }
        """)
        self.clear_btn.clicked.connect(self.clear_formatting)
        row1.addWidget(self.clear_btn)

        row1.addStretch()

        # ── ROW 2: Alignment | Lists | Table | Indent ──

        # Alignment buttons (mutually exclusive feel via checkable)
        self.align_left_btn   = self._make_tool_btn("≡\u2190", "Align Left (Ctrl+L)",   checkable=True, width=32)
        self.align_center_btn = self._make_tool_btn("≡·",      "Center (Ctrl+E)",        checkable=True, width=32)
        self.align_right_btn  = self._make_tool_btn("≡\u2192", "Align Right (Ctrl+R)",  checkable=True, width=32)
        self.align_just_btn   = self._make_tool_btn("≡≡",      "Justify (Ctrl+J)",       checkable=True, width=32)

        self.align_left_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        self.align_center_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignHCenter))
        self.align_right_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        self.align_just_btn.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignJustify))

        # Use Unicode block characters for nicer alignment icons
        self.align_left_btn.setText("⬜⬜⬜\n⬜⬜·\n⬜⬜⬜")
        self.align_center_btn.setText("·⬜⬜·")
        self.align_right_btn.setText("⬜⬜⬜")
        self.align_just_btn.setText("⬛⬛⬛")

        # Actually use cleaner text symbols
        self.align_left_btn.setText("  ≡")
        self.align_center_btn.setText(" ≡ ")
        self.align_right_btn.setText("≡  ")
        self.align_just_btn.setText("≣")

        for btn in (self.align_left_btn, self.align_center_btn,
                    self.align_right_btn, self.align_just_btn):
            row2.addWidget(btn)

        sep(row2)

        # Lists
        self.bullet_list_btn = self._make_tool_btn("• ≡", "Bullet List (Ctrl+Shift+L)", width=38)
        self.bullet_list_btn.clicked.connect(self.toggle_bullet_list)
        row2.addWidget(self.bullet_list_btn)

        self.numbered_list_btn = self._make_tool_btn("1. ≡", "Numbered List (Ctrl+Shift+N)", width=42)
        self.numbered_list_btn.clicked.connect(self.toggle_numbered_list)
        row2.addWidget(self.numbered_list_btn)

        sep(row2)

        # Indent
        self.indent_btn = self._make_tool_btn("→ ≡", "Increase Indent (Tab)", width=38)
        self.indent_btn.clicked.connect(self._increase_indent)
        row2.addWidget(self.indent_btn)

        self.outdent_btn = self._make_tool_btn("← ≡", "Decrease Indent (Shift+Tab)", width=38)
        self.outdent_btn.clicked.connect(self._decrease_indent)
        row2.addWidget(self.outdent_btn)

        sep(row2)

        # Horizontal line
        self.hr_btn = self._make_tool_btn("─", "Insert Horizontal Line", width=32)
        self.hr_btn.clicked.connect(self._insert_horizontal_line)
        row2.addWidget(self.hr_btn)

        # Image insert
        self.image_btn = self._make_tool_btn("🖼", "Insert Image", width=38)
        self.image_btn.clicked.connect(self._insert_image)
        row2.addWidget(self.image_btn)

        sep(row2)

        # Line Spacing dropdown
        self.line_spacing_combo = QComboBox()
        self.line_spacing_combo.setFixedWidth(100)
        self.line_spacing_combo.setFixedHeight(28)
        self.line_spacing_combo.addItems(['Single', '1.5x', 'Double'])
        self.line_spacing_combo.setToolTip("Line Spacing")
        self.line_spacing_combo.currentTextChanged.connect(self._on_line_spacing_changed)
        row2.addWidget(self.line_spacing_combo)

        sep(row2)

        # Table
        self.table_btn = self._make_tool_btn("⊞ Table", "Insert Table (Ctrl+T)", width=72)
        self.table_btn.clicked.connect(self.insert_table)
        row2.addWidget(self.table_btn)

        self.table_props_btn = self._make_tool_btn("⊟ Props", "Table Properties (Ctrl+Shift+T)", width=72)
        self.table_props_btn.clicked.connect(self.show_table_properties)
        row2.addWidget(self.table_props_btn)

        row2.addStretch()
    
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
        
        # Replace signals
        self.search_bar.replace_requested.connect(self._replace_text)
        self.search_bar.replace_all_requested.connect(self._replace_all_text)
        
        # Toggle replace with Ctrl+H
        replace_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        replace_shortcut.activated.connect(self._show_search_bar_with_replace)
    
    def _setup_timers(self):
        """Setup periodic timers for status updates"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_bar)
        self.status_timer.start(100)
    
    def _restore_settings(self):
        """Restore saved application settings"""
        if not self.settings_manager.restore_window_geometry(self):
            screen = QApplication.primaryScreen().geometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2
            )
    
    def _restore_session(self):
        """Restore previously open tabs from last session"""
        self._is_restoring_session = True
        open_tabs, active_index = self.settings_manager.get_open_tabs()
        
        if open_tabs:
            for filepath in open_tabs:
                try:
                    self._load_file_async(Path(filepath))
                except Exception as e:
                    print(f"Failed to restore tab: {filepath} - {e}")
            
            if 0 <= active_index < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(active_index)
        
        if self.tab_widget.count() == 0:
            self.new_tab()
        
        self._is_restoring_session = False
    
    def _save_session(self):
        """Save currently open tabs for next session"""
        open_tabs = []
        for tab in self.tabs:
            if tab.current_file:
                open_tabs.append(str(tab.current_file))
        
        active_index = self.tab_widget.currentIndex()
        self.settings_manager.save_open_tabs(open_tabs, active_index)
    
    # Tab Management Methods
    def new_tab(self):
        """Create a new document tab"""
        tab_name = f"Untitled {self.tab_counter}"
        doc_tab = DocumentTab(tab_name)
        
        doc_tab.text_edit.textChanged.connect(self._on_text_changed)
        doc_tab.text_edit.cursorPositionChanged.connect(self._update_format_buttons)
        doc_tab.text_edit.cursorPositionChanged.connect(self._update_status_bar)
        doc_tab.text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        doc_tab.text_edit.customContextMenuRequested.connect(
            lambda pos, te=doc_tab.text_edit: self._show_context_menu(pos, te)
        )
        
        index = self.tab_widget.addTab(doc_tab.text_edit, doc_tab.get_display_name())
        self.tabs.append(doc_tab)
        self.tab_widget.setCurrentIndex(index)
        self.tab_counter += 1
        
        doc_tab.text_edit.setFocus()
    
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
    
    # File Operations
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
        
        for i, tab in enumerate(self.tabs):
            if tab.current_file == file_path:
                self.tab_widget.setCurrentIndex(i)
                self.statusBar().showMessage(f"File already open: {file_path.name}", 3000)
                return
        
        QTimer.singleShot(0, lambda: self._load_file_async(file_path))
    
    # One file doesn't prevent the others from loading
    # Not truly async (uses event loop scheduling to avoid blocking UI)
    def _load_file_async(self, filepath: Path):
        """Load file asynchronously to avoid UI blocking"""
        try:
            self.statusBar().showMessage(f"Loading {filepath.name}...")
            QApplication.processEvents()
            
            content, is_html = FileOperations.read_file(filepath)
            
            doc_tab = DocumentTab()
            doc_tab.set_content(content, is_html)
            doc_tab.current_file = filepath
            
            doc_tab.text_edit.textChanged.connect(self._on_text_changed)
            doc_tab.text_edit.cursorPositionChanged.connect(self._update_format_buttons)
            doc_tab.text_edit.cursorPositionChanged.connect(self._update_status_bar)
            doc_tab.text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            doc_tab.text_edit.customContextMenuRequested.connect(
                lambda pos, te=doc_tab.text_edit: self._show_context_menu(pos, te)
            )
            
            index = self.tab_widget.addTab(doc_tab.text_edit, doc_tab.get_display_name())
            self.tabs.append(doc_tab)
            self.tab_widget.setCurrentIndex(index)
            
            self.settings_manager.add_recent_file(str(filepath))
            self._update_recent_files_menu()
            
            if not self._is_restoring_session:
                self._save_session()
            
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
            
            current_index = self.tab_widget.currentIndex()
            self.tab_widget.removeTab(current_index)
            self.tabs.pop(current_index)
            
            if self.tab_widget.count() == 0:
                self.new_tab()
            
            self._save_session()
            
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
    
    # Text Formatting Methods
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
            color = QColorDialog.getColor(self._current_text_color, self, "Choose Text Color")
            
            if color.isValid():
                self._current_text_color = color
                fmt = current_tab.text_edit.currentCharFormat()
                fmt.setForeground(QBrush(color))
                current_tab.text_edit.mergeCurrentCharFormat(fmt)
                self._refresh_text_color_btn()
                current_tab.text_edit.setFocus()
    
    def _refresh_text_color_btn(self):
        """Update text color button to show current color as underline"""
        c = self._current_text_color.name()
        self.text_color_btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold;
                font-size: 11pt;
                border-bottom: 3px solid {c};
                background-color: #4A4A4A;
                border-top: 1px solid #555;
                border-left: 1px solid #555;
                border-right: 1px solid #555;
            }}
            QPushButton:hover {{ background-color: #5A5A5A; }}
            QPushButton:pressed {{ background-color: #353535; }}
        """)
    
    def change_background_color(self):
        """Change text background (highlight) color"""
        current_tab = self._get_current_tab()
        if current_tab:
            color = QColorDialog.getColor(self._current_bg_color, self, "Choose Highlight Color")
            
            if color.isValid():
                self._current_bg_color = color
                fmt = current_tab.text_edit.currentCharFormat()
                fmt.setBackground(QBrush(color))
                current_tab.text_edit.mergeCurrentCharFormat(fmt)
                self._refresh_bg_color_btn()
                current_tab.text_edit.setFocus()
    
    def _refresh_bg_color_btn(self):
        """Update highlight button to show current color as background strip"""
        c = self._current_bg_color.name()
        lum = self._current_bg_color.lightnessF()
        text_color = "#000000" if lum > 0.5 else "#FFFFFF"
        self.bg_color_btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold;
                font-size: 9pt;
                border-bottom: 3px solid {c};
                background-color: #4A4A4A;
                border-top: 1px solid #555;
                border-left: 1px solid #555;
                border-right: 1px solid #555;
                color: {text_color};
            }}
            QPushButton:hover {{ background-color: #5A5A5A; }}
            QPushButton:pressed {{ background-color: #353535; }}
        """)
    
    def add_link(self):
        """Add or edit a hyperlink"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        cursor = current_tab.text_edit.textCursor()
        selected_text = cursor.selectedText()
        
        # Check if cursor is on an existing link
        char_fmt = cursor.charFormat()
        existing_url = char_fmt.anchorHref()
        
        # If on existing link and no selection, show edit dialog with current URL
        if existing_url and not selected_text:
            url, ok = QInputDialog.getText(
                self,
                "Edit Link",
                "Edit URL:",
                QLineEdit.EchoMode.Normal,
                existing_url
            )
            if ok and url:
                fmt = QTextCharFormat()
                fmt.setAnchor(True)
                fmt.setAnchorHref(url)
                fmt.setForeground(QBrush(QColor("#0078D4")))
                fmt.setFontUnderline(True)
                cursor.mergeCharFormat(fmt)
            current_tab.text_edit.setFocus()
            return
        
        # Normal link creation
        url, ok = QInputDialog.getText(
            self,
            "Insert Link",
            "Enter URL:",
            QLineEdit.EchoMode.Normal,
            "https://"
        )
        
        if not ok or not url:
            return
        
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
                fmt = QTextCharFormat()
                cursor.setCharFormat(fmt)
            else:
                current_tab.text_edit.setCurrentCharFormat(QTextCharFormat())
            
            current_tab.text_edit.setFocus()
    
    def _apply_text_style(self, style_name: str):
        """Apply predefined text style (Normal, Title, Heading, etc)"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        cursor = current_tab.text_edit.textCursor()
        fmt = QTextCharFormat()
        block_fmt = cursor.blockFormat()
        
        # Define styles
        styles = {
            'Normal': {'size': 12, 'bold': False, 'italic': False},
            'Title': {'size': 28, 'bold': True, 'italic': False},
            'Subtitle': {'size': 18, 'bold': True, 'italic': True},
            'Heading 1': {'size': 24, 'bold': True, 'italic': False},
            'Heading 2': {'size': 20, 'bold': True, 'italic': False},
            'Heading 3': {'size': 18, 'bold': True, 'italic': False},
            'Heading 4': {'size': 16, 'bold': True, 'italic': False},
            'Heading 5': {'size': 14, 'bold': True, 'italic': False},
            'Heading 6': {'size': 12, 'bold': True, 'italic': False},
        }
        
        if style_name in styles:
            style = styles[style_name]
            fmt.setFontPointSize(style['size'])
            fmt.setFontWeight(QFont.Weight.Bold if style['bold'] else QFont.Weight.Normal)
            fmt.setFontItalic(style['italic'])
            
            # Add spacing for headings
            if style_name.startswith('Heading') or style_name in ('Title', 'Subtitle'):
                block_fmt.setTopMargin(12)
                block_fmt.setBottomMargin(12)
            else:
                block_fmt.setTopMargin(0)
                block_fmt.setBottomMargin(0)
            
            cursor.setBlockFormat(block_fmt)
            cursor.setCharFormat(fmt)
            current_tab.text_edit.setTextCursor(cursor)
        
        current_tab.text_edit.setFocus()
    
    def _insert_horizontal_line(self):
        """Insert a horizontal line separator"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        cursor = current_tab.text_edit.textCursor()
        cursor.insertText('\n')
        
        # Create a block with a bottom border to simulate a horizontal line
        block_fmt = cursor.blockFormat()
        
        # Use a frame or table line format - insert a line of dashes
        cursor.insertText('─' * 60)
        cursor.insertText('\n')
        
        current_tab.text_edit.setFocus()
    
    def _insert_image(self):
        """Insert an image into the document with resize support"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Insert Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Load and verify the image
            image = QImage(file_path)
            if image.isNull():
                QMessageBox.warning(self, "Error", "Could not load image file")
                return
            
            # Get original dimensions
            orig_width = image.width()
            orig_height = image.height()
            
            # Scale image to reasonable size (max 500px width)
            display_width = min(orig_width, 500)
            display_height = int((display_width / orig_width) * orig_height) if orig_width > 0 else orig_height
            
            # For now, insert as regular image and show resize dialog
            cursor = current_tab.text_edit.textCursor()
            
            # Create a dialog for image size
            dialog = QDialog(self)
            dialog.setWindowTitle("Insert Image")
            layout = QFormLayout(dialog)
            
            width_spin = QSpinBox()
            width_spin.setRange(50, 800)
            width_spin.setValue(display_width)
            width_spin.setSuffix(" px")
            layout.addRow("Width:", width_spin)
            
            height_spin = QSpinBox()
            height_spin.setRange(50, 800)
            height_spin.setValue(display_height)
            height_spin.setSuffix(" px")
            layout.addRow("Height:", height_spin)
            
            # Maintain aspect ratio checkbox
            aspect_ratio_cb = QCheckBox()
            aspect_ratio_cb.setChecked(True)
            layout.addRow("Maintain Aspect Ratio:", aspect_ratio_cb)
            
            # Buttons
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok |
                QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            
            # Connect signals for aspect ratio
            def on_width_changed(w):
                if aspect_ratio_cb.isChecked() and orig_width > 0:
                    new_h = int((w / orig_width) * orig_height)
                    height_spin.blockSignals(True)
                    height_spin.setValue(new_h)
                    height_spin.blockSignals(False)
            
            def on_height_changed(h):
                if aspect_ratio_cb.isChecked() and orig_height > 0:
                    new_w = int((h / orig_height) * orig_width)
                    width_spin.blockSignals(True)
                    width_spin.setValue(new_w)
                    width_spin.blockSignals(False)
            
            width_spin.valueChanged.connect(on_width_changed)
            height_spin.valueChanged.connect(on_height_changed)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                final_width = width_spin.value()
                final_height = height_spin.value()
                
                # Scale the image to the chosen size
                scaled_image = image.scaled(
                    final_width,
                    final_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Insert the scaled image
                cursor.insertImage(scaled_image, "image")
                cursor.insertText('\n')  # Add newline after image
                current_tab.text_edit.setTextCursor(cursor)
                
                QMessageBox.information(self, "Image Inserted", 
                                        f"Image inserted: {final_width}×{final_height}px\n\n"
                                        "Tip: Right-click on the image to resize it further.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to insert image: {str(e)}")
        
        current_tab.text_edit.setFocus()
    
    def toggle_bullet_list(self):
        """Toggle bullet list formatting"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        cursor = current_tab.text_edit.textCursor()
        
        # Check current list style
        current_list = cursor.currentList()
        
        if current_list and current_list.format().style() == QTextListFormat.Style.ListDisc:
            # Remove list formatting
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
            
            # Remove from list
            list_fmt = current_list.format()
            list_fmt.setIndent(list_fmt.indent() - 1)
            current_list.setFormat(list_fmt)
            current_list.remove(cursor.block())
        else:
            # Apply bullet list
            list_fmt = QTextListFormat()
            list_fmt.setStyle(QTextListFormat.Style.ListDisc)
            cursor.createList(list_fmt)
        
        current_tab.text_edit.setFocus()
    
    def toggle_numbered_list(self):
        """Toggle numbered list formatting"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        cursor = current_tab.text_edit.textCursor()
        
        # Check current list style
        current_list = cursor.currentList()
        
        if current_list and current_list.format().style() == QTextListFormat.Style.ListDecimal:
            # Remove list formatting
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
            
            # Remove from list
            list_fmt = current_list.format()
            list_fmt.setIndent(list_fmt.indent() - 1)
            current_list.setFormat(list_fmt)
            current_list.remove(cursor.block())
        else:
            # Apply numbered list
            list_fmt = QTextListFormat()
            list_fmt.setStyle(QTextListFormat.Style.ListDecimal)
            cursor.createList(list_fmt)
        
        current_tab.text_edit.setFocus()
    
    def insert_table(self):
        """Insert a table into the document"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        # Create dialog to get table dimensions
        dialog = QDialog(self)
        dialog.setWindowTitle("Insert Table")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Rows input
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("Rows:"))
        rows_spin = QSpinBox()
        rows_spin.setRange(1, 50)
        rows_spin.setValue(3)
        row_layout.addWidget(rows_spin)
        layout.addLayout(row_layout)
        
        # Columns input
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("Columns:"))
        cols_spin = QSpinBox()
        cols_spin.setRange(1, 20)
        cols_spin.setValue(3)
        col_layout.addWidget(cols_spin)
        layout.addLayout(col_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rows = rows_spin.value()
            cols = cols_spin.value()
            
            cursor = current_tab.text_edit.textCursor()
            
            # Create table format
            table_fmt = QTextTableFormat()
            table_fmt.setBorder(1)
            table_fmt.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Solid)
            table_fmt.setCellPadding(5)
            table_fmt.setCellSpacing(0)
            table_fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
            
            # Insert the table
            cursor.insertTable(rows, cols, table_fmt)
        
        current_tab.text_edit.setFocus()
    
    def show_table_properties(self):
        """Show table properties dialog for the table under cursor"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        cursor = current_tab.text_edit.textCursor()
        table = cursor.currentTable()
        if not table:
            QMessageBox.information(self, "Table Properties",
                                    "Please click inside a table first.")
            return
        
        dlg = TablePropertiesDialog(table, self)
        dlg.exec()
        current_tab.text_edit.setFocus()
    
    def _show_context_menu(self, pos: QPoint, text_edit: QTextEdit):
        """Show custom right-click context menu"""
        menu = text_edit.createStandardContextMenu()
        
        cursor = text_edit.cursorForPosition(pos)
        # Move cursor to click position so table detection works
        text_edit.setTextCursor(cursor)
        table = cursor.currentTable()
        
        if table:
            menu.addSeparator()
            table_menu = menu.addMenu("Table")
            
            add_row_above = table_menu.addAction("Insert Row Above")
            add_row_below = table_menu.addAction("Insert Row Below")
            add_col_left  = table_menu.addAction("Insert Column Left")
            add_col_right = table_menu.addAction("Insert Column Right")
            table_menu.addSeparator()
            del_row = table_menu.addAction("Delete Row")
            del_col = table_menu.addAction("Delete Column")
            table_menu.addSeparator()
            table_props = table_menu.addAction("Table Properties…")
            
            cell = table.cellAt(cursor)
            row = cell.row()
            col = cell.column()
            
            add_row_above.triggered.connect(lambda: table.insertRows(row, 1))
            add_row_below.triggered.connect(lambda: table.insertRows(row + 1, 1))
            add_col_left.triggered.connect(lambda: table.insertColumns(col, 1))
            add_col_right.triggered.connect(lambda: table.insertColumns(col + 1, 1))
            del_row.triggered.connect(
                lambda: table.removeRows(row, 1) if table.rows() > 1 else None
            )
            del_col.triggered.connect(
                lambda: table.removeColumns(col, 1) if table.columns() > 1 else None
            )
            table_props.triggered.connect(
                lambda: self._open_table_props_for(table, text_edit)
            )
        
        menu.addSeparator()
        align_menu = menu.addMenu("Alignment")
        align_menu.addAction("Align Left",    lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        align_menu.addAction("Center",        lambda: self.set_alignment(Qt.AlignmentFlag.AlignHCenter))
        align_menu.addAction("Align Right",   lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        align_menu.addAction("Justify",       lambda: self.set_alignment(Qt.AlignmentFlag.AlignJustify))
        
        # Image resize - check if cursor is at an image
        char_fmt = cursor.charFormat()
        # Check if the character format has an image name property
        image_name = char_fmt.stringProperty(QTextFormat.Property.ImageName)
        if image_name:  # If image_name exists, we're on an image
            menu.addSeparator()
            image_resize = menu.addAction("Resize Image…")
            image_resize.triggered.connect(lambda: self._resize_image_at_cursor(text_edit))
        
        menu.exec(text_edit.mapToGlobal(pos))
    
    def _open_table_props_for(self, table: QTextTable, text_edit: QTextEdit):
        """Open table properties for a specific table"""
        dlg = TablePropertiesDialog(table, self)
        dlg.exec()
        text_edit.setFocus()
    
    def _resize_image_at_cursor(self, text_edit: QTextEdit):
        """Show dialog to resize image at cursor position"""
        cursor = text_edit.textCursor()
        char_fmt = cursor.charFormat()
        
        # Get the image resource name
        image_name = char_fmt.stringProperty(QTextFormat.Property.ImageName)
        if not image_name:
            QMessageBox.information(self, "Resize Image", "No image found at cursor position.")
            return
        
        # Get the document's image resource
        doc = text_edit.document()
        image = doc.resource(QTextDocument.ResourceType.ImageResource, QUrl(image_name))
        
        if image.isNull() or not isinstance(image, QImage):
            QMessageBox.warning(self, "Error", "Could not access image data.")
            return
        
        # Show resize dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Resize Image")
        layout = QFormLayout(dialog)
        
        width_spin = QSpinBox()
        width_spin.setRange(50, 800)
        width_spin.setValue(image.width())
        width_spin.setSuffix(" px")
        layout.addRow("Width:", width_spin)
        
        height_spin = QSpinBox()
        height_spin.setRange(50, 800)
        height_spin.setValue(image.height())
        height_spin.setSuffix(" px")
        layout.addRow("Height:", height_spin)
        
        aspect_ratio_cb = QCheckBox()
        aspect_ratio_cb.setChecked(True)
        layout.addRow("Maintain Aspect Ratio:", aspect_ratio_cb)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        orig_width = image.width()
        orig_height = image.height()
        
        def on_width_changed(w):
            if aspect_ratio_cb.isChecked() and orig_width > 0:
                new_h = int((w / orig_width) * orig_height)
                height_spin.blockSignals(True)
                height_spin.setValue(new_h)
                height_spin.blockSignals(False)
        
        def on_height_changed(h):
            if aspect_ratio_cb.isChecked() and orig_height > 0:
                new_w = int((h / orig_height) * orig_width)
                width_spin.blockSignals(True)
                width_spin.setValue(new_w)
                width_spin.blockSignals(False)
        
        width_spin.valueChanged.connect(on_width_changed)
        height_spin.valueChanged.connect(on_height_changed)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_width = width_spin.value()
            new_height = height_spin.value()
            
            # Scale the image
            scaled = image.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Update the document resource
            doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(image_name), scaled)
            
            # Refresh the display
            text_edit.updateGeometry()
            text_edit.viewport().update()
            
            QMessageBox.information(self, "Image Resized", 
                                    f"Image resized to {new_width}×{new_height}px")
    
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
    
    def set_alignment(self, alignment: Qt.AlignmentFlag):
        """Set paragraph alignment for current selection"""
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.text_edit.setAlignment(alignment)
            self._update_format_buttons()
            current_tab.text_edit.setFocus()
    
    def _increase_indent(self):
        """Increase paragraph indent"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        cursor = current_tab.text_edit.textCursor()
        block_fmt = cursor.blockFormat()
        block_fmt.setIndent(block_fmt.indent() + 1)
        cursor.setBlockFormat(block_fmt)
        current_tab.text_edit.setFocus()
    
    def _decrease_indent(self):
        """Decrease paragraph indent"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        cursor = current_tab.text_edit.textCursor()
        block_fmt = cursor.blockFormat()
        new_indent = max(0, block_fmt.indent() - 1)
        block_fmt.setIndent(new_indent)
        cursor.setBlockFormat(block_fmt)
        current_tab.text_edit.setFocus()

    def _on_line_spacing_changed(self, text: str):
        """Handle line spacing combo change"""
        spacing_map = {
            'Single': 1.0,
            '1.5x': 1.5,
            'Double': 2.0
        }
        if text in spacing_map:
            self._set_line_spacing(spacing_map[text])

    def _update_format_buttons(self):
        """Update formatting button states based on current cursor position"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        fmt = current_tab.text_edit.currentCharFormat()
        
        for btn in (self.bold_btn, self.italic_btn, self.underline_btn,
                    self.strike_btn, self.superscript_btn, self.subscript_btn,
                    self.font_combo, self.size_combo,
                    self.align_left_btn, self.align_center_btn,
                    self.align_right_btn, self.align_just_btn):
            btn.blockSignals(True)
        
        self.bold_btn.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.italic_btn.setChecked(fmt.fontItalic())
        self.underline_btn.setChecked(fmt.fontUnderline())
        self.strike_btn.setChecked(fmt.fontStrikeOut())
        
        # Superscript & Subscript
        va = fmt.verticalAlignment()
        self.superscript_btn.setChecked(va == QTextCharFormat.VerticalAlignment.AlignSuperScript)
        self.subscript_btn.setChecked(va == QTextCharFormat.VerticalAlignment.AlignSubScript)
        
        ps = fmt.fontPointSize()
        if ps and ps > 0:
            self.size_combo.setCurrentText(str(int(ps)))
        
        # Alignment
        alignment = current_tab.text_edit.alignment()
        self.align_left_btn.setChecked(alignment == Qt.AlignmentFlag.AlignLeft or
                                       alignment == Qt.AlignmentFlag.AlignAbsolute)
        self.align_center_btn.setChecked(alignment == Qt.AlignmentFlag.AlignHCenter)
        self.align_right_btn.setChecked(alignment == Qt.AlignmentFlag.AlignRight)
        self.align_just_btn.setChecked(alignment == Qt.AlignmentFlag.AlignJustify)
        
        for btn in (self.bold_btn, self.italic_btn, self.underline_btn,
                    self.strike_btn, self.superscript_btn, self.subscript_btn,
                    self.font_combo, self.size_combo,
                    self.align_left_btn, self.align_center_btn,
                    self.align_right_btn, self.align_just_btn):
            btn.blockSignals(False)
    
    # Search Methods
    def _show_search_bar(self):
        """Toggle the search bar visibility"""
        if self.search_bar.isVisible():
            self._hide_search_bar()
        else:
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
        """Highlight all occurrences of search text"""
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
        matches = []
        while True:
            pos = search_func(search_text, pos)
            if pos == -1:
                break
            matches.append(pos)
            pos += len(search_text)
        
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
            
            if start_pos == current_pos:
                # Current match - use orange with dark text
                selection.format.setBackground(QColor("#FF8C00"))
                selection.format.setForeground(QColor("#000000"))
                current_match_idx = i
            else:
                # Other matches - use darker yellow/gold with dark text
                selection.format.setBackground(QColor("#CCAA00"))
                selection.format.setForeground(QColor("#000000"))
            
            extra_selections.append(selection)
        
        current_tab.text_edit.setExtraSelections(extra_selections)
        
        total = len(matches)
        current = (current_match_idx + 1) if total > 0 else 0
        self.search_bar.update_counter(current, total)
    
    # Undo/Redo
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
    
    # Status Bar
    def _update_status_bar(self):
        """Update status bar with current document info"""
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
    
    # Event Handlers
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
        
        self.settings_manager.save_window_geometry(
            self.saveGeometry(),
            self.saveState()
        )
        self._save_session()
        
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle global key press events"""
        if event.key() == Qt.Key.Key_Escape:
            if self.search_bar.isVisible():
                self._hide_search_bar()
            else:
                self.close()
        else:
            super().keyPressEvent(event)
    
    # ========================================================================
    # REPLACE FUNCTIONALITY
    # ========================================================================
    
    def _show_search_bar_with_replace(self):
        """Toggle search bar replace mode (Ctrl+H: show/hide replace)"""
        if self.search_bar.isVisible() and self.search_bar.replace_widget.isVisible():
            # If search bar and replace are already visible, hide the replace widget
            self.search_bar.replace_widget.setVisible(False)
            self.search_bar.search_input.setFocus()
        else:
            # Show search bar with replace
            self._show_search_bar()
            self.search_bar.show_replace = True
            self.search_bar.replace_widget.setVisible(True)
            self.search_bar.replace_input.setFocus()
    
    def _replace_text(self):
        """Replace current match with replacement text"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        search_text = self.search_bar.get_search_text()
        replace_text = self.search_bar.get_replace_text()
        
        if not search_text:
            QMessageBox.warning(self, "Replace", "Please enter text to find")
            return
        
        cursor = current_tab.text_edit.textCursor()
        
        # Check if current selection matches search text
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
                # Find next occurrence
                self._find_text(backward=False)
                return
        
        # If no selection, find first occurrence
        if current_tab.text_edit.find(search_text, flags):
            cursor = current_tab.text_edit.textCursor()
            cursor.insertText(replace_text)
            current_tab.text_edit.setTextCursor(cursor)
            self._find_text(backward=False)
    
    def _replace_all_text(self):
        """Replace all occurrences of search text"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        search_text = self.search_bar.get_search_text()
        replace_text = self.search_bar.get_replace_text()
        
        if not search_text:
            QMessageBox.warning(self, "Replace All", "Please enter text to find")
            return
        
        # Move to start of document
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
            QMessageBox.information(
                self, 
                "Replace All", 
                f"Replaced {count} occurrence{'s' if count != 1 else ''}"
            )
        else:
            QMessageBox.information(self, "Replace All", "No matches found")
        
        self._highlight_all_matches(replace_text)
    
    # ========================================================================
    # PRINT & PDF EXPORT
    # ========================================================================
    
    def _print_document(self):
        """Print the current document"""
        current_tab = self._get_current_tab()
        if not current_tab:
            QMessageBox.warning(self, "Print", "No document to print")
            return
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        print_dialog = QPrintDialog(printer, self)
        
        if print_dialog.exec() == QDialog.DialogCode.Accepted:
            current_tab.text_edit.print(printer)
            QMessageBox.information(self, "Print", "Document sent to printer successfully")
    
    def _export_to_pdf(self):
        """Export current document to PDF"""
        current_tab = self._get_current_tab()
        if not current_tab:
            QMessageBox.warning(self, "Export PDF", "No document to export")
            return
        
        default_filename = current_tab.current_file.stem if current_tab.current_file else "document"
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export as PDF",
            default_filename + ".pdf",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if filename:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filename)
            
            current_tab.text_edit.print(printer)
            QMessageBox.information(
                self, 
                "Success", 
                f"PDF exported successfully to:\n{filename}"
            )
    
    # ========================================================================
    # SUPERSCRIPT & SUBSCRIPT
    # ========================================================================
    
    def _apply_superscript(self):
        """Toggle superscript formatting on selected text"""
        current_tab = self._get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            va = fmt.verticalAlignment()
            
            if va == QTextCharFormat.VerticalAlignment.AlignSuperScript:
                fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
            else:
                fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSuperScript)
            
            current_tab.text_edit.mergeCurrentCharFormat(fmt)
            current_tab.text_edit.setFocus()
    
    def _apply_subscript(self):
        """Toggle subscript formatting on selected text"""
        current_tab = self._get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            va = fmt.verticalAlignment()
            
            if va == QTextCharFormat.VerticalAlignment.AlignSubScript:
                fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
            else:
                fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSubScript)
            
            current_tab.text_edit.mergeCurrentCharFormat(fmt)
            current_tab.text_edit.setFocus()
    
    # ========================================================================
    # CODE BLOCK FORMATTING
    # ========================================================================
    
    def _insert_code_block(self):
        """Insert a code block with monospace formatting"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        cursor = current_tab.text_edit.textCursor()
        
        # Create block format (paragraph style)
        block_fmt = QTextBlockFormat()
        block_fmt.setBackground(QColor("#2b2b2b"))  # Dark background
        block_fmt.setLeftMargin(10)
        block_fmt.setRightMargin(10)
        block_fmt.setTopMargin(5)
        block_fmt.setBottomMargin(5)
        
        # Create character format (text style)
        char_fmt = QTextCharFormat()
        char_fmt.setFontFamily("Courier New")
        char_fmt.setFontPointSize(10)
        char_fmt.setForeground(QColor("#00FF00"))  # Green text
        char_fmt.setBackground(QColor("#1e1e1e"))  # Very dark background
        
        # Insert code block
        cursor.insertBlock(block_fmt)
        cursor.setCharFormat(char_fmt)
        cursor.insertText("# Enter your code here\n")
        
        current_tab.text_edit.setTextCursor(cursor)
        current_tab.text_edit.setFocus()
    
    # ========================================================================
    # LINE SPACING CONTROL
    # ========================================================================
    
    def _set_line_spacing(self, spacing: float):
        """Set line spacing for current paragraph"""
        current_tab = self._get_current_tab()
        if not current_tab:
            return
        
        cursor = current_tab.text_edit.textCursor()
        
        # If text is selected, apply to all blocks in selection
        if cursor.hasSelection():
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()
            
            cursor.setPosition(start_pos)
            block = cursor.block()
            
            while block.isValid() and block.position() <= end_pos:
                cursor.setPosition(block.position())
                fmt = cursor.blockFormat()
                
                # Use int value: 0 = SingleHeight, 1 = ProportionalHeight
                # Or use the enum value directly with .value
                fmt.setLineHeight(spacing * 100, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
                cursor.setBlockFormat(fmt)
                
                block = block.next()
        else:
            # Apply to current block only
            fmt = cursor.blockFormat()
            fmt.setLineHeight(spacing * 100, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
            cursor.setBlockFormat(fmt)
        
        current_tab.text_edit.setFocus()