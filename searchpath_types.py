from typing import Any, Dict, List, Optional, Tuple, TypedDict


class HistoryItem(TypedDict):
    url: str
    title: str
    visit_count: int
    last_visit_time: str
    search_query: Optional[str]
    search_engine: Optional[str]


class HistoryByWeek(TypedDict):
    # This is the output from extract.get_history_by_week
    week_num: int
    history: List[HistoryItem]
    start_date: str
    end_date: str
    total_weeks_logged: int


class HistoryByWeekAnalyzed(TypedDict):
    # This is the output from analyze.get_search_engine_percentages
    start_date: str
    end_date: str
    total_searches: int
    search_query_history: List[Dict[str, Any]]
    search_engines: List[Tuple[str, int]]
