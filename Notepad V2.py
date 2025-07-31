from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

class DocumentTab:
    def __init__(self, name=None):
        self.text_edit = QPlainTextEdit()
        self.current_file = None
        self.is_modified = False
        self.name = name or "New Document"

    def get_display_name(self):
        filename = self.current_file.split('/')[-1] if self.current_file else self.name
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
            min-height: 30px
        }
        QPushButton:hover {
            background-color: #5A5A5A;
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
        """

        self.setStyleSheet(style)
        self.setWindowTitle("Notepad")
        self.setFixedSize(QSize(1200, 700))

        # Create tab widget FIRST
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        # Now create and add the + button for new tabs
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
        
        # Create first tab
        self.new_tab()
        
        # Set up shortcuts
        self.setup_shortcuts()
        
        self.setCentralWidget(self.tab_widget)
        
    def setup_shortcuts(self):
        # Save shortcut
        saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        saveShortcut.activated.connect(self.save)
        
        # Open shortcut
        openShortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        openShortcut.activated.connect(self.open_file)
        
        # New tab shortcut
        newTabShortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        newTabShortcut.activated.connect(self.new_tab)
        
        # Close tab shortcut
        closeTabShortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        closeTabShortcut.activated.connect(self.close_current_tab)

    def new_tab(self):
        tab_name = f"New Document {self.tab_counter}"
        doc_tab = DocumentTab(tab_name)
        doc_tab.text_edit.textChanged.connect(lambda: self.text_changed(doc_tab))

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
    
    def tab_changed(self, index):
        if index >= 0 and index < len(self.tabs):
            doc_tab = self.tabs[index]
            self.update_window_title(doc_tab)

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
                with open(doc_tab.current_file, 'w') as file:
                    file.write(doc_tab.text_edit.toPlainText())
                    doc_tab.is_modified = False
                    self.update_tab_title(doc_tab)
                    self.update_window_title(doc_tab)  # Add this line
                    print(f"File saved: {doc_tab.current_file} ✅")
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
            "untitled.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as file:
                    file.write(doc_tab.text_edit.toPlainText())
                    doc_tab.current_file = filename
                    doc_tab.is_modified = False
                    self.update_tab_title(doc_tab)
                    self.update_window_title(doc_tab)
                    print(f"File saved as {filename} ✅")
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
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as file:
                    content = file.read()
                    
                    # Create new tab for opened file
                    doc_tab = DocumentTab()
                    doc_tab.text_edit.setPlainText(content)
                    doc_tab.current_file = filename
                    doc_tab.is_modified = False
                    
                    # Connect text changed signal
                    doc_tab.text_edit.textChanged.connect(lambda: self.text_changed(doc_tab))
                    
                    # Add tab
                    file_name = filename.split('/')[-1]
                    index = self.tab_widget.addTab(doc_tab.text_edit, file_name)
                    self.tabs.append(doc_tab)
                    
                    # Switch to new tab
                    self.tab_widget.setCurrentIndex(index)
                    
                    print(f"File opened: {filename} ✅")
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
        self.setWindowTitle(f"Notepad - {display_name}")

app = QApplication([])
window = MainWindow()
window.show()
app.exec()