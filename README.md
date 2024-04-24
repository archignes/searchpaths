# Searchpaths

Searchpaths is a Python program that analyzes your browser history to provide insights into your search engine usage. It retrieves data from your Chromium-based browser (e.g., Chrome, Brave) and presents interactive statistics on your search patterns.

This is very much a work in progress. Status: beta

## Features

- Retrieves search history from Chromium-based browsers
- Calculates the percentage of searches done on different search engines
- Provides a weekly breakdown of search engine usage
- Allows investigation of specific search queries and their surrounding context
- Supports exporting search data to CSV or TXT formats
- Includes a minimal testing suite for basic functionality
- Private and local, no data is sent to anyone

## Limitations

1. **Configuration Required**: The path to the Chromium history database must be manually set in the `config.py` file for the tool to function properly.

2. **Limited History**: Chromium browsers typically only retain the last 3 months of browsing history. Searches performed beyond this period will not be included in the analysis.

3. **Desktop Searches Only**: Currently, Searchpaths only analyzes searches conducted on desktop browsers. Mobile browser searches are not included unless they are synced with the desktop history.

4. **App-Based Searches**: Searches performed within mobile apps or other non-browser applications are not captured by Searchpaths.

5. **Non-URL-Based Searches**: Searchpaths counts searches that are not explicitly indicated by query parameters in the URL. These searches are labeled as "**not-url-based**" in the output.

6. **Configurable Complements**: Certain search systems, referred to as "Complements" and configured in `config.py`, are optionally included in the analysis. To include them, press 'c' at the main menu. Queries for these systems are marked as "**chat-based-search-complement**" in the output.

7. **URL Pattern Handling**: Searchpaths employs various techniques to handle unusual URL patterns and redirects. However, some edge cases may not be perfectly addressed, potentially leading to inconsistencies and gaps in the data and subsequent analysis.

8. **Issue Investigation**: To investigate specific issues or anomalies in the search data, users can load the details of a query and view it in the context of the surrounding searches (following the interactive menu). 

## Query Labels

- **not-url-based**: no query available via query parameters in the URL.
- **chat-based-search-complement**: a search associated with a chat-based search system (configured in `config.py`)
- **duplicate**: a search query that is a duplicate of a previous search query but appears as unique history items logged within 1-second.
- **redirect**: a search is associated with a redirect of some sort, a type of duplicate where the URL is distinct but the system is the same and logged within 1-second of each other. In this case the second URL is shown as the search, the first is labeled as a redirect.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/searchpaths.git
   ```

2. Navigate to the project directory:
   ```
   cd searchpaths
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Update the `config.py` file with the path to your browser's history database.

## Usage

To run Searchpaths, use the following command:

```
python main.py -b <browser_name>
```

Replace `<browser_name>` with the name of your Chromium-based browser (e.g., `Chrome`, `Brave`).


The script will retrieve your search history and present an interactive menu where you can:
- View search engine usage percentages for the current week
- Investigate specific search queries and their surrounding context
- Jump to previous or next weeks
- Export search data to CSV or TXT formats

### Additional command line options

- run with a toy dataset with `python main.py -t`
- load a random query from your history with `python main.py -b {browser name} -r`
   - will show the query within the context of other history items (`dive_into_search_context`)
- reload context of a query via the datetime
   - `python main.py -b {browser name} -d "{datetime}"`
   - datetime must be in YYYY-MM-DD HH:MM:SS format, in quotes
   - uses `dive_into_search_context`
- fuzzy search for a query string (and then an instance of it if multiple)
   - `python main.py -b {browser name} -f`
   - lets you fuzzily search for a query and then show the context of that query (`dive_into_search_context`)


## Configuration

The `config.py` file contains various configuration options:

- `HISTORY_DATABASE_PATHS`: Specify the paths to your browser's history database.
- `SKIP_DOMAINS`: List of domains to exclude from the search history analysis.
- `SITE_SEARCH_DOMAINS`: List of domains to consider as site-specific searches.
- `LOGGABLE_SEARCH_SYSTEMS`: List of search systems that may not have query strings in the URL.
- `CHAT_BASED_SEARCH_COMPLEMENTS`: List of chat-based search complements.

## Testing

Searchpaths includes a minimal testing suite to ensure the correctness of basic functionality. 

To run the tests, use the following command:

```
pytest tests/
```


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## Acknowledgments

Very early versions of this code was written during Daniel's dissertation research as a tool for self-reflection.

This latest push is motivated by online discourse about how much of searching people are shifting from Google to alternative search systems.






