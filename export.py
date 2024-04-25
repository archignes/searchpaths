import csv
import os
import json
from datetime import datetime
from urllib.parse import urlparse


def format_entry_for_file(entry):
    if entry["search_query"]:
        parsed_url = urlparse(entry["url"])
        root_domain = "{uri.netloc}".format(uri=parsed_url)
        formatted_date = entry["last_visit_time"]
        # Include the full URL in the formatted entry
        formatted_entry = {
            "csv": [formatted_date, root_domain, entry["search_query"], entry["url"]],
            "txt": f"{formatted_date}, {root_domain}, {entry['search_query']}, {entry['url']}\n",
        }
        return formatted_entry
    return None

def save_to_json(history, timestamp, dir):
    json_filename = f"search_queries_{timestamp}.json"
    # Convert datetime objects to strings
    for entry in history:
        if 'last_visit_time' in entry and isinstance(entry['last_visit_time'], datetime):
            entry['last_visit_time'] = entry['last_visit_time'].isoformat()
    with open(dir + json_filename, "w") as file:
        json.dump(history, file)
    return json_filename

def save_to_csv(history, timestamp):
    csv_filename = f"search_queries_{timestamp}.csv"
    with open(dir + csv_filename, "w", newline="") as file:
        writer = csv.writer(file)
        # Add 'URL' to the header
        writer.writerow(["Date", "Root Domain", "Search Query", "URL"])
        for entry in history:
            formatted_entry = format_entry_for_file(entry)
            if formatted_entry:
                writer.writerow(formatted_entry["csv"])
    return csv_filename


def save_to_txt(history, timestamp):
    txt_filename = f"search_queries_{timestamp}.txt"
    with open(dir + txt_filename, "w") as file:
        for entry in history:
            formatted_entry = format_entry_for_file(entry)

            if formatted_entry:
                file.write(formatted_entry["txt"])
    return txt_filename


def export_searches(data):
    """data is either all search history or week data"""
    choice = input(
        "Choose the file format to export search queries with `last_visit_time` and root domain:\n"
        "1: csv\n"
        "2: txt\n"
        "3: json\n"
        "Q: quit\n"
        ": "
    ).lower()
    formats = {"1": "csv", "2": "txt", "3": "json", "q": "quit"}
    file_format = formats.get(choice)
    if file_format == "quit":
        print("Export canceled.")
        return
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dir = "exports/"
    if file_format in ["csv"]:
        export_filename = save_to_csv(data, timestamp, dir)
    if file_format in ["txt"]:
        export_filename = save_to_txt(data, timestamp, dir)
    if file_format == "json":
        export_filename = save_to_json(data, timestamp, dir)
        
    # print the files to ope    n
    print(f"Exported file: {export_filename}")
    # Open the saved files for the user
    os.system(f"open {export_filename}")
