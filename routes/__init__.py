# -*- coding: utf-8 -*-
"""
見積書作成システム - ルートモジュール
"""

from .api import register_api_routes
from .web import register_web_routes, register_error_handlers

__all__ = [
    'register_api_routes',
    'register_web_routes',
    'register_error_handlers'
]
