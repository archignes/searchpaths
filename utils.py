"""
This module contains utility functions.
"""

from datetime import datetime, timedelta
from typing import List

import pytz

from sp_types import SearchHistoryItem


def convert_chrome_time(chrome_time: str) -> datetime:
    try:
        chrome_time_int = int(chrome_time)
    except ValueError:
        return (
            datetime.strptime(chrome_time, "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=pytz.utc)
            .astimezone(tz=None)
        )
    else:
        utc_time = datetime(1601, 1, 1) + timedelta(microseconds=chrome_time_int)
        return utc_time.replace(tzinfo=pytz.utc).astimezone(tz=None)


def get_time_diff(
    current_item_visit_time: datetime, last_item_visit_time: str
) -> timedelta:
    if not isinstance(current_item_visit_time, datetime):
        raise TypeError("current_item_visit_time must be a datetime object")

    return current_item_visit_time - convert_chrome_time(last_item_visit_time)


def get_total_timespan_logged(
    search_history: List[SearchHistoryItem],
    timespan: str = "week",
    start_on_monday: bool = True,
):
    if not search_history:
        return 0

    # Convert all last_visit_time to datetime objects
    for entry in search_history:
        entry["last_visit_time_datetime"] = convert_chrome_time(
            entry["last_visit_time"]
        )

    # Sort history by last_visit_time
    search_history.sort(key=lambda x: x["last_visit_time_datetime"])

    # Get the most recent and earliest dates, converting them to datetime
    most_recent_date = search_history[-1]["last_visit_time_datetime"]
    first_date = search_history[0]["last_visit_time_datetime"]

    if timespan == "week":
        # Determine the weekday of the most recent date
        most_recent_weekday = most_recent_date.weekday()

        # Adjust the start day of the week based on user preference
        if start_on_monday:
            start_day_adjustment = (most_recent_weekday + 7) % 7
        else:  # If start_on_monday is False, the week starts on Sunday
            start_day_adjustment = (most_recent_weekday + 1) % 7

        # Calculate the start of the current week
        current_week_start = most_recent_date - timedelta(days=start_day_adjustment)

        # Calculate the difference in weeks
        weeks_logged = (current_week_start - first_date).days // 7

        # Include the current week
        weeks_logged += 1

        return weeks_logged

    elif timespan == "month":
        # Calculate the difference in months
        months_logged = (most_recent_date.year - first_date.year) * 12 + (
            most_recent_date.month - first_date.month
        )

        # Include the current month
        months_logged += 1

        return months_logged

    elif timespan == "day":
        days_logged = (most_recent_date - first_date).days
        return days_logged

    else:
        raise ValueError("Unsupported timespan. Choose 'week', 'month', or 'day'.")


def get_filtered_history(
    search_history: List[SearchHistoryItem], start_date: datetime, end_date: datetime
) -> List[SearchHistoryItem]:
    # Normalize start_date to the start of the day in local time
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Normalize end_date to the end of the day in local time
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return [
        entry
        for entry in search_history
        if start_date.replace(tzinfo=pytz.utc)
        <= entry["last_visit_time_datetime"].replace(tzinfo=pytz.utc)
        <= end_date.replace(tzinfo=pytz.utc)
    ]
