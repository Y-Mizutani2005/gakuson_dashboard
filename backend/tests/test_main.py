
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import sys

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set environment variables for tests
os.environ['GA_PROPERTY_ID'] = 'test_property_id'
os.environ['SERVICE_ACCOUNT_FILE'] = 'test_service_account.json'

from main import app

client = TestClient(app)

@pytest.fixture
def mock_google_analytics_client():
    with patch('main.BetaAnalyticsDataClient') as mock_client:
        yield mock_client

@patch('google.oauth2.service_account.Credentials.from_service_account_file')
@patch('os.path.exists')
def test_get_active_users_success(mock_path_exists, mock_from_service_account_file, mock_google_analytics_client):
    mock_path_exists.return_value = True
    mock_from_service_account_file.return_value = MagicMock()
    mock_instance = mock_google_analytics_client.return_value
    mock_response = MagicMock()
    mock_response.row_count = 2
    mock_response.rows = [
        MagicMock(dimension_values=[MagicMock(value='20250601')], metric_values=[MagicMock(value='150')]),
        MagicMock(dimension_values=[MagicMock(value='20250602')], metric_values=[MagicMock(value='165')]),
    ]
    mock_instance.run_report.return_value = mock_response

    response = client.get("/api/v1/active-users?start_date=2025-06-01&end_date=2025-06-02")

    assert response.status_code == 200
    data = response.json()
    assert data['start_date'] == '2025-06-01'
    assert data['end_date'] == '2025-06-02'
    assert len(data['data']) == 2
    assert data['data'][0]['date'] == '2025-06-01'
    assert data['data'][0]['active_users'] == 150

def test_get_active_users_invalid_dates():
    response = client.get("/api/v1/active-users?start_date=2025-06-02&end_date=2025-06-01")
    assert response.status_code == 400
    assert "start_date must be before end_date" in response.json()['detail']

@patch('google.oauth2.service_account.Credentials.from_service_account_file')
@patch('os.path.exists')
def test_get_active_users_ga_api_error(mock_path_exists, mock_from_service_account_file, mock_google_analytics_client):
    mock_path_exists.return_value = True
    mock_from_service_account_file.return_value = MagicMock()
    mock_instance = mock_google_analytics_client.return_value
    mock_instance.run_report.side_effect = Exception("GA API Error")

    response = client.get("/api/v1/active-users?start_date=2025-06-01&end_date=2025-06-02")
    assert response.status_code == 500
    assert "Error fetching data from Google Analytics: GA API Error" in response.json()['detail']
