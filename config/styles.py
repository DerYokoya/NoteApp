# ============================================================================
# Styles
# ============================================================================
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARROW_PATH = (BASE_DIR / "icons" / "down_arrow.svg").as_posix()

class StyleSheet:
    """Application-wide stylesheet"""
    DARK_THEME = (
        """
        QWidget {
            background-color: #2D2D2D;
            color: #E8E8E8;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }
        QLineEdit {
            padding: 4px 8px;
            border: 1px solid #555555;
            border-radius: 4px;
            min-height: 26px;
            background-color: #3A3A3A;
            color: #E8E8E8;
        }
        QLineEdit:focus { border: 1px solid #0078D4; }
        QPushButton {
            background-color: #484848;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #555555;
            color: #E8E8E8;
            margin: 0;
        }
        QPushButton:hover  { background-color: #565656; border-color: #666666; }
        QPushButton:pressed { background-color: #323232; }
        QPushButton:checked { background-color: #0078D4; border: 1px solid #0060AA; color: #FFFFFF; }
        QPushButton:disabled { background-color: #3A3A3A; color: #707070; border-color: #484848; }
        QTabWidget::pane { border: none; background-color: #2D2D2D; }
        QTabBar::tab {
            background-color: #3A3A3A; color: #CCCCCC;
            padding: 6px 14px; margin-right: 1px;
            border-top-left-radius: 4px; border-top-right-radius: 4px;
            border: 1px solid #484848; border-bottom: none; min-width: 80px;
        }
        QTabBar::tab:selected { background-color: #2D2D2D; color: #FFFFFF; border-bottom: 2px solid #0078D4; }
        QTabBar::tab:hover:!selected { background-color: #444444; }
        QMenuBar { background-color: #333333; border-bottom: 1px solid #222222; padding: 2px 0px; }
        QMenuBar::item { padding: 4px 12px; background-color: transparent; border-radius: 3px; }
        QMenuBar::item:selected { background-color: #484848; }
        QMenu { background-color: #383838; border: 1px solid #505050; border-radius: 4px; padding: 3px; }
        QMenu::item { padding: 5px 28px 5px 12px; border-radius: 3px; }
        QMenu::item:selected { background-color: #0078D4; color: #FFFFFF; }
        QMenu::separator { height: 1px; background: #505050; margin: 3px 8px; }
        QStatusBar { background-color: #1A1A1A; border-top: 1px solid #111111; color: #AAAAAA; font-size: 9pt; }
        QLabel { color: #CCCCCC; }
        QComboBox, QFontComboBox {
            min-height: 26px; padding: 3px 24px 3px 8px;
            border: 1px solid #555555; border-radius: 4px;
            background-color: #3A3A3A; color: #E8E8E8;
            selection-background-color: #0078D4;
        }
        QComboBox:hover { border: 1px solid #666666; }
        QComboBox:focus { border: 1px solid #0078D4; }
        QComboBox::drop-down {
            subcontrol-origin: padding; subcontrol-position: top right;
            width: 20px; border-left: 1px solid #555555; background-color: #484848;
            border-top-right-radius: 4px; border-bottom-right-radius: 4px;
        }
        QComboBox::down-arrow { image: url(\""""
        + ARROW_PATH +
        """\"); width: 10px; height: 10px; }
        QComboBox QAbstractItemView {
            background-color: #2D2D2D; border: 1px solid #555555;
            selection-background-color: #0078D4; outline: none; padding: 3px;
        }
        QTextEdit {
            background-color: #1A1A1A; color: #E8E8E8; border: none;
            font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt;
            padding: 20px 28px; selection-background-color: #0078D4;
        }
        QScrollBar:vertical { background: #252525; width: 10px; border: none; }
        QScrollBar::handle:vertical { background: #505050; border-radius: 5px; min-height: 20px; }
        QScrollBar::handle:vertical:hover { background: #606060; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        QScrollBar:horizontal { background: #252525; height: 10px; border: none; }
        QScrollBar::handle:horizontal { background: #505050; border-radius: 5px; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        QDialog { background-color: #2D2D2D; }
        QSpinBox, QDoubleSpinBox {
            background-color: #3A3A3A; border: 1px solid #555555; border-radius: 4px;
            padding: 3px 6px; color: #E8E8E8; min-height: 24px;
        }
        QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #0078D4; }
        QTableWidget { background-color: #252525; gridline-color: #404040; border: 1px solid #484848; }
        QTableWidget::item:selected { background-color: #0078D4; }
        QHeaderView::section { background-color: #383838; border: 1px solid #484848; padding: 4px 8px; }
        QListWidget { background-color: #252525; border: 1px solid #484848; border-radius: 4px; }
        QListWidget::item { padding: 4px 8px; }
        QListWidget::item:selected { background-color: #0078D4; }
        QCheckBox { color: #CCCCCC; spacing: 6px; }
        QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #555555; border-radius: 3px; background-color: #3A3A3A; }
        QCheckBox::indicator:checked { background-color: #0078D4; border-color: #0060AA; }
        QDialogButtonBox QPushButton { min-width: 80px; min-height: 28px; padding: 4px 16px; }
        QToolTip { background-color: #1A1A1A; color: #E8E8E8; border: 1px solid #555555; border-radius: 3px; padding: 4px 8px; font-size: 9pt; }
        """
    )
