import argparse
import os
from datetime import datetime
from termcolor import cprint

from pyfzf import FzfPrompt

import config
import extract
import show

from tests.test_mock_history import MOCK_HISTORY

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process browser history.")
    parser.add_argument(
        "-b",
        "--browser",
        choices=config.HISTORY_DATABASE_PATHS.keys(),
        help="Choose the browser's history to process.",
    )
    parser.add_argument(
        "-htu",
        "--htu",
        action="store_true",
        help="Load history from the HTU database.",
    )
    parser.add_argument(
        "-r",
        "--random",
        action="store_true",
        help="Show a random entry in deep context.",
    )
    parser.add_argument(
        "-d",
        "--date",
        type=str,
        help="Show entries from a specific datetime (YYYY-MM-DD HH:MM:SS).",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Load the mock history for interactive demo.",
    )
    parser.add_argument(
        "-z",
        "--fzf",
        action="store_true",
        help="Use fzf to search for and select a search query from your history.",
    )

    args = parser.parse_args()

    if args.browser or args.htu:
        if args.browser:
            browser_choice = args.browser
            data_path = os.path.expanduser(config.HISTORY_DATABASE_PATHS[browser_choice])
        if args.htu:
            browser_choice = "HTU sync"
            data_path = "htu"
        print(f"Processing history from {browser_choice} database...")
        history = extract.get_history(data_path)
        if args.random:
            random_url = extract.get_random_search_url(history)
            show.dive_into_search_context(random_url)
        elif args.date:
            search_entry = extract.get_search_entry_by_datetime(history, args.date)
            if search_entry:
                show.dive_into_search_context(search_entry)
            else:
                print(f"No entries found for {args.date}")
        elif args.fzf:
            show.fzf_search_queries(history)
        else:
            show.interact_with_user_for_search_data(history)
    elif args.test:
        history = extract.add_search_data_to_history(MOCK_HISTORY)
        extract.save_cache(history)
        show.interact_with_user_for_search_data(history)
    else:
        available_sources = []
        for browser_choice in config.HISTORY_DATABASE_PATHS:
            if os.path.exists(config.HISTORY_DATABASE_PATHS[browser_choice]):
                available_sources.append(browser_choice)
            else:
                print(f"The specified path does not exist: {config.HISTORY_DATABASE_PATHS[browser_choice]}")
        if config.HTU_PROFILE_PATH and os.path.exists(config.HTU_PROFILE_PATH):
            available_sources.append("HTU sync")
        if not available_sources:
            print("No available sources found. Exiting...")
            exit(1)
        fzf = FzfPrompt()
        selected_source = fzf.prompt(available_sources, "--prompt='Select a source: '")[0]
        if selected_source:
            print(f"Processing history from {selected_source} database...")
            if selected_source == "HTU sync":
                history = extract.get_history("htu")
            else:
                data_path = os.path.expanduser(config.HISTORY_DATABASE_PATHS[selected_source])
                history = extract.get_history(data_path)
            show.interact_with_user_for_search_data(history)
        exit(1)

    # Calculate the length of the history
    history_length = len(history)
    cprint(f"\nTotal history entries: {history_length}\n", "yellow")

    # Group history entries by month
    history_by_month = {}
    for entry in history:
        month = datetime.strptime(
            entry["last_visit_time"], "%Y-%m-%d %H:%M:%S"
        ).strftime("%Y-%m")
        if month not in history_by_month:
            history_by_month[month] = []
        history_by_month[month].append(entry)
