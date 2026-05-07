# This test file is for testing the FileOperations class.
# It uses pytest to test the functionality of reading, writing, and deleting files,
# as well as handling edge cases like non-existent files and invalid paths.
from pathlib import Path
import pytest
from services.file_operations import FileOperations

def test_read_write_text_file(tmp_path):
    """Test reading and writing plain text files"""
    file = tmp_path / "test.txt"
    content = "Hello, World!"
    
    FileOperations.write_file(file, content, as_html=False)
    assert file.exists()
    assert file.read_text(encoding='utf-8') == content
    
    read_content, is_html = FileOperations.read_file(file)
    assert read_content == content
    assert is_html is False

def test_read_write_html_file(tmp_path):
    """Test reading and writing HTML files"""
    file = tmp_path / "test.html"
    content = "<html><body><h1>Title</h1></body></html>"
    
    FileOperations.write_file(file, content, as_html=True)
    assert file.exists()
    
    read_content, is_html = FileOperations.read_file(file)
    assert read_content == content
    assert is_html is True

def test_read_nonexistent_file():
    """Test reading a file that doesn't exist"""
    with pytest.raises(Exception):
        FileOperations.read_file(Path("nonexistent.txt"))

def test_write_to_invalid_path():
    """Test writing to an invalid path"""
    with pytest.raises(Exception):
        FileOperations.write_file(Path("/invalid/path/file.txt"), "content", as_html=False)

def test_delete_file(tmp_path):
    """Test file deletion"""
    file = tmp_path / "delete_me.txt"
    file.write_text("content")
    assert file.exists()
    
    FileOperations.delete_file(file)
    assert not file.exists()

def test_delete_nonexistent_file(tmp_path):
    """Test deleting a file that doesn't exist"""
    file = tmp_path / "nonexistent.txt"
    with pytest.raises(Exception):
        FileOperations.delete_file(file)