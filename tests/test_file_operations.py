from pathlib import Path
import pytest
from services.file_operations import FileOperations

def test_read_write_file(tmp_path):
    file = tmp_path / "test.txt"
    FileOperations.write_file(file, "hello", as_html=False)

    content, is_html = FileOperations.read_file(file)

    assert content == "hello"
    assert is_html is False