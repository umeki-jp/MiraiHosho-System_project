# flaskapp/routes/logs.py

import json
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flaskapp.utils.db import get_db_connection
from flaskapp.common import constants

# Blueprint名を 'logs_bp' に変更
logs_bp = Blueprint("logs", __name__)

# URLを /logs/loglist に変更
@logs_bp.route("/logs/loglist")
def show_loglist():
    # --- 1. 権限チェックの準備 ---
    user_role = session.get('role', 0)
    # システム管理者のロールIDを定義します (例: 1)
    # ご自身の環境に合わせてIDを調整してください
    ADMIN_ROLE_ID = 1 
    # 管理者のみが閲覧可能な履歴タイプを定義します
    restricted_targets = {10, 11} # 10:社員リスト, 11:認証アカウント

    target_type_str = request.args.get('target', '1')
    target_type = int(target_type_str) if target_type_str.isdigit() else 1

    # --- 2. URL直接アクセスに対するブロック ---
    if target_type in restricted_targets and user_role != ADMIN_ROLE_ID:
        flash("この履歴を閲覧する権限がありません。", "danger")
        # 権限がない場合は、デフォルトの履歴画面（申込履歴）にリダイレクトします
        return redirect(url_for('logs.show_loglist'))

    # --- 3. 権限に基づいて表示するタブをフィルタリング ---
    visible_target_type_map = constants.TARGET_TYPE_MAP.copy()
    if user_role != ADMIN_ROLE_ID:
        for type_id in restricted_targets:
            visible_target_type_map.pop(type_id, None) # 存在すれば辞書から削除

    logs = []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # (データベースからログを取得するロジックは変更なし)
            sql = "SELECT * FROM tr31_action_log WHERE target_type = %s ORDER BY log_timestamp DESC"
            cursor.execute(sql, (target_type,))
            logs = cursor.fetchall()

            for log in logs:
                if log.get('action_details'):
                    try:
                        log['action_details_dict'] = json.loads(log['action_details'])
                    except (json.JSONDecodeError, TypeError):
                        log['action_details_dict'] = {'raw': log['action_details']}
                else:
                    log['action_details_dict'] = None
    except Exception as e:
        print(f"History log acquisition failed: {e}")
        flash("履歴の取得中にエラーが発生しました。管理者にお問い合わせください。", "danger")
    finally:
        if conn:
            conn.close()

    return render_template(
        "logs/loglist.html",
        logs=logs,
        # --- 4. フィルタリングした辞書をテンプレートに渡す ---
        target_type_map=visible_target_type_map,
        action_source_map=constants.ACTION_SOURCE_MAP,
        action_type_map=constants.ACTION_TYPE_MAP,
        current_target_type=target_type
    )