# ============================================================================
# Table Properties Dialog
# ============================================================================

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


class TablePropertiesDialog(QDialog):
    """Dialog for editing table size, borders, and column widths"""

    BORDER_STYLES = {
        "None":   QTextFrameFormat.BorderStyle.BorderStyle_None,
        "Solid":  QTextFrameFormat.BorderStyle.BorderStyle_Solid,
        "Dashed": QTextFrameFormat.BorderStyle.BorderStyle_Dashed,
        "Dotted": QTextFrameFormat.BorderStyle.BorderStyle_Dotted,
        "Double": QTextFrameFormat.BorderStyle.BorderStyle_Double,
        "Groove": QTextFrameFormat.BorderStyle.BorderStyle_Groove,
        "Ridge":  QTextFrameFormat.BorderStyle.BorderStyle_Ridge,
        "Inset":  QTextFrameFormat.BorderStyle.BorderStyle_Inset,
        "Outset": QTextFrameFormat.BorderStyle.BorderStyle_Outset,
    }

    def __init__(self, table: QTextTable, parent=None):
        super().__init__(parent)
        self.table = table
        self.setWindowTitle("Table Properties")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        self._load_current_values()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        tabs = QTabWidget()
        root.addWidget(tabs)

        tabs.addTab(self._build_structure_tab(), "Structure")
        tabs.addTab(self._build_border_tab(),    "Borders")
        tabs.addTab(self._build_columns_tab(),   "Columns")

        # OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    # --- Structure tab ------------------------------------------------

    def _build_structure_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Table properties form
        form = QFormLayout()
        form.setVerticalSpacing(10)

        # Table width
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 100)
        self.width_spin.setSuffix(" %")
        self.width_spin.setValue(100)
        form.addRow("Table width:", self.width_spin)

        # Cell padding
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 50)
        self.padding_spin.setSuffix(" px")
        form.addRow("Cell padding:", self.padding_spin)

        # Cell spacing
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 30)
        self.spacing_spin.setSuffix(" px")
        form.addRow("Cell spacing:", self.spacing_spin)

        layout.addLayout(form)

        # Add spacing before rows/columns section
        layout.addSpacing(16)

        # Add / remove rows
        row_label = QLabel("Rows:")
        layout.addWidget(row_label)

        row_hl = QHBoxLayout()
        row_hl.setSpacing(8)
        self.add_rows_spin = QSpinBox()
        self.add_rows_spin.setRange(1, 50)
        self.add_rows_spin.setValue(1)
        self.add_rows_spin.setMaximumWidth(60)
        add_row_btn = QPushButton("Add Rows")
        add_row_btn.clicked.connect(self._add_rows)
        del_row_btn = QPushButton("Remove Last Row")
        del_row_btn.clicked.connect(self._remove_last_row)
        row_hl.addWidget(self.add_rows_spin)
        row_hl.addSpacing(12)
        row_hl.addWidget(add_row_btn)
        row_hl.addWidget(del_row_btn)
        row_hl.addStretch()
        layout.addLayout(row_hl)

        # Add spacing
        layout.addSpacing(12)

        # Add / remove columns
        col_label = QLabel("Columns:")
        layout.addWidget(col_label)

        col_hl = QHBoxLayout()
        col_hl.setSpacing(8)
        self.add_cols_spin = QSpinBox()
        self.add_cols_spin.setRange(1, 20)
        self.add_cols_spin.setValue(1)
        self.add_cols_spin.setMaximumWidth(60)
        add_col_btn = QPushButton("Add Columns")
        add_col_btn.clicked.connect(self._add_cols)
        del_col_btn = QPushButton("Remove Last Column")
        del_col_btn.clicked.connect(self._remove_last_col)
        col_hl.addWidget(self.add_cols_spin)
        col_hl.addSpacing(12)
        col_hl.addWidget(add_col_btn)
        col_hl.addWidget(del_col_btn)
        col_hl.addStretch()
        layout.addLayout(col_hl)

        # Live info
        layout.addSpacing(16)
        self.info_label = QLabel()
        self._refresh_info()
        info_layout = QFormLayout()
        info_layout.addRow("Current size:", self.info_label)
        layout.addLayout(info_layout)
        
        layout.addStretch()

        return w

    # --- Border tab ---------------------------------------------------

    def _build_border_tab(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setVerticalSpacing(10)

        self.border_style_combo = QComboBox()
        self.border_style_combo.addItems(list(self.BORDER_STYLES.keys()))
        layout.addRow("Border style:", self.border_style_combo)

        self.border_width_spin = QDoubleSpinBox()
        self.border_width_spin.setRange(0, 20)
        self.border_width_spin.setSingleStep(0.5)
        self.border_width_spin.setSuffix(" px")
        layout.addRow("Border width:", self.border_width_spin)

        # Border colour
        self.border_color = QColor("#888888")
        self.border_color_btn = QPushButton()
        self._update_color_btn(self.border_color_btn, self.border_color)
        self.border_color_btn.clicked.connect(self._pick_border_color)
        layout.addRow("Border colour:", self.border_color_btn)

        # Background colour
        self.bg_color = QColor(Qt.GlobalColor.transparent)
        self.bg_color_btn = QPushButton()
        self._update_color_btn(self.bg_color_btn, self.bg_color)
        self.bg_color_btn.clicked.connect(self._pick_bg_color)
        layout.addRow("Background colour:", self.bg_color_btn)

        return w

    # --- Columns tab --------------------------------------------------

    def _build_columns_tab(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(12, 12, 12, 12)

        vl.addWidget(QLabel(
            "Set individual column widths (percentage of table, "
            "or 0 to auto-distribute):"
        ))

        self.col_table = QTableWidget()
        self.col_table.setColumnCount(2)
        self.col_table.setHorizontalHeaderLabels(["Column", "Width (%)"])
        self.col_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.col_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        vl.addWidget(self.col_table)

        even_btn = QPushButton("Distribute Evenly")
        even_btn.clicked.connect(self._distribute_evenly)
        vl.addWidget(even_btn)

        return w

    # ------------------------------------------------------------------
    # Load current table values
    # ------------------------------------------------------------------

    def _load_current_values(self):
        fmt = self.table.format()

        # Structure
        w = fmt.width()
        if w.type() == QTextLength.Type.PercentageLength:
            self.width_spin.setValue(int(w.rawValue()))
        self.padding_spin.setValue(int(fmt.cellPadding()))
        self.spacing_spin.setValue(int(fmt.cellSpacing()))

        # Borders
        style_name = "Solid"
        for name, val in self.BORDER_STYLES.items():
            if val == fmt.borderStyle():
                style_name = name
                break
        self.border_style_combo.setCurrentText(style_name)
        self.border_width_spin.setValue(fmt.border())
        bc = fmt.borderBrush().color()
        if bc.isValid():
            self.border_color = bc
            self._update_color_btn(self.border_color_btn, self.border_color)
        bg = fmt.background().color()
        if bg.isValid():
            self.bg_color = bg
            self._update_color_btn(self.bg_color_btn, self.bg_color)

        # Columns
        n_cols = self.table.columns()
        self.col_table.setRowCount(n_cols)
        col_widths = fmt.columnWidthConstraints()
        for i in range(n_cols):
            name_item = QTableWidgetItem(f"Column {i + 1}")
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.col_table.setItem(i, 0, name_item)
            pct = 0.0
            if i < len(col_widths):
                cw = col_widths[i]
                if cw.type() == QTextLength.Type.PercentageLength:
                    pct = cw.rawValue()
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setSuffix(" %")
            spin.setSpecialValueText("Auto")
            spin.setValue(pct)
            self.col_table.setCellWidget(i, 1, spin)

    # ------------------------------------------------------------------
    # Apply changes
    # ------------------------------------------------------------------

    def _apply(self):
        fmt = self.table.format()

        # Structure
        fmt.setWidth(QTextLength(
            QTextLength.Type.PercentageLength,
            self.width_spin.value()
        ))
        fmt.setCellPadding(self.padding_spin.value())
        fmt.setCellSpacing(self.spacing_spin.value())

        # Borders
        fmt.setBorderStyle(self.BORDER_STYLES[self.border_style_combo.currentText()])
        fmt.setBorder(self.border_width_spin.value())
        fmt.setBorderBrush(QBrush(self.border_color))
        if self.bg_color != Qt.GlobalColor.transparent:
            fmt.setBackground(QBrush(self.bg_color))
        else:
            fmt.clearBackground()

        # Column widths
        n_cols = self.table.columns()
        constraints = []
        for i in range(n_cols):
            widget = self.col_table.cellWidget(i, 1)
            if widget:
                val = widget.value()
                if val > 0:
                    constraints.append(
                        QTextLength(QTextLength.Type.PercentageLength, val)
                    )
                else:
                    constraints.append(QTextLength())   # auto
            else:
                constraints.append(QTextLength())
        fmt.setColumnWidthConstraints(constraints)

        self.table.setFormat(fmt)
        self.accept()

    # ------------------------------------------------------------------
    # Row / column helpers
    # ------------------------------------------------------------------

    def _add_rows(self):
        n = self.add_rows_spin.value()
        self.table.insertRows(self.table.rows(), n)
        self._refresh_info()
        self._reload_col_tab()

    def _remove_last_row(self):
        if self.table.rows() > 1:
            self.table.removeRows(self.table.rows() - 1, 1)
            self._refresh_info()
        else:
            QMessageBox.warning(self, "Remove Row", "Cannot remove the last row.")

    def _add_cols(self):
        n = self.add_cols_spin.value()
        self.table.insertColumns(self.table.columns(), n)
        self._refresh_info()
        self._reload_col_tab()

    def _remove_last_col(self):
        if self.table.columns() > 1:
            self.table.removeColumns(self.table.columns() - 1, 1)
            self._refresh_info()
            self._reload_col_tab()
        else:
            QMessageBox.warning(self, "Remove Column", "Cannot remove the last column.")

    def _refresh_info(self):
        self.info_label.setText(
            f"{self.table.rows()} rows × {self.table.columns()} columns"
        )

    def _reload_col_tab(self):
        """Sync column tab after structure changes"""
        n_cols = self.table.columns()
        old_count = self.col_table.rowCount()
        self.col_table.setRowCount(n_cols)
        for i in range(old_count, n_cols):
            name_item = QTableWidgetItem(f"Column {i + 1}")
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.col_table.setItem(i, 0, name_item)
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setSuffix(" %")
            spin.setSpecialValueText("Auto")
            spin.setValue(0)
            self.col_table.setCellWidget(i, 1, spin)

    def _distribute_evenly(self):
        n = self.col_table.rowCount()
        if n == 0:
            return
        each = round(100.0 / n, 1)
        for i in range(n):
            w = self.col_table.cellWidget(i, 1)
            if w:
                w.setValue(each)

    # ------------------------------------------------------------------
    # Colour helpers
    # ------------------------------------------------------------------

    def _pick_border_color(self):
        c = QColorDialog.getColor(self.border_color, self, "Border Colour")
        if c.isValid():
            self.border_color = c
            self._update_color_btn(self.border_color_btn, c)

    def _pick_bg_color(self):
        c = QColorDialog.getColor(self.bg_color, self, "Background Colour",
                                   QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if c.isValid():
            self.bg_color = c
            self._update_color_btn(self.bg_color_btn, c)

    @staticmethod
    def _update_color_btn(btn: QPushButton, color: QColor):
        lum = color.lightnessF()
        text_color = "#000000" if lum > 0.5 else "#FFFFFF"
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {color.name()}; "
            f"color: {text_color}; border: 1px solid #555; }}"
        )
        btn.setText(color.name().upper())
