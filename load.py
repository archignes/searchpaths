import csv
import glob
import json
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlparse

import pytz

from config import SKIP_DOMAINS
from extract_htu import get_htu_history
from sp_types import HistoryItem
from utils import convert_chrome_time


def load_cache():
    import glob

    cache_files = glob.glob("cached_histories/cache_*.json")
    if cache_files:
        most_recent_file = max(cache_files, key=os.path.getctime)
        with open(most_recent_file, "r") as f:
            return json.load(f)
    else:
        return []


def clear_old_cache():
    cache_files = glob.glob("cached_histories/cache_*.json")
    if len(cache_files) > 3:
        # Sort files by creation time
        sorted_files = sorted(cache_files, key=os.path.getctime)
        # Delete the oldest files, keeping only the 3 most recent
        for file_to_delete in sorted_files[:-3]:
            os.remove(file_to_delete)


def save_cache(history):
    def datetime_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError("Object of type '{}' is not JSON serializable".format(type(o).__name__))

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    cache_dir = "cached_histories"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    with open(f"{cache_dir}/cache_{timestamp}.json", "w") as f:
        json.dump(history, f, default=datetime_serializer)
    clear_old_cache()


def get_tsv_history(data_path: str) -> List[HistoryItem]:
    with open(data_path, "r") as f:
        data_reader = csv.reader(f, delimiter="\t")
        data = [row for row in data_reader]

    raw_history = []
    for entry in data:
        (
            url,
            host,
            domain,
            visit_time,
            visit_time_string,
            day_of_visit,
            transition,
            title,
        ) = entry
        history_item = HistoryItem(
            url=url,
            title=title,
            visit_count=1,
            last_visit_time=visit_time_string,
            last_visit_time_datetime=convert_chrome_time(visit_time),
        )
        raw_history.append(history_item)

    return raw_history


def get_chromium_history(data_path: str) -> List[HistoryItem]:
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"The specified path does not exist: {data_path}")
    history_db = os.path.join(data_path, "History")

    copied_db = os.path.join(data_path, "Copied_History")
    shutil.copyfile(history_db, copied_db)

    c = sqlite3.connect(copied_db)
    cursor = c.cursor()
    query = "SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC"

    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    c.close()

    raw_history = []
    for entry in data:
        url, title, visit_count, last_visit_time = entry
        history_item = HistoryItem(
            url=url,
            title=title,
            visit_count=int(visit_count),
            last_visit_time=last_visit_time,
            last_visit_time_datetime=convert_chrome_time(last_visit_time),
        )
        raw_history.append(history_item)

    return raw_history


def get_json_history(data_path: str) -> List[HistoryItem]:
    with open(data_path, "r") as f:
        data = json.load(f)
        # add last_visit_time_datetime
        for entry in data:
            entry["last_visit_time_datetime"] = convert_chrome_time(
                entry["last_visit_time"]
            )
        return data


def remove_invalid_history(history: List[HistoryItem]) -> List[HistoryItem]:
    def is_valid_history_item(item: HistoryItem) -> bool:
        stat = item["last_visit_time_datetime"].year != 1600
        return stat
    return [
        item
        for item in history
        if is_valid_history_item(item)
    ]

def update_last_visit_time(history: List[HistoryItem]) -> List[HistoryItem]:
    for item in history:
        item["last_visit_time"] = item["last_visit_time_datetime"].strftime('%Y-%m-%d %H:%M:%S')
    return history

def get_history(data_path: str) -> List[HistoryItem]:
    if data_path == "htu_sync":
        raw_history = get_htu_history()
    elif data_path.endswith(".tsv"):
        raw_history = get_tsv_history(data_path)
    elif data_path.endswith(".json"):
        raw_history = get_json_history(data_path)
    else:
        raw_history = get_chromium_history(data_path)
    history = update_last_visit_time(raw_history)
    return remove_invalid_history(history)
