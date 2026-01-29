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
            image: url(NoteApp/icons/down_arrow.svg);
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