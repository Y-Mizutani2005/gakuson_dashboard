import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta

# --- 定数 ---
BACKEND_URL = "http://127.0.0.1:8000/api/v1/active-users"
PAGE_VIEW_URL = "http://127.0.0.1:8000/api/v1/page-views"
TODAY = date.today()

# --- エラーダイアログ ---
@st.dialog("日付エラー")
def future_date_error():
    st.write("終了日が未来の日付です。本日以前を選択してください。")
    if st.button("OK"):
        st.rerun()

@st.dialog("期間エラー")
def invalid_period_error():
    st.write("期間の開始日は終了日より前に設定してください。")
    if st.button("OK"):
        st.rerun()

# --- データ取得 ---
def fetch_data(params1, params2, metric_mode):
    """APIからデータを取得し、DataFrameを返す"""
    url = BACKEND_URL if metric_mode == "アクティブユーザー" else PAGE_VIEW_URL
    
    resp1 = requests.get(url, params=params1)
    resp1.raise_for_status()
    data1 = resp1.json()

    resp2 = requests.get(url, params=params2)
    resp2.raise_for_status()
    data2 = resp2.json()

    df1 = pd.DataFrame(data1.get("data", []))
    df2 = pd.DataFrame(data2.get("data", []))

    for df in [df1, df2]:
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
    return data1, data2, df1, df2

# --- 表示ロジック ---
def display_active_users(data1, data2, df1, df2, start_date1, end_date1, start_date2, end_date2, time_unit):
    """アクティブユーザーの指標とチャートを表示"""
    config_map = {
        "週": {"label": "平均(7日)", "avg_key": "avg_active7DayUsers", "total_key": "total_active7DayUsers", "chart_col": "active7DayUsers", "diff_label": "7日ユーザー数"},
        "月": {"label": "平均(28日)", "avg_key": "avg_active28DayUsers", "total_key": "total_active28DayUsers", "chart_col": "active28DayUsers", "diff_label": "28日ユーザー数"}
    }
    config = config_map[time_unit]
    
    st.header(f"アクティブユーザー数{time_unit}比較")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"期間1: {start_date1} ～ {end_date1}")
        st.metric(config['label'], f"{data1['stats'][config['avg_key']]:,}")
        st.line_chart(df1[[config['chart_col']]])
    
    with col2:
        st.subheader(f"期間2: {start_date2} ～ {end_date2}")
        st.metric(config['label'], f"{data2['stats'][config['avg_key']]:,}")
        st.line_chart(df2[[config['chart_col']]])
    
    st.subheader(f"2{time_unit}期間の比較")
    total1, total2 = data1['stats'][config['total_key']], data2['stats'][config['total_key']]
    diff = total1 - total2
    ratio = (total1 / total2 * 100) if total2 else 0
    st.write(f"{config['diff_label']}差分: {diff:+,}　（期間1 - 期間2）")
    st.write(f"{config['diff_label']}比率: {ratio:.2f}%")

def display_page_views(df1, df2, start_date1, end_date1, start_date2, end_date2, time_unit):
    """ページビューの指標とチャートを表示"""
    st.header(f"表示回数{time_unit}比較")
    col1, col2 = st.columns(2)
    total1, total2 = df1['pageViews'].sum(), df2['pageViews'].sum()
    
    with col1:
        st.subheader(f"期間1: {start_date1} ～ {end_date1}")
        st.metric("合計表示回数", f"{total1:,}")
        st.line_chart(df1[["pageViews"]])
    
    with col2:
        st.subheader(f"期間2: {start_date2} ～ {end_date2}")
        st.metric("合計表示回数", f"{total2:,}")
        st.line_chart(df2[["pageViews"]])

    st.subheader(f"2{time_unit}期間の比較")
    diff = total1 - total2
    ratio = (total1 / total2 * 100) if total2 else 0
    st.write(f"表示回数差分: {diff:+,}　（期間1 - 期間2）")
    st.write(f"表示回数比率: {ratio:.2f}%")

# --- メイン処理 ---
def main():
    st.set_page_config(page_title="がくそんダッシュボード", layout="wide")
    st.title("がくそんダッシュボード")

    st.sidebar.header("比較する2つの期間を選択")
    input_mode = st.sidebar.selectbox("集計単位", ["週", "月"], key="input_mode")
    metric_mode = st.sidebar.radio("表示指標", ["アクティブユーザー", "表示回数"], key="metric_mode")

    # --- 日付選択 ---
    st.sidebar.subheader(f"{input_mode}単位の比較対象日を選択")
    date_label = "基準日から1週間" if input_mode == "週" else "基準日から1ヶ月"
    
    default1_end = TODAY - timedelta(days=1)
    default2_end = default1_end - timedelta(days=7 if input_mode == "週" else 28)

    selected_date1 = st.sidebar.date_input(f"期間1の基準日（{date_label}）", value=default1_end, key=f"{input_mode}_date1")
    selected_date2 = st.sidebar.date_input(f"期間2の基準日（{date_label}）", value=default2_end, key=f"{input_mode}_date2")

    # --- 期間計算 ---
    if input_mode == "週":
        start_date1, end_date1 = selected_date1, selected_date1 + timedelta(days=6)
        start_date2, end_date2 = selected_date2, selected_date2 + timedelta(days=6)
    else:  # 月
        start_date1, end_date1 = selected_date1, selected_date1 + timedelta(days=27)
        start_date2, end_date2 = selected_date2, selected_date2 + timedelta(days=27)

    if st.sidebar.button(f"{input_mode}データ表示", key=f"{input_mode}_button"):
        if start_date1 > end_date1 or start_date2 > end_date2:
            invalid_period_error()
        elif end_date1 > TODAY or end_date2 > TODAY:
            future_date_error()
        else:
            with st.spinner(f'{input_mode}データを取得しています...'):
                try:
                    params1 = {'start_date': start_date1.strftime('%Y-%m-%d'), 'end_date': end_date1.strftime('%Y-%m-%d')}
                    params2 = {'start_date': start_date2.strftime('%Y-%m-%d'), 'end_date': end_date2.strftime('%Y-%m-%d')}
                    
                    data1, data2, df1, df2 = fetch_data(params1, params2, metric_mode)

                    if df1.empty or df2.empty:
                        st.warning(f"いずれかの{input_mode}期間でデータが見つかりませんでした。")
                    else:
                        if metric_mode == "アクティブユーザー":
                            display_active_users(data1, data2, df1, df2, start_date1, end_date1, start_date2, end_date2, input_mode)
                        elif metric_mode == "表示回数":
                            display_page_views(df1, df2, start_date1, end_date1, start_date2, end_date2, input_mode)
                
                except requests.exceptions.RequestException as e:
                    st.error(f"バックエンドへの接続に失敗しました: {e}")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
