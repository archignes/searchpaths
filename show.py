import textwrap
from datetime import datetime, timedelta
from urllib.parse import urlparse

from pyfzf.pyfzf import FzfPrompt
from termcolor import cprint

from export import export_searches
from extract import (get_search_engine_percentages, get_surrounding_history,
                     load_cache)

def print_search_lines(history_item: dict):
        if 'search_query' in history_item and history_item['search_query']:
                print()
                system_line = f"{' '*6}{'System:':<8}{history_item['search_engine']:<13}"
                print(system_line)
                query_line = f"{' '*6}{'Query:':<8}[{history_item['search_query']}]"
                wrapped_query_line = '\n'.join(textwrap.wrap(query_line, width=80, 
                                              subsequent_indent=' ' * 14))
                print(wrapped_query_line)


def print_history_items(records, url=None):
    print(f"{'Index':<6}{'Last Visit Time':<25}{'URL'}")
    divider = "-" * 80
    print(divider)

    for n, history_item in enumerate(records, start=1):
        last_visit_time = history_item['last_visit_time']
        url_item = history_item['url'].strip()
        full_line = f"{n:<6}{last_visit_time:<25}{url_item}"
        wrapped_line = '\n'.join(textwrap.wrap(full_line, width=80, 
                                              subsequent_indent=' ' * 31))
        if history_item['url'] == url:
            print(divider)
            print()
            print(f"{'         **Subject Search Entry**     '}")
            print()
            print(f"{wrapped_line}")
            print_search_lines(history_item)
            print()
            print(divider)
        else:
            print(f"{wrapped_line}")
            print_search_lines(history_item)
            print(divider)
        print()
    print(divider)


def print_search_engine_percentages(data, min_percentage=None, top_n=10):
    """
    Prints the formatted search engine percentages and other relevant data.

    :param data: The data dictionary returned by get_search_engine_percentages.
    :param min_percentage: Minimum percentage to display a search engine.
    :param top_n: Number of top search engines to display.
    """
    start_date = data["start_date"]
    current_date = datetime.now().date()
    week_difference = ((current_date - start_date).days // 7)

    if week_difference == 0:
        week_label = "This week"
    elif week_difference == 1:
        week_label = "Last week"
    else:
        week_label = f"{week_difference} weeks ago"

    week_label += f"\n{data['start_date'].strftime('%A')} {data['start_date'].strftime('%Y-%m-%d')} to {data['end_date'].strftime('%Y-%m-%d')}"

    cprint(week_label, "cyan")
    cprint(f"Total desktop searches: {data['total_searches']}", "green")

    print("|-----------------------------------------|")
    print("| #  | System            | %      | Count |")
    print("|----|-------------------|--------|-------|")

    other_percentage = 100
    for index, (search_engine, count) in enumerate(
        data["search_engines"][:top_n] if top_n is not None else data["search_engines"], start=1
    ):
        percentage = (count / data["total_searches"]) * 100
        other_percentage -= percentage if top_n is not None else 0
        if min_percentage is None or percentage >= min_percentage:
            engine_display = (search_engine if len(search_engine) <= 17
                              else search_engine[:14] + '...')
            print(
                f"| {index:<2} | {engine_display:<17} | {percentage:5.2f}% | {count:5} |")

    if top_n is not None:
        other_count = data["total_searches"] - \
            sum(count for _, count in data["search_engines"][:top_n])
        print(
            f"| -  | other             | {other_percentage:5.2f}% | {other_count:5} |")
        
        print("|-----------------------------------------|")
        print("|        Searchpaths, from ARCHIGNES      |")
        print("|-----------------------------------------|")
    print()
    total_systems_used = len(
        set(search_engine for search_engine, _ in data["search_engines"]))
    print(f"Total systems searched: {total_systems_used}")
    print()
    return data


def investigate_week(week_data):
    """
    Initiates the investigation process for a specific week's search data.

    Parameters:
    - week_data: A dictionary containing data for a specific week, including
      search engines and their search counts.
    """
    print_week_summary(week_data)
    user_input = input("Type 'all' to list all or just press enter to explore by "
                       "search system: ").strip().lower()
    if user_input == "all":
        list_all_investigation(week_data)
    else:
        particular_investigation(week_data)


def print_week_summary(week_data):
    """
    Prints a summary of the week's search data.

    Parameters:
    - week_data: A dictionary containing data for a specific week.
    """
    total_searches = sum(count for _, count in week_data["search_engines"])
    total_engines = len(week_data["search_engines"])
    print(f"\nDuring this week, there were a total of {total_searches} searches "
          f"across {total_engines} search engines.\n")


def list_all_investigation(week_data=None, full_history=False):
    """
    Lists all searches in a formatted table, sorted in reverse chronological order.
    """
    if full_history:
        sorted_searches = [item for item in load_cache() if "search_engine" in item]
    else:    
        sorted_searches = sorted(
            week_data["search_query_history"],
            key=lambda x: x['last_visit_time'],
            reverse=True
        )
        
    
    print_history_items(sorted_searches)
    investigation_user_interaction(sorted_searches)

def add_search_engine_data(data):
    history = data
    search_engine_data = set([item["search_engine"] for item in data])
    data = {}
    data["search_engines"] = {search_engine: 0 for search_engine in list(search_engine_data)}
    data["search_query_history"] = history
    return data

def particular_investigation(data):
    """
    Allows the user to investigate a particular search engine's data.

    Parameters:
    - data: A dictionary containing data for a specific week or all searches.
    """
    if "search_engines" not in data:
        data = add_search_engine_data(data)
    fzf = FzfPrompt()
    search_engine_list = [engine for engine, _ in data["search_engines"]]
    selected_engine = fzf.prompt(
        search_engine_list, "--prompt='Select a search engine: '")[0]
    # Calculate the time range from the start date to the end date or current date
    start_date = data["start_date"]
    end_date = data.get("end_date", datetime.now().date())
    start_week = start_date.isocalendar()[1]
    start_year = start_date.isocalendar()[0]
    end_week = end_date.isocalendar()[1]
    end_year = end_date.isocalendar()[0]
    week_difference_start = (start_year - end_year) * 52 + (start_week - end_week)
    week_difference_end = (end_year - start_year) * 52 + (end_week - start_week)

    # Determine the appropriate time phrase based on the calculated time range
    if week_difference_start == 0 and week_difference_end == 0:
        time_phrase = "this week"
    elif week_difference_start == 1 and week_difference_end == 1:
        time_phrase = "last week"
    elif week_difference_start > 1 or week_difference_end > 1:
        time_phrase = f"from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    selected_engine_searches = [
        entry for entry in data["search_query_history"]
        if urlparse(entry["url"]).netloc.replace("www.", "") == selected_engine
    ]

    print(f"\nSearches made with {selected_engine} {time_phrase}:")
    print_history_items(selected_engine_searches)
    investigation_user_interaction(data, selected_engine_searches)


def dive_into_search_context(search: dict) -> None:
    """
    Allows the user to dive into the context of a search for a specific week.

    Parameters:
    - search: A dictionary containing data for a specific search.
    """
    url = search['url']
    history = load_cache()
    surrounding_history = get_surrounding_history(url, history, context_window=3)
    print("\nSurrounding History\n")
    print_history_items(surrounding_history, url=url)


def investigation_user_interaction(data, selected_engine_searches=None):
    """
    Handles user interaction during the investigation of a specific engine's searches.

    Parameters:
    - data: Data for a specific week or all searches.
    - selected_engine_searches: Searches related to the selected engine.
    """

    print()
    while True:
        user_choice = input("Investigation Menu:\n"
                            " - 'R' to Return to the main menu\n"
                            " - 'I' to Investigate an engine\n"
                            " - 'Q' to Quit\n"
                            " - Enter a query number for detailed data: ").lower()
        if user_choice == 'r':
            break
        elif user_choice == 'i':
            particular_investigation(data)
            break
        elif user_choice == 'e':
            export_searches(data)
            break
        elif user_choice == 'q':
            exit(0)
        else:
            try:
                query_number = int(user_choice)
                searches_to_use = data["search_query_history"] if selected_engine_searches is None else selected_engine_searches
                if 1 <= query_number <= len(searches_to_use):
                    search = searches_to_use[query_number - 1]
                    print(f"\nDetailed data for query {query_number}:")
                    for key, value in search.items():
                        print(f"{key}: {value}")
                surrounding_context = input("\nWould you like to see the "
                                            "surrounding context? (Y/N): ").lower()
                if surrounding_context == 'y':
                    dive_into_search_context(search)
                else:
                    print("Invalid query number. Please try again.")
            except ValueError:
                print("Invalid option. Please try again.")


def interact_with_user_for_search_data(history, week_num=None, hide_complements=True):
    """
    Engages the user to present search engine usage percentages for a given
    week or a span of weeks, initiating with the current week's data, and
    accommodates a variety of user choices for data interaction.
    """

    # Determine the total number of searches logged
    total_searches_logged = len([item for item in history if "search_query" in item and item["search_query"] is not None])
    # Determine the total number of weeks logged
    total_weeks_logged = set()
    for entry in history:
        if isinstance(entry["last_visit_time"], int):
            # Convert Chrometime to datetime
            dt = datetime(1601, 1, 1) + timedelta(microseconds=entry["last_visit_time"])
            entry["last_visit_time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Parse the datetime string
            dt = datetime.strptime(entry["last_visit_time"].split('.')[0], "%Y-%m-%d %H:%M:%S")
        total_weeks_logged.add(week_num)
    total_weeks_logged = len(total_weeks_logged)
    if week_num is None:
        current_week_num = 0
    else:
        current_week_num = week_num
    week_data = get_search_engine_percentages(history, week_num=current_week_num, hide_complements=hide_complements)
    print_search_engine_percentages(week_data)
    print(
        f"\nTotal weeks logged: {total_weeks_logged}. Currently showing this week.")


    context = None
    while True:
        menu_options = {
            'V': "show the current week's percentages",
            'A': f"for a list of All {total_searches_logged} searches",
            'W': f"for a list of the {week_data['total_searches']} search{'es' if week_data['total_searches'] != 1 else ''} for the Week",
            'P': f"for the Previous week ({current_week_num + 1})",
            'N': f"for the Next week ({current_week_num - 1})",
            'S': "to jump to a Specific week",
            'C': f"to {'exclude' if hide_complements else 'include'} hat-based search Complements",
            'I': "to Investigate this week",
            'E': "to Export",
            'Q': "to Quit"
        }
        if context is None:
            del menu_options['V']
        if context == "list_all":
            del menu_options['A']
        if current_week_num == 0:
            del menu_options['N']  # Remove option for previous week
        elif current_week_num == total_weeks_logged:
            print("This is the last week. No previous week.")
            del menu_options['P']  # Remove option for next week

        # Constructing the menu string from the options dictionary
        menu_string = "Menu:"
        for key, value in menu_options.items():
            menu_string += f"\n - '{key}' {value}"

        user_choice = input(menu_string+"\n").lower()
        if user_choice == 'n':
            current_week_num -= 1
            week_data = get_search_engine_percentages(
                history, week_num=current_week_num)
            print_search_engine_percentages(week_data)
            context = "next_week"
        elif user_choice == 'a':
            list_all_investigation(full_history=True)
            context = "list_all"
        elif user_choice == 'v':
            return interact_with_user_for_search_data(history, week_num=current_week_num, hide_complements=hide_complements)
        elif user_choice == 'c':
            return interact_with_user_for_search_data(history, week_num=current_week_num, hide_complements=not hide_complements)
        elif user_choice == 'w':
            list_all_investigation(week_data)
            context = "list_week"
        elif user_choice == 'p':
            current_week_num += 1
            week_data = get_search_engine_percentages(
                history, week_num=current_week_num)
            print_search_engine_percentages(week_data)
            context = "previous_week"
        elif user_choice == 's':
            week_num = int(input("Enter the number of weeks back to view: "))
            current_week_num = week_num
            week_data = get_search_engine_percentages(
                history, week_num=week_num)
            print_search_engine_percentages(week_data)
            context = "specific_week"
        elif user_choice == 'i':
            investigate_week(week_data)
            context = "investigate_week"
        elif user_choice == 'e':
            data_scope = input(
                "Export data for:\n1: This week\n2: All history\n: ").strip()
            if data_scope == "1":
                export_searches(week_data)
            elif data_scope == "2":
                export_searches(history)
            elif user_choice == 'q':
                break
            else:
                print("Invalid option. Please try again.")
            context = "export"
        elif user_choice == 'q':
            break
        else:
            print("Invalid option. Please try again.")
