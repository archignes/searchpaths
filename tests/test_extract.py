# run: p -m pytest tests/test_extract.py

import os
import sys
from unittest.mock import patch
from datetime import datetime
import pytz

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extract import get_random_search_url, get_search_entry_by_datetime
from load import get_history
from process import get_search_history

mock_history = get_history("tests/mock_history_simple.json")
mock_search_history = get_search_history(mock_history)

def test_get_random_search_url():
    with patch("random.choice") as mock_choice:
        mock_choice.return_value = mock_search_history[0]
        entry = get_random_search_url(mock_search_history)
        assert entry["search_query"] == "python testing"


def test_get_search_entry_by_datetime():
    datetime_object = datetime.strptime("2024-04-20 03:00:00", "%Y-%m-%d %H:%M:%S")
    converted_object = datetime_object.replace(tzinfo=pytz.utc)
    converted_string = converted_object.strftime("%Y-%m-%d %H:%M:%S")
    entry = get_search_entry_by_datetime(mock_search_history, converted_string)
    assert entry["search_query"] == "python testing"
