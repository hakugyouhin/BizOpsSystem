# 設定ファイルドキュメント

## 概要

見積書作成システムの設定は、以下の方法で管理されます：

1. **環境変数（.env）** - サーバー実行設定
2. **設定ファイル（config.*.json）** - アプリケーション設定

## 環境変数（.env）

`.env` ファイルでサーバーの実行環境を設定します。

### 設定項目

| 変数名 | デフォルト | 説明 |
|---------|-----------|------|
| `PORT` | 3000 | Flask サーバーのポート番号 |
| `NODE_ENV` | development | 実行環境（development / production） |
| `PYTHONIOENCODING` | utf-8 | Python の文字エンコーディング |

### サンプル

```env
PORT=3000
NODE_ENV=development
PYTHONIOENCODING=utf-8
```

## 設定ファイル（config.json）

`config.json` でアプリケーションの動作を設定します。

### ファイル構成

```
config.json        - デフォルト設定（互換性用）
config.dev.json    - 開発環境用設定
config.prod.json   - 本番環境用設定
config.example.json - テンプレート
```

### 環境の選択

アプリケーションは `NODE_ENV` 環境変数に応じて、自動的に設定ファイルを選択します：

- `NODE_ENV=development` → `config.dev.json`
- `NODE_ENV=production` → `config.prod.json`
- その他 → `config.json`

### 設定項目

#### app - アプリケーション情報

```json
{
  "app": {
    "name": "見積書作成システム",
    "version": "1.0.0",
    "description": "Flask ベースの見積書自動生成システム"
  }
}
```

#### files - ファイルパス

```json
{
  "files": {
    "managementFile": "G:\\マイドライブ\\96_tmp\\20261010\\請求書＆注文書生成_双日用_Excel版2.xlsx",
    "priceListFile": "G:\\マイドライブ\\96_tmp\\20261010\\派遣業務管理台帳_統合.xlsx",
    "outputFolder": "G:\\マイドライブ\\96_tmp\\20261010",
    "templateFolder": "C:\\Server\\BizOps\\OfficeTemplate",
    "dataFolder": "C:\\Server\\BizOps\\data"
  }
}
```

| 設定項目 | 説明 |
|---------|------|
| `managementFile` | 管理ファイル（Excel）のフルパス |
| `priceListFile` | 単価リスト（Excel）のフルパス |
| `outputFolder` | 見積書出力フォルダ |
| `templateFolder` | テンプレート格納フォルダ |
| `dataFolder` | データ格納フォルダ |

#### excel - Excel 操作設定

```json
{
  "excel": {
    "templateFile": "見積書テンプレート.xlsx",
    "managementSheet": "見積書",
    "priceListSheet": "金額リスト",
    "estimateNoPrefix": "N",
    "estimateDateFormat": "%Y%m%d",
    "headerRowRemovalEnabled": true
  }
}
```

| 設定項目 | 説明 |
|---------|------|
| `templateFile` | テンプレートファイル名 |
| `managementSheet` | 管理ファイルのシート名 |
| `priceListSheet` | 単価リストのシート名 |
| `estimateNoPrefix` | 見積No のプレフィックス |
| `estimateDateFormat` | 日付フォーマット |
| `headerRowRemovalEnabled` | ヘッダー行の背景色削除 |

#### pdf - PDF 生成設定

```json
{
  "pdf": {
    "enabled": true,
    "libreOfficePath": "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    "timeout": 60
  }
}
```

| 設定項目 | 説明 |
|---------|------|
| `enabled` | PDF 生成機能の有効/無効 |
| `libreOfficePath` | LibreOffice 実行ファイルのパス |
| `timeout` | PDF 生成のタイムアウト（秒） |

#### logging - ログ設定

```json
{
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

| 設定項目 | 説明 |
|---------|------|
| `level` | ログレベル（DEBUG / INFO / WARNING / ERROR / CRITICAL） |
| `format` | ログのフォーマット |

**ログレベル：**
- `DEBUG` - 詳細情報（開発時）
- `INFO` - 一般情報
- `WARNING` - 警告（本番環境の推奨） |
- `ERROR` - エラー
- `CRITICAL` - 致命的エラー

## 完全な設定例

```json
{
  "app": {
    "name": "見積書作成システム",
    "version": "1.0.0",
    "description": "Flask ベースの見積書自動生成システム"
  },
  "files": {
    "managementFile": "G:\\マイドライブ\\96_tmp\\20261010\\請求書＆注文書生成_双日用_Excel版2.xlsx",
    "priceListFile": "G:\\マイドライブ\\96_tmp\\20261010\\派遣業務管理台帳_統合.xlsx",
    "outputFolder": "G:\\マイドライブ\\96_tmp\\20261010",
    "templateFolder": "C:\\Server\\BizOps\\OfficeTemplate",
    "dataFolder": "C:\\Server\\BizOps\\data"
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
    "libreOfficePath": "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    "timeout": 60
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

## トラブルシューティング

### LibreOffice パスが見つからない

`libreOfficePath` を確認してください。デフォルトは：

- 32bit: `C:\Program Files (x86)\LibreOffice\program\soffice.exe`
- 64bit: `C:\Program Files\LibreOffice\program\soffice.exe`

### Excel ファイルが見つからない

`managementFile`、`priceListFile` のパスを確認してください。フルパスの指定が必要です。

---

最終更新：2026-11-01
