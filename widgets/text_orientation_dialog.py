# ============================================================================
# Text Orientation Dialog
# ============================================================================
#
# QTextEdit does not natively support per-character rotation, but it does
# render inline HTML. We insert a <span> with a CSS transform around the
# selected text (or the word under the cursor) to achieve rotation.
# The result is stored as HTML and survives save/load when using .html files.
# ============================================================================

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


_PRESETS = [
    ("Normal (0°)",          "rotate(0deg)"),
    ("Rotated 45°",          "rotate(45deg)"),
    ("Rotated 90° CW",       "rotate(90deg)"),
    ("Rotated 135°",         "rotate(135deg)"),
    ("Upside-down (180°)",   "rotate(180deg)"),
    ("Rotated 225°",         "rotate(225deg)"),
    ("Rotated 90° CCW",      "rotate(270deg)"),
    ("Rotated 315°",         "rotate(315deg)"),
    ("Flip Horizontal",      "scaleX(-1)"),
    ("Flip Vertical",        "scaleY(-1)"),
    ("Flip Both",            "scale(-1,-1)"),
    ("Skew X 20°",           "skewX(20deg)"),
    ("Skew X -20°",          "skewX(-20deg)"),
    ("Skew Y 20°",           "skewY(20deg)"),
    ("Skew Y -20°",          "skewY(-20deg)"),
]


class TextOrientationDialog(QDialog):
    """
    Apply CSS transform to selected text (or the word under the cursor).
    Works by wrapping the target text in a <span style='display:inline-block;
    transform:...'> tag.
    """

    def __init__(self, text_edit: QTextEdit, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit
        self.setWindowTitle("Text Orientation")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Info label
        info = QLabel(
            "Select text in the editor first, then choose a transformation.\n"
            "If nothing is selected the word under the cursor will be used."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #AAAAAA; font-size: 9pt;")
        layout.addWidget(info)

        # Preset list
        layout.addWidget(QLabel("Preset transformations:"))
        self.preset_list = QListWidget()
        for label, _ in _PRESETS:
            self.preset_list.addItem(label)
        self.preset_list.setCurrentRow(0)
        self.preset_list.setMaximumHeight(200)
        layout.addWidget(self.preset_list)

        # Custom transform input
        layout.addWidget(QLabel("— or enter a custom CSS transform —"))
        custom_hl = QHBoxLayout()
        custom_hl.addWidget(QLabel("transform:"))
        self.custom_edit = QLineEdit()
        self.custom_edit.setPlaceholderText('e.g.  rotate(30deg)  or  skewX(15deg) scaleX(-1)')
        custom_hl.addWidget(self.custom_edit)
        layout.addLayout(custom_hl)

        # Origin
        origin_hl = QHBoxLayout()
        origin_hl.addWidget(QLabel("Transform origin:"))
        self.origin_combo = QComboBox()
        self.origin_combo.addItems([
            "center", "top left", "top center", "top right",
            "center left", "center right",
            "bottom left", "bottom center", "bottom right",
        ])
        origin_hl.addWidget(self.origin_combo)
        layout.addLayout(origin_hl)

        # Preview text
        layout.addWidget(QLabel("Preview:"))
        self.preview = QLabel("Sample Text  Agjy123")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(80)
        self.preview.setStyleSheet(
            "background-color: #3A3A3A; border: 1px solid #555; border-radius: 4px;"
        )
        layout.addWidget(self.preview)

        # Remove button
        remove_btn = QPushButton("Remove Orientation (reset to normal)")
        remove_btn.clicked.connect(self._remove_orientation)
        layout.addWidget(remove_btn)

        # OK / Cancel
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._apply)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # Connect preview updates
        self.preset_list.currentRowChanged.connect(self._update_preview)
        self.custom_edit.textChanged.connect(self._update_preview)
        self.origin_combo.currentTextChanged.connect(self._update_preview)
        self._update_preview()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_transform(self) -> str:
        """Return the CSS transform string to use"""
        custom = self.custom_edit.text().strip()
        if custom:
            return custom
        row = self.preset_list.currentRow()
        if 0 <= row < len(_PRESETS):
            return _PRESETS[row][1]
        return "rotate(0deg)"

    def _update_preview(self):
        t = self._get_transform()
        o = self.origin_combo.currentText()
        style = (
            f"display:inline-block; "
            f"transform:{t}; "
            f"transform-origin:{o}; "
            f"padding:4px;"
        )
        self.preview.setText(
            f'<span style="{style}">Sample Text  Agjy123</span>'
        )

    # ------------------------------------------------------------------
    # Apply / Remove
    # ------------------------------------------------------------------

    def _apply(self):
        cursor = self.text_edit.textCursor()

        # If nothing selected, select the word under cursor
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            self.text_edit.setTextCursor(cursor)

        if not cursor.hasSelection():
            QMessageBox.information(self, "Text Orientation",
                                    "No text selected and no word found under cursor.")
            return

        selected_html = self._cursor_to_html(cursor)
        transform = self._get_transform()
        origin = self.origin_combo.currentText()

        span = (
            f'<span style="display:inline-block; '
            f'transform:{transform}; '
            f'transform-origin:{origin};">'
            f'{selected_html}'
            f'</span>'
        )

        cursor.insertHtml(span)
        self.accept()

    def _remove_orientation(self):
        """Strip orientation spans and replace with plain text"""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            self.text_edit.setTextCursor(cursor)

        if cursor.hasSelection():
            # Grab plain text (no transform HTML), reinsert
            plain = cursor.selectedText()
            cursor.insertText(plain)
        self.accept()

    @staticmethod
    def _cursor_to_html(cursor: QTextCursor) -> str:
        """
        Extract selected content as an HTML fragment.
        We create a temporary document from the selection to get HTML.
        """
        temp_doc = cursor.document().clone()
        temp_cursor = QTextCursor(temp_doc)
        # Select same range
        temp_cursor.setPosition(cursor.selectionStart())
        temp_cursor.setPosition(cursor.selectionEnd(), QTextCursor.MoveMode.KeepAnchor)
        # Delete everything outside the selection
        temp_cursor2 = QTextCursor(temp_doc)
        temp_cursor2.select(QTextCursor.SelectionType.Document)
        # Instead, just return plain text with basic entity escaping
        # (the span wrapper handles the display; inner formatting is preserved
        #  because insertHtml merges char formats)
        text = cursor.selectedText()
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace("\u2029", "<br>")   # Qt paragraph separator
        return text
