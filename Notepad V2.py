from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import os

class DocumentTab:
    def __init__(self, name=None):
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.current_file = None
        self.is_modified = False
        self.name = name or "New Document"

    def get_display_name(self):
        if self.current_file:
            filename = os.path.basename(self.current_file)
        else:
            filename = self.name
        return f"{'*' if self.is_modified else ''}{filename}"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Track current file
        self.tabs = []
        self.tab_counter = 1

        style = """
        QWidget {
            background-color: #2D2D2D;
            color: #FFFFFF;
            font-family: Arial;
            font-size: 14px;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #555555;
            border-radius: 5px;
            min-height: 30px
        }
        QPushButton {
            background-color: #4A4A4A;
            padding: 8px 15px;
            border-radius: 5px;
            min-height: 30px;
            border: 1px solid #555555;
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
        QColorDialog {
            background-color: #2D2D2D;
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
        """

        self.setStyleSheet(style)
        self.setWindowTitle("Rich Text Notepad")
        self.setFixedSize(QSize(1200, 700))

        # Create menu bar
        self.create_menu_bar()

        # Create central widget with layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create formatting toolbar
        self.create_formatting_toolbar()
        layout.addWidget(self.format_toolbar)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        # Add + button for new tabs
        plus_button = QToolButton()
        plus_button.setText("+")
        plus_button.setStyleSheet("""
            QToolButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
                padding: 0px;
            }
            QToolButton:hover {
                background-color: #4A4A4A;
            }
            QToolButton:pressed {
                background-color: #353535;
            }
        """)
        plus_button.setFixedSize(25, 25)
        plus_button.clicked.connect(self.new_tab)
        self.tab_widget.setCornerWidget(plus_button, Qt.Corner.TopRightCorner)

        layout.addWidget(self.tab_widget)

        # --- Search Bar ---
        self.search_bar = QWidget()
        search_layout = QHBoxLayout(self.search_bar)
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find...")

        self.search_counter = QLabel("0/0")
        self.search_counter.setStyleSheet("color: gray;")

        self.find_next_btn = QPushButton("Next")
        self.find_prev_btn = QPushButton("Prev")
        self.close_search_btn = QPushButton("X")
        self.close_search_btn.setFixedWidth(30)
        self.close_search_btn.clicked.connect(self.hide_search_bar)

        # Add widgets to layout
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_counter)
        search_layout.addWidget(self.find_prev_btn)
        search_layout.addWidget(self.find_next_btn)
        search_layout.addWidget(self.close_search_btn)

        # Connect signals
        self.search_input.textChanged.connect(self.find_next)
        self.search_input.returnPressed.connect(self.find_next)

        self.search_bar.setLayout(search_layout)
        self.search_bar.setVisible(False)

        layout.addWidget(self.search_bar)

        self.setCentralWidget(central_widget)
        
        # Create first tab
        self.new_tab()
        
        # Set up shortcuts
        self.setup_shortcuts()

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")

        file_menu.addSeparator()
        delete_file_action = QAction("Delete File (Ctrl+Del)", self)
        delete_file_action.triggered.connect(self.delete_file)
        file_menu.addAction(delete_file_action)

        new_action = QAction("New (Ctrl+N)", self)
        new_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open File (Ctrl+O)", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Save File (Ctrl+S)", self)
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save File As (Ctrl+Shift+S)", self)
        save_as_action.triggered.connect(lambda: self.save_as())
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_tab_action = QAction("Close Tab (Ctrl + W)", self)
        close_tab_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_tab_action)
        
    def create_formatting_toolbar(self):
        self.format_toolbar = QToolBar("Formatting")
        self.format_toolbar.setMovable(False)
        
        # Bold button
        self.bold_btn = QPushButton("B")
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(60, 35)
        self.bold_btn.clicked.connect(self.toggle_bold)
        self.format_toolbar.addWidget(self.bold_btn)
        
        # Italic button
        self.italic_btn = QPushButton("I")
        self.italic_btn.setFont(QFont("Arial", 10, QFont.Weight.Normal, True))
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(60, 35)
        self.italic_btn.clicked.connect(self.toggle_italic)
        self.format_toolbar.addWidget(self.italic_btn)
        
        # Underline button
        self.underline_btn = QPushButton("U")
        font = QFont("Arial", 10)
        font.setUnderline(True)
        self.underline_btn.setFont(font)
        self.underline_btn.setCheckable(True)
        self.underline_btn.setFixedSize(60, 35)
        self.underline_btn.clicked.connect(self.toggle_underline)
        self.format_toolbar.addWidget(self.underline_btn)
        
        # Strikethrough button
        self.strike_btn = QPushButton("S")
        font = QFont("Arial", 10)
        font.setStrikeOut(True)
        self.strike_btn.setFont(font)
        self.strike_btn.setCheckable(True)
        self.strike_btn.setFixedSize(60, 35)
        self.strike_btn.clicked.connect(self.toggle_strikethrough)
        self.format_toolbar.addWidget(self.strike_btn)
        
        self.format_toolbar.addSeparator()
        
        # Text color button
        self.text_color_btn = QPushButton("A")
        self.text_color_btn.setStyleSheet("""
            QPushButton {
                color: #FF0000;
                font-weight: bold;
                border-bottom: 3px solid #FF0000;
            }
        """)
        self.text_color_btn.setFixedSize(60, 35)
        self.text_color_btn.clicked.connect(self.change_text_color)
        self.format_toolbar.addWidget(self.text_color_btn)
        
        # Background color button
        self.bg_color_btn = QPushButton("H")
        self.bg_color_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFF00;
                color: #000000;
                font-weight: bold;
            }
        """)
        self.bg_color_btn.setFixedSize(60, 35)
        self.bg_color_btn.clicked.connect(self.change_background_color)
        self.format_toolbar.addWidget(self.bg_color_btn)
        
        self.format_toolbar.addSeparator()
        
        # Link button
        self.link_btn = QPushButton("URL")
        self.link_btn.setFixedSize(60, 35)
        self.link_btn.clicked.connect(self.add_link)
        self.format_toolbar.addWidget(self.link_btn)
        
        # Remove formatting button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedSize(70, 35)
        self.clear_btn.clicked.connect(self.clear_formatting)
        self.format_toolbar.addWidget(self.clear_btn)
        
    def toggle_bold(self):
        current_tab = self.get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            is_bold = fmt.fontWeight() == QFont.Weight.Bold
            fmt.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
            current_tab.text_edit.setCurrentCharFormat(fmt)
            self.bold_btn.setChecked(not is_bold)
            current_tab.text_edit.setFocus()
    
    def toggle_italic(self):
        current_tab = self.get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            is_italic = fmt.fontItalic()
            fmt.setFontItalic(not is_italic)
            current_tab.text_edit.setCurrentCharFormat(fmt)
            self.italic_btn.setChecked(not is_italic)
            current_tab.text_edit.setFocus()

    def toggle_underline(self):
        current_tab = self.get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            is_underlined = fmt.fontUnderline()
            fmt.setFontUnderline(not is_underlined)
            current_tab.text_edit.setCurrentCharFormat(fmt)
            self.underline_btn.setChecked(not is_underlined)
            current_tab.text_edit.setFocus()
    
    def toggle_strikethrough(self):
        current_tab = self.get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            is_strike = fmt.fontStrikeOut()
            fmt.setFontStrikeOut(not is_strike)
            current_tab.text_edit.setCurrentCharFormat(fmt)
            self.strike_btn.setChecked(not is_strike)
            current_tab.text_edit.setFocus()
    
    def change_text_color(self):
        current_tab = self.get_current_tab()
        if current_tab:
            color = QColorDialog.getColor(Qt.GlobalColor.red, self, "Choose Text Color")
            if color.isValid():
                fmt = current_tab.text_edit.currentCharFormat()
                fmt.setForeground(QBrush(color))
                current_tab.text_edit.setCurrentCharFormat(fmt)
                
                # Update button color
                self.text_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {color.name()};
                        font-weight: bold;
                        border-bottom: 3px solid {color.name()};
                        background-color: #4A4A4A;
                    }}
                    QPushButton:hover {{
                        background-color: #5A5A5A;
                    }}
                """)
                current_tab.text_edit.setFocus()
    
    def change_background_color(self):
        current_tab = self.get_current_tab()
        if current_tab:
            color = QColorDialog.getColor(Qt.GlobalColor.yellow, self, "Choose Background Color")
            if color.isValid():
                fmt = current_tab.text_edit.currentCharFormat()
                fmt.setBackground(QBrush(color))
                current_tab.text_edit.setCurrentCharFormat(fmt)
                
                # Update button color
                text_color = "#000000" if color.lightness() > 128 else "#FFFFFF"
                self.bg_color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color.name()};
                        color: {text_color};
                        font-weight: bold;
                        border: 1px solid #555555;
                    }}
                    QPushButton:hover {{
                        opacity: 0.8;
                    }}
                """)
                current_tab.text_edit.setFocus()
    
    def add_link(self):
        current_tab = self.get_current_tab()
        if current_tab:
            cursor = current_tab.text_edit.textCursor()
            selected_text = cursor.selectedText()
            
            # Get URL from user
            url, ok = QInputDialog.getText(self, "Add Link", "Enter URL:")
            if ok and url:
                if not selected_text:
                    # If no text is selected, ask for link text
                    link_text, ok2 = QInputDialog.getText(self, "Add Link", "Enter link text:")
                    if ok2 and link_text:
                        selected_text = link_text
                    else:
                        selected_text = url
                
                # Create the link
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
        current_tab = self.get_current_tab()
        if current_tab:
            cursor = current_tab.text_edit.textCursor()
            if cursor.hasSelection():
                # Clear formatting for selected text
                fmt = QTextCharFormat()
                cursor.mergeCharFormat(fmt)
            else:
                # Reset current character format
                fmt = QTextCharFormat()
                current_tab.text_edit.setCurrentCharFormat(fmt)
            current_tab.text_edit.setFocus()
    
    def update_format_buttons(self):
        current_tab = self.get_current_tab()
        if current_tab:
            fmt = current_tab.text_edit.currentCharFormat()
            
            # Update button states
            self.bold_btn.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
            self.italic_btn.setChecked(fmt.fontItalic())
            self.underline_btn.setChecked(fmt.fontUnderline())
            self.strike_btn.setChecked(fmt.fontStrikeOut())

    def show_search_bar(self):
        self.search_bar.setVisible(True)
        self.search_input.setFocus()

    def hide_search_bar(self):
        self.search_bar.setVisible(False)
        current_tab = self.get_current_tab()
        if current_tab:
            cursor = current_tab.text_edit.textCursor()
            cursor.clearSelection()
            current_tab.text_edit.setTextCursor(cursor)

    def find_next(self, backward=False):
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        text_edit = current_tab.text_edit
        search_text = self.search_input.text().strip()
        if not search_text:
            text_edit.setExtraSelections([])
            self.update_search_counter(0, 0)
            return

        # Count total matches
        document_text = text_edit.toPlainText()
        occurrences = []
        start = 0
        while True:
            start = document_text.find(search_text, start)
            if start == -1:
                break
            occurrences.append(start)
            start += len(search_text)

        total = len(occurrences)
        if total == 0:
            text_edit.setExtraSelections([])
            self.update_search_counter(0, 0)
            return

        # Find next occurrence
        flags = QTextDocument.FindFlag(0)
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward

        found = text_edit.find(search_text, flags)

        # Wrap around
        if not found:
            cursor = text_edit.textCursor()
            if backward:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            text_edit.setTextCursor(cursor)
            text_edit.find(search_text, flags)

        # Get current match index
        current_pos = text_edit.textCursor().selectionStart()
        current_index = 0
        for i, pos in enumerate(occurrences):
            if pos == current_pos:
                current_index = i
                break

        # Highlight all with current one in orange
        self.highlight_all_occurrences(search_text, current_index)

        # Update counter label in search bar
        self.update_search_counter(current_index + 1, total)

    def update_search_counter(self, current, total):
        """Update the small counter next to the search bar."""
        if total == 0:
            self.search_counter.setText("0/0")
        else:
            self.search_counter.setText(f"{current}/{total}")

    def count_word_occurrences(self, term_to_search):
        current_tab = self.get_current_tab()
        if not current_tab:
            return 0

        text_edit = current_tab.text_edit
        document_text = text_edit.toPlainText()

        # Count case-insensitive matches
        return document_text.lower().count(term_to_search.lower())

    def highlight_all_occurrences(self, term, current_index=None):
        """Highlight all occurrences and mark the current one in orange."""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        text_edit = current_tab.text_edit
        cursor = text_edit.textCursor()
        extraSelections = []

        if not term:
            text_edit.setExtraSelections([])
            return

        text = text_edit.toPlainText()
        start = 0
        match_index = 0

        while True:
            start = text.find(term, start)
            if start == -1:
                break

            selection = QTextEdit.ExtraSelection()
            cursor = QTextCursor(text_edit.document())
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(term))
            selection.cursor = cursor

            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.Right,
                                QTextCursor.MoveMode.KeepAnchor, len(term))
            selection.cursor = cursor
            extraSelections.append(selection)
            start += len(term)
            match_index += 1

        text_edit.setExtraSelections(extraSelections)

    def highlight_current_occurrence(self, term):
        """Highlight only the current selected match in a stronger color."""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        text_edit = current_tab.text_edit
        cursor = text_edit.textCursor()
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor

        # Keep previous highlights + current one
        existing = text_edit.extraSelections()
        existing.append(selection)
        text_edit.setExtraSelections(existing)

    def switch_to_tab(self, tab_number):
        """Switch to tab by number (1-9), or to last tab if 9 and more than 9 tabs exist"""
        if tab_number == 9:
            # Ctrl+9 goes to last tab
            last_index = self.tab_widget.count() - 1
            if last_index >= 0:
                self.tab_widget.setCurrentIndex(last_index)
        else:
            # Ctrl+1 through Ctrl+8 go to specific tabs
            tab_index = tab_number - 1
            if 0 <= tab_index < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(tab_index)

    def setup_shortcuts(self):
        # Delete current file shortcut
        deleteFileShortcut = QShortcut(QKeySequence("Ctrl+Delete"), self)
        deleteFileShortcut.activated.connect(self.delete_file)

        # Search shortcut
        findShortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        findShortcut.activated.connect(self.show_search_bar)

        # Save shortcut
        saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        saveShortcut.activated.connect(self.save)
        
        # Save As shortcut
        saveAsShortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        saveAsShortcut.activated.connect(lambda: self.save_as())
        
        # Open shortcut
        openShortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        openShortcut.activated.connect(self.open_file)
        
        # New tab shortcut
        newTabShortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        newTabShortcut.activated.connect(self.new_tab)
        
        # Close tab shortcut
        closeTabShortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        closeTabShortcut.activated.connect(self.close_current_tab)
        
        # Formatting shortcuts
        boldShortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        boldShortcut.activated.connect(self.toggle_bold)
        
        italicShortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        italicShortcut.activated.connect(self.toggle_italic)
        
        underlineShortcut = QShortcut(QKeySequence("Ctrl+U"), self)
        underlineShortcut.activated.connect(self.toggle_underline)

        # Tab navigation shortcuts (Ctrl+1 through Ctrl+9)
        for i in range(1, 10):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(lambda num=i: self.switch_to_tab(num))

    def new_tab(self):
        tab_name = f"New Document {self.tab_counter}"
        doc_tab = DocumentTab(tab_name)
        doc_tab.text_edit.textChanged.connect(lambda: self.text_changed(doc_tab))
        doc_tab.text_edit.cursorPositionChanged.connect(self.update_format_buttons)

        index = self.tab_widget.addTab(doc_tab.text_edit, doc_tab.get_display_name())
        self.tabs.append(doc_tab)
        self.tab_widget.setCurrentIndex(index)
        self.tab_counter += 1
        
    def close_tab(self, index):
        if self.tab_widget.count() <= 1:
            return  # Don't close the last tab
            
        doc_tab = self.tabs[index]
        
        # Check if document is modified
        if doc_tab.is_modified:
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                f"Do you want to save changes to {doc_tab.get_display_name().replace('*', '')}?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_document(doc_tab):
                    return  # Don't close if save failed
            elif reply == QMessageBox.StandardButton.Cancel:
                return  # Don't close
        
        # Remove tab
        self.tab_widget.removeTab(index)
        self.tabs.pop(index)
        
    def close_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)
    
    def delete_file(self):
        current_tab = self.get_current_tab()
        if not current_tab or not current_tab.current_file:
            QMessageBox.information(self, "Delete File", "No file to delete.")
            return
        
        filename = current_tab.current_file
        reply = QMessageBox.question(
            self,
            "Delete File",
            f"Are you sure you want to delete '{os.path.basename(filename)}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(filename)
                self.statusBar().showMessage(f"File deleted: {filename}", 3000)
                
                # Close the tab after deletion
                current_index = self.tab_widget.currentIndex()
                self.close_tab(current_index)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete file:\n{str(e)}")
    


    def tab_changed(self, index):
        if index >= 0 and index < len(self.tabs):
            doc_tab = self.tabs[index]
            self.update_window_title(doc_tab)
            self.update_format_buttons()

    def text_changed(self, doc_tab):
        if not doc_tab.is_modified:
            doc_tab.is_modified = True
            self.update_tab_title(doc_tab)
            self.update_window_title(doc_tab)
    
    def get_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0 and current_index < len(self.tabs):
            return self.tabs[current_index]
        return None
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def save(self):
        current_tab = self.get_current_tab()
        if current_tab:
            self.save_document(current_tab)
    
    def save_document(self, doc_tab):
        # If we already have a file, just save to it
        if doc_tab.current_file:
            try:
                with open(doc_tab.current_file, 'w', encoding='utf-8') as file:
                    # Save as HTML to preserve formatting
                    if doc_tab.current_file.endswith('.html'):
                        file.write(doc_tab.text_edit.toHtml())
                    else:
                        file.write(doc_tab.text_edit.toPlainText())
                    doc_tab.is_modified = False
                    self.update_tab_title(doc_tab)
                    self.update_window_title(doc_tab)
                    self.statusBar().showMessage(f"File saved: {doc_tab.current_file}", 3000)
                    return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")
                return False
        else:
            # New document - ask for filename
            return self.save_as(doc_tab)
    
    def save_as(self, doc_tab=None):
        if not doc_tab:
            doc_tab = self.get_current_tab()
        if not doc_tab:
            return False
            
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "untitled.html",
            "HTML Files (*.html);;Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    # Save as HTML to preserve formatting
                    if filename.endswith('.html'):
                        file.write(doc_tab.text_edit.toHtml())
                    else:
                        file.write(doc_tab.text_edit.toPlainText())
                    doc_tab.current_file = filename
                    doc_tab.is_modified = False
                    self.update_tab_title(doc_tab)
                    self.update_window_title(doc_tab)
                    self.statusBar().showMessage(f"File saved as: {filename}", 3000)
                    return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")
                return False
        return False
    
    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Supported Files (*.html *.txt);;HTML Files (*.html);;Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            # Check if file is already open in a tab
            for i, tab in enumerate(self.tabs):
                if tab.current_file == filename:
                    self.tab_widget.setCurrentIndex(i)
                    self.statusBar().showMessage(f"File already open: {filename}", 3000)
                    return
            
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                    # Create new tab for opened file
                    doc_tab = DocumentTab()
                    
                    # Load content based on file type
                    if filename.endswith('.html'):
                        doc_tab.text_edit.setHtml(content)
                    else:
                        doc_tab.text_edit.setPlainText(content)
                    
                    doc_tab.current_file = filename
                    doc_tab.is_modified = False
                    
                    # Connect signals
                    doc_tab.text_edit.textChanged.connect(lambda: self.text_changed(doc_tab))
                    doc_tab.text_edit.cursorPositionChanged.connect(self.update_format_buttons)
                    
                    # Add tab
                    file_name = os.path.basename(filename)
                    index = self.tab_widget.addTab(doc_tab.text_edit, file_name)
                    self.tabs.append(doc_tab)
                    
                    # Switch to new tab
                    self.tab_widget.setCurrentIndex(index)
                    
                    self.statusBar().showMessage(f"File opened: {filename}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file:\n{str(e)}")
    
    def update_tab_title(self, doc_tab):
        # Find the tab index
        for i, tab in enumerate(self.tabs):
            if tab == doc_tab:
                self.tab_widget.setTabText(i, doc_tab.get_display_name())
                break
    
    def update_window_title(self, doc_tab):
        display_name = doc_tab.get_display_name()
        self.setWindowTitle(f"Rich Text Notepad - {display_name}")

app = QApplication([])
window = MainWindow()
window.show()
app.exec()