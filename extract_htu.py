# See https://sites.google.com/view/history-trends-unlimited/faq#h.p_Ierouyo2Q6LA

import os
import shutil
import sqlite3
from typing import List
from datetime import datetime
from searchpath_types import HistoryItem
from config import HTU_PROFILE_PATH

# Change the threshold to the size you expect of the HTU database
# See chrome-extension://pnmchffiealhkdloeffcdnbgdnedheme/options.html
# Storage Stats
# Database Size:	__ MB
THRESHOLD = 10 * 1024 * 1024 # 10 MB

# This is the path to the folder where the database will be copied to and 
# where the filepath will be cached
EXTERNAL_DATA_PATH = "external_data/htu"


def cache_filepath(filepath: str):
    htu_database_filepath = os.path.join(EXTERNAL_DATA_PATH, "htu_database_filepath.txt")
    with open(htu_database_filepath, "w") as f:
        f.write(filepath)

def find_htu_history_database(profile_path: str) -> str:
    # Check for cached filepath
    htu_database_filepath = os.path.join(EXTERNAL_DATA_PATH, "htu_database_filepath.txt")
    if os.path.exists(htu_database_filepath):
        with open(htu_database_filepath, "r") as f:
            return f.read()

    # Navigate to the profile path + File System
    # You may need to instead navigate the Databases folder
    # (see the link above and find_htu_history_database_legacy below)
    file_system_path = os.path.join(profile_path, "File System")
    large_files = []

    
    if not os.path.exists(file_system_path):
        print(f"Directory not found: {file_system_path}")
        return []

    # Function to recursively find large files
    def find_large_files(directory):
        for entry in os.scandir(directory):
            if entry.is_dir():
                find_large_files(entry.path)
            elif entry.is_file():
                if entry.stat().st_size > THRESHOLD:
                    large_files.append(entry.path)
                    size_in_mb = entry.stat().st_size / (1024 * 1024)
                    print(f"Found large file: {entry.path} ({size_in_mb:.2f} MB)")

    find_large_files(file_system_path)
    # Function to check if a file has the required tables
    def has_required_tables(file_path):
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            # Check for 'urls' and 'visits' tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            return 'urls' in tables and 'visits' in tables
        except sqlite3.Error as e:
            return False
        finally:
            conn.close()

    # Sort files by modification time
    large_files_sorted = sorted(large_files, key=lambda x: os.path.getmtime(x), reverse=True)

    # Try opening each file with sqlite to check for 'urls' and 'visits' tables
    print(f"Checking {len(large_files_sorted)} files for HTU database")
    for file_path in large_files_sorted:
        if has_required_tables(file_path):
            print(f"Found HTU database: {file_path}")
            cache_filepath(file_path)
            print(f"Caching the filepath: {file_path}")
            return file_path


def get_htu_history() -> List[HistoryItem]:
    # Ensure the target directory exists
    os.makedirs(EXTERNAL_DATA_PATH, exist_ok=True)

    database_path = find_htu_history_database(HTU_PROFILE_PATH)

    # Copy it to the external data folder
    shutil.copy(database_path, EXTERNAL_DATA_PATH)

    # Attempt to read the copy

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
    visit_counts = {}
    for urlid, _, _, _ in data:
        if urlid in visit_counts:
            visit_counts[urlid] += 1
        else:
            visit_counts[urlid] = 1

    # Create a list of history items using the precomputed visit counts
    history_items = []
    for urlid, url, title, visit_time in data:           
        if not title:
            title = ""
        last_visit_time = datetime.fromtimestamp(float(visit_time)/1000).strftime('%Y-%m-%d %H:%M:%S')
        history_item = {
            "url": url,
            "title": title,
            "visit_count": visit_counts.get(urlid, 1),  # Use .get() with default 1
            "last_visit_time": last_visit_time
        }
        history_items.append(history_item)

    history_items.sort(key=lambda x: x["last_visit_time"], reverse=True)

    return history_items




# def find_htu_history_database_legacy(profile_path) -> str:
#     # Navigate to the profile path + Databases
#     databases_path = os.path.join(profile_path, "Databases")

#     # Look in the extension's folder
#     extension_path = os.path.join(databases_path, "chrome-extension_pnmchffiealhkdloeffcdnbgdnedheme_0")
#     item_name = os.listdir(extension_path)[0]  # Assuming there's only one item

#     return os.path.join(extension_path, item_name)

