# This test file is for testing the TablePropertiesDialog.
# It uses pytest and the qtbot fixture to create a test environment for the dialog.
# The test checks if the dialog can be created successfully when a table is inserted into a QTextEdit widget.
from widgets.table_dialog import TablePropertiesDialog
from PyQt6.QtWidgets import QTextEdit
import pytest

def test_table_properties_dialog(qtbot):
    """Test table properties dialog"""
    text_edit = QTextEdit()
    cursor = text_edit.textCursor()
    table = cursor.insertTable(3, 3)
    
    dialog = TablePropertiesDialog(table, None)
    qtbot.addWidget(dialog)
    
    # Test dialog exists
    assert dialog is not None