import csv
from datetime import datetime
import os
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


def save_to_csv(history, timestamp):
    csv_filename = f"search_queries_{timestamp}.csv"
    with open(csv_filename, "w", newline="") as file:
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
    with open(txt_filename, "w") as file:
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
        "3: both\n"
        "Q: quit\n"
        ": "
    ).lower()
    formats = {"1": "csv", "2": "txt", "3": "both", "q": "quit"}
    file_format = formats.get(choice)
    if file_format == "quit":
        print("Export canceled.")
        return
    files_to_open = []
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    if file_format in ["csv", "both"]:
        csv_filename = save_to_csv(data, timestamp)
        files_to_open.append(csv_filename)
    if file_format in ["txt", "both"]:
        txt_filename = save_to_txt(data, timestamp)
        files_to_open.append(txt_filename)
    # print the files to open
    print(f"Exported files: {files_to_open}")
    # Open the saved files for the user
    for filename in files_to_open:
        os.system(f"open {filename}")
