from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout

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