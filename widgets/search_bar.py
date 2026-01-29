from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal

class SearchBar(QWidget):
    """Custom search bar with find and replace functionality"""
    
    find_next_requested = pyqtSignal()
    find_prev_requested = pyqtSignal()
    close_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
      # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find...")

        # Valid font to avoid the QFont warning
        font = QFont()
        font.setPointSize(25)
        self.search_input.setFont(font)

        # Enable clear button
        self.search_input.setClearButtonEnabled(True)

        # Counter label
        self.counter_label = QLabel("0/0")
        self.counter_label.setStyleSheet("color: gray; min-width: 50px;")
        
        # Navigation buttons
        self.prev_btn = QPushButton("↑")
        self.prev_btn.setFixedWidth(35)
        self.prev_btn.setToolTip("Previous (Shift+F3)")
        
        self.next_btn = QPushButton("↓")
        self.next_btn.setFixedWidth(35)
        self.next_btn.setToolTip("Next (F3)")
        
        # Case sensitive checkbox
        self.case_sensitive_cb = QCheckBox("Aa")
        self.case_sensitive_cb.setToolTip("Match case")
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedWidth(35)
        self.close_btn.setToolTip("Close (Esc)")
        
        # Add to layout
        layout.addWidget(self.search_input)
        layout.addWidget(self.counter_label)
        layout.addWidget(self.case_sensitive_cb)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.close_btn)
        
        # Connect signals
        self.search_input.returnPressed.connect(self.find_next_requested)
        self.next_btn.clicked.connect(self.find_next_requested)
        self.prev_btn.clicked.connect(self.find_prev_requested)
        self.close_btn.clicked.connect(self.close_requested)
        
    def get_search_text(self) -> str:
        """Get current search text"""
        return self.search_input.text()
    
    def is_case_sensitive(self) -> bool:
        """Check if case sensitive search is enabled"""
        return self.case_sensitive_cb.isChecked()
    
    def update_counter(self, current: int, total: int):
        """Update the match counter display"""
        self.counter_label.setText(f"{current}/{total}")
        
    def focus_input(self):
        """Focus the search input and select all text"""
        self.search_input.setFocus()
        self.search_input.selectAll()


class StatusBarWidget(QWidget):
    """Custom status bar with document info"""
    
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(15)
        
        self.file_label = QLabel("No file")
        self.cursor_label = QLabel("Line 1, Col 1")
        self.word_count_label = QLabel("0 words")
        self.encoding_label = QLabel("UTF-8")
        
        layout.addWidget(self.file_label)
        layout.addStretch()
        layout.addWidget(self.word_count_label)
        layout.addWidget(self.cursor_label)
        layout.addWidget(self.encoding_label)
    
    def update_file(self, filepath: str):
        """Update file path display"""
        if filepath:
            self.file_label.setText(filepath)
        else:
            self.file_label.setText("No file")
    
    def update_cursor(self, line: int, col: int):
        """Update cursor position display"""
        self.cursor_label.setText(f"Line {line}, Col {col}")
    
    def update_word_count(self, words: int, chars: int):
        """Update word and character count"""
        self.word_count_label.setText(f"{words} words, {chars} chars")