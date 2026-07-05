# ============================================================================
# Document Model
# document logic, content management, and state tracking for each open document
# ============================================================================

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QMouseEvent, QImage, QTextDocument, QTextFormat
from PyQt6.QtCore import QMimeData
from PyQt6.QtCore import Qt, QBuffer, QIODevice, QUrl
import webbrowser
import re


class LinkAwareTextEdit(QTextEdit):
    """Custom QTextEdit that opens links on Ctrl+Click and supports clipboard image paste"""
    
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
    
    def _get_image_at_cursor(self) -> Optional[QImage]:
        """Return the image resource under the current cursor, if any."""
        cursor = self.textCursor()
        char_fmt = cursor.charFormat()
        if not char_fmt.isImageFormat():
            return None

        image_name = char_fmt.stringProperty(QTextFormat.Property.ImageName)
        if not image_name:
            return None

        doc = self.document()
        resource = doc.resource(QTextDocument.ResourceType.ImageResource, QUrl(image_name))
        if isinstance(resource, QImage):
            return resource
        if hasattr(resource, 'value') and isinstance(resource.value(), QImage):
            return resource.value()
        return None

    def createMimeDataFromSelection(self) -> Optional[QMimeData]:
        """Expose copied images through the clipboard mime data."""
        mime_data = super().createMimeDataFromSelection()
        if mime_data is None:
            mime_data = QMimeData()

        image = self._get_image_at_cursor()
        if image is not None and not image.isNull():
            mime_data.setImageData(image)

        return mime_data

    def insertFromMimeData(self, source: QMimeData):
        """Override to support pasting images from clipboard (Ctrl+V)"""
        # Check if the mime data contains an image
        if source.hasImage():
            image = QImage(source.imageData())
            if not image.isNull():
                # Generate a unique image name
                import uuid
                image_name = f"clipboard_{uuid.uuid4().hex[:8]}.png"
                
                # Add image to document resources
                doc = self.document()
                doc.addResource(QTextDocument.ResourceType.ImageResource, 
                               QUrl(image_name), image)
                
                # Insert the image into the document
                cursor = self.textCursor()
                cursor.insertImage(image_name)
                self.setTextCursor(cursor)
                return
        
        # Fall back to default paste behavior for non-image content
        super().insertFromMimeData(source)


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
        
        # Find all src="..." values in the HTML
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

    def set_content(self, content: str, is_html: bool = False):
        """Set document content, preserving undo stack and restoring images"""
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        
        if is_html:
            # Extract base64 images from HTML before setting
            import base64
            from PyQt6.QtCore import QByteArray
            from PyQt6.QtGui import QImageReader
            from PyQt6.QtCore import QBuffer, QIODevice
            
            images = {}
            
            def extract_and_replace(match):
                src = match.group(1)
                if src.startswith('data:image/'):
                    # Parse the data URI
                    header, data = src.split(',', 1)
                    # Extract image format (png, jpeg, etc.)
                    image_format = header.split('/')[1].split(';')[0]
                    
                    # Decode base64 data
                    try:
                        image_data = base64.b64decode(data)
                        
                        # Create QImage from bytes
                        buffer = QBuffer()
                        buffer.setData(QByteArray(image_data))
                        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
                        
                        reader = QImageReader(buffer)
                        reader.setAutoDetectImageFormat(True)
                        image = reader.read()
                        buffer.close()
                        
                        if not image.isNull():
                            # Generate unique name
                            import uuid
                            img_name = f"restored_{uuid.uuid4().hex[:8]}.{image_format}"
                            images[img_name] = image
                            return f'src="{img_name}"'
                    except Exception as e:
                        print(f"Failed to decode image: {e}")
                
                return match.group(0)
            
            # Replace all base64 data URIs with placeholder names
            processed_html = re.sub(r'src="([^"]*)"', extract_and_replace, content)
            
            # Set the processed HTML
            self.text_edit.setHtml(processed_html)
            
            # Add extracted images as document resources
            doc = self.text_edit.document()
            for img_name, image in images.items():
                doc.addResource(QTextDocument.ResourceType.ImageResource, 
                            QUrl(img_name), image)
            
            # Force document to refresh
            doc.adjustSize()
        else:
            self.text_edit.setPlainText(content)
            
        cursor.endEditBlock()
        self.text_edit.document().setModified(False)
        self._last_saved_content = content
        
    def get_content_plain(self) -> str:
        """Get document content as plain text"""
        return self.text_edit.toPlainText()
    
    def get_image_info(self):
        """Debug method to get information about images in the document"""
        doc = self.text_edit.document()
        resources = []
        # QTextDocument.ResourceType.ImageResource == 2
        # Since we can't easily enumerate resources in Qt, this is just informational
        return "Images are stored as resources within the QTextDocument"