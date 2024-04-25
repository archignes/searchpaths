# run: p -m pytest tests/test_process.py

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from load import get_history
from process import (
    get_search_history,
    get_history_by_week,
    get_search_engine_percentages,
    is_guid_version_of_query,
)

mock_history = get_history("tests/mock_history_simple.json")
mock_search_history = get_search_history(mock_history)


def test_get_history_by_week_defaults():
    result = get_history_by_week(mock_search_history)
    assert result["timespan_period_num"] == 0

    # Get the current date and calculate the expected start and end dates
    current_date = datetime.now().date()
    expected_start_date = current_date - timedelta(
        days=(current_date.weekday() + 7) % 7
    )
    expected_end_date = expected_start_date + timedelta(days=6)

    assert result["start_date"].date() == expected_start_date
    assert result["end_date"].date() == expected_end_date
    assert result["start_date"].strftime("%A") == "Monday"
    assert len(result["search_history"]) == 1


def test_get_history_by_week_start_on_sunday():
    result = get_history_by_week(mock_search_history, start_on_monday=False)
    assert result["timespan_period_num"] == 0

    # Get the current date and calculate the expected start and end dates
    current_date = datetime.now().date()
    expected_start_date = current_date - timedelta(
        days=(current_date.weekday() + 1) % 7
    )
    expected_end_date = expected_start_date + timedelta(days=6)
    print(f"Expected start date: {expected_start_date}, Actual start date: {result['start_date'].date()}")
    print(f"Expected end date: {expected_end_date}, Actual end date: {result['end_date'].date()}")
    print(f"Expected start day of the week: Sunday, Actual: {result['start_date'].strftime('%A')}")
    print(f"Expected number of search history entries: 2, Actual: {len(result['search_history'])}")
    import pprint
    pprint.pprint(mock_search_history)
    for entry in mock_search_history:
        print(f"Date of entry: {entry['last_visit_time']}")
    print(f"Full datetime of expected start date: {expected_start_date.isoformat()}")
    assert result["start_date"].date() == expected_start_date
    assert result["end_date"].date() == expected_end_date
    assert result["start_date"].strftime("%A") == "Sunday"
    assert len(result["search_history"]) == 2


def test_get_history_by_week():
    result = get_history_by_week(mock_search_history, 1)
    assert result["timespan_period_num"] == 1

    # Get the current date and calculate the expected start and end dates
    current_date = datetime.now().date()
    expected_start_date = current_date - timedelta(days=current_date.weekday() + 7)
    expected_end_date = expected_start_date + timedelta(days=6)

    assert result["start_date"].date() == expected_start_date
    assert result["end_date"].date() == expected_end_date
    assert result["start_date"].strftime("%A") == "Monday"
    print(result["search_history"])
    assert len(result["search_history"]) == 2


def test_get_search_engine_percentages():
    result = get_search_engine_percentages(mock_search_history)
    print(result)
    assert result["total_searches"] == 1
    assert result["search_engines"] == [("duckduckgo.com", 1)]


def test_is_guid_version_of_query():
    assert is_guid_version_of_query(
        "https://www.perplexity.ai/search/?q=is+there+a+kid+focused+search+engine%3F",
        "https://www.perplexity.ai/search/is-there-a-zNl4gXV4Tjmq5_FCHOORHQ?s=u",
    )
