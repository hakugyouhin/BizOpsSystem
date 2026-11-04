# API ドキュメント

## 概要

見積書作成システムの REST API エンドポイント仕様です。

## ベース URL

```
http://localhost:3000
```

## 認証

現在、認証は実装されていません。

## エンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/` | メインページ（HTML） |
| GET | `/api/config` | 設定ファイルを取得 |
| POST | `/api/write-content` | 見積内容を Excel に記入 |
| POST | `/api/generate-estimate` | 見積書 Excel ファイルを生成 |
| POST | `/api/generate-pdf` | Excel ファイルを PDF に変換 |
| GET | `/health` | ヘルスチェック |

---

## GET /api/config

設定ファイルを取得します。

### リクエスト

```bash
curl http://localhost:3000/api/config
```

### レスポンス

```json
{
  "success": true,
  "data": {
    "app": {
      "name": "見積書作成システム",
      "version": "1.0.0"
    },
    "files": {
      "managementFile": "G:\\マイドライブ\\...",
      "priceListFile": "G:\\マイドライブ\\...",
      "outputFolder": "G:\\マイドライブ\\..."
    }
  }
}
```

---

## POST /api/write-content

見積内容を Excel に記入します。

### リクエスト

```bash
curl -X POST http://localhost:3000/api/write-content \
  -H "Content-Type: application/json" \
  -d '{
    "rows": [
      {
        "company": "会社名",
        "project": "案件名",
        "person": "担当者",
        "deadline": "2026/10/1 ～ 2026/12/31",
        "period": "3",
        "workload": "5"
      }
    ],
    "managementFile": "...",
    "priceList": "..."
  }'
```

### パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `rows` | array | 見積データ行配列 |
| `rows[].company` | string | 会社名 |
| `rows[].project` | string | 案件名 |
| `rows[].person` | string | 担当者名 |
| `rows[].deadline` | string | 作業期限（例：2026/10/1 ～ 2026/12/31） |
| `rows[].period` | number | 期間（ヶ月） |
| `rows[].workload` | number | 工数（人月） |
| `managementFile` | string | 管理ファイル（Excel）のフルパス |
| `priceList` | string | 単価リスト（Excel）のフルパス |

### レスポンス

```json
{
  "success": true,
  "message": "見積内容が保存されました（N件）",
  "session_id": "uuid-string",
  "data": [...]
}
```

---

## POST /api/generate-estimate

見積書 Excel ファイルを生成します。

### リクエスト

```bash
curl -X POST http://localhost:3000/api/generate-estimate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "uuid-string",
    "output_folder": "G:\\マイドライブ\\...",
    "management_file": "...",
    "price_list": "..."
  }'
```

### パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `session_id` | string | /api/write-content で取得したセッション ID |
| `output_folder` | string | 出力フォルダのフルパス |
| `management_file` | string | 管理ファイル（Excel）のフルパス |
| `price_list` | string | 単価リスト（Excel）のフルパス |

### レスポンス

```json
{
  "success": true,
  "message": "N件の見積書を生成しました",
  "files": [
    "見積書_案件名_（20261001～20261231）_N2610001.xlsx",
    "見積書_案件名_（20261001～20261231）_N2610002.xlsx"
  ]
}
```

---

## POST /api/generate-pdf

Excel ファイルを PDF に変換します。

### リクエスト

```bash
curl -X POST http://localhost:3000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "output_folder": "G:\\マイドライブ\\...",
    "excel_files": [
      "見積書_案件名_（20261001～20261231）_N2610001.xlsx"
    ]
  }'
```

### パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `output_folder` | string | 出力フォルダのフルパス |
| `excel_files` | array | 変換対象の Excel ファイル名配列 |

### レスポンス

```json
{
  "success": true,
  "message": "N件の PDF ファイルを生成しました",
  "files": [
    "見積書_案件名_（20261001～20261231）_N2610001.pdf"
  ]
}
```

---

## GET /health

ヘルスチェック（サーバーが正常に動作しているか確認）

### リクエスト

```bash
curl http://localhost:3000/health
```

### レスポンス

```json
{
  "status": "ok",
  "time": "2026-11-01T20:36:52.267576"
}
```

---

## エラーレスポンス

エラーが発生した場合、以下の形式でレスポンスが返されます。

```json
{
  "success": false,
  "message": "エラーメッセージ"
}
```

HTTP ステータスコード：
- `200` - 成功
- `400` - リクエストエラー
- `500` - サーバーエラー

---

## レート制限

現在、レート制限は実装されていません。

## セッション管理

セッション情報はメモリに保持されます（サーバー再起動時にリセット）。

---

最終更新：2026-11-01
