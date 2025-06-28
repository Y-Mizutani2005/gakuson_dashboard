
# GA4 アクティブユーザー数可視化アプリ

これは、Google Analytics Data API v1 を利用して、ウェブサイトのアクティブユーザー数を可視化するStreamlitアプリケーションです。

## 概要

このアプリケーションは、指定した期間の日別アクティブユーザー数をGoogle Analyticsから取得し、インタラクティブなダッシュボードに表示します。

- **フロントエンド**: Streamlit
- **バックエンド**: FastAPI

## セットアップ方法

### 1. 前提条件

- Python 3.8 以降
- Google Cloud Platform (GCP) プロジェクト
- Google Analytics 4 (GA4) プロパティ

### 2. Google APIの準備

1. **Google Analytics Data APIを有効にする**:
   - [GCP Console](https://console.cloud.google.com/)であなたのプロジェクトを選択します。
   - 「APIとサービス」 > 「ライブラリ」に移動し、「Google Analytics Data API」を検索して有効にします。

2. **サービスアカウントを作成する**:
   - 「APIとサービス」 > 「認証情報」に移動します。
   - 「認証情報を作成」 > 「サービスアカウント」を選択します。
   - サービスアカウントに名前を付け、「作成して続行」をクリックします。
   - ロールは不要です。「続行」をクリックします。
   - 「キーを作成」 > 「JSON」を選択し、キーファイルをダウンロードします。このファイルは後で使います。

3. **サービスアカウントに権限を付与する**:
   - [Google Analytics](https://analytics.google.com/)にアクセスします。
   - 「管理」 > 対象のGA4プロパティ > 「プロパティのアクセス管理」に移動します。
   - 「+」ボタン > 「ユーザーを追加」をクリックします。
   - ダウンロードしたキーファイル（JSON）に記載されている `client_email`（例: `your-account@your-project.iam.gserviceaccount.com`）をメールアドレスとして入力します。
   - 「閲覧者」の権限を付与し、「追加」をクリックします。

### 3. アプリケーションのインストール

1. **リポジトリをクローンまたはダウンロードします。**

2. **必要なライブラリをインストールします:**
   ```bash
   pip install -r requirements.txt
   ```
   (このプロジェクトでは `requirements.txt` の代わりに `pip install streamlit fastapi uvicorn google-analytics-data requests python-dotenv` を直接実行しました)

3. **環境変数を設定します:**
   - `.env.example` ファイルをコピーして `.env` という名前のファイルを作成します。
   - `.env` ファイルを編集し、以下の項目を設定します:
     - `GA_PROPERTY_ID`: あなたのGA4プロパティID（例: `123456789`）。
     - `SERVICE_ACCOUNT_FILE`: ステップ2でダウンロードしたサービスアカウントキー（JSONファイル）への**絶対パス**。
       - Windowsの例: `C:\Users\YourUser\Documents\secrets\your-key.json`
       - (パスの区切り文字 `\` は2重にするか `/` を使用してください)

## 実行方法

このアプリケーションは、バックエンドサーバーとフロントエンドアプリの2つのプロセスを起動する必要があります。

1. **ターミナル1: バックエンドサーバーを起動**
   ```bash
   uvicorn backend.main:app --reload
   ```
   サーバーが `http://127.0.0.1:8000` で起動します。

2. **ターミナル2: フロントエンドアプリを起動**
   ```bash
   streamlit run frontend/app.py
   ```
   ブラウザで `http://localhost:8501` が自動的に開かれ、ダッシュボードが表示されます。

## 使い方

1. ブラウザで表示されたダッシュボードの左サイドバーにあるカレンダーで、分析したい期間の「開始日」と「終了日」を選択します。
2. 「表示」ボタンをクリックします。
3. データが取得され、合計・平均アクティブユーザー数と、日別の推移を示す折れ線グラフが表示されます。
