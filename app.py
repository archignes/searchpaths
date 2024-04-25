import argparse
from main import (
    process_history,
    process_test_history,
    get_available_sources,
    select_source,
    get_data_path
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process browser history.")
    parser.add_argument("--browser", help="Specify the browser to process.")
    parser.add_argument("--htu", action="store_true", help="Process HTU sync.")
    parser.add_argument("--random", action="store_true", help="Process a random browser.")
    parser.add_argument("--date", help="Specify the date to process.")
    parser.add_argument("--test", action="store_true", help="Run tests.")
    parser.add_argument("--fzf", action="store_true", help="Use fzf to select the browser.")

    args = parser.parse_args()

    if args.browser or args.htu:
        if args.browser:
            browser_choice = args.browser
            data_path = get_data_path(browser_choice)
        elif args.htu:
            browser_choice = "HTU sync"
            data_path = get_data_path("HTU sync")
        process_history(browser_choice, data_path, args)
    elif args.test:
        process_test_history()
    else:
        available_sources = get_available_sources()
        selected_source = select_source(available_sources)
        if selected_source:
            data_path = get_data_path(selected_source)
            process_history(selected_source, data_path, args)
        exit(1)

