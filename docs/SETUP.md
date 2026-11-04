# セットアップガイド

## 前提条件

- Windows 11 Pro
- Python 3.8 以上
- LibreOffice（PDF 生成用）

## インストール手順

### 1. Python 仮想環境の作成

```bash
cd C:\Server\BizOps
python -m venv venv
```

### 2. 仮想環境の有効化

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**
```cmd
.\venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

主なパッケージ：
- Flask 2.3.3 - Web フレームワーク
- openpyxl 3.1.2 - Excel 操作
- Flask-CORS 4.0.0 - CORS サポート
- python-dotenv - 環境変数管理
- Pillow 13.0.0 - 画像処理

### 4. LibreOffice のインストール

PDF 生成機能を使用する場合、LibreOffice が必要です。

**インストール手順：**
1. [LibreOffice 公式ページ](https://ja.libreoffice.org/download/) からダウンロード
2. インストーラーを実行
3. 標準インストールを選択
4. コンピューターを再起動

**デフォルトインストール場所：**
- 32bit: `C:\Program Files (x86)\LibreOffice\program\soffice.exe`
- 64bit: `C:\Program Files\LibreOffice\program\soffice.exe`

### 5. 設定ファイルの作成

`config.example.json` をコピーして `config.json` を作成：

```bash
copy config.example.json config.json
```

必要に応じて、以下を編集：
- `files.managementFile` - 管理ファイル（Excel）のパス
- `files.priceListFile` - 単価リスト（Excel）のパス
- `files.outputFolder` - 出力フォルダ

### 6. 環境変数の設定

`.env.example` をコピーして `.env` を作成：

```bash
copy .env.example .env
```

必要に応じて、以下を編集：
- `PORT` - Flask サーバーのポート番号（デフォルト: 3000）
- `NODE_ENV` - 実行環境（development / production）

### 7. サーバーの起動

```bash
python app.py
```

起動成功時：
```
================================================================================
  見積書作成システム - Flask サーバー起動
================================================================================
URL: http://localhost:3000
環境: development
...
 * Running on http://127.0.0.1:3000
```

### 8. ブラウザでアクセス

`http://localhost:3000` をブラウザで開く

## トラブルシューティング

### エラー：Module not found

```
ModuleNotFoundError: No module named 'flask'
```

**対応：** 仮想環境が有効化されているか確認し、`pip install -r requirements.txt` を再実行

### エラー：Port already in use

```
Address already in use
```

**対応：** 別のプロセスがポート 3000 を使用しています。以下のいずれかを実行：

```bash
# 別のポートを使用
set PORT=3001
python app.py

# またはサーバーを停止
taskkill /F /IM python.exe
```

### エラー：LibreOffice not found

```
LibreOffice がインストールされていません
```

**対応：** LibreOffice をインストール（上記 4. を参照）

### Excel ファイルが開けない

**原因：** ファイルがロックされている

**対応：** 以前に開いたファイルをすべて閉じる

## 開発環境のセットアップ

### IDE の推奨設定

**Visual Studio Code:**
1. Python 拡張をインストール
2. `.vscode/settings.json` で仮想環境を指定

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python"
}
```

### デバッグモード

`NODE_ENV=development` の場合、自動リロード機能が有効になります。

### ログレベルの変更

`config.dev.json` の `logging.level` を変更：

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

## 次のステップ

- [API ドキュメント](API.md) - API エンドポイントの詳細
- [設定ドキュメント](CONFIG.md) - 設定ファイルの詳細
- [アーキテクチャ](ARCHITECTURE.md) - システム設計の詳細
