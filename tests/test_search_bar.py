# This test file is for testing the SearchBar widget.
# It uses pytest and the qtbot fixture to create a test environment for the widget.
# The tests check the initialization, toggling of replace mode, counter updates,
# and signal emissions of the SearchBar.
from widgets.search_bar import SearchBar
import pytest

def test_search_bar_initialization(qtbot):
    """Test search bar initialization"""
    search_bar = SearchBar()
    qtbot.addWidget(search_bar)
    
    assert search_bar.get_search_text() == ""
    assert search_bar.get_replace_text() == ""
    assert search_bar.is_case_sensitive() is False
    assert search_bar.replace_widget.isVisible() is False

def test_search_bar_toggle_replace(qtbot):
    """Test replace mode toggling"""
    search_bar = SearchBar()
    qtbot.addWidget(search_bar)
    
    assert search_bar.show_replace is False
    assert search_bar.replace_widget.isVisible() is False
    
    search_bar.toggle_replace_mode()
    assert search_bar.show_replace is True
    assert search_bar.replace_widget.isVisible() is True
    
    search_bar.toggle_replace_mode()
    assert search_bar.show_replace is False
    assert search_bar.replace_widget.isVisible() is False

def test_search_bar_counter_update(qtbot):
    """Test counter display update"""
    search_bar = SearchBar()
    qtbot.addWidget(search_bar)
    
    search_bar.update_counter(3, 10)
    assert search_bar.counter_label.text() == "3/10"
    
    search_bar.update_counter(0, 0)
    assert search_bar.counter_label.text() == "0/0"

def test_search_bar_signals(qtbot):
    """Test search bar signals"""
    search_bar = SearchBar()
    qtbot.addWidget(search_bar)
    
    # Test find next signal
    with qtbot.waitSignal(search_bar.find_next_requested, timeout=1000):
        search_bar.next_btn.click()
    
    # Test find prev signal
    with qtbot.waitSignal(search_bar.find_prev_requested, timeout=1000):
        search_bar.prev_btn.click()
    
    # Test close signal
    with qtbot.waitSignal(search_bar.close_requested, timeout=1000):
        search_bar.close_btn.click()
