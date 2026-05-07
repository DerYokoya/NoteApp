from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal
from config.styles import StyleSheet  # Import the global styles

class SearchBar(QWidget):
    """Custom search bar with find and replace functionality"""
    
    find_next_requested = pyqtSignal()
    find_prev_requested = pyqtSignal()
    close_requested = pyqtSignal()
    replace_requested = pyqtSignal()
    replace_all_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.show_replace = False
        
    def _setup_ui(self):
        # Apply global stylesheet
        self.setStyleSheet(StyleSheet.DARK_THEME)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Find row
        find_layout = QHBoxLayout()
        find_layout.setSpacing(5)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find...")
        self.search_input.setFixedHeight(28)
        font = QFont()
        font.setPointSize(10)
        self.search_input.setFont(font)
        self.search_input.setClearButtonEnabled(True)
        
        # Override background for search bar to match theme
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #E8E8E8;
            }
            QLineEdit:focus {
                border: 1px solid #0078D4;
            }
        """)

        # Counter label
        self.counter_label = QLabel("0/0")
        self.counter_label.setStyleSheet("color: #AAAAAA; min-width: 50px;")
        
        # Navigation buttons
        self.prev_btn = QPushButton("↑")
        self.prev_btn.setFixedWidth(35)
        self.prev_btn.setFixedHeight(28)
        self.prev_btn.setToolTip("Previous (Shift+F3)")
        
        self.next_btn = QPushButton("↓")
        self.next_btn.setFixedWidth(35)
        self.next_btn.setFixedHeight(28)
        self.next_btn.setToolTip("Next (F3)")
        
        # Case sensitive checkbox - use standard QCheckBox styling from global theme
        self.case_sensitive_cb = QCheckBox("Aa")
        self.case_sensitive_cb.setToolTip("Match case")
        
        # Toggle replace button - MAKE IT CHECKABLE
        self.toggle_replace_btn = QPushButton("≡")
        self.toggle_replace_btn.setFixedWidth(35)
        self.toggle_replace_btn.setFixedHeight(28)
        self.toggle_replace_btn.setToolTip("Toggle Replace (Ctrl+H)")
        self.toggle_replace_btn.setCheckable(True)  # Make it toggleable

        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedWidth(35)
        self.close_btn.setFixedHeight(28)
        self.close_btn.setToolTip("Close (Esc)")
        
        find_layout.addWidget(self.search_input)
        find_layout.addWidget(self.counter_label)
        find_layout.addWidget(self.case_sensitive_cb)
        find_layout.addWidget(self.prev_btn)
        find_layout.addWidget(self.next_btn)
        find_layout.addWidget(self.toggle_replace_btn)
        find_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(find_layout)
        
        # Replace row (hidden by default)
        replace_layout = QHBoxLayout()
        replace_layout.setSpacing(5)
        
        replace_label = QLabel("Replace:")
        replace_label.setStyleSheet("color: #AAAAAA;")
        replace_label.setFixedWidth(60)
        
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        self.replace_input.setFixedHeight(28)
        self.replace_input.setFont(font)
        
        # Override background for replace input
        self.replace_input.setStyleSheet("""
            QLineEdit {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #E8E8E8;
            }
            QLineEdit:focus {
                border: 1px solid #0078D4;
            }
        """)
        
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setFixedWidth(80)
        self.replace_btn.setFixedHeight(28)
        
        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.setFixedWidth(100)
        self.replace_all_btn.setFixedHeight(28)
        
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.replace_btn)
        replace_layout.addWidget(self.replace_all_btn)
        replace_layout.addStretch()
        
        self.replace_widget = QWidget()
        self.replace_widget.setLayout(replace_layout)
        self.replace_widget.setVisible(False)
        main_layout.addWidget(self.replace_widget)
        
        # Connect signals
        self.search_input.returnPressed.connect(self.find_next_requested)
        self.next_btn.clicked.connect(self.find_next_requested)
        self.prev_btn.clicked.connect(self.find_prev_requested)
        self.close_btn.clicked.connect(self.close_requested)
        self.toggle_replace_btn.clicked.connect(self.toggle_replace_mode)
        self.replace_btn.clicked.connect(self.replace_requested)
        self.replace_all_btn.clicked.connect(self.replace_all_requested)
        self.replace_input.returnPressed.connect(self.replace_requested)
        
    def toggle_replace_mode(self):
        """Toggle between find and find/replace mode"""
        self.show_replace = not self.show_replace
        self.replace_widget.setVisible(self.show_replace)
        self.toggle_replace_btn.setChecked(self.show_replace)
        
        # Update button check state to match visibility
        self.toggle_replace_btn.setChecked(self.show_replace)
        
        if self.show_replace:
            self.replace_input.setFocus()
        else:
            self.search_input.setFocus()
        
    def get_search_text(self) -> str:
        """Get current search text"""
        return self.search_input.text()
    
    def get_replace_text(self) -> str:
        """Get current replace text"""
        return self.replace_input.text()
    
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