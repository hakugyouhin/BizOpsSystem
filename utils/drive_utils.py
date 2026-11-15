# -*- coding: utf-8 -*-
"""
Google Drive API ユーティリティ
Google Drive のファイル・フォルダ操作をサポート
"""

import os
import io
from pathlib import Path
from google.oauth2.service_account import Credentials
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Google Drive API スコープ
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Google Drive API サービスを取得"""
    try:
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        if credentials_path:
            # サービスアカウント キーファイルがある場合
            credentials = Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
        else:
            # デフォルトのアプリケーション認証情報を使う（Cloud Run推奨）
            credentials, project = default(scopes=SCOPES)

        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"Google Drive API 初期化エラー: {e}")
        return None


def download_file_from_drive(file_id, output_path=None):
    """
    Google Drive からファイルをダウンロード

    Args:
        file_id: Google Drive のファイル ID
        output_path: 保存先パス（省略時はメモリに保持）

    Returns:
        bytes: ファイルの内容（output_path 指定時は None）
    """
    service = get_drive_service()
    if not service:
        raise Exception("Google Drive API が初期化できません")

    try:
        request = service.files().get_media(fileId=file_id)

        if output_path:
            # ファイルに保存
            with open(output_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

            # ファイルサイズを確認
            file_size = Path(output_path).stat().st_size
            if file_size == 0:
                raise Exception(f"ダウンロードしたファイルが空です")

            return None
        else:
            # メモリに保持
            file_obj = io.BytesIO()
            downloader = MediaIoBaseDownload(file_obj, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return file_obj.getvalue()

    except Exception as e:
        raise Exception(f"ファイルダウンロードエラー: {e}")


def upload_file_to_drive(file_path, parent_folder_id=None, file_name=None):
    """
    Google Drive にファイルをアップロード

    Args:
        file_path: ローカルファイルパス
        parent_folder_id: 親フォルダ ID（省略時はルート）
        file_name: アップロード時のファイル名（省略時は元のファイル名）

    Returns:
        str: アップロードされたファイルの ID
    """
    service = get_drive_service()
    if not service:
        raise Exception("Google Drive API が初期化できません")

    try:
        if not file_name:
            file_name = Path(file_path).name

        file_metadata = {'name': file_name}
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get('id')

    except Exception as e:
        raise Exception(f"ファイルアップロードエラー: {e}")


def find_folder_id_by_name(folder_name, parent_folder_id=None):
    """
    フォルダ名から Google Drive フォルダ ID を取得

    Args:
        folder_name: フォルダ名
        parent_folder_id: 親フォルダ ID（省略時はマイドライブ）

    Returns:
        str: フォルダ ID
    """
    service = get_drive_service()
    if not service:
        raise Exception("Google Drive API が初期化できません")

    try:
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"

        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()

        files = results.get('files', [])
        if files:
            return files[0]['id']
        else:
            raise Exception(f"フォルダが見つかりません: {folder_name}")

    except Exception as e:
        raise Exception(f"フォルダ検索エラー: {e}")


def find_file_id_by_name(file_name, folder_id=None):
    """
    ファイル名から Google Drive ファイル ID を取得

    Args:
        file_name: ファイル名
        folder_id: フォルダ ID（省略時はマイドライブ）

    Returns:
        str: ファイル ID
    """
    service = get_drive_service()
    if not service:
        raise Exception("Google Drive API が初期化できません")

    try:
        query = f"name='{file_name}' and trashed=false"

        if folder_id:
            query += f" and '{folder_id}' in parents"

        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()

        files = results.get('files', [])
        if files:
            return files[0]['id']
        else:
            return None

    except Exception as e:
        raise Exception(f"ファイル検索エラー: {e}")


def is_google_drive_path(path_str):
    """
    パスが Google Drive パスかローカルパスか判定

    Args:
        path_str: ファイルパス文字列

    Returns:
        bool: Google Drive パスの場合は True
    """
    if not path_str:
        return False

    # パターン1: Google Drive フォルダ ID（28文字の英数字）
    if len(path_str) == 28 and path_str.replace('_', '').replace('-', '').isalnum():
        return True

    # パターン2: gdrive:// プロトコル
    if path_str.startswith('gdrive://'):
        return True

    # パターン3: ローカルパスではない（パス区切りがない）
    if '\\' not in path_str and '/' not in path_str and not path_str.startswith('G:'):
        return True

    return False


def parse_google_drive_path(path_str):
    """
    Google Drive パス文字列をパース

    Args:
        path_str: Google Drive パス（フォルダID または gdrive://folder_name/file_name）

    Returns:
        dict: {'type': 'folder_id'|'path', 'value': ...}
    """
    if path_str.startswith('gdrive://'):
        # gdrive://folder_name/file_name 形式
        path_str = path_str.replace('gdrive://', '')
        parts = path_str.split('/')
        return {
            'type': 'path',
            'folder_name': parts[0] if parts else None,
            'file_name': parts[1] if len(parts) > 1 else None
        }
    else:
        # フォルダ ID 形式
        return {
            'type': 'folder_id',
            'folder_id': path_str
        }
