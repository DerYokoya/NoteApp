# ============================================================================
# Document Model
# ============================================================================

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QMouseEvent, QImage
from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODevice, QUrl
import webbrowser
import re


class LinkAwareTextEdit(QTextEdit):
    """Custom QTextEdit that opens links on Ctrl+Click"""
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse click - open links on Ctrl+Click"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier: # Get the cursor at click position
            cursor = self.cursorForPosition(event.pos())
            char_fmt = cursor.charFormat()
            url = char_fmt.anchorHref()
            
            if url:
                # Open URL in default browser
                try:
                    webbrowser.open(url)
                except Exception as e:
                    print(f"Failed to open URL: {e}")
                event.accept()
                return
        
        # Normal click handling
        super().mousePressEvent(event)


class DocumentTab:
    """Encapsulating a single document with its state and metadata"""
    
    def __init__(self, name: Optional[str] = None):
        self.text_edit = LinkAwareTextEdit()
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
        """Get document content as HTML with embedded images"""
        html = self.text_edit.toHtml()
        
        # Find all src="..." values in the HTML and embed any resolvable images
        doc = self.text_edit.document()
        
        def embed_image(match):
            src = match.group(1)
            # Skip already-embedded base64 data URIs
            if src.startswith("data:"):
                return match.group(0)
            url = QUrl(src)
            # QTextDocument.ResourceType.ImageResource == 2 in PyQt6
            resource = doc.resource(2, url)
            image = None
            if isinstance(resource, QImage):
                image = resource
            elif hasattr(resource, 'value') and isinstance(resource.value(), QImage):
                image = resource.value()
            if image is not None and not image.isNull():
                buf = QBuffer()
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                image.save(buf, "PNG")
                buf.close()
                base64_data = buf.data().toBase64().data().decode('utf-8')
                return f'src="data:image/png;base64,{base64_data}"'
            return match.group(0)
        
        html = re.sub(r'src="([^"]*)"', embed_image, html)
        
        # Qt bakes the app's dark palette colors into table cell inline styles.
        # Strip background-color from <td> and <th> cells so they inherit the
        # page background when opened in a browser.
        def strip_cell_background(match):
            tag, attrs = match.group(1), match.group(2)
            attrs = re.sub(r'\s*background-color\s*:\s*[^;"]+(;)?', '', attrs, flags=re.IGNORECASE)
            return f'<{tag} {attrs.strip()}>'
        html = re.sub(r'<(td|th)\s+([^>]+)>', strip_cell_background, html, flags=re.IGNORECASE)
        
        return html
    
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