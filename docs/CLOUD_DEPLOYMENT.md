# Google Cloud Run クラウド化デプロイメント

## 概要

見積書作成システムを Google Cloud Run に移行するための完全ガイドです。
既存のローカル Flask アプリケーションをそのままクラウドで運用できます。

**所要時間：4～6週間**
**月額コスト：$0～$10（初期はほぼ無料）**

---

## Phase 1: 準備（1週間）

### 1.1 GCP プロジェクト作成

**前提条件：** Gemini Pro アカウント保有

#### ステップ 1: Google Cloud Console にログイン
```
https://console.cloud.google.com
```

- Google アカウント（Gemini Pro）でログイン
- 新しいプロジェクトを作成

#### ステップ 2: プロジェクト設定
```
プロジェクト名：estimate-system
リージョン：asia-northeast1 (東京)
```

#### ステップ 3: 必要な API を有効化

**Cloud Run API**
- コンソール → API とサービス → ライブラリ
- 検索：Cloud Run
- 有効化

**Google Drive API**
- 検索：Google Drive API
- 有効化

**Cloud Build API**
- 検索：Cloud Build
- 有効化

**Firestore API**（セッション管理用）
- 検索：Cloud Firestore
- 有効化

### 1.2 GitHub リポジトリ準備

#### ステップ 1: GitHub に既存コードを push
```bash
cd C:\Server\BizOps

# リモートリポジトリを追加
git remote add origin https://github.com/YOUR_USERNAME/estimate-system.git

# コードをプッシュ
git branch -M main
git push -u origin main
```

#### ステップ 2: ファイル構成の確認
```
estimate-system/
├── app.py
├── config.json
├── config.dev.json
├── config.prod.json
├── requirements.txt
├── routes/
│   ├── api.py
│   └── web.py
├── utils/
│   ├── config.py
│   ├── excel_utils.py
│   └── pdf_utils.py
├── templates/
│   └── index.html
├── docs/
├── .env.example
├── .gitignore
└── Dockerfile  ← 新規作成
```

---

## Phase 2: 開発（2～3週間）

### 2.1 Dockerfile 作成

ファイル: `Dockerfile`

```dockerfile
FROM python:3.9-slim

# 作業ディレクトリ
WORKDIR /app

# LibreOffice インストール
RUN apt-get update && \
    apt-get install -y libreoffice && \
    rm -rf /var/lib/apt/lists/*

# Python 依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# ポート指定
ENV PORT=8080
EXPOSE 8080

# アプリケーション起動
CMD ["python", "app.py"]
```

### 2.2 requirements.txt を更新

以下を追加：

```txt
Flask==2.3.3
openpyxl==3.1.2
Flask-CORS==4.0.0
python-dotenv==1.0.0
Pillow==13.0.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.2.0
google-api-python-client==2.96.0
firebase-admin==6.2.0
gunicorn==21.2.0
```

### 2.3 app.py を修正

#### 修正 1: ポート番号を環境変数から読み込む

```python
# 修正前
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

# 修正後
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
```

#### 修正 2: Google Drive API 認証を追加

ファイル: `utils/auth.py` (新規作成)

```python
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import os

def get_drive_service():
    """Google Drive API サービスを取得"""
    # GCP サービスアカウント キーを使用
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not credentials_path:
        raise ValueError('GOOGLE_APPLICATION_CREDENTIALS が設定されていません')
    
    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    
    from googleapiclient.discovery import build
    return build('drive', 'v3', credentials=credentials)
```

#### 修正 3: Firestore セッション管理

ファイル: `utils/session.py` (新規作成)

```python
import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime, timedelta

def init_firestore():
    """Firestore を初期化"""
    cred = credentials.Certificate(
        os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    )
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = None

def get_db():
    global db
    if db is None:
        db = init_firestore()
    return db

def save_session(session_id, data):
    """セッションデータを保存（24時間有効）"""
    db = get_db()
    expiry = datetime.utcnow() + timedelta(hours=24)
    
    db.collection('sessions').document(session_id).set({
        'data': data,
        'created_at': datetime.utcnow(),
        'expiry_at': expiry
    })

def get_session(session_id):
    """セッションデータを取得"""
    db = get_db()
    doc = db.collection('sessions').document(session_id).get()
    
    if doc.exists:
        return doc.to_dict().get('data')
    return None
```

### 2.4 環境変数設定

ファイル: `.env.cloud`

```env
# Cloud Run
PORT=8080
NODE_ENV=production

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/workspace/service-account-key.json
GOOGLE_CLOUD_PROJECT=estimate-system

# Flask
FLASK_ENV=production
PYTHONIOENCODING=utf-8
```

### 2.5 config.prod.json を更新

Google Drive のパスに変更：

```json
{
  "app": {
    "name": "見積書作成システム",
    "version": "1.0.0",
    "description": "クラウド版"
  },
  "files": {
    "managementFile": "https://drive.google.com/file/d/YOUR_FILE_ID/view",
    "priceListFile": "https://drive.google.com/file/d/YOUR_FILE_ID/view",
    "outputFolder": "https://drive.google.com/drive/folders/YOUR_FOLDER_ID",
    "templateFolder": "/app/OfficeTemplate",
    "dataFolder": "/tmp/data"
  },
  "excel": {
    "templateFile": "見積書テンプレート.xlsx",
    "managementSheet": "見積書",
    "priceListSheet": "金額リスト",
    "estimateNoPrefix": "N",
    "estimateDateFormat": "%Y%m%d",
    "headerRowRemovalEnabled": true
  },
  "pdf": {
    "enabled": true,
    "libreOfficePath": "/usr/bin/soffice",
    "timeout": 60
  },
  "logging": {
    "level": "WARNING",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### 2.6 .gitignore を更新

```
.env
.env.local
.env.cloud
service-account-key.json
__pycache__/
*.pyc
venv/
logs/
*.log
.DS_Store
config.local.json
```

---

## Phase 3: GCP デプロイ設定（1週間）

### 3.1 Cloud Build トリガー設定

#### ステップ 1: GitHub リポジトリを接続
```
Cloud Console → Cloud Build → リポジトリ
GitHub を選択 → リポジトリを接続
```

#### ステップ 2: トリガーを作成
```
新しいトリガー
├─ 名前：estimate-system-deploy
├─ リポジトリ：estimate-system
├─ ブランチ：main
└─ ビルド設定：Dockerfile
```

#### ステップ 3: cloudbuild.yaml を作成（オプション）

ファイル: `cloudbuild.yaml`

```yaml
steps:
  # ステップ 1: イメージをビルド
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/estimate-system:$SHORT_SHA', '.']

  # ステップ 2: Container Registry にプッシュ
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/estimate-system:$SHORT_SHA']

  # ステップ 3: Cloud Run にデプロイ
  - name: 'gcr.io/cloud-builders/gke-deploy'
    args:
      - run
      - --filename=.
      - --image=gcr.io/$PROJECT_ID/estimate-system:$SHORT_SHA
      - --location=asia-northeast1
      - --output=/workspace/out

images:
  - 'gcr.io/$PROJECT_ID/estimate-system:$SHORT_SHA'
```

### 3.2 サービスアカウント作成

#### ステップ 1: サービスアカウントを作成
```
IAM と管理 → サービスアカウント
新しいサービスアカウント
├─ 名前：estimate-system-server
└─ ロール：Cloud Run 管理者、Firestore 管理者
```

#### ステップ 2: キーを作成
```
サービスアカウント → キー → 新しいキー → JSON
ダウンロード → service-account-key.json
```

#### ステップ 3: Cloud Run に追加
```
Cloud Run → サービス選択 → セキュリティ
サービスアカウント：estimate-system-server
```

### 3.3 Cloud Run に初回デプロイ

#### 方法 1: Cloud Console から（推奨）

```
Cloud Run → サービスの作成
├─ コンテナイメージの URL：gcr.io/PROJECT_ID/estimate-system
├─ サービス名：estimate-system
├─ リージョン：asia-northeast1
├─ メモリ：2GB
├─ CPU：1
├─ タイムアウト：3600秒
├─ 環境変数：
│  ├─ PORT=8080
│  ├─ NODE_ENV=production
│  └─ GOOGLE_APPLICATION_CREDENTIALS=/workspace/service-account-key.json
└─ デプロイ
```

#### 方法 2: コマンドラインから

```bash
gcloud run deploy estimate-system \
  --source . \
  --region asia-northeast1 \
  --platform managed \
  --memory 2Gi \
  --cpu 1 \
  --timeout 3600 \
  --set-env-vars NODE_ENV=production
```

---

## Phase 4: テスト（1～2週間）

### 4.1 動作確認

#### ステップ 1: サービス URL を確認
```
Cloud Run → estimate-system → サービスの詳細
URL: https://estimate-system-xxx.run.app
```

#### ステップ 2: ブラウザでアクセス
```
https://estimate-system-xxx.run.app
```

#### ステップ 3: API テスト
```bash
# 設定ファイル取得
curl https://estimate-system-xxx.run.app/api/config

# ヘルスチェック
curl https://estimate-system-xxx.run.app/health
```

### 4.2 複数ユーザーでテスト

1. テストユーザーを招待
2. 見積書生成フロー全体をテスト
3. パフォーマンス計測
4. エラーログ確認

---

## Phase 5: 本番移行（1週間）

### 5.1 ドメイン設定（オプション）

#### ステップ 1: カスタムドメイン マッピング
```
Cloud Run → estimate-system → マッピング
カスタムドメイン → 新しいドメイン マッピング
ドメイン：estimate.yourcompany.com
```

#### ステップ 2: DNS レコード設定
```
ドメインレジストラで CNAME レコード を追加
CNAME estimate → ghs.googleusercontent.com
```

#### ステップ 3: 確認
```
https://estimate.yourcompany.com でアクセス可能か確認
```

### 5.2 運用開始

- ユーザー招待
- トレーニング実施
- ローカル版のサポート終了告知
- 段階的に移行

---

## 運用ガイド

### システム更新方法

#### パターン 1: GitHub から自動デプロイ（推奨）
```bash
# ローカルで修正
vim app.py

# コミット＆プッシュ
git add .
git commit -m "フィーチャー追加"
git push origin main

# Cloud Build が自動検知
# → Docker イメージビルド
# → Cloud Run にデプロイ
# （ユーザーは何もしない）
```

#### パターン 2: Cloud Console から手動デプロイ
```
Cloud Run → estimate-system → 新しいリビジョンをデプロイ
```

#### パターン 3: gcloud コマンドから
```bash
gcloud run deploy estimate-system --source .
```

### ログ確認

```bash
# リアルタイムログ表示
gcloud run logs read estimate-system --limit 50 --follow

# Cloud Console から
# Cloud Run → estimate-system → ログ
```

### ロールバック

**前のバージョンに戻す：**
```
Cloud Run → estimate-system → リビジョン
前のリビジョンを選択 → トラフィックを割り当て
```

### パフォーマンス監視

```
Cloud Run → estimate-system → メトリクス
├─ リクエスト数
├─ エラー率
├─ レイテンシー
└─ CPU/メモリ使用率
```

---

## トラブルシューティング

### エラー 1: ビルド失敗
```
Cloud Build → ビルド履歴 → ログを確認
```

### エラー 2: Google Drive アクセス失敗
```
✓ サービスアカウント が Drive フォルダへのアクセス権を持つか確認
✓ GOOGLE_APPLICATION_CREDENTIALS が正しく設定されているか確認
```

### エラ 3: タイムアウト
```
Cloud Run → サービス設定 → タイムアウト を 3600秒 に延長
```

---

## チェックリスト

### 事前準備
- [ ] GCP プロジェクト作成
- [ ] 必要な API を有効化
- [ ] Gemini Pro アカウント確認

### 開発フェーズ
- [ ] Dockerfile 作成
- [ ] requirements.txt 更新
- [ ] app.py 修正（ポート環境変数対応）
- [ ] Google Drive API 統合
- [ ] Firestore セッション管理
- [ ] GitHub にプッシュ

### GCP セットアップ
- [ ] Cloud Build トリガー設定
- [ ] サービスアカウント作成
- [ ] Cloud Run 初回デプロイ

### テスト
- [ ] URL アクセス確認
- [ ] API テスト実施
- [ ] 複数ユーザーでテスト
- [ ] パフォーマンス計測

### 本番移行
- [ ] ドメイン設定（オプション）
- [ ] ユーザー招待
- [ ] トレーニング実施
- [ ] ローカル版サポート終了

---

## 参考リンク

- [Google Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud Build ドキュメント](https://cloud.google.com/build/docs)
- [Google Drive API](https://developers.google.com/drive)
- [Cloud Firestore](https://cloud.google.com/firestore/docs)

---

**最終更新：2026-11-01**
**次回開始日時：TBD**
