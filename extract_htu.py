# See https://sites.google.com/view/history-trends-unlimited/faq#h.p_Ierouyo2Q6LA

import os
import shutil
import sqlite3
from datetime import datetime
from typing import List, Union

from config import HTU_PROFILE_PATH
from sp_types import HistoryItem
from utils import convert_chrome_time

# Change the threshold to the size you expect of the HTU database
# See chrome-extension://pnmchffiealhkdloeffcdnbgdnedheme/options.html
# Storage Stats
# Database Size:	__ MB
THRESHOLD = 10 * 1024 * 1024  # 10 MB

# This is the path to the folder where the database will be copied to and
# where the filepath will be cached
EXTERNAL_DATA_PATH: str = "external_data/htu"


def cache_filepath(filepath: str) -> None:
    htu_database_filepath = os.path.join(
        EXTERNAL_DATA_PATH, "htu_database_filepath.txt"
    )
    with open(htu_database_filepath, "w") as f:
        f.write(filepath)


# Function to recursively find large files
def find_large_files(directory: str, large_files: List[str] = []) -> List[str]:
    for entry in os.scandir(directory):
        if entry.is_dir():
            find_large_files(entry.path, large_files)
        elif entry.is_file():
            if entry.stat().st_size > THRESHOLD:
                large_files.append(entry.path)
                size_in_mb = entry.stat().st_size / (1024 * 1024)
                print(f"Found large file: {entry.path} ({size_in_mb:.2f} MB)")
    return large_files


def has_required_tables(file_path: str) -> bool:
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        # Check for 'urls' and 'visits' tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        return "urls" in tables and "visits" in tables
    except sqlite3.Error as e:
        return False
    finally:
        conn.close()


def find_htu_history_database(profile_path: str) -> Union[None, str]:
    # Check for cached filepath
    htu_database_filepath = os.path.join(
        EXTERNAL_DATA_PATH, "htu_database_filepath.txt"
    )
    if os.path.exists(htu_database_filepath):
        with open(htu_database_filepath, "r") as f:
            return f.read()

    # Navigate to the profile path + File System
    file_system_path = os.path.join(profile_path, "File System")
    if not os.path.exists(file_system_path):
        print(f"Directory not found: {file_system_path}")
        return None

    large_files = find_large_files(file_system_path)
    # Sort files by modification time
    large_files_sorted = sorted(
        large_files, key=lambda x: os.path.getmtime(x), reverse=True
    )

    # Try opening each file with sqlite to check for 'urls' and 'visits' tables
    print(f"Checking {len(large_files_sorted)} files for HTU database")
    for file_path in large_files_sorted:
        if has_required_tables(file_path):
            print(f"Found HTU database: {file_path}")
            cache_filepath(file_path)
            print(f"Caching the filepath: {file_path}")
            return file_path
    return None


def get_htu_history() -> List[HistoryItem]:
    # Ensure the target directory exists
    os.makedirs(EXTERNAL_DATA_PATH, exist_ok=True)

    database_path = find_htu_history_database(HTU_PROFILE_PATH)
    if database_path is None:
        return []

    # Copy it to the external data folder
    shutil.copy(database_path, EXTERNAL_DATA_PATH)

    # Connect to the copied database
    copied_db_path = os.path.join(EXTERNAL_DATA_PATH, "copied_extension_database")
    shutil.copy(database_path, copied_db_path)
    connection = sqlite3.connect(copied_db_path)
    cursor = connection.cursor()

    # Combine data from the urls and visits tables to create a history list
    query = """
    SELECT urls.urlid, urls.url, urls.title, visits.visit_time
    FROM urls
    JOIN visits ON urls.urlid = visits.urlid
    ORDER BY visits.visit_time DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()

    # Create a dictionary to count visits per urlid
    visit_counts: dict[int, int] = {}
    for urlid, _, _, _ in data:
        if urlid in visit_counts:
            visit_counts[urlid] += 1
        else:
            visit_counts[urlid] = 1

    # Create a list of history items using the precomputed visit counts
    history_items: List[HistoryItem] = []
    for urlid, url, title, visit_time in data:
        title = title if title else ""
        formatted_visit_time = datetime.fromtimestamp(
            float(visit_time) / 1000
        ).strftime("%Y-%m-%d %H:%M:%S")
        history_item = HistoryItem(
            url=url,
            title=title,
            visit_count=visit_counts.get(urlid, 1),
            last_visit_time=formatted_visit_time,
            last_visit_time_datetime=convert_chrome_time(visit_time),
        )
        history_items.append(history_item)

    history_items.sort(key=lambda item: item["last_visit_time"], reverse=True)

    return history_items
