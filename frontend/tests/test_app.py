import pytest
from unittest.mock import patch, MagicMock
import os
import sys
from streamlit.testing.v1 import AppTest
import requests

# Add the parent directory to the path to allow imports so `app` can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_requests_get():
    # Patch requests.get in the context of the app module
    with patch('app.requests.get') as mock_get:
        yield mock_get

def test_app_initial_state():
    """Test the initial state of the app before any interaction."""
    at = AppTest.from_file("../app.py", default_timeout=30).run()

    # Check that initial widgets are present
    assert len(at.date_input) == 2
    assert len(at.button) == 1

    # On initial run, no data is loaded, so these elements should not exist
    assert not at.get("line_chart")
    assert not at.get("metric")
    assert not at.get("error")

def test_app_success(mock_requests_get):
    """Test the app's behavior on a successful API call."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"date": "2025-06-01", "active_users": 150},
            {"date": "2025-06-02", "active_users": 165},
        ]
    }
    # On success, raise_for_status() should do nothing
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    at = AppTest.from_file("../app.py", default_timeout=30).run()
    at.button[0].click().run()

    # Verify that the API was called
    mock_requests_get.assert_called_once()
    
    # Verify that the chart and metrics are displayed
    assert len(at.get("line_chart")) == 1
    assert len(at.get("metric")) == 2  # Total and Average

    # Verify the metric values (st.metric renders values as strings)
    assert at.get("metric")[0].value == "315"
    assert at.get("metric")[1].value == "157.50"

    # No error message should be shown
    assert not at.get("error")

def test_app_api_error(mock_requests_get):
    """Test the app's behavior when the API call fails."""
    # Configure the mock to raise a RequestException when called
    mock_requests_get.side_effect = requests.exceptions.RequestException("API connection failed")

    at = AppTest.from_file("../app.py", default_timeout=30).run()
    at.button[0].click().run()

    # Verify an error message is shown
    assert len(at.get("error")) == 1
    assert "API connection failed" in at.get("error")[0].value

    # Verify that no data elements are displayed
    assert not at.get("line_chart")
    assert not at.get("metric")