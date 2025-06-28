
import os
from fastapi import FastAPI, HTTPException, Query
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from google.oauth2 import service_account
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime

# 環境変数を読み込む
load_dotenv()

# 環境変数から設定を読み込む
GA_PROPERTY_ID = os.getenv("GA_PROPERTY_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

# FastAPIアプリケーションの初期化
app = FastAPI()

# Google Analyticsクライアントの初期化
def get_ga_client():
    """Google Analytics Data APIクライアントを初期化して返します。"""
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("SERVICE_ACCOUNT_FILE環境変数が設定されていません。")
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"サービスアカウントキーファイルが見つかりません: {SERVICE_ACCOUNT_FILE}")
    
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    return BetaAnalyticsDataClient(credentials=credentials)

# レスポンスモデルの定義
class ActiveUsersData(BaseModel):
    date: str
    active7DayUsers: int
    active28DayUsers: int

class ActiveUsersStats(BaseModel):
    total_active7DayUsers: int
    total_active28DayUsers: int
    avg_active7DayUsers: float
    avg_active28DayUsers: float

class ActiveUsersResponse(BaseModel):
    start_date: str
    end_date: str
    property_id: str
    data: list[ActiveUsersData]
    stats: ActiveUsersStats

def fetch_ga_metrics(
    client,
    property_id: str,
    start_date: str,
    end_date: str,
    metrics: list[str]
):
    """指定した指標のデータを日別で取得（将来の拡張も考慮）"""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )
    response = client.run_report(request)
    results = []
    for row in response.rows:
        row_data = {"date": datetime.strptime(row.dimension_values[0].value, "%Y%m%d").strftime("%Y-%m-%d")}
        for idx, m in enumerate(metrics):
            row_data[m] = int(row.metric_values[idx].value)
        results.append(row_data)
    results.sort(key=lambda x: x["date"])
    return results

@app.get("/api/v1/active-users", response_model=ActiveUsersResponse)
def get_active_users(
    start_date: str = Query(..., description="開始日 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., description="終了日 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
):
    """
    指定された期間の日別active7DayUsers/active28DayUsersをGoogle Analytics Data APIから取得します。
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="日付のフォーマットが不正です。YYYY-MM-DD形式で指定してください。")

    if start_dt > end_dt:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    if not GA_PROPERTY_ID:
        raise HTTPException(status_code=500, detail="GA_PROPERTY_IDが設定されていません。")

    try:
        client = get_ga_client()
        metrics = ["active7DayUsers", "active28DayUsers"]
        rows = fetch_ga_metrics(client, GA_PROPERTY_ID, start_date, end_date, metrics)

        data = []
        total_7 = 0
        total_28 = 0
        for row in rows:
            d = ActiveUsersData(
                date=row["date"],
                active7DayUsers=row.get("active7DayUsers", 0),
                active28DayUsers=row.get("active28DayUsers", 0)
            )
            data.append(d)
            total_7 += d.active7DayUsers
            total_28 += d.active28DayUsers

        count = len(data)
        stats = ActiveUsersStats(
            total_active7DayUsers=total_7,
            total_active28DayUsers=total_28,
            avg_active7DayUsers=round(total_7 / count, 2) if count else 0,
            avg_active28DayUsers=round(total_28 / count, 2) if count else 0
        )

        return ActiveUsersResponse(
            start_date=start_date,
            end_date=end_date,
            property_id=GA_PROPERTY_ID,
            data=data,
            stats=stats
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Google Analytics: {e}")

