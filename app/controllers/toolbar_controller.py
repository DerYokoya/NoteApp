"""
ToolbarController
=================
Owns the creation, wiring, and theming of the two-row formatting toolbar that
was previously built entirely inside ``MainWindow._create_formatting_toolbar``
and partially updated by ``MainWindow._apply_toolbar_theme``.

Usage
-----
Instantiate once inside MainWindow.__init__ / _setup_ui, then call
``build(sep_color)`` to create the QWidget, and wire the returned widget into
the main layout::

    self.toolbar_ctrl = ToolbarController(fmt_ctrl, self)
    self.format_toolbar = self.toolbar_ctrl.build(sep_color)
    layout.addWidget(self.format_toolbar)

All button references that MainWindow previously held directly (``bold_btn``,
``font_combo``, etc.) are now attributes of this controller.  MainWindow reads
them only when calling ``_update_format_buttons``.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QComboBox, QFontComboBox, QToolTip,
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from config.styles import StyleSheet


class ToolbarController:
    """Creates and manages the two-row formatting toolbar."""

    def __init__(self, fmt_ctrl, parent_widget):
        """
        Parameters
        ----------
        fmt_ctrl      : FormattingController  (handles the actual text ops)
        parent_widget : QMainWindow           (toolbar is owned by main window)
        """
        self._fmt = fmt_ctrl
        self._parent = parent_widget
        self.toolbar_widget: QWidget = None  # set after build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, sep_color: str) -> QWidget:
        """Create the toolbar widget and return it.  Must be called once."""
        self._sep_color = sep_color

        self.toolbar_widget = QWidget()
        self.toolbar_widget.setObjectName("FormatToolbar")

        outer = QVBoxLayout(self.toolbar_widget)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(2)
        row2 = QHBoxLayout()
        row2.setSpacing(2)
        outer.addLayout(row1)
        outer.addLayout(row2)

        def sep(row):
            line = QFrame()
            line.setFrameShape(QFrame.Shape.VLine)
            line.setStyleSheet(
                f"color: {self._sep_color}; max-width: 1px; margin: 2px 4px;"
            )
            row.addWidget(line)

        # ── ROW 1 ────────────────────────────────────────────────────
        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setFixedWidth(160)
        self.font_combo.setFixedHeight(28)
        self.font_combo.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        self.font_combo.currentFontChanged.connect(self._fmt.change_font_family)
        row1.addWidget(self.font_combo)
        row1.addSpacing(4)

        # Font size
        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.setFixedWidth(80)
        self.size_combo.setFixedHeight(28)
        self.size_combo.addItems(['8','9','10','11','12','14','16','18','20','24','28','36','48','72'])
        self.size_combo.setCurrentText('12')
        sz_font = QFont()
        sz_font.setPointSize(10)
        self.size_combo.setFont(sz_font)
        if self.size_combo.lineEdit():
            self.size_combo.lineEdit().setFont(sz_font)
        self.size_combo.currentTextChanged.connect(self._fmt.change_font_size)
        self.size_combo.lineEdit().returnPressed.connect(
            lambda: self._fmt.change_font_size(self.size_combo.currentText())
        )
        row1.addWidget(self.size_combo)
        row1.addSpacing(4)

        # Style dropdown
        self.style_combo = QComboBox()
        self.style_combo.setFixedWidth(130)
        self.style_combo.setFixedHeight(28)
        self.style_combo.addItems([
            'Normal', 'Title', 'Subtitle',
            'Heading 1', 'Heading 2', 'Heading 3',
            'Heading 4', 'Heading 5', 'Heading 6',
            'Code Block',
        ])
        self.style_combo.currentTextChanged.connect(self._fmt.apply_text_style)
        row1.addWidget(self.style_combo)
        row1.addSpacing(4)

        # Line spacing dropdown
        self.line_spacing_combo = QComboBox()
        self.line_spacing_combo.setFixedWidth(100)
        self.line_spacing_combo.setFixedHeight(28)
        self.line_spacing_combo.addItems(['Single', '1.5x', 'Double'])
        self.line_spacing_combo.setToolTip("Line Spacing")
        self.line_spacing_combo.currentTextChanged.connect(self._on_line_spacing_changed)
        row1.addWidget(self.line_spacing_combo)

        sep(row1)

        # Bold / Italic / Underline / Strikethrough
        bold_font = QFont("Georgia", 10, QFont.Weight.Bold)
        self.bold_btn = self._btn("B", "Bold (Ctrl+B)", checkable=True, font_override=bold_font)
        self.bold_btn.clicked.connect(self._fmt.toggle_bold)
        row1.addWidget(self.bold_btn)

        italic_font = QFont("Georgia", 10)
        italic_font.setItalic(True)
        self.italic_btn = self._btn("I", "Italic (Ctrl+I)", checkable=True, font_override=italic_font)
        self.italic_btn.clicked.connect(self._fmt.toggle_italic)
        row1.addWidget(self.italic_btn)

        ul_font = QFont("Arial", 9)
        ul_font.setUnderline(True)
        self.underline_btn = self._btn("U", "Underline (Ctrl+U)", checkable=True, font_override=ul_font)
        self.underline_btn.clicked.connect(self._fmt.toggle_underline)
        row1.addWidget(self.underline_btn)

        st_font = QFont("Arial", 9)
        st_font.setStrikeOut(True)
        self.strike_btn = self._btn("S", "Strikethrough", checkable=True, font_override=st_font)
        self.strike_btn.clicked.connect(self._fmt.toggle_strikethrough)
        row1.addWidget(self.strike_btn)

        sup_font = QFont("Arial", 8)
        self.superscript_btn = self._btn("x²", "Superscript (Ctrl+Shift+P)", checkable=True,
                                         font_override=sup_font, width=32)
        self.superscript_btn.clicked.connect(self._fmt.apply_superscript)
        row1.addWidget(self.superscript_btn)

        sub_font = QFont("Arial", 8)
        self.subscript_btn = self._btn("x₂", "Subscript (Ctrl+Shift+B)", checkable=True,
                                       font_override=sub_font, width=32)
        self.subscript_btn.clicked.connect(self._fmt.apply_subscript)
        row1.addWidget(self.subscript_btn)

        code_font = QFont("Courier", 8)
        self.code_block_btn = self._btn("<>", "Code Block (Ctrl+`)", font_override=code_font, width=32)
        self.code_block_btn.clicked.connect(self._fmt.insert_code_block)
        row1.addWidget(self.code_block_btn)

        sep(row1)

        # Colour buttons (created here; styled by apply_theme)
        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setFixedSize(32, 28)
        self.text_color_btn.setToolTip("Text Color")
        self.text_color_btn.clicked.connect(
            lambda: self._fmt.change_text_color(self.refresh_text_color_btn)
        )
        row1.addWidget(self.text_color_btn)

        self.bg_color_btn = QPushButton("ab")
        self.bg_color_btn.setFixedSize(34, 28)
        self.bg_color_btn.setToolTip("Highlight Color")
        self.bg_color_btn.clicked.connect(
            lambda: self._fmt.change_background_color(self.refresh_bg_color_btn)
        )
        row1.addWidget(self.bg_color_btn)

        sep(row1)

        self.link_btn = self._btn("🔗", "Insert Link (Ctrl+K)", width=34)
        self.link_btn.clicked.connect(self._fmt.add_link)
        row1.addWidget(self.link_btn)

        sep(row1)

        self.clear_btn = self._btn("Tx", "Clear Formatting (Ctrl+\\)", width=34)
        self.clear_btn.clicked.connect(self._fmt.clear_formatting)
        row1.addWidget(self.clear_btn)

        row1.addStretch()

        # ── ROW 2 ────────────────────────────────────────────────────
        self.align_left_btn   = self._btn("  ≡",  "Align Left (Ctrl+L)",   checkable=True)
        self.align_center_btn = self._btn(" ≡ ",  "Center (Ctrl+E)",       checkable=True)
        self.align_right_btn  = self._btn("≡  ",  "Align Right (Ctrl+R)",  checkable=True)
        self.align_just_btn   = self._btn("≣",    "Justify (Ctrl+J)",      checkable=True)

        from PyQt6.QtCore import Qt as _Qt
        self.align_left_btn.clicked.connect(
            lambda: self._fmt.set_alignment(_Qt.AlignmentFlag.AlignLeft))
        self.align_center_btn.clicked.connect(
            lambda: self._fmt.set_alignment(_Qt.AlignmentFlag.AlignHCenter))
        self.align_right_btn.clicked.connect(
            lambda: self._fmt.set_alignment(_Qt.AlignmentFlag.AlignRight))
        self.align_just_btn.clicked.connect(
            lambda: self._fmt.set_alignment(_Qt.AlignmentFlag.AlignJustify))

        for btn in (self.align_left_btn, self.align_center_btn,
                    self.align_right_btn, self.align_just_btn):
            row2.addWidget(btn)
        sep(row2)

        self.bullet_list_btn = self._btn("• ≡", "Bullet List (Ctrl+Shift+L)", width=38)
        self.bullet_list_btn.clicked.connect(self._fmt.toggle_bullet_list)
        row2.addWidget(self.bullet_list_btn)

        self.numbered_list_btn = self._btn("1. ≡", "Numbered List (Ctrl+Shift+N)", width=42)
        self.numbered_list_btn.clicked.connect(self._fmt.toggle_numbered_list)
        row2.addWidget(self.numbered_list_btn)

        sep(row2)

        self.indent_btn = self._btn("→ ≡", "Increase Indent (Tab)", width=38)
        self.indent_btn.clicked.connect(self._fmt.increase_indent)
        row2.addWidget(self.indent_btn)

        self.outdent_btn = self._btn("← ≡", "Decrease Indent (Shift+Tab)", width=38)
        self.outdent_btn.clicked.connect(self._fmt.decrease_indent)
        row2.addWidget(self.outdent_btn)

        sep(row2)

        self.hr_btn = self._btn("─", "Insert Horizontal Line", width=32)
        self.hr_btn.clicked.connect(self._fmt.insert_horizontal_line)
        row2.addWidget(self.hr_btn)

        self.image_btn = self._btn("🖼", "Insert Image", width=38)
        self.image_btn.clicked.connect(self._fmt.insert_image)
        row2.addWidget(self.image_btn)

        sep(row2)

        self.table_btn = self._btn("⊞ Table", "Insert Table (Ctrl+T)", width=72)
        self.table_btn.clicked.connect(self._fmt.insert_table)
        row2.addWidget(self.table_btn)

        self.table_props_btn = self._btn("⊟ Props", "Table Properties (Ctrl+Shift+T)", width=72)
        self.table_props_btn.clicked.connect(self._fmt.show_table_properties)
        row2.addWidget(self.table_props_btn)

        row2.addStretch()
        return self.toolbar_widget

    # ------------------------------------------------------------------
    # Theme application
    # ------------------------------------------------------------------

    def apply_theme(self, dark_theme: bool):
        """Re-apply colours whenever the user switches light/dark."""
        t = StyleSheet.toolbar_tokens(dark_theme)
        self._sep_color = t["sep_color"]
        # Only set the keys that toolbar_tokens actually provides.
        # Button/combo colours come from the global application QSS.
        self.toolbar_widget.setStyleSheet(f"""
            QWidget#FormatToolbar {{
                background-color: {t['toolbar_bg']};
                border-bottom: 1px solid {t['toolbar_border']};
            }}
        """)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{ font-weight: bold; color: {t['clear_btn_fg']}; }}
            QPushButton:hover {{ background-color: {t['clear_btn_hover']}; }}
        """)
        self.refresh_text_color_btn()
        self.refresh_bg_color_btn()

    # ------------------------------------------------------------------
    # Colour-button painters (called by FormattingController callbacks)
    # ------------------------------------------------------------------

    def refresh_text_color_btn(self):
        dark_theme = self._fmt._get_dark()
        c = self._fmt.current_text_color.name()
        t = StyleSheet.toolbar_tokens(dark_theme)
        self.text_color_btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold; font-size: 11pt;
                border-bottom: 3px solid {c};
                background-color: {t['swatch_bg']};
                border-top: 1px solid {t['swatch_border']};
                border-left: 1px solid {t['swatch_border']};
                border-right: 1px solid {t['swatch_border']};
            }}
            QPushButton:hover {{ background-color: {t['swatch_hover']}; }}
            QPushButton:pressed {{ background-color: {t['swatch_pressed']}; }}
        """)

    def refresh_bg_color_btn(self):
        dark_theme = self._fmt._get_dark()
        c = self._fmt.current_bg_color.name()
        lum = self._fmt.current_bg_color.lightnessF()
        text_color = "#000000" if lum > 0.5 else "#FFFFFF"
        t = StyleSheet.toolbar_tokens(dark_theme)
        self.bg_color_btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold; font-size: 9pt;
                border-bottom: 3px solid {c};
                background-color: {t['swatch_bg']};
                border-top: 1px solid {t['swatch_border']};
                border-left: 1px solid {t['swatch_border']};
                border-right: 1px solid {t['swatch_border']};
                color: {text_color};
            }}
            QPushButton:hover {{ background-color: {t['swatch_hover']}; }}
            QPushButton:pressed {{ background-color: {t['swatch_pressed']}; }}
        """)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _btn(self, text: str, tooltip: str, *,
             checkable: bool = False, width: int = 32,
             font_override: QFont = None) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCheckable(checkable)
        btn.setFixedSize(width, 28)
        if font_override:
            btn.setFont(font_override)
        return btn

    def _on_line_spacing_changed(self, text: str):
        spacing_map = {'Single': 1.0, '1.5x': 1.5, 'Double': 2.0}
        if text in spacing_map:
            self._fmt.set_line_spacing(spacing_map[text])
