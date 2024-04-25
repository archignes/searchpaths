import textwrap
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse

from pyfzf.pyfzf import FzfPrompt  # type: ignore
from termcolor import cprint

from export import export_searches
from extract import get_surrounding_history
from load import load_cache
from process import get_search_engine_percentages
from sp_types import SearchHistoryItem


def print_search_lines(history_item: SearchHistoryItem):
    if "search_engine" in history_item and history_item["search_engine"]:
        print()
        system_line = f"{' '*6}{'System:':<8}{history_item['search_engine']:<13}"
        print(system_line)
        if "search_label" in history_item and history_item["search_label"]:
            label_line = f"{' '*6}{'Label:':<8}[{history_item['search_label']}]"
            wrapped_label_line = "\n".join(
                textwrap.wrap(label_line, width=80, subsequent_indent=" " * 14)
            )
            print(wrapped_label_line)
        if "search_query" in history_item and history_item["search_query"]:
            query_line = f"{' '*6}{'Query:':<8}[{history_item['search_query']}]"
            wrapped_query_line = "\n".join(
                textwrap.wrap(query_line, width=80, subsequent_indent=" " * 14)
            )
            print(wrapped_query_line)


def print_history_items(records: List[SearchHistoryItem], url=None, full_history=False):
    print(f"{'Index':<6}{'  Last Visit Time':<25}{'URL'}")
    divider = "-" * 80
    print(divider)

    count = 1
    for history_item in records:
        if not (full_history or history_item["included_search_entry"]):
            continue
        if history_item["default_visible"] == False:
            continue
        n = count
        count += 1
        last_visit_time = history_item["last_visit_time"]
        url_item = history_item["url"].strip()
        full_line = f"{n:<6}{last_visit_time:<25}"
        url_line = f"{' '*6}URL: {url_item}"
        wrapped_line = "\n".join(textwrap.wrap(full_line, width=80))
        if history_item["url"] == url:
            print(f"{'         **Subject Search Entry**     '}")
            print()
            print(f"{wrapped_line}")
            print_search_lines(history_item)
            print(f"{url_line}")
            print()
            print(divider)
        else:
            print(f"{wrapped_line}")
            print_search_lines(history_item)
            print(f"{url_line}")
            print(divider)
    print(divider)


def print_search_engine_percentages(
    data, min_percentage=None, top_n=10, by_month=False, full_history=False
):
    """
    Prints the formatted search engine percentages and other relevant data.

    :param data: The data dictionary returned by get_search_engine_percentages.
    :param min_percentage: Minimum percentage to display a search engine.
    :param top_n: Number of top search engines to display.
    """
    start_date = data["start_date"].date()
    current_date = datetime.now().date()
    week_difference = (current_date - start_date).days // 7

    if by_month:
        label = f"   {start_date.strftime('%B')} {start_date.strftime('%Y')}"
    elif full_history:
        label = "   Full history view"
    elif week_difference == 0:
        label = "   Week: Current"
    elif week_difference == 1:
        label = "   Week: 1 week ago"
    else:
        label = f"   Week: {week_difference} weeks ago"

    label += f"\n   {data['start_date'].strftime('%A')} {data['start_date'].strftime('%Y-%m-%d')} to {data['end_date'].strftime('%Y-%m-%d')}"
    print()
    cprint(label, "cyan")

    print("  |-----------------------------------------|")
    print("  | #  | System            | %      | Count |")
    print("  |----|-------------------|--------|-------|")

    other_percentage = 100
    for index, (search_engine, count) in enumerate(
        data["search_engines"][:top_n] if top_n is not None else data["search_engines"],
        start=1,
    ):
        percentage = (count / data["total_searches"]) * 100
        other_percentage -= percentage if top_n is not None else 0
        if min_percentage is None or percentage >= min_percentage:
            engine_display = (
                search_engine
                if len(search_engine) <= 17
                else search_engine[:14] + "..."
            )
            print(
                f"  | {index:<2} | {engine_display:<17} | {percentage:5.2f}% | {count:5} |"
            )

    if top_n is not None:
        other_count = data["total_searches"] - sum(
            count for _, count in data["search_engines"][:top_n]
        )
        if other_count > 0:
            print(
                f"  | -  | other             | {other_percentage:5.2f}% | {other_count:5} |"
            )
        elif data["total_searches"] == 0:
            if full_history:
                no_searches_label = "."
            elif by_month:
                no_searches_label = " for this month."
            else:
                no_searches_label = " for this week."
            print(f"  |      No searches found{no_searches_label:<18}|")
        print("  |-----------------------------------------|")
    print()
    total_systems_used = len(
        set(search_engine for search_engine, _ in data["search_engines"])
    )
    cprint(f"   Total desktop searches: {data['total_searches']}", "green")
    print(f"   Total systems searched: {total_systems_used}")
    print("  -------------------------------------------")
    print("         Searchpaths, from ARCHIGNES")
    return data


def investigate_week(timespan_data):
    """
    Initiates the investigation process for a specific week's search data.

    Parameters:
    - timespan_data: A dictionary containing data for a specific week, including
      search engines and their search counts.
    """
    print_week_summary(timespan_data)
    user_input = (
        input(
            "Type 'all' to list all or just press enter to explore by "
            "search system: "
        )
        .strip()
        .lower()
    )
    if user_input == "all":
        list_all_investigation(timespan_data)
    else:
        particular_investigation(timespan_data)


def print_week_summary(timespan_data):
    """
    Prints a summary of the week's search data.

    Parameters:
    - timespan_data: A dictionary containing data for a specific week.
    """
    total_searches = sum(count for _, count in timespan_data["search_engines"])
    total_engines = len(timespan_data["search_engines"])
    print(
        f"\nDuring this week, there were a total of {total_searches} searches "
        f"across {total_engines} search engines.\n"
    )


def list_all_investigation(timespan_data=None, full_history=False):
    """
    Lists all searches in a formatted table, sorted in reverse chronological order.
    """
    
    if full_history:
        sorted_searches = [item for item in load_cache() if "search_engine" in item]
        data = {
            "search_history": sorted_searches,
            "start_date": (
                sorted_searches[0]["last_visit_time"]
                if sorted_searches
                else datetime.now()
            ),
            "end_date": (
                sorted_searches[-1]["last_visit_time"]
                if sorted_searches
                else datetime.now()
            ),
        }
    else:
        sorted_searches = sorted(
            timespan_data["search_history"],
            key=lambda x: x["last_visit_time"],
            reverse=True,
        )
        data = {
            "search_history": sorted_searches,
            "start_date": timespan_data["start_date"],
            "end_date": timespan_data.get("end_date", datetime.now().date()),
        }

    print_history_items(sorted_searches)
    investigation_user_interaction(data)


def add_search_engine_data(data):
    search_engine_data = set(
        [
            item["search_engine"].replace("www.", "")
            for item in data["search_history"]
        ]
    )
    updated_data = {}
    updated_data["search_engines"] = {
        search_engine: 0 for search_engine in list(search_engine_data)
    }
    print(updated_data["search_engines"])
    updated_data["search_history"] = data["search_history"]
    updated_data["start_date"] = data["search_history"][0]["last_visit_time"]
    updated_data["end_date"] = data["search_history"][-1]["last_visit_time"]
    return updated_data


def particular_investigation(data):
    """
    Allows the user to investigate a particular search engine's data.

    Parameters:
    - data: A dictionary containing data for a specific week or all searches.
    """
    if "search_engines" not in data:
        data = add_search_engine_data(data)
    fzf = FzfPrompt()
    search_engine_list = [engine for engine in data["search_engines"].keys()]
    selected_engine = fzf.prompt(
        search_engine_list, "--prompt='Select a search engine: '"
    )[0]
    # Calculate the time range from the start date to the end date or current date
    start_date = data["start_date"]
    end_date = data.get("end_date", datetime.now().date())
    try:
        start_week = start_date.isocalendar()[1]
        start_year = start_date.isocalendar()[0]
    except AttributeError:
        # If the date is not a valid datetime object, convert it to a datetime object
        start_date = datetime.strptime(start_date.split(" ")[0], "%Y-%m-%d").date()
        start_week = start_date.isocalendar()[1]
        start_year = start_date.isocalendar()[0]
    try:
        end_week = end_date.isocalendar()[1]
        end_year = end_date.isocalendar()[0]
    except AttributeError:
        # If the date is not a valid datetime object, convert it to a datetime object
        end_date = datetime.strptime(end_date.split(" ")[0], "%Y-%m-%d").date()
        end_week = end_date.isocalendar()[1]
        end_year = end_date.isocalendar()[0]
    week_difference_start = (start_year - end_year) * 52 + (start_week - end_week)
    week_difference_end = (end_year - start_year) * 52 + (end_week - start_week)

    # Determine the appropriate time phrase based on the calculated time range
    if week_difference_start == 0 and week_difference_end == 0:
        time_phrase = "Week: Current"
    elif week_difference_start == 1 and week_difference_end == 1:
        time_phrase = "Week: Last"
    elif week_difference_start > 1 or week_difference_end > 1:
        time_phrase = (
            f"from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
    selected_engine_searches = [
        entry
        for entry in data["search_history"]
        if urlparse(entry["url"]).netloc.replace("www.", "") == selected_engine
    ]

    print(f"\nSearches made with {selected_engine} {time_phrase}:")
    print_history_items(selected_engine_searches)
    investigation_user_interaction(data, selected_engine_searches)


def dive_into_search_context(
    search: SearchHistoryItem, context_window: int = 3
) -> None:
    """
    Allows the user to dive into the context of a search for a specific week.

    Parameters:
    - search: A dictionary containing data for a specific search.
    """
    url = search["url"]
    history = load_cache()
    surrounding_history = get_surrounding_history(
        url, history, context_window=context_window
    )
    print("\nSurrounding History\n")
    print_history_items(surrounding_history, url=url)
    print(
        "Submit a number to expand the context window (less than 50) or "
        "press enter to exit:"
    )
    input_window_size = input()
    if input_window_size.isdigit() and int(input_window_size) < 50:
        context_window = int(input_window_size)
        return dive_into_search_context(search, context_window)


def investigation_user_interaction(data, selected_engine_searches=None):
    """
    Handles user interaction during the investigation of a specific engine's searches.

    Parameters:
    - data: Data for a specific week or all searches.
    - selected_engine_searches: Searches related to the selected engine.
    """

    print()
    while True:
        user_choice = input(
            "Investigation Menu:\n"
            " - 'R' to Return to the main menu\n"
            " - 'I' to Investigate an engine\n"
            " - 'Q' to Quit\n"
            " - Enter a query number for detailed data: "
        ).lower()
        if user_choice == "r":
            break
        elif user_choice == "i":
            particular_investigation(data)
            break
        elif user_choice == "e":
            export_searches(data)
            break
        elif user_choice == "q":
            exit(0)
        else:
            try:
                query_number = int(user_choice)
                searches_to_use = (
                    data["search_history"]
                    if selected_engine_searches is None
                    else selected_engine_searches
                )
                if 1 <= query_number <= len(searches_to_use):
                    search = searches_to_use[query_number - 1]
                    print(f"\nDetailed data for query {query_number}:")
                    for key, value in search.items():
                        print(f"{key}: {value}")
                surrounding_context = input(
                    "\nWould you like to see the " "surrounding context? (Y/N): "
                ).lower()
                if surrounding_context == "y":
                    dive_into_search_context(search)
                else:
                    print("Invalid query number. Please try again.")
            except ValueError:
                print("Invalid option. Please try again.")


def fzf_search_queries(search_history: List[SearchHistoryItem]):
    """
    Allows the user to select a search query from the history using fzf (fuzzy finder),
    and then dives into the search context of the selected query.

    Parameters:
    - search_history (list of SearchHistoryItem): The search history containing search queries and labels.

    This function filters out entries with certain labels such as 'redirect', 'duplicate', and
    others, and then presents the remaining queries to the user to select using fzf. If multiple
    entries are found for a selected query, the user is prompted again to select one specific entry.
    """
    fzf = FzfPrompt()
    filtered_search_history = [
        entry
        for entry in search_history
        if entry.get("search_query")
        and entry.get("search_label", None)
        not in [
            "redirect",
            "duplicate",
            "chat-based-search-complement",
            "not-url-based",
            "site_search",
            "",
        ]
    ]
    search_queries: List[SearchHistoryItem] = [
        item for item in filtered_search_history if item["included_search_entry"]
    ]
    print(f"Total number of queries: {len(search_queries)}")
    search_query_mapping: dict[str, List[SearchHistoryItem]] = {}
    for item in search_queries:
        search_query = item["search_query"]
        if search_query is not None:
            if search_query not in search_query_mapping:
                search_query_mapping[search_query] = []
            search_query_mapping[search_query].append(item)

    # Create a list of search queries with their counts
    search_query_options = [
        f"{search_query} ({len(search_query_mapping[search_query])})"
        for search_query in search_query_mapping
    ]
    # Sort the search queries by string in descending order ignoring case
    search_query_options.sort(key=lambda x: x.lower())
    selected_query = fzf.prompt(
        search_query_options, "--prompt='Select a search query: '"
    )[0]
    selected_query = selected_query.split(" (")[0]

    if selected_query:
        selected_entries = search_query_mapping.get(selected_query, [])
        if selected_entries:
            if len(selected_entries) > 1:
                selected_entry = fzf.prompt(
                    [str(entry) for entry in selected_entries],
                    "--prompt='Multiple entries found. Select one: '",
                )[0]
                selected_entry = next(
                    filter(lambda x: str(x) == selected_entry, selected_entries), None
                )
            else:
                selected_entry = selected_entries[0]

            dive_into_search_context(selected_entry)


def interact_with_user_for_search_data(
    search_history, week_num=None, hide_complements=True
):
    """
    Engages the user to present search engine usage percentages for a given
    week or a span of weeks, initiating with the current week's data, and
    accommodates a variety of user choices for data interaction.
    """

    # Determine the total number of searches logged
    total_searches_logged = len(
        [
            item
            for item in search_history
            if "search_query" in item and item["search_query"] is not None
        ]
    )
    # Determine the total number of weeks logged

    if week_num is None:
        current_timespan_num = 0
    else:
        current_timespan_num = week_num
    timespan_data = get_search_engine_percentages(
        search_history, week_num=current_timespan_num, hide_complements=hide_complements
    )
    print_search_engine_percentages(timespan_data)
    
    
    context = "week_view"
    
    while True:
        print(
        f"\n  Total {timespan_data['label']}s logged: {timespan_data['total_timespan_periods_logged']}."
    )
    
        views = {
        "week_view": f"Week {current_timespan_num}",
        "month_view": f"Month {current_timespan_num}",
        "full_view": "Full",
        "list_all": "List All",
            }
        print(f"  Current view: {views[context]}")
        
        menu_options = {
            "V": f"show the current {timespan_data['label']}'s percentages",
            "A": f"for a list of All {total_searches_logged} searches",
            "L": f"for a List of the {timespan_data['total_searches']} search{'es' if timespan_data['total_searches'] != 1 else ''} for the {timespan_data['label']}",
            "M": f"to toggle the Month view",
            "W": f"to toggle the Week view",
            "F": f"to toggle the Full data view",
            "P": f"for the Previous {timespan_data['label']} ({current_timespan_num + 1})",
            "N": f"for the Next {timespan_data['label']} ({current_timespan_num - 1})",
            "S": f"to jump to a Specific {timespan_data['label']}",
            "C": f"to {'exclude' if hide_complements else 'include'} chat-based search Complements",
            "I": f"to Investigate the {timespan_data['label']}",
            "E": f"to Export the {timespan_data['label']}",
            "Q": "to Quit",
        }
        if context is None:
            del menu_options["V"]
        if context == "list_all":
            del menu_options["A"]
        if context == "month_view":
            del menu_options["M"]
        if context == "full_view":
            del menu_options["F"]
        if context == "week_view":
            del menu_options["W"]
        if current_timespan_num == 0:
            del menu_options["N"]  # Remove option for previous week
        elif current_timespan_num == timespan_data["total_timespan_periods_logged"]:
            print("This is the last week. No previous week.")
            del menu_options["P"]  # Remove option for next week

        # Constructing the menu string from the options dictionary
        menu_string = "Menu:"
        for key, value in menu_options.items():
            menu_string += f"\n - '{key}' {value}"

        user_choice = input(menu_string + "\n").lower()
        if user_choice == "n":
            if current_timespan_num == 0:
                print("This is the first week. No previous week.")
                continue
            current_timespan_num -= 1
            if context == "month_view":
                timespan_data = get_search_engine_percentages(
                    search_history, month_num=current_timespan_num, by_month=True
                )
            else:
                timespan_data = get_search_engine_percentages(
                    search_history, week_num=current_timespan_num
                )
            print_search_engine_percentages(timespan_data)
        elif user_choice == "f":
            context = "full_view"
            timespan_data = get_search_engine_percentages(
                search_history, full_history=True
            )
            print_search_engine_percentages(timespan_data, full_history=True)
        elif user_choice == "a":
            list_all_investigation(full_history=True)
            context = "list_all"
        elif user_choice == "m":
            # convert current_timespan_num to a month
            # Adjust current_timespan_num to month number using modulo division
            current_timespan_num = (current_timespan_num - 1) // 4 + 1
            timespan_data = get_search_engine_percentages(
                search_history, by_month=True, month_num=current_timespan_num
            )
            print_search_engine_percentages(timespan_data, by_month=True)
            context = "month_view"
        elif user_choice == "w":
            timespan_data = get_search_engine_percentages(
                search_history, week_num=current_timespan_num
            )
            print_search_engine_percentages(timespan_data)
            context = "week_view"
        elif user_choice == "v":
            return interact_with_user_for_search_data(
                search_history,
                week_num=current_timespan_num,
                hide_complements=hide_complements,
            )
        elif user_choice == "c":
            return interact_with_user_for_search_data(
                search_history,
                week_num=current_timespan_num,
                hide_complements=not hide_complements,
            )
        elif user_choice == "l":
            list_all_investigation(timespan_data)
            context = "list"
        elif user_choice == "p":
            current_timespan_num += 1
            if context == "month_view":
                timespan_data = get_search_engine_percentages(
                    search_history, month_num=current_timespan_num, by_month=True
                )
                print_search_engine_percentages(timespan_data, by_month=True)
            else:
                timespan_data = get_search_engine_percentages(
                    search_history, week_num=current_timespan_num
                )
                print_search_engine_percentages(timespan_data)
        elif user_choice == "s":
            week_num = int(input("Enter the number of weeks back to view: "))
            current_timespan_num = week_num
            timespan_data = get_search_engine_percentages(
                search_history, week_num=week_num
            )
            print_search_engine_percentages(timespan_data)
            context = "specific_week"
        elif user_choice == "i":
            investigate_week(timespan_data)
            context = "investigate_week"
        elif user_choice == "e":
            data_scope = input(
                "Export data for:\n1: This week\n2: All history\n: "
            ).strip()
            if data_scope == "1":
                export_searches(timespan_data)
            elif data_scope == "2":
                export_searches(search_history)
            elif user_choice == "q":
                break
            else:
                print("Invalid option. Please try again.")
            context = "export"
        elif user_choice == "q":
            break
        else:
            print("Invalid option. Please try again.")
