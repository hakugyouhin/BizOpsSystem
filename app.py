# -*- coding: utf-8 -*-
"""
見積書作成システム - Flask メインアプリケーション
Python 3.8+ (モジュール化版)
"""

import os
import sys

# UTF-8 エンコーディングを設定
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
from datetime import datetime

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# ローカルモジュールをインポート
from utils.excel_utils import set_app_context as set_excel_app_context
from utils.pdf_utils import set_app_context as set_pdf_app_context
from routes.api import register_api_routes
from routes.web import register_web_routes, register_error_handlers

# VBA cmyInfoGet() 相当の関数をインポート
from get_company_info import get_company_info

# 環境変数を読み込み
load_dotenv()

# ========================================
# Flask アプリケーション初期化
# ========================================

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')

# CORS を有効化
CORS(app)

# ========================================
# 設定
# ========================================

PORT = int(os.getenv('PORT', 3000))
NODE_ENV = os.getenv('NODE_ENV', 'development')

# データ保存ディレクトリ
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# 見積データをメモリで管理
estimate_data = {}  # {session_id: {'rows': [...], 'management_file': '...', ...}}

# ========================================
# モジュールコンテキストを設定
# ========================================

set_excel_app_context(app, DATA_DIR)
set_pdf_app_context(app)

# ========================================
# ルートを登録
# ========================================

register_web_routes(app)
register_api_routes(app, estimate_data)
register_error_handlers(app)

# ========================================
# メイン
# ========================================

if __name__ == '__main__':
    print("=" * 80)
    print("  見積書作成システム - Flask サーバー起動")
    print("=" * 80)
    print(f"URL: http://localhost:{PORT}")
    print(f"環境: {NODE_ENV}")
    print(f"データディレクトリ: {DATA_DIR}")
    print(f"時刻: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
    print("=" * 80)
    print()

    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=(NODE_ENV == 'development')
    )
