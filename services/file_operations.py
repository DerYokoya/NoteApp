from pathlib import Path
from config.app_config import AppConfig

# ============================================================================
# File Operations Handler
# ============================================================================

class FileOperations:
    """Handles all file I/O operations with proper error handling"""
    
    @staticmethod
    def check_file_size(filepath: Path) -> bool:
        """Check if file size is within acceptable limits"""
        size_mb = filepath.stat().st_size / (1024 * 1024)
        return size_mb <= AppConfig.MAX_FILE_SIZE_MB
    
    @staticmethod
    def read_file(filepath: Path) -> tuple[str, bool]:
        """
        Read file content safely
        Returns: (content, is_html)
        Raises: IOError, UnicodeDecodeError
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if not FileOperations.check_file_size(filepath):
            raise IOError(
                f"File too large ({filepath.stat().st_size / (1024*1024):.1f} MB). "
                f"Maximum size is {AppConfig.MAX_FILE_SIZE_MB} MB."
            )
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            is_html = filepath.suffix.lower() == '.html'
            return content, is_html
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
            is_html = filepath.suffix.lower() == '.html'
            return content, is_html
    
    @staticmethod
    def write_file(filepath: Path, content: str, as_html: bool = True):
        """
        Write content to file safely
        Raises: IOError
        """
        # Create backup if file exists
        if filepath.exists():
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            try:
                backup_path.write_text(filepath.read_text(encoding='utf-8'), encoding='utf-8')
            except Exception:
                pass  # Backup is best-effort
        
        # Write new content
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write file: {e}")
    
    @staticmethod
    def delete_file(filepath: Path):
        """
        Delete file safely
        Raises: IOError
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            filepath.unlink()
        except Exception as e:
            raise IOError(f"Failed to delete file: {e}")