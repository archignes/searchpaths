# run: p -m pytest tests/test_searchpath.py

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extract import (
    get_history_by_week,
    get_random_search_url,
    get_search_engine_percentages,
    get_search_entry_by_datetime,
    is_guid_version_of_query
)

# Create a mock history dataset for testing
mock_history = [
    {
        "url": "https://www.google.com/search?q=python+testing",
        "title": "python testing - Google Search",
        "visit_count": 1,
        "last_visit_time": "2024-04-20 10:00:00",
        "search_query": "python testing",
        "search_engine": "google.com",
    },
    {
        "url": "https://www.google.com/search?q=pytest",
        "title": "pytest - Google Search",
        "visit_count": 1,
        "last_visit_time": "2024-04-21 11:00:00",
        "search_query": "pytest",
        "search_engine": "google.com",
    },
    {
        "url": "https://duckduckgo.com/?q=mock+data&t=h_&ia=web",
        "title": "mock data at DuckDuckGo",
        "visit_count": 1,
        "last_visit_time": "2024-04-23 12:00:00",
        "search_query": "mock data",
        "search_engine": "duckduckgo.com",
    },
]

def test_get_history_by_week_defaults():
    result = get_history_by_week(mock_history)
    assert result["week_num"] == 0
    
    # Get the current date and calculate the expected start and end dates
    current_date = datetime.now().date()
    expected_start_date = current_date - timedelta(days=(current_date.weekday() + 7) % 7)
    expected_end_date = expected_start_date + timedelta(days=6)
    
    assert result["start_date"] == expected_start_date
    assert result["end_date"] == expected_end_date
    assert result["start_date"].strftime("%A") == "Monday"
    assert len(result["history"]) == 1


def test_get_history_by_week_start_on_sunday():
    result = get_history_by_week(mock_history, start_on_monday=False)
    assert result["week_num"] == 0
    
    # Get the current date and calculate the expected start and end dates
    current_date = datetime.now().date()
    expected_start_date = current_date - timedelta(days=(current_date.weekday() + 1) % 7)
    expected_end_date = expected_start_date + timedelta(days=6)
    
    assert result["start_date"] == expected_start_date
    assert result["end_date"] == expected_end_date
    assert result["start_date"].strftime("%A") == "Sunday"
    assert len(result["history"]) == 2

def test_get_history_by_week():
    result = get_history_by_week(mock_history, 1)
    assert result["week_num"] == 1
    
    # Get the current date and calculate the expected start and end dates
    current_date = datetime.now().date()
    expected_start_date = current_date - timedelta(days=current_date.weekday() + 7)
    expected_end_date = expected_start_date + timedelta(days=6)
    
    assert result["start_date"] == expected_start_date
    assert result["end_date"] == expected_end_date
    assert result["start_date"].strftime("%A") == "Monday"
    assert len(result["history"]) == 2


def test_get_search_engine_percentages():
    result = get_search_engine_percentages(mock_history)
    assert result["total_searches"] == 1
    assert result["search_engines"] == [("duckduckgo.com", 1)]


def test_get_search_entry_by_datetime():
    entry = get_search_entry_by_datetime(mock_history, "2024-04-21 11:00:00")
    assert entry["search_query"] == "pytest"


def test_get_random_search_url():
    with patch("random.choice") as mock_choice:
        mock_choice.return_value = mock_history[0]
        entry = get_random_search_url(mock_history)
        assert entry["search_query"] == "python testing"


def test_is_guid_version_of_query():
    assert is_guid_version_of_query("https://www.perplexity.ai/search/?q=is+there+a+kid+focused+search+engine%3F",
                                    "https://www.perplexity.ai/search/is-there-a-zNl4gXV4Tjmq5_FCHOORHQ?s=u")

