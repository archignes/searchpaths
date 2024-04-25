"""
This module contains functions for processing search history data:
- adding search metadata to history
- cleaning up search history
- getting search engine percentages
"""

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import parse_qs, unquote, urlparse

from config import (
    CHAT_BASED_SEARCH_COMPLEMENTS,
    INCLUDED_SEARCH_SYSTEMS,
    LANDING_PAGE_ONLY_SEARCH_SYSTEMS,
    SITE_SEARCH_DOMAINS,
    SKIP_DOMAINS,
)
from sp_types import HistoryItem, ScopedHistory, SearchHistoryItem
from utils import (
    convert_chrome_time,
    get_filtered_history,
    get_time_diff,
    get_total_timespan_logged,
)


def perplexity_cleanup(url, temp_history: List[HistoryItem]):
    """Returns false for perplexity cleanup pairs, true if the addition is countable."""
    if len(temp_history) <= 1:
        return True
    if url.replace("www.", "") == temp_history[-1]["url"].replace("www.", ""):
        return False

    if not any("perplexity.ai" in entry["url"] for entry in temp_history[-3:]):
        if url not in {entry["url"] for entry in temp_history}:
            return True

    # Parse the URLs to compare their base parts and query parameters
    last_url_parsed = urlparse(temp_history[-1]["url"])
    current_url_parsed = urlparse(url)

    # Remove query parameters to just compare the base URL
    last_url_base = last_url_parsed._replace(query="").geturl()
    current_url_base = current_url_parsed._replace(query="").geturl()

    # Check if the base URLs are the same after removing the trailing slash if any
    if last_url_base.rstrip("/") == current_url_base.rstrip("/"):
        # Compare the query parameters
        last_url_query = parse_qs(last_url_parsed.query)
        current_url_query = parse_qs(current_url_parsed.query)

        # Remove 'copilot' parameter from the current URL's query if it exists
        current_url_query.pop("copilot", None)

        # If the query parameters are the same after removing 'copilot', return False
        last_url_q = last_url_query.get("q", [""])[0].replace("+", "%20")
        current_url_q = current_url_query.get("q", [""])[0].replace("+", "%20")
        if last_url_q == current_url_q:
            return False
        else:
            return False

    if is_guid_version_of_query(url, temp_history[-1]["url"]):
        return False
    return False


SITE_SPECIFIC_SEARCH_CLEANUP = {"https://www.perplexity.ai/search/": perplexity_cleanup}


def is_landing_page(url):
    for item in INCLUDED_SEARCH_SYSTEMS:
        if url == item:
            return True
    return False


def is_included_search_system(url):
    """This captures urls that may not have query params."""
    for item in INCLUDED_SEARCH_SYSTEMS:
        if url.startswith(item):
            return True
    return False


def cleanup(url, temp_history):
    for key, cleanup in SITE_SPECIFIC_SEARCH_CLEANUP.items():
        if url.startswith(key):
            return cleanup(url, temp_history)
    else:
        return True


def update_temp_history(temp_history, url, title, visit_count, last_visit_time):
    visit_time = convert_chrome_time(last_visit_time)
    if temp_history and url.split("?")[0] == temp_history[-1]["url"].split("?")[0]:
        time_diff = get_time_diff(visit_time, temp_history[-1]["last_visit_time_raw"])
        if time_diff.total_seconds() <= 1:
            return temp_history

    temp_history.append(
        {
            "url": url,
            "title": title,
            "visit_count": visit_count,
            "last_visit_time": visit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_visit_time_raw": last_visit_time,
        }
    )
    return temp_history


def is_likely_countable_search_url(temp_history, url, visit_count):
    """
    Determines if a URL should be kept based on various criteria.

    :param url: The URL to check.
    :param visit_count: The visit count of the URL.
    :return: True if the URL should be kept, False otherwise.
    """
    # Define a list of common search engine query patterns
    search_patterns = [
        "search?q=",  # Common for many search engines like Google
        "search/web?q=",  # Another common pattern
        "query=",  # Used by some search engines
        "search?p=",  # Yahoo
        "q=",  # Short and common, but be careful as it might match non-search URLs
    ]

    site_specific_search_exclusion_rule = {
        # this is how Google safeloads URLs from Gmail, perhaps?
        "https://www.google.com/": "https://www.google.com/url?q=",
    }

    site_specific_search_inclusion_rule = {
        "https://www.tiktok.com": "https://www.tiktok.com/search?q=",
        "https://www.perplexity.ai": "https://www.perplexity.ai/search",
    }

    if is_included_search_system(url):
        return True
    if visit_count > 0 and any(pattern in url for pattern in search_patterns):
        for site, pattern in site_specific_search_inclusion_rule.items():
            if url.startswith(site) and not url.startswith(pattern):
                return False
        for site, pattern in site_specific_search_exclusion_rule.items():
            if url.startswith(site) and url.startswith(pattern):
                return False
        for skip_domain in SKIP_DOMAINS:
            if url.startswith(skip_domain):
                return False
            if skip_domain.startswith("*"):
                if skip_domain.replace("*", "") in url:
                    return False
        for key, cleanup in SITE_SPECIFIC_SEARCH_CLEANUP.items():
            if url.startswith(key):
                return cleanup(url, temp_history)
        return True
    return False


def add_search_metadata_to_history(
    history: List[HistoryItem], full_history: bool = False
) -> List[SearchHistoryItem]:
    temp_history: List[HistoryItem] = []
    search_history = []
    for entry in history:
        updated_entry: SearchHistoryItem = {
            **entry,
            "included_search_entry": False,
            "search_query": None,
            "search_engine": None,
            "search_label": None,
            "default_visible": True,
        }
        if not is_likely_countable_search_url(temp_history, entry["url"], entry["visit_count"]):
            search_history.append(updated_entry)
            continue
        url = entry["url"]
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        if "q" in query:
            updated_entry["search_query"] = unquote(query["q"][0])
        elif "query" in query:
            updated_entry["search_query"] = unquote(query["query"][0])
        elif "p" in query:
            updated_entry["search_query"] = unquote(query["p"][0])
        elif is_included_search_system(url):
            for site in CHAT_BASED_SEARCH_COMPLEMENTS:
                if url.startswith(site):
                    updated_entry["search_label"] = "chat-based-search-complement"
                    updated_entry["search_query"] = "..."
                    break
            else:
                updated_entry["search_label"] = "not-url-based"
                updated_entry["search_query"] = "..."
        else:
            updated_entry["search_query"] = None

        if any(url.startswith(site) for site in SITE_SEARCH_DOMAINS):
            updated_entry["search_label"] = "site_search"
        if not cleanup(url, temp_history):
            updated_entry["search_label"] = "redirect"

        if "search_query" in updated_entry and updated_entry["search_query"]:
            updated_entry["search_engine"] = parsed_url.netloc.replace("www.", "")
        if "search_query" in updated_entry:
            temp_history = update_temp_history(
                temp_history,
                url,
                updated_entry["title"],
                updated_entry["visit_count"],
                updated_entry["last_visit_time"],
            )
        if is_landing_page(url):
            updated_entry["search_label"] = "landing_page"
        
        if updated_entry["search_label"] in ["redirect"]:
            updated_entry["included_search_entry"] = False
        elif updated_entry["search_label"] == "landing_page":
            if url in LANDING_PAGE_ONLY_SEARCH_SYSTEMS:
                updated_entry["included_search_entry"] = True
                updated_entry["search_label"] = "landing_page_only_search_system"
            else:
                updated_entry["included_search_entry"] = False
        else:
            updated_entry["included_search_entry"] = True
        search_history.append(updated_entry)
    return search_history


def is_guid_version_of_query(url, url_to_check_against):
    url_to_check_against_reduced = url_to_check_against.replace(
        "https://www.perplexity.ai/search/", ""
    )
    url_reduced = url.replace("https://www.perplexity.ai/search/?q=", "")
    terms_url_string_to_check_against = url_to_check_against_reduced.split("-")
    url_string_to_check_against = "-".join(terms_url_string_to_check_against[:-1])
    hyphenated_url_query = url_reduced.replace("+", "-").replace("%20", "-")
    return hyphenated_url_query.startswith(url_string_to_check_against)


def get_history_by_month(
    search_history: List[SearchHistoryItem], month_num: int = 0
) -> ScopedHistory:
    current_date = datetime.now()

    # Calculate the target year and month considering month_num
    target_year = current_date.year - (month_num // 12)
    target_month = current_date.month - (month_num % 12)

    # Adjust for when target_month becomes 0 or negative
    if target_month <= 0:
        target_month += 12
        target_year -= 1

    start_date = datetime(target_year, target_month, 1)
    end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(
        day=1
    ) - timedelta(days=1)

    month_search_data: ScopedHistory = {
        "start_date": start_date,
        "end_date": end_date,
        "search_history": get_filtered_history(search_history, start_date, end_date),
        "timespan_period_num": month_num,
        "total_timespan_periods_logged": get_total_timespan_logged(
            search_history, "month"
        ),
    }
    return month_search_data


def get_history_by_week(
    search_history: List[SearchHistoryItem],
    week_num: int = 0,
    start_on_monday: bool = True,
) -> ScopedHistory:
    current_date = datetime.now()

    # Adjust the start day of the week based on user preference
    if start_on_monday:
        start_day_adjustment = (current_date.weekday() + 7) % 7

    else:  # If start_on_monday is False, the week starts on Sunday
        start_day_adjustment = (current_date.weekday() + 1) % 7

    week_start_day = current_date - timedelta(days=start_day_adjustment)

    start_date = week_start_day - timedelta(days=7 * week_num)
    end_date = start_date + timedelta(days=6)

    week_search_data: ScopedHistory = {
        "timespan_period_num": week_num,
        "start_date": start_date,
        "end_date": end_date,
        "search_history": get_filtered_history(search_history, start_date, end_date),
        "total_timespan_periods_logged": get_total_timespan_logged(
            search_history, "week", start_on_monday
        ),
    }
    return week_search_data


def get_search_engine_percentages(
    search_history: List[SearchHistoryItem],
    week_num: int = 0,
    start_on_monday: bool = True,
    full_history: bool = False,
    by_month: bool = False,
    month_num: int = 0,
    hide_complements: bool = True,
) -> Dict[str, Any]:
    if full_history:
        scoped_history: ScopedHistory = {
            "search_history": search_history,
            "start_date": search_history[0]["last_visit_time_datetime"],
            "end_date": search_history[-1]["last_visit_time_datetime"],
            "timespan_period_num": 0,
            "total_timespan_periods_logged": get_total_timespan_logged(
                search_history, "day"
            ),
        }
    elif by_month:
        scoped_history = get_history_by_month(search_history, month_num)
    else:
        scoped_history = get_history_by_week(search_history, week_num, start_on_monday)
    search_engines: Dict[str, int] = Counter()
    for entry in scoped_history["search_history"]:
        # These are entries that will be visible in the search history log but not counted
        # toward the search engine percentages
        if entry["search_label"] == "site_search":
            entry["default_visible"] = False
            continue
        if hide_complements and entry["search_label"] == "chat-based-search-complement":
            entry["default_visible"] = False
            continue
        if entry["included_search_entry"] and entry["search_engine"]:
            search_engines[entry["search_engine"]] += 1
    
    total_searches = sum(search_engines.values())

    sorted_search_engines = sorted(
        search_engines.items(),
        key=lambda x: (x[1] / total_searches) * 100,
        reverse=True,
    )

    return {
        "label": "month" if by_month else "day" if full_history else "week",
        "start_date": scoped_history["start_date"],
        "end_date": scoped_history["end_date"],
        "total_searches": total_searches,
        "search_history": scoped_history["search_history"],
        "search_engines": sorted_search_engines,
        "total_timespan_periods_logged": scoped_history[
            "total_timespan_periods_logged"
        ],
    }


def get_search_history(history: List[HistoryItem]) -> List[SearchHistoryItem]:
    search_history = add_search_metadata_to_history(history)
    return search_history
