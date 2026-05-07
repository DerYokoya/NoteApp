# This test file is for testing the TablePropertiesDialog.
# It uses pytest and the qtbot fixture to create a test environment for the dialog.
# The test checks if the dialog can be created successfully when a table is inserted into a QTextEdit widget.
from widgets.table_dialog import TablePropertiesDialog
from PyQt6.QtWidgets import QTextEdit, QApplication
import pytest

def test_table_properties_dialog(qtbot):
    """Test table properties dialog"""
    text_edit = QTextEdit()
    cursor = text_edit.textCursor()
    table = cursor.insertTable(3, 3)
    
    dialog = TablePropertiesDialog(table, None)
    # Don't use qtbot.addWidget for dialogs that might be modal
    # Just verify the dialog was created
    assert dialog is not None
    assert dialog.table == table