"""
ContextMenuController
=====================
Builds and shows the right-click context menu for every QTextEdit in the
application.  Previously this logic lived in ``MainWindow._show_context_menu``
and ``MainWindow._resize_image_at_cursor``.

Responsibilities
----------------
- Standard Qt edit actions (cut/copy/paste/undo/redo) via
  ``QTextEdit.createStandardContextMenu()``.
- In-table sub-menu: insert/delete rows & columns, table properties.
- Alignment sub-menu (delegates back to FormattingController).
- Image resize dialog when the cursor is on an embedded image.
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QCheckBox, QDialogButtonBox,
    QMessageBox, QTextEdit, QMenu,
)
from PyQt6.QtGui import (
    QTextFormat, QTextDocument, QImage,
)
from PyQt6.QtCore import Qt, QUrl, QPoint

from widgets.table_dialog import TablePropertiesDialog


class ContextMenuController:
    """Builds and executes the context menu for a given QTextEdit."""

    def __init__(self, set_alignment_fn, parent_widget):
        """
        Parameters
        ----------
        set_alignment_fn : callable(Qt.AlignmentFlag)
            Delegated to FormattingController.set_alignment inside the window.
        parent_widget    : QWidget  (dialogs are parented here)
        """
        self._set_alignment = set_alignment_fn
        self._parent = parent_widget

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def show(self, pos: QPoint, text_edit: QTextEdit):
        """Build and exec the context menu at *pos* inside *text_edit*."""
        menu = text_edit.createStandardContextMenu()

        cursor = text_edit.cursorForPosition(pos)
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
            del_row   = table_menu.addAction("Delete Row")
            del_col   = table_menu.addAction("Delete Column")
            table_menu.addSeparator()
            table_props = table_menu.addAction("Table Properties…")

            cell = table.cellAt(cursor)
            row  = cell.row()
            col  = cell.column()

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
                lambda: self._open_table_props(table, text_edit)
            )

        menu.addSeparator()
        align_menu = menu.addMenu("Alignment")
        align_menu.addAction("Align Left",  lambda: self._set_alignment(Qt.AlignmentFlag.AlignLeft))
        align_menu.addAction("Center",      lambda: self._set_alignment(Qt.AlignmentFlag.AlignHCenter))
        align_menu.addAction("Align Right", lambda: self._set_alignment(Qt.AlignmentFlag.AlignRight))
        align_menu.addAction("Justify",     lambda: self._set_alignment(Qt.AlignmentFlag.AlignJustify))

        char_fmt = cursor.charFormat()
        image_name = char_fmt.stringProperty(QTextFormat.Property.ImageName)
        if image_name:
            menu.addSeparator()
            resize_action = menu.addAction("Resize Image…")
            resize_action.triggered.connect(lambda: self._resize_image(text_edit))

        menu.exec(text_edit.mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _open_table_props(self, table, text_edit: QTextEdit):
        dlg = TablePropertiesDialog(table, self._parent)
        dlg.exec()
        text_edit.setFocus()

    def _resize_image(self, text_edit: QTextEdit):
        cursor   = text_edit.textCursor()
        char_fmt = cursor.charFormat()
        image_name = char_fmt.stringProperty(QTextFormat.Property.ImageName)
        if not image_name:
            QMessageBox.information(self._parent, "Resize Image",
                                    "No image found at cursor position.")
            return

        doc   = text_edit.document()
        image = doc.resource(QTextDocument.ResourceType.ImageResource, QUrl(image_name))
        if image.isNull() or not isinstance(image, QImage):
            QMessageBox.warning(self._parent, "Error", "Could not access image data.")
            return

        dialog = QDialog(self._parent)
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

        aspect_cb = QCheckBox()
        aspect_cb.setChecked(True)
        layout.addRow("Maintain Aspect Ratio:", aspect_cb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        orig_w, orig_h = image.width(), image.height()

        def on_width_changed(w):
            if aspect_cb.isChecked() and orig_w > 0:
                height_spin.blockSignals(True)
                height_spin.setValue(int((w / orig_w) * orig_h))
                height_spin.blockSignals(False)

        def on_height_changed(h):
            if aspect_cb.isChecked() and orig_h > 0:
                width_spin.blockSignals(True)
                width_spin.setValue(int((h / orig_h) * orig_w))
                width_spin.blockSignals(False)

        width_spin.valueChanged.connect(on_width_changed)
        height_spin.valueChanged.connect(on_height_changed)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_w = width_spin.value()
            new_h = height_spin.value()
            scaled = image.scaled(
                new_w, new_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(image_name), scaled)
            text_edit.updateGeometry()
            text_edit.viewport().update()
            QMessageBox.information(self._parent, "Image Resized",
                                    f"Image resized to {new_w}×{new_h}px")
