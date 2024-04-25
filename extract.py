"""
This module contains functions for extracting search history data:
- getting surrounding history
- getting random search url
- getting search entry by datetime
"""

import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from sp_types import HistoryItem, SearchHistoryItem


def get_surrounding_history(url, history, context_window=3):
    for i, entry in enumerate(history):
        if entry["url"] == url:
            return history[i - context_window : i + context_window]


def get_random_search_url(
    history: List[SearchHistoryItem],
) -> Optional[SearchHistoryItem]:
    search_history = [
        entry
        for entry in history
        if entry.get("search_query")
        and entry.get("search_label", None)
        not in [
            "redirect",
            "duplicate",
            "chat-based-search-complement",
            "not-url-based",
        ]
    ]
    return random.choice(search_history) if search_history else None


def get_search_entry_by_datetime(
    history: List[SearchHistoryItem], datetime_str: str
) -> Optional[SearchHistoryItem]:
    target_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    print(target_datetime)
    
    for entry in history:
        print(entry["last_visit_time"])
        entry_datetime = datetime.strptime(
            entry["last_visit_time"], "%Y-%m-%d %H:%M:%S"
        )
        if entry_datetime == target_datetime:
            return entry
    return None
