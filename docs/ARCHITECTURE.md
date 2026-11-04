# アーキテクチャドキュメント

## システム概要

見積書作成システムは、Flask ベースの Web アプリケーションで、Excel ファイルから見積書を自動生成し、PDF に変換します。

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                   Web ブラウザ                          │
│           (http://localhost:3000)                       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Flask アプリケーション                  │
│                     (app.py)                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │          ルート登録（routes/）                   │  │
│  │  ├── api.py     - API エンドポイント            │  │
│  │  └── web.py     - Web ページ + エラーハンドラ   │  │
│  └──────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────────┬─────────────┘
             │                              │
             ▼                              ▼
    ┌────────────────────┐      ┌────────────────────┐
    │  ユーティリティ     │      │    設定管理         │
    │   (utils/)         │      │   (utils/config.py)│
    │                    │      │                    │
    │ ├── excel_utils.py │      │ • config.json      │
    │ ├── pdf_utils.py   │      │ • config.dev.json  │
    │ └── config.py      │      │ • config.prod.json │
    └────────────┬───────┘      └────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
    ┌────────────┐  ┌────────────┐
    │   Excel    │  │    PDF     │
    │  操作      │  │   生成     │
    │            │  │            │
    │ • 読込     │  │ • 変換     │
    │ • 書込     │  │ • 出力     │
    │ • 生成     │  └────────────┘
    └────────────┘
```

## ファイル構成

### ルートディレクトリ

```
C:\Server\BizOps/
├── app.py                      # Flask メインアプリケーション
├── get_company_info.py         # 会社情報取得
├── requirements.txt            # 依存パッケージ
├── config.json                 # 設定ファイル
├── .env                        # 環境変数
├── .gitignore                  # Git 除外ファイル
├── README.md                   # プロジェクト概要
└── start-server.bat            # サーバー起動スクリプト
```

### routes/ - ルート定義

```
routes/
├── __init__.py                 # モジュール初期化
├── api.py                      # APIエンドポイント
│   ├── /api/write-content      - 見積内容を Excel に記入
│   ├── /api/generate-estimate  - 見積書 Excel 生成
│   └── /api/generate-pdf       - PDF 生成
└── web.py                      # Web ページとエラーハンドラ
    ├── /                       - メインページ
    ├── /api/config             - 設定取得
    └── /health                 - ヘルスチェック
```

### utils/ - ユーティリティモジュール

```
utils/
├── __init__.py                 # モジュール初期化
├── config.py                   # 設定管理
│   ├── load_config()           - 環境別に設定を読込
│   ├── get_config_value()      - ネストされたキーから値を取得
│   └── init_config()           - グローバル設定を初期化
├── excel_utils.py              # Excel 操作（589行）
│   ├── generate_estimate_sheets()     - 見積書生成
│   ├── write_to_excel()               - Excel 書込
│   ├── check_excel_macros()           - マクロ確認
│   └── その他 Excel 操作関数
└── pdf_utils.py                # PDF 生成（155行）
    └── generate_pdf_from_excel()      - PDF 生成
```

### その他のディレクトリ

```
templates/           # HTML テンプレート
├── index.html      # メインページ UI

OfficeTemplate/     # 見積書テンプレート
├── 見積書テンプレート.xlsx

Image/              # 画像ファイル
├── CompanyStamp.png

docs/               # ドキュメンテーション
├── README.md       # ドキュメント一覧
├── SETUP.md        # セットアップガイド
├── API.md          # API ドキュメント
├── CONFIG.md       # 設定ドキュメント
└── ARCHITECTURE.md # このファイル

logs/               # ログファイル出力先
backups/            # バックアップ
data/               # データファイル
static/             # 静的ファイル（CSS、JS など）
venv/               # Python 仮想環境
```

## 処理フロー

### 見積書生成フロー

```
1. ユーザー入力
   └── ステップ①：見積依頼内容を入力
       ├── 会社名、案件名、担当者、期限、期間、工数

2. Excel 書込
   └── ステップ②：見積内容を管理ファイル（Excel）に記入
       ├── write_to_excel() 関数で処理
       ├── 会社情報を自動取得
       ├── 担当者から単価を検索
       └── Excel に行データを記入

3. フォルダ指定
   └── ステップ③：見積書格納フォルダを指定
       └── config.json から自動入力

4. 見積書生成
   └── ステップ④：見積書 Excel ファイルを生成
       ├── generate_estimate_sheets() 関数で処理
       ├── テンプレートをコピー
       ├── データを設定されたセルに書込
       ├── ヘッダー背景色を削除
       └── ファイル名は「見積書_案件名_（期限）_見積No.xlsx」

5. PDF 生成
   └── ステップ⑤：Excel ファイルを PDF に変換
       ├── generate_pdf_from_excel() 関数で処理
       ├── LibreOffice コマンドラインで変換
       └── 同じフォルダに PDF を保存
```

## データフロー

### セッション管理

```
┌─────────────────────┐
│  クライアント       │
│  (ブラウザ)         │
└──────────┬──────────┘
           │ POST /api/write-content
           ▼
┌─────────────────────────────┐
│ Flask アプリケーション      │
│ ┌───────────────────────┐   │
│ │  estimate_data{}      │   │ セッションデータを
│ │  (メモリに保持)       │   │ メモリに保持
│ │ {                     │   │
│ │   session_id1: {      │   │
│ │     rows: [...]       │   │
│ │   }                   │   │
│ │ }                     │   │
│ └───────────────────────┘   │
└──────────┬────────────────────┘
           │ session_id を返却
           ▼
┌─────────────────────┐
│  クライアント       │
│  (session_id を保存)│
└─────────────────────┘
```

## 主要な関数

### routes/api.py

| 関数 | エンドポイント | 処理内容 |
|-----|--------------|--------|
| `write_content()` | POST /api/write-content | 見積内容を Excel に記入 |
| `generate_estimate()` | POST /api/generate-estimate | 見積書 Excel 生成 |
| `generate_pdf()` | POST /api/generate-pdf | PDF 生成 |

### utils/excel_utils.py

| 関数 | 処理内容 |
|-----|--------|
| `generate_estimate_sheets()` | 見積書ファイルを生成 |
| `write_to_excel()` | Excel に行データを記入 |
| `get_unit_price_from_ledger()` | 担当者から単価を検索 |
| `generate_unique_estimate_no()` | 一意の見積No を生成 |

### utils/pdf_utils.py

| 関数 | 処理内容 |
|-----|--------|
| `generate_pdf_from_excel()` | Excel を PDF に変換 |

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| **Web フレームワーク** | Flask 2.3.3 |
| **Excel 操作** | openpyxl 3.1.2 |
| **画像処理** | Pillow 13.0.0 |
| **CORS** | Flask-CORS 4.0.0 |
| **環境変数** | python-dotenv |
| **フロントエンド** | HTML5 + Vanilla JavaScript |
| **PDF 生成** | LibreOffice（コマンドライン） |

## 拡張性

### 新機能追加時

1. **API エンドポイント追加**
   - `routes/api.py` に新しいルート関数を追加
   - 必要に応じて `routes/__init__.py` を更新

2. **ユーティリティ関数追加**
   - 適切な `utils/*.py` モジュールに追加
   - `utils/__init__.py` でエクスポート

3. **設定項目追加**
   - `config.json` に新しいキーを追加
   - `utils/config.py` で取得関数を定義
   - ドキュメント（`docs/CONFIG.md`）を更新

### モジュール間の依存性

```
app.py
 ├── routes/
 │   ├── api.py (utils に依存)
 │   └── web.py
 └── utils/
     ├── config.py
     ├── excel_utils.py (get_company_info に依存)
     └── pdf_utils.py
```

## パフォーマンス考慮事項

1. **メモリ管理**
   - セッションデータはメモリに保持（サーバー再起動時にリセット）
   - 大量のセッションに対応する場合は、データベース導入を検討

2. **Excel ファイル処理**
   - 大きなファイルの処理は時間がかかる可能性
   - openpyxl のメモリ効率を確認

3. **PDF 生成**
   - LibreOffice コマンドラインは I/O バウンド
   - タイムアウト設定（デフォルト：60秒）

## セキュリティ考慮事項

1. **入力検証**
   - ファイルパス、ユーザー入力の検証が必要

2. **ファイルアクセス制御**
   - 指定されたフォルダのみアクセス可能

3. **認証・認可**
   - 現在、認証機構なし
   - 本番環境では実装推奨

---

最終更新：2026-11-01
