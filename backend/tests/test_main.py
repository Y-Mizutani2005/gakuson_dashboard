import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import backend.main as main

client = TestClient(main.app)

# 正常系: 正しいリクエストでのレスポンス
@patch("backend.main.get_ga_client")
@patch("backend.main.fetch_ga_metrics")
@patch("backend.main.GA_PROPERTY_ID", "test-property-id")
def test_get_active_users_success(mock_fetch, mock_client):
    mock_fetch.return_value = [
        {"date": "2024-06-01", "active7DayUsers": 10, "active28DayUsers": 20},
        {"date": "2024-06-02", "active7DayUsers": 30, "active28DayUsers": 40},
    ]
    response = client.get(
        "/api/v1/active-users?start_date=2024-06-01&end_date=2024-06-02"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["start_date"] == "2024-06-01"
    assert body["end_date"] == "2024-06-02"
    assert body["property_id"] == "test-property-id"
    assert len(body["data"]) == 2
    assert body["data"][0]["date"] == "2024-06-01"
    assert body["data"][0]["active7DayUsers"] == 10
    assert body["data"][0]["active28DayUsers"] == 20
    assert body["stats"]["total_active7DayUsers"] == 40
    assert body["stats"]["total_active28DayUsers"] == 60
    assert body["stats"]["avg_active7DayUsers"] == 20.0
    assert body["stats"]["avg_active28DayUsers"] == 30.0

# 異常系: 日付フォーマット不正
@patch("backend.main.GA_PROPERTY_ID", "test-property-id")
def test_get_active_users_invalid_date_format():
    response = client.get(
        "/api/v1/active-users?start_date=20240601&end_date=2024-06-02"
    )
    assert response.status_code == 422  # FastAPIのQueryバリデーション

# 異常系: start_date > end_date
@patch("backend.main.GA_PROPERTY_ID", "test-property-id")
def test_get_active_users_start_after_end():
    response = client.get(
        "/api/v1/active-users?start_date=2024-06-03&end_date=2024-06-02"
    )
    assert response.status_code == 400
    assert "start_date must be before end_date" in response.text

# 異常系: GA_PROPERTY_ID未設定
@patch("backend.main.GA_PROPERTY_ID", None)
def test_get_active_users_no_property_id():
    response = client.get(
        "/api/v1/active-users?start_date=2024-06-01&end_date=2024-06-02"
    )
    assert response.status_code == 500
    assert "GA_PROPERTY_IDが設定されていません" in response.text

# 異常系: サービスアカウントファイル未設定
@patch("backend.main.GA_PROPERTY_ID", "test-property-id")
@patch("backend.main.SERVICE_ACCOUNT_FILE", None)
def test_get_active_users_no_service_account_file():
    with patch("backend.main.get_ga_client", side_effect=ValueError("SERVICE_ACCOUNT_FILE環境変数が設定されていません。")):
        response = client.get(
            "/api/v1/active-users?start_date=2024-06-01&end_date=2024-06-02"
        )
        assert response.status_code == 500
        assert "SERVICE_ACCOUNT_FILE環境変数が設定されていません" in response.text

# 異常系: サービスアカウントファイルが存在しない
@patch("backend.main.GA_PROPERTY_ID", "test-property-id")
@patch("backend.main.SERVICE_ACCOUNT_FILE", "dummy.json")
def test_get_active_users_service_account_file_not_found():
    with patch("backend.main.get_ga_client", side_effect=FileNotFoundError("サービスアカウントキーファイルが見つかりません: dummy.json")):
        response = client.get(
            "/api/v1/active-users?start_date=2024-06-01&end_date=2024-06-02"
        )
        assert response.status_code == 500
        assert "サービスアカウントキーファイルが見つかりません" in response.text

# 異常系: Google Analytics APIエラー
@patch("backend.main.GA_PROPERTY_ID", "test-property-id")
def test_get_active_users_ga_api_error():
    with patch("backend.main.get_ga_client") as mock_client:
        mock_client.return_value = MagicMock()
        with patch("backend.main.fetch_ga_metrics", side_effect=Exception("API error")):
            response = client.get(
                "/api/v1/active-users?start_date=2024-06-01&end_date=2024-06-02"
            )
            assert response.status_code == 500
            assert "Error fetching data from Google Analytics" in response.text
