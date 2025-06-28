import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta

# バックエンドAPIのURL
BACKEND_URL = "http://127.0.0.1:8000/api/v1/active-users"

# StreamlitアプリのUI設定
st.set_page_config(page_title="GA4 アクティブユーザー数ダッシュボード", layout="wide")

st.title("GA4 アクティブユーザー数ダッシュボード")

# 期間指定UI
st.sidebar.header("期間を選択")

# デフォルトの日付を設定（昨日から遡って8日間）
today = date.today()
end_date_default = today - timedelta(days=1)
start_date_default = end_date_default - timedelta(days=7)

start_date = st.sidebar.date_input("開始日", start_date_default)
end_date = st.sidebar.date_input("終了日", end_date_default)

if st.sidebar.button("表示"):
    if start_date > end_date:
        st.error("エラー: 開始日は終了日より前に設定してください。")
    else:
        with st.spinner('データを取得しています...'):
            try:
                # バックエンドAPIにリクエストを送信
                params = {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
                response = requests.get(BACKEND_URL, params=params)
                response.raise_for_status()  # HTTPエラーがあれば例外を発生させる

                api_response = response.json()
                data = api_response.get("data", [])

                if data:
                    df = pd.DataFrame(data)
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)

                    # 合計と平均を計算
                    total_users = df['active_users'].sum()
                    avg_users = df['active_users'].mean()

                    st.header(f"{start_date} から {end_date} のアクティブユーザー数")

                    # メトリクスを表示
                    col1, col2 = st.columns(2)
                    col1.metric("合計アクティブユーザー数", f"{total_users:,}")
                    col2.metric("平均アクティブユーザー数", f"{avg_users:,.2f}")

                    # 折れ線グラフを表示
                    st.line_chart(df['active_users'])
                    
                    # 生データを表示（任意）
                    with st.expander("生データを表示"):
                        st.dataframe(df)

                else:
                    st.warning("指定された期間のデータが見つかりませんでした。")

            except requests.exceptions.RequestException as e:
                st.error(f"バックエンドへの接続に失敗しました: {e}")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")