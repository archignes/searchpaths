# run: p -m pytest tests/test_utils.py

import os
import sys
from datetime import datetime

from load import get_history
from process import get_search_history
from utils import get_filtered_history


# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


mock_history = get_history("tests/mock_history_simple.json")
mock_search_history = get_search_history(mock_history)

def test_get_filtered_history():
    start_date = datetime.strptime("2024-04-22 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime("2024-04-25 23:59:59", "%Y-%m-%d %H:%M:%S")
    result = get_filtered_history(mock_search_history, start_date, end_date)
    assert len(result) == 1

def test_get_filtered_history_sunday():
    start_date = datetime.strptime("2024-04-21", "%Y-%m-%d")
    end_date = datetime.strptime("2024-04-27", "%Y-%m-%d")
    result = get_filtered_history(mock_search_history, start_date, end_date)
    assert len(result) == 2

def test_get_filtered_history_all():
    start_date = datetime.strptime("2024-04-01", "%Y-%m-%d")
    end_date = datetime.strptime("2024-04-27", "%Y-%m-%d")
    result = get_filtered_history(mock_search_history, start_date, end_date)
    assert len(result) == 3

