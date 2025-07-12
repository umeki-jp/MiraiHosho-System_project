import os
import datetime
import json
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash
from flaskapp.utils.db import get_db_connection
from flaskapp.common import constants
from flaskapp.services.logging_service import log_action

# Blueprintの作成
auth_user_bp = Blueprint("auth_user", __name__, url_prefix="/masters")

# ▼▼▼ customerlist.pyのfield_namesに倣い、扱うカラムをリストとして定義 ▼▼▼
auth_user_field_names = [
    'shain_code',
    'account_id',
    'password_hash',
    'role',
    'login_enabled',
    'auth_remarks',
    'registration_status',
    'registration_date',
    'registration_shain',
    'update_date',
    'update_shain'
]

# ヘルパー関数
def get_auth_user_field_labels():
    """認証マスタの日本語項目名を返す"""
    return {
        "shain_code": "社員コード",
        "account_id": "アカウントID",
        "role": "権限",
        "login_enabled": "状態",
        "auth_remarks": "備考",
        "registration_status": "登録状況"
    }

#
# 一覧表示機能
#
@auth_user_bp.route("/auth_user")  # 認証マスタ一覧表示
def show_auth_userlist():
    """認証マスタ一覧の表示と検索を行う"""
    error_message = None
    conn = None
    results = []
    total = 0

    try:
        # 検索フィルターの値を取得
        filters = {
            "user_id": request.args.get("user_id", "").strip(),
            "account_id": request.args.get("account_id", "").strip(),
            "shain_name": request.args.get("shain_name", "").strip(),
            "role": request.args.get("role", "").strip(),
            "login_enabled": request.args.get("login_enabled", "").strip(),
            "registration_date_from": request.args.get("registration_date_from", "").strip(),
            "registration_date_to": request.args.get("registration_date_to", "").strip(),
        }
        has_search = any(filters.values())

        # ページネーションの設定
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)
        offset = (page - 1) * limit

        # ソートの設定
        sort_by = request.args.get("sort_by", "user_id")
        sort_order = request.args.get("sort_order", "asc")
        allowed_sort_columns = ['user_id', 'account_id', 'shain_name', 'role', 'login_enabled', 'registration_date']
        if sort_by not in allowed_sort_columns:
            sort_by = 'user_id'
        if sort_order not in ['asc', 'desc']:
            sort_order = 'asc'

        # ソートキーにテーブルエイリアスを付与
        sort_by_aliased = f"au.{sort_by}"
        if sort_by == 'shain_name':
            sort_by_aliased = f"ms.{sort_by}"
        order_by_sql = f"ORDER BY {sort_by_aliased} {sort_order.upper()}"

        conn = get_db_connection()
        if not conn:
            raise Exception("データベースに接続できませんでした。")

        # SQLファイルを安全に読み込む
        try:
            sql_file_path = os.path.join(current_app.root_path, 'sql/auth/select_auth_user.sql')
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                base_sql = f.read()
        except FileNotFoundError:
            raise Exception("SQL定義ファイル(auth_user)が見つかりません。")

        # 検索条件の組み立て
        where_clauses = ["1=1"]
        params = {}
        if filters["user_id"]:
            where_clauses.append("au.user_id LIKE %(user_id)s")
            params['user_id'] = f"%{filters['user_id']}%"
        if filters["account_id"]:
            where_clauses.append("au.account_id LIKE %(account_id)s")
            params['account_id'] = f"%{filters['account_id']}%"
        if filters["shain_name"]:
            where_clauses.append("ms.shain_name LIKE %(shain_name)s")
            params['shain_name'] = f"%{filters['shain_name']}%"
        if filters["role"]:
            where_clauses.append("au.role = %(role)s")
            params['role'] = filters['role']
        if filters["login_enabled"]:
            where_clauses.append("au.login_enabled = %(login_enabled)s")
            params['login_enabled'] = filters['login_enabled']
        if filters["registration_date_from"]:
            where_clauses.append("au.registration_date >= %(registration_date_from)s")
            params['registration_date_from'] = filters['registration_date_from']
        if filters["registration_date_to"]:
            date_to = datetime.datetime.strptime(filters["registration_date_to"], '%Y-%m-%d').date()
            date_to_end_of_day = datetime.datetime.combine(date_to, datetime.time.max)
            where_clauses.append("au.registration_date <= %(registration_date_to)s")
            params['registration_date_to'] = date_to_end_of_day
        
        where_sql = " AND ".join(where_clauses)

        with conn.cursor() as cursor:
            # COUNTクエリの組み立てと実行
            count_query_template = base_sql.replace("/*[LIMIT]*/", "").replace("/*[ORDER_BY]*/", "")
            count_query = count_query_template.replace("/*[WHERE]*/", f"WHERE {where_sql}")
            count_sql = "SELECT COUNT(*) as total FROM (" + count_query.strip().rstrip(';') + ") AS count_table"
            
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0

            # 本体クエリの組み立てと実行
            if total > 0:
                params_with_limit = params.copy()
                params_with_limit['limit'] = limit
                params_with_limit['offset'] = offset
                
                main_sql = base_sql.replace("/*[WHERE]*/", f"WHERE {where_sql}")
                main_sql = main_sql.replace("/*[ORDER_BY]*/", order_by_sql)
                main_sql = main_sql.replace("/*[LIMIT]*/", "LIMIT %(limit)s OFFSET %(offset)s")
                
                cursor.execute(main_sql, params_with_limit)
                results = cursor.fetchall()

    except Exception as e:
        error_message = f"処理中にエラーが発生しました: {e}"
        flash(error_message, "danger")
        results = []
        total = 0
    finally:
        if conn:
            conn.close()
            
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return render_template(
        "masters/auth_user.html",
        auth_users=results,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        filters=filters,
        has_search=has_search,
        selected_limit=str(limit),
        sort_by=sort_by,
        sort_order=sort_order,
        error_message=error_message
    )
#
# 新規登録機能
#
@auth_user_bp.route("/auth_user/new", methods=["GET", "POST"])
def auth_user_new():
    """新規認証ユーザーの登録"""
    button_config = {"show_instant_register": True}

    if request.method == 'GET':
        return render_template("masters/auth_user_form.html", mode="create", form_data={}, button_config=button_config)

    # --- POSTリクエスト (登録実行) ---
    conn = None
    try:
        # auth_user_field_namesからキーを取得するが、パスワードは別途扱う
        form_data = {f: request.form.get(f, "").strip() for f in auth_user_field_names if f != 'password_hash'}
        password = request.form.get("password", "").strip()

        # バリデーション
        if not form_data.get("account_id") or not password:
            flash("アカウントIDとパスワードは必須です。", "danger")
            return render_template("masters/auth_user_form.html", mode="create", form_data=form_data, button_config=button_config)

        conn = get_db_connection()
        if not conn:
            raise Exception("データベースに接続できませんでした。")
        
        # アカウントIDの重複チェック
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM ms_auth_user WHERE account_id = %s", (form_data.get("account_id"),))
            account_exists = cursor.fetchone()['count']
        
        if account_exists > 0:
            flash("このアカウントIDは既に使用されています。別のIDを指定してください。", "danger")
            # 入力内容を保持したままフォーム画面に戻る
            return render_template("masters/auth_user_form.html", mode="create", form_data=request.form.to_dict(), button_config=button_config)

        with conn.cursor() as cursor:
            # 新しいUser IDを生成 (ID + 5桁のゼロ埋め数字)
            cursor.execute("SELECT MAX(CAST(SUBSTRING(user_id, 3) AS UNSIGNED)) AS max_num FROM ms_auth_user WHERE user_id LIKE 'ID%'")
            max_num = cursor.fetchone()['max_num']
            new_user_id = f"ID{(max_num or 0) + 1:05d}"

            # 登録用データ準備
            form_data['registration_date'] = datetime.datetime.now()
            form_data['registration_shain'] = session.get('shain_name', 'system')
            form_data['registration_status'] = 1  # ステータスを「1: 登録済」に固定

            # ★★★ 重要: パスワードをハッシュ化して格納 ★★★
            form_data['password_hash'] = generate_password_hash(password)

            # DBに挿入するカラムと値のリストを作成
            insert_columns = ['user_id'] + auth_user_field_names
            values = [new_user_id] + [form_data.get(f) or None for f in auth_user_field_names]

            sql = f"INSERT INTO ms_auth_user ({', '.join(insert_columns)}) VALUES ({', '.join(['%s'] * len(values))})"
            cursor.execute(sql, values)
            conn.commit()

            # ログ記録
            log_action(
                target_type=11,  # 11: 認証マスタ
                target_id=new_user_id,
                action_source=2, # 2: ユーザー操作
                action_type=1,  # 1: 登録
                action_details={'message': f'ユーザー {new_user_id} ({form_data["account_id"]}) が新規登録されました。'}
            )
        
        flash(f"ユーザーID {new_user_id} で登録しました。", "success")
        # 登録後は編集画面にリダイレクト
        return redirect(url_for('auth_user.auth_user_edit', user_id=new_user_id))

    except Exception as e:
        flash(f"登録中にエラーが発生しました: {e}", "danger")
        return render_template("masters/auth_user_form.html", mode="create", form_data=request.form.to_dict(), button_config=button_config)
    finally:
        if conn:
            conn.close()

#
# 編集機能
#
@auth_user_bp.route("/auth_user/<user_id>", methods=["GET", "POST"])
def auth_user_edit(user_id):
    """既存認証ユーザーの編集"""
    conn = get_db_connection()
    if not conn:
        flash("データベースに接続できませんでした。", "danger")
        return redirect(url_for('auth_user.show_auth_userlist'))

    try:
        button_config = {"show_instant_update": True, "show_instant_delete": False}

        if request.method == 'POST':
            action = request.form.get("action")
            
            # --- 1. 更新ボタン（1回目） > 確認画面表示 ---
            if action == "update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in auth_user_field_names if f != 'password_hash'}
                password = request.form.get("password", "").strip()

                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ms_auth_user WHERE user_id = %s", (user_id,))
                    before_data = cursor.fetchone()

                changes = []
                field_labels = get_auth_user_field_labels()
                for field in field_labels.keys():
                    before_val = before_data.get(field)
                    after_val = form_data.get(field, '')
                    
                    before_str, after_str = str(before_val or ''), str(after_val or '')

                    if field == "login_enabled":
                        before_str = "有効" if before_val == 1 else "無効"
                        after_str = "有効" if str(after_val) == '1' else "無効"
                    
                    # ▼▼▼ 追加 ▼▼▼
                    elif field == "role":
                        # before_val (DBからの値) は数値
                        before_str = constants.role_map.get(before_val, '不明')
                        # after_val (フォームからの値) は文字列なので整数に変換
                        after_str = constants.role_map.get(int(after_val), '不明')
                    # ▲▲▲ 追加 ▲▲▲

                    if before_str != after_str:
                        changes.append({"label": field_labels.get(field, field), "before": before_str, "after": after_str})                
                
                # パスワードが入力されていたら、変更項目として追加
                if password:
                    changes.append({"label": "パスワード", "before": "（変更前）", "after": "（変更後）"})
                
                if not changes:
                    flash("変更された項目がありません。", "info")
                    return redirect(url_for('auth_user.auth_user_edit', user_id=user_id))
                
                # パスワードをフォームデータに含めて確認画面へ渡す
                form_data['password'] = password
                return render_template(
                    "shared/update_confirm.html",
                    changes=changes, form_data=form_data,
                    submit_url=url_for('auth_user.auth_user_edit', user_id=user_id),
                    is_approval_flow=False, final_action_value="submit_update_instant"
                )

             # --- 2. 削除ボタン（1回目） > 確認画面表示 ---
            elif action == "delete_instant":
                with conn.cursor() as cursor:
                    # サーバー側で再度、削除条件を確認
                    cursor.execute("SELECT shain_code, account_id FROM ms_auth_user WHERE user_id = %s", (user_id,))
                    user_to_delete = cursor.fetchone()

                # 社員コードが紐づいていないかチェック
                is_deletable = not user_to_delete.get('shain_code')
                
                if is_deletable:
                    message = f"ユーザー「{user_to_delete.get('account_id')}」（ID: {user_id}）を削除します。この操作は元に戻せません。よろしいですか？"
                else:
                    message = "このユーザーは社員情報に紐づいているため、削除できません。"

                return render_template(
                   "shared/delete_confirm.html",
                   message=message,
                   deletable=is_deletable, # ← ここを「is_deletable=」から「deletable=」に変更
                   submit_url=url_for('auth_user.auth_user_edit', user_id=user_id),
                   final_action_value="submit_delete_instant"
               )

            # --- 3. 確認画面の更新ボタン（2回目） > DB更新実行 ---
            elif action == "submit_update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in auth_user_field_names if f != 'password_hash'}
                password = request.form.get("password", "").strip()
                
                form_data['update_date'] = datetime.datetime.now()
                form_data['update_shain'] = session.get('shain_name', 'system')
                form_data['registration_status'] = 1

                # 更新対象のカラムと値を動的に構築
                update_fields = [f for f in auth_user_field_names if f not in ['password_hash', 'registration_date', 'registration_shain']]
                values = [form_data.get(f) or None for f in update_fields]
                
                # パスワードが入力されていれば、ハッシュ化して更新対象に加える
                if password:
                    update_fields.append('password_hash')
                    values.append(generate_password_hash(password))

                with conn.cursor() as cursor:
                    update_clause = ", ".join([f"{col} = %s" for col in update_fields])
                    sql = f"UPDATE ms_auth_user SET {update_clause} WHERE user_id = %s"
                    values.append(user_id)
                    cursor.execute(sql, values)
                    conn.commit()

                    # ログ記録
                    changes_for_log = json.loads(request.form.get('changes_json', '[]'))
                    log_action(
                        target_type=11,  # 11: 認証マスタ
                        target_id=user_id,
                        action_source=2,
                        action_type=2,  # 2: 更新
                        action_details=changes_for_log
                    )
                
                return render_template("shared/action_done.html", action_label="更新")

             # --- 4. 削除確認画面の「削除する」ボタン（2回目） > DB削除実行 ---
            elif action == "submit_delete_instant":
                with conn.cursor() as cursor:
                    # 念のため、再度サーバー側で削除条件を確認
                    cursor.execute("SELECT shain_code, account_id FROM ms_auth_user WHERE user_id = %s", (user_id,))
                    user_to_delete = cursor.fetchone()

                    if user_to_delete and not user_to_delete.get('shain_code'):
                        # 削除を実行
                        cursor.execute("DELETE FROM ms_auth_user WHERE user_id = %s", (user_id,))
                        conn.commit()

                        # ログ記録
                        log_action(
                            target_type=11,  # 11: 認証マスタ
                            target_id=user_id,
                            action_source=2,
                            action_type=3,  # 3: 削除
                            action_details={'message': f"ユーザー「{user_to_delete.get('account_id')}」が削除されました。"}
                        )
                        # 完了画面を表示
                        return render_template("shared/action_done.html", action_label="削除")
                    else:
                        # 条件に合わない場合はエラーメッセージを表示
                        flash("このユーザーは削除できません。", "danger")
                        return redirect(url_for('auth_user.auth_user_edit', user_id=user_id))

        # --- GETリクエスト（初期表示） ---
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms_auth_user WHERE user_id = %s", (user_id,))
            user_data = cursor.fetchone()

        if not user_data:
            flash("指定されたユーザーが見つかりませんでした。", "danger")
            return redirect(url_for('auth_user.show_auth_userlist'))

        # ▼▼▼ 変更 ▼▼▼
        # shain_codeがなければ削除ボタンを表示
        show_delete_button = not user_data.get('shain_code')
        button_config = {"show_instant_update": True, "show_instant_delete": show_delete_button}
        # ▲▲▲ 変更 ▲▲▲

        return render_template("masters/auth_user_form.html", mode="edit", form_data=user_data, button_config=button_config)

    except Exception as e:
        flash(f"処理中にエラーが発生しました: {e}", "danger")
        return redirect(url_for('auth_user.show_auth_userlist'))
    finally:
        if conn:
            conn.close()