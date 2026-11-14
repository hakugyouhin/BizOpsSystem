# BizOpsSystem - 開発ガイド

## 📋 概要

このドキュメントでは、BizOpsSystem の開発フロー、デプロイ方法、デバッグ方法を説明します。

---

## 🚀 高速開発フロー

### **推奨フロー**

```
1. ローカル Flask 開発 (最速)
   ↓
2. Docker ローカル検証 (オプション)
   ↓
3. gcloud run deploy で本番デプロイ (30秒)
   ↓
4. GitHub に push (履歴記録 + Cloud Build バックアップ)
```

---

## 🔥 **方法1: Flask 開発サーバー（推奨）**

**最速開発方法。UI/ロジック開発に最適。**

### セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/hakugyouhin/BizOpsSystem.git
cd BizOpsSystem

# Python 仮想環境を作成
python -m venv venv

# 仮想環境を有効化（Windows）
venv\Scripts\activate.bat

# 仮想環境を有効化（Mac/Linux）
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 開発サーバー起動

```bash
python app.py

# ブラウザで開く
# http://localhost:8080
```

### ホットリロード（自動リロード）

Flask は開発モード（`NODE_ENV != production`）では自動的にファイル変更を検知してリロードします。

```bash
# ファイルを編集 → 保存 → ブラウザをリロード
# または設定で自動リロード有効化
```

### デバッグ方法

```python
# コード内に print を挿入
print(f"DEBUG: {variable_name}")  # コンソール出力

# ブラウザの開発者ツール（F12）
# Console タブでエラー確認
# Network タブで API リクエスト確認
```

**メリット:**
- ✅ 変更が秒単位で反映
- ✅ デバッグが簡単
- ✅ 最速開発可能

**デメリット:**
- ❌ ローカル環境のみ
- ❌ Firestore は実環境と異なる

---

## 🐳 **方法2: Docker でローカル検証**

**本番環境に近い検証環境。本番デプロイ前の最終確認に最適。**

### Docker イメージをビルド

```bash
cd C:\Server\BizOps

# イメージをビルド
docker build -t bizopssystem:latest .

# ビルド確認
docker images | grep bizopssystem
```

### コンテナで実行

```bash
# 環境変数を設定してコンテナ起動
docker run -p 8080:8080 \
  -e NODE_ENV=production \
  -e GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp_key.json \
  bizopssystem:latest

# ブラウザで確認
# http://localhost:8080
```

### コンテナをキル

```bash
# 実行中のコンテナ一覧表示
docker ps

# コンテナを停止
docker stop <CONTAINER_ID>

# 削除（オプション）
docker rm <CONTAINER_ID>
```

**メリット:**
- ✅ 本番環境に近い検証
- ✅ 問題を早期発見
- ✅ 本番デプロイ前の安心確認

**デメリット:**
- ⏱️ ビルドに 1～2 分
- ❌ Firestore 認証は実環境と異なる

---

## ⚡ **方法3: gcloud run deploy で高速本番デプロイ**

**テスト完了後、Cloud Build を待たずに直接本番へデプロイ。最速本番反映。**

### 前提条件

```bash
# gcloud CLI がインストール済み
# Docker がインストール済み
gcloud --version
docker --version

# GCP に認証
gcloud auth login
gcloud config set project bizopssystem

# Docker を GCP に認証
gcloud auth configure-docker
```

### デプロイスクリプト実行（Windows）

```bash
# スクリプトを実行
deploy.bat

# または強制実行（確認なし）
deploy.bat --force
```

### デプロイスクリプト実行（Mac/Linux）

```bash
# 実行権限を付与
chmod +x deploy.sh

# スクリプトを実行
./deploy.sh

# または強制実行（確認なし）
./deploy.sh --force
```

### 手動コマンド

```bash
# Step 1: Docker イメージをビルド
docker build -t gcr.io/bizopssystem/bizopssystem:latest .

# Step 2: Container Registry にプッシュ
docker push gcr.io/bizopssystem/bizopssystem:latest

# Step 3: Cloud Run へデプロイ
gcloud run deploy bizopssystem \
    --image gcr.io/bizopssystem/bizopssystem:latest \
    --region asia-northeast1 \
    --platform managed \
    --allow-unauthenticated

# Step 4: サービス URL を確認
gcloud run services describe bizopssystem \
    --region asia-northeast1 \
    --format='value(status.url)'
```

**実行時間:**
- Docker ビルド: 2～3 分
- プッシュ: 1～2 分
- デプロイ: 30 秒
- **合計: 3～5 分（Cloud Build と同等）**

**メリット:**
- ✅ 本番反映が確実
- ✅ Cloud Build の待機時間なし
- ✅ 実環境で即座にテスト可能

**デメリット:**
- ⚠️ 手動確認が必要
- ⚠️ gcloud CLI の設定が必要

---

## 📤 **Step 4: GitHub に push（履歴記録）**

デプロイ完了後、コードを GitHub に push。

```bash
# 変更をステージ
git add .

# コミット
git commit -m "feat: 新しいホーム画面を追加"

# GitHub にプッシュ
git push origin main
```

**このとき Cloud Build も自動的に実行されます。**

---

## 🔄 **推奨開発ワークフロー（1日の流れ）**

```
朝（開発開始）
├─ Flask 開発サーバー起動: python app.py
├─ ローカルで機能開発・テスト
└─ ホットリロードで即座に確認

午前中（開発継続）
├─ UI/ロジックの修正
├─ ブラウザで確認（F12 でデバッグ）
└─ 同じサイクル

昼（テスト準備）
├─ Docker でローカル検証: docker build && docker run
├─ 本番環境に近い環境でテスト
└─ 問題がなければ OK

午後（本番反映）
├─ deploy.bat 実行（または deploy.sh）
├─ 本番環境で最終確認
└─ git push origin main（履歴記録）

夕方（CI/CD バックアップ）
├─ Cloud Build が自動実行（バックアップ）
├─ 確認: Cloud Build ログを見て成功確認
└─ 終了
```

---

## 🐛 **デバッグ方法**

### コンソール出力確認

```python
# app.py またはルートハンドラーに print を挿入
print(f"DEBUG: estimate_data = {estimate_data}")
```

ローカル開発時はコンソール（ターミナル）に出力されます。

### ブラウザ開発者ツール

```
F12 キー → Developer Tools
├─ Console: JavaScript エラー・console.log
├─ Network: API リクエスト・レスポンス
├─ Elements: HTML 構造・CSS
└─ Application: localStorage・Cookie
```

### Cloud Run ログ確認

```bash
# ログをリアルタイムで表示
gcloud run logs read bizopssystem \
    --region asia-northeast1 \
    --limit=50 \
    --follow
```

### ローカル Flask デバッグモード

```python
# app.py に追加
if __name__ == '__main__':
    app.run(debug=True)  # デバッグモード有効

# デバッグモードでは:
# - エラーが詳細表示
# - エラー発生時にデバッガが起動
# - ファイル変更で自動リロード
```

---

## 📊 **開発方法の速度比較**

| 方法 | ビルド | デプロイ | テスト環境 | 合計 |
|------|-------|---------|----------|------|
| Flask 開発 | 0秒 | 0秒 | ローカル | **0秒** 🔥 |
| Docker | 120秒 | 0秒 | ローカル | **2分** |
| gcloud deploy | 120秒 | 30秒 | 本番 | **2.5分** |
| Cloud Build | 120秒 | 30秒 | 本番 | **4分** ⏳ |

**結論: Flask 開発 → Docker 検証 → gcloud deploy が最適。**

---

## ✅ **チェックリスト**

新機能を追加するときの確認事項：

- [ ] Flask 開発サーバーでローカルテスト
- [ ] ブラウザの F12 でエラー確認
- [ ] レスポンシブ表示確認（PC・モバイル）
- [ ] Docker でローカル検証
- [ ] `git add . && git commit && git push`
- [ ] Cloud Build ログで成功確認（またはスキップして手動デプロイ）
- [ ] 本番環境で動作確認

---

## 🔗 **参考リンク**

- [Flask ドキュメント](https://flask.palletsprojects.com/)
- [Docker ドキュメント](https://docs.docker.com/)
- [Google Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [gcloud CLI リファレンス](https://cloud.google.com/cli/docs/reference)

---

**開発効率 UP！ Happy Coding! 🚀**
