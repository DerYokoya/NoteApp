from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from config.app_config import AppConfig

# ============================================================================
# File Operations Handler
# handles disk I/O
# ============================================================================

class FileLoadWorker(QObject):
    """
    Runs FileOperations.read_file() on a background thread so large files
    don't block the UI. Create one per load, move it to a QThread, and
    start the thread - do not call run() directly.
    """
    finished = pyqtSignal(str, bool)   # content, is_html
    failed = pyqtSignal(str)           # error message

    def __init__(self, filepath: Path):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            content, is_html = FileOperations.read_file(self.filepath)
            self.finished.emit(content, is_html)
        except Exception as e:
            self.failed.emit(str(e))


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
        Write content to file safely.
        A .bak is created before writing so the original is recoverable if the
        write fails.  The backup is removed automatically on success so old
        backups never accumulate silently.
        Raises: IOError
        """
        backup_path = None

        # Create backup if file exists (best-effort safety net during write)
        if filepath.exists():
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            try:
                backup_path.write_text(filepath.read_text(encoding='utf-8'), encoding='utf-8')
            except Exception:
                backup_path = None  # Backup failed; don't try to delete it later

        # Write new content
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write file: {e}")

        # Write succeeded — remove the now-redundant backup
        if backup_path is not None:
            try:
                backup_path.unlink(missing_ok=True)
            except Exception:
                pass  # Non-critical; leave the stale backup rather than masking the save

    @staticmethod
    def cleanup_backups(target: Path) -> int:
        """
        Delete .bak files associated with *target*.

        If *target* is a file, only its own .bak sibling is removed.
        If *target* is a directory, all *.bak files anywhere under it are removed.

        Returns the number of backup files deleted.
        """
        deleted = 0
        if target.is_dir():
            for bak in target.rglob('*.bak'):
                try:
                    bak.unlink()
                    deleted += 1
                except Exception:
                    pass
        else:
            bak = target.with_suffix(target.suffix + '.bak')
            if bak.exists():
                try:
                    bak.unlink()
                    deleted += 1
                except Exception:
                    pass
        return deleted

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