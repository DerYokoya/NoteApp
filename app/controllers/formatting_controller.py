"""
FormattingController
====================
Owns every text-formatting operation that was previously scattered across
MainWindow.  MainWindow instantiates one of these and delegates all
formatting calls to it.

Design contract
---------------
- The controller holds a ``get_current_tab`` callable (injected at
  construction) so it never imports or references MainWindow directly.
- It stores the two colour-picker states (text colour / highlight colour)
  that used to live as ``_current_text_color`` / ``_current_bg_color`` on
  MainWindow.
- Every method that previously did ``if current_tab: …`` still does so here;
  the guard is unchanged, just relocated.
"""

from PyQt6.QtWidgets import (
    QColorDialog, QInputDialog, QDialog, QFormLayout, QSpinBox, QCheckBox,
    QDialogButtonBox, QLabel, QMessageBox, QTextEdit, QHBoxLayout,
    QVBoxLayout,
)
from PyQt6.QtGui import (
    QFont, QTextCharFormat, QBrush, QColor, QTextListFormat,
    QTextBlockFormat, QTextTableFormat, QImage,
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QTextDocument, QTextFormat
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QTextFrameFormat
from PyQt6.QtGui import QTextLength

from config.styles import StyleSheet
from widgets.table_dialog import TablePropertiesDialog


class FormattingController:
    """Handles all rich-text formatting operations for the active document tab."""

    def __init__(self, get_current_tab, get_dark_theme, parent_widget):
        """
        Parameters
        ----------
        get_current_tab : callable() -> DocumentTab | None
        get_dark_theme  : callable() -> bool
        parent_widget   : QWidget  (used as parent for dialogs)
        """
        self._get_tab = get_current_tab
        self._get_dark = get_dark_theme
        self._parent = parent_widget

        self._current_text_color = QColor("#FFFFFF")
        self._current_bg_color = QColor("#FFFF00")

    # ------------------------------------------------------------------
    # Colour-button accessors (ToolbarController reads these)
    # ------------------------------------------------------------------

    @property
    def current_text_color(self) -> QColor:
        return self._current_text_color

    @property
    def current_bg_color(self) -> QColor:
        return self._current_bg_color

    # ------------------------------------------------------------------
    # Basic character formatting
    # ------------------------------------------------------------------

    def toggle_bold(self):
        tab = self._get_tab()
        if tab:
            fmt = tab.text_edit.currentCharFormat()
            weight = QFont.Weight.Normal if fmt.fontWeight() == QFont.Weight.Bold else QFont.Weight.Bold
            fmt.setFontWeight(weight)
            tab.text_edit.mergeCurrentCharFormat(fmt)
            tab.text_edit.setFocus()

    def toggle_italic(self):
        tab = self._get_tab()
        if tab:
            fmt = tab.text_edit.currentCharFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            tab.text_edit.mergeCurrentCharFormat(fmt)
            tab.text_edit.setFocus()

    def toggle_underline(self):
        tab = self._get_tab()
        if tab:
            fmt = tab.text_edit.currentCharFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            tab.text_edit.mergeCurrentCharFormat(fmt)
            tab.text_edit.setFocus()

    def toggle_strikethrough(self):
        tab = self._get_tab()
        if tab:
            fmt = tab.text_edit.currentCharFormat()
            fmt.setFontStrikeOut(not fmt.fontStrikeOut())
            tab.text_edit.mergeCurrentCharFormat(fmt)
            tab.text_edit.setFocus()

    def apply_superscript(self):
        tab = self._get_tab()
        if tab:
            fmt = tab.text_edit.currentCharFormat()
            va = fmt.verticalAlignment()
            if va == QTextCharFormat.VerticalAlignment.AlignSuperScript:
                fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
            else:
                fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSuperScript)
            tab.text_edit.mergeCurrentCharFormat(fmt)
            tab.text_edit.setFocus()

    def apply_subscript(self):
        tab = self._get_tab()
        if tab:
            fmt = tab.text_edit.currentCharFormat()
            va = fmt.verticalAlignment()
            if va == QTextCharFormat.VerticalAlignment.AlignSubScript:
                fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
            else:
                fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSubScript)
            tab.text_edit.mergeCurrentCharFormat(fmt)
            tab.text_edit.setFocus()

    def clear_formatting(self):
        tab = self._get_tab()
        if tab:
            cursor = tab.text_edit.textCursor()
            if cursor.hasSelection():
                cursor.setCharFormat(QTextCharFormat())
            else:
                tab.text_edit.setCurrentCharFormat(QTextCharFormat())
            tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Colour pickers
    # ------------------------------------------------------------------

    def change_text_color(self, refresh_btn_callback):
        tab = self._get_tab()
        if tab:
            color = QColorDialog.getColor(self._current_text_color, self._parent, "Choose Text Color")
            if color.isValid():
                self._current_text_color = color
                fmt = tab.text_edit.currentCharFormat()
                fmt.setForeground(QBrush(color))
                tab.text_edit.mergeCurrentCharFormat(fmt)
                refresh_btn_callback()
                tab.text_edit.setFocus()

    def change_background_color(self, refresh_btn_callback):
        tab = self._get_tab()
        if tab:
            color = QColorDialog.getColor(self._current_bg_color, self._parent, "Choose Highlight Color")
            if color.isValid():
                self._current_bg_color = color
                fmt = tab.text_edit.currentCharFormat()
                fmt.setBackground(QBrush(color))
                tab.text_edit.mergeCurrentCharFormat(fmt)
                refresh_btn_callback()
                tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Font family / size
    # ------------------------------------------------------------------

    def change_font_family(self, font: QFont):
        tab = self._get_tab()
        if tab:
            fmt = tab.text_edit.currentCharFormat()
            fmt.setFontFamily(font.family())
            tab.text_edit.mergeCurrentCharFormat(fmt)
            tab.text_edit.setFocus()

    def change_font_size(self, size: str):
        tab = self._get_tab()
        if tab and size:
            try:
                fmt = tab.text_edit.currentCharFormat()
                fmt.setFontPointSize(int(size))
                tab.text_edit.mergeCurrentCharFormat(fmt)
                tab.text_edit.setFocus()
            except ValueError:
                pass

    # ------------------------------------------------------------------
    # Alignment
    # ------------------------------------------------------------------

    def set_alignment(self, alignment: Qt.AlignmentFlag):
        tab = self._get_tab()
        if tab:
            tab.text_edit.setAlignment(alignment)
            tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Indentation
    # ------------------------------------------------------------------

    def increase_indent(self):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        block_fmt = cursor.blockFormat()
        block_fmt.setIndent(block_fmt.indent() + 1)
        cursor.setBlockFormat(block_fmt)
        tab.text_edit.setFocus()

    def decrease_indent(self):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        block_fmt = cursor.blockFormat()
        block_fmt.setIndent(max(0, block_fmt.indent() - 1))
        cursor.setBlockFormat(block_fmt)
        tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Line spacing
    # ------------------------------------------------------------------

    def set_line_spacing(self, spacing: float):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        height_type = QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
        if cursor.hasSelection():
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()
            cursor.setPosition(start_pos)
            block = cursor.block()
            while block.isValid() and block.position() <= end_pos:
                cursor.setPosition(block.position())
                fmt = cursor.blockFormat()
                fmt.setLineHeight(spacing * 100, height_type)
                cursor.setBlockFormat(fmt)
                block = block.next()
        else:
            fmt = cursor.blockFormat()
            fmt.setLineHeight(spacing * 100, height_type)
            cursor.setBlockFormat(fmt)
        tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Text styles (Normal / Title / Heading / Code Block)
    # ------------------------------------------------------------------

    def apply_text_style(self, style_name: str):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        styles = {
            'Normal':    {'size': 12, 'bold': False, 'italic': False, 'bg': None, 'fg': None, 'family': None},
            'Title':     {'size': 28, 'bold': True,  'italic': False, 'bg': None, 'fg': None, 'family': None},
            'Subtitle':  {'size': 18, 'bold': True,  'italic': True,  'bg': None, 'fg': None, 'family': None},
            'Heading 1': {'size': 24, 'bold': True,  'italic': False, 'bg': None, 'fg': None, 'family': None},
            'Heading 2': {'size': 20, 'bold': True,  'italic': False, 'bg': None, 'fg': None, 'family': None},
            'Heading 3': {'size': 18, 'bold': True,  'italic': False, 'bg': None, 'fg': None, 'family': None},
            'Heading 4': {'size': 16, 'bold': True,  'italic': False, 'bg': None, 'fg': None, 'family': None},
            'Heading 5': {'size': 14, 'bold': True,  'italic': False, 'bg': None, 'fg': None, 'family': None},
            'Heading 6': {'size': 12, 'bold': True,  'italic': False, 'bg': None, 'fg': None, 'family': None},
            'Code Block': {
                'size': 10, 'bold': False, 'italic': False,
                'bg': QColor("#1e1e1e"), 'fg': QColor("#00FF00"),
                'family': "Courier New", 'block_bg': QColor("#2b2b2b"),
            },
        }
        if style_name not in styles:
            return
        style = styles[style_name]
        fmt = QTextCharFormat()
        fmt.setFontPointSize(style['size'])
        fmt.setFontWeight(QFont.Weight.Bold if style['bold'] else QFont.Weight.Normal)
        fmt.setFontItalic(style['italic'])
        if style.get('family'):
            fmt.setFontFamily(style['family'])
        if style.get('fg'):
            fmt.setForeground(QBrush(style['fg']))
        if style.get('bg'):
            fmt.setBackground(QBrush(style['bg']))
        block_fmt = cursor.blockFormat()
        if style_name == 'Code Block' and style.get('block_bg'):
            block_fmt.setBackground(style['block_bg'])
            block_fmt.setLeftMargin(10)
            block_fmt.setRightMargin(10)
            block_fmt.setTopMargin(5)
            block_fmt.setBottomMargin(5)
        else:
            block_fmt.setBackground(Qt.GlobalColor.transparent)
            block_fmt.setLeftMargin(0)
            block_fmt.setRightMargin(0)
            block_fmt.setTopMargin(0)
            block_fmt.setBottomMargin(0)
            if style_name.startswith('Heading') or style_name in ('Title', 'Subtitle'):
                block_fmt.setTopMargin(12)
                block_fmt.setBottomMargin(12)
        cursor.setBlockFormat(block_fmt)
        cursor.setCharFormat(fmt)
        tab.text_edit.setTextCursor(cursor)
        tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    def toggle_bullet_list(self):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        current_list = cursor.currentList()
        if current_list and current_list.format().style() == QTextListFormat.Style.ListDisc:
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
            list_fmt = current_list.format()
            list_fmt.setIndent(list_fmt.indent() - 1)
            current_list.setFormat(list_fmt)
            current_list.remove(cursor.block())
        else:
            list_fmt = QTextListFormat()
            list_fmt.setStyle(QTextListFormat.Style.ListDisc)
            cursor.createList(list_fmt)
        tab.text_edit.setFocus()

    def toggle_numbered_list(self):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        current_list = cursor.currentList()
        if current_list and current_list.format().style() == QTextListFormat.Style.ListDecimal:
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
            list_fmt = current_list.format()
            list_fmt.setIndent(list_fmt.indent() - 1)
            current_list.setFormat(list_fmt)
            current_list.remove(cursor.block())
        else:
            list_fmt = QTextListFormat()
            list_fmt.setStyle(QTextListFormat.Style.ListDecimal)
            cursor.createList(list_fmt)
        tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------

    def insert_table(self):
        tab = self._get_tab()
        if not tab:
            return
        dialog = QDialog(self._parent)
        dialog.setWindowTitle("Insert Table")
        dialog.setModal(True)
        layout = QVBoxLayout()
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("Rows:"))
        from PyQt6.QtWidgets import QSpinBox as _QSpinBox
        rows_spin = _QSpinBox()
        rows_spin.setRange(1, 50)
        rows_spin.setValue(3)
        row_layout.addWidget(rows_spin)
        layout.addLayout(row_layout)
        col_layout = QHBoxLayout()
        col_layout.addWidget(QLabel("Columns:"))
        cols_spin = _QSpinBox()
        cols_spin.setRange(1, 20)
        cols_spin.setValue(3)
        col_layout.addWidget(cols_spin)
        layout.addLayout(col_layout)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        from PyQt6.QtWidgets import QDialog as _QDialog
        if dialog.exec() == _QDialog.DialogCode.Accepted:
            rows = rows_spin.value()
            cols = cols_spin.value()
            cursor = tab.text_edit.textCursor()
            table_fmt = QTextTableFormat()
            table_fmt.setBorder(1)
            table_fmt.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Solid)
            table_fmt.setCellPadding(5)
            table_fmt.setCellSpacing(0)
            table_fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
            cursor.insertTable(rows, cols, table_fmt)
        tab.text_edit.setFocus()

    def show_table_properties(self):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        table = cursor.currentTable()
        if not table:
            QMessageBox.information(self._parent, "Table Properties",
                                    "Please click inside a table first.")
            return
        dlg = TablePropertiesDialog(table, self._parent)
        dlg.exec()
        tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Hyperlinks
    # ------------------------------------------------------------------

    def add_link(self):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        selected_text = cursor.selectedText()
        char_fmt = cursor.charFormat()
        existing_url = char_fmt.anchorHref()
        if existing_url and not selected_text:
            from PyQt6.QtWidgets import QLineEdit
            url, ok = QInputDialog.getText(
                self._parent, "Edit Link", "Edit URL:",
                QLineEdit.EchoMode.Normal, existing_url
            )
            if ok and url:
                fmt = QTextCharFormat()
                fmt.setAnchor(True)
                fmt.setAnchorHref(url)
                fmt.setForeground(QBrush(QColor("#0078D4")))
                fmt.setFontUnderline(True)
                cursor.mergeCharFormat(fmt)
            tab.text_edit.setFocus()
            return
        from PyQt6.QtWidgets import QLineEdit
        url, ok = QInputDialog.getText(
            self._parent, "Insert Link", "Enter URL:",
            QLineEdit.EchoMode.Normal, "https://"
        )
        if not ok or not url:
            return
        if not selected_text:
            link_text, ok2 = QInputDialog.getText(
                self._parent, "Insert Link", "Enter link text:",
                QLineEdit.EchoMode.Normal, url
            )
            selected_text = link_text if (ok2 and link_text) else url
        fmt = QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref(url)
        fmt.setForeground(QBrush(QColor("#0078D4")))
        fmt.setFontUnderline(True)
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            cursor.insertText(selected_text, fmt)
        tab.text_edit.setFocus()

    # ------------------------------------------------------------------
    # Special inserts
    # ------------------------------------------------------------------

    def insert_horizontal_line(self):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        cursor.insertText('\n')
        cursor.insertText('─' * 60)
        cursor.insertText('\n')
        tab.text_edit.setFocus()

    def insert_code_block(self):
        tab = self._get_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        block_fmt = QTextBlockFormat()
        block_fmt.setBackground(QColor("#2b2b2b"))
        block_fmt.setLeftMargin(10)
        block_fmt.setRightMargin(10)
        block_fmt.setTopMargin(5)
        block_fmt.setBottomMargin(5)
        char_fmt = QTextCharFormat()
        char_fmt.setFontFamily("Courier New")
        char_fmt.setFontPointSize(10)
        char_fmt.setForeground(QColor("#00FF00"))
        char_fmt.setBackground(QColor("#1e1e1e"))
        if cursor.hasSelection():
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()
            selected_text = cursor.selectedText()
            cursor.setPosition(selection_start)
            cursor.beginEditBlock()
            cursor.setPosition(selection_end, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            cursor.insertBlock(block_fmt)
            cursor.setCharFormat(char_fmt)
            lines = selected_text.split('\u2029')
            for i, line in enumerate(lines):
                cursor.insertText(line)
                if i < len(lines) - 1:
                    cursor.insertBlock()
            cursor.endEditBlock()
            cursor.insertBlock()
        else:
            cursor.beginEditBlock()
            cursor.insertBlock(block_fmt)
            cursor.setCharFormat(char_fmt)
            cursor.insertText("# Enter your code here\n")
            cursor.endEditBlock()
        tab.text_edit.setTextCursor(cursor)
        tab.text_edit.setFocus()

    def insert_image(self):
        tab = self._get_tab()
        if not tab:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self._parent, "Insert Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        if not file_path:
            return
        try:
            image = QImage(file_path)
            if image.isNull():
                QMessageBox.warning(self._parent, "Error", "Could not load image file")
                return
            orig_width = image.width()
            orig_height = image.height()
            display_width = min(orig_width, 500)
            display_height = int((display_width / orig_width) * orig_height) if orig_width > 0 else orig_height
            cursor = tab.text_edit.textCursor()
            dialog = QDialog(self._parent)
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

            def on_width_changed(w):
                if aspect_ratio_cb.isChecked() and orig_width > 0:
                    height_spin.blockSignals(True)
                    height_spin.setValue(int((w / orig_width) * orig_height))
                    height_spin.blockSignals(False)

            def on_height_changed(h):
                if aspect_ratio_cb.isChecked() and orig_height > 0:
                    width_spin.blockSignals(True)
                    width_spin.setValue(int((h / orig_height) * orig_width))
                    width_spin.blockSignals(False)

            width_spin.valueChanged.connect(on_width_changed)
            height_spin.valueChanged.connect(on_height_changed)

            from PyQt6.QtWidgets import QDialog as _QDialog
            if dialog.exec() == _QDialog.DialogCode.Accepted:
                final_width = width_spin.value()
                final_height = height_spin.value()
                scaled_image = image.scaled(
                    final_width, final_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                cursor.insertImage(scaled_image, "image")
                cursor.insertText('\n')
                tab.text_edit.setTextCursor(cursor)
                QMessageBox.information(
                    self._parent, "Image Inserted",
                    f"Image inserted: {final_width}×{final_height}px\n\n"
                    "Tip: Right-click on the image to resize it further."
                )
        except Exception as e:
            QMessageBox.warning(self._parent, "Error", f"Failed to insert image: {str(e)}")
        tab.text_edit.setFocus()
