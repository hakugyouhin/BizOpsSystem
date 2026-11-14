# -*- coding: utf-8 -*-
"""
Firestore セッション管理モジュール
メモリ内セッション（ローカル）とFirestore（クラウド）の両対応
"""

import os
import json
import uuid
from datetime import datetime, timedelta

# Firestore インポート（オプション）
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False

# メモリベースのセッション（ローカル開発用）
_memory_sessions = {}


class SessionManager:
    """セッション管理クラス"""

    def __init__(self, use_firestore=False):
        """初期化

        Args:
            use_firestore (bool): Firestore を使用するか
        """
        self.use_firestore = use_firestore and FIRESTORE_AVAILABLE
        self.db = None

        if self.use_firestore:
            self._init_firestore()

    def _init_firestore(self):
        """Firestore を初期化"""
        try:
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if not cred_path:
                raise ValueError('GOOGLE_APPLICATION_CREDENTIALS が設定されていません')

            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)

            self.db = firestore.client()
        except Exception as e:
            print(f"⚠️ Firestore 初期化失敗: {e}")
            self.use_firestore = False

    def create_session(self, data):
        """新しいセッションを作成

        Args:
            data (dict): セッションデータ

        Returns:
            str: セッション ID
        """
        session_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        expiry = timestamp + timedelta(hours=24)

        session_data = {
            'id': session_id,
            'data': data,
            'created_at': timestamp,
            'expiry_at': expiry,
        }

        if self.use_firestore and self.db:
            try:
                self.db.collection('sessions').document(session_id).set({
                    'data': data,
                    'created_at': timestamp,
                    'expiry_at': expiry
                })
            except Exception as e:
                print(f"⚠️ Firestore セッション保存失敗: {e}")
                # メモリフォールバック
                _memory_sessions[session_id] = session_data
        else:
            _memory_sessions[session_id] = session_data

        return session_id

    def get_session(self, session_id):
        """セッションデータを取得

        Args:
            session_id (str): セッション ID

        Returns:
            dict: セッションデータ、または None
        """
        if self.use_firestore and self.db:
            try:
                doc = self.db.collection('sessions').document(session_id).get()
                if doc.exists:
                    return doc.to_dict().get('data')
            except Exception as e:
                print(f"⚠️ Firestore セッション取得失敗: {e}")

        # メモリから取得
        session = _memory_sessions.get(session_id)
        if session:
            return session.get('data')

        return None

    def update_session(self, session_id, data):
        """セッションデータを更新

        Args:
            session_id (str): セッション ID
            data (dict): 更新データ

        Returns:
            bool: 成功したか
        """
        if self.use_firestore and self.db:
            try:
                self.db.collection('sessions').document(session_id).update({
                    'data': data,
                    'updated_at': datetime.utcnow()
                })
                return True
            except Exception as e:
                print(f"⚠️ Firestore セッション更新失敗: {e}")

        # メモリを更新
        if session_id in _memory_sessions:
            _memory_sessions[session_id]['data'] = data
            return True

        return False

    def delete_session(self, session_id):
        """セッションを削除

        Args:
            session_id (str): セッション ID

        Returns:
            bool: 成功したか
        """
        if self.use_firestore and self.db:
            try:
                self.db.collection('sessions').document(session_id).delete()
                return True
            except Exception as e:
                print(f"⚠️ Firestore セッション削除失敗: {e}")

        # メモリから削除
        if session_id in _memory_sessions:
            del _memory_sessions[session_id]
            return True

        return False


# グローバルセッションマネージャー
_session_manager = None


def init_session_manager(use_firestore=False):
    """セッションマネージャーを初期化

    Args:
        use_firestore (bool): Firestore を使用するか
    """
    global _session_manager
    _session_manager = SessionManager(use_firestore=use_firestore)


def get_session_manager():
    """セッションマネージャーを取得

    Returns:
        SessionManager: セッションマネージャー
    """
    global _session_manager
    if _session_manager is None:
        # 環境に応じて Firestore を使用するか判定
        use_firestore = os.getenv('NODE_ENV') == 'production'
        init_session_manager(use_firestore=use_firestore)
    return _session_manager
