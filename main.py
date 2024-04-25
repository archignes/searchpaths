import os
from pyfzf.pyfzf import FzfPrompt   # type: ignore

from config import HISTORY_DATABASE_PATHS, HTU_PROFILE_PATH
from extract import get_random_search_url, get_search_entry_by_datetime
from load import get_history, save_cache
from process import get_search_history
from show import (
    dive_into_search_context,
    fzf_search_queries,
    interact_with_user_for_search_data
)

def process_history(browser_choice, data_path, args):
    print(f"Processing history from {browser_choice} database...")
    history = get_history(data_path)
    search_history = get_search_history(history)

    if args.random:
        random_url = get_random_search_url(search_history)
        if random_url:
            dive_into_search_context(random_url)
    elif args.date:
        search_entry = get_search_entry_by_datetime(search_history, args.date)
        if search_entry:
            dive_into_search_context(search_entry)
        else:
            print(f"No entries found for {args.date}")
    elif args.fzf:
        fzf_search_queries(search_history)
    else:
        interact_with_user_for_search_data(search_history)

def process_test_history():
    history = get_history("tests/mock_history_simple.json")
    search_history = get_search_history(history)
    save_cache(search_history)
    interact_with_user_for_search_data(search_history)

def get_available_sources():
    available_sources = []
    for browser_choice in HISTORY_DATABASE_PATHS:
        if os.path.exists(HISTORY_DATABASE_PATHS[browser_choice]):
            available_sources.append(browser_choice)
        else:
            print(
                f"The specified path does not exist: {HISTORY_DATABASE_PATHS[browser_choice]}"
            )
    if HTU_PROFILE_PATH and os.path.exists(HTU_PROFILE_PATH):
        available_sources.append("HTU sync")
    return available_sources

def select_source(available_sources):
    if not available_sources:
        print("No available sources found. Exiting...")
        exit(1)
    fzf = FzfPrompt()
    selected_source = fzf.prompt(available_sources, "--prompt='Select a source: '")[
        0
    ]
    return selected_source

def get_data_path(selected_source):
    if selected_source == "HTU sync":
        data_path = "htu_sync"
    else:
        data_path = os.path.expanduser(HISTORY_DATABASE_PATHS[selected_source])
    return data_path
