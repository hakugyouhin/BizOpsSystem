# -*- coding: utf-8 -*-
"""
見積書作成システム - Webページ・エラーハンドラ
Web UI ルートとエラーハンドリングを定義
"""

import json
from datetime import datetime
from pathlib import Path

from flask import render_template, send_from_directory, jsonify

# グローバルなアプリケーション参照（外部から渡される）
app = None


def register_web_routes(flask_app):
    """
    Web ルートを登録

    Args:
        flask_app: Flask アプリケーションインスタンス
    """
    global app
    app = flask_app

    @app.route('/')
    def index():
        """ホーム画面（メニュー）を返す"""
        return render_template('home.html')

    @app.route('/estimate')
    def estimate():
        """見積書作成ページを返す"""
        return render_template('estimate.html')

    @app.route('/invoice')
    def invoice():
        """請求書作成ページを返す"""
        return render_template('invoice.html')

    @app.route('/order')
    def order():
        """注文書ページを返す"""
        return render_template('order.html')

    @app.route('/attendance')
    def attendance():
        """勤務管理ページを返す"""
        return render_template('attendance.html')

    @app.route('/api/config', methods=['GET'])
    def get_config():
        """設定ファイルを返す"""
        try:
            config_file = Path(__file__).parent.parent / 'config.json'
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return jsonify({
                    'success': True,
                    'data': config
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Config file not found'
                }), 404
        except Exception as error:
            app.logger.error(f'設定読み込みエラー: {error}')
            return jsonify({
                'success': False,
                'error': str(error)
            }), 500

    @app.route('/static/<path:filename>')
    def static_files(filename):
        """静的ファイルを返す"""
        return send_from_directory('static', filename)

    @app.route('/health', methods=['GET'])
    def health_check():
        """ヘルスチェック"""
        return jsonify({
            'status': 'ok',
            'time': datetime.now().isoformat()
        })


def register_error_handlers(flask_app):
    """
    エラーハンドラを登録

    Args:
        flask_app: Flask アプリケーションインスタンス
    """
    global app
    app = flask_app

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'ページが見つかりません'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'サーバーエラーが発生しました'}), 500
