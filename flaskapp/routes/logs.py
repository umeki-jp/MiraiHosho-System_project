# flaskapp/routes/logs.py

import json
import datetime  # 追加
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flaskapp.utils.db import get_db_connection
from flaskapp.common import constants

logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/logs/loglist")
def show_loglist():
    # --- 1. 権限チェック ---
    user_role = session.get('role', 0)
    ADMIN_ROLE_ID = 1
    restricted_targets = {10, 11} # 社員リスト, 認証アカウント

    # --- 2. 検索・表示条件の取得 ---
    filters = {
        "target_id": request.args.get("target_id", "").strip(),
        "shain_name": request.args.get("shain_name", "").strip(),
        "log_timestamp_from": request.args.get("log_timestamp_from", "").strip(),
        "log_timestamp_to": request.args.get("log_timestamp_to", "").strip(),
        "action_source": request.args.get("action_source", "").strip(),
        "action_type": request.args.get("action_type", "").strip(),
    }
    target_type_str = request.args.get('target', '1') # デフォルトは「契約」
    target_type = int(target_type_str) if target_type_str.isdigit() else 1

    # --- 3. 権限チェックとリダイレクト ---
    if target_type in restricted_targets and user_role != ADMIN_ROLE_ID:
        flash("この履歴を閲覧する権限がありません。", "danger")
        return redirect(url_for('logs.show_loglist'))

    # --- 4. ページネーションとソート ---
    page = int(request.args.get("page", "1"))
    limit = int(request.args.get("limit", "20"))
    offset = (page - 1) * limit
    sort_by = request.args.get("sort_by", "log_timestamp")
    sort_order = request.args.get("sort_order", "desc")

    allowed_sort_columns = ['log_timestamp', 'target_id', 'shain_name', 'action_source', 'action_type']
    order_by_sql = "ORDER BY log_timestamp DESC"
    if sort_by in allowed_sort_columns and sort_order in ['asc', 'desc']:
        order_by_sql = f"ORDER BY {sort_by} {sort_order.upper()}"

    # --- 5. データベース検索 ---
    logs = []
    total = 0
    conn = get_db_connection()
    try:
        # WHERE句の組み立て
        where_clauses = ["target_type = %(target_type)s"]
        params = {"target_type": target_type}

        if filters["target_id"]:
            where_clauses.append("target_id LIKE %(target_id)s")
            params["target_id"] = f"%{filters['target_id']}%"
        if filters["shain_name"]:
            where_clauses.append("shain_name LIKE %(shain_name)s")
            params["shain_name"] = f"%{filters['shain_name']}%"
        if filters["log_timestamp_from"]:
            where_clauses.append("log_timestamp >= %(log_timestamp_from)s")
            params["log_timestamp_from"] = filters["log_timestamp_from"]
        if filters["log_timestamp_to"]:
            # 翌日の0時までを範囲に含める
            to_date = datetime.datetime.strptime(filters["log_timestamp_to"], '%Y-%m-%d').date() + datetime.timedelta(days=1)
            where_clauses.append("log_timestamp < %(log_timestamp_to)s")
            params["log_timestamp_to"] = to_date.strftime('%Y-%m-%d')
        if filters["action_source"]:
            where_clauses.append("action_source = %(action_source)s")
            params["action_source"] = filters["action_source"]
        if filters["action_type"]:
            where_clauses.append("action_type = %(action_type)s")
            params["action_type"] = filters["action_type"]

        where_sql = " AND ".join(where_clauses)

        with conn.cursor() as cursor:
            # 総件数を取得
            count_sql = f"SELECT COUNT(*) as total FROM tr31_action_log WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0

            # 表示するデータを取得
            params_with_limit = params.copy()
            params_with_limit['limit'] = limit
            params_with_limit['offset'] = offset
            sql = f"SELECT * FROM tr31_action_log WHERE {where_sql} {order_by_sql} LIMIT %(limit)s OFFSET %(offset)s"
            cursor.execute(sql, params_with_limit)
            logs = cursor.fetchall()

            # JSON詳細を辞書に変換
            for log in logs:
                if log.get('action_details'):
                    try:
                        log['action_details_dict'] = json.loads(log['action_details'])
                    except (json.JSONDecodeError, TypeError):
                        log['action_details_dict'] = {}
    except Exception as e:
        flash(f"履歴の取得中にエラーが発生しました: {e}", "danger")
    finally:
        if conn: conn.close()
    
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    # 権限に基づいて表示タブをフィルタリング
    visible_target_type_map = constants.TARGET_TYPE_MAP.copy()
    if user_role != ADMIN_ROLE_ID:
        for type_id in restricted_targets:
            visible_target_type_map.pop(type_id, None)

    return render_template(
        "logs/loglist.html",
        logs=logs,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
        target_type_map=visible_target_type_map,
        action_source_map=constants.ACTION_SOURCE_MAP,
        action_type_map=constants.ACTION_TYPE_MAP,
        current_target_type=target_type
    )