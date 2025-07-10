import datetime
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flaskapp.utils.db import get_db_connection
from flaskapp.common import constants
from flaskapp.services.logging_service import log_action

# Blueprintの作成
shainlist_bp = Blueprint("shainlist", __name__, url_prefix="/masters")

# ▼▼▼ customerlist.pyのfield_namesに倣い、扱うカラムをリストとして定義 ▼▼▼
shain_field_names = [
    'shain_name', 'shain_kana', 'shain_joindate', 'shain_department', 'shain_position',
    'shain_leftdate', 'is_active', 'shain_remarks', 'registration_status',
    'registration_date', 'registration_shain', 'update_date', 'update_shain'
]

# ヘルパー関数
def get_shain_field_labels():
    """社員マスタの日本語項目名を返す"""
    return {
        "shain_name": "社員名", "shain_kana": "社員名カナ", "is_active": "状態",
        "shain_joindate": "入社日", "shain_department": "部署", "shain_position": "役職",
        "shain_leftdate": "退職日", "registration_status": "登録状況", "shain_remarks": "備考"
    }

#
# 一覧表示機能
#
@shainlist_bp.route("/shainlist")
def show_shainlist():
    """社員一覧の表示と検索を行う"""
    try:
        # 検索フィルターの値を取得
        filters = {
            "shain_code": request.args.get("shain_code", "").strip(),
            "shain_name": request.args.get("shain_name", "").strip(),
            "shain_kana": request.args.get("shain_kana", "").strip(),
            "registration_status": request.args.get("registration_status", "").strip(),
            "is_active": request.args.get("is_active", "").strip(),
            "registration_date_from": request.args.get("registration_date_from", "").strip(),
            "registration_date_to": request.args.get("registration_date_to", "").strip(),
        }
        has_search = any(filters.values())
        
        # ページネーションの設定
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        offset = (page - 1) * limit

        # ソートの設定
        sort_by = request.args.get("sort_by", "shain_code")
        sort_order = request.args.get("sort_order", "asc")
        allowed_sort_columns = ['shain_code', 'shain_name', 'shain_kana', 'registration_date', 'last_login_at', 'is_active']
        if sort_by not in allowed_sort_columns: sort_by = 'shain_code'
        if sort_order not in ['asc', 'desc']: sort_order = 'asc'
        order_by_sql = f"ORDER BY {sort_by} {sort_order.upper()}"

        conn = get_db_connection()
        if not conn:
            flash("データベースに接続できませんでした。", "danger")
            return render_template("masters/shainlist.html", shains=[], total=0, page=page, limit=limit, total_pages=0, filters=filters)

        results = []
        total = 0
        with conn.cursor() as cursor:
            # 検索条件の組み立て
            where_clauses = ["1=1"]
            params = {}
            if filters["shain_code"]:
                where_clauses.append("shain_code LIKE %(shain_code)s")
                params['shain_code'] = f"%{filters['shain_code']}%"
            if filters["shain_name"]:
                where_clauses.append("shain_name LIKE %(shain_name)s")
                params['shain_name'] = f"%{filters['shain_name']}%"
            if filters["shain_kana"]:
                where_clauses.append("shain_kana LIKE %(shain_kana)s")
                params['shain_kana'] = f"%{filters['shain_kana']}%"
            if filters["registration_status"]:
                where_clauses.append("registration_status = %(registration_status)s")
                params['registration_status'] = filters['registration_status']
            if filters["is_active"]:
                where_clauses.append("is_active = %(is_active)s")
                params['is_active'] = filters['is_active']
            if filters["registration_date_from"]:
                where_clauses.append("registration_date >= %(registration_date_from)s")
                params['registration_date_from'] = filters['registration_date_from']
            if filters["registration_date_to"]:
                where_clauses.append("registration_date <= %(registration_date_to)s")
                params['registration_date_to'] = filters['registration_date_to']
            
            where_sql = " AND ".join(where_clauses)

            # 総件数を取得
            count_sql = f"SELECT COUNT(*) as total FROM ms_shainlist WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0

            # 社員データを取得
            if total > 0:
                params_with_limit = params.copy()
                params_with_limit['limit'] = limit
                params_with_limit['offset'] = offset
                
                with open('flaskapp/sql/shains/select_shainlist.sql', 'r', encoding='utf-8') as f:
                    base_sql = f.read()
                
                sql = f"{base_sql.strip().rstrip(';')} WHERE {where_sql} {order_by_sql} LIMIT %(limit)s OFFSET %(offset)s"
                cursor.execute(sql, params_with_limit)
                results = cursor.fetchall()

    except Exception as e:
        flash(f"データ取得中にエラーが発生しました: {e}", "danger")
        results = []
        total = 0
    finally:
        if conn:
            conn.close()
            
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return render_template(
        "masters/shainlist.html",
        shains=results,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        filters=filters,
        has_search=has_search,
        selected_limit=str(limit),
        sort_by=sort_by,
        sort_order=sort_order
    )

#
# 新規登録機能
#
@shainlist_bp.route("/ms_shainlist/new", methods=["GET", "POST"])
def shain_new():
    """新規社員の登録"""
    button_config = {"show_instant_register": True}

    if request.method == 'GET':
        return render_template("masters/shain_form.html", mode="create", form_data={}, button_config=button_config)

    conn = None
    try:
        form_data = {f: request.form.get(f, "").strip() for f in shain_field_names}
        if not form_data.get("shain_name"):
            flash("社員名を入力してください。", "danger")
            return render_template("masters/shain_form.html", mode="create", form_data=form_data, button_config=button_config)

        conn = get_db_connection()
        if not conn:
            raise Exception("データベースに接続できませんでした。")

        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(CAST(SUBSTRING(shain_code, 2) AS UNSIGNED)) AS max_num FROM ms_shainlist WHERE shain_code LIKE 'S%'")
            max_num = cursor.fetchone()['max_num']
            new_shain_code = f"S{(max_num or 0) + 1:05d}"

            # ▼▼▼ 変更点 ▼▼▼
            form_data['registration_date'] = datetime.datetime.now()
            form_data['registration_shain'] = session.get('shain_name', 'system')
            form_data['registration_status'] = 1 # ステータスを「1: 登録済」に固定

            insert_columns = ['shain_code'] + shain_field_names
            # shain_field_namesの順序で値を取得
            values = [new_shain_code] + [form_data.get(f) or None for f in shain_field_names]
            # ▲▲▲ 変更点 ▲▲▲

            sql = f"INSERT INTO ms_shainlist ({', '.join(insert_columns)}) VALUES ({', '.join(['%s'] * len(values))})"
            cursor.execute(sql, values)
            conn.commit()

            # ▼▼▼ ログ記録処理を追加 ▼▼▼
            log_action(
                target_type=10,  # 10: 社員リスト
                target_id=new_shain_code,
                action_source=2, # 2: ユーザー操作
                action_type=1,  # 1: 登録
                action_details={'message': f'社員 {new_shain_code} が新規登録されました。'}
            )
            # ▲▲▲ ログ記録処理ここまで ▲▲▲
        
        flash(f"社員コード {new_shain_code} で登録しました。", "success")
        return redirect(url_for('shainlist.shain_edit', shain_code=new_shain_code))

    except Exception as e:
        flash(f"登録中にエラーが発生しました: {e}", "danger")
        return render_template("masters/shain_form.html", mode="create", form_data=request.form.to_dict(), button_config=button_config)
    finally:
        if conn:
            conn.close()

# 編集機能（改訂版）
#
@shainlist_bp.route("/ms_shainlist/<shain_code>", methods=["GET", "POST"])
def shain_edit(shain_code):
    """既存社員の編集（customerlist.pyのロジックに準拠）"""
    conn = get_db_connection()
    if not conn:
        flash("データベースに接続できませんでした。", "danger")
        return redirect(url_for('shainlist.show_shainlist'))

    try:
        button_config = {"show_instant_update": True, "show_instant_delete": False}

        if request.method == 'POST':
            action = request.form.get("action")
            
            # --- 1. 更新ボタン（1回目） > 確認画面表示 ---
            if action == "update_instant":
                # ▼▼▼ 最重要修正点：安全なフォームデータ取得 ▼▼▼
                form_data = {f: request.form.get(f, "").strip() for f in shain_field_names}

                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ms_shainlist WHERE shain_code = %s", (shain_code,))
                    before_data = cursor.fetchone()

                changes = []
                field_labels = get_shain_field_labels()
                for field in field_labels.keys():
                    before_val = before_data.get(field)
                    after_val = form_data.get(field, '')

                    # (比較ロジックはcustomerlistに準拠)
                    before_str, after_str = str(before_val or ''), str(after_val or '')
                    if field == "is_active":
                        before_str = "有効" if before_val == 1 else "無効"
                        after_str = "有効" if str(after_val) == '1' else "無効"
                    elif isinstance(before_val, datetime.date):
                        before_str = before_val.strftime('%Y-%m-%d')
                    
                    if before_str != after_str:
                        changes.append({"label": field_labels.get(field, field), "before": before_str, "after": after_str})
                
                if not changes:
                    flash("変更された項目がありません。", "info")
                    return redirect(url_for('shainlist.shain_edit', shain_code=shain_code))

                return render_template(
                    "shared/update_confirm.html",
                    changes=changes, form_data=form_data,
                    submit_url=url_for('shainlist.shain_edit', shain_code=shain_code),
                    is_approval_flow=False, final_action_value="submit_update_instant"
                )

            # --- 2. 確認画面の更新ボタン（2回目） > DB更新実行 ---
            elif action == "submit_update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in shain_field_names}
                
                # ▼▼▼ 変更点 ▼▼▼
                form_data['update_date'] = datetime.datetime.now()
                form_data['update_shain'] = session.get('shain_name', 'system')
                form_data['registration_status'] = 1 # ステータスを「1: 登録済」に固定

                with conn.cursor() as cursor:
                    update_clause = ", ".join([f"{col} = %s" for col in shain_field_names])
                    values = [form_data.get(f) or None for f in shain_field_names]
                    
                    sql = f"UPDATE ms_shainlist SET {update_clause} WHERE shain_code = %s"
                    values.append(shain_code)
                    cursor.execute(sql, values)
                    conn.commit()

                     # ▼▼▼ ログ記録処理を追加 ▼▼▼
                    # 確認画面から渡された変更内容のJSON文字列を読み込む
                    changes_for_log = json.loads(request.form.get('changes_json', '[]'))
                    log_action(
                        target_type=10,  # 10: 社員リスト
                        target_id=shain_code,
                        action_source=2, # 2: ユーザー操作
                        action_type=2,  # 2: 更新
                        action_details=changes_for_log
                    )
                    # ▲▲▲ ログ記録処理ここまで ▲▲▲
                
                # flash("更新しました。", "success") # ←完了画面にメッセージがあるので不要
            return render_template("shared/action_done.html", action_label="更新")

        # --- GETリクエスト（初期表示） ---
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms_shainlist WHERE shain_code = %s", (shain_code,))
            shain_data = cursor.fetchone()

        if not shain_data:
            flash("指定された社員が見つかりませんでした。", "danger")
            return redirect(url_for('shainlist.show_shainlist'))

        return render_template("masters/shain_form.html", mode="edit", form_data=shain_data, button_config=button_config)

    except Exception as e:
        flash(f"処理中にエラーが発生しました: {e}", "danger")
        return redirect(url_for('shainlist.show_shainlist'))
    finally:
        if conn:
            conn.close()
