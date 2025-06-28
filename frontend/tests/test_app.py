import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import date, timedelta
from streamlit.testing.v1 import AppTest
import requests

# app.pyのパスを通す
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BACKEND_URL = "http://127.0.0.1:8000/api/v1/active-users"

@pytest.fixture
def mock_requests_get():
    with patch("app.requests.get") as mock_get:
        yield mock_get

def make_api_response(data=None, stats=None):
    return {
        "data": data if data is not None else [
            {"date": "2025-06-01", "active7DayUsers": 100, "active28DayUsers": 200},
            {"date": "2025-06-02", "active7DayUsers": 110, "active28DayUsers": 210},
        ],
        "stats": stats if stats is not None else {
            "total_active7DayUsers": 210,
            "avg_active7DayUsers": 105,
            "total_active28DayUsers": 410,
            "avg_active28DayUsers": 205,
        }
    }

def test_initial_ui_state():
    """初期状態で日付入力とボタンが表示され、他のUI要素は表示されない"""
    at = AppTest.from_file("../app.py").run()
    # サイドバー日付入力4つ
    assert len(at.date_input) == 4
    # ボタン
    assert len(at.button) == 1
    # 初期状態ではメトリクスやグラフ等は表示されない
    assert not at.get("metric")
    assert not at.get("line_chart")
    assert not at.get("error")

def test_date_validation_error():
    """開始日が終了日より後の場合、エラーが表示される"""
    at = AppTest.from_file("../app.py").run()
    # 期間1の開始日を終了日より後に設定
    at.date_input[0].set_value(date(2025, 6, 10)).run()
    at.date_input[1].set_value(date(2025, 6, 5)).run()
    at.button[0].click().run()
    # エラー表示
    errors = at.get("error")
    assert errors
    assert "開始日は終了日より前" in errors[0].value

def test_api_success_and_ui_display(mock_requests_get):
    """API正常応答時、全UI要素が正しく表示される"""
    # 2期間分のAPIレスポンスを用意
    mock_response1 = MagicMock()
    mock_response1.status_code = 200
    mock_response1.json.return_value = make_api_response()
    mock_response1.raise_for_status.return_value = None

    mock_response2 = MagicMock()
    mock_response2.status_code = 200
    mock_response2.json.return_value = make_api_response()
    mock_response2.raise_for_status.return_value = None

    mock_requests_get.side_effect = [mock_response1, mock_response2]

    at = AppTest.from_file("../app.py").run()
    at.button[0].click().run()

    # APIが2回呼ばれる
    assert mock_requests_get.call_count == 2

    # メトリクス（合計・平均×2期間×2種）
    metrics = at.get("metric")
    assert metrics and len(metrics) >= 8
    # グラフ
    charts = at.get("line_chart")
    assert charts and len(charts) == 2
    # 差分・比率
    assert any("ユーザー数差分" in w.value for w in at.get("text") + at.get("markdown"))
    assert any("ユーザー数比率" in w.value for w in at.get("text") + at.get("markdown"))
    # データテーブル
    assert any("期間1データ" in w.value for w in at.get("expander"))
    assert any("期間2データ" in w.value for w in at.get("expander"))
    # エラーなし
    assert not at.get("error")

def test_api_returns_empty_data(mock_requests_get):
    """APIが空データを返した場合、警告が表示される"""
    mock_response1 = MagicMock()
    mock_response1.status_code = 200
    mock_response1.json.return_value = {"data": [], "stats": {}}
    mock_response1.raise_for_status.return_value = None

    mock_response2 = MagicMock()
    mock_response2.status_code = 200
    mock_response2.json.return_value = {"data": [], "stats": {}}
    mock_response2.raise_for_status.return_value = None

    mock_requests_get.side_effect = [mock_response1, mock_response2]

    at = AppTest.from_file("../app.py").run()
    at.button[0].click().run()
    # 警告表示
    warnings = at.get("warning")
    assert warnings
    assert "データが見つかりません" in warnings[0].value

def test_api_request_exception(mock_requests_get):
    """API通信エラー時、エラーが表示される"""
    mock_requests_get.side_effect = requests.exceptions.RequestException("API接続失敗")
    at = AppTest.from_file("../app.py").run()
    at.button[0].click().run()
    errors = at.get("error")
    assert errors
    assert "バックエンドへの接続に失敗" in errors[0].value

def test_unexpected_exception(mock_requests_get):
    """予期しない例外発生時、エラーが表示される"""
    mock_requests_get.side_effect = Exception("予期しない例外")
    at = AppTest.from_file("../app.py").run()
    at.button[0].click().run()
    errors = at.get("error")
    assert errors
    assert "エラーが発生しました" in errors[0].value