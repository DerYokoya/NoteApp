# ============================================================================
# Settings Manager
# ============================================================================

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from pathlib import Path
from typing import List

from config.app_config import AppConfig

class SettingsManager:
    """Manages application settings persistence"""
    
    def __init__(self):
        self.settings = QSettings("RichTextNotepad", "MainApp")
    
    def save_window_geometry(self, geometry: QByteArray, state: QByteArray):
        """Save window geometry and state"""
        self.settings.setValue("window/geometry", geometry)
        self.settings.setValue("window/state", state)
    
    def restore_window_geometry(self, window: QMainWindow) -> bool:
        """Restore window geometry and state"""
        geometry = self.settings.value("window/geometry")
        state = self.settings.value("window/state")
        
        if geometry:
            window.restoreGeometry(geometry)
        if state:
            window.restoreState(state)
        
        return bool(geometry and state)
    
    def save_recent_files(self, files: List[str]):
        """Save list of recent files"""
        # Keep only existing files
        existing_files = [f for f in files if Path(f).exists()]
        self.settings.setValue("recent_files", existing_files[:AppConfig.MAX_RECENT_FILES])
    
    def get_recent_files(self) -> List[str]:
        """Get list of recent files"""
        files = self.settings.value("recent_files", [])
        if isinstance(files, str):
            files = [files] if files else []
        # Filter to only existing files
        return [f for f in files if Path(f).exists()]
    
    def add_recent_file(self, filepath: str):
        """Add a file to recent files list"""
        recent = self.get_recent_files()
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        self.save_recent_files(recent[:AppConfig.MAX_RECENT_FILES])
    
    def save_open_tabs(self, tabs: List[str], active_index: int):
        """Save list of currently open tabs"""
        # Keep only existing files (filter out empty strings for untitled tabs)
        existing_tabs = [f for f in tabs if f and Path(f).exists()]
        self.settings.setValue("open_tabs", existing_tabs)
        self.settings.setValue("active_tab_index", active_index)
    
    def get_open_tabs(self) -> tuple[List[str], int]:
        """Get list of previously open tabs and active index"""
        tabs = self.settings.value("open_tabs", [])
        if isinstance(tabs, str):
            tabs = [tabs] if tabs else []
        # Filter to only existing files
        existing_tabs = [f for f in tabs if Path(f).exists()]
        active_index = self.settings.value("active_tab_index", 0, type=int)
        return existing_tabs, active_index
    
    def clear_open_tabs(self):
        """Clear the saved open tabs"""
        self.settings.remove("open_tabs")
        self.settings.remove("active_tab_index")