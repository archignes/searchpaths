import json
import glob
import os
import random
import shutil
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

import pytz

from config import SITE_SEARCH_DOMAINS, SKIP_DOMAINS, LOGGABLE_SEARCH_SYSTEMS, CHAT_BASED_SEARCH_COMPLEMENTS
from searchpath_types import HistoryByWeek, HistoryByWeekAnalyzed, HistoryItem




def convert_chrome_time(chrome_time: str) -> datetime:
    try:
        # Attempt to convert chrome_time directly to an integer
        chrome_time_int = int(chrome_time)
    except ValueError:
        # If conversion fails, assume chrome_time is already in datetime format
        return datetime.strptime(chrome_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(tz=None)
    else:
        # Convert Chrome's timestamp to datetime in UTC if conversion succeeds
        utc_time = datetime(1601, 1, 1) + timedelta(microseconds=chrome_time_int)
        # Convert UTC datetime to local datetime
        return utc_time.replace(tzinfo=pytz.utc).astimezone(tz=None)


def perplexity_cleanup(url, temp_history):
    """Returns false for perplexity cleanup pairs, true if the addition is countable."""
    if len(temp_history) <= 1:
        return True
    if url.replace("www.", "") == temp_history[-1]['url'].replace("www.", ""):
        return False
   
    if not any("perplexity.ai" in entry['url'] for entry in temp_history[-3:]):
        if url not in {entry['url'] for entry in temp_history}:
            return True

    # Parse the URLs to compare their base parts and query parameters
    last_url_parsed = urlparse(temp_history[-1]['url'])
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
        current_url_query.pop('copilot', None)

        # If the query parameters are the same after removing 'copilot', return False
        last_url_q = last_url_query.get('q', [''])[0].replace("+", "%20")
        current_url_q = current_url_query.get('q', [''])[0].replace("+", "%20")
        if last_url_q == current_url_q:
            return False
        else:
            return False

    if is_guid_version_of_query(url, temp_history[-1]['url']):
        return False
    return False

SITE_SPECIFIC_SEARCH_CLEANUP = {
        "https://www.perplexity.ai/search/": perplexity_cleanup
    }

def is_loggable_search_system(url):
    for each in LOGGABLE_SEARCH_SYSTEMS:
        if url.startswith(each):
            return True
    return False

def cleanup(url, temp_history):
    for key, cleanup in SITE_SPECIFIC_SEARCH_CLEANUP.items():
        if url.startswith(key):
            return cleanup(url, temp_history)
    else:
        return True
    
def get_time_diff(current_item_visit_time: datetime, last_item_visit_time: str) -> timedelta:
    if not isinstance(current_item_visit_time, datetime):
        raise TypeError("current_item_visit_time must be a datetime object")
        
    return current_item_visit_time - convert_chrome_time(last_item_visit_time)

def update_temp_history(temp_history, url, title, visit_count, last_visit_time):
    # Convert last_visit_time to a datetime object for comparison
    visit_time = convert_chrome_time(last_visit_time)
    # Check if the current URL matches the URL of the last entry in temp_history
    if (
        temp_history
        and url.split("?")[0] == temp_history[-1]["url"].split("?")[0]
    ):
        # Calculate the time difference between the current and last entry
        time_diff = get_time_diff(visit_time, temp_history[-1]["last_visit_time_raw"])
        # If the time difference is less than or equal to 1 second, skip adding this entry
        if time_diff.total_seconds() <= 1:
            return temp_history
    # Check if the last entry in temp_history is a redirect and remove it
    if url.startswith("https://www.perplexity.ai/search/"):
        if len(temp_history) > 1 and temp_history[-1]["url"].split("search")[0] == url.split("search")[0]:
            time_diff = get_time_diff(visit_time, temp_history[-1]["last_visit_time_raw"])
            if time_diff.total_seconds() <= 1:
                temp_history[-1]["search_query"] = "**redirect**"
    # Add the entry to temp_history with raw last_visit_time for comparison
    temp_history.append(
        {
            "url": url,
            "title": title,
            "visit_count": visit_count,
            "last_visit_time": visit_time.strftime("%Y-%m-%d %H:%M:%S"),
            # Store raw last_visit_time for comparison
            "last_visit_time_raw": last_visit_time,
        }
    )
    return temp_history


def add_search_data_to_history(history):
    temp_history = []
    for entry in history:
        url = entry["url"]
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        if "q" in query:
            entry["search_query"] = unquote(query["q"][0])
        elif "query" in query:
            entry["search_query"] = unquote(query["query"][0])
        elif "p" in query:
            entry["search_query"] = unquote(query["p"][0])
        elif is_loggable_search_system(url):
            for site in CHAT_BASED_SEARCH_COMPLEMENTS:
                if url.startswith(site):
                    entry["search_label"] = "chat-based-search-complement"
                    entry["search_query"] = "..."
                    break
            else:
                entry["search_label"] = "not-url-based"
                entry["search_query"] = "..."
        else:
            entry.pop("search_query", None)
        
        if any(url.startswith(site) for site in SITE_SEARCH_DOMAINS):
            entry["search_label"] = "site_search"
        if not cleanup(url, temp_history):
            entry["search_label"] = "redirect"

        if "search_query" in entry and entry["search_query"]:
            entry["search_engine"] = parsed_url.netloc.replace("www.", "")
        if "search_query" in entry:
            temp_history = update_temp_history(temp_history, url, entry["title"], entry["visit_count"], entry["last_visit_time"])
        
    return history

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
    }

    if is_loggable_search_system(url):
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

def get_surrounding_history(url, history, context_window=3):
    for i, entry in enumerate(history):
        if entry['url'] == url:
            return history[i-context_window:i+context_window]

def load_cache():
    import glob
    cache_files = glob.glob('cached_histories/cache_*.json')
    if cache_files:
        most_recent_file = max(cache_files, key=os.path.getctime)
        with open(most_recent_file, "r") as f:
            return json.load(f)
    else:
        return []

def clear_old_cache():
    cache_files = glob.glob('cached_histories/cache_*.json')
    if len(cache_files) > 3:
        # Sort files by creation time
        sorted_files = sorted(cache_files, key=os.path.getctime)
        # Delete the oldest files, keeping only the 3 most recent
        for file_to_delete in sorted_files[:-3]:
            os.remove(file_to_delete)


def save_cache(history):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    cache_dir = "cached_histories"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    with open(f"{cache_dir}/cache_{timestamp}.json", "w") as f:
        json.dump(history, f)
    clear_old_cache()

def is_guid_version_of_query(url, url_to_check_against):
        """
        Determines if a URL is a GUID version of another URL.
        Example:
        - checking_url: https://www.perplexity.ai/search/?q=is+there+a+kid+focused+search+engine%3F
        - checking_against_url: https://www.perplexity.ai/search/is-there-a-zNl4gXV4Tjmq5_FCHOORHQ?s=u
        This function returns True if one URL is the GUID version of the other.
        """
        url_to_check_against_reduced = url_to_check_against.replace(
            "https://www.perplexity.ai/search/", "")
        url_reduced = url.replace("https://www.perplexity.ai/search/?q=", "")
        terms_url_string_to_check_against = url_to_check_against_reduced.split(
            "-")
        url_string_to_check_against = "-".join(
            terms_url_string_to_check_against[:-1])
        hyphenated_url_query = url_reduced.replace(
            "+", "-").replace("%20", "-")
        return hyphenated_url_query.startswith(url_string_to_check_against)



def get_chromium_history(data_path):

    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"The specified path does not exist: {data_path}")
    history_db = os.path.join(data_path, "History")

    # Copy the database to a new location
    copied_db = os.path.join(data_path, "Copied_History")
    shutil.copyfile(history_db, copied_db)

    # Connect to the copied database
    c = sqlite3.connect(copied_db)
    cursor = c.cursor()
    # Query to extract the browser's history
    query = "SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC"

    # Execute the query
    cursor.execute(query)

    # Fetch all results
    results = cursor.fetchall()

    # Close the connection to the database
    cursor.close()
    c.close()

    # Create a list to hold the history
    history = []

    # Loop through the results and format them
    temp_history = []
    for url, title, visit_count, last_visit_time in results:
        if is_likely_countable_search_url(temp_history, url, visit_count):
            temp_history = update_temp_history(temp_history, url, title, visit_count, last_visit_time)
    # Filter out the raw last_visit_time before appending to the final history list
    history = [
        {k: v for k, v in entry.items() if k != "last_visit_time_raw"}
        for entry in temp_history
    ]

    history = add_search_data_to_history(history)
    
    # Return the formatted history
    save_cache(history)

    return history

def get_history_by_week(history: List[HistoryItem], week_num: int = 0, start_on_monday: bool = True) -> HistoryByWeek:
    current_date = datetime.now()

    
    # Adjust the start day of the week based on user preference
    if start_on_monday:
        start_day_adjustment = (current_date.weekday() + 7) % 7
    
    else:  # If start_on_monday is False, the week starts on Sunday
        start_day_adjustment = (current_date.weekday() + 1) % 7
    
    week_start_day = (current_date - timedelta(days=start_day_adjustment)).date()
    
    start_date = week_start_day - timedelta(days=7 * week_num)
    end_date = start_date + timedelta(days=6)
    
    filtered_history = [
        entry
        for entry in history
        if start_date
        <= datetime.strptime(entry["last_visit_time"], "%Y-%m-%d %H:%M:%S").date()
        <= end_date
    ]
    week_search_data: HistoryByWeek = {
        "week_num": week_num,
        "start_date": start_date,
        "end_date": end_date,
        "history": filtered_history,
    }
    return week_search_data


def get_search_engine_percentages(
    history: List[HistoryItem],
    week_num: int = 0,
    start_on_monday: bool = True,
    all: bool = False,
    hide_complements: bool = True
) -> Dict[str, Any]:
    """
    Processes search history to calculate the percentage of searches done on 
    different search engines over a specified number of weeks.

    :param history: List of search history entries.
    :param week_num: Number of weeks backwards from this week to analyze.
    :param start_on_monday: Whether the week starts on Monday or not.
    :return: A dictionary containing the search engine data and the start and end dates for the week.
    """
    if all:
        scoped_history = {
            "history": history,
            "start_date": history[0]["last_visit_time"],
            "end_date": history[-1]["last_visit_time"],
        }
    else:
        scoped_history = get_history_by_week(history, week_num, start_on_monday)
    search_engines = Counter()
    search_query_history = []
    for entry in scoped_history["history"]:
        if "search_query" in entry and entry["search_query"]:
            if entry.get("search_label", None) in ["duplicate", "redirect", "site_search"]:
                continue
            if hide_complements and entry.get("search_label", None) == "chat-based-search-complement":
                continue
            parsed_url = urlparse(entry["url"])
            search_engine = parsed_url.netloc
            search_engines[search_engine] += 1
            search_query_history.append({
                "search_engine": search_engine,
                "search_query": entry["search_query"],
                "url": entry["url"],
                "last_visit_time": entry["last_visit_time"]
            })
    total_searches = sum(search_engines.values())

    search_engines = {
        key.replace("www.", ""): value for key, value in search_engines.items()
    }

    sorted_search_engines = sorted(
        search_engines.items(),
        key=lambda x: (x[1] / total_searches) * 100,
        reverse=True,
    )

    
    # Return the search engine data and the start and end dates for the week
    return {
        "start_date": scoped_history["start_date"],
        "end_date": scoped_history["end_date"],
        "total_searches": total_searches,
        "search_query_history": search_query_history,
        "search_engines": sorted_search_engines,
    }

def get_search_entry_by_datetime(history: List[Dict[str, Any]], datetime_str: str) -> Optional[Dict[str, Any]]:
    target_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    for entry in history:
        entry_datetime = datetime.strptime(entry["last_visit_time"], "%Y-%m-%d %H:%M:%S")
        if entry_datetime == target_datetime:
            return entry
    return None

def get_random_search_url(history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    search_history = [
        entry for entry in history if entry.get("search_query") and 
        entry.get("search_label", None) not in ["redirect", "duplicate", 
                                      "chat-based-search-complement", 
                                      "not-url-based"]
    ]
    return random.choice(search_history) if search_history else None
