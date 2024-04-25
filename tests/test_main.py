import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from unittest.mock import patch
from app import get_data_path

def test_initial_activity_does_not_crash():
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
        # Test with --browser option
        mock_parse_args.return_value = argparse.Namespace(
            browser='Chrome',
            htu=False,
            random=False,
            date=None,
            test=False,
            fzf=False
        )

        process_history = MagicMock()
        with patch('app.process_history', process_history):
            process_history(mock_parse_args.return_value.browser, get_data_path(mock_parse_args.return_value.browser))
            process_history.assert_called_once_with('Chrome', '/Users/dsg/Library/Application Support/Google/Chrome/Default')

        # Test with --htu option
        mock_parse_args.return_value = argparse.Namespace(
            browser=None,
            htu=True,
            random=False,
            date=None,
            test=False,
            fzf=False
        )

        process_history = MagicMock()
        with patch('app.process_history', process_history):
            process_history(mock_parse_args.return_value.htu, get_data_path('HTU sync'))
            process_history.assert_called_once_with(True, 'htu_sync')

        # Test with --test option
        mock_parse_args.return_value = argparse.Namespace(
            browser=None,
            htu=False,
            random=False,
            date=None,
            test=True,
            fzf=False
        )

        process_test_history = MagicMock()
        with patch('app.process_test_history', process_test_history):
            process_test_history()
            process_test_history.assert_called_once()

        # Test with --random option
        mock_parse_args.return_value = argparse.Namespace(
            browser='Brave',
            htu=False,
            random=True,
            date=None,
            test=True,
            fzf=False
        )