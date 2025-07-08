# flaskapp/services/logging_service.py

import json
from flask import session
from flaskapp.utils.db import get_db_connection

def log_action(target_type, target_id, action_source, action_type, action_details=None):
    """
    行動履歴をデータベースに記録する共通関数
    """
    # セッションから操作者情報を取得
    shain_code = session.get('shain_code', 'UNKNOWN')
    shain_name = session.get('shain_name', '不明なユーザー')

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO tr31_action_log (
                    shain_code, shain_name, target_type, target_id,
                    action_source, action_type, action_details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            # action_detailsが辞書やリストの場合、JSON文字列に変換
            details_json = json.dumps(action_details, ensure_ascii=False) if action_details else None

            cursor.execute(sql, (
                shain_code, shain_name, target_type, target_id,
                action_source, action_type, details_json
            ))
        conn.commit()
    except Exception as e:
        # ログ記録のエラーはメインの処理に影響させない
        print(f"!!! Log recording failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()