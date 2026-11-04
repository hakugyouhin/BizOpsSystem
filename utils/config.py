# -*- coding: utf-8 -*-
"""
設定管理モジュール
"""

import json
import os
from pathlib import Path

def load_config(env=None):
    """
    環境に応じた設定ファイルを読み込む

    Args:
        env: 環境名（'development', 'production'）
             None の場合は環境変数 NODE_ENV から取得

    Returns:
        dict: 設定辞書
    """
    if env is None:
        env = os.getenv('NODE_ENV', 'development')

    config_dir = Path(__file__).parent.parent

    # 環境別設定ファイル
    if env == 'production':
        config_file = config_dir / 'config.prod.json'
    elif env == 'development':
        config_file = config_dir / 'config.dev.json'
    else:
        config_file = config_dir / 'config.json'

    # デフォルト設定ファイル
    default_config_file = config_dir / 'config.json'

    # ファイルが存在しない場合のフォールバック
    if not config_file.exists():
        config_file = default_config_file

    if not config_file.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_file}")

    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config


def get_config_value(config, key_path, default=None):
    """
    ネストされたキーから設定値を取得

    Args:
        config: 設定辞書
        key_path: キーパス（例: 'files.managementFile'）
        default: デフォルト値

    Returns:
        設定値またはデフォルト値
    """
    keys = key_path.split('.')
    value = config

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


# グローバル設定インスタンス
_config = None

def init_config(env=None):
    """設定を初期化"""
    global _config
    _config = load_config(env)
    return _config

def get_config():
    """グローバル設定を取得"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
