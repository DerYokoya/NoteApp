
# ============================================================================
# Document Model
# ============================================================================

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QTextEdit

class DocumentTab:
    """Encapsulating a single document with its state and metadata"""
    
    def __init__(self, name: Optional[str] = None):
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setUndoRedoEnabled(True)  # Explicitly enable
        
        self.current_file: Optional[Path] = None
        self.name = name or "Untitled"
        self._last_saved_content = ""
        
        # Use Qt's built-in document modified tracking
        self.text_edit.document().setModified(False)
        
    @property
    def is_modified(self) -> bool:
        """Check if document has unsaved changes"""
        return self.text_edit.document().isModified()
    
    def mark_saved(self):
        """Mark document as saved"""
        self.text_edit.document().setModified(False)
        self._last_saved_content = self.text_edit.toHtml()
    
    def get_display_name(self) -> str:
        """Get the display name for tab/window title"""
        if self.current_file:
            filename = self.current_file.name
        else:
            filename = self.name
        return f"{'●' if self.is_modified else ''}{filename}"
    
    def get_file_path(self) -> str:
        """Get the file path as string, or empty if unsaved"""
        return str(self.current_file) if self.current_file else ""
    
    def get_content_html(self) -> str:
        """Get document content as HTML"""
        return self.text_edit.toHtml()
    
    def get_content_plain(self) -> str:
        """Get document content as plain text"""
        return self.text_edit.toPlainText()
    
    def set_content(self, content: str, is_html: bool = False):
        """Set document content, preserving undo stack"""
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        
        if is_html:
            self.text_edit.setHtml(content)
        else:
            self.text_edit.setPlainText(content)
            
        cursor.endEditBlock()
        self.text_edit.document().setModified(False)
        self._last_saved_content = content