from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TypedDict


class HistoryItem(TypedDict):
    url: str
    title: str
    visit_count: int
    last_visit_time: str
    last_visit_time_datetime: datetime


class SearchHistoryItem(TypedDict):
    url: str
    title: str
    visit_count: int
    last_visit_time: str
    last_visit_time_datetime: datetime

    search_query: Optional[str]
    search_engine: Optional[str]
    search_label: Optional[str]
    included_search_entry: bool
    default_visible: bool


class ScopedHistory(TypedDict):
    # This is the output from extract.get_history_by_week
    start_date: datetime
    end_date: datetime
    search_history: List[SearchHistoryItem]
    timespan_period_num: int
    total_timespan_periods_logged: int


class HistoryByWeekAnalyzed(TypedDict):
    # This is the output from analyze.get_search_engine_percentages
    start_date: str
    end_date: str
    total_searches: int
    search_history: List[Dict[str, Any]]
    search_engines: List[Tuple[str, int]]
