# -*- coding: utf-8 -*-
"""
Google Drive API 認証モジュール
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def get_drive_service():
    """Google Drive API サービスを取得

    Returns:
        Google Drive API クライアント
    """
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    if not credentials_path:
        raise ValueError('GOOGLE_APPLICATION_CREDENTIALS が設定されていません')

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/drive']
    )

    return build('drive', 'v3', credentials=credentials)


def get_sheet_service():
    """Google Sheets API サービスを取得

    Returns:
        Google Sheets API クライアント
    """
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    if not credentials_path:
        raise ValueError('GOOGLE_APPLICATION_CREDENTIALS が設定されていません')

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    return build('sheets', 'v4', credentials=credentials)
