import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta

# バックエンドAPIのURL
BACKEND_URL = "http://127.0.0.1:8000/api/v1/active-users"

PAGE_VIEW_URL = "http://127.0.0.1:8000/api/v1/page-views"

st.set_page_config(page_title="がくそんダッシュボード", layout="wide")
st.title("がくそんダッシュボード")

st.sidebar.header("比較する2つの期間を選択")

today = date.today()
# デフォルト値
default1_end = today - timedelta(days=1)
default1_start = default1_end - timedelta(days=6)
default2_end = default1_start - timedelta(days=1)
default2_start = default2_end - timedelta(days=6)

# 週/月切替
input_mode = st.sidebar.selectbox("集計単位", ["週", "月"], key="input_mode")

# 指標切替（表示回数 or アクティブユーザー）
metric_mode = st.sidebar.radio("表示指標", ["アクティブユーザー", "表示回数"], key="metric_mode")

def week_ui_and_logic():
    st.sidebar.subheader("週単位の比較対象日を選択")
    week_selected_date1 = st.sidebar.date_input("期間1の基準日（基準日から1週間）", value=default1_end, key="week_date1_only")
    week_selected_date2 = st.sidebar.date_input("期間2の基準日（基準日から1週間）", value=default2_end, key="week_date2_only")

    def week_period(selected_date):
        start_date = selected_date
        end_date = selected_date + timedelta(days=6)
        return start_date, end_date

    week_start_date1, week_end_date1 = week_period(week_selected_date1)
    week_start_date2, week_end_date2 = week_period(week_selected_date2)

    if st.sidebar.button("週データ表示", key="week_button_only"):
        if week_end_date1 > today or week_end_date2 > today:
            st.error("エラー: 終了日が未来の日付です。本日以前を選択してください。")
        else:
            with st.spinner('週データを取得しています...'):
                try:
                    params1 = {
                        'start_date': week_start_date1.strftime('%Y-%m-%d'),
                        'end_date': week_end_date1.strftime('%Y-%m-%d')
                    }
                    params2 = {
                        'start_date': week_start_date2.strftime('%Y-%m-%d'),
                        'end_date': week_end_date2.strftime('%Y-%m-%d')
                    }

                    if metric_mode == "アクティブユーザー":
                        resp1 = requests.get(BACKEND_URL, params=params1)
                        resp1.raise_for_status()
                        data1 = resp1.json()

                        resp2 = requests.get(BACKEND_URL, params=params2)
                        resp2.raise_for_status()
                        data2 = resp2.json()

                        week_df1 = pd.DataFrame(data1.get("data", []))
                        week_df2 = pd.DataFrame(data2.get("data", []))

                        if week_df1.empty or week_df2.empty:
                            st.warning("いずれかの週期間でデータが見つかりませんでした。")
                        else:
                            for df in [week_df1, week_df2]:
                                df['date'] = pd.to_datetime(df['date'])
                                df.set_index('date', inplace=True)

                            st.header("アクティブユーザー数週比較")

                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader(f"期間1: {week_start_date1} ～ {week_end_date1}")
                                st.metric("平均(7日)", f"{data1['stats']['avg_active7DayUsers']:,}")
                                st.line_chart(week_df1[["active7DayUsers"]])

                            with col2:
                                st.subheader(f"期間2: {week_start_date2} ～ {week_end_date2}")
                                st.metric("平均(7日)", f"{data2['stats']['avg_active7DayUsers']:,}")
                                st.line_chart(week_df2[["active7DayUsers"]])

                            st.subheader("2週期間の比較")
                            diff_7 = data1['stats']['total_active7DayUsers'] - data2['stats']['total_active7DayUsers']
                            ratio_7 = (data1['stats']['total_active7DayUsers'] / data2['stats']['total_active7DayUsers'] * 100) if data2['stats']['total_active7DayUsers'] else 0

                            st.write(f"7日ユーザー数差分: {diff_7:+,}　（期間1 - 期間2）")
                            st.write(f"7日ユーザー数比率: {ratio_7:.2f}%")

                    elif metric_mode == "表示回数":
                        resp1 = requests.get(PAGE_VIEW_URL, params=params1)
                        resp1.raise_for_status()
                        data1 = resp1.json()

                        resp2 = requests.get(PAGE_VIEW_URL, params=params2)
                        resp2.raise_for_status()
                        data2 = resp2.json()

                        week_df1 = pd.DataFrame(data1.get("data", []))
                        week_df2 = pd.DataFrame(data2.get("data", []))

                        if week_df1.empty or week_df2.empty:
                            st.warning("いずれかの週期間でデータが見つかりませんでした。")
                        else:
                            for df in [week_df1, week_df2]:
                                df['date'] = pd.to_datetime(df['date'])
                                df.set_index('date', inplace=True)

                            st.header("表示回数週比較")

                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader(f"期間1: {week_start_date1} ～ {week_end_date1}")
                                st.metric("合計表示回数", f"{week_df1['pageViews'].sum():,}")
                                st.line_chart(week_df1[["pageViews"]])

                            with col2:
                                st.subheader(f"期間2: {week_start_date2} ～ {week_end_date2}")
                                st.metric("合計表示回数", f"{week_df2['pageViews'].sum():,}")
                                st.line_chart(week_df2[["pageViews"]])

                            st.subheader("2週期間の比較")
                            diff_views = week_df1['pageViews'].sum() - week_df2['pageViews'].sum()
                            ratio_views = (week_df1['pageViews'].sum() / week_df2['pageViews'].sum() * 100) if week_df2['pageViews'].sum() else 0

                            st.write(f"表示回数差分: {diff_views:+,}　（期間1 - 期間2）")
                            st.write(f"表示回数比率: {ratio_views:.2f}%")

                except requests.exceptions.RequestException as e:
                    st.error(f"バックエンドへの接続に失敗しました: {e}")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

def month_ui_and_logic():
    st.sidebar.subheader("月単位の比較対象日を選択")
    month_selected_date1 = st.sidebar.date_input("期間1の基準日（基準日から1ヶ月）", value=default1_end, key="month_date1_only")
    month_selected_date2 = st.sidebar.date_input("期間2の基準日（基準日から1ヶ月）", value=default2_end, key="month_date2_only")

    def month_period(selected_date):
        start_date = selected_date - timedelta(days=27)
        end_date = selected_date
        return start_date, end_date

    month_start_date1, month_end_date1 = month_period(month_selected_date1)
    month_start_date2, month_end_date2 = month_period(month_selected_date2)

    if st.sidebar.button("月データ表示", key="month_button_only"):
        if month_end_date1 > today or month_end_date2 > today:
            st.error("エラー: 終了日が未来の日付です。本日以前を選択してください。")
        else:
            with st.spinner('月データを取得しています...'):
                try:
                    params1 = {
                        'start_date': month_start_date1.strftime('%Y-%m-%d'),
                        'end_date': month_end_date1.strftime('%Y-%m-%d')
                    }
                    params2 = {
                        'start_date': month_start_date2.strftime('%Y-%m-%d'),
                        'end_date': month_end_date2.strftime('%Y-%m-%d')
                    }

                    if metric_mode == "アクティブユーザー":
                        resp1 = requests.get(BACKEND_URL, params=params1)
                        resp1.raise_for_status()
                        data1 = resp1.json()

                        resp2 = requests.get(BACKEND_URL, params=params2)
                        resp2.raise_for_status()
                        data2 = resp2.json()

                        month_df1 = pd.DataFrame(data1.get("data", []))
                        month_df2 = pd.DataFrame(data2.get("data", []))

                        if month_df1.empty or month_df2.empty:
                            st.warning("いずれかの月期間でデータが見つかりませんでした。")
                        else:
                            for df in [month_df1, month_df2]:
                                df['date'] = pd.to_datetime(df['date'])
                                df.set_index('date', inplace=True)

                            st.header("アクティブユーザー数月間比較")

                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader(f"期間1: {month_start_date1} ～ {month_end_date1}")
                                st.metric("平均(28日)", f"{data1['stats']['avg_active28DayUsers']:,}")
                                st.line_chart(month_df1[["active28DayUsers"]])

                            with col2:
                                st.subheader(f"期間2: {month_start_date2} ～ {month_end_date2}")
                                st.metric("平均(28日)", f"{data2['stats']['avg_active28DayUsers']:,}")
                                st.line_chart(month_df2[[ "active28DayUsers"]])

                            st.subheader("2月期間の比較")
                            diff_28 = data1['stats']['total_active28DayUsers'] - data2['stats']['total_active28DayUsers']
                            ratio_28 = (data1['stats']['total_active28DayUsers'] / data2['stats']['total_active28DayUsers'] * 100) if data2['stats']['total_active28DayUsers'] else 0

                            st.write(f"28日ユーザー数差分: {diff_28:+,}　（期間1 - 期間2）")
                            st.write(f"28日ユーザー数比率: {ratio_28:.2f}%")

                    elif metric_mode == "表示回数":
                        resp1 = requests.get(PAGE_VIEW_URL, params=params1)
                        resp1.raise_for_status()
                        data1 = resp1.json()

                        resp2 = requests.get(PAGE_VIEW_URL, params=params2)
                        resp2.raise_for_status()
                        data2 = resp2.json()

                        month_df1 = pd.DataFrame(data1.get("data", []))
                        month_df2 = pd.DataFrame(data2.get("data", []))

                        if month_df1.empty or month_df2.empty:
                            st.warning("いずれかの月期間でデータが見つかりませんでした。")
                        else:
                            for df in [month_df1, month_df2]:
                                df['date'] = pd.to_datetime(df['date'])
                                df.set_index('date', inplace=True)

                            st.header("表示回数月間比較")

                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader(f"期間1: {month_start_date1} ～ {month_end_date1}")
                                st.metric("合計表示回数", f"{month_df1['pageViews'].sum():,}")
                                st.line_chart(month_df1[["pageViews"]])

                            with col2:
                                st.subheader(f"期間2: {month_start_date2} ～ {month_end_date2}")
                                st.metric("合計表示回数", f"{month_df2['pageViews'].sum():,}")
                                st.line_chart(month_df2[["pageViews"]])

                            st.subheader("2月期間の比較")
                            diff_views = month_df1['pageViews'].sum() - month_df2['pageViews'].sum()
                            ratio_views = (month_df1['pageViews'].sum() / month_df2['pageViews'].sum() * 100) if month_df2['pageViews'].sum() else 0

                            st.write(f"表示回数差分: {diff_views:+,}　（期間1 - 期間2）")
                            st.write(f"表示回数比率: {ratio_views:.2f}%")

                except requests.exceptions.RequestException as e:
                    st.error(f"バックエンドへの接続に失敗しました: {e}")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

if input_mode == "週":
    week_ui_and_logic()
elif input_mode == "月":
    month_ui_and_logic()