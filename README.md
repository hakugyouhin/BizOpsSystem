# 見積書作成システム

Flask ベースの見積書自動生成システム。Excel ファイルから見積書を自動生成し、PDF に変換します。

## 主な機能

- **ステップ①**：見積依頼内容の手動入力
- **ステップ②**：見積内容を Excel に自動記入
- **ステップ③**：見積書格納フォルダを指定
- **ステップ④**：見積書 Excel ファイルを自動生成
- **ステップ⑤**：Excel ファイルを PDF に変換

## クイックスタート

### 必要な環境

- Python 3.8+
- LibreOffice（PDF 生成用）

### セットアップ

```bash
# 1. 仮想環境を作成
python -m venv venv

# 2. 仮想環境を有効化
.\venv\Scripts\Activate.ps1  # Windows PowerShell
source venv/bin/activate      # Mac/Linux

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. サーバーを起動
python app.py
```

### 使用方法

1. ブラウザで `http://localhost:3000` にアクセス
2. ステップ①～⑤を順に実行

詳細は [SETUP.md](docs/SETUP.md) を参照してください。

## プロジェクト構成

```
C:\Server\BizOps/
├── app.py                      # Flask メインアプリケーション
├── get_company_info.py         # 会社情報取得機能
├── config.json                 # 設定ファイル
├── requirements.txt            # Python 依存パッケージ
│
├── routes/                     # API ルート定義
│   ├── api.py                 # API エンドポイント
│   └── web.py                 # Web ページ
│
├── utils/                      # ユーティリティモジュール
│   ├── excel_utils.py         # Excel 操作
│   ├── pdf_utils.py           # PDF 生成
│   └── config.py              # 設定管理
│
├── templates/                  # HTML テンプレート
├── static/                     # 静的ファイル（CSS、JS など）
│
├── OfficeTemplate/             # 見積書テンプレート
├── Image/                      # 画像ファイル
├── docs/                       # ドキュメント
├── logs/                       # ログファイル
└── backups/                    # バックアップ
```

詳細は [ARCHITECTURE.md](docs/ARCHITECTURE.md) を参照してください。

## 設定

### 環境変数（.env）

```
PORT=3000
NODE_ENV=development
PYTHONIOENCODING=utf-8
```

### アプリケーション設定（config.json）

```json
{
  "files": {
    "managementFile": "...",
    "priceListFile": "...",
    "outputFolder": "..."
  },
  "excel": { ... },
  "pdf": { ... }
}
```

詳細は [CONFIG.md](docs/CONFIG.md) を参照してください。

## API エンドポイント

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/config` | 設定ファイルを取得 |
| POST | `/api/write-content` | 見積内容を Excel に記入 |
| POST | `/api/generate-estimate` | 見積書 Excel ファイルを生成 |
| POST | `/api/generate-pdf` | Excel ファイルを PDF に変換 |
| GET | `/health` | ヘルスチェック |

詳細は [API.md](docs/API.md) を参照してください。

## トラブルシューティング

### LibreOffice が見つからない

`config.json` の `pdf.libreOfficePath` を確認してください。

### Excel ファイルがロックされている

生成後のファイルを手動で編集する際は、確実にファイルを閉じてください。

## ライセンス

MIT License

## サポート

問題が発生した場合は、`logs/` フォルダのログファイルを確認してください。

---

最終更新：2026-11-01

# Last deployment attempt: 2026-11-14 16:07:17
