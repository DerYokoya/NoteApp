# ============================================================================
# Styles
# ============================================================================
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARROW_PATH = (BASE_DIR / "icons" / "down_arrow.svg").as_posix()
class StyleSheet:
    """Application-wide stylesheet"""
    DARK_THEME = """
        QWidget {
            background-color: #2D2D2D;
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10.5pt;
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
            min-height: 30px;
            padding: 5px 30px 5px 10px; /* space for arrow */
            border: 1px solid #555555;
            border-radius: 5px;
            background-color: #3D3D3D;
            selection-background-color: #0078D4;
        }

        QComboBox:hover {
            border: 1px solid #666666;
        }

        QComboBox:focus {
            border: 1px solid #0078D4;
        }

        /* The dropdown button area */
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;
            border-left: 1px solid #555555;
            background-color: #404040;
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }

        /* The arrow itself */
        QComboBox::down-arrow {
            image: url(""" + ARROW_PATH + """);
            width: 12px;
            height: 12px;
        }

        /* When pressed */
        QComboBox::down-arrow:on {
            top: 1px;
        }

        /* The popup list */
        QComboBox QAbstractItemView {
            background-color: #2D2D2D;
            border: 1px solid #555555;
            selection-background-color: #0078D4;
            outline: none;
            padding: 5px;
        }
    """